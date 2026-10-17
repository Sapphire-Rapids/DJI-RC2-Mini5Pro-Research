"""Self-check: the emitter must reproduce the decompiled uav_cmd_base_req ctor byte-for-byte.

Anchors are the literal writes in
uav::core::uav_cmd_base_req<(uchar)1,(uchar)3,(uchar)119,
uav_fc_handle_eid_switch,uav_fc_eid_switch_status>::uav_cmd_base_req:

    *(u32*)this        = 0x02770301  -> 01 03 77 02 at 0x00
    *(u64*)(this+1)    = 0x0300000200000000 -> 02 at 0x05 etc. (0x01..0x03 then overwritten by the later u32 write)
    *(u32*)(this+0xc)  = 0x57490000  -> 00 00 49 57 at 0x0c
    *(u32*)(this+0x14) = 500         -> f4 01 00 00 at 0x14
    *(u16*)(this+0x10) = 0 ; *(u16*)(this+0x18) = 0
    this[6] = GlobalPacketStatus::GetGlobalSenderIndex()
"""
import eid_switch_message as m

msg = m.build(sender=0, receiver=0, value=0)

assert len(msg) == 0x21, len(msg)
assert msg[0x00:0x04] == bytes([0x01, 0x03, 0x77, 0x02])
assert msg[0x04:0x09] == bytes([0x00, 0x02, 0x00, 0x00, 0x03]), msg[0x04:0x09].hex()
assert msg[0x0C:0x0E] == b'\x00\x00' and msg[0x0E:0x10] == bytes([0x49, 0x57])
assert msg[0x10:0x12] == b"\x00\x00"
assert msg[0x14:0x18] == (500).to_bytes(4, "little")
assert msg[0x18:0x1A] == b"\x00\x00"
assert msg[0x20] == 0x00

# sender lands at 0x06
assert m.build(sender=0x2A)[0x06] == 0x2A
# value 1 = on
assert m.build(value=1)[0x20] == 1
# nothing writes the receiver slot inside the header (it is caller-side)
assert m.build(receiver=0x7F)[0x06] == 0x00

print("ok: emitter matches the decompiled ctor byte-for-byte")
