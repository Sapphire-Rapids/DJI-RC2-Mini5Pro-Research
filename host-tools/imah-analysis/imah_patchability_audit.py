#!/usr/bin/env python3
"""Read-only IMaH patchability audit.

The script parses an IM*H container, checks its encrypted-payload digest, and
tries every public authentication-key variant bundled with the pinned local
dji-firmware-tools checkout.  It never extracts, decrypts, modifies, repacks,
signs, transfers, or flashes firmware.
"""

from __future__ import annotations

import argparse
import array
import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace


# Keep pinned public-source checkouts clean when loading their parser module.
sys.dont_write_bytecode = True


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TOOL_COMMIT = "195692263c2684cf1ddc4995f2736be6c0fb135e"
DEFAULT_TOOL = Path(
    os.environ.get(
        "DJI_FIRMWARE_TOOLS_DIR",
        str(SCRIPT_DIR / "third-party" / "dji-firmware-tools"),
    )
) / "dji_imah_fwsig.py"


def load_tool(path: Path):
    spec = importlib.util.spec_from_file_location("pinned_dji_imah_fwsig", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load IMaH parser: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module.__name__] = module
    spec.loader.exec_module(module)
    return module


def decode_fourcc(value: bytes) -> str:
    return value.rstrip(b"\0").decode("ascii", errors="replace")


def sha256_region(handle, offset: int, size: int) -> str:
    digest = hashlib.sha256()
    handle.seek(offset)
    remaining = size
    while remaining:
        block = handle.read(min(4 * 1024 * 1024, remaining))
        if not block:
            raise EOFError("container ended inside declared payload")
        digest.update(block)
        remaining -= len(block)
    return digest.hexdigest()


def checksum_words(data: bytes, start: int = 0) -> int:
    """DJI IMaH additive little-endian uint32 checksum, before complement."""
    whole = len(data) & ~3
    words = array.array("I")
    words.frombytes(data[:whole])
    if sys.byteorder != "little":
        words.byteswap()
    value = (start + sum(words)) & 0xFFFFFFFF
    if whole != len(data):
        value = (value + int.from_bytes(data[whole:] + b"\0" * (4 - len(data[whole:])), "little")) & 0xFFFFFFFF
    return value


def checksum_region(handle, offset: int, size: int, start: int) -> int:
    handle.seek(offset)
    remaining = size
    value = start
    while remaining:
        block = handle.read(min(4 * 1024 * 1024, remaining))
        if not block:
            raise EOFError("container ended inside declared payload")
        value = checksum_words(block, value)
        remaining -= len(block)
    return (-value) & 0xFFFFFFFF


def dotted_version(value: int) -> str:
    return ".".join(str((value >> shift) & 0xFF) for shift in (24, 16, 8, 0))


def verify_auth_variants(tool, header, chunks_raw: bytes, signature: bytes, source: Path):
    from Crypto.Hash import SHA256
    from Crypto.Signature import PKCS1_v1_5, pss

    auth_fourcc = decode_fourcc(bytes(header.auth_key))
    names = sorted(name for name in tool.keys if name[:4] == auth_fourcc)
    digest = SHA256.new(bytes(header) + chunks_raw)
    verified: list[str] = []
    public_only: list[str] = []

    for name in names:
        opts = SimpleNamespace(
            key_select=[name],
            show_multiple_keys_warn=False,
            sigfile=str(source),
            verbose=0,
        )
        key = tool.imah_get_auth_params(opts, header)
        if key is None:
            continue
        if not key.has_private():
            public_only.append(name)
        if key.size_in_bytes() != len(signature):
            continue
        try:
            if header.header_version >= 2:
                mgf = lambda seed, length: pss.MGF1(seed, length, SHA256)
                pss.new(key, mask_func=mgf, salt_bytes=digest.digest_size).verify(
                    digest, signature
                )
            else:
                if not PKCS1_v1_5.new(key).verify(digest, signature):
                    continue
        except (ValueError, TypeError):
            continue
        verified.append(name)

    return names, public_only, verified


