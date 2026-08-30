"""Strict, offline-safe parsers for DJI FLYC hash-parameter replies.

This module builds no packets and has no USB dependency. It accepts only the
read-side F7 metadata and F8 value reply shapes needed by the fixed RID-policy
probe. Ambiguous or inconsistent inputs fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import struct
from typing import Any


CMD_TYPE_REQUEST_ACK = 0x40
CMD_TYPE_RESPONSE = 0x80
CMD_TYPE_ACK_RESPONSE = 0xC0
CMD_SET_FLYC = 0x03
CMD_GET_PARAM_INFO_BY_HASH = 0xF7
CMD_GET_PARAM_VALUE_BY_HASH = 0xF8
CMD_WRITE_PARAM_BY_HASH = 0xF9
READ_ONLY_COMMANDS = frozenset(
    {CMD_GET_PARAM_INFO_BY_HASH, CMD_GET_PARAM_VALUE_BY_HASH}
)
WRITE_COMMANDS = frozenset({CMD_WRITE_PARAM_BY_HASH})


class ParamProtocolError(ValueError):
    """A reply cannot be accepted without guessing."""


class ParamStatusError(ParamProtocolError):
    """A status-bearing reply explicitly reported failure."""


@dataclass(frozen=True)
class ParamMetadata:
    name: str
    data_type: int
    size: int
    attribute: int
    minimum_raw: bytes
    maximum_raw: bytes
    default_raw: bytes


@dataclass(frozen=True)
class ParamValue:
    layout: str
    raw: bytes
    decoded: int | float | bool


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
    11: 1,  # bool when the wire type itself is bool
}
_UNSIGNED_TYPES = frozenset({0, 1, 2, 3})
_SIGNED_TYPES = frozenset({4, 5, 6, 7})
_FLOAT_TYPES = frozenset({8, 9})
_BOOL_TYPE = 11

# DJI's SIMPLE keystream table recovered from libGroudStation.so.  The native
# implementation uses the 21-byte string plus its terminating NUL byte.
_SIMPLE_KEY = bytes.fromhex(
    "784f2433282d3240236c642a766941517e69784645"
) + b"\x00"
_ENCRYPTION_MASK = 0x07
_ENCRYPTION_NONE = 0x00
_ENCRYPTION_SIMPLE = 0x03


def simple_filter(data: bytes, sequence: int) -> bytes:
    """Apply DJI's self-inverse SIMPLE keystream to one DUML body region."""

    if not 0 <= sequence <= 0xFFFF:
        raise ParamProtocolError("DUML sequence is outside u16")
    output = bytearray(len(data))
    key_index = 1
    sequence_low = sequence & 0xFF
    sequence_high = (sequence >> 8) & 0xFF
    for index, value in enumerate(data):
        if key_index >= len(_SIMPLE_KEY):
            key_index = 0
        sequence_byte = sequence_high if index & 1 else sequence_low
        output[index] = _SIMPLE_KEY[key_index] ^ value ^ sequence_byte
        key_index = ((index + 1) & 0x0F) ^ (key_index + 1)
    return bytes(output)


def encrypt_request_frame(
    frame: bytes,
    *,
    duml: Any,
    allowed_commands: frozenset[int] = READ_ONLY_COMMANDS,
) -> bytes:
    """Encrypt one already-built FLYC request with the SIMPLE keystream.

    This deliberately refuses every command outside ``allowed_commands``. The
    read-only default rejects F9 and FA; a caller must opt in to write commands
    explicitly by passing ``WRITE_COMMANDS`` (or a subset of it).
    """

    _validate_raw_frame(frame, duml=duml)
    if frame[8] != CMD_TYPE_REQUEST_ACK:
        raise ParamProtocolError("SIMPLE input is not a plaintext request")
    if frame[9] != CMD_SET_FLYC:
        raise ParamProtocolError("SIMPLE input is not a FLYC command")
    if frame[10] not in allowed_commands:
        raise ParamProtocolError(
            f"SIMPLE input is not an allow-listed command (0x{frame[10]:02X})"
        )

    encrypted = bytearray(frame)
    sequence = int.from_bytes(encrypted[6:8], "little")
    encrypted[9:-2] = simple_filter(bytes(encrypted[9:-2]), sequence)
    encrypted[8] |= _ENCRYPTION_SIMPLE
    checksum = duml.calc_crc16(encrypted, len(encrypted) - 2)
    encrypted[-2:] = checksum.to_bytes(2, "little")
    return bytes(encrypted)


def encrypt_read_request_frame(frame: bytes, *, duml: Any) -> bytes:
    """Encrypt one already-built F7/F8 request and reject every write command."""

    return encrypt_request_frame(frame, duml=duml, allowed_commands=READ_ONLY_COMMANDS)


