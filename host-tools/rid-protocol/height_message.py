"""Emit the DJI Fly drone dynamic max height GET bytes.

Ctor uav_cmd_base_req<(uchar)1,(uchar)17,(uchar)80,
uav_adsb_get_drone_dynamic_max_height_req,uav_adsb_get_drone_dynamic_max_height_rsp> at 0x02cb9980 is
a standard plain GET (cmd 0x50 / sub 0x11) with no extra constant and an empty payload.

Receiver is caller-supplied. STATIC only; no live send.
"""
from __future__ import annotations

import argparse

CMD = 0x50
SUB = 0x11
TIMEOUT = 500
MAGIC = b"IW"


def build(sender: int = 0, receiver: int = 0) -> bytes:
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
    return bytes(h)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sender", type=int, default=0)
    ap.add_argument("--receiver", type=int, default=0)
    a = ap.parse_args()
    print(f"receiver={a.receiver} (caller-supplied)")
    print(build(a.sender, a.receiver).hex())


if __name__ == "__main__":
    main()
