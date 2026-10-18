"""Call DJI Assistant's own CRijndael-based `aesDecode2Ex` from the dylib.

Framing (static): `aesDecode2Ex` builds a CRijndael, `MakeKey(key, *sm_chain0, 0x20, 0x10)`, then
`Decrypt(len, mode1)` — AES-256 CBC with a zero IV. The sm_chain0 symbol holds a pointer to that IV.
Key arrives as a QByteArray; this wrapper requires all 32 bytes read by MakeKey. Builds on
wb_aes_bridge's mirror tree and Rosetta runner, carrying key and ciphertext through binary stdin.

Boundary: this is Assistant's local utility. Whether a supplied key is the module `STUE` key is
separate and unproven.
"""
from __future__ import annotations

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

key = sys.stdin.buffer.read(32)
data = sys.stdin.buffer.read()
if len(key) != 32 or len(data) % 16:
    raise ValueError("expected a 32-byte key followed by whole ciphertext blocks")
out = ctypes.create_string_buffer(8)
aesd(out, qba_of(data), qba_of(key))
sys.stdout.buffer.write(data_of(out))
'''


_ROOT = None


def decode2ex(data: bytes, key: bytes) -> bytes:
    if len(key) != 32:
        raise ValueError("aesDecode2Ex requires exactly 32 key bytes")
    if len(data) % 16:
        raise ValueError("aesDecode2Ex requires whole 16-byte ciphertext blocks")
    global _ROOT
    if _ROOT is None:
        _ROOT = wb_aes_bridge.build_mirror()
    root = _ROOT
    out = subprocess.run(
        ["/usr/bin/arch", "-x86_64", str(root / "MacOS/Python"), "-c", _WORKER, str(root)],
        input=key + data, capture_output=True, check=True,
        env={**os.environ, "PYTHONHOME": sys.base_prefix},
    )
    return out.stdout


if __name__ == "__main__":
    import argparse
    import struct
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sigfile", type=Path)
    parser.add_argument("--key-file", required=True, type=Path,
                        help="local binary file containing exactly 32 key bytes")
    args = parser.parse_args()
    sig = args.sigfile.read_bytes()
    head = struct.unpack_from("<I", sig, 16)[0]
    ssz = struct.unpack_from("<I", sig, 20)[0]
    coff = struct.unpack_from("<I", sig, 196)[0]
    csize = struct.unpack_from("<I", sig, 200)[0]
    enc = sig[head + ssz + coff: head + ssz + coff + csize + (-csize) % 32]
    print(len(decode2ex(enc, args.key_file.read_bytes())))
