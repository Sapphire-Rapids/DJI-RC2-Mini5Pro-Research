#!/usr/bin/env python3
"""Target-locked, download-only DJI module fetcher for five wa150 artifacts.

This utility can fetch only the two versions of modules 0802/2603 plus the
single package-identical 0806 candidate from wa150 01.00.0700. Expected
filenames, sizes, and MD5 values are compiled into the program and must also
match the de-identified metadata report. It contains no device transport,
upgrade, cache-install, or generic URL capability.

The Assistant application material is reconstructed in memory from the
installed libDJIUavService.dylib.  It is never printed or persisted.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import re
import secrets
import ssl
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence
from urllib.parse import unquote, urlencode, urlsplit

import dji_official_metadata as metadata


API_HOST = "mydjiflight.dji.com"
API_PATH = "/getfile/firmware"
PRODUCT_ID = "wa150"
BASE_DIR = Path(__file__).resolve().parent
SUMMARY_PATH = BASE_DIR / "wa150_metadata_summary.json"
FIRMWARE_ROOT = BASE_DIR / "firmware"
CHUNK_BYTES = 1024 * 1024


class DownloadSafetyError(RuntimeError):
    """Raised before or during any operation outside the fixed boundary."""


class DownloadFormatError(RuntimeError):
    """Raised when the official metadata or response shape is unexpected."""


@dataclass(frozen=True)
class LockedTarget:
    product_version: str
    module_id: str
    module_version: str
    filename: str
    size: int
    md5: str


LOCKED_TARGETS: Mapping[tuple[str, str], LockedTarget] = {
    ("01.00.0600", "0802"): LockedTarget(
        "01.00.0600",
        "0802",
        "10.00.12.83",
        "wa150_0802_v10.00.12.83_20260424.ar1.pro.fw.sig",
        679_368_672,
        "91cf041e95424215fd84b4daa5d86546",
    ),
    ("01.00.0600", "2603"): LockedTarget(
        "01.00.0600",
        "2603",
        "01.00.00.01",
        "wa150_2603_v01.00.00.01_20260129_uc6580.pro.fw.sig",
        436_000,
        "4012b4aa83c88b457101a05876550a35",
    ),
    ("01.00.0700", "0802"): LockedTarget(
        "01.00.0700",
        "0802",
        "10.00.15.17",
        "wa150_0802_v10.00.15.17_20260723.ar2.pro.fw.sig",
        679_295_296,
        "998d1f1448e8f4cddc3269c2c7549f65",
    ),
    ("01.00.0700", "2603"): LockedTarget(
        "01.00.0700",
        "2603",
        "01.05.03.01",
        "wa150_2603_v01.05.03.01_20260508_uc6580.pro.fw.sig",
        437_312,
        "aabd0ec7683bb1d2af4b2f48a561f725",
    ),
    ("01.00.0700", "0806"): LockedTarget(
        "01.00.0700",
        "0806",
        "00.38.20.18",
        "wa150_0806_v00.38.20.18_20251107_4GG4CN.pro.fw.sig",
        12_251_264,
        "8313cb445976a6a47343f3c6e13a6fa4",
    ),
}


def _assert_locked_target(target: LockedTarget) -> LockedTarget:
    expected = LOCKED_TARGETS.get((target.product_version, target.module_id))
    if expected is None or target != expected:
        raise DownloadSafetyError("operation target differs from the compiled lock record")
    return expected


def _destination_for(target: LockedTarget) -> Path:
    target = _assert_locked_target(target)
    return (
        FIRMWARE_ROOT
        / PRODUCT_ID
        / target.product_version
        / target.module_id
        / "original"
        / target.filename
    )


def _load_and_validate_target(
    product_version: str, module_id: str, summary_path: Path = SUMMARY_PATH
) -> LockedTarget:
    expected = LOCKED_TARGETS.get((product_version, module_id))
    if expected is None:
        raise DownloadSafetyError("requested product/module pair is not target-locked")
    try:
        report = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DownloadFormatError("could not read the de-identified metadata report") from exc
    if not isinstance(report, dict) or report.get("product_id") != PRODUCT_ID:
        raise DownloadFormatError("metadata report is not the expected wa150 report")

    matches: list[dict[str, Any]] = []
    configs = report.get("configs")
    if not isinstance(configs, list):
        raise DownloadFormatError("metadata report has no configuration list")
    for config in configs:
        if not isinstance(config, dict) or config.get("product_version") != product_version:
            continue
        modules = config.get("modules")
        if not isinstance(modules, list):
            continue
        matches.extend(
            module
            for module in modules
            if isinstance(module, dict) and module.get("module_id") == module_id
        )
    if len(matches) != 1:
        raise DownloadFormatError("metadata report does not contain exactly one target module")
    observed = matches[0]
    expected_fields = {
        "module_id": expected.module_id,
        "module_version": expected.module_version,
        "filename": expected.filename,
        "size": expected.size,
        "md5": expected.md5,
    }
    if any(observed.get(key) != value for key, value in expected_fields.items()):
        raise DownloadSafetyError("metadata target differs from the compiled lock record")
    return expected


def _tls_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    system_ca_bundle = Path("/etc/ssl/cert.pem")
    if system_ca_bundle.is_file():
        context.load_verify_locations(cafile=str(system_ca_bundle))
    return context


def _validated_firmware_redirect(
    location: str, expected_filename: str
) -> tuple[str, str, str]:
    """Return host, private request target, and public path for one CDN hop."""

    if (
        not location
        or len(location) > 8192
        or any(ord(char) < 0x21 or ord(char) > 0x7E for char in location)
        or re.search(r"%(?![0-9a-fA-F]{2})", location)
    ):
        raise DownloadSafetyError("firmware redirect failed the CDN allowlist")
    parsed = urlsplit(location)
    host = (parsed.hostname or "").lower()
    decoded_path = unquote(parsed.path)
    path_parts = PurePosixPath(decoded_path).parts
    valid_host = bool(
        re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)*\.djicdn\.com", host)
    )
    valid_path = (
        parsed.path.startswith("/")
        and not parsed.path.startswith("//")
        and not decoded_path.startswith("//")
        and "\\" not in decoded_path
        and ".." not in path_parts
        and PurePosixPath(decoded_path).name == expected_filename
        and expected_filename.endswith(".pro.fw.sig")
    )
    try:
        port = parsed.port
    except ValueError as exc:
        raise DownloadSafetyError("firmware redirect failed the CDN allowlist") from exc
    if (
        parsed.scheme != "https"
        or not valid_host
        or not valid_path
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or parsed.fragment
    ):
        raise DownloadSafetyError("firmware redirect failed the CDN allowlist")
    private_target = parsed.path + (("?" + parsed.query) if parsed.query else "")
    return host, private_target, parsed.path


def _new_hash(name: str) -> Any:
    if name == "md5":
        try:
            return hashlib.md5(usedforsecurity=False)
        except TypeError:  # pragma: no cover - older Python compatibility
            return hashlib.md5()
    return hashlib.new(name)


def _hash_fd(descriptor: int) -> tuple[int, str, str]:
    os.lseek(descriptor, 0, os.SEEK_SET)
    size = 0
    md5 = _new_hash("md5")
    sha256 = _new_hash("sha256")
    while chunk := os.read(descriptor, CHUNK_BYTES):
        size += len(chunk)
        md5.update(chunk)
        sha256.update(chunk)
    return size, md5.hexdigest(), sha256.hexdigest()


def _open_secure_output_dir(target: LockedTarget) -> tuple[int, Path]:
    """Open the fixed output directory without following any symlink.

    All later file operations use the returned directory descriptor, closing
    the parent-symlink and TOCTOU escape that path-based publication would
    otherwise create.
    """

    target = _assert_locked_target(target)
    if FIRMWARE_ROOT != BASE_DIR / "firmware":
        raise DownloadSafetyError("firmware root differs from the compiled location")
    segments = (
        "firmware",
        PRODUCT_ID,
        target.product_version,
        target.module_id,
        "original",
    )
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    current = os.open(BASE_DIR, flags)
    try:
        for segment in segments:
            if not segment or segment in {".", ".."} or "/" in segment or "\\" in segment:
                raise DownloadSafetyError("invalid compiled output path segment")
            try:
                os.mkdir(segment, mode=0o755, dir_fd=current)
            except FileExistsError:
                pass
            try:
                child = os.open(segment, flags, dir_fd=current)
            except OSError as exc:
                raise DownloadSafetyError(
                    "fixed output directory is not a symlink-free directory chain"
                ) from exc
            os.close(current)
            current = child
        return current, _destination_for(target)
    except BaseException:
        os.close(current)
        raise


def _verify_existing_at(
    directory_fd: int,
    destination: Path,
    target: LockedTarget,
) -> dict[str, Any] | None:
    target = _assert_locked_target(target)
    if destination != _destination_for(target):
        raise DownloadSafetyError("destination differs from the compiled output path")
    try:
        descriptor = os.open(
            target.filename, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd
        )
    except FileNotFoundError:
        return None
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise DownloadSafetyError("destination exists but is not a regular file")
        size, md5, sha256 = _hash_fd(descriptor)
        if size != target.size or md5 != target.md5:
            raise DownloadSafetyError(
                "existing destination fails the official size/MD5 lock"
            )
        os.fchmod(descriptor, 0o444)
        current = os.stat(target.filename, dir_fd=directory_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
            raise DownloadSafetyError("destination changed while it was being verified")
    finally:
        os.close(descriptor)
    return {
        "status": "already-present-and-verified",
        "path": str(destination),
        "size": size,
        "md5": md5,
        "sha256": sha256,
    }


def _request_redirect(
    target: LockedTarget, secret: bytes, timeout: float, context: ssl.SSLContext
) -> tuple[str, str, str]:
    target = _assert_locked_target(target)
    token = ""
    account = ""
    signature = metadata.signature_firmware_evidence_only(
        secret,
        PRODUCT_ID,
        target.product_version,
        target.module_id,
        target.module_version,
        token,
    )
    params = (
        ("module_version", target.module_version),
        ("product_version", target.product_version),
        ("module_id", target.module_id),
        ("token", token),
        ("product_id", PRODUCT_ID),
        ("filename", target.filename),
        ("signature", signature),
        ("account", account),
    )
    private_api_target = API_PATH + "?" + urlencode(params)
    headers = {
        "Accept": "application/octet-stream, application/pgp-signature",
        "Accept-Encoding": "identity",
        "Connection": "close",
        "User-Agent": "DJI-Assistant-target-locked-audit/1.0",
    }
    connection = http.client.HTTPSConnection(
        API_HOST, 443, timeout=timeout, context=context
    )
    try:
        try:
            connection.request("GET", private_api_target, headers=headers)
            response = connection.getresponse()
        except (http.client.HTTPException, ValueError) as exc:
            raise DownloadFormatError(
                "official firmware API rejected the sanitized request"
            ) from None
        if response.status != 302:
            raise DownloadFormatError(
                f"official firmware endpoint returned HTTP {response.status}; expected 302"
            )
        location = response.getheader("Location") or ""
        return _validated_firmware_redirect(location, target.filename)
    finally:
        connection.close()
        del signature, private_api_target


def _stream_cdn(
    host: str,
    private_target: str,
    public_path: str,
    target: LockedTarget,
    destination: Path,
    output_directory_fd: int,
    timeout: float,
    context: ssl.SSLContext,
) -> dict[str, Any]:
    target = _assert_locked_target(target)
    if destination != _destination_for(target):
        raise DownloadSafetyError("destination differs from the compiled output path")
    checked_host, checked_target, checked_path = _validated_firmware_redirect(
        f"https://{host}{private_target}", target.filename
    )
    if (host, private_target, public_path) != (
        checked_host,
        checked_target,
        checked_path,
    ):
        raise DownloadSafetyError("CDN request differs from the validated redirect")
    temporary_name = f".target-locked-{secrets.token_hex(16)}.part"
    descriptor = os.open(
        temporary_name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=output_directory_fd,
    )
    md5 = _new_hash("md5")
    sha256 = _new_hash("sha256")
    size = 0
    connection = http.client.HTTPSConnection(
        host, 443, timeout=timeout, context=context
    )
    try:
        with os.fdopen(descriptor, "wb") as output:
            descriptor = -1
            try:
                connection.request(
                    "GET",
                    private_target,
                    headers={
                        "Accept": "application/octet-stream, application/pgp-signature",
                        "Accept-Encoding": "identity",
                        "Connection": "close",
                        "User-Agent": "DJI-Assistant-target-locked-audit/1.0",
                    },
                )
                response = connection.getresponse()
            except (http.client.HTTPException, ValueError):
                raise DownloadFormatError(
                    "official firmware CDN rejected the sanitized request"
                ) from None
            if 300 <= response.status < 400:
                raise DownloadSafetyError("a second firmware redirect was refused")
            if response.status != 200:
                raise DownloadFormatError(
                    f"official firmware CDN returned HTTP {response.status}"
                )
            media_type = (response.getheader("Content-Type") or "").split(";", 1)[0].lower()
            if media_type not in {
                "application/octet-stream",
                "binary/octet-stream",
                "application/x-download",
                "application/pgp-signature",
            }:
                raise DownloadFormatError(
                    f"unexpected firmware Content-Type {media_type or '<missing>'!r}"
                )
            declared = response.getheader("Content-Length")
            try:
                declared_size = int(declared) if declared is not None else -1
            except ValueError as exc:
                raise DownloadFormatError("firmware CDN returned invalid Content-Length") from exc
            if declared_size != target.size:
                raise DownloadSafetyError("firmware Content-Length differs from the locked size")
            while chunk := response.read(CHUNK_BYTES):
                size += len(chunk)
                if size > target.size:
                    raise DownloadSafetyError("firmware body exceeded the locked size")
                output.write(chunk)
                md5.update(chunk)
                sha256.update(chunk)
            output.flush()
            os.fsync(output.fileno())
        if size != target.size or md5.hexdigest() != target.md5:
            raise DownloadSafetyError("downloaded firmware failed official size/MD5 validation")
        verified_descriptor = os.open(
            temporary_name,
            os.O_RDONLY | os.O_NOFOLLOW,
            dir_fd=output_directory_fd,
        )
        try:
            os.fchmod(verified_descriptor, 0o444)
        finally:
            os.close(verified_descriptor)
        try:
            os.link(
                temporary_name,
                target.filename,
                src_dir_fd=output_directory_fd,
                dst_dir_fd=output_directory_fd,
                follow_symlinks=False,
            )
        except FileExistsError:
            existing = _verify_existing_at(output_directory_fd, destination, target)
            if existing is None:  # pragma: no cover - race defense
                raise DownloadSafetyError("destination changed during atomic publish")
            return existing
        finally:
            try:
                os.unlink(temporary_name, dir_fd=output_directory_fd)
            except FileNotFoundError:
                pass
        return {
            "status": "downloaded-and-verified",
            "path": str(destination),
            "size": size,
            "md5": md5.hexdigest(),
            "sha256": sha256.hexdigest(),
            "source": {
                "api_host": API_HOST,
                "api_path": API_PATH,
                "cdn_host": host,
                "cdn_path": public_path,
                "cdn_query": "omitted",
                "redirect_count": 1,
            },
        }
    except http.client.HTTPException:
        raise DownloadFormatError(
            "official firmware CDN response failed after the sanitized request"
        ) from None
    finally:
        connection.close()
        if descriptor >= 0:
            os.close(descriptor)
        try:
            os.unlink(temporary_name, dir_fd=output_directory_fd)
        except FileNotFoundError:
            pass


def download_target(
    product_version: str, module_id: str, timeout: float = 30.0
) -> dict[str, Any]:
    target = _load_and_validate_target(product_version, module_id)
    output_directory_fd, destination = _open_secure_output_dir(target)
    try:
        existing = _verify_existing_at(output_directory_fd, destination, target)
        if existing:
            return existing
        host, secret, _ = metadata.extract_assistant_material()
        if host != f"https://{API_HOST}":
            raise DownloadSafetyError("installed Assistant API host differs from the lock")
        context = _tls_context()
        try:
            cdn_host, private_target, public_path = _request_redirect(
                target, secret, timeout, context
            )
        finally:
            del secret
        try:
            return _stream_cdn(
                cdn_host,
                private_target,
                public_path,
                target,
                destination,
                output_directory_fd,
                timeout,
                context,
            )
        finally:
            del private_target
    finally:
        os.close(output_directory_fd)


def _dry_run_report(target: LockedTarget) -> dict[str, Any]:
    target = _assert_locked_target(target)
    return {
        "status": "validated-dry-run-no-network",
        "product_id": PRODUCT_ID,
        "product_version": target.product_version,
        "module_id": target.module_id,
        "module_version": target.module_version,
        "filename": target.filename,
        "expected_size": target.size,
        "expected_md5": target.md5,
        "destination": str(_destination_for(target)),
        "device_transport": "absent",
        "upgrade": "absent",
    }


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, choices=("01.00.0600", "01.00.0700"))
    parser.add_argument("--module", required=True, choices=("0802", "0806", "2603"))
    parser.add_argument("--dry-run", action="store_true", help="validate locks without network")
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if not 1.0 <= args.timeout <= 300.0:
            raise DownloadSafetyError("timeout is outside the fixed safe range")
        target = _load_and_validate_target(args.version, args.module)
        report = (
            _dry_run_report(target)
            if args.dry_run
            else download_target(args.version, args.module, args.timeout)
        )
        report.update(
            {
                "product_id": PRODUCT_ID,
                "product_version": target.product_version,
                "module_id": target.module_id,
                "module_version": target.module_version,
                "filename": target.filename,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (
        DownloadSafetyError,
        DownloadFormatError,
        metadata.SafetyError,
        metadata.FormatError,
        http.client.HTTPException,
        OSError,
        RuntimeError,
    ) as exc:
        print(f"error: {exc}", file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
