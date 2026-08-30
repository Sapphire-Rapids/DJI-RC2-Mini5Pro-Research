"""Offline validation shared by the fixed by-index research tools."""

WA150_TABLE_CRC = 0x5F8B2AE1
WA150_TABLE_COUNT = 1557


def verify_table_identity(attributes):
    if (attributes.crc, attributes.count) != (WA150_TABLE_CRC, WA150_TABLE_COUNT):
        raise RuntimeError("WA150 table CRC/count mismatch")


def validate_response(frame, *, duml, sender, receiver, sequence, command):
    if command not in (0xE0, 0xE1, 0xE2, 0xE3):
        raise RuntimeError("unlisted by-index response command")
    if len(frame) < 13 or frame[0] != 0x55:
        raise RuntimeError("invalid DUML framing")
    declared = int.from_bytes(frame[1:3], "little")
    if (declared & 0x03FF) != len(frame) or (declared >> 10) != 1:
        raise RuntimeError("invalid DUML length/version")
    if duml.calc_crc8(frame, 3) != frame[3]:
        raise RuntimeError("invalid DUML header CRC")
    if duml.calc_crc16(frame, len(frame) - 2) != int.from_bytes(frame[-2:], "little"):
        raise RuntimeError("invalid DUML body CRC")
    if frame[8] not in (0x80, 0xC0):
        raise RuntimeError("DUML packet is not a plaintext response")
    if frame[4:6] != bytes((sender, receiver)):
        raise RuntimeError("DUML response route mismatch")
    if int.from_bytes(frame[6:8], "little") != sequence:
        raise RuntimeError("DUML response sequence mismatch")
    if frame[9:11] != bytes((0x03, command)):
        raise RuntimeError("DUML response command mismatch")
    return bytes(frame[11:-2])
