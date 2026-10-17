"""Self-check: OID emitter must match RID-005B exactly (18-byte pack, 8-byte copy, zero tail)."""
import oid_identifier_message as m

msg = m.build(b"12345678")
assert len(msg) == 0x20 + 18, len(msg)
assert msg[0x00:0x04] == bytes([0x01, 0x11, 0xD6, 0x02])
assert msg[0x0E:0x10] == bytes([0x49, 0x57])
assert msg[0x14:0x18] == (500).to_bytes(4, "little")

pack = msg[0x20:]
assert len(pack) == 18
assert pack[0] == 0x01
assert pack[1] == 0x01                       # non-empty -> 01
assert pack[2:10] == b"12345678"             # at most first 8 copied
assert pack[10:] == bytes(8)                 # rest zeroed

# empty -> flag 03, no copy
p2 = m.build(b"")[0x20:]
assert p2[1] == 0x03 and p2[2:] == bytes(16)

# over-length input copies only 8
assert m.build(b"A" * 20)[0x20:][2:10] == b"A" * 8

# GET mirror writes prefix [01,02] and a zeroed tail
g = m.build_get()[0x20:]
assert g[0:2] == bytes([0x01, 0x02]) and g[2:] == bytes(16)

print("ok: OID emitter matches RID-005B (18-byte pack, 8-copy, zero tail, GET mirror)")
