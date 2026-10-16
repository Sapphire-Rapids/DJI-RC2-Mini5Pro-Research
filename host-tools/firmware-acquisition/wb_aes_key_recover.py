"""Recover the AES key baked into DJI Assistant's whitebox tables.

`t_box_dec[i]` is affine in `InvSbox(x ^ k_i)` (`k_i` = key byte for input position `perm[i]`), plus a
constant encoding. The affine check against real AES S-boxes yields exactly one `k` per table.

Output is a candidate 16-byte key. It is a HYPOTHESIS, not a proven AES key: the tables carry a
per-table constant encoding, so plain AES with this key does not equal the whitebox. Recovering the
key is still the prerequisite for stripping the encoding.

Table extraction needs the Assistant dylib vmaddr -> file offset mapping; run under any interpreter.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

SBOX = bytes.fromhex(
    "637c777bf26b6fc53001672bfed7ab76ca82c97dfa5947f0add4a2af9ca472c0b7fd9326363ff7cc34a5e5f171d831150"
    "4c723c31896059a071280e2eb27b27509832c1a1b6e5aa0523bd6b329e32f8453d100ed20fcb15b6acbbe394a4c58cf"
    "d0efaafb434d338545f9027f503c9fa851a3408f929d38f5bcb6da2110fff3d2cd0c13ec5f974417c4a77e3d645d197"
    "360814fdc222a908846eeb814de5e0bdbe0323a0a4906245cc2d3ac629195e479e7c8376d8dd54ea96c56f4ea657aae08"
    "ba78252e1ca6b4c6e8dd741f4bbd8b8a703eb5664803f60e613557b986c11d9ee1f8981169d98e949b1e87e9ce5528df"
    "8ca1890dbfe6426841992d0fb054bb16")
INV = bytes(SBOX.index(i) for i in range(256))

# output byte i reads input byte perm[i]
PERM = (0, 0xD, 0xA, 0x7, 0x4, 0x1, 0xE, 0xB, 0x8, 0x5, 0x2, 0xF, 0xC, 0x9, 0x6, 0x3)

DYLIB = Path("/Applications/DJI Assistant 2(Consumer Drones Series).app/Contents/MacOS/DJIServices"
             "/libDJIUavService.dylib")
TABLE_SYMBOL = "t_box_dec"


def _symbol(name: str) -> int:
    sys.path.insert(0, str(Path(__file__).parent))
    import subprocess
    out = subprocess.run(["nm", "-a", str(DYLIB)], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[2].endswith(name):
            return int(parts[0], 16)
    raise KeyError(name)


def _file_offset(va: int) -> int:
    d = DYLIB.read_bytes()
    ncmds = struct.unpack_from("<I", d, 16)[0]
    p = 32
    for _ in range(ncmds):
        cmd, size = struct.unpack_from("<II", d, p)
        if cmd == 0x19:  # LC_SEGMENT_64
            vmaddr, filesz, fileoff = struct.unpack_from("<QQQ", d, p + 24)
            if vmaddr <= va < vmaddr + filesz and filesz:
                return fileoff + (va - vmaddr)
        p += size
    raise ValueError("symbol vmaddr not backed by a file segment")


def recover_key() -> bytes:
    d = DYLIB.read_bytes()
    start = _file_offset(_symbol(TABLE_SYMBOL))
    tables = d[start:start + 4096]
    key = bytearray(16)
    for i in range(16):
        T = tables[i * 256:(i + 1) * 256]
        good = []
        for k in range(256):
            v = [INV[x ^ k] for x in range(256)]
            vinv = [0] * 256
            for x in range(256):
                vinv[v[x]] = x
            g = [T[vinv[u]] for u in range(256)]
            ok = True
            for u in range(256):
                for w in range(256):
                    if g[u] ^ g[u ^ w] ^ g[0] ^ g[w] != 0:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                good.append(k)
        if len(good) != 1:
            raise ValueError(f"table {i}: {len(good)} candidates, expected 1")
        key[PERM[i]] = good[0]
    return bytes(key)


if __name__ == "__main__":
    print(recover_key().hex())
