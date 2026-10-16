"""Try IMaH `STUE` decryption with DJI Assistant's baked whitebox AES.

Byte ranges are validated independently through the recorded encrypted-checksum chain (negated
additive form). `STUE` has no entry in the public key corpus, so this probe borrows the Assistant
whitebox AES as the cipher primitive and enumerates the scheme variants the pinned tool supports.

It is a probe, not yet a verified decrypt: success is only the decrypted plaintext checksum.
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
    root = build_mirror()
    os.environ["PYTHONHOME"] = sys.base_prefix
    os.execv(str(root / "MacOS/Python"), [str(root / "MacOS/Python"), __file__, path])


import numpy as _np


def _sum(buf: bytes) -> int:
    return int(_np.frombuffer(buf, dtype="<u4").sum(dtype=_np.uint64)) & 0xFFFFFFFF


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


def validate_ranges(sig: bytes, meta: dict) -> bool:
    hdr = bytearray(meta["header"]); hdr[108:112] = b"\0\0\0\0"
    c = _checksum(bytes(hdr))
    for i in range(len(meta["chunks"])):
        base = 192 + i * 32
        c = _checksum(sig[base:base + 32], c)
    enc = bytearray()
    for coff, csize in meta["chunks"]:
        start = meta["head_size"] + meta["sig_size"] + coff
        pad = (32 - csize % 32) % 32
        enc += sig[start:start + csize + pad]
    return _checksum(bytes(enc), c, negate=True) == meta["encr_cksum"]


def try_schemes(sig: bytes, meta: dict) -> list[str]:
    enc = bytearray()
    for coff, csize in meta["chunks"]:
        start = meta["head_size"] + meta["sig_size"] + coff
        pad = (32 - csize % 32) % 32
        enc += sig[start:start + csize + pad]
    enc = bytes(enc)
    n = (len(enc) + 15) // 16
    hits = []

    def trim(dec: bytes) -> bytes:
        out = bytearray(); p = 0
        for _, csize in meta["chunks"]:
            out += dec[p:p + csize]; p += csize + (32 - csize % 32) % 32
        return bytes(out)

    # keystreams do not depend on the crypt key: build once
    streams = {}
    for s_tag, s_fn in (("e", encrypt_block), ("d", decrypt_block)):
        for order in ("big", "little"):
            streams[(s_tag, order)] = b"".join(
                s_fn(b"\0" * 12 + c.to_bytes(4, order)) for c in range(n))

    for ck_tag, ck_fn in (("d", decrypt_block), ("e", encrypt_block)):
        ck = ck_fn(meta["scram"])
        for (s_tag, order), ks in streams.items():
            dec = bytes(a ^ b for a, b in zip(enc, ks))
            if _checksum(trim(dec)) == meta["plain_cksum"]:
                hits.append(f"ctr ck={ck_tag} stream={s_tag} order={order}")
        for s_tag, s_fn in (("e", encrypt_block), ("d", decrypt_block)):
            for iv_tag, iv in (("scram", meta["scram"]), ("zero", bytes(16))):
                prev, dec = iv, bytearray()
                for i in range(0, len(enc), 16):
                    blk = enc[i:i + 16]
                    dec += bytes(a ^ b for a, b in zip(s_fn(blk), prev)); prev = blk
                if _checksum(bytes(dec)) == meta["plain_cksum"]:
                    hits.append(f"cbc ck={ck_tag} stream={s_tag} iv={iv_tag}")
        dec = b"".join(s_fn(enc[i:i + 16]) for i in range(0, len(enc), 16))
        if _checksum(dec) == meta["plain_cksum"]:
            hits.append(f"ecb ck={ck_tag}")
    return hits


def main(path: str) -> int:
    _reexec_under_rosetta(path)
    wb_aes_bridge._ENC, wb_aes_bridge._DEC = wb_aes_bridge.load()
    sig = Path(path).read_bytes()
    meta = parse(sig)
    print("encrypted checksum range validation:", "MATCH" if validate_ranges(sig, meta) else "NO")
    hits = try_schemes(sig, meta)
    print("scheme hits:", hits if hits else "NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
