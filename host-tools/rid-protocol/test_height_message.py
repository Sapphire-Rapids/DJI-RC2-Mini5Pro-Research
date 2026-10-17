"""Self-check: height GET emitter header and empty payload."""
import height_message as m

msg = m.build()
assert len(msg) == 0x20, len(msg)
assert msg[0x00:0x04] == bytes([0x01, 0x11, 0x50, 0x02])
assert msg[0x05] == 0x02 and msg[0x08] == 0x03
assert msg[0x0E:0x10] == bytes([0x49, 0x57])
assert msg[0x14:0x18] == (500).to_bytes(4, "little")
assert m.build(sender=0x2A)[0x06] == 0x2A
print("ok: height GET emitter header holds with an empty payload")
