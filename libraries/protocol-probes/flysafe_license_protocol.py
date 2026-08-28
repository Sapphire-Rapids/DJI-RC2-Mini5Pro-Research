"""Strict DJI FlySafe license-inventory protocol primitives.

The sole request builder in this module emits ADS-B/whitelist command
``0x11/0x11`` with exactly one request-index byte.  It cannot be parameterised
with another command.  Response parsing keeps only non-sensitive inventory
state and deliberately ignores descriptions, IDs, times, geometry, unknown
extension tails, and raw bytes after transient validation.
"""

from __future__ import annotations

from dataclasses import dataclass


DUML_SOF = 0x55
DUML_MIN_LENGTH = 13
DUML_MAX_LENGTH = 1023
DUML_PROTOCOL_VERSION = 1
CRC8_SEED = 0x77
CRC8_POLYNOMIAL_REFLECTED = 0x8C
CRC16_SEED = 0x3692
CRC16_POLYNOMIAL_REFLECTED = 0x8408

SOURCE_DIRECT_AIRCRAFT = 0x0A
SOURCE_RC2_PROXY = 0xAA
ALLOWED_SOURCES = frozenset({SOURCE_DIRECT_AIRCRAFT, SOURCE_RC2_PROXY})
TARGET_FLIGHT_CONTROLLER = 0x03

CMD_TYPE_REQUEST_ACK = 0x40
CMD_TYPE_RESPONSE = 0x80
CMD_SET_ADSB_WHITELIST = 0x11
CMD_REQUEST_LICENSE = 0x11
READ_ONLY_COMMANDS = frozenset({CMD_REQUEST_LICENSE})

REQUEST_PAYLOAD_LENGTH = 1
RESPONSE_RECORD_LENGTH = 80
RESULT_RECORD = 0
RESULT_END = 1
MAX_INVENTORY_RECORDS = 20

_LICENSE_TYPE_NAMES = {
    0: "GEO_UNLOCK",
    1: "CIRCLE_UNLOCK_AREA",
    2: "COUNTRY_UNLOCK",
    3: "PARAMETER_CONFIGURATION",
    4: "PENTAGON_UNLOCK_AREA",
    5: "POWER_UNLOCK",
    6: "RID_UNLOCK",
    0xFF: "UNKNOWN",
}


class LicenseProtocolError(ValueError):
    """A request or response cannot be accepted without guessing."""


class LicenseStatusError(LicenseProtocolError):
    """The fixed inventory request returned an unsupported result code."""


@dataclass(frozen=True)
class LicenseSummary:
    """The only per-license fields permitted to leave the parser."""

    type_code: int
    level: int
    enabled: bool
    valid: bool

    @property
    def type_name(self) -> str:
        known = _LICENSE_TYPE_NAMES.get(self.type_code)
        return known if known is not None else f"UNKNOWN({self.type_code})"


@dataclass(frozen=True)
class LicenseResponse:
    result: int
    total_count: int
    license: LicenseSummary | None


@dataclass(frozen=True)
class LicenseInventory:
    count: int
    licenses: tuple[LicenseSummary, ...]

    @property
    def truncated(self) -> bool:
        return self.count > len(self.licenses)


def calc_crc8(data: bytes) -> int:
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


def _validate_source(source: int) -> None:
    if source not in ALLOWED_SOURCES:
        raise LicenseProtocolError("source is not an allow-listed read route")


def build_license_request_frame(
    *, source: int, request_id: int, sequence: int
) -> bytes:
    """Build only the fixed one-byte ``0x11/0x11`` inventory request."""

    _validate_source(source)
    # IDs 0..19 can retrieve at most 20 records. ID 20 is reachable only as
    # the public manager's end-marker query when total_count is exactly 20.
    if not 0 <= request_id <= MAX_INVENTORY_RECORDS:
        raise LicenseProtocolError("request ID is outside the fixed 0..20 bound")
    if not 0 <= sequence <= 0xFFFF:
        raise LicenseProtocolError("DUML sequence is outside u16")
    if (
        CMD_SET_ADSB_WHITELIST,
        CMD_REQUEST_LICENSE,
        READ_ONLY_COMMANDS,
    ) != (0x11, 0x11, frozenset({0x11})):
        raise AssertionError("read-only command allow-list changed")

    length = DUML_MIN_LENGTH + REQUEST_PAYLOAD_LENGTH
    frame = bytearray(
        (
            DUML_SOF,
            length & 0xFF,
            ((length >> 8) & 0x03) | (DUML_PROTOCOL_VERSION << 2),
        )
    )
    frame.append(calc_crc8(bytes(frame)))
    frame.extend((source, TARGET_FLIGHT_CONTROLLER))
    frame.extend(sequence.to_bytes(2, "little"))
    frame.extend(
        (
            CMD_TYPE_REQUEST_ACK,
            CMD_SET_ADSB_WHITELIST,
            CMD_REQUEST_LICENSE,
            request_id,
        )
    )
    frame.extend(calc_crc16(bytes(frame)).to_bytes(2, "little"))
    return bytes(frame)


