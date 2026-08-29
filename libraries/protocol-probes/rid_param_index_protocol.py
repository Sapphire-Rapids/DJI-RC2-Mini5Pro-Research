"""Offline codec for DJI FLYC by-index parameter commands (0xE0--0xE3).

This module composes and parses the four by-index parameter commands recovered
from the public Mini 5 Pro (wa150) firmware parameter table and the community
parameter editor ``lmdegreeds/djiparam``. It is transport-free: it builds no
packet and performs no I/O, no write, and no motor action.

Command family (FLYC set 0x03):

- ``0xE0`` get_table_attributes : request ``<table:u16>``, reply
  ``<status:u16><table:u16><crc:u32><count:u32>``.
- ``0xE1`` get_info              : request ``<table:u16><index:u16>``, reply
  ``<status:u16><table:u16><index:u16><type_id:u16><size:u16>
   <def[4]><min[4]><max[4]><name NUL>`` (2017 layout).
- ``0xE2`` read_value           : request ``<table:u16><1:u16><index:u16>``,
  reply ``<status:u32><index:u16><value>``.
- ``0xE3`` write_value          : request ``<table:u16><1:u16><index:u16>
  <value>``, reply ``<status:u32>``.

Strict rules: every value is validated against the width decoded from get_info,
and a write value must be exactly the type width. Names are NUL-terminated
ASCII and a mismatch is an error, never a fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import Any


CMD_SET_FLYC = 0x03
CMD_GET_TABLE_ATTRIBUTES = 0xE0
CMD_GET_INFO = 0xE1
CMD_READ_VALUE = 0xE2
CMD_WRITE_VALUE = 0xE3
INDEX_COMMANDS = frozenset(
    {
        CMD_GET_TABLE_ATTRIBUTES,
        CMD_GET_INFO,
        CMD_READ_VALUE,
        CMD_WRITE_VALUE,
    }
)
READ_ONLY_INDEX_COMMANDS = frozenset(
    {CMD_GET_TABLE_ATTRIBUTES, CMD_GET_INFO, CMD_READ_VALUE}
)

_TYPE_WIDTHS = {
    0: 1,  # u8
    1: 2,  # u16
    2: 4,  # u32
    3: 8,  # u64
    4: 1,  # i8
    5: 2,  # i16
    6: 4,  # i32
    7: 8,  # i64
    8: 4,  # float
    9: 8,  # double
    10: 0,  # array (width resolved elsewhere)
    11: 1,  # bool
}
_UNSIGNED_TYPES = frozenset({0, 1, 2, 3})
_SIGNED_TYPES = frozenset({4, 5, 6, 7})
_FLOAT_TYPES = frozenset({8, 9})
_BOOL_TYPE = 11


class ParamIndexError(ValueError):
    """A by-index reply cannot be accepted without guessing."""


class ParamIndexStatusError(ParamIndexError):
    """A status-bearing reply explicitly reported failure."""


@dataclass(frozen=True)
class TableAttributes:
    crc: int
    count: int


@dataclass(frozen=True)
class ParamInfo:
    name: str
    type_id: int
    size: int
    default_raw: bytes
    minimum_raw: bytes
    maximum_raw: bytes


@dataclass(frozen=True)
class ParamValue:
    raw: bytes
    decoded: int | float | bool


def build_table_attributes_request(table: int) -> bytes:
    """Return the exact two-byte 0xE0 request payload ``<table:u16>``."""

    _check_u16(table, "table")
    return table.to_bytes(2, "little")


def parse_table_attributes(payload: bytes) -> TableAttributes:
    """Parse one 0xE0 reply into ``(crc, count)``."""

    if len(payload) < 12:
        raise ParamIndexError("0xE0 reply is shorter than 12 bytes")
    status = int.from_bytes(payload[0:2], "little")
    if status != 0:
        raise ParamIndexStatusError(f"0xE0 returned status 0x{status:04X}")
    if int.from_bytes(payload[2:4], "little") != 0:
        # table field is echoed; table 0 is the only documented array today
        raise ParamIndexError("0xE0 echoed an unsupported table")
    crc = int.from_bytes(payload[4:8], "little")
    count = int.from_bytes(payload[8:12], "little")
    return TableAttributes(crc=crc, count=count)


def build_get_info_request(table: int, index: int) -> bytes:
    """Return the exact four-byte 0xE1 request payload ``<table:u16><index:u16>``."""

    _check_u16(table, "table")
    _check_u16(index, "index")
    return table.to_bytes(2, "little") + index.to_bytes(2, "little")


def parse_get_info(
    payload: bytes,
    *,
    expected_name: str,
    expected_index: int,
) -> ParamInfo:
    """Parse one 0xE1 reply and verify the on-board parameter name and index."""

    if len(payload) < 22:
        raise ParamIndexError("0xE1 reply is shorter than 22 bytes")
    status = int.from_bytes(payload[0:2], "little")
    if status != 0:
        raise ParamIndexStatusError(f"0xE1 returned status 0x{status:04X}")
    table = int.from_bytes(payload[2:4], "little")
    index = int.from_bytes(payload[4:6], "little")
    if table != 0:
        raise ParamIndexError("0xE1 echoed a non-zero table")
    if index != expected_index:
        raise ParamIndexError(
            f"0xE1 echoed index {index}, expected {expected_index}"
        )
    type_id = int.from_bytes(payload[6:8], "little")
    size = int.from_bytes(payload[8:10], "little")
    if type_id not in _TYPE_WIDTHS:
        raise ParamIndexError(f"0xE1 reported unsupported type id {type_id}")
    width = _TYPE_WIDTHS[type_id]
    if width and size != width:
        raise ParamIndexError(
            f"0xE1 type/size mismatch: type {type_id}, size {size}"
        )

    name_field = payload[22:]
    terminator = name_field.find(b"\x00")
    if terminator < 0:
        raise ParamIndexError("0xE1 parameter name is not NUL-terminated")
    name_raw = name_field[:terminator]
    try:
        name = name_raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ParamIndexError("0xE1 parameter name is not ASCII") from exc
    if name != expected_name:
        raise ParamIndexError(
            f"0xE1 parameter identity mismatch: expected {expected_name!r}, got {name!r}"
        )

    return ParamInfo(
        name=name,
        type_id=type_id,
        size=size,
        default_raw=payload[10:14],
        minimum_raw=payload[14:18],
        maximum_raw=payload[18:22],
    )


def build_read_value_request(table: int, index: int) -> bytes:
    """Return the exact six-byte 0xE2 request payload ``<table><1><index>``."""

    _check_u16(table, "table")
    _check_u16(index, "index")
    return table.to_bytes(2, "little") + b"\x01\x00" + index.to_bytes(2, "little")


def parse_read_value(
    payload: bytes,
    *,
    index: int,
    info: ParamInfo,
) -> ParamValue:
    """Parse one 0xE2 reply against the width recovered from get_info."""

    if len(payload) < 6:
        raise ParamIndexError("0xE2 reply is shorter than 6 bytes")
    status = int.from_bytes(payload[0:4], "little")
    if status != 0:
        raise ParamIndexStatusError(f"0xE2 returned status 0x{status:08X}")
    echoed_index = int.from_bytes(payload[4:6], "little")
    if echoed_index != index:
        raise ParamIndexError("0xE2 echoed a different index")

    raw = payload[6:]
    if len(raw) != info.size:
        raise ParamIndexError(
            f"0xE2 value width {len(raw)} differs from get_info size {info.size}"
        )
    decoded = _decode_value(raw, info)
    return ParamValue(raw=raw, decoded=decoded)


def build_write_value_request(
    table: int,
    index: int,
    value_raw: bytes,
    *,
    info: ParamInfo,
) -> bytes:
    """Return the exact 0xE3 request payload with a strictly typed value."""

    _check_u16(table, "table")
    _check_u16(index, "index")
    if len(value_raw) != info.size:
        raise ParamIndexError(
            f"0xE3 value width {len(value_raw)} differs from get_info size {info.size}"
        )
    return table.to_bytes(2, "little") + b"\x01\x00" + index.to_bytes(2, "little") + value_raw


def encode_boolean_value(value: bool, *, info: ParamInfo) -> bytes:
    """Encode one Boolean value in the get_info-declared width."""

    _check_boolean_capable(info)
    if info.type_id == _BOOL_TYPE:
        return bytes([1 if value else 0])
    return bytes([1 if value else 0]) * info.size


def parse_write_status(payload: bytes) -> int:
    """Return the 0xE3 write status; a short or missing status is an error."""

    if len(payload) < 4:
        raise ParamIndexError("0xE3 reply is shorter than 4 bytes")
    status = int.from_bytes(payload[0:4], "little")
    if status != 0:
        raise ParamIndexStatusError(f"0xE3 returned status 0x{status:08X}")
    return status


def _decode_value(raw: bytes, info: ParamInfo) -> int | float | bool:
    if len(raw) != info.size:
        raise ParamIndexError("value width differs from get_info")
    if info.type_id in _UNSIGNED_TYPES:
        value: int | float = int.from_bytes(raw, "little", signed=False)
    elif info.type_id in _SIGNED_TYPES:
        value = int.from_bytes(raw, "little", signed=True)
    elif info.type_id == 8:
        value = struct.unpack("<f", raw)[0]
    elif info.type_id == 9:
        value = struct.unpack("<d", raw)[0]
    elif info.type_id == _BOOL_TYPE:
        value = raw[0]
    else:
        raise ParamIndexError("unsupported value type")
    if isinstance(value, float) and not (value == value):  # NaN
        raise ParamIndexError("floating-point value is NaN")
    return value


def _check_boolean_capable(info: ParamInfo) -> None:
    if info.type_id == _BOOL_TYPE:
        return
    if info.type_id not in (_UNSIGNED_TYPES | _SIGNED_TYPES | _FLOAT_TYPES):
        raise ParamIndexError("parameter type cannot hold a Boolean value")


def _check_u16(value: int, label: str) -> None:
    if not 0 <= value <= 0xFFFF:
        raise ParamIndexError(f"{label} is outside u16")


def info_summary(info: ParamInfo) -> dict[str, object]:
    """Return de-identified, JSON-safe get_info evidence."""

    return {
        "name": info.name,
        "type_id": info.type_id,
        "size": info.size,
        "default_raw_hex": info.default_raw.hex(),
        "minimum_raw_hex": info.minimum_raw.hex(),
        "maximum_raw_hex": info.maximum_raw.hex(),
    }
