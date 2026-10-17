"""Emit the DJI Fly `eid_switch` (RID/EID enable) request bytes recovered statically.

Layout derived from the decompiled `uav_cmd_base_req<(uchar)1,(uchar)3,(uchar)119,
uav_fc_handle_eid_switch,uav_fc_eid_switch_status>` constructor in DJI Fly's libsdk_jni.so:

    +0x00  01 03 77 02        template1, template2(sub3), cmd119(0x77), 0x02
    +0x04  00 00              -
    +0x06  <sender>           GlobalPacketStatus::GetGlobalSenderIndex(), auto in-process
    +0x07  00
    +0x08  03
    +0x0c  00 00 49 57        'I','W' magic
    +0x10  00 00
    +0x14  f4 01 00 00        timeout 500
    +0x18  00 00
    +0x20  <payload>          one enable byte (set); Get uses 0x02 at its own slot

Receiver index comes from Characteristics+0x30 and is caller-supplied; transport is
SendSetPack -> BaseAbstraction::SendPack (slot0x128) -> UavCoreCancelation::SendData.

Set with value 0 is the candidate "Remote ID off".
This is a STATIC reconstruction: no live send is performed here.
"""
from __future__ import annotations

import argparse

CMD = 0x77
SUB = 0x03
TEMPLATE1 = 0x01
TEMPLATE2 = 0x02  # the ctor writes 0x02 at this[3]
TIMEOUT = 500
MAGIC = b"IW"


def build(sender: int = 0, receiver: int = 0, value: int = 0) -> bytes:
    h = bytearray(0x20)
    h[0x00] = TEMPLATE1
    h[0x01] = SUB
    h[0x02] = CMD
    h[0x03] = TEMPLATE2
    h[0x06] = sender & 0xFF
    h[0x08] = 0x03
    h[0x0C:0x0E] = MAGIC
    h[0x14:0x18] = TIMEOUT.to_bytes(4, "little")
    return bytes(h) + bytes([value & 0xFF])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sender", type=int, default=0)
    ap.add_argument("--receiver", type=int, default=0)
    ap.add_argument("--value", type=int, default=0, help="0 = RID off, 1 = on")
    a = ap.parse_args()
    m = build(a.sender, a.receiver, a.value)
    print("receiver (caller slot, Characteristics+0x30):", a.receiver)
    print(m.hex())


if __name__ == "__main__":
    main()
