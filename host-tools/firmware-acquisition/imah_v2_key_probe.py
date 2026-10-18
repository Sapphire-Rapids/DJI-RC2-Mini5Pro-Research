"""Check one key against the public IMaH-v2 model, without exporting plaintext.

Model reference: o-gs/dji-firmware-tools at
195692263c2684cf1ddc4995f2736be6c0fb135e, dji_imah_fwsig.py.
Matching that model is a hypothesis for STUE, not an established STUE algorithm.
Raw key input is read from stdin; neither the key nor plaintext is printed.
macOS CommonCrypto supplies AES; no third-party Python dependency is required.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import struct
import sys
from pathlib import Path


def aes_ecb(data: bytes, key: bytes, *, decrypt: bool = False) -> bytes:
    if len(key) not in (16, 24, 32) or len(data) % 16:
        raise ValueError("AES requires a 16/24/32-byte key and whole 16-byte blocks")
    if not data:
        return b""
    crypto = ctypes.CDLL("/usr/lib/system/libcommonCrypto.dylib")
    crypt = crypto.CCCrypt
    crypt.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
                      ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                      ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    crypt.restype = ctypes.c_int32
    out = ctypes.create_string_buffer(len(data))
    moved = ctypes.c_size_t()
    # kCCAlgorithmAES=0, kCCOptionECBMode=2, no padding.
    status = crypt(int(decrypt), 0, 2, key, len(key), None, data, len(data),
                   out, len(out), ctypes.byref(moved))
    if status != 0 or moved.value != len(data):
        raise RuntimeError(f"CommonCrypto failed: status={status}, bytes={moved.value}")
    return out.raw


def ctr(data: bytes, key: bytes, counter: int = 0) -> tuple[bytes, int]:
    if len(key) != 16 or len(data) % 16:
        raise ValueError("IMaH-v2 uses a 16-byte content key and whole AES blocks")
    blocks = len(data) // 16
    if counter + blocks > 1 << 32:
        raise ValueError("IMaH-v2 counter exhausted")
    stream = aes_ecb(b"".join(bytes(12) + i.to_bytes(4, "big")
                              for i in range(counter, counter + blocks)), key)
    return bytes(a ^ b for a, b in zip(data, stream)), counter + blocks


def checksum(data: bytes) -> int:
    padded = data + bytes(-len(data) % 4)
    return sum(word[0] for word in struct.iter_unpack("<I", padded)) & 0xFFFFFFFF


def probe(image: bytes, key: bytes, kind: str = "kek") -> dict:
    if image[:4] != b"IM*H" or struct.unpack_from("<I", image, 4)[0] != 2:
        raise ValueError("Expected an IMaH version-2 image")
    header_size, signature_size, payload_size = struct.unpack_from("<III", image, 16)
    count = struct.unpack_from("<I", image, 156)[0]
    if header_size != 192 + 32 * count:
        raise ValueError("Unsupported IMaH header/chunk-table layout")
    payload_start = header_size + signature_size
    payload = image[payload_start:payload_start + payload_size]
    if len(payload) != payload_size:
        raise ValueError("Truncated payload")
    if hashlib.sha256(payload).digest() != image[160:192]:
        raise ValueError("Payload SHA-256 mismatch")
    header = bytearray(image[:header_size])
    header[108:112] = bytes(4)
    encrypted_checksum = (-(checksum(header) + checksum(payload))) & 0xFFFFFFFF
    if encrypted_checksum != struct.unpack_from("<I", image, 108)[0]:
        raise ValueError("Encrypted checksum mismatch")
    if kind == "kek":
        content_key = aes_ecb(image[48:64], key, decrypt=True)
    elif kind == "content":
        if len(key) != 16:
            raise ValueError("Content key must be 16 bytes")
        content_key = key
    else:
        raise ValueError("Key kind must be kek or content")
    counter = 0
    plain_checksum = 0
    logical_digest = hashlib.sha256()
    chunks = []
    for i in range(count):
        offset, size, attributes = struct.unpack_from("<III", image, 192 + 32 * i + 4)
        encrypted = bool(image[44:48].rstrip(b"\0")) and not attributes & 1
        stored_size = size + (-size % 32) if encrypted else size
        data = payload[offset:offset + stored_size]
        if len(data) != stored_size:
            raise ValueError(f"Truncated chunk {i}")
        if encrypted:
            data, counter = ctr(data, content_key, counter)
        plain_checksum = (plain_checksum + checksum(data)) & 0xFFFFFFFF
        logical_digest.update(data[:size])
        chunks.append({"index": i, "logical_size": size, "stored_size": stored_size,
                       "encrypted": encrypted})
    expected = struct.unpack_from("<I", image, 152)[0]
    return {
        "image_sha256": hashlib.sha256(image).hexdigest(),
        "model": "public IMaH-v2 AES-ECB unwrap then AES-CTR; STUE applicability unproven",
        "key_kind": kind, "input_key_sha256": hashlib.sha256(key).hexdigest(),
        "encryption_id": image[44:48].rstrip(b"\0").decode("ascii"),
        "payload_sha256_valid": True, "encrypted_checksum_valid": True,
        "chunks": chunks, "ctr_blocks": counter,
        "expected_plain_checksum": f"0x{expected:08x}",
        "observed_plain_checksum": f"0x{plain_checksum:08x}",
        "checksum_match": plain_checksum == expected,
        "logical_output_sha256": logical_digest.hexdigest(),
        "limit": "A checksum match still requires structural corroboration; no signature verification or device access.",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image", type=Path)
    ap.add_argument("--key-kind", choices=("kek", "content"), default="kek")
    args = ap.parse_args()
    result = probe(args.image.read_bytes(), sys.stdin.buffer.read(), args.key_kind)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