def _validate_complete_frame(frame: bytes) -> None:
    if not DUML_MIN_LENGTH <= len(frame) <= DUML_MAX_LENGTH:
        raise LicenseProtocolError("invalid DUML frame length")
    if frame[0] != DUML_SOF:
        raise LicenseProtocolError("DUML start byte is not 0x55")
    declared = int.from_bytes(frame[1:3], "little")
    if (declared & 0x03FF) != len(frame):
        raise LicenseProtocolError("DUML declared length mismatch")
    if declared >> 10 != DUML_PROTOCOL_VERSION:
        raise LicenseProtocolError("unexpected DUML protocol version")
    if calc_crc8(frame[:3]) != frame[3]:
        raise LicenseProtocolError("DUML header CRC mismatch")
    if calc_crc16(frame[:-2]) != int.from_bytes(frame[-2:], "little"):
        raise LicenseProtocolError("DUML body CRC mismatch")


def extract_valid_duml_frames(buffer: bytearray):
    """Yield checksum-valid frames while safely resynchronising a byte stream."""

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


def parse_license_response_frame(
    frame: bytes, *, expected_source: int, expected_sequence: int
) -> LicenseResponse:
    """Validate the reverse route and parse one fixed command response."""

    _validate_source(expected_source)
    if not 0 <= expected_sequence <= 0xFFFF:
        raise LicenseProtocolError("expected sequence is outside u16")
    _validate_complete_frame(frame)
    if frame[4] != TARGET_FLIGHT_CONTROLLER or frame[5] != expected_source:
        raise LicenseProtocolError("DUML response route mismatch")
    if int.from_bytes(frame[6:8], "little") != expected_sequence:
        raise LicenseProtocolError("DUML response sequence mismatch")
    if frame[8] != CMD_TYPE_RESPONSE:
        raise LicenseProtocolError("DUML command type is not a plaintext response")
    if (
        frame[9] != CMD_SET_ADSB_WHITELIST
        or frame[10] != CMD_REQUEST_LICENSE
    ):
        raise LicenseProtocolError("DUML response command mismatch")
    return parse_license_response_payload(frame[11:-2])


def parse_license_response_payload(payload: bytes) -> LicenseResponse:
    """Parse only the public header and four approved summary fields."""

    if len(payload) < 1:
        raise LicenseProtocolError("license response payload is empty")
    result = payload[0]
    if result == RESULT_END:
        return LicenseResponse(result=result, total_count=0, license=None)
    if result != RESULT_RECORD:
        raise LicenseStatusError(f"license inventory returned status {result}")
    if len(payload) < RESPONSE_RECORD_LENGTH:
        raise LicenseProtocolError("record response is shorter than 80 bytes")

    total_count = payload[1]
    if total_count == 0:
        raise LicenseProtocolError("record response reports a zero total count")
    if payload[2] not in (0, 1):
        raise LicenseProtocolError("enabled field is not exactly zero or one")

    return LicenseResponse(
        result=result,
        total_count=total_count,
        license=LicenseSummary(
            type_code=payload[34],
            level=payload[35],
            enabled=payload[2] == 1,
            valid=payload[3] == 0,
        ),
    )


def collect_inventory(fetch) -> LicenseInventory:
    """Fetch at most 20 records and confirm the public end marker when bounded."""

    first = fetch(0)
    if not isinstance(first, LicenseResponse):
        raise LicenseProtocolError("fetch returned an unexpected object")
    if first.result == RESULT_END:
        if first.total_count != 0:
            raise LicenseProtocolError("empty inventory reports a nonzero count")
        return LicenseInventory(count=0, licenses=())
    if first.result != RESULT_RECORD or first.license is None:
        raise LicenseProtocolError("index zero did not return a record or end marker")

    total = first.total_count
    records = [first.license]
    for request_id in range(1, min(total, MAX_INVENTORY_RECORDS)):
        response = fetch(request_id)
        if not isinstance(response, LicenseResponse):
            raise LicenseProtocolError("fetch returned an unexpected object")
        if response.result != RESULT_RECORD or response.license is None:
            raise LicenseProtocolError("inventory ended before the reported count")
        if response.total_count != total:
            raise LicenseProtocolError("inventory total count changed during the read")
        records.append(response.license)

    # The public manager requests request_id == total after records 0..total-1
    # and requires result==1. Do the same only while that request remains
    # inside the fixed 0..20 bound; larger inventories are reported truncated.
    if total <= MAX_INVENTORY_RECORDS:
        end = fetch(total)
        if not isinstance(end, LicenseResponse):
            raise LicenseProtocolError("fetch returned an unexpected object")
        if (
            end.result != RESULT_END
            or end.total_count != 0
            or end.license is not None
        ):
            raise LicenseProtocolError("inventory did not return the final end marker")
    return LicenseInventory(count=total, licenses=tuple(records))


def deidentified_inventory_summary(
    inventory: LicenseInventory,
) -> dict[str, object]:
    """Return only counts and approved non-sensitive per-license state."""

    return {
        "count": inventory.count,
        "returned_count": len(inventory.licenses),
        "truncated": inventory.truncated,
        "licenses": [
            {
                "type": item.type_name,
                "level": item.level,
                "enabled": item.enabled,
                "valid": item.valid,
            }
            for item in inventory.licenses
        ],
    }
