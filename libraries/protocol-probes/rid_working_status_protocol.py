"""Strict offline parser for DJI RID working-status pushes.

This module is deliberately read-only: it contains no request builder and has
no USB dependency.  A payload is interpreted only after the complete DUML
frame, route, command type, checksums, and the currently proven seven-byte
layout have all been validated.
"""

from __future__ import annotations

from dataclasses import dataclass
import struct


DUML_SOF = 0x55
DUML_MIN_LENGTH = 13
DUML_MAX_LENGTH = 1023
DUML_PROTOCOL_VERSION = 1

CMD_TYPE_PUSH_PLAINTEXT = 0x00
CMD_SET_ADSB = 0x11
CMD_ID_RID_WORKING_STATUS = 0x1C
RID_PAYLOAD_LENGTH = 7

CRC8_SEED = 0x77
CRC8_POLYNOMIAL_REFLECTED = 0x8C
CRC16_SEED = 0x3692
CRC16_POLYNOMIAL_REFLECTED = 0x8408


class RidProtocolError(ValueError):
    """A frame cannot be accepted without guessing."""


@dataclass(frozen=True)
class RidWorkingStatus:
    """Fields proven for the official DJI Fly native handler studied here."""

    sender: int
    receiver: int
    sequence: int
    flags_word: int
    is_eid_supported: bool
    is_rid_supported: bool
    is_eid_normal: bool
    is_rid_normal: bool
    area_code_value: int
    failure_code: int


def calc_crc8(data: bytes) -> int:
    """Calculate DJI's reflected CRC-8 (seed 0x77, polynomial 0x8C)."""

    crc = CRC8_SEED
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = (
                (crc >> 1) ^ CRC8_POLYNOMIAL_REFLECTED
                if crc & 1
                else crc >> 1
            )
    return crc & 0xFF


def calc_crc16(data: bytes) -> int:
    """Calculate DJI's reflected CRC-16 (seed 0x3692, polynomial 0x8408)."""

    crc = CRC16_SEED
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = (
                (crc >> 1) ^ CRC16_POLYNOMIAL_REFLECTED
                if crc & 1
                else crc >> 1
            )
    return crc & 0xFFFF


def _validate_complete_duml_frame(frame: bytes) -> None:
    if len(frame) < DUML_MIN_LENGTH:
        raise RidProtocolError("DUML frame is shorter than 13 bytes")
    if len(frame) > DUML_MAX_LENGTH:
        raise RidProtocolError("DUML frame exceeds the 10-bit length limit")
    if frame[0] != DUML_SOF:
        raise RidProtocolError("DUML start byte is not 0x55")

    declared = int.from_bytes(frame[1:3], "little")
    if (declared & 0x03FF) != len(frame):
        raise RidProtocolError("DUML declared length does not match the frame")
    if declared >> 10 != DUML_PROTOCOL_VERSION:
        raise RidProtocolError("unexpected DUML protocol version")
    if calc_crc8(frame[:3]) != frame[3]:
        raise RidProtocolError("DUML header CRC mismatch")
    if calc_crc16(frame[:-2]) != int.from_bytes(frame[-2:], "little"):
        raise RidProtocolError("DUML body CRC mismatch")


def extract_valid_duml_frames(buffer: bytearray):
    """Yield checksum-valid frames from a mutable streaming buffer.

    A false 0x55 or corrupted frame advances by one byte, allowing the parser
    to resynchronise without trusting a bad declared length.
    """

    while True:
        try:
            start = buffer.index(DUML_SOF)
        except ValueError:
            buffer.clear()
            return

        if start:
            del buffer[:start]
        if len(buffer) < 4:
            return

        declared = int.from_bytes(buffer[1:3], "little")
        length = declared & 0x03FF
        if (
            length < DUML_MIN_LENGTH
            or length > DUML_MAX_LENGTH
            or declared >> 10 != DUML_PROTOCOL_VERSION
            or calc_crc8(bytes(buffer[:3])) != buffer[3]
        ):
            del buffer[0]
            continue
        if len(buffer) < length:
            return

        candidate = bytes(buffer[:length])
        if calc_crc16(candidate[:-2]) != int.from_bytes(
            candidate[-2:], "little"
        ):
            del buffer[0]
            continue

        del buffer[:length]
        yield candidate


def parse_rid_working_status_frame(frame: bytes) -> RidWorkingStatus:
    """Validate and parse one ``0x11/0x1C`` plaintext push.

    The sender and receiver are reported but deliberately not allow-listed:
    their Mini 5 Pro / RC 2 transport-specific values have not yet been proven.
    """

    _validate_complete_duml_frame(frame)
    if frame[8] != CMD_TYPE_PUSH_PLAINTEXT:
        raise RidProtocolError(
            "RID status command type is not a plaintext no-ACK push"
        )
    if frame[9] != CMD_SET_ADSB or frame[10] != CMD_ID_RID_WORKING_STATUS:
        raise RidProtocolError("DUML route is not ADS-B 0x11/0x1C")

    payload = frame[11:-2]
    if len(payload) != RID_PAYLOAD_LENGTH:
        raise RidProtocolError(
            "RID working-status payload is not the proven seven-byte layout"
        )

    flags = int.from_bytes(payload[:2], "little")
    return RidWorkingStatus(
        sender=frame[4],
        receiver=frame[5],
        sequence=int.from_bytes(frame[6:8], "little"),
        flags_word=flags,
        is_eid_supported=bool(flags & (1 << 1)),
        is_rid_supported=bool(flags & (1 << 0)),
        is_eid_normal=bool(flags & (1 << 9)),
        is_rid_normal=bool(flags & (1 << 8)),
        area_code_value=struct.unpack("<i", payload[2:6])[0],
        failure_code=payload[6],
    )


def msdk_5_18_us_industry_state(status: RidWorkingStatus) -> str:
    """Apply only DJI MSDK 5.18's *US industry* delegate state mapping.

    This is a labelled compatibility interpretation, not a claim that the
    consumer Mini 5 Pro uses the same public state machine.
    """

    if not status.is_rid_supported:
        return "NOT_SUPPORTED"
    if status.failure_code == 0:
        return "WORKING" if status.is_rid_normal else "IDLE"
    if status.failure_code == 1:
        return "OPERATOR_LOCATION_LOST_ERROR"
    if status.failure_code == 2:
        return "FIRMWARE_ERROR"
    return "UNKNOWN_ERROR"


def deidentified_summary(status: RidWorkingStatus) -> dict[str, object]:
    """Return status/routing metadata without raw frames or identity payloads."""

    return {
        "sender": status.sender,
        "receiver": status.receiver,
        "sequence": status.sequence,
        "flags_word": status.flags_word,
        "is_eid_supported": status.is_eid_supported,
        "is_rid_supported": status.is_rid_supported,
        "is_eid_normal": status.is_eid_normal,
        "is_rid_normal": status.is_rid_normal,
        "area_code_value": status.area_code_value,
        "failure_code": status.failure_code,
        "msdk_5_18_us_industry_state": msdk_5_18_us_industry_state(status),
    }
