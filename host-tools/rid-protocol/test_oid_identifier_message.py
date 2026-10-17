"""Self-check: OID emitter must mirror the same ctor layout with cmd214/sub17 and string payload.

Anchors are the same uav_cmd_base_req literal writes as the EID test, but with the
<1,17,214,...> instantiation (cmd 0xD6, sub 0x11, prefix 01 11 D6 02) and the string payload
appended after the 0x20 header, capped at 0x70.
"""
import oid_identifier_message as m

msg = m.build(b"ABC", sender=0, receiver=0)
assert len(msg) == 0x20 + 3, len(msg)
assert msg[0x00:0x04] == bytes([0x01, 0x11, 0xD6, 0x02])
assert msg[0x04] == 0x00 and msg[0x05] == 0x02
assert msg[0x08] == 0x03
assert msg[0x0C:0x0E] == b"\x00\x00"
assert msg[0x0E:0x10] == bytes([0x49, 0x57])
assert msg[0x14:0x18] == (500).to_bytes(4, "little")
assert msg[0x20:] == b"ABC"

# length cap at 0x70
try:
    m.build(b"A" * 0x71)
    raise AssertionError("cap not enforced")
except ValueError:
    pass
assert len(m.build(b"A" * 0x70)) == 0x20 + 0x70

print("ok: OID emitter mirrors the ctor layout and enforces the 0x70 cap")
