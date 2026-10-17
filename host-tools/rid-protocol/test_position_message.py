"""Self-check: position emitter header/структура and length invariants."""
import position_message as m

msg = m.build(lat=31, lon=121, alt=50, ts=1)

# header per the ctor shape: cmd0x43/sub0x11
assert msg[0x00:0x04] == bytes([0x01, 0x11, 0x43, 0x02])
assert msg[0x05] == 0x02 and msg[0x08] == 0x03
assert msg[0x0E:0x10] == bytes([0x49, 0x57])
assert msg[0x14:0x18] == (500).to_bytes(4, "little")

# layout: 0x20 header + 16 prefix + 16 blob + 0x100 ciphertext + 32 mac
assert len(msg) == 0x20 + 16 + 16 + 0x100 + 32, len(msg)
assert msg[0x20 + 16 : 0x20 + 32] == m.BLOB16
assert msg[0x20 + 32 : 0x20 + 32 + 0x100] is not None

# deterministic and sender lands at 0x06
assert m.build(ts=1) == m.build(ts=1)
assert m.build(sender=0x2A)[0x06] == 0x2A

# constants are 48-byte key and 16-byte iv
assert len(m.KEY48) == 48 and len(m.IV16) == 16
print("ok: position emitter header/layout/lengths hold")