def audit(source: Path, tool_path: Path) -> dict:
    tool = load_tool(tool_path)
    file_size = source.stat().st_size
    whole_digest = hashlib.sha256()
    with source.open("rb") as handle:
        while block := handle.read(4 * 1024 * 1024):
            whole_digest.update(block)

        handle.seek(0)
        header = tool.ImgPkgHeader()
        if handle.readinto(header) != tool.sizeof(header):
            raise EOFError("container is shorter than the IMaH header")
        if bytes(header.magic) != b"IM*H":
            raise ValueError("not an IM*H container")
        if header.header_size != tool.sizeof(header) + header.chunk_num * tool.sizeof(tool.ImgChunkHeader):
            raise ValueError("declared header size does not match chunk table")
        if header.target_size != header.header_size + header.signature_size + header.payload_size:
            raise ValueError("declared target size is inconsistent")
        if header.target_size != file_size:
            raise ValueError("declared target size does not match file size")

        chunks = []
        chunks_raw = bytearray()
        enc_fourcc = decode_fourcc(bytes(header.enc_key))
        for _ in range(header.chunk_num):
            raw = handle.read(tool.sizeof(tool.ImgChunkHeader))
            if len(raw) != tool.sizeof(tool.ImgChunkHeader):
                raise EOFError("container ended inside chunk table")
            chunk = tool.ImgChunkHeader.from_buffer_copy(raw)
            chunks_raw.extend(raw)
            chunks.append(
                {
                    "id": decode_fourcc(bytes(chunk.id)),
                    "offset": chunk.offset,
                    "size": chunk.size,
                    # dji-firmware-tools treats the chunk as plaintext when
                    # either attrib bit 0 is set *or* the package encryption
                    # key id is empty.
                    "encrypted": not bool(chunk.attrib & 0x01) and bool(enc_fourcc),
                    "attributes": f"0x{chunk.attrib:08x}",
                }
            )

        signature = handle.read(header.signature_size)
        if len(signature) != header.signature_size:
            raise EOFError("container ended inside header signature")
        payload_offset = header.header_size + header.signature_size
        payload_sha256 = sha256_region(handle, payload_offset, header.payload_size)
        checksum_header = copy.copy(header)
        checksum_header.encr_cksum = 0
        checksum_seed = checksum_words(bytes(checksum_header) + bytes(chunks_raw))
        encrypted_checksum = checksum_region(
            handle, payload_offset, header.payload_size, checksum_seed
        )

    auth_names, public_only, verified = verify_auth_variants(
        tool, header, bytes(chunks_raw), signature, source
    )
    private_auth = sorted(
        name
        for name in auth_names
        if isinstance(tool.keys[name], str) and "PRIVATE KEY" in tool.keys[name]
    )
    verified_public_auth = sorted(name for name in verified if name in public_only)
    verified_private_auth = sorted(name for name in private_auth if name in verified)
    signed_header_sha256 = hashlib.sha256(bytes(header) + bytes(chunks_raw)).hexdigest()
    enc_names = sorted(name for name in tool.keys if name[:4] == enc_fourcc)
    encrypted_chunks = sum(1 for chunk in chunks if chunk["encrypted"])
    plaintext_bytes_available_without_decryption = encrypted_chunks == 0
    plaintext_checksum_verified = False
    payload_digest_matches = payload_sha256 == bytes(header.payload_digest).hex()
    encrypted_checksum_matches = encrypted_checksum == header.encr_cksum

    reasons = []
    if not payload_digest_matches:
        reasons.append("stored payload SHA-256 does not match the current payload")
    if not encrypted_checksum_matches:
        reasons.append("stored encrypted-data checksum does not match the current container")
    if encrypted_chunks and not enc_names:
        reasons.append(f"no pinned public {enc_fourcc or '[empty]'} decryption-key variant")
    elif encrypted_chunks:
        reasons.append(
            "matching encryption-key labels exist, but this read-only audit does not "
            "claim verified plaintext without a successful decrypt-and-checksum pass"
        )
    if not verified:
        reasons.append("no pinned public authentication key verifies this header")
    if not verified_private_auth:
        reasons.append("no verified matching private signing key exists in the pinned key corpus")
    reasons.append("any payload change requires new digest/checksum fields in the signed header")

    return {
        "source": str(source),
        "sha256": whole_digest.hexdigest(),
        "size": file_size,
        "format_version": header.header_version,
        "anti_version": header.anti_version,
        "firmware_version": dotted_version(header.version),
        "build_date_bcd_hex": f"{header.date:08x}",
        "name": decode_fourcc(bytes(header.name)),
        "type": decode_fourcc(bytes(header.type)),
        "auth_key_fourcc": decode_fourcc(bytes(header.auth_key)),
        "enc_key_fourcc": enc_fourcc,
        "signature_size": header.signature_size,
        "header_size": header.header_size,
        "payload_offset": header.header_size + header.signature_size,
        "payload_size": header.payload_size,
        "payload_sha256_computed": payload_sha256,
        "payload_sha256_declared": bytes(header.payload_digest).hex(),
        "payload_digest_matches": payload_digest_matches,
        "encrypted_checksum_declared": f"0x{header.encr_cksum:08x}",
        "encrypted_checksum_computed": f"0x{encrypted_checksum:08x}",
        "encrypted_checksum_matches": encrypted_checksum_matches,
        "plaintext_checksum_declared": f"0x{header.plain_cksum:08x}",
        "plaintext_checksum_verified": plaintext_checksum_verified,
        "signed_header_and_chunk_table_sha256": signed_header_sha256,
        "encrypted_scramble_material_sha256": hashlib.sha256(bytes(header.scram_key)).hexdigest(),
        "chunks": chunks,
        "matching_auth_variants": auth_names,
        "matching_public_only_auth_variants": public_only,
        "verified_auth_variants": verified,
        "verified_public_auth_variants": verified_public_auth,
        "matching_private_auth_variants": private_auth,
        "verified_private_auth_variants": verified_private_auth,
        "matching_encryption_variants": enc_names,
        "candidate_decryption_material_present": bool(enc_names),
        "plaintext_bytes_available_without_decryption": plaintext_bytes_available_without_decryption,
        "verified_plaintext_available": (
            plaintext_bytes_available_without_decryption and plaintext_checksum_verified
        ),
        "repack_signing_key_available": bool(verified_private_auth),
        "safe_flashable_patch_ready": False,
        "blockers": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--tool", type=Path, default=DEFAULT_TOOL)
    args = parser.parse_args()

    reports = [audit(path.resolve(), args.tool.resolve()) for path in args.images]
    json.dump(reports, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
