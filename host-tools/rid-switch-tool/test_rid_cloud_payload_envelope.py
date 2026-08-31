import contextlib
import io
import json
from pathlib import Path
import random
import stat
import struct
import tempfile
import unittest

import rid_cloud_payload_envelope as probe


def fixture(body=b"TEST-BODY", trailer=None, fields=(7, 9, 123456, 234567, 11)):
    """Synthetic offline envelope only; no vendor sample or device identifier."""
    if trailer is None:
        trailer = (b"TEST-OPAQUE-TAIL-" * 4)[:64]
    assert len(trailer) == 64
    a, b, c, d, e = fields
    return struct.pack("<IHHIIHH", probe.MAGIC_LE32, a, b, c, d, e, len(body)) + body + trailer


class EnvelopeTests(unittest.TestCase):
    def test_fixed_envelope_lengths_and_opaque_trailer(self):
        result = probe.analyze_bytes(fixture())
        self.assertTrue(result["envelope_structure_valid"])
        self.assertEqual(result["header"]["bytes"], 20)
        self.assertEqual(result["body"]["bytes"], 9)
        self.assertEqual(result["trailer"], {"offset": 29, "bytes": 64, "interpretation": "OPAQUE"})
        self.assertIsNone(result["body"]["layout_candidate"])
        self.assertIsNone(result["named_rid_switch_field"])

    def test_all_unnamed_header_fields_use_exact_offsets_and_widths(self):
        result = probe.analyze_bytes(fixture(fields=(0x1234, 0x5678, 0x12345678, 0x9abcdef0, 0xabcd)))
        fields = result["header"]["unnamed_fields"]
        self.assertEqual([(f["offset"], f["width_bytes"]) for f in fields],
                         [(0, 4), (4, 2), (6, 2), (8, 4), (12, 4), (16, 2), (18, 2)])
        self.assertEqual([f["unsigned_value"] for f in fields],
                         [probe.MAGIC_LE32, 0x1234, 0x5678, 0x12345678, 0x9abcdef0, 0xabcd, 9])
        encoded = json.dumps(result)
        for semantic in ("version", "timestamp", "expiry", "signature", "enabled"):
            self.assertNotIn(semantic, encoded)

    def test_13_byte_body_is_only_an_alignment_candidate(self):
        body = struct.pack("<BHHII", 1, 0x1234, 0x5678, 0x12345678, 0xfedcba98)
        result = probe.analyze_bytes(fixture(body))
        candidate = result["body"]["layout_candidate"]
        self.assertEqual(candidate["evidence"], "HYPOTHESIS")
        self.assertEqual(candidate["body_relative_offsets"], [0, 1, 3, 5, 9])
        self.assertEqual([f["offset"] for f in candidate["fields"]], [20, 21, 23, 25, 29])
        self.assertEqual([f["unsigned_value"] for f in candidate["fields"]],
                         [1, 0x1234, 0x5678, 0x12345678, 0xfedcba98])
        self.assertIsNone(result["named_rid_switch_field"])

    def test_exact_13_byte_layout_never_applied_to_other_lengths(self):
        for size in (0, 1, 12, 14, 256):
            with self.subTest(size=size):
                result = probe.analyze_bytes(fixture(bytes(size)))
                self.assertEqual(result["body"]["bytes"], size)
                self.assertIsNone(result["body"]["layout_candidate"])

    def test_repeated_candidate_covers_13_26_and_39_bytes(self):
        values = [(7, 0x1234, 0x0100, 123456, 654321),
                  (8, 0x5678, 0x0200, 234567, 765432),
                  (9, 0x9abc, 0x3405, 345678, 876543)]
        for count in (1, 2, 3):
            with self.subTest(count=count):
                body = b"".join(struct.pack("<BHHII", *row) for row in values[:count])
                result = probe.analyze_bytes(fixture(body))
                repeated = result["body"]["repeated_layout_candidate"]
                self.assertEqual(repeated["evidence"], "HYPOTHESIS")
                self.assertEqual(repeated["basis"], "UNNAMED_REPEATED_WIDTH_ALIGNMENT_ONLY")
                self.assertEqual(repeated["segment_bytes"], 13)
                self.assertEqual(repeated["segment_count"], count)
                self.assertEqual([row["body_relative_offset"] for row in repeated["segments"]],
                                 [index * 13 for index in range(count)])
                for index, row in enumerate(repeated["segments"]):
                    self.assertEqual([field["unsigned_value"] for field in row["fields"]],
                                     list(values[index]))
                    self.assertEqual([field["width_bytes"] for field in row["fields"]], [1, 2, 2, 4, 4])
                    self.assertEqual([field["offset"] for field in row["fields"]],
                                     [20 + index * 13 + offset for offset in (0, 1, 3, 5, 9)])
                if count == 1:
                    self.assertEqual(result["body"]["layout_candidate"]["fields"],
                                     repeated["segments"][0]["fields"])
                else:
                    self.assertIsNone(result["body"]["layout_candidate"])

    def test_repeated_candidate_requires_nonempty_exact_multiple(self):
        for size in (0, 1, 12, 14, 25, 27, 38, 40):
            with self.subTest(size=size):
                result = probe.analyze_bytes(fixture(bytes(size)))
                self.assertIsNone(result["body"]["repeated_layout_candidate"])

    def test_repeated_candidate_exposes_independent_bytes_at_3_and_4(self):
        body = struct.pack("<BHHII", 4, 5, 0x0100, 6, 7) + struct.pack("<BHHII", 8, 9, 0x0203, 10, 11)
        segments = probe.analyze_bytes(fixture(body))["body"]["repeated_layout_candidate"]["segments"]
        self.assertEqual([field["unsigned_value"] for field in segments[0]["alternative_u8_fields"]], [0, 1])
        self.assertEqual([field["unsigned_value"] for field in segments[1]["alternative_u8_fields"]], [3, 2])
        for index, segment in enumerate(segments):
            self.assertEqual([field["offset"] for field in segment["alternative_u8_fields"]],
                             [20 + index * 13 + 3, 20 + index * 13 + 4])
            self.assertEqual([field["width_bytes"] for field in segment["alternative_u8_fields"]], [1, 1])

    def test_repeated_count_does_not_use_header_offset_6(self):
        for header_value in (0, 1, 2, 65535):
            with self.subTest(header_value=header_value):
                result = probe.analyze_bytes(fixture(bytes(26), fields=(7, header_value, 123456, 234567, 11)))
                self.assertEqual(result["body"]["repeated_layout_candidate"]["segment_count"], 2)
                field = next(field for field in result["header"]["unnamed_fields"] if field["offset"] == 6)
                self.assertEqual(field["unsigned_value"], header_value)

    def test_repeated_candidate_remains_numeric_and_propagates_to_pair_capture(self):
        body = b"TEST-SEGMENT!" * 2
        result = probe.analyze_capture({"matched_hex": fixture(body).hex(),
                                        "default_hex": fixture(body[:13]).hex()})
        self.assertEqual(result["schema"], "finduas-cloud-policy-envelope-capture/v1")
        self.assertEqual(result["matched"]["schema"], "finduas-cloud-policy-envelope/v1")
        self.assertEqual(result["matched"]["body"]["repeated_layout_candidate"]["segment_count"], 2)
        self.assertEqual(result["default"]["body"]["repeated_layout_candidate"]["segment_count"], 1)
        self.assertIsNone(result["comparison"]["body_changed_candidate_fields"])
        encoded = json.dumps(result)
        for raw_or_name in (body.hex(), "TEST-SEGMENT", "TEST-OPAQUE", "signature", "enabled"):
            self.assertNotIn(raw_or_name, encoded)

    def test_truncation_magic_and_unclaimed_trailing_data_rejected(self):
        good = fixture()
        for raw, code in ((good[:83], "TRUNCATED_ENVELOPE"),
                          (b"TEST" + good[4:], "MAGIC_MISMATCH"),
                          (good[:-1], "LENGTH_MISMATCH"),
                          (good + b"X", "LENGTH_MISMATCH")):
            with self.subTest(code=code), self.assertRaisesRegex(probe.Invalid, "^" + code + "$"):
                probe.analyze_bytes(raw)

    def test_length_field_is_little_endian_not_scanned_from_other_positions(self):
        raw = bytearray(fixture(bytes(256)))
        self.assertEqual(raw[18:20], b"\x00\x01")
        self.assertEqual(probe.analyze_bytes(bytes(raw))["body"]["bytes"], 256)
        raw[18:20] = b"\x01\x00"
        with self.assertRaisesRegex(probe.Invalid, "LENGTH_MISMATCH"):
            probe.analyze_bytes(bytes(raw))

    def test_payload_limit_and_exact_limit(self):
        raw = fixture(bytes(probe.MAX_BYTES - 84))
        self.assertEqual(len(raw), probe.MAX_BYTES)
        self.assertEqual(probe.analyze_bytes(raw)["total_bytes"], probe.MAX_BYTES)
        with self.assertRaisesRegex(probe.Invalid, "LIMIT_EXCEEDED"):
            probe.analyze_bytes(raw + b"X")
        with self.assertRaisesRegex(probe.Invalid, "LIMIT_EXCEEDED"):
            probe.strict_hex("00" * (probe.MAX_BYTES + 1))

    def test_hex_type_character_and_length_boundaries(self):
        for value, code in ((None, "HEX_NOT_STRING"), (123, "HEX_NOT_STRING"),
                            ("A", "ODD_HEX_LENGTH"), ("0x12", "NON_CANONICAL_HEX"),
                            ("AA BB ", "NON_CANONICAL_HEX"), ("GG", "NON_CANONICAL_HEX")):
            with self.subTest(value=value), self.assertRaisesRegex(probe.Invalid, code):
                probe.strict_hex(value)
        self.assertEqual(probe.strict_hex("aAbB"), b"\xaa\xbb")
        with self.assertRaisesRegex(probe.Invalid, "BYTES_REQUIRED"):
            probe.analyze_bytes(bytearray(fixture()))

    def test_pair_locates_changed_candidate_fields_without_naming_switch(self):
        matched = fixture(struct.pack("<BHHII", 1, 5, 7, 64, 128))
        default = fixture(struct.pack("<BHHII", 0, 4, 0, 68, 9), fields=(7, 9, 123457, 234567, 11))
        result = probe.compare_bytes(matched, default)
        comparison = result["comparison"]
        self.assertEqual(comparison["header_changed_offsets"], [8])
        self.assertEqual(comparison["body_changed_offsets"], [20, 21, 23, 25, 29])
        self.assertEqual([f["body_relative_offset"] for f in comparison["body_changed_candidate_fields"]], [0, 1, 3, 5, 9])
        self.assertEqual(comparison["body_changed_candidate_fields"][0],
                         {"offset": 20, "body_relative_offset": 0, "width_bytes": 1,
                          "matched_unsigned": 1, "default_unsigned": 0})
        self.assertTrue(comparison["trailer_equal"])
        self.assertEqual(comparison["trailer_changed_byte_count"], 0)
        self.assertIsNone(result["named_rid_switch_field"])

    def test_trailer_alignment_when_body_lengths_differ(self):
        result = probe.compare_bytes(fixture(b"TEST"), fixture(b"TEST-MORE"))
        comparison = result["comparison"]
        self.assertEqual(comparison["body_changed_offsets"], [24, 25, 26, 27, 28])
        self.assertIsNone(comparison["body_changed_candidate_fields"])
        self.assertTrue(comparison["trailer_equal"])
        self.assertEqual(comparison["trailer_changed_byte_count"], 0)

    def test_trailer_changes_only_emit_counts_never_values(self):
        secret = b"TEST-PRIVATE-OPAQUE-CONTENT".ljust(64, b"!")
        other = bytes(value ^ 255 for value in secret)
        result = probe.compare_bytes(fixture(trailer=secret), fixture(trailer=other))
        self.assertEqual(result["comparison"]["trailer_changed_byte_count"], 64)
        self.assertFalse(result["comparison"]["trailer_equal"])
        encoded = json.dumps(result)
        self.assertNotIn("TEST-PRIVATE", encoded)
        self.assertNotIn(secret.hex(), encoded)
        self.assertNotIn(other.hex(), encoded)
        self.assertNotIn("TEST-BODY", encoded)

    def test_identical_pair(self):
        result = probe.compare_bytes(fixture(), fixture())["comparison"]
        self.assertTrue(result["identical"])
        self.assertEqual(result["header_changed_offsets"], [])
        self.assertEqual(result["body_changed_offsets"], [])

    def test_arbitrary_trailer_is_opaque_not_a_signature_validator(self):
        for trailer in (bytes(64), bytes([255]) * 64, bytes(range(64))):
            self.assertTrue(probe.analyze_bytes(fixture(trailer=trailer))["envelope_structure_valid"])

    def test_capture_presence_states_and_no_metadata_leak(self):
        base = {"matched_hex": fixture().hex(), "matching_row_count": 2,
                "TEST-extra": "TEST-PRIVATE-ACCOUNT"}
        for additional, state in (({}, "UNOBSERVED"), ({"default_present": False}, "MISSING"),
                                  ({"default_present": True}, "UNCAPTURED"),
                                  ({"default_present": True, "default_hex": ""}, "EMPTY"),
                                  ({"default_hex": fixture().hex()}, "NONEMPTY")):
            result = probe.analyze_capture(base | additional)
            self.assertEqual(result["default_state"], state)
            self.assertEqual(result["matching_row_count"], 2)
            self.assertNotIn("TEST-PRIVATE", json.dumps(result))
            self.assertNotIn("TEST-extra", json.dumps(result))

    def test_capture_metadata_errors_are_explicit(self):
        base = {"matched_hex": fixture().hex()}
        invalid = [{"default_present": "true"}, {"default_present": False, "default_hex": ""},
                   {"matching_row_count": True}, {"matching_row_count": 0}, {"matching_row_count": 257},
                   {"default_nonempty": "true"}, {"default_present": False, "default_nonempty": True},
                   {"default_hex": "", "default_nonempty": True},
                   {"default_hex": fixture().hex(), "default_nonempty": False}]
        for extra in invalid:
            with self.subTest(extra=extra), self.assertRaises(probe.Invalid):
                probe.analyze_capture(base | extra)
        for wrong in ([], None, {}, {"matched_hex": ""}):
            with self.assertRaises(probe.Invalid): probe.analyze_capture(wrong)

    def test_bounded_random_valid_envelopes_preserve_region_boundaries(self):
        rng = random.Random(5703)
        for _ in range(100):
            size = rng.randrange(0, 512)
            body = bytes(rng.randrange(256) for _ in range(size))
            trailer = bytes(rng.randrange(256) for _ in range(64))
            raw = fixture(body, trailer)
            result = probe.analyze_bytes(raw)
            self.assertEqual(result["body"]["bytes"], size)
            self.assertEqual(result["trailer"]["offset"], size + 20)
            changed = bytearray(raw)
            changed[-1] ^= 1
            comparison = probe.compare_bytes(raw, bytes(changed))["comparison"]
            self.assertEqual(comparison["body_changed_offsets"], [])
            self.assertEqual(comparison["trailer_changed_byte_count"], 1)

    def test_cli_new_private_output_no_raw_stdout_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="TEST-envelope-") as directory:
            source = Path(directory) / "TEST-input.json"
            output = Path(directory) / "TEST-output.json"
            original = json.dumps({"matched_hex": fixture().hex(), "default_present": False})
            source.write_text(original)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(probe.main([str(source), "--output", str(output)]), 0)
            self.assertEqual(stdout.getvalue(), "private envelope analysis saved\n")
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertNotIn("TEST-OPAQUE", output.read_text())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(probe.main([str(source), "--output", str(source)]), 2)
            self.assertEqual(source.read_text(), original)
            self.assertEqual(json.loads(output.read_text())["default_state"], "MISSING")

    def test_cli_malformed_duplicate_or_oversized_capture_has_no_output(self):
        with tempfile.TemporaryDirectory(prefix="TEST-envelope-") as directory:
            source = Path(directory) / "TEST-input.json"
            output = Path(directory) / "TEST-output.json"
            for text in ('{"matched_hex":"", "matched_hex":""}', '{"TEST": NaN}',
                         '[' * 2000, ' ' * (probe.MAX_CAPTURE_BYTES + 1)):
                source.write_text(text)
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    self.assertEqual(probe.main([str(source), "--output", str(output)]), 2)
                self.assertFalse(output.exists())
                self.assertEqual(stdout.getvalue(), "envelope analysis failed: invalid input or unavailable output\n")


if __name__ == "__main__":
    unittest.main()
