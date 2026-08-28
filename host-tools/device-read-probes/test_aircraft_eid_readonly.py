import unittest
from pathlib import Path

import aircraft_eid_readonly as probe


class EIDPayloadTests(unittest.TestCase):
    def test_exact_disabled_response(self):
        self.assertEqual(probe.parse_eid_payload(b"\x00\x00"), "disabled")

    def test_exact_enabled_response(self):
        self.assertEqual(probe.parse_eid_payload(b"\x00\x01"), "enabled")

    def test_nonzero_status_is_not_mislabeled(self):
        self.assertEqual(
            probe.parse_eid_payload(b"\x03\x00"), "unsupported_or_error"
        )

    def test_unknown_bits_fail_closed(self):
        self.assertEqual(
            probe.parse_eid_payload(b"\x00\x02"), "unknown_state_bits"
        )

    def test_extensions_are_not_guessed(self):
        self.assertEqual(probe.parse_eid_payload(b"\x00\x01\x00"), "malformed")

    def test_short_payload_is_malformed(self):
        self.assertEqual(probe.parse_eid_payload(b"\x00"), "malformed")


class EIDWireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.duml = probe.load_duml_module()

    def test_fixed_get_is_product139_route_and_has_no_set_surface(self):
        request = probe.build_fixed_get(self.duml, source=0x0A, sequence=0x1234)
        self.assertTrue(probe.valid_crc(request, self.duml))
        self.assertEqual(request[4], 0x0A)
        self.assertEqual(request[5], 0x92)
        self.assertEqual(request[6:8], b"\x34\x12")
        self.assertEqual(request[8:11], b"\x40\x03\x77")
        self.assertEqual(request[11:-2], b"\x02")
        self.assertFalse(hasattr(probe, "build_set"))
        source = Path(probe.__file__).read_text(encoding="utf-8")
        self.assertEqual(source.count("bulkWrite("), 1)

    def test_fixed_get_can_use_direct_flyc_lab_route(self):
        request = probe.build_fixed_get(
            self.duml,
            source=0x0A,
            sequence=0x1234,
            receiver=probe.EID_RECEIVER_DIRECT_FLYC,
        )
        self.assertEqual(request[5], 0x03)
        self.assertEqual(request[8:11], b"\x40\x03\x77")
        self.assertEqual(request[11:-2], b"\x02")

        response = self.duml.build_packet(
            0x03, 0x0A, 0x80, 0x03, 0x77, b"\x00\x01", 0x1234
        )
        self.assertIsNotNone(
            probe.matching_get_response(
                response,
                duml=self.duml,
                expected_source=0x0A,
                expected_sequence=0x1234,
                expected_receiver=probe.EID_RECEIVER_DIRECT_FLYC,
            )
        )

    def test_get_response_requires_exact_reverse_route_sequence_and_shape(self):
        response = self.duml.build_packet(
            0x92, 0x0A, 0x80, 0x03, 0x77, b"\x00\x01", 0x1234
        )
        self.assertIsNotNone(
            probe.matching_get_response(
                response,
                duml=self.duml,
                expected_source=0x0A,
                expected_sequence=0x1234,
            )
        )
        for wrong in (
            self.duml.build_packet(0x91, 0x0A, 0x80, 0x03, 0x77, b"\x00\x01", 0x1234),
            self.duml.build_packet(0x92, 0x0B, 0x80, 0x03, 0x77, b"\x00\x01", 0x1234),
            self.duml.build_packet(0x92, 0x0A, 0x80, 0x03, 0x77, b"\x00\x01", 0x1235),
            self.duml.build_packet(0x92, 0x0A, 0x00, 0x03, 0x77, b"\x00\x01", 0x1234),
            self.duml.build_packet(0x92, 0x0A, 0xA0, 0x03, 0x77, b"\x00\x01", 0x1234),
            self.duml.build_packet(0x92, 0x0A, 0xE0, 0x03, 0x77, b"\x00\x01", 0x1234),
            self.duml.build_packet(0x92, 0x0A, 0x80, 0x04, 0x77, b"\x00\x01", 0x1234),
            self.duml.build_packet(0x92, 0x0A, 0x80, 0x03, 0x76, b"\x00\x01", 0x1234),
            self.duml.build_packet(0x92, 0x0A, 0x80, 0x03, 0x77, b"\x00", 0x1234),
            self.duml.build_packet(0x92, 0x0A, 0x80, 0x03, 0x77, b"\x00\x01\x00", 0x1234),
        ):
            self.assertIsNone(
                probe.matching_get_response(
                    wrong,
                    duml=self.duml,
                    expected_source=0x0A,
                    expected_sequence=0x1234,
                )
            )

    def test_get_response_accepts_only_the_closed_response_type_set(self):
        response = self.duml.build_packet(
            0x92, 0xAA, 0xC0, 0x03, 0x77, b"\x00\x00", 7
        )
        self.assertIsNotNone(
            probe.matching_get_response(
                response,
                duml=self.duml,
                expected_source=0xAA,
                expected_sequence=7,
            )
        )

    def test_crc_corruption_is_rejected(self):
        response = bytearray(
            self.duml.build_packet(
                0x92, 0x0A, 0x80, 0x03, 0x77, b"\x00\x01", 0x1234
            )
        )
        response[-1] ^= 1
        self.assertIsNone(
            probe.matching_get_response(
                bytes(response),
                duml=self.duml,
                expected_source=0x0A,
                expected_sequence=0x1234,
            )
        )

    def test_header_version_and_declared_length_corruption_are_rejected(self):
        exact = self.duml.build_packet(
            0x92, 0x0A, 0x80, 0x03, 0x77, b"\x00\x01", 0x1234
        )
        for offset, value in ((2, exact[2] ^ 0x04), (1, exact[1] + 1), (3, exact[3] ^ 1)):
            corrupt = bytearray(exact)
            corrupt[offset] = value
            self.assertFalse(probe.valid_crc(bytes(corrupt), self.duml))

    def test_simple_get_and_response(self):
        request = probe.build_fixed_get(
            self.duml,
            source=0x0A,
            sequence=0x1234,
            wire_mode="simple",
        )
        self.assertEqual(request[8] & 0x03, 3)
        interpreted = bytearray(request)
        interpreted[9:-2] = probe.simple_filter(
            bytes(interpreted[9:-2]), 0x1234
        )
        self.assertEqual(interpreted[9:-2], b"\x03\x77\x02")

        response = bytearray(
            self.duml.build_packet(
                0x92, 0x0A, 0x80, 0x03, 0x77, b"\x00\x01", 0x1234
            )
        )
        response[9:-2] = probe.simple_filter(bytes(response[9:-2]), 0x1234)
        response[8] |= 3
        response[-2:] = self.duml.calc_crc16(response, len(response) - 2).to_bytes(
            2, "little"
        )
        self.assertEqual(
            probe.matching_get_response(
                bytes(response),
                duml=self.duml,
                expected_source=0x0A,
                expected_sequence=0x1234,
            ),
            b"\x00\x01",
        )

    def test_false_plausible_header_cannot_block_a_later_valid_frame(self):
        valid = self.duml.build_packet(
            0x92, 0x0A, 0x80, 0x03, 0x77, b"\x00\x01", 0x1234
        )
        # DUML v1, declared length 511, but deliberately incomplete.
        pending = bytearray(b"\x55\xff\x05\x00noise" + valid)
        self.assertEqual(list(probe.extract_frames(pending, self.duml)), [valid])

    def test_both_usb_transport_configs_are_fixed_and_distinct(self):
        self.assertEqual(probe.TRANSPORTS["aircraft"]["source"], 0x0A)
        self.assertEqual(probe.TRANSPORTS["rc2"]["source"], 0xAA)
        self.assertNotEqual(
            probe.TRANSPORTS["aircraft"]["pid"], probe.TRANSPORTS["rc2"]["pid"]
        )


if __name__ == "__main__":
    unittest.main()
