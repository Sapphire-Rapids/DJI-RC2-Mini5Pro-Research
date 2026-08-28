from __future__ import annotations

from pathlib import Path
import unittest

import rid_rc2_loopback_parser as loopback
import rid_working_status_protocol as rid


BASE_DIR = Path(__file__).resolve().parent


def build_frame(
    *,
    command_set: int = 0x11,
    command_id: int = 0x1C,
    flags: int = 0x0101,
    area_code: int = 156,
    failure_code: int = 0,
    payload: bytes | None = None,
) -> bytes:
    if payload is None:
        payload = b"".join(
            (
                flags.to_bytes(2, "little"),
                area_code.to_bytes(4, "little", signed=True),
                bytes((failure_code,)),
            )
        )
    length = len(payload) + 13
    frame = bytearray((0x55, length & 0xFF, ((length >> 8) & 3) | 4))
    frame.append(rid.calc_crc8(frame))
    frame.extend((0x03, 0x02, 0x34, 0x12, 0x00, command_set, command_id))
    frame.extend(payload)
    frame.extend(rid.calc_crc16(frame).to_bytes(2, "little"))
    return bytes(frame)


def wrap(frame: bytes) -> bytes:
    return loopback.OUTER_MAGIC + len(frame).to_bytes(4, "little") + frame


class LoopbackFramingTests(unittest.TestCase):
    def test_accepts_direct_and_wrapped_frames_in_one_stream(self):
        first = build_frame(flags=0x0001)
        second = build_frame(flags=0x0101)
        parser = loopback.LoopbackDumlStreamParser()
        self.assertEqual(parser.feed(first + wrap(second)), [first, second])

    def test_waits_across_fragmented_outer_header_and_inner_frame(self):
        frame = build_frame()
        wire = wrap(frame)
        parser = loopback.LoopbackDumlStreamParser()
        found = []
        for split in (wire[:3], wire[3:7], wire[7:12], wire[12:]):
            found.extend(parser.feed(split))
        self.assertEqual(found, [frame])

    def test_resynchronises_after_noise_and_corrupt_envelope(self):
        corrupt = bytearray(wrap(build_frame()))
        corrupt[-1] ^= 1
        valid = build_frame(flags=0x0101)
        parser = loopback.LoopbackDumlStreamParser()
        self.assertEqual(parser.feed(b"noise" + corrupt + valid), [valid])


class PrivacyAndRidFilterTests(unittest.TestCase):
    def test_returns_only_deidentified_rid_summary(self):
        unrelated = build_frame(command_set=0x03, command_id=0x44)
        events = loopback.deidentified_rid_events(
            (unrelated, wrap(build_frame(flags=0x0101, failure_code=0)))
        )
        self.assertEqual(len(events), 1)
        keys = " ".join(events[0]).lower()
        for forbidden in ("raw", "payload", "frame", "serial", "uas_id", "gps"):
            self.assertNotIn(forbidden, keys)
        self.assertTrue(events[0]["is_rid_supported"])
        self.assertTrue(events[0]["is_rid_normal"])

    def test_rejects_route_shaped_unknown_payload_length(self):
        frame = bytearray(build_frame())
        payload = frame[11:-2] + b"\x00"
        length = len(payload) + 13
        changed = bytearray((0x55, length & 0xFF, ((length >> 8) & 3) | 4))
        changed.append(rid.calc_crc8(changed))
        changed.extend(frame[4:11])
        changed.extend(payload)
        changed.extend(rid.calc_crc16(changed).to_bytes(2, "little"))
        self.assertEqual(loopback.deidentified_rid_events((wrap(bytes(changed)),)), [])

    def test_parser_source_contains_no_network_or_write_primitive(self):
        source = (BASE_DIR / "rid_rc2_loopback_parser.py").read_text()
        for forbidden in ("import socket", "Socket(", "socket.", ".write(", "open("):
            self.assertNotIn(forbidden, source)


class FlySafeGateFilterTests(unittest.TestCase):
    def test_extracts_only_current_cache_update_fields(self):
        area = bytearray(8)
        area[3:5] = (2 << 14).to_bytes(2, "little")
        frames = (
            wrap(
                build_frame(
                    command_set=0x03,
                    command_id=0x09,
                    payload=bytes(area),
                )
            ),
            wrap(
                build_frame(
                    command_set=0x03,
                    command_id=0x42,
                    payload=bytes((10,)),
                )
            ),
        )
        events = loopback.deidentified_flysafe_events(frames)
        self.assertEqual(
            events,
            [
                {"event": "area_info", "unlock_version": 2},
                {
                    "event": "whitelist_info",
                    "usable": True,
                    "unlock_supported": True,
                    "encoding": "version_byte",
                },
            ],
        )
        text = repr(events).lower()
        for forbidden in ("raw", "payload", "frame", "serial", "gps"):
            self.assertNotIn(forbidden, text)

    def test_short_legacy_whitelist_is_seen_but_not_false(self):
        frame = wrap(
            build_frame(
                command_set=0x03,
                command_id=0x42,
                payload=bytes((9, 0, 0, 0)),
            )
        )
        self.assertEqual(
            loopback.deidentified_flysafe_events((frame,)),
            [
                {
                    "event": "whitelist_info",
                    "usable": False,
                    "unlock_supported": None,
                    "encoding": "short_legacy_no_update",
                }
            ],
        )

    def test_non_push_and_bad_area_payload_fail_closed(self):
        bad_area = build_frame(
            command_set=0x03,
            command_id=0x09,
            payload=b"\x00" * 7,
        )
        response = bytearray(
            build_frame(
                command_set=0x03,
                command_id=0x42,
                payload=bytes((10,)),
            )
        )
        response[8] = 0x80
        response[-2:] = rid.calc_crc16(response[:-2]).to_bytes(2, "little")
        self.assertEqual(
            loopback.deidentified_flysafe_events((bad_area, bytes(response))),
            [],
        )


if __name__ == "__main__":
    unittest.main()
