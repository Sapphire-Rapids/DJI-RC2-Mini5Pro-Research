"""Encode the 84-byte app-position payload observed in the Fly 1.21.10 SDK.

The caller supplies the 22-byte serialized field block, a decoded 32-byte key,
and a 16-byte IV. Keychain slot 0x37 stores wrapped data, not the plaintext key.
The payload is LE32(80) + AES-256-CBC ciphertext[32] + IV[16] + HMAC-SHA256[32].

This is an offline payload encoder. It does not build the SDK's internal request
object or a DUML transport frame, interpret coordinate units, or control a device.
See C-459 and the subsequent position-payload validation in the evidence register.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import struct
from pathlib import Path

from Crypto.Cipher import AES

CMD = 0x43
SUB = 0x11
PLAIN_LEN = 22


def build(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    if len(plaintext) != PLAIN_LEN:
        raise ValueError("position field block must be exactly 22 bytes")
    if len(key) != 32:
        raise ValueError("decoded position key must be exactly 32 bytes")
    if len(iv) != 16:
        raise ValueError("position IV must be exactly 16 bytes")
    padded = plaintext + bytes([10]) * 10
    ciphertext = AES.new(key, AES.MODE_CBC, iv).encrypt(padded)
    authenticated = ciphertext + iv
    body = authenticated + hmac.new(key, authenticated, hashlib.sha256).digest()
    return struct.pack("<I", len(body)) + body


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plaintext-file", required=True, type=Path)
    parser.add_argument("--key-file", required=True, type=Path)
    parser.add_argument("--iv-file", required=True, type=Path)
    args = parser.parse_args()
    payload = build(args.plaintext_file.read_bytes(), args.key_file.read_bytes(),
                    args.iv_file.read_bytes())
    print(payload.hex())


if __name__ == "__main__":
    main()
