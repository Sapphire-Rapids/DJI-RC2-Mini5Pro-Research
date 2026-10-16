"""Call DJI Assistant's own CRijndael-based `aesDecode2Ex` from the dylib.

Framing (static): `aesDecode2` builds a CRijndael, `MakeKey(key, sm_chain0, 0x20, 0x10)`, then
`Decrypt(len, mode1)` — AES-256 CBC with the fixed IV `sm_chain0`. Key arrives as QString for
aesDecode2 and as QByteArray for aesDecode2Ex (simpler ABI, used here). Builds on wb_aes_bridge's
mirror tree and Rosetta runner.

Boundary: this is Assistant's local utility. Whether its key literal is the module `STUE` key is
separate and unproven.
"""
from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from pathlib import Path

import wb_aes_bridge

_WORKER = r'''
import ctypes, sys
root = sys.argv[1]
ctypes.CDLL(root + "/Frameworks/libquazip1-qt5.1.0.0.dylib", mode=ctypes.RTLD_GLOBAL)
lib = ctypes.CDLL(root + "/MacOS/DJIServices/libDJIUavService.dylib")
qba_ctor = lib._ZN10QByteArrayC1EPKci
aesd = lib._Z12aesDecode2ExRK10QByteArrayS1_
qba_ctor.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]; qba_ctor.restype = None
aesd.argtypes = [ctypes.c_void_p]*3; aesd.restype = None

def qba_of(b):
    q = ctypes.create_string_buffer(8); qba_ctor(q, b, len(b)); return q

def data_of(q):
    d = ctypes.c_void_p.from_buffer(q).value
    size = ctypes.c_int.from_address(d + 4).value
    off = ctypes.c_size_t.from_address(d + 0x10).value
    return ctypes.string_at(d + off, size)

data = bytes.fromhex(sys.argv[2]); key = bytes.fromhex(sys.argv[3])
out = ctypes.create_string_buffer(8)
aesd(out, qba_of(data), qba_of(key))
print(data_of(out).hex())
'''


def decode2ex(data: bytes, key: bytes) -> bytes:
    root = wb_aes_bridge.build_mirror()
    out = subprocess.run(
        ["arch", "-x86_64", str(root / "MacOS/Python"), "-c", _WORKER, str(root), data.hex(), key.hex()],
        capture_output=True, text=True, check=True,
        env={**os.environ, "PYTHONHOME": sys.base_prefix},
    )
    return bytes.fromhex(out.stdout.strip())


if __name__ == "__main__":
    import struct
    sig = Path(sys.argv[1]).read_bytes()
    head = struct.unpack_from("<I", sig, 16)[0]
    ssz = struct.unpack_from("<I", sig, 20)[0]
    coff = struct.unpack_from("<I", sig, 196)[0]
    csize = struct.unpack_from("<I", sig, 200)[0]
    enc = sig[head + ssz + coff: head + ssz + coff + csize]
    print(len(decode2ex(enc, bytes.fromhex("1ff6b8ca503b47ad8d04d8686dcb13a0"))))
