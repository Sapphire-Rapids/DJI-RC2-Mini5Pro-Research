"""Offline parser for RID/FlySafe state copied from RC 2 loopback streams.

This module deliberately contains no socket, USB, Android, or file-writing
code.  It accepts byte chunks supplied by a caller, extracts CRC-valid DUML
frames from either the direct broker representation or the port-40007 outer
envelope, and returns only de-identified RID or FlySafe capability summaries.
"""

from __future__ import annotations

from collections.abc import Iterable

from flysafe_runtime_state_protocol import (
    CMD_ID_AREA_INFO,
    CMD_ID_WHITE_LIST_INFO,
    CMD_SET_FLIGHT_CONTROLLER,
    CMD_TYPE_PUSH_PLAINTEXT,
    FlySafeStateError,
    decode_area_unlock_version,
    decode_whitelist_support,
)
from rid_working_status_protocol import (
    DUML_MAX_LENGTH,
    DUML_MIN_LENGTH,
    RidProtocolError,
    calc_crc16,
    calc_crc8,
    deidentified_summary,
    parse_rid_working_status_frame,
)


OUTER_MAGIC = b"\x55\xCC\x30\x75"
OUTER_HEADER_LENGTH = 8
RID_COMMAND_SET = 0x11
RID_COMMAND_ID = 0x1C


def _is_valid_duml(frame: bytes) -> bool:
    if not (DUML_MIN_LENGTH <= len(frame) <= DUML_MAX_LENGTH):
        return False
    if frame[0] != 0x55:
        return False
    declared = int.from_bytes(frame[1:3], "little")
    if (declared & 0x03FF) != len(frame) or declared >> 10 != 1:
        return False
    if calc_crc8(frame[:3]) != frame[3]:
        return False
    return calc_crc16(frame[:-2]) == int.from_bytes(frame[-2:], "little")


class LoopbackDumlStreamParser:
    """Incrementally extract valid inner DUML from 40009/direct or 40007/wrapped.

    The 40007 envelope is ``55 cc 30 75`` followed by a little-endian u32
    length and exactly one inner DUML frame.  Some recorded 40007 streams also
    contain direct-compatible DUML, so both representations are accepted.
    Corrupt candidates advance by one byte to allow bounded resynchronisation.
    """

    def __init__(self) -> None:
        self._pending = bytearray()

    def feed(self, chunk: bytes) -> list[bytes]:
        if chunk:
            self._pending.extend(chunk)

        frames: list[bytes] = []
        while True:
            try:
                marker = self._pending.index(0x55)
            except ValueError:
                self._pending.clear()
                return frames

            if marker:
                del self._pending[:marker]
            if len(self._pending) < 4:
                return frames

            if self._pending[:4] == OUTER_MAGIC:
                if len(self._pending) < OUTER_HEADER_LENGTH:
                    return frames
                inner_length = int.from_bytes(self._pending[4:8], "little")
                if not (DUML_MIN_LENGTH <= inner_length <= DUML_MAX_LENGTH):
                    del self._pending[0]
                    continue
                envelope_length = OUTER_HEADER_LENGTH + inner_length
                if len(self._pending) < envelope_length:
                    return frames
                inner = bytes(self._pending[8:envelope_length])
                if not _is_valid_duml(inner):
                    del self._pending[0]
                    continue
                frames.append(inner)
                del self._pending[:envelope_length]
                continue

            declared = int.from_bytes(self._pending[1:3], "little")
            direct_length = declared & 0x03FF
            header_valid = (
                DUML_MIN_LENGTH <= direct_length <= DUML_MAX_LENGTH
                and declared >> 10 == 1
                and calc_crc8(bytes(self._pending[:3])) == self._pending[3]
            )
            if not header_valid:
                del self._pending[0]
                continue
            if len(self._pending) < direct_length:
                return frames
            candidate = bytes(self._pending[:direct_length])
            if not _is_valid_duml(candidate):
                del self._pending[0]
                continue
            frames.append(candidate)
            del self._pending[:direct_length]


def deidentified_rid_events(chunks: Iterable[bytes]) -> list[dict[str, object]]:
    """Return strict RID summaries and silently ignore all unrelated telemetry.

    A route-shaped but unsupported RID variant is rejected rather than decoded
    heuristically.  The function never returns a raw frame or payload.
    """

    parser = LoopbackDumlStreamParser()
    events: list[dict[str, object]] = []
    for chunk in chunks:
        for frame in parser.feed(chunk):
            if frame[9] != RID_COMMAND_SET or frame[10] != RID_COMMAND_ID:
                continue
            try:
                status = parse_rid_working_status_frame(frame)
            except RidProtocolError:
                continue
            events.append(deidentified_summary(status))
    return events


def deidentified_flysafe_events(
    chunks: Iterable[bytes],
) -> list[dict[str, object]]:
    """Return only the two current FlySafe cache-update events.

    Area/whitelist pushes are known to coexist with RID telemetry in historical
    port-40007 captures.  This decoder exposes only the fields consumed by
    DJI Fly's current support/version gate; raw payloads and route identities
    are discarded.  A malformed candidate is ignored rather than guessed.
    """

    parser = LoopbackDumlStreamParser()
    events: list[dict[str, object]] = []
    for chunk in chunks:
        for frame in parser.feed(chunk):
            if frame[8] != CMD_TYPE_PUSH_PLAINTEXT:
                continue
            if frame[9] != CMD_SET_FLIGHT_CONTROLLER:
                continue
            command_id = frame[10]
            payload = frame[11:-2]
            if command_id == CMD_ID_AREA_INFO:
                try:
                    version = decode_area_unlock_version(payload)
                except FlySafeStateError:
                    continue
                events.append(
                    {
                        "event": "area_info",
                        "unlock_version": version,
                    }
                )
            elif command_id == CMD_ID_WHITE_LIST_INFO:
                try:
                    update = decode_whitelist_support(payload)
                except FlySafeStateError:
                    continue
                events.append(
                    {
                        "event": "whitelist_info",
                        "usable": update.usable,
                        "unlock_supported": update.supported,
                        "encoding": update.encoding,
                    }
                )
    return events
