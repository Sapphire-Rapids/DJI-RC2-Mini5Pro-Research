"""Emit the DJI Fly `UploadMobileDevicePosition` (app_update_pos_enc) set bytes.

Static reconstruction from UploadMobileDevicePositionSet (0x04e23260):
- template uav_cmd_base_req<(uchar)1,(uchar)17,(uchar)67,
  uav_adsb_set_app_update_pos_enc_req,uav_adsb_set_app_update_pos_enc_rsp> -> cmd 0x43, sub 0x11
- plaintext is a 22-byte (0x16) struct built from the value: bytes at +8/+0xc, doubles at +0x10
  and +0x18 truncated to int, an int at +0x20, timestamp at +0x28
- AES256Encrypt(key, 0x100, plaintext, iv, out) with a whitebox-derived key (keychain id 0x37)
- HmacEncode over ciphertext+blob
- sent buffer = 16 prefix bytes + 16 constant bytes + ciphertext + hmac

The 0x37 keychain resolves to two 48-byte static blobs (file offs 0x740b30 / 0x73a600 in
libsdk_base.so); key = first 32 bytes, remainder unused here. The AES iv constant is the 16 bytes at
0x140f4c0 in libsdk_jni. The blob constant begins at 0x5366cbc (16 bytes identical to the iv).

AES/HMAC semantics are now confirmed from the helpers (C-426/C-427); the prefix composition still follows the vendor Buffer-field copy and is approximate.

STATIC only; no live send.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import struct

from Crypto.Cipher import AES

CMD = 0x43
SUB = 0x11
TIMEOUT = 500
MAGIC = b"IW"
PLAIN_LEN = 0x16

KEY48 = bytes.fromhex("588ad0f4075a925e531269c7c58d2eac2756a9960b490cddef9910b1926d52ba8a4a1d667c665b41b091dd67d13c5361")
IV16 = bytes.fromhex("d3006306bd44fe08200bfd10025716a5")
BLOB16 = IV16  # blob at 0x5366cbc starts with the same 16 bytes


def build(lat: float = 0.0, lon: float = 0.0, alt: float = 0.0, ts: int = 0,
          sender: int = 0, receiver: int = 0) -> bytes:
    # plaintext shape mirrors the vendor packing: byte, byte, then the double tail truncated to ints
    p = bytearray(PLAIN_LEN)
    p[0x00] = lat if False else 0x00          # value +8 byte slot
    p[0x01] = 0x00                             # value +0xc byte slot
    struct.pack_into("<i", p, 0x02, int(lat))  # +0x10 double, truncated
    struct.pack_into("<i", p, 0x06, int(lon))  # +0x18 double, truncated
    struct.pack_into("<i", p, 0x0A, int(alt))  # +0x20 int
    p[0x0E:0x16] = (ts & 0xFFFFFFFFFFFFFFFF).to_bytes(8, "little")  # +0x28 timestamp

    # vendor AES256Encrypt applies PKCS#7-style padding to a block multiple, then AES-CBC
    rem = len(p) % 16
    padlen = 16 - rem if rem else 16
    padded = bytes(p) + bytes([padlen]) * padlen

    key = KEY48[:32]
    ct = AES.new(key, AES.MODE_CBC, IV16).encrypt(padded)

    # vendor HmacEncode writes the full digest over (ciphertext Buffer + appended blob)
    mac = hmac.new(key, ct + BLOB16, hashlib.sha256).digest()

    h = bytearray(0x20)
    h[0x00] = 0x01
    h[0x01] = SUB
    h[0x02] = CMD
    h[0x03] = 0x02
    h[0x05] = 0x02
    h[0x06] = sender & 0xFF
    h[0x08] = 0x03
    h[0x0E:0x10] = MAGIC
    h[0x14:0x18] = TIMEOUT.to_bytes(4, "little")

    prefix16 = bytes(p[:16])                    # approximate Buffer-field copy
    ct_field = ct.ljust(0x100, b"\0")
    return bytes(h) + prefix16 + BLOB16 + ct_field + mac


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, default=0.0)
    ap.add_argument("--lon", type=float, default=0.0)
    ap.add_argument("--alt", type=float, default=0.0)
    ap.add_argument("--ts", type=int, default=0)
    ap.add_argument("--sender", type=int, default=0)
    ap.add_argument("--receiver", type=int, default=0)
    a = ap.parse_args()
    print(f"receiver={a.receiver} (Characteristics+0x30, caller-supplied)")
    print(build(a.lat, a.lon, a.alt, a.ts, a.sender, a.receiver).hex())


if __name__ == "__main__":
    main()