def build_write_request_body(value_raw: bytes, *, parameter_hash: int) -> bytes:
    """Build the exact F9 application payload ``[hash:u32le][value]``.

    This helper only composes bytes. It validates the hash and the encoded
    one-byte Boolean representation but performs no I/O and cannot transmit a packet.
    """

    if not 0 <= parameter_hash <= 0xFFFFFFFF:
        raise ParamProtocolError("write parameter hash is outside u32")
    if value_raw not in (b"\x00", b"\x01"):
        raise ParamProtocolError("only one-byte Boolean writes are established")
    return parameter_hash.to_bytes(4, "little") + bytes(value_raw)


def parse_f9_write_ack(payload: bytes) -> int:
    """Parse the application payload of one F9 write acknowledgement.

    Accepted success shapes are an empty payload and ``[status==0]``. Any
    non-empty payload whose first byte is nonzero raises ``ParamStatusError``.
    """

    if payload == b"":
        return 0
    if payload[0] == 0:
        return 0
    raise ParamStatusError(f"F9 returned status 0x{payload[0]:02X}")


def parse_f7_metadata(
    payload: bytes,
    *,
    expected_name: str,
    semantic_kind: str,
) -> ParamMetadata:
    """Parse the public F7 metadata layout with strict identity/type checks."""

    if semantic_kind not in {"int", "bool"}:
        raise ParamProtocolError("unsupported semantic kind")
    if not payload:
        raise ParamProtocolError("F7 metadata reply is empty")
    if payload[0] != 0:
        raise ParamStatusError(f"F7 returned status 0x{payload[0]:02X}")
    if len(payload) < 20:
        raise ParamProtocolError("F7 metadata reply is shorter than 20 bytes")

    data_type = int.from_bytes(payload[1:3], "little")
    size = int.from_bytes(payload[3:5], "little")
    attribute = int.from_bytes(payload[5:7], "little")
    if data_type not in _TYPE_WIDTHS:
        raise ParamProtocolError(f"unsupported F7 data type {data_type}")
    if size != _TYPE_WIDTHS[data_type]:
        raise ParamProtocolError(
            f"F7 type/size mismatch: type {data_type}, size {size}"
        )
    if semantic_kind == "bool" and data_type not in {
        0,
        1,
        2,
        4,
        5,
        6,
        8,
        9,
        _BOOL_TYPE,
    }:
        raise ParamProtocolError("boolean key reported an unsupported wire type")
    if semantic_kind == "int" and data_type not in (
        _UNSIGNED_TYPES | _SIGNED_TYPES | _FLOAT_TYPES
    ):
        raise ParamProtocolError("integer key reported an unsupported wire type")

    name_field = payload[19:]
    terminator = name_field.find(b"\x00")
    if terminator < 0:
        raise ParamProtocolError("F7 parameter name is not NUL-terminated")
    if any(name_field[terminator + 1 :]):
        raise ParamProtocolError("F7 parameter name has nonzero trailing bytes")
    name_raw = name_field[:terminator]
    try:
        name = name_raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ParamProtocolError("F7 parameter name is not ASCII") from exc
    if name != expected_name:
        raise ParamProtocolError(
            f"F7 parameter identity mismatch: expected {expected_name!r}, got {name!r}"
        )

    return ParamMetadata(
        name=name,
        data_type=data_type,
        size=size,
        attribute=attribute,
        minimum_raw=payload[7:11],
        maximum_raw=payload[11:15],
        default_raw=payload[15:19],
    )


def parse_f8_value(
    payload: bytes,
    *,
    expected_hash: int,
    metadata: ParamMetadata,
    semantic_kind: str,
) -> ParamValue:
    """Parse exactly one F8 value using the two published candidate layouts."""

    if not 0 <= expected_hash <= 0xFFFFFFFF:
        raise ParamProtocolError("expected hash is outside u32")
    encoded_hash = expected_hash.to_bytes(4, "little")
    candidates: list[tuple[str, bytes]] = []

    if len(payload) == 1 and payload[0] != 0:
        raise ParamStatusError(f"F8 returned status 0x{payload[0]:02X}")

    if len(payload) == 5 + metadata.size and payload[1:5] == encoded_hash:
        if payload[0] != 0:
            raise ParamStatusError(f"F8 returned status 0x{payload[0]:02X}")
        candidates.append(("status_hash_value", payload[5:]))
    if len(payload) == 4 + metadata.size and payload[:4] == encoded_hash:
        candidates.append(("hash_value", payload[4:]))

    if not candidates:
        raise ParamProtocolError(
            "F8 reply matches neither validated echoed-hash layout"
        )
    if len(candidates) != 1:
        raise ParamProtocolError("F8 reply layout is ambiguous")

    layout, raw = candidates[0]
    decoded = _decode_value(raw, metadata=metadata, semantic_kind=semantic_kind)
    return ParamValue(layout=layout, raw=raw, decoded=decoded)


