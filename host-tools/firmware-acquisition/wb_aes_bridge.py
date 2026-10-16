"""Call DJI Assistant's baked whitebox AES out of the macOS dylib.

The Assistant services each embed one whitebox AES-128 pair (`t_box_enc` / `t_box_dec`, byte-identical
across services) behind `WAES_encrypt` / `WAES_decrypt`. The app ships x86_64, so on Apple silicon the
bridge runs under Rosetta. `@executable_path` / `@loader_path` deps are satisfied by a small mirrored
tree with symlinked frameworks; a copied interpreter is ad-hoc re-signed.

This module only exposes raw 16-byte block encrypt/decrypt. It carries no key, no mode and no device
transport of its own; callers decide the IMaH scheme.

Boundary: the whitebox pair is a fixed DJI Assistant artifact, not a proof that it is the module
`STUE` key, and not a live-device fact.
"""
from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
from pathlib import Path

ASSISTANT = Path("/Applications/DJI Assistant 2(Consumer Drones Series).app")
DYLIB = ASSISTANT / "Contents/MacOS/DJIServices/libDJIUavService.dylib"
FRAMEWORKS = ASSISTANT / "Contents/Frameworks"
MIRROR = Path(os.environ.get("FIND_UAS_WB_MIRROR", "/tmp/finduas_wb_bridge"))

# dependency order matters: frameworks first, then the service dylib
PRELOAD = (
    "libquazip1-qt5.1.0.0.dylib",
    "QtCore.framework/Versions/5/QtCore",
    "QtXml.framework/Versions/5/QtXml",
    "QtNetwork.framework/Versions/5/QtNetwork",
    "QtSerialPort.framework/Versions/5/QtSerialPort",
    "QtGui.framework/Versions/5/QtGui",
    "DJILog.framework/Versions/1/DJILog",
    "DJIDevice.framework/Versions/1/DJIDevice",
)


def _inner_python() -> Path:
    return Path(sys.base_prefix) / "Resources/Python.app/Contents/MacOS/Python"


def build_mirror() -> Path:
    """Create the mirrored tree with symlinked frameworks and an ad-hoc signed interpreter."""
    if MIRROR.exists():
        shutil.rmtree(MIRROR)
    (MIRROR / "MacOS/DJIServices").mkdir(parents=True)
    (MIRROR / "Frameworks").mkdir()
    for entry in FRAMEWORKS.iterdir():
        os.symlink(entry, MIRROR / "Frameworks" / entry.name)
    interp = MIRROR / "MacOS/Python"
    shutil.copy2(_inner_python(), interp)
    subprocess.run(["codesign", "-s", "-", "-f", str(interp)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    dylib = MIRROR / "MacOS/DJIServices/libDJIUavService.dylib"
    shutil.copy2(DYLIB, dylib)
    subprocess.run(["codesign", "-s", "-", "-f", str(dylib)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return MIRROR


_WORKER = r'''
import ctypes, sys
root = sys.argv[1]
ctypes.CDLL(root + "/Frameworks/libquazip1-qt5.1.0.0.dylib", mode=ctypes.RTLD_GLOBAL)
lib = ctypes.CDLL(root + "/MacOS/DJIServices/libDJIUavService.dylib")
enc = lib._Z12WAES_encryptPhS_; dec = lib._Z12WAES_decryptPhS_
for f in (enc, dec):
    f.argtypes = [ctypes.c_char_p, ctypes.c_char_p]; f.restype = None
def run(fn, data):
    i = ctypes.create_string_buffer(data, 16); o = ctypes.create_string_buffer(16)
    fn(i, o); return bytes(o)
mode = sys.argv[2]; data = bytes.fromhex(sys.argv[3])
print(run(enc if mode == "enc" else dec, data).hex())
'''


def _run(mode: str, data: bytes) -> bytes:
    root = MIRROR if MIRROR.exists() else build_mirror()
    out = subprocess.run(
        ["arch", "-x86_64", str(root / "MacOS/Python"), "-c", _WORKER, str(root), mode, data.hex()],
        capture_output=True, text=True, check=True,
        env={**os.environ, "PYTHONHOME": sys.base_prefix},
    )
    return bytes.fromhex(out.stdout.strip())




def load(lib_path: Path | None = None):
    """In-process loader: build the mirror, preload deps and return the two WAES functions."""
    root = build_mirror()
    ctypes.CDLL(str(root / "Frameworks/libquazip1-qt5.1.0.0.dylib"), mode=ctypes.RTLD_GLOBAL)
    lib = ctypes.CDLL(str(lib_path or (root / "MacOS/DJIServices/libDJIUavService.dylib")))
    enc = lib._Z12WAES_encryptPhS_; dec = lib._Z12WAES_decryptPhS_
    for f in (enc, dec):
        f.argtypes = [ctypes.c_char_p, ctypes.c_char_p]; f.restype = None

    def call(fn, data):
        i = ctypes.create_string_buffer(data, 16); o = ctypes.create_string_buffer(16)
        fn(i, o); return bytes(o)

    return (lambda b: call(enc, b)), (lambda b: call(dec, b))


_ENC = _DEC = None


def _ensure():
    global _ENC, _DEC
    if _ENC is None:
        _ENC, _DEC = load()


def encrypt_block(data: bytes) -> bytes:
    """Block encrypt. Uses the in-process loader when this interpreter is already x86_64,
    otherwise one Rosetta subprocess per call (fine for a few blocks, slow for bulk)."""
    if len(data) != 16:
        raise ValueError("whitebox AES works on one 16-byte block")
    if _ENC is not None:
        return _ENC(data)
    return _run("enc", data)


def decrypt_block(data: bytes) -> bytes:
    if len(data) != 16:
        raise ValueError("whitebox AES works on one 16-byte block")
    if _DEC is not None:
        return _DEC(data)
    return _run("dec", data)


def keystream_encrypt(data: bytes) -> bytes:
    """ECB keystream: encrypt every 16-byte block (zero-pad the tail)."""
    pad = (-len(data)) % 16
    blocks = data + b"\0" * pad
    out = b"".join(encrypt_block(blocks[i:i + 16]) for i in range(0, len(blocks), 16))
    return out[:len(data)]
