"""Probe fixed-WAES arrangements against an IMaH plaintext checksum.

Byte ranges are validated independently through the recorded encrypted-checksum chain (negated
additive form). CTR, CBC and ECB use the Assistant's fixed whitebox block functions directly.
This does not unwrap scram into a new AES key or test the upstream derived-key model. The fixed
whitebox primitive has not been established as the module `STUE` cipher.

All candidates checksum the full decrypted, padded chunk ranges. A checksum hit is a candidate
for further verification, not proof of a valid or flashable firmware image.
"""
from __future__ import annotations

import os
import platform
import struct
import sys
from pathlib import Path

import wb_aes_bridge
from wb_aes_bridge import build_mirror, decrypt_block, encrypt_block


def _reexec_under_rosetta(path: str) -> None:
    if platform.machine() == "x86_64":
        return
    if os.environ.get("FIND_UAS_ROSETTA_REEXEC") == "1":
        raise RuntimeError("Rosetta restart did not select x86_64")
    os.environ["PYTHONHOME"] = sys.base_prefix
    os.environ["FIND_UAS_ROSETTA_REEXEC"] = "1"
    root = build_mirror()
    os.execv("/usr/bin/arch", ["arch", "-x86_64", str(root / "MacOS/Python"),
                             str(Path(__file__).resolve()), path])


def _sum(buf: bytes) -> int:
    padded = buf + bytes((-len(buf)) % 4)
    return sum(word[0] for word in struct.iter_unpack("<I", padded)) & 0xFFFFFFFF


def _checksum(buf: bytes, start: int = 0, negate: bool = False) -> int:
    c = (start + _sum(buf)) & 0xFFFFFFFF
    return (-c) & 0xFFFFFFFF if negate else c


def parse(sig: bytes) -> dict:
    head_size = struct.unpack_from("<I", sig, 16)[0]
    sig_size = struct.unpack_from("<I", sig, 20)[0]
    chunks = []
    for i in range(struct.unpack_from("<I", sig, 156)[0]):
        base = 192 + i * 32
        chunks.append((struct.unpack_from("<I", sig, base + 4)[0],
                       struct.unpack_from("<I", sig, base + 8)[0]))
    return {"head_size": head_size, "sig_size": sig_size,
            "scram": bytes(sig[48:64]),
            "plain_cksum": struct.unpack_from("<I", sig, 152)[0],
            "encr_cksum": struct.unpack_from("<I", sig, 108)[0],
            "chunks": chunks, "header": sig[:192]}


def _encrypted_chunks(sig: bytes, meta: dict) -> list[bytes]:
    chunks = []
    for coff, csize in meta["chunks"]:
        start = meta["head_size"] + meta["sig_size"] + coff
        size = csize + (-csize) % 32
        chunk = sig[start:start + size]
        if len(chunk) != size:
            raise ValueError("truncated encrypted chunk")
        chunks.append(chunk)
    return chunks


def validate_ranges(sig: bytes, meta: dict) -> bool:
    hdr = bytearray(meta["header"]); hdr[108:112] = b"\0\0\0\0"
    c = _checksum(bytes(hdr))
    for i in range(len(meta["chunks"])):
        base = 192 + i * 32
        c = _checksum(sig[base:base + 32], c)
    for chunk in _encrypted_chunks(sig, meta):
        c = _checksum(chunk, c)
    return (-c) & 0xFFFFFFFF == meta["encr_cksum"]


def try_schemes(sig: bytes, meta: dict) -> list[str]:
    chunks = _encrypted_chunks(sig, meta)
    enc = b"".join(chunks)
    n = len(enc) // 16
    hits = []

    # These are fixed-WAES hypotheses, not AES under an unwrapped scram key.
    for s_tag, s_fn in (("e", encrypt_block), ("d", decrypt_block)):
        for order in ("big", "little"):
            ks = b"".join(
                s_fn(b"\0" * 12 + c.to_bytes(4, order)) for c in range(n))
            dec = bytes(a ^ b for a, b in zip(enc, ks))
            if _checksum(dec) == meta["plain_cksum"]:
                hits.append(f"ctr primitive={s_tag} order={order}")
        for iv_tag, iv in (("scram", meta["scram"]), ("zero", bytes(16))):
            dec = bytearray()
            for chunk in chunks:
                prev = iv
                for i in range(0, len(chunk), 16):
                    blk = chunk[i:i + 16]
                    dec += bytes(a ^ b for a, b in zip(s_fn(blk), prev))
                    prev = blk
            if _checksum(bytes(dec)) == meta["plain_cksum"]:
                hits.append(f"cbc primitive={s_tag} iv={iv_tag}")
        dec = b"".join(s_fn(enc[i:i + 16]) for i in range(0, len(enc), 16))
        if _checksum(dec) == meta["plain_cksum"]:
            hits.append(f"ecb primitive={s_tag}")
    return hits


def main(path: str) -> int:
    _reexec_under_rosetta(path)
    sig = Path(path).read_bytes()
    meta = parse(sig)
    if not validate_ranges(sig, meta):
        raise ValueError("encrypted checksum range validation failed")
    print("encrypted checksum range validation: MATCH")
    wb_aes_bridge._ENC, wb_aes_bridge._DEC = wb_aes_bridge.load()
    print("scope: 10 fixed-WAES candidates; derived-key models are not tested")
    hits = try_schemes(sig, meta)
    print("scheme hits:", hits if hits else "NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
