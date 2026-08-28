#!/usr/bin/env python3
"""Create an intentionally non-flashable IMaH integrity probe.

This offline-only helper changes exactly one byte inside an already encrypted
chunk and recomputes only the public payload SHA-256 and IMaH v2 encrypted-data
checksum.  It preserves the original signature bytes and plaintext checksum,
does not decrypt or repack a chunk, and has no device, transfer, upgrade, or
flash interface.  Output names must end in ``.nonflashable.bin``.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

from imah_patchability_audit import (
    DEFAULT_TOOL,
    audit,
    checksum_region,
    checksum_words,
    decode_fourcc,
    load_tool,
    sha256_region,
)


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parent.parent
NONFLASHABLE_SUFFIX = ".nonflashable.bin"


def hash_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        while block := handle.read(4 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_paths(source: Path, output: Path) -> tuple[Path, Path]:
    if source.is_symlink():
        raise ValueError("source must be a regular, non-symlink file")
    source = source.resolve(strict=True)
    output_parent = output.parent.resolve(strict=True)
    output = output_parent / output.name

    if not source.is_file():
        raise ValueError("source must be a regular, non-symlink file")
    if output.name == source.name or output == source:
        raise ValueError("output must be a distinct working copy")
    if not output.name.endswith(NONFLASHABLE_SUFFIX):
        raise ValueError(f"output must end in {NONFLASHABLE_SUFFIX}")
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    if "original" in (part.lower() for part in output.parts):
        raise ValueError("output may not be placed in an original/ directory")
    if is_relative_to(output, REPOSITORY_ROOT.resolve()):
        raise ValueError("vendor-derived output may not be placed in this repository")
    return source, output


def read_layout(source: Path, tool_path: Path):
    tool = load_tool(tool_path)
    with source.open("rb") as handle:
        header = tool.ImgPkgHeader()
        if handle.readinto(header) != tool.sizeof(header):
            raise EOFError("container is shorter than the IMaH header")
        if bytes(header.magic) != b"IM*H":
            raise ValueError("not an IM*H container")
        chunks = []
        chunks_raw = bytearray()
        enc_fourcc = decode_fourcc(bytes(header.enc_key))
        for _ in range(header.chunk_num):
            raw = handle.read(tool.sizeof(tool.ImgChunkHeader))
            if len(raw) != tool.sizeof(tool.ImgChunkHeader):
                raise EOFError("container ended inside the chunk table")
            chunk = tool.ImgChunkHeader.from_buffer_copy(raw)
            chunks_raw.extend(raw)
            chunks.append(
                {
                    "id": decode_fourcc(bytes(chunk.id)),
                    "offset": chunk.offset,
                    "size": chunk.size,
                    "encrypted": not bool(chunk.attrib & 0x01) and bool(enc_fourcc),
                }
            )
        signature = handle.read(header.signature_size)
        if len(signature) != header.signature_size:
            raise EOFError("container ended inside the signature")
    return tool, header, bytes(chunks_raw), chunks, signature


def copy_with_one_byte_xor(source: Path, output: Path, absolute_offset: int, xor_mask: int) -> tuple[int, int]:
    before = None
    after = None
    cursor = 0
    try:
        with source.open("rb") as src, output.open("xb") as dst:
            while block := src.read(4 * 1024 * 1024):
                next_cursor = cursor + len(block)
                if cursor <= absolute_offset < next_cursor:
                    index = absolute_offset - cursor
                    mutable = bytearray(block)
                    before = mutable[index]
                    mutable[index] ^= xor_mask
                    after = mutable[index]
                    block = bytes(mutable)
                dst.write(block)
                cursor = next_cursor
            dst.flush()
            os.fsync(dst.fileno())
    except Exception:
        output.unlink(missing_ok=True)
        raise
    if before is None or after is None:
        output.unlink(missing_ok=True)
        raise EOFError("selected byte is outside the source file")
    return before, after


def create_probe(
    source: Path,
    output: Path,
    payload_offset: int,
    xor_mask: int = 1,
    tool_path: Path = DEFAULT_TOOL,
) -> dict:
    source, output = validate_paths(source, output)
    tool_path = tool_path.resolve(strict=True)
    if tool_path != DEFAULT_TOOL.resolve(strict=True):
        raise ValueError("probe is restricted to the pinned default IMaH parser")
    if not 1 <= xor_mask <= 0xFF:
        raise ValueError("xor mask must be between 1 and 255")

    source_report = audit(source, tool_path)
    if source_report["format_version"] != 2:
        raise ValueError("probe is restricted to IMaH v2")
    if not source_report["payload_digest_matches"] or not source_report["encrypted_checksum_matches"]:
        raise ValueError("source public integrity fields must pass before mutation")
    if source_report["plaintext_bytes_available_without_decryption"]:
        raise ValueError("probe is restricted to encrypted images without directly available plaintext")
    if source_report["candidate_decryption_material_present"]:
        raise ValueError("probe refuses images for which local candidate decryption material exists")
    if source_report["verified_auth_variants"]:
        raise ValueError("probe refuses images with any locally verified authentication key")

    tool, header, chunks_raw, chunks, signature = read_layout(source, tool_path)
    if not 0 <= payload_offset < header.payload_size:
        raise ValueError("payload offset is outside the declared payload")
    selected_chunks = [
        chunk
        for chunk in chunks
        if chunk["offset"] <= payload_offset < chunk["offset"] + chunk["size"]
    ]
    if len(selected_chunks) != 1 or not selected_chunks[0]["encrypted"]:
        raise ValueError("selected offset must fall inside exactly one encrypted chunk, not padding")

    absolute_offset = header.header_size + header.signature_size + payload_offset
    before, after = copy_with_one_byte_xor(source, output, absolute_offset, xor_mask)
    try:
        with output.open("r+b") as handle:
            mutated_payload_digest = sha256_region(
                handle,
                header.header_size + header.signature_size,
                header.payload_size,
            )
            header.payload_digest = (tool.c_ubyte * 32)(*bytes.fromhex(mutated_payload_digest))
            checksum_header = copy.copy(header)
            checksum_header.encr_cksum = 0
            checksum_seed = checksum_words(bytes(checksum_header) + chunks_raw)
            recomputed_encrypted_checksum = checksum_region(
                handle,
                header.header_size + header.signature_size,
                header.payload_size,
                checksum_seed,
            )
            header.encr_cksum = recomputed_encrypted_checksum
            handle.seek(0)
            handle.write(bytes(header))
            handle.flush()
            os.fsync(handle.fileno())

        output_report = audit(output, tool_path)
        _, output_header, _, _, output_signature = read_layout(output, tool_path)
        if output_signature != signature:
            raise AssertionError("safety invariant failed: signature bytes changed")
        if not output_report["payload_digest_matches"] or not output_report["encrypted_checksum_matches"]:
            raise AssertionError("public integrity fields were not recomputed consistently")
        os.chmod(output, 0o444)
    except Exception:
        output.unlink(missing_ok=True)
        raise

    return {
        "classification": "intentionally-corrupted-nonflashable-integrity-probe",
        "source": str(source),
        "output": str(output),
        "source_sha256": source_report["sha256"],
        "output_sha256": output_report["sha256"],
        "source_md5": hash_file(source, "md5"),
        "output_md5": hash_file(output, "md5"),
        "container": {
            "format_version": source_report["format_version"],
            "module": source_report["name"],
            "type": source_report["type"],
            "authentication": source_report["auth_key_fourcc"],
            "encryption": source_report["enc_key_fourcc"],
            "signature_size": source_report["signature_size"],
            "chunk": selected_chunks[0]["id"],
        },
        "mutation": {
            "payload_relative_offset": payload_offset,
            "file_absolute_offset": absolute_offset,
            "xor_mask": f"0x{xor_mask:02x}",
            "before": f"0x{before:02x}",
            "after": f"0x{after:02x}",
        },
        "public_integrity_fields_recomputed": {
            "payload_sha256": mutated_payload_digest,
            "encrypted_checksum": f"0x{recomputed_encrypted_checksum:08x}",
            "payload_digest_matches": output_report["payload_digest_matches"],
            "encrypted_checksum_matches": output_report["encrypted_checksum_matches"],
        },
        "intentionally_not_recomputed": {
            "plaintext_checksum": f"0x{output_header.plain_cksum:08x}",
            "reason": "STUE plaintext is unavailable; a ciphertext change changes unknown plaintext",
            "official_package_md5_or_manifest": True,
            "rsa_pss_signature": True,
        },
        "signature": {
            "bytes_preserved": output_signature == signature,
            "signed_region_sha256_before": source_report["signed_header_and_chunk_table_sha256"],
            "signed_region_sha256_after": output_report["signed_header_and_chunk_table_sha256"],
            "signed_region_changed": (
                source_report["signed_header_and_chunk_table_sha256"]
                != output_report["signed_header_and_chunk_table_sha256"]
            ),
            "verified_public_auth_variants_after": output_report["verified_public_auth_variants"],
            "private_signing_key_available": False,
        },
        "device_network_or_flash_capability": False,
        "safe_flashable_patch_ready": False,
        "blockers": [
            "the changed byte is STUE ciphertext, not a located RID/FC/FlySafe/C0 plaintext field",
            "the plaintext checksum cannot be correctly determined or validated from the current evidence",
            "recomputed public fields changed the RSA-PSS-signed header while the signature stayed unchanged",
            "no matching WA150 public authentication key or private signing key exists in the pinned local corpus",
            "the official package MD5/manifest was deliberately not repaired",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--payload-offset",
        required=True,
        type=lambda value: int(value, 0),
        help="zero-based offset inside the encrypted IMaH payload",
    )
    parser.add_argument(
        "--xor-mask",
        default=1,
        type=lambda value: int(value, 0),
        help="one-byte XOR mask (1..255; default: 1)",
    )
    parser.add_argument("--tool", type=Path, default=DEFAULT_TOOL)
    parser.add_argument(
        "--confirm-nonflashable",
        action="store_true",
        help="required acknowledgement that the output is deliberately invalid and must never be flashed",
    )
    args = parser.parse_args()
    if not args.confirm_nonflashable:
        parser.error("--confirm-nonflashable is required")
    report = create_probe(
        args.source,
        args.output,
        args.payload_offset,
        args.xor_mask,
        args.tool,
    )
    json.dump(report, fp=sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
