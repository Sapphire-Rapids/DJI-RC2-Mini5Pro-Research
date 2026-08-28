"""DJI FunctionDiscover 0x00/B8 request and reply codec.

The wire layout is reconstructed from DJI Fly 1.21.10 ``libsdk_jni.so``.
This module is deliberately transport-free: it builds the official 19-byte
download request and parses paged replies without touching a USB device.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CMD_TYPE_REQUEST_ACK = 0x40
CMD_TYPE_RESPONSE = 0x80
CMD_TYPE_ACK_RESPONSE = 0xC0
CMD_SET_GENERAL = 0x00
CMD_ID_FUNCTION_DISCOVERY = 0xB8
FORMAT_VERSION = 1
REQUEST_LENGTH = 19


class FunctionDiscoveryError(ValueError):
    """A FunctionDiscover packet or payload is malformed or inconsistent."""


class FunctionDiscoveryStatusError(FunctionDiscoveryError):
    """The aircraft explicitly rejected a FunctionDiscover request."""


@dataclass(frozen=True)
class FunctionRecord:
    version0: int
    version1: int
    function_id: int
    reserved: int
    attributes: bytes
    host_ids: tuple[int, ...]
    is_minimum_page: bool


@dataclass(frozen=True)
class DiscoveryPage:
    current_index: int
    total_index: int
    functions: tuple[FunctionRecord, ...]
    device_groups: tuple[bytes, ...]
    unknown_tlvs: tuple[tuple[int, bytes], ...]


def device_address(device_type: int, device_index: int) -> int:
    """Encode DJI's five-bit device type and three-bit device index."""

    if not 0 <= device_type <= 0x1F:
        raise FunctionDiscoveryError("device type is outside five bits")
    if not 0 <= device_index <= 0x07:
        raise FunctionDiscoveryError("device index is outside three bits")
    return device_type | (device_index << 5)


def build_download_payload(*, main_version: int, page_index: int) -> bytes:
    """Build the exact 19-byte payload used by FunctionDiscover::Download."""

    if not 0 <= main_version <= 0xFF:
        raise FunctionDiscoveryError("main version is outside u8")
    if not 1 <= page_index <= 0xFF:
        raise FunctionDiscoveryError("page index must be 1..255")
    payload = bytearray(REQUEST_LENGTH)
    payload[0] = main_version
    payload[2] = FORMAT_VERSION
    payload[3] = page_index
    return bytes(payload)


def parse_discovery_page(
    payload: bytes, *, expected_page_index: int | None = None
) -> DiscoveryPage:
    """Parse one B8 reply page, including all variable-length function rows."""

    if len(payload) < 8:
        raise FunctionDiscoveryError("reply is shorter than its eight-byte header")
    if payload[0] != 0:
        raise FunctionDiscoveryStatusError(
            f"FunctionDiscover returned status 0x{payload[0]:02X}"
        )
    if payload[3] != FORMAT_VERSION:
        raise FunctionDiscoveryError(
            f"unsupported reply format version {payload[3]}"
        )

    current_index = payload[4]
    total_index = payload[5]
    if current_index == 0 or total_index == 0 or current_index > total_index:
        raise FunctionDiscoveryError("invalid current/total page indexes")
    if expected_page_index is not None and current_index != expected_page_index:
        raise FunctionDiscoveryError(
            f"reply page {current_index} does not match request {expected_page_index}"
        )

    tlv_size = int.from_bytes(payload[6:8], "little")
    if len(payload) != 8 + tlv_size:
        raise FunctionDiscoveryError("reply TLV length does not match payload length")

    functions: list[FunctionRecord] = []
    device_groups: list[bytes] = []
    unknown_tlvs: list[tuple[int, bytes]] = []
    cursor = 8
    while cursor < len(payload):
        if cursor + 3 > len(payload):
            raise FunctionDiscoveryError("truncated TLV header")
        tlv_type = payload[cursor]
        value_size = int.from_bytes(payload[cursor + 1 : cursor + 3], "little")
        cursor += 3
        end = cursor + value_size
        if end > len(payload):
            raise FunctionDiscoveryError("TLV value exceeds reply payload")
        value = payload[cursor:end]
        cursor = end

        if tlv_type == 0:
            device_groups.append(value)
        elif tlv_type == 1:
            functions.extend(
                _parse_function_group(value, is_minimum_page=current_index == 1)
            )
        else:
            unknown_tlvs.append((tlv_type, value))

    return DiscoveryPage(
        current_index=current_index,
        total_index=total_index,
        functions=tuple(functions),
        device_groups=tuple(device_groups),
        unknown_tlvs=tuple(unknown_tlvs),
    )


