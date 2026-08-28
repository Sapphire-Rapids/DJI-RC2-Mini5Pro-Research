#!/usr/bin/env python3
"""Single-target DJI Assistant downloader for rc331 10.00.0700/0205.

The only compiled target is the official RC 2 Android OTA candidate
``rc331/10.00.0700/0205``. No product, version, module, URL, filename, output
directory, or metadata-report path can be supplied by the caller. The helper
contains no device transport, cache installation, upgrade call, or extraction
operation.

Assistant request material is reconstructed in memory specifically from the
installed ``libDJIRc2Service.dylib`` and is never printed or persisted.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import secrets
import ssl
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlencode

import dji_official_metadata as metadata
import dji_target_locked_module_download as audited


DownloadSafetyError = audited.DownloadSafetyError
DownloadFormatError = audited.DownloadFormatError
LockedTarget = audited.LockedTarget

API_HOST = "mydjiflight.dji.com"
API_PATH = "/getfile/firmware"
PRODUCT_ID = "rc331"
BASE_DIR = Path(__file__).resolve().parent
SUMMARY_PATH = BASE_DIR / "rc331_metadata_summary.json"
FIRMWARE_ROOT = BASE_DIR / "firmware"
RC2_DYLIB = Path(
    "/Applications/DJI Assistant 2(Consumer Drones Series).app/Contents/"
    "MacOS/DJIServices/libDJIRc2Service.dylib"
)
CHUNK_BYTES = 1024 * 1024

LOCKED_TARGET = LockedTarget(
    product_version="10.00.0700",
    module_id="0205",
    module_version="00.01.14.99",
    filename="rc331_0205_v00.01.14.99_20260609.pro.fw.sig",
    size=985_959_104,
    md5="5c874f6e39819067caa31b67e0ad341b",
)


def _assert_locked_target(target: LockedTarget) -> LockedTarget:
    if target != LOCKED_TARGET:
        raise DownloadSafetyError("operation target differs from the single compiled lock")
    return LOCKED_TARGET


def _destination_for(target: LockedTarget = LOCKED_TARGET) -> Path:
    target = _assert_locked_target(target)
    return (
        FIRMWARE_ROOT
        / PRODUCT_ID
        / target.product_version
        / target.module_id
        / "original"
        / target.filename
    )


def _load_and_validate_target(summary_path: Path | None = None) -> LockedTarget:
    if summary_path is None:
        summary_path = SUMMARY_PATH
    if summary_path != SUMMARY_PATH:
        raise DownloadSafetyError("metadata path differs from the compiled report path")
    try:
        report = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DownloadFormatError("could not read the de-identified rc331 report") from exc
    if not isinstance(report, dict) or report.get("product_id") != PRODUCT_ID:
        raise DownloadFormatError("metadata report is not the expected rc331 report")
    if report.get("target_versions") != ["10.00.0700", "10.00.0800"]:
        raise DownloadSafetyError("metadata report target versions differ from the audit lock")

    matches: list[dict[str, Any]] = []
    configs = report.get("configs")
    if not isinstance(configs, list):
        raise DownloadFormatError("metadata report has no configuration list")
    for config in configs:
        if (
            not isinstance(config, dict)
            or config.get("product_version") != LOCKED_TARGET.product_version
            or config.get("xml_retrieved") is not True
        ):
            continue
        modules = config.get("modules")
        if not isinstance(modules, list):
            continue
        matches.extend(
            module
            for module in modules
            if isinstance(module, dict)
            and module.get("module_id") == LOCKED_TARGET.module_id
        )
    if len(matches) != 1:
        raise DownloadFormatError("metadata report does not contain exactly one locked module")
    observed = matches[0]
    expected_fields = {
        "module_id": LOCKED_TARGET.module_id,
        "module_version": LOCKED_TARGET.module_version,
        "filename": LOCKED_TARGET.filename,
        "size": LOCKED_TARGET.size,
        "md5": LOCKED_TARGET.md5,
    }
    if any(observed.get(key) != value for key, value in expected_fields.items()):
        raise DownloadSafetyError("metadata module differs from the compiled lock record")
    return LOCKED_TARGET


def _tls_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    system_ca_bundle = Path("/etc/ssl/cert.pem")
    if system_ca_bundle.is_file():
        context.load_verify_locations(cafile=str(system_ca_bundle))
    return context


def _validated_firmware_redirect(
    location: str, expected_filename: str
) -> tuple[str, str, str]:
    return audited._validated_firmware_redirect(location, expected_filename)


def _new_hash(name: str) -> Any:
    return audited._new_hash(name)


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
    directory_fd: int, destination: Path, target: LockedTarget
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
            raise DownloadSafetyError("existing destination fails size/MD5 lock")
        os.fchmod(descriptor, 0o444)
        current = os.stat(target.filename, dir_fd=directory_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
            raise DownloadSafetyError("destination changed during verification")
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
        "User-Agent": "DJI-Assistant-rc331-0205-locked-audit/1.0",
    }
    connection = http.client.HTTPSConnection(
        API_HOST, 443, timeout=timeout, context=context
    )
    try:
        try:
            connection.request("GET", private_api_target, headers=headers)
            response = connection.getresponse()
        except (http.client.HTTPException, ValueError):
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

    temporary_name = f".rc331-0205-locked-{secrets.token_hex(16)}.part"
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
                        "User-Agent": "DJI-Assistant-rc331-0205-locked-audit/1.0",
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
                raise DownloadFormatError(
                    "firmware CDN returned invalid Content-Length"
                ) from exc
            if declared_size != target.size:
                raise DownloadSafetyError("firmware Content-Length differs from locked size")
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
            raise DownloadSafetyError("downloaded firmware failed size/MD5 validation")
        verified_descriptor = os.open(
            temporary_name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=output_directory_fd
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
                "cdn_filename": target.filename,
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


def _extract_rc2_material() -> tuple[str, bytes, str]:
    host, secret, binary_sha256 = metadata.extract_assistant_material(RC2_DYLIB)
    if host != f"https://{API_HOST}":
        del secret
        raise DownloadSafetyError("installed RC2 Assistant host differs from the lock")
    return host, secret, binary_sha256


def dry_run() -> dict[str, Any]:
    target = _load_and_validate_target()
    host, secret, binary_sha256 = _extract_rc2_material()
    del secret
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
        "assistant_source": {
            "library": str(RC2_DYLIB),
            "sha256": binary_sha256,
            "validated_host": host,
            "embedded_material": "validated in memory; omitted",
        },
        "network_used": False,
        "device_transport": "absent",
        "upgrade": "absent",
    }


def download_target(timeout: float = 30.0) -> dict[str, Any]:
    target = _load_and_validate_target()
    output_directory_fd, destination = _open_secure_output_dir(target)
    try:
        existing = _verify_existing_at(output_directory_fd, destination, target)
        if existing:
            return existing
        _, secret, _ = _extract_rc2_material()
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


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true", help="offline lock validation")
    action.add_argument(
        "--download",
        action="store_true",
        help="download the one compiled target; never transfers it to a device",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if not 1.0 <= args.timeout <= 300.0:
            raise DownloadSafetyError("timeout is outside the fixed safe range")
        report = dry_run() if args.dry_run else download_target(args.timeout)
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
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
