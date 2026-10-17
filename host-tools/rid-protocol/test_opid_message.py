"""Self-check: opid emitter must mirror the ctor layout (cmd120/sub3) and enforce the 16 cap."""
import opid_message as m

msg = m.build(b"CHN12345678")
assert len(msg) == 0x20 + 11, len(msg)
assert msg[0x00:0x04] == bytes([0x01, 0x03, 0x78, 0x02])
assert msg[0x05] == 0x02 and msg[0x08] == 0x03
assert msg[0x0E:0x10] == bytes([0x49, 0x57])
assert msg[0x14:0x18] == (500).to_bytes(4, "little")
assert msg[0x20:] == b"CHN12345678"
assert m.build(b"")[0x20:] == b""          # delete
try:
    m.build(b"A" * 17); raise AssertionError("cap not enforced")
except ValueError:
    pass
print("ok: opid emitter mirrors the ctor layout and enforces the 16 cap")