def _parse_function_group(
    value: bytes, *, is_minimum_page: bool
) -> list[FunctionRecord]:
    if len(value) < 2:
        raise FunctionDiscoveryError("function group is missing its row count")
    count = int.from_bytes(value[:2], "little")
    cursor = 2
    records: list[FunctionRecord] = []
    for _ in range(count):
        if cursor + 7 > len(value):
            raise FunctionDiscoveryError("truncated function row")
        version0 = value[cursor]
        version1 = value[cursor + 1]
        function_id = int.from_bytes(value[cursor + 2 : cursor + 4], "little")
        reserved = value[cursor + 4]
        attribute_count = value[cursor + 5]
        cursor += 6

        attribute_end = cursor + attribute_count
        if attribute_end + 1 > len(value):
            raise FunctionDiscoveryError("function attributes exceed group length")
        attributes = value[cursor:attribute_end]
        cursor = attribute_end

        host_count = value[cursor]
        cursor += 1
        host_end = cursor + 2 * host_count
        if host_end > len(value):
            raise FunctionDiscoveryError("function host IDs exceed group length")
        host_ids = tuple(
            int.from_bytes(value[pos : pos + 2], "little")
            for pos in range(cursor, host_end, 2)
        )
        cursor = host_end
        records.append(
            FunctionRecord(
                version0=version0,
                version1=version1,
                function_id=function_id,
                reserved=reserved,
                attributes=attributes,
                host_ids=host_ids,
                is_minimum_page=is_minimum_page,
            )
        )

    if cursor != len(value):
        raise FunctionDiscoveryError("function group has unconsumed trailing bytes")
    return records


def _validate_raw_frame(frame: bytes, *, duml: Any) -> None:
    if len(frame) < 13 or frame[0] != 0x55:
        raise FunctionDiscoveryError("invalid DUML framing")
    declared = int.from_bytes(frame[1:3], "little")
    if (declared & 0x03FF) != len(frame) or (declared >> 10) != 1:
        raise FunctionDiscoveryError("invalid DUML length/version field")
    if duml.calc_crc8(frame, 3) != frame[3]:
        raise FunctionDiscoveryError("DUML header CRC mismatch")
    if duml.calc_crc16(frame, len(frame) - 2) != int.from_bytes(
        frame[-2:], "little"
    ):
        raise FunctionDiscoveryError("DUML body CRC mismatch")


def validate_response_frame(
    frame: bytes,
    *,
    duml: Any,
    expected_sender: int,
    expected_receiver: int,
    expected_sequence: int,
) -> bytes:
    """Validate a plaintext B8 response and return its payload."""

    _validate_raw_frame(frame, duml=duml)
    if frame[4] != expected_sender or frame[5] != expected_receiver:
        raise FunctionDiscoveryError("DUML response route mismatch")
    if int.from_bytes(frame[6:8], "little") != expected_sequence:
        raise FunctionDiscoveryError("DUML response sequence mismatch")
    if frame[8] not in {CMD_TYPE_RESPONSE, CMD_TYPE_ACK_RESPONSE}:
        raise FunctionDiscoveryError("DUML command type is not a plaintext response")
    if frame[9] != CMD_SET_GENERAL or frame[10] != CMD_ID_FUNCTION_DISCOVERY:
        raise FunctionDiscoveryError("DUML response command mismatch")
    return frame[11:-2]
