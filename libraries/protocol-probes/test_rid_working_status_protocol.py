from __future__ import annotations

from pathlib import Path
import unittest

import rid_working_status_listener as listener
import rid_working_status_protocol as protocol


BASE_DIR = Path(__file__).resolve().parent


def build_frame(
    payload: bytes,
    *,
    sender: int = 0x03,
    receiver: int = 0x0A,
    sequence: int = 0x1234,
    command_type: int = 0x00,
    command_set: int = 0x11,
    command_id: int = 0x1C,
    protocol_version: int = 1,
) -> bytes:
    length = 13 + len(payload)
    frame = bytearray(
        (
            0x55,
            length & 0xFF,
            ((length >> 8) & 0x03) | (protocol_version << 2),
        )
    )
    frame.append(protocol.calc_crc8(bytes(frame)))
    frame.extend((sender, receiver))
    frame.extend(sequence.to_bytes(2, "little"))
    frame.extend((command_type, command_set, command_id))
    frame.extend(payload)
    frame.extend(protocol.calc_crc16(bytes(frame)).to_bytes(2, "little"))
    return bytes(frame)


def status_payload(
    *, flags: int = 0, area_code: int = 0, failure_code: int = 0
) -> bytes:
    return b"".join(
        (
            flags.to_bytes(2, "little"),
            area_code.to_bytes(4, "little", signed=True),
            bytes((failure_code,)),
        )
    )


class RidFieldLayoutTests(unittest.TestCase):
    def test_exact_seven_byte_mapping(self):
        flags = (1 << 0) | (1 << 1) | (1 << 8) | (1 << 9) | (1 << 13)
        result = protocol.parse_rid_working_status_frame(
            build_frame(
                status_payload(flags=flags, area_code=156, failure_code=2),
                sender=0xAD,
                receiver=0x42,
                sequence=0xBEEF,
            )
        )
        self.assertEqual(result.sender, 0xAD)
        self.assertEqual(result.receiver, 0x42)
        self.assertEqual(result.sequence, 0xBEEF)
        self.assertEqual(result.flags_word, flags)
        self.assertTrue(result.is_eid_supported)
        self.assertTrue(result.is_rid_supported)
        self.assertTrue(result.is_eid_normal)
        self.assertTrue(result.is_rid_normal)
        self.assertEqual(result.area_code_value, 156)
        self.assertEqual(result.failure_code, 2)

    def test_each_primary_flag_is_independent(self):
        cases = (
            (1 << 1, "is_eid_supported"),
            (1 << 0, "is_rid_supported"),
            (1 << 9, "is_eid_normal"),
            (1 << 8, "is_rid_normal"),
        )
        for flag, expected_name in cases:
            with self.subTest(expected_name=expected_name):
                result = protocol.parse_rid_working_status_frame(
                    build_frame(status_payload(flags=flag))
                )
                values = {
                    "is_eid_supported": result.is_eid_supported,
                    "is_rid_supported": result.is_rid_supported,
                    "is_eid_normal": result.is_eid_normal,
                    "is_rid_normal": result.is_rid_normal,
                }
                self.assertEqual(
                    {name for name, enabled in values.items() if enabled},
                    {expected_name},
                )

    def test_area_code_is_the_signed_int_consumed_by_native_helper(self):
        result = protocol.parse_rid_working_status_frame(
            build_frame(status_payload(area_code=-1))
        )
        self.assertEqual(result.area_code_value, -1)

    def test_sender_receiver_are_reported_without_unproven_allow_list(self):
        result = protocol.parse_rid_working_status_frame(
            build_frame(status_payload(), sender=0x00, receiver=0xFF)
        )
        self.assertEqual((result.sender, result.receiver), (0x00, 0xFF))


