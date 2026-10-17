"""Emit the DJI Fly ADS-B agent switch set bytes.

From UAV77FlightControllerAbstraction::SetADSBSwitch (0x02d9a9d0):
template uav_cmd_base_req<(uchar)1,(uchar)17,(uchar)55,
uav_adsb_set_set_adsb_agent_switch_req,uav_adsb_set_set_adsb_agent_switch_rsp>; pack
uav::core::adsb_switch_pack; payload is one boolean byte (value +8, non-zero = on).

Header shape matches the EID one with cmd 0x37 (55), sub 0x11. Receiver is caller-supplied.

STATIC only; no live send.
"""
from __future__ import annotations

import argparse

CMD = 0x37
SUB = 0x11
TIMEOUT = 500
MAGIC = b"IW"


def build(value: int = 0, sender: int = 0, receiver: int = 0) -> bytes:
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
    return bytes(h) + bytes([1 if value else 0])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--value", type=int, default=0, help="0 = off, non-zero = on")
    ap.add_argument("--sender", type=int, default=0)
    ap.add_argument("--receiver", type=int, default=0)
    a = ap.parse_args()
    print(f"receiver={a.receiver} (Characteristics+0x30, caller-supplied)")
    print(build(a.value, a.sender, a.receiver).hex())


if __name__ == "__main__":
    main()
