#!/usr/bin/env python3
"""Read-only DJI Assistant firmware metadata client for wa150.

The client deliberately has no device transport and no upgrade entry point.  It
only performs GET requests to two metadata endpoints on one pinned HTTPS host.
The third official firmware path is recorded in the allowlist but is hard
blocked in this build so an accidental module-body download cannot occur.

The Assistant application secret is reconstructed in memory from the installed
libDJIUavService.dylib constructor.  It is never printed or persisted.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import re
import ssl
import struct
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import unquote, urlencode, urlsplit
import xml.etree.ElementTree as ET


DEFAULT_DYLIB = Path(
    "/Applications/DJI Assistant 2(Consumer Drones Series).app/Contents/"
    "MacOS/DJIServices/libDJIUavService.dylib"
)
CONSTRUCTOR_SYMBOL = "__ZN12DJIServerApiC2Ev"

ALLOWED_HOST = "mydjiflight.dji.com"
ALLOWED_PATHS = frozenset(
    {"/getfile/getallfile", "/getfile/download", "/getfile/firmware"}
)
METADATA_PATHS = frozenset({"/getfile/getallfile", "/getfile/download"})
PRODUCT_ID = "wa150"
TARGET_VERSIONS = ("01.00.0600", "01.00.0700")
APP_VERSION_HEADER = "da2/csm/2.1.40.0"
MAX_LIST_BYTES = 2 * 1024 * 1024
MAX_CONFIG_BYTES = 8 * 1024 * 1024


class SafetyError(RuntimeError):
    """Raised when an operation crosses the metadata-only safety boundary."""


class RedirectRefused(SafetyError):
    """A sanitized cross-host redirect that the client intentionally refused."""

    def __init__(self, status: int, host: str, path: str) -> None:
        self.status = status
        self.host = host
        self.path = path
        super().__init__(
            f"redirect refused; HTTP {status} target host={host!r} path={path!r}"
        )


class FormatError(RuntimeError):
    """Raised when the installed binary or response format is not recognized."""


def _run_otool(dylib: Path) -> list[str]:
    if not dylib.is_file():
        raise FormatError(f"DJI service library is missing: {dylib}")
    result = subprocess.run(
        ["/usr/bin/otool", "-tvV", "-p", CONSTRUCTOR_SYMBOL, str(dylib)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
    )
    if result.returncode != 0 or f"{CONSTRUCTOR_SYMBOL}:" not in result.stdout:
        raise FormatError("otool could not isolate the expected DJIServerApi constructor")
    return result.stdout.splitlines()


def _parse_imm(text: str) -> int:
    return int(text, 16) & 0xFF


def _extract_encoded_block(
    lines: Sequence[str], allocation_size: int, expected_payload_size: int
) -> bytes:
    marker = re.compile(rf"\bmovl\s+\$0x{allocation_size:x},\s*%edi\b", re.I)
    byte_write = re.compile(
        r"\bmovb\s+\$0x([0-9a-f]+),\s*(?:(0x[0-9a-f]+)\s*)?\(%rax\)", re.I
    )
    append_imm = re.compile(r"\bmovl\s+\$0x([0-9a-f]+),\s*%esi\b", re.I)

    start = next((i for i, line in enumerate(lines) if marker.search(line)), None)
    if start is None:
        raise FormatError(f"constructor allocation marker 0x{allocation_size:x} not found")

    initial: dict[int, int] = {}
    appended: list[int] = []
    for line in lines[start + 1 :]:
        if re.search(r"\bcallq\s+\*0x38\(%rax\)", line):
            break
        match = byte_write.search(line)
        if match:
            offset = int(match.group(2), 16) if match.group(2) else 0
            if offset in (0, 1):
                initial[offset] = _parse_imm(match.group(1))
            continue
        match = append_imm.search(line)
        if match:
            appended.append(_parse_imm(match.group(1)))
    else:
        raise FormatError("constructor encoded block has no terminator")

    if set(initial) != {0, 1}:
        raise FormatError("constructor encoded block is missing its first two bytes")
    encoded = bytes((initial[0], initial[1], *appended))
    if len(encoded) != expected_payload_size:
        raise FormatError(
            f"unexpected encoded payload length {len(encoded)}; "
            f"expected {expected_payload_size}"
        )
    return encoded


def _rip_literal_address(lines: Sequence[str]) -> int:
    literal = re.compile(
        r"^([0-9a-f]+)\s+leaq\s+0x([0-9a-f]+)\(%rip\),\s*%rsi\s+"
        r"## literal pool for:",
        re.I,
    )
    address_line = re.compile(r"^([0-9a-f]+)\s+")
    for index, line in enumerate(lines[:-1]):
        match = literal.search(line.strip())
        if not match:
            continue
        next_match = address_line.search(lines[index + 1].strip())
        if not next_match:
            raise FormatError("could not determine RIP-relative instruction length")
        return int(next_match.group(1), 16) + int(match.group(2), 16)
    raise FormatError("constructor decode-key reference was not found")


def _vm_to_file_offset(image: bytes, vm_address: int) -> int:
    if len(image) < 32:
        raise FormatError("truncated Mach-O image")
    magic, _, _, _, command_count, command_bytes, _, _ = struct.unpack_from(
        "<IiiIIIII", image, 0
    )
    if magic != 0xFEEDFACF:
        raise FormatError("only the installed thin 64-bit Mach-O layout is accepted")
    cursor = 32
    commands_end = cursor + command_bytes
    if commands_end > len(image):
        raise FormatError("invalid Mach-O load-command size")
    for _ in range(command_count):
        if cursor + 8 > commands_end:
            raise FormatError("truncated Mach-O load command")
        command, size = struct.unpack_from("<II", image, cursor)
        if size < 8 or cursor + size > commands_end:
            raise FormatError("invalid Mach-O load command")
        if command == 0x19 and size >= 72:  # LC_SEGMENT_64
            _, _, _, vmaddr, _, fileoff, filesize, _, _, _, _ = struct.unpack_from(
                "<II16sQQQQiiII", image, cursor
            )
            if vmaddr <= vm_address < vmaddr + filesize:
                offset = fileoff + (vm_address - vmaddr)
                if offset >= len(image):
                    raise FormatError("Mach-O virtual address maps outside the file")
                return offset
        cursor += size
    raise FormatError("decode-key virtual address is not in a file-backed segment")


def _rotate_right_8(value: int, count: int) -> int:
    count &= 7
    if count == 0:
        return value & 0xFF
    return ((value >> count) | (value << (8 - count))) & 0xFF


def extract_assistant_material(dylib: Path = DEFAULT_DYLIB) -> tuple[str, bytes, str]:
    """Return (validated host, secret bytes, binary SHA-256).

    No recovered credential is included in exceptions or diagnostics.
    """

    lines = _run_otool(dylib)
    # XsBuffer includes the terminating NUL in the encoded payload.  The
    # constructor later calls strlen(), so strip only that verified terminator.
    encoded_secret = _extract_encoded_block(lines, 0x22, 33)
    encoded_host = _extract_encoded_block(lines, 0x1D, 28)
    key_address = _rip_literal_address(lines)
    image = dylib.read_bytes()
    key_offset = _vm_to_file_offset(image, key_address)
    key = image[key_offset : key_offset + 17]
    if len(key) != 17:
        raise FormatError("truncated constructor decode key")

    def decode(encoded: bytes) -> bytes:
        return bytes(
            _rotate_right_8(value, index) ^ key[index % len(key)]
            for index, value in enumerate(encoded)
        )

    secret_with_nul = decode(encoded_secret)
    host_with_nul = decode(encoded_host)
    if not secret_with_nul.endswith(b"\0") or b"\0" in secret_with_nul[:-1]:
        raise FormatError("decoded Assistant application material has an invalid terminator")
    if not host_with_nul.endswith(b"\0") or b"\0" in host_with_nul[:-1]:
        raise FormatError("decoded Assistant host has an invalid terminator")
    secret = secret_with_nul[:-1]
    host_bytes = host_with_nul[:-1]
    try:
        host = host_bytes.decode("ascii")
    except UnicodeDecodeError as exc:
        raise FormatError("decoded Assistant host is not ASCII") from exc
    if host != f"https://{ALLOWED_HOST}":
        raise SafetyError("installed Assistant host does not match the pinned allowlist")
    if len(secret) != 32 or any(byte < 0x21 or byte > 0x7E for byte in secret):
        raise FormatError("decoded Assistant application material failed shape validation")
    return host, secret, hashlib.sha256(image).hexdigest()


def _md5_hex(parts: Iterable[bytes]) -> str:
    digest_input = b"".join(parts)
    try:
        digest = hashlib.md5(digest_input, usedforsecurity=False)
    except TypeError:  # pragma: no cover - compatibility with older Python
        digest = hashlib.md5(digest_input)
    return digest.hexdigest()


def signature_getallfile(secret: bytes, product_id: str, token: str) -> str:
    return _md5_hex((secret, product_id.encode("utf-8"), token.encode("utf-8")))


def signature_download(
    secret: bytes, product_id: str, product_version: str, token: str
) -> str:
    return _md5_hex(
        (
            secret,
            product_id.encode("utf-8"),
            product_version.encode("utf-8"),
            token.encode("utf-8"),
        )
    )


def signature_firmware_evidence_only(
    secret: bytes,
    product_id: str,
    product_version: str,
    module_id: str,
    module_version: str,
    token: str,
) -> str:
    """Document the recovered formula; this build cannot issue the request.

    Static register/parameter evidence shows the final field is token, not
    account.  Keeping the formula separate from HTTP routing makes that fact
    testable without enabling firmware-body downloads.
    """

    return _md5_hex(
        (
            secret,
            product_id.encode("utf-8"),
            product_version.encode("utf-8"),
            module_id.encode("utf-8"),
            module_version.encode("utf-8"),
            token.encode("utf-8"),
        )
    )


class AllowlistedMetadataHttp:
    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout
        self.context = ssl.create_default_context()
        # The python.org macOS runtime can have an unset OpenSSL cafile even
        # though macOS maintains a current system bundle here.  Add, never
        # replace, those roots; hostname and chain verification remain enabled.
        system_ca_bundle = Path("/etc/ssl/cert.pem")
        if system_ca_bundle.is_file():
            self.context.load_verify_locations(cafile=str(system_ca_bundle))
        self.last_followed_config_redirect: dict[str, Any] | None = None

    @staticmethod
    def _check_response_size(response: http.client.HTTPResponse, max_bytes: int) -> None:
        declared = response.getheader("Content-Length")
        if declared is None:
            return
        try:
            if int(declared) > max_bytes:
                raise SafetyError("response exceeds the metadata-only size ceiling")
        except ValueError as exc:
            raise FormatError("invalid Content-Length from metadata endpoint") from exc

    @staticmethod
    def _validated_config_redirect(location: str) -> tuple[str, str, str]:
        """Return ``(host, target, public_path)`` for one approved CDN hop.

        ``target`` can contain the opaque CDN query required for the request;
        callers must never log or serialize it.  ``public_path`` is safe for a
        de-identified audit report.
        """

        parsed = urlsplit(location)
        host = (parsed.hostname or "").lower()
        decoded_path = unquote(parsed.path)
        path_parts = PurePosixPath(decoded_path).parts
        valid_host = bool(
            re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)*\.djicdn\.com", host)
        )
        valid_path = (
            parsed.path.startswith("/")
            and "\\" not in decoded_path
            and ".." not in path_parts
            and PurePosixPath(decoded_path).name.endswith(".pro.cfg.sig")
        )
        try:
            port = parsed.port
        except ValueError as exc:
            raise SafetyError(
                "configuration redirect failed the second-layer allowlist"
            ) from exc
        if (
            parsed.scheme != "https"
            or not valid_host
            or not valid_path
            or parsed.username is not None
            or parsed.password is not None
            or port not in (None, 443)
            or parsed.fragment
        ):
            raise SafetyError("configuration redirect failed the second-layer allowlist")
        target = parsed.path + (("?" + parsed.query) if parsed.query else "")
        return host, target, parsed.path

    def _follow_config_redirect(
        self,
        location: str,
        request_headers: Mapping[str, str],
        max_bytes: int,
    ) -> bytes:
        host, target, public_path = self._validated_config_redirect(location)
        connection = http.client.HTTPSConnection(
            host, 443, timeout=self.timeout, context=self.context
        )
        try:
            connection.request("GET", target, headers=dict(request_headers))
            response = connection.getresponse()
            if 300 <= response.status < 400:
                raise SafetyError("second configuration redirect was refused")
            if response.status != 200:
                raise RuntimeError(
                    f"official configuration CDN returned HTTP {response.status}"
                )
            media_type = (response.getheader("Content-Type") or "").split(";", 1)[0].lower()
            if media_type not in {
                "application/octet-stream",
                "binary/octet-stream",
                "application/x-download",
                "application/pgp-signature",
                "application/xml",
                "text/xml",
            }:
                raise FormatError(
                    f"unexpected configuration Content-Type {media_type or '<missing>'!r}"
                )
            self._check_response_size(response, max_bytes)
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise SafetyError("configuration exceeded the metadata-only size ceiling")
            self.last_followed_config_redirect = {
                "host": host,
                "path": public_path,
                "query": "omitted",
                "redirect_count": 1,
            }
            return body
        finally:
            connection.close()

    def get(
        self,
        path: str,
        params: Sequence[tuple[str, str]],
        *,
        headers: Mapping[str, str] | None = None,
        max_bytes: int,
    ) -> bytes:
        if path not in ALLOWED_PATHS:
            raise SafetyError(f"path is not allowlisted: {path}")
        if path not in METADATA_PATHS:
            raise SafetyError("firmware module-body requests are disabled in this build")
        if not path.startswith("/") or "//" in path or "?" in path or "#" in path:
            raise SafetyError("path failed canonical-form validation")
        if max_bytes <= 0 or max_bytes > MAX_CONFIG_BYTES:
            raise SafetyError("response limit is outside the metadata-only ceiling")
        self.last_followed_config_redirect = None

        target = path + "?" + urlencode(params, doseq=True)
        request_headers = {
            "Accept": "application/json, application/xml, text/xml, application/octet-stream",
            "User-Agent": "DJI-Assistant-metadata-audit/1.0",
            "Connection": "close",
        }
        if headers:
            request_headers.update(headers)

        connection = http.client.HTTPSConnection(
            ALLOWED_HOST, 443, timeout=self.timeout, context=self.context
        )
        try:
            connection.request("GET", target, headers=request_headers)
            response = connection.getresponse()
            if 300 <= response.status < 400:
                location = response.getheader("Location") or ""
                parsed = urlsplit(location)
                redirect_host = parsed.hostname or ALLOWED_HOST
                redirect_path = parsed.path or "<empty>"
                if path == "/getfile/download":
                    return self._follow_config_redirect(
                        location, request_headers, max_bytes
                    )
                # Intentionally omit the redirect query and fragment.
                raise RedirectRefused(response.status, redirect_host, redirect_path)
            if response.status != 200:
                # Do not include the URL, query, response body, or auth material.
                raise RuntimeError(f"official metadata endpoint returned HTTP {response.status}")
            self._check_response_size(response, max_bytes)
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise SafetyError("response exceeded the metadata-only size ceiling")
            return body
        finally:
            connection.close()


def _list_entries(body: bytes) -> list[dict[str, Any]]:
    try:
        root = json.loads(body.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FormatError("firmware list response is not valid UTF-8 JSON") from exc
    entries: Any = root.get("data") if isinstance(root, dict) else root
    if not isinstance(entries, list):
        raise FormatError("firmware list JSON has no data array")
    return [entry for entry in entries if isinstance(entry, dict)]


def _extract_config_xml(body: bytes) -> tuple[bytes, str]:
    stripped = body.lstrip()
    if stripped.startswith(b"<"):
        return stripped, "xml"
    if len(body) < 0xCC or body[:4] != b"IM*H":
        raise FormatError("configuration response is neither XML nor a recognized IM*H container")
    total = struct.unpack_from("<I", body, 8)[0]
    header_size, signature_size, payload_size = struct.unpack_from("<III", body, 0x10)
    if total != len(body) or header_size + signature_size + payload_size != total:
        raise FormatError("IM*H container length fields are inconsistent")
    payload_start = header_size + signature_size
    xml_size = struct.unpack_from("<I", body, 0xC8)[0]
    if xml_size <= 0 or xml_size > payload_size or payload_start + xml_size > len(body):
        raise FormatError("IM*H XML payload bounds are invalid")
    payload = body[payload_start : payload_start + xml_size].lstrip()
    if not payload.startswith(b"<"):
        raise FormatError("IM*H inner payload is not XML")
    return payload, "imah"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _safe_filename(value: str) -> str:
    value = value.strip().replace("\\", "/")
    parsed = urlsplit(value)
    candidate = parsed.path if parsed.scheme or parsed.netloc else value.split("?", 1)[0]
    name = PurePosixPath(candidate).name
    if not name or len(name) > 255 or any(ord(char) < 0x20 for char in name):
        return "<invalid-or-empty>"
    return name


def summarize_config(xml_body: bytes, version: str, container: str) -> dict[str, Any]:
    try:
        root = ET.fromstring(xml_body)
    except ET.ParseError as exc:
        raise FormatError(f"configuration XML for {version} could not be parsed") from exc

    modules: list[dict[str, Any]] = []
    for element in root.iter():
        attrs = {str(key): str(value) for key, value in element.attrib.items()}
        if not {"id", "version", "size", "md5"}.issubset(attrs):
            continue
        try:
            size = int(attrs["size"], 10)
        except ValueError:
            size = -1
        filename_value = attrs.get("filename") or "".join(element.itertext()).strip()
        md5_value = attrs["md5"].lower()
        modules.append(
            {
                "module_id": attrs["id"],
                "module_version": attrs["version"],
                "size": size,
                "md5": md5_value if re.fullmatch(r"[0-9a-f]{32}", md5_value) else "<invalid>",
                "filename": _safe_filename(filename_value),
                "group": attrs.get("group", ""),
                "base_sha1": attrs.get("base_sha1", ""),
            }
        )
    if not modules:
        raise FormatError(f"configuration XML for {version} contained no module records")
    return {
        "product_version": version,
        "container": container,
        "module_count": len(modules),
        "total_module_bytes": sum(max(0, module["size"]) for module in modules),
        "modules": modules,
    }


def _public_list_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: entry[key]
        for key in (
            "product_version",
            "released_time",
            "flow",
            "roles",
            "sub_product_types",
        )
        if key in entry
    }


def fetch_metadata(dylib: Path = DEFAULT_DYLIB, timeout: float = 20.0) -> dict[str, Any]:
    _, secret, binary_sha256 = extract_assistant_material(dylib)
    token = ""
    account = ""
    client = AllowlistedMetadataHttp(timeout=timeout)

    list_params = [
        ("product_id", PRODUCT_ID),
        ("token", token),
        ("signature", signature_getallfile(secret, PRODUCT_ID, token)),
        ("account", account),
        ("eng", "false"),
        ("force_update", "true"),
    ]
    list_body = client.get(
        "/getfile/getallfile",
        list_params,
        headers={"x-app-ver": APP_VERSION_HEADER},
        max_bytes=MAX_LIST_BYTES,
    )
    entries = _list_entries(list_body)
    selected = {
        str(entry.get("product_version")): entry
        for entry in entries
        if str(entry.get("product_version")) in TARGET_VERSIONS
    }

    configs: list[dict[str, Any]] = []
    for version in TARGET_VERSIONS:
        if version not in selected:
            configs.append(
                {
                    "product_version": version,
                    "available_in_list": False,
                    "metadata_requested": False,
                }
            )
            continue
        config_params = [
            ("product_version", version),
            ("product_id", PRODUCT_ID),
            ("token", token),
            ("device", "pc"),
            ("signature", signature_download(secret, PRODUCT_ID, version, token)),
            ("account", account),
            ("eng", "false"),
        ]
        try:
            body = client.get(
                "/getfile/download", config_params, max_bytes=MAX_CONFIG_BYTES
            )
        except RedirectRefused as redirect:
            configs.append(
                {
                    "product_version": version,
                    "available_in_list": True,
                    "metadata_requested": True,
                    "xml_retrieved": False,
                    "redirect_refused": {
                        "status": redirect.status,
                        "host": redirect.host,
                        "path": redirect.path,
                        "query": "omitted",
                    },
                }
            )
            continue
        xml_body, container = _extract_config_xml(body)
        summary = summarize_config(xml_body, version, container)
        summary["available_in_list"] = True
        summary["metadata_requested"] = True
        summary["xml_retrieved"] = True
        if client.last_followed_config_redirect:
            summary["config_source"] = client.last_followed_config_redirect
        configs.append(summary)

    # Drop the secret reference before constructing output.  Python cannot
    # guarantee immediate memory zeroization, but no code path serializes it.
    del secret
    return {
        "safety": {
            "mode": "metadata-only",
            "http_method": "GET",
            "api_host_allowlist": [ALLOWED_HOST],
            "config_redirect_host_rule": "HTTPS *.djicdn.com; one redirect; *.pro.cfg.sig only",
            "metadata_paths_used": sorted(METADATA_PATHS),
            "firmware_path_allowlisted_but_blocked": "/getfile/firmware",
            "redirects": "one validated *.djicdn.com config hop; all others refused",
            "device_transport": "absent",
            "upgrade_calls": "absent",
        },
        "assistant_binary": {
            "path": str(dylib),
            "sha256": binary_sha256,
            "embedded_material": "decoded in memory; never emitted",
        },
        "request_fields": {
            "getallfile": [name for name, _ in list_params],
            "download": [
                "product_version",
                "product_id",
                "token",
                "device",
                "signature",
                "account",
                "eng",
            ],
            "redaction": {
                "token": "empty (Assistant not logged in)",
                "account": "empty (Assistant not logged in)",
                "signature": "computed in memory; value omitted",
            },
        },
        "product_id": PRODUCT_ID,
        "target_versions": list(TARGET_VERSIONS),
        "matching_list_entries": [
            _public_list_entry(selected[version])
            for version in TARGET_VERSIONS
            if version in selected
        ],
        "configs": configs,
    }


def self_test(dylib: Path = DEFAULT_DYLIB) -> dict[str, Any]:
    host, secret, binary_sha256 = extract_assistant_material(dylib)
    # Check all recovered formulas without showing their outputs.
    signatures = (
        signature_getallfile(secret, PRODUCT_ID, ""),
        signature_download(secret, PRODUCT_ID, TARGET_VERSIONS[0], ""),
        signature_firmware_evidence_only(
            secret, PRODUCT_ID, TARGET_VERSIONS[0], "0100", "01.00.0000", ""
        ),
    )
    if not all(re.fullmatch(r"[0-9a-f]{32}", value) for value in signatures):
        raise FormatError("signature self-test failed")
    del secret, signatures
    return {
        "ok": True,
        "network_used": False,
        "validated_host": host,
        "assistant_binary_sha256": binary_sha256,
        "embedded_material": "validated but not emitted",
        "firmware_body_path": "blocked",
    }


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--self-test", action="store_true", help="offline extraction test")
    action.add_argument(
        "--fetch-metadata",
        action="store_true",
        help="GET only the wa150 list and 01.00.0600/0700 XML configs",
    )
    parser.add_argument("--dylib", type=Path, default=DEFAULT_DYLIB)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--output", type=Path, help="write the de-identified JSON report")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = (
            self_test(args.dylib)
            if args.self_test
            else fetch_metadata(args.dylib, timeout=args.timeout)
        )
        rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"wrote de-identified report: {args.output}")
        else:
            sys.stdout.write(rendered)
        return 0
    except (FormatError, SafetyError, RuntimeError, OSError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
