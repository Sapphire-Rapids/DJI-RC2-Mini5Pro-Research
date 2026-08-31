"""Verify existing cloud-policy envelopes with an externally supplied P-256 key.

The signed message is the complete20-byte header and declared body; the existing
64-byte trailer holds big-endian r||s. Only ECDSA/P-256/SHA-256 verification is
performed. This module has no signing, editing, network or device operation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

import rid_cloud_payload_envelope as envelope


MAX_PUBLIC_KEY_BYTES = 4096
OPENSSL_TIMEOUT_SECONDS = 5
P256_ORDER = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
P256_ALGORITHM_DER = bytes.fromhex("301306072a8648ce3d020106082a8648ce3d030107")


class Invalid(ValueError):
    """Error messages are fixed codes and never include subprocess output."""


def raw_signature_to_der(raw: bytes) -> bytes:
    """Re-encode the two existing unsigned scalars; create no new signature."""
    if type(raw) is not bytes or len(raw) != 64:
        raise Invalid("SIGNATURE_LENGTH")
    encoded = bytearray()
    for half in (raw[:32], raw[32:]):
        value = int.from_bytes(half, "big")
        if not 0 < value < P256_ORDER:
            raise Invalid("SIGNATURE_SCALAR_RANGE")
        integer = half.lstrip(b"\0")
        if integer[0] & 0x80:
            integer = b"\0" + integer
        encoded.extend(bytes((2, len(integer))) + integer)
    return bytes((0x30, len(encoded))) + bytes(encoded)


def _openssl(args: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["openssl", *args], stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=OPENSSL_TIMEOUT_SECONDS, check=False)
    except FileNotFoundError:
        raise Invalid("OPENSSL_UNAVAILABLE") from None
    except subprocess.TimeoutExpired:
        raise Invalid("OPENSSL_TIMEOUT") from None
    except OSError:
        raise Invalid("OPENSSL_EXECUTION_FAILED") from None


def _p256_spki(der: bytes) -> bool:
    # OpenSSL emits canonical SPKI. Accept named P-256 with a compressed or
    # uncompressed SEC1 point; do not infer a curve from key length alone.
    for point_bytes, tags in ((65, (4,)), (33, (2, 3))):
        prefix = bytes((0x30, 24 + point_bytes)) + P256_ALGORITHM_DER + bytes((3, 1 + point_bytes, 0))
        if len(der) == len(prefix) + point_bytes and der.startswith(prefix) and der[len(prefix)] in tags:
            return True
    return False


def _prepare_key(public_key_pem: bytes, path: Path) -> None:
    if type(public_key_pem) is not bytes or not public_key_pem:
        raise Invalid("PUBLIC_KEY_REQUIRED")
    if len(public_key_pem) > MAX_PUBLIC_KEY_BYTES:
        raise Invalid("PUBLIC_KEY_LIMIT")
    # The file and directory are temporary local inputs, never report artifacts.
    with path.open("xb") as stream:
        stream.write(public_key_pem)
    path.chmod(0o600)
    result = _openssl(["pkey", "-pubin", "-in", str(path), "-pubout", "-outform", "DER"])
    if result.returncode != 0:
        raise Invalid("PUBLIC_KEY_PARSE_FAILED")
    if not _p256_spki(result.stdout):
        raise Invalid("PUBLIC_KEY_NOT_NAMED_P256")
    if len(result.stdout) == 59:
        # Some platform LibreSSL verifiers cannot consume compressed points.
        # Normalize only the supplied public key, never the captured message.
        normalized = path.with_suffix(".uncompressed.pem")
        converted = _openssl(["ec", "-pubin", "-in", str(path), "-pubout",
                              "-conv_form", "uncompressed", "-out", str(normalized)])
        if converted.returncode != 0:
            raise Invalid("PUBLIC_KEY_NORMALIZATION_FAILED")
        normalized.chmod(0o600)
        normalized.replace(path)


def _verify(data: bytes, key_path: Path, directory: Path, label: str) -> dict:
    try:
        structure = envelope.analyze_bytes(data)
    except envelope.Invalid as error:
        raise Invalid(str(error)) from None
    report = {
        "algorithm": "ECDSA_P256_SHA256",
        "total_bytes": len(data),
        "header_bytes": structure["header"]["bytes"],
        "body_bytes": structure["body"]["bytes"],
        "signed_bytes": len(data) - envelope.TRAILER_BYTES,
        "signature_bytes": envelope.TRAILER_BYTES,
        "signature_scalar_range_valid": False,
        "verified_with_supplied_key": False,
        "verification_ran": False,
    }
    try:
        der = raw_signature_to_der(data[-envelope.TRAILER_BYTES:])
    except Invalid:
        return report
    report["signature_scalar_range_valid"] = True
    message_path = directory / (label + ".message")
    signature_path = directory / (label + ".der")
    message_path.write_bytes(data[:-envelope.TRAILER_BYTES])
    signature_path.write_bytes(der)
    result = _openssl(["dgst", "-sha256", "-verify", str(key_path),
                       "-signature", str(signature_path), str(message_path)])
    if result.returncode not in (0, 1):
        raise Invalid("OPENSSL_VERIFICATION_FAILED")
    report["verification_ran"] = True
    report["verified_with_supplied_key"] = result.returncode == 0
    return report


def verify_bytes(data: bytes, public_key_pem: bytes) -> dict:
    with tempfile.TemporaryDirectory(prefix="finduas-policy-verify-") as temporary:
        directory = Path(temporary)
        key_path = directory / "verification.pem"
        _prepare_key(public_key_pem, key_path)
        return _verify(data, key_path, directory, "existing")


def verify_capture(capture: dict, public_key_pem: bytes) -> dict:
    # Reuse the envelope module's bounded hex and presence/metadata validation.
    try:
        state = envelope.analyze_capture(capture)
        matched = envelope.strict_hex(capture["matched_hex"])
        default = envelope.strict_hex(capture["default_hex"]) if capture.get("default_hex") is not None else None
    except envelope.Invalid as error:
        raise Invalid(str(error)) from None
    with tempfile.TemporaryDirectory(prefix="finduas-policy-verify-") as temporary:
        directory = Path(temporary)
        key_path = directory / "verification.pem"
        _prepare_key(public_key_pem, key_path)
        result = {
            "schema": "finduas-cloud-policy-signature/v1",
            "matched": _verify(matched, key_path, directory, "matched"),
            "default_state": state["default_state"],
        }
        if default:
            result["default"] = _verify(default, key_path, directory, "default")
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", type=Path, help="private existing matched/DEFAULT capture JSON")
    parser.add_argument("--public-key", type=Path, required=True, help="externally supplied P-256 verification PEM")
    args = parser.parse_args(argv)
    try:
        with args.input.open("rb") as stream:
            raw = stream.read(envelope.MAX_CAPTURE_BYTES + 1)
        if len(raw) > envelope.MAX_CAPTURE_BYTES:
            raise Invalid("CAPTURE_LIMIT")
        capture = json.loads(raw, object_pairs_hook=envelope._strict_object,
                             parse_constant=envelope._reject_constant)
        with args.public_key.open("rb") as stream:
            public_key = stream.read(MAX_PUBLIC_KEY_BYTES + 1)
        result = verify_capture(capture, public_key)
    except (Invalid, envelope.Invalid, ValueError, KeyError, TypeError, OSError, RecursionError):
        print("signature verification failed: invalid input or verifier unavailable")
        return 2
    print(json.dumps(result, sort_keys=True))
    verified = [value["verified_with_supplied_key"] for key, value in result.items() if key in ("matched", "default")]
    return 0 if all(verified) else 1


if __name__ == "__main__":
    raise SystemExit(main())
