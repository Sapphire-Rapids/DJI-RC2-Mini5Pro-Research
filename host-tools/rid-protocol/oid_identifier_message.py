"""Emit the DJI Fly `OIDIdentifier` (China UOM realname tag) set/get bytes.

Realigned to the repo's exact RID-005B schema (docs/05_RID_CONTROL_SURFACES.md):
command `0x11/0xD6` `china_uom_realname_tag`; product-139 receiver is fixed at type/index 18/4
(`0x92`); timeout 500 ms; retry 3; SET pack is 18 bytes `[01][03 if empty else 01][16-byte field]`
where at most the first 8 input bytes are copied and the rest of the field zeroes.

HostID ExtraParam is absent for product-139, so the receiver is constant here (not caller-sourced).
GET allocates the same 18 bytes but only writes the `[01,02]` prefix; this emitter deterministically
zeroes the undefined tail (repo drops the vendor's uninitialised behaviour).

STATIC only; no live send.
"""
from __future__ import annotations

import argparse

CMD = 0xD6
SUB = 0x11
RECEIVER = 0x92          # product-139 type/index 18/4
TIMEOUT = 500
RETRY = 3
MAGIC = b"IW"
PACK_LEN = 18
MAX_INPUT = 8            # vendor copies at most the first 8 bytes


def build(text: bytes, sender: int = 0) -> bytes:
    field = bytearray(16)
    field[: min(len(text), MAX_INPUT)] = text[:MAX_INPUT]

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

    pack = bytes([0x01, 0x03 if not text else 0x01]) + bytes(field)
    assert len(pack) == PACK_LEN
    return bytes(h) + pack


def build_get(sender: int = 0) -> bytes:
    """GET mirror: prefix [01,02], zeroed tail."""
    h = bytearray(0x20)
    h[0x01] = SUB
    h[0x02] = CMD
    h[0x03] = 0x02
    h[0x05] = 0x02
    h[0x06] = sender & 0xFF
    h[0x08] = 0x03
    h[0x0E:0x10] = MAGIC
    h[0x14:0x18] = TIMEOUT.to_bytes(4, "little")
    return bytes(h) + bytes([0x01, 0x02]) + bytes(16)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="", help="realname tag (<=8 bytes copied)")
    ap.add_argument("--sender", type=int, default=0)
    ap.add_argument("--get", action="store_true")
    a = ap.parse_args()
    m = build_get(a.sender) if a.get else build(a.text.encode(), a.sender)
    print(f"receiver=0x{RECEIVER:02x} timeout={TIMEOUT} retry={RETRY}")
    print(m.hex())


if __name__ == "__main__":
    main()