class StrictFrameValidationTests(unittest.TestCase):
    def setUp(self):
        self.payload = status_payload(flags=(1 << 0) | (1 << 8))
        self.frame = build_frame(self.payload)

    def test_wrong_start_byte_is_rejected(self):
        changed = bytearray(self.frame)
        changed[0] = 0x54
        with self.assertRaisesRegex(protocol.RidProtocolError, "start byte"):
            protocol.parse_rid_working_status_frame(bytes(changed))

    def test_declared_length_mismatch_is_rejected(self):
        changed = bytearray(self.frame)
        changed[1] -= 1
        with self.assertRaisesRegex(protocol.RidProtocolError, "declared length"):
            protocol.parse_rid_working_status_frame(bytes(changed))

    def test_wrong_protocol_version_is_rejected_even_with_valid_crcs(self):
        changed = build_frame(self.payload, protocol_version=2)
        with self.assertRaisesRegex(protocol.RidProtocolError, "protocol version"):
            protocol.parse_rid_working_status_frame(changed)

    def test_bad_header_crc_is_rejected(self):
        changed = bytearray(self.frame)
        changed[3] ^= 1
        with self.assertRaisesRegex(protocol.RidProtocolError, "header CRC"):
            protocol.parse_rid_working_status_frame(bytes(changed))

    def test_bad_body_crc_is_rejected(self):
        changed = bytearray(self.frame)
        changed[-1] ^= 1
        with self.assertRaisesRegex(protocol.RidProtocolError, "body CRC"):
            protocol.parse_rid_working_status_frame(bytes(changed))

    def test_response_ack_or_encryption_types_are_rejected(self):
        for command_type in (0x03, 0x40, 0x80, 0xC0):
            with self.subTest(command_type=command_type):
                changed = build_frame(self.payload, command_type=command_type)
                with self.assertRaisesRegex(
                    protocol.RidProtocolError, "plaintext no-ACK push"
                ):
                    protocol.parse_rid_working_status_frame(changed)

    def test_wrong_command_route_is_rejected(self):
        for command_set, command_id in ((0x03, 0x1C), (0x11, 0x1D)):
            with self.subTest(command_set=command_set, command_id=command_id):
                changed = build_frame(
                    self.payload, command_set=command_set, command_id=command_id
                )
                with self.assertRaisesRegex(protocol.RidProtocolError, "route"):
                    protocol.parse_rid_working_status_frame(changed)

    def test_short_and_extended_payload_variants_fail_closed(self):
        for payload in (self.payload[:-1], self.payload + b"\x00"):
            with self.subTest(length=len(payload)):
                with self.assertRaisesRegex(
                    protocol.RidProtocolError, "seven-byte layout"
                ):
                    protocol.parse_rid_working_status_frame(build_frame(payload))


class StreamingExtractorTests(unittest.TestCase):
    def setUp(self):
        self.first = build_frame(status_payload(flags=1), sequence=1)
        self.second = build_frame(status_payload(flags=0x100), sequence=2)

    def test_waits_for_split_frame(self):
        pending = bytearray(self.first[:6])
        self.assertEqual(list(protocol.extract_valid_duml_frames(pending)), [])
        pending.extend(self.first[6:])
        self.assertEqual(
            list(protocol.extract_valid_duml_frames(pending)), [self.first]
        )
        self.assertEqual(pending, b"")

    def test_resynchronises_after_noise_and_bad_crc(self):
        corrupt = bytearray(self.first)
        corrupt[-1] ^= 1
        pending = bytearray(b"\x01\x02\x55\x00\x00\x00")
        pending.extend(corrupt)
        pending.extend(self.second)
        self.assertEqual(
            list(protocol.extract_valid_duml_frames(pending)), [self.second]
        )

    def test_yields_multiple_complete_frames(self):
        pending = bytearray(self.first + self.second)
        self.assertEqual(
            list(protocol.extract_valid_duml_frames(pending)),
            [self.first, self.second],
        )


class ScopedStateInterpretationTests(unittest.TestCase):
    def parse(self, *, supported=True, normal=False, failure=0):
        flags = (1 if supported else 0) | ((1 << 8) if normal else 0)
        return protocol.parse_rid_working_status_frame(
            build_frame(status_payload(flags=flags, failure_code=failure))
        )

    def test_msdk_5_18_us_industry_mapping(self):
        cases = (
            (dict(supported=False), "NOT_SUPPORTED"),
            (dict(normal=False), "IDLE"),
            (dict(normal=True), "WORKING"),
            (dict(failure=1), "OPERATOR_LOCATION_LOST_ERROR"),
            (dict(failure=2), "FIRMWARE_ERROR"),
            (dict(failure=99), "UNKNOWN_ERROR"),
        )
        for arguments, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(
                    protocol.msdk_5_18_us_industry_state(self.parse(**arguments)),
                    expected,
                )

    def test_summary_retains_no_raw_frame_or_identity_payload(self):
        summary = protocol.deidentified_summary(self.parse(normal=True))
        keys = " ".join(summary).lower()
        for forbidden in ("payload", "frame_hex", "uas_id", "gps", "serial"):
            self.assertNotIn(forbidden, keys)
        self.assertEqual(summary["msdk_5_18_us_industry_state"], "WORKING")


class ListenerSafetyTests(unittest.TestCase):
    def test_all_configured_endpoints_are_input_endpoints(self):
        self.assertTrue(listener.SOURCES)
        for spec in listener.SOURCES.values():
            self.assertEqual(spec.endpoint_in & 0x80, 0x80)

    def test_listener_source_contains_no_usb_write_call(self):
        source = (BASE_DIR / "rid_working_status_listener.py").read_text()
        for forbidden in ("bulk" + "Write", "control" + "Write", "interrupt" + "Write"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
