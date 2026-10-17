"""Emit the DJI Fly `OperatorRegistrationNumber` (opid) set/delete action bytes.

Static reconstruction from OperatorRegistrationNumberSet (0x04e15874), which instantiates
`uav_cmd_base_req<(uchar)1,(uchar)3,(uchar)120,
uav_fc_action_rid_set_and_delete_opid,uav_fc_action_rid_set_and_delete_opid_ack>` and calls
SendSetPack<uav::core::operator_registration_number_action_pack>.

Header shape matches the EID one with cmd 0x78 (120) and sub 3 -> prefix 01 03 78 02.
Payload is the operator registration number string: validated by RemoteIDHelper::isValidInput and
kept as a 16-char 0-origin substring. Empty payload is the delete candidate.
Receiver comes from Characteristics+0x30 and is caller-supplied.

STATIC only; no live send.
"""
from __future__ import annotations

import argparse

CMD = 0x78
SUB = 0x03
TEMPLATE1 = 0x01
TEMPLATE2 = 0x02
TIMEOUT = 500
MAGIC = b"IW"
MAX_LEN = 16


def build(payload: bytes, sender: int = 0, receiver: int = 0) -> bytes:
    if len(payload) > MAX_LEN:
        raise ValueError(f"payload exceeds {MAX_LEN}")
    h = bytearray(0x20)
    h[0x00] = TEMPLATE1
    h[0x01] = SUB
    h[0x02] = CMD
    h[0x03] = TEMPLATE2
    h[0x05] = 0x02
    h[0x06] = sender & 0xFF
    h[0x08] = 0x03
    h[0x0E:0x10] = MAGIC
    h[0x14:0x18] = TIMEOUT.to_bytes(4, "little")
    return bytes(h) + payload


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--opid", default="", help="operator registration number; empty = delete")
    ap.add_argument("--sender", type=int, default=0)
    ap.add_argument("--receiver", type=int, default=0)
    a = ap.parse_args()
    print(build(a.opid.encode(), a.sender, a.receiver).hex())


if __name__ == "__main__":
    main()
