"""Self-check: adsb switch emitter mirrors the ctor layout and takes one boolean."""
import adsb_switch_message as m

msg = m.build(1)
assert len(msg) == 0x21, len(msg)
assert msg[0x00:0x04] == bytes([0x01, 0x11, 0x37, 0x02])
assert msg[0x05] == 0x02 and msg[0x08] == 0x03
assert msg[0x0E:0x10] == bytes([0x49, 0x57])
assert msg[0x14:0x18] == (500).to_bytes(4, "little")
assert msg[0x20] == 1
assert m.build(0)[0x20] == 0
assert m.build(7)[0x20] == 1          # non-zero normalises to 1
assert m.build(sender=0x2A)[0x06] == 0x2A
print("ok: adsb switch emitter header/layout holds")