def _decode_value(
    raw: bytes,
    *,
    metadata: ParamMetadata,
    semantic_kind: str,
) -> int | float | bool:
    if len(raw) != metadata.size:
        raise ParamProtocolError("value width differs from F7 metadata")
    if metadata.data_type in _UNSIGNED_TYPES:
        value: int | float = int.from_bytes(raw, "little", signed=False)
    elif metadata.data_type in _SIGNED_TYPES:
        value = int.from_bytes(raw, "little", signed=True)
    elif metadata.data_type == 8:
        value = struct.unpack("<f", raw)[0]
    elif metadata.data_type == 9:
        value = struct.unpack("<d", raw)[0]
    elif metadata.data_type == _BOOL_TYPE:
        value = raw[0]
    else:  # guarded by parse_f7_metadata
        raise ParamProtocolError("unsupported value type")

    if isinstance(value, float) and not math.isfinite(value):
        raise ParamProtocolError("floating-point value is not finite")

    if semantic_kind == "bool":
        if isinstance(value, bool) or value not in (0, 1, 0.0, 1.0):
            raise ParamProtocolError("boolean value is not exactly 0 or 1")
        return bool(value)
    if semantic_kind != "int":
        raise ParamProtocolError("unsupported semantic kind")
    return value


def _validate_raw_frame(frame: bytes, *, duml: Any) -> None:
    """Validate framing and checksums before interpreting or decrypting a frame."""

    if len(frame) < 13 or frame[0] != 0x55:
        raise ParamProtocolError("invalid DUML framing")
    declared = int.from_bytes(frame[1:3], "little")
    if (declared & 0x03FF) != len(frame):
        raise ParamProtocolError("DUML declared length mismatch")
    if (declared >> 10) != 1:
        raise ParamProtocolError("unexpected DUML protocol version")
    if duml.calc_crc8(frame, 3) != frame[3]:
        raise ParamProtocolError("DUML header CRC mismatch")
    if duml.calc_crc16(frame, len(frame) - 2) != int.from_bytes(
        frame[-2:], "little"
    ):
        raise ParamProtocolError("DUML body CRC mismatch")


def validate_response_frame(
    frame: bytes,
    *,
    duml: Any,
    expected_sender: int,
    expected_receiver: int,
    expected_sequence: int,
    expected_command_id: int,
) -> bytes:
    """Validate one plaintext or SIMPLE-encrypted response and return its payload.

    Both read (F7/F8) and write (F9) command IDs are accepted. This function
    only validates transport identity and returns the decrypted payload; it
    does not interpret a status byte or assert that a write was applied.
    """

    if expected_command_id not in (READ_ONLY_COMMANDS | WRITE_COMMANDS):
        raise ParamProtocolError("refusing to validate an unknown command")
    _validate_raw_frame(frame, duml=duml)
    if frame[4] != expected_sender or frame[5] != expected_receiver:
        raise ParamProtocolError("DUML response route mismatch")
    if int.from_bytes(frame[6:8], "little") != expected_sequence:
        raise ParamProtocolError("DUML response sequence mismatch")

    encryption = frame[8] & _ENCRYPTION_MASK
    base_command_type = frame[8] & ~_ENCRYPTION_MASK
    if base_command_type not in {CMD_TYPE_RESPONSE, CMD_TYPE_ACK_RESPONSE}:
        raise ParamProtocolError("DUML command type is not a response")
    if encryption not in {_ENCRYPTION_NONE, _ENCRYPTION_SIMPLE}:
        raise ParamProtocolError("unsupported DUML response encryption type")

    if encryption == _ENCRYPTION_SIMPLE:
        interpreted = bytearray(frame)
        interpreted[9:-2] = simple_filter(
            bytes(interpreted[9:-2]), expected_sequence
        )
    else:
        interpreted = frame

    if interpreted[9] != CMD_SET_FLYC or interpreted[10] != expected_command_id:
        raise ParamProtocolError("DUML response command mismatch")
    return bytes(interpreted[11:-2])


def metadata_summary(metadata: ParamMetadata) -> dict[str, object]:
    """Return de-identified, JSON-safe metadata evidence."""

    return {
        "name": metadata.name,
        "data_type": metadata.data_type,
        "size": metadata.size,
        "attribute": metadata.attribute,
        "minimum_raw_hex": metadata.minimum_raw.hex(),
        "maximum_raw_hex": metadata.maximum_raw.hex(),
        "default_raw_hex": metadata.default_raw.hex(),
    }
