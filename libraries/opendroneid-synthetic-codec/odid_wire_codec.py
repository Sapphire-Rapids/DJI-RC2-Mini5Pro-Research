"""Independently written OpenDroneID (ASTM F3411 / ASD-STAN prEN 4709-002) wire codec.

This module re-implements the 25-byte standardized Remote ID message encodings and
the 0xF "Message Pack" container from the public OpenDroneID Core C model
(``opendroneid-core-c``, Apache-2.0, authored by Intel) from its published
semantics, not from any DJI software. It exists only for the separate
**synthetic laboratory source** lane in the RC 2 / Mini 5 Pro research archive:

- it encodes/decodes standardized messages with fully synthetic identity and
  coordinates for detector compatibility tests;
- it performs no RF transmission, no device I/O, no DUML, and no aircraft control.

The encoded wire layouts are:

- every message is 25 bytes (``ODID_MESSAGE_SIZE``);
- byte 0 is ``[MessageType:4][ProtoVersion:4]`` with the message type in the high
  nibble and the protocol version in the low nibble (version 2);
- Message Pack (type 0xF) is ``[type/version][SingleMessageSize][MsgPackSize]``
  followed by ``MsgPackSize`` 25-byte messages (maximum 9).

Field quantisation matches the public reference:

- latitude/longitude: signed int32 of degrees x 10**7 (``LATLON_MULT``);
- altitude/height/area ceiling/floor: uint16 of ``(m + 1000) / 0.5``;
- horizontal speed: 0.25 m/s per unit below 255*0.25, else a second 0.75 m/s scale
  selected by the ``SpeedMult`` bit;
- vertical speed: int8 of ``m/s / 0.5``;
- direction: 0..179 degrees plus an east/west bit;
- timestamp: tenths of a second since the top of the hour;
- area radius: meters / 10 as a uint8.

This module is source-only. It does not bundle, derive from, or redistribute DJI
software, and its synthetic fixtures must never use a real device, account,
operator identity, or coordinate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import struct
from typing import Union

MESSAGE_SIZE = 25
ID_SIZE = 20
STR_SIZE = 23
PACK_MAX_MESSAGES = 9
PROTOCOL_VERSION = 2

LATLON_MULT = 10_000_000
ALT_DIV = 0.5
ALT_ADDER = 1000.0
SPEED_DIV_LOW = 0.25
SPEED_DIV_HIGH = 0.75
VSPEED_DIV = 0.5
AREA_RADIUS_DIV = 10

# Message types (high nibble of byte 0)
MSG_BASIC_ID = 0
MSG_LOCATION = 1
MSG_AUTH = 2
MSG_SELF_ID = 3
MSG_SYSTEM = 4
MSG_OPERATOR_ID = 5
MSG_PACKED = 0xF

# Basic ID
IDTYPE_NONE = 0
IDTYPE_SERIAL_NUMBER = 1
IDTYPE_CAA_REGISTRATION_ID = 2
IDTYPE_UTM_ASSIGNED_UUID = 3
IDTYPE_SPECIFIC_SESSION_ID = 4

UATYPE_NONE = 0
UATYPE_AEROPLANE = 1
UATYPE_HELICOPTER_OR_MULTIROTOR = 2
UATYPE_GYROPLANE = 3
UATYPE_HYBRID_LIFT = 4
UATYPE_ORNITHOPTER = 5
UATYPE_GLIDER = 6
UATYPE_KITE = 7
UATYPE_FREE_BALLOON = 8
UATYPE_CAPTIVE_BALLOON = 9
UATYPE_AIRSHIP = 10
UATYPE_FREE_FALL_PARACHUTE = 11
UATYPE_ROCKET = 12
UATYPE_TETHERED_POWERED_AIRCRAFT = 13
UATYPE_GROUND_OBSTACLE = 14
UATYPE_OTHER = 15

# Location status
STATUS_UNDECLARED = 0
STATUS_GROUND = 1
STATUS_AIRBORNE = 2
STATUS_EMERGENCY = 3
STATUS_REMOTE_ID_SYSTEM_FAILURE = 4

HEIGHT_REF_OVER_TAKEOFF = 0
HEIGHT_REF_OVER_GROUND = 1

# Accuracy classes (values are the public enum ordinals)
HOR_ACC_UNKNOWN = 0
VER_ACC_UNKNOWN = 0
SPEED_ACC_UNKNOWN = 0
TIME_ACC_UNKNOWN = 0

# Auth
AUTH_NONE = 0
AUTH_UAS_ID_SIGNATURE = 1
AUTH_OPERATOR_ID_SIGNATURE = 2
AUTH_MESSAGE_SET_SIGNATURE = 3
AUTH_NETWORK_REMOTE_ID = 4
AUTH_SPECIFIC_AUTHENTICATION = 5

AUTH_PAGE_ZERO_DATA_SIZE = 17
AUTH_PAGE_NONZERO_DATA_SIZE = 23
AUTH_MAX_PAGES = 16

# Self ID
DESC_TYPE_TEXT = 0
DESC_TYPE_EMERGENCY = 1
DESC_TYPE_EXTENDED_STATUS = 2

# System
OPERATOR_LOCATION_TYPE_TAKEOFF = 0
OPERATOR_LOCATION_TYPE_LIVE_GNSS = 1
OPERATOR_LOCATION_TYPE_FIXED = 2

CLASSIFICATION_TYPE_UNDECLARED = 0
CLASSIFICATION_TYPE_EU = 1

CATEGORY_EU_UNDECLARED = 0
CATEGORY_EU_OPEN = 1
CATEGORY_EU_SPECIFIC = 2
CATEGORY_EU_CERTIFIED = 3

CLASS_EU_UNDECLARED = 0
CLASS_EU_CLASS_0 = 1
CLASS_EU_CLASS_1 = 2
CLASS_EU_CLASS_2 = 3
CLASS_EU_CLASS_3 = 4
CLASS_EU_CLASS_4 = 5
CLASS_EU_CLASS_5 = 6
CLASS_EU_CLASS_6 = 7

# Operator ID
OPERATOR_ID_TYPE_OPERATOR = 0


class CodecError(ValueError):
    """A standardized-message byte sequence cannot be accepted without guessing."""


def _u4(byte: int) -> int:
    return byte & 0x0F


def _l4(byte: int) -> int:
    return (byte >> 4) & 0x0F


def _check_u4(value: int, label: str) -> None:
    if not isinstance(value, int) or not (0 <= value <= 0x0F):
        raise CodecError(f"{label} must be a 4-bit integer")


def _check_u8(value: int, label: str) -> None:
    if not isinstance(value, int) or not (0 <= value <= 0xFF):
        raise CodecError(f"{label} must fit in one byte")


def _pack_basic_id_header(id_type: int, ua_type: int) -> int:
    _check_u4(id_type, "id_type")
    _check_u4(ua_type, "ua_type")
    return (id_type << 4) | ua_type


def encode_lat_lon(value: float) -> int:
    return int(round(value * LATLON_MULT))


def decode_lat_lon(value: int) -> float:
    return value / LATLON_MULT


def encode_altitude(value: float) -> int:
    return int(round((value + ALT_ADDER) / ALT_DIV))


def decode_altitude(value: int) -> float:
    return value * ALT_DIV - ALT_ADDER


def encode_speed_horizontal(value: float) -> tuple[int, int]:
    """Return ``(byte, speed_mult_bit)`` for a horizontal speed in m/s."""
    if value <= 0xFF * SPEED_DIV_LOW:
        return int(round(value / SPEED_DIV_LOW)), 0
    big = int(round((value - 0xFF * SPEED_DIV_LOW) / SPEED_DIV_HIGH))
    return max(0, min(0xFF, big)), 1


def decode_speed_horizontal(byte: int, mult: int) -> float:
    if mult:
        return byte * SPEED_DIV_HIGH + 0xFF * SPEED_DIV_LOW
    return byte * SPEED_DIV_LOW


def encode_speed_vertical(value: float) -> int:
    return max(-128, min(127, int(round(value / VSPEED_DIV))))


def decode_speed_vertical(value: int) -> float:
    return value * VSPEED_DIV


def encode_direction(value: float) -> tuple[int, int]:
    """Return ``(byte, east_west_bit)`` for a direction in degrees 0..360."""
    d = int(round(value))
    if d == 360:
        d = 0
    if d < 180:
        return d, 0
    return d - 180, 1


def decode_direction(byte: int, east_west: int) -> float:
    return byte + (180 if east_west else 0)


def encode_timestamp(value: float) -> int:
    """Seconds after the top of the hour -> tenths-of-a-second uint16."""
    return int(round(value * 10))


def decode_timestamp(value: int) -> float:
    return value / 10.0


def encode_area_radius(value: int) -> int:
    return max(0, min(0xFF, value // AREA_RADIUS_DIV))


def decode_area_radius(value: int) -> int:
    return value * AREA_RADIUS_DIV


@dataclass
class BasicID:
    ua_type: int = UATYPE_HELICOPTER_OR_MULTIROTOR
    id_type: int = IDTYPE_SERIAL_NUMBER
    uas_id: str = ""


@dataclass
class Location:
    status: int = STATUS_UNDECLARED
    direction: float = 0.0
    speed_horizontal: float = 0.0
    speed_vertical: float = 0.0
    latitude: float = 0.0
    longitude: float = 0.0
    altitude_baro: float = 0.0
    altitude_geo: float = 0.0
    height_type: int = HEIGHT_REF_OVER_TAKEOFF
    height: float = 0.0
    horiz_accuracy: int = HOR_ACC_UNKNOWN
    vert_accuracy: int = VER_ACC_UNKNOWN
    baro_accuracy: int = VER_ACC_UNKNOWN
    speed_accuracy: int = SPEED_ACC_UNKNOWN
    ts_accuracy: int = TIME_ACC_UNKNOWN
    timestamp: float = 0.0


@dataclass
class Auth:
    data_page: int = 0
    auth_type: int = AUTH_NONE
    last_page_index: int = 0
    length: int = 0
    timestamp: int = 0
    auth_data: bytes = b""


@dataclass
class SelfID:
    desc_type: int = DESC_TYPE_TEXT
    desc: str = ""


@dataclass
class System:
    operator_location_type: int = OPERATOR_LOCATION_TYPE_TAKEOFF
    classification_type: int = CLASSIFICATION_TYPE_UNDECLARED
    operator_latitude: float = 0.0
    operator_longitude: float = 0.0
    area_count: int = 1
    area_radius: int = 0
    area_ceiling: float = 0.0
    area_floor: float = 0.0
    category_eu: int = CATEGORY_EU_UNDECLARED
    class_eu: int = CLASS_EU_UNDECLARED
    operator_altitude_geo: float = 0.0
    timestamp: int = 0


@dataclass
class OperatorID:
    operator_id_type: int = OPERATOR_ID_TYPE_OPERATOR
    operator_id: str = ""


def _cstr(value: str, size: int, label: str) -> bytes:
    raw = value.encode("ascii", "replace")
    if len(raw) > size:
        raise CodecError(f"{label} exceeds {size} bytes")
    return raw + b"\x00" * (size - len(raw))


def encode_basic_id(msg: BasicID) -> bytes:
    out = bytearray(MESSAGE_SIZE)
    out[0] = (MSG_BASIC_ID << 4) | PROTOCOL_VERSION
    out[1] = _pack_basic_id_header(msg.id_type, msg.ua_type)
    out[2:22] = _cstr(msg.uas_id, ID_SIZE, "uas_id")
    return bytes(out)


def decode_basic_id(raw: bytes) -> BasicID:
    if len(raw) != MESSAGE_SIZE:
        raise CodecError("Basic ID message must be 25 bytes")
    if _l4(raw[0]) != MSG_BASIC_ID:
        raise CodecError("not a Basic ID message")
    return BasicID(
        ua_type=_u4(raw[1]),
        id_type=_l4(raw[1]),
        uas_id=raw[2:22].split(b"\x00", 1)[0].decode("ascii", "replace"),
    )


def encode_location(msg: Location) -> bytes:
    out = bytearray(MESSAGE_SIZE)
    out[0] = (MSG_LOCATION << 4) | PROTOCOL_VERSION

    direction_byte, ew = encode_direction(msg.direction)
    speed_byte, mult = encode_speed_horizontal(msg.speed_horizontal)
    v_speed = encode_speed_vertical(msg.speed_vertical)

    out[1] = (
        (int(bool(mult)))
        | (int(bool(ew)) << 1)
        | (msg.height_type << 2)
        | (msg.status << 4)
    )
    out[2] = direction_byte
    out[3] = speed_byte
    out[4] = v_speed & 0xFF
    out[5:9] = struct.pack("<i", encode_lat_lon(msg.latitude))
    out[9:13] = struct.pack("<i", encode_lat_lon(msg.longitude))
    out[13:15] = struct.pack("<H", encode_altitude(msg.altitude_baro))
    out[15:17] = struct.pack("<H", encode_altitude(msg.altitude_geo))
    out[17:19] = struct.pack("<H", encode_altitude(msg.height))
    out[19] = (msg.horiz_accuracy & 0x0F) | ((msg.vert_accuracy & 0x0F) << 4)
    out[20] = (msg.speed_accuracy & 0x0F) | ((msg.baro_accuracy & 0x0F) << 4)
    out[21:23] = struct.pack("<H", encode_timestamp(msg.timestamp))
    out[23] = msg.ts_accuracy & 0x0F
    return bytes(out)


def decode_location(raw: bytes) -> Location:
    if len(raw) != MESSAGE_SIZE:
        raise CodecError("Location message must be 25 bytes")
    if _l4(raw[0]) != MSG_LOCATION:
        raise CodecError("not a Location message")
    b1 = raw[1]
    return Location(
        status=(b1 >> 4) & 0x0F,
        direction=decode_direction(raw[2], (b1 >> 1) & 1),
        speed_horizontal=decode_speed_horizontal(raw[3], b1 & 1),
        speed_vertical=decode_speed_vertical(struct.unpack("<b", raw[4:5])[0]),
        latitude=decode_lat_lon(struct.unpack("<i", raw[5:9])[0]),
        longitude=decode_lat_lon(struct.unpack("<i", raw[9:13])[0]),
        altitude_baro=decode_altitude(struct.unpack("<H", raw[13:15])[0]),
        altitude_geo=decode_altitude(struct.unpack("<H", raw[15:17])[0]),
        height_type=(b1 >> 2) & 1,
        height=decode_altitude(struct.unpack("<H", raw[17:19])[0]),
        horiz_accuracy=raw[19] & 0x0F,
        vert_accuracy=(raw[19] >> 4) & 0x0F,
        speed_accuracy=raw[20] & 0x0F,
        baro_accuracy=(raw[20] >> 4) & 0x0F,
        ts_accuracy=raw[23] & 0x0F,
        timestamp=decode_timestamp(struct.unpack("<H", raw[21:23])[0]),
    )


def encode_auth(msg: Auth) -> bytes:
    out = bytearray(MESSAGE_SIZE)
    out[0] = (MSG_AUTH << 4) | PROTOCOL_VERSION
    out[1] = (msg.data_page & 0x0F) | ((msg.auth_type & 0x0F) << 4)
    if msg.data_page == 0:
        out[2] = msg.last_page_index & 0xFF
        out[3] = msg.length & 0xFF
        out[4:8] = struct.pack("<I", msg.timestamp & 0xFFFFFFFF)
        start = 8
        data_size = AUTH_PAGE_ZERO_DATA_SIZE
    else:
        start = 2
        data_size = AUTH_PAGE_NONZERO_DATA_SIZE
    if len(msg.auth_data) > data_size:
        raise CodecError("auth_data exceeds page capacity")
    out[start : start + len(msg.auth_data)] = msg.auth_data
    return bytes(out)


def decode_auth(raw: bytes) -> Auth:
    if len(raw) != MESSAGE_SIZE:
        raise CodecError("Auth message must be 25 bytes")
    if _l4(raw[0]) != MSG_AUTH:
        raise CodecError("not an Auth message")
    data_page = raw[1] & 0x0F
    auth_type = (raw[1] >> 4) & 0x0F
    if data_page == 0:
        return Auth(
            data_page=0,
            auth_type=auth_type,
            last_page_index=raw[2],
            length=raw[3],
            timestamp=struct.unpack("<I", raw[4:8])[0],
            auth_data=bytes(raw[8:25]),
        )
    return Auth(data_page=data_page, auth_type=auth_type, auth_data=bytes(raw[2:25]))


def encode_self_id(msg: SelfID) -> bytes:
    out = bytearray(MESSAGE_SIZE)
    out[0] = (MSG_SELF_ID << 4) | PROTOCOL_VERSION
    out[1] = msg.desc_type & 0xFF
    out[2:25] = _cstr(msg.desc, STR_SIZE, "desc")
    return bytes(out)


def decode_self_id(raw: bytes) -> SelfID:
    if len(raw) != MESSAGE_SIZE:
        raise CodecError("Self ID message must be 25 bytes")
    if _l4(raw[0]) != MSG_SELF_ID:
        raise CodecError("not a Self ID message")
    return SelfID(desc_type=raw[1], desc=raw[2:25].split(b"\x00", 1)[0].decode("ascii", "replace"))


def encode_system(msg: System) -> bytes:
    out = bytearray(MESSAGE_SIZE)
    out[0] = (MSG_SYSTEM << 4) | PROTOCOL_VERSION
    out[1] = (
        (msg.operator_location_type & 0x03)
        | ((msg.classification_type & 0x07) << 2)
    )
    out[2:6] = struct.pack("<i", encode_lat_lon(msg.operator_latitude))
    out[6:10] = struct.pack("<i", encode_lat_lon(msg.operator_longitude))
    out[10:12] = struct.pack("<H", msg.area_count & 0xFFFF)
    out[12] = encode_area_radius(msg.area_radius)
    out[13:15] = struct.pack("<H", encode_altitude(msg.area_ceiling))
    out[15:17] = struct.pack("<H", encode_altitude(msg.area_floor))
    out[17] = (msg.class_eu & 0x0F) | ((msg.category_eu & 0x0F) << 4)
    out[18:20] = struct.pack("<H", encode_altitude(msg.operator_altitude_geo))
    out[20:24] = struct.pack("<I", msg.timestamp & 0xFFFFFFFF)
    return bytes(out)


def decode_system(raw: bytes) -> System:
    if len(raw) != MESSAGE_SIZE:
        raise CodecError("System message must be 25 bytes")
    if _l4(raw[0]) != MSG_SYSTEM:
        raise CodecError("not a System message")
    b1 = raw[1]
    return System(
        operator_location_type=b1 & 0x03,
        classification_type=(b1 >> 2) & 0x07,
        operator_latitude=decode_lat_lon(struct.unpack("<i", raw[2:6])[0]),
        operator_longitude=decode_lat_lon(struct.unpack("<i", raw[6:10])[0]),
        area_count=struct.unpack("<H", raw[10:12])[0],
        area_radius=decode_area_radius(raw[12]),
        area_ceiling=decode_altitude(struct.unpack("<H", raw[13:15])[0]),
        area_floor=decode_altitude(struct.unpack("<H", raw[15:17])[0]),
        class_eu=raw[17] & 0x0F,
        category_eu=(raw[17] >> 4) & 0x0F,
        operator_altitude_geo=decode_altitude(struct.unpack("<H", raw[18:20])[0]),
        timestamp=struct.unpack("<I", raw[20:24])[0],
    )


def encode_operator_id(msg: OperatorID) -> bytes:
    out = bytearray(MESSAGE_SIZE)
    out[0] = (MSG_OPERATOR_ID << 4) | PROTOCOL_VERSION
    out[1] = msg.operator_id_type & 0xFF
    out[2:22] = _cstr(msg.operator_id, ID_SIZE, "operator_id")
    return bytes(out)


def decode_operator_id(raw: bytes) -> OperatorID:
    if len(raw) != MESSAGE_SIZE:
        raise CodecError("Operator ID message must be 25 bytes")
    if _l4(raw[0]) != MSG_OPERATOR_ID:
        raise CodecError("not an Operator ID message")
    return OperatorID(operator_id_type=raw[1], operator_id=raw[2:22].split(b"\x00", 1)[0].decode("ascii", "replace"))


def decode_message_type(byte: int) -> int:
    t = _l4(byte)
    if t in (MSG_BASIC_ID, MSG_LOCATION, MSG_AUTH, MSG_SELF_ID, MSG_SYSTEM, MSG_OPERATOR_ID, MSG_PACKED):
        return t
    raise CodecError("unknown message type")


def encode_pack(messages: list[bytes]) -> bytes:
    if not messages:
        raise CodecError("pack must contain at least one message")
    if len(messages) > PACK_MAX_MESSAGES:
        raise CodecError("pack exceeds the 9-message maximum")
    for m in messages:
        if len(m) != MESSAGE_SIZE:
            raise CodecError("packed messages must each be 25 bytes")
    out = bytearray([(MSG_PACKED << 4) | PROTOCOL_VERSION, MESSAGE_SIZE, len(messages)])
    for m in messages:
        out.extend(m)
    return bytes(out)


def decode_pack(raw: bytes) -> list[bytes]:
    if len(raw) < 3:
        raise CodecError("pack is too short")
    if _l4(raw[0]) != MSG_PACKED:
        raise CodecError("not a Message Pack")
    if raw[1] != MESSAGE_SIZE:
        raise CodecError("unsupported single-message size")
    count = raw[2]
    if count > PACK_MAX_MESSAGES:
        raise CodecError("pack declares too many messages")
    if len(raw) != 3 + count * MESSAGE_SIZE:
        raise CodecError("pack length does not match declared message count")
    return [raw[3 + i * MESSAGE_SIZE : 3 + (i + 1) * MESSAGE_SIZE] for i in range(count)]


_ENCODERS = {
    MSG_BASIC_ID: (encode_basic_id, decode_basic_id),
    MSG_LOCATION: (encode_location, decode_location),
    MSG_AUTH: (encode_auth, decode_auth),
    MSG_SELF_ID: (encode_self_id, decode_self_id),
    MSG_SYSTEM: (encode_system, decode_system),
    MSG_OPERATOR_ID: (encode_operator_id, decode_operator_id),
}


def decode_message(raw: bytes) -> tuple[int, object]:
    """Decode one 25-byte message into ``(message_type, dataclass)``."""
    if len(raw) != MESSAGE_SIZE:
        raise CodecError("message must be 25 bytes")
    msg_type = decode_message_type(raw[0])
    _, decoder = _ENCODERS[msg_type]
    return msg_type, decoder(raw)


if __name__ == "__main__":  # pragma: no cover - thin CLI, tested indirectly
    import argparse
    import json

    def _encode(args: argparse.Namespace) -> int:
        if args.basic_id is not None:
            raw = encode_basic_id(BasicID(uas_id=args.basic_id, id_type=args.id_type, ua_type=args.ua_type))
        elif args.location is not None:
            raw = encode_location(Location(latitude=args.location, longitude=args.longitude, status=args.status))
        else:
            raise SystemExit("choose --basic-id or --location")
        print(raw.hex())
        return 0

    def _decode(args: argparse.Namespace) -> int:
        raw = bytes.fromhex(args.hex)
        if _l4(raw[0]) == MSG_PACKED:
            for m in decode_pack(raw):
                mt, obj = decode_message(m)
                print(mt, json.dumps(obj, default=str))
        else:
            mt, obj = decode_message(raw)
            print(mt, json.dumps(obj, default=str))
        return 0

    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")

    enc = sub.add_parser("encode", help="encode a synthetic Basic ID or Location message")
    enc.add_argument("--basic-id", help="synthetic UAS ID text")
    enc.add_argument("--id-type", type=int, default=IDTYPE_SERIAL_NUMBER)
    enc.add_argument("--ua-type", type=int, default=UATYPE_HELICOPTER_OR_MULTIROTOR)
    enc.add_argument("--location", type=float, help="synthetic latitude")
    enc.add_argument("--longitude", type=float, default=0.0)
    enc.add_argument("--status", type=int, default=STATUS_AIRBORNE)

    dec = sub.add_parser("decode", help="decode a hex message or pack")
    dec.add_argument("hex")

    args = parser.parse_args()
    if args.command == "encode":
        raise SystemExit(_encode(args))
    if args.command == "decode":
        raise SystemExit(_decode(args))
    parser.print_help()
    raise SystemExit(2)
