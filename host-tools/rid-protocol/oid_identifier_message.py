"""Emit the DJI Fly `OIDIdentifier` request bytes (static reconstruction).

Sibling of the EID switch, but a *string* parameter on a distinct opcode pair:
template `uav_cmd_base_req<(uchar)1,(uchar)17,(uchar)214,
uav_adsb_set_china_uom_realname_tag_req,uav_adsb_set_china_uom_realname_tag_rsp>`.

Header shape matches the EID one with cmd 0xD6 (214), sub 0x11 (17) and prefix 01 11 D6 02.
Payload is a std::string copied from the value object at +8, capped at 0x70 (112) bytes.
Receiver comes from Characteristics+0x30 and is caller-supplied.

STATIC only; no live send.
"""
from __future__ import annotations

import argparse

CMD = 0xD6
SUB = 0x11
TEMPLATE1 = 0x01
TEMPLATE2 = 0x02
TIMEOUT = 500
MAGIC = b"IW"
MAX_LEN = 0x70


def build(payload: bytes, sender: int = 0, receiver: int = 0) -> bytes:
    if len(payload) > MAX_LEN:
        raise ValueError(f"payload exceeds 0x{MAX_LEN:x}")
    h = bytearray(0x20)
    h[0x00] = TEMPLATE1
    h[0x01] = SUB
    h[0x02] = CMD
    h[0x03] = TEMPLATE2
    h[0x06] = sender & 0xFF
    h[0x08] = 0x03
    h[0x0C:0x0E] = MAGIC
    h[0x14:0x18] = TIMEOUT.to_bytes(4, "little")
    return bytes(h) + payload


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="", help="OID identifier string")
    ap.add_argument("--sender", type=int, default=0)
    ap.add_argument("--receiver", type=int, default=0)
    a = ap.parse_args()
    print(build(a.text.encode(), a.sender, a.receiver).hex())


if __name__ == "__main__":
    main()
