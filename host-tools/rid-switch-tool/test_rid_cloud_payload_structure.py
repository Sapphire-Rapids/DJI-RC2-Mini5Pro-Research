import gzip
import json
import random
import unittest
import zlib

import rid_cloud_payload_structure as probe


def varint(value):
    out = bytearray()
    while value >= 128:
        out.append((value & 127) | 128); value >>= 7
    out.append(value)
    return bytes(out)


class StructureTests(unittest.TestCase):
    def test_json_named_boolean_candidate_does_not_claim_switch(self):
        payload = b'{"rid":{"enabled":true},"TEST-secret-key":"TEST-PRIVATE-VALUE"}'
        result = probe.analyze_bytes(payload)
        parsed = result["formats"]["json"]
        self.assertEqual(parsed["status"], "SYNTAX_VALID")
        self.assertEqual(parsed["named_boolean_candidates"][0]["path"], ["rid", "enabled"])
        self.assertIsNone(result["rid_switch_field"])
        encoded = json.dumps(result)
        self.assertNotIn("TEST-PRIVATE-VALUE", encoded)
        self.assertNotIn("TEST-secret-key", encoded)

    def test_json_duplicate_keys_nan_and_bad_unicode(self):
        for raw in [b'{"enabled":true,"enabled":false}', b'{"enabled":NaN}', b'{"a":"\\ud800"}']:
            self.assertEqual(probe.analyze_bytes(raw)["formats"]["json"]["status"], "NOT_ACCEPTED")

    def test_protobuf_varint_and_embedded_message_are_syntax_only(self):
        raw = b'\x08\x01\x12\x02\x08\x00'
        parsed = probe.analyze_bytes(raw)
        fields = parsed["formats"]["protobuf"]["fields"]
        self.assertEqual(parsed["formats"]["protobuf"]["status"], "SYNTAX_VALID")
        self.assertTrue(any(field.get("embedded_message_syntax") for field in fields))
        self.assertEqual(parsed["formats"]["protobuf"]["named_boolean_candidates"], [])
        self.assertIsNone(parsed["rid_switch_field"])

    def test_protobuf_bounds_canonical_encoding_and_unsupported_groups(self):
        for raw in [b'\x00', b'\x08\x80\x00', b'\x08' + b'\xff' * 9 + b'\x02',
                    b'\x12\xff\xff', b'\x09\x01', b'\x0b\x0c', varint(1 << 32) + b'\x00']:
            self.assertEqual(probe.analyze_bytes(raw)["formats"]["protobuf"]["status"], "NOT_ACCEPTED")

    def test_uint64_maximum_is_accepted_without_value_dump(self):
        parsed = probe.protobuf_structure(b'\x08' + varint((1 << 64) - 1), probe.Limits())
        self.assertEqual(parsed["fields"][0]["bit_width"], 64)
        self.assertNotIn("small_unsigned_value", parsed["fields"][0])

    def test_der_sequence_boolean_integer_and_octets(self):
        data = bytes.fromhex('30090101ff020101040100')
        result = probe.analyze_bytes(data)
        parsed = result["formats"]["asn1_tlv"]
        self.assertEqual(parsed["status"], "SYNTAX_VALID")
        self.assertEqual(len(parsed["fields"]), 4)
        self.assertIsNone(result["rid_switch_field"])
        self.assertEqual(parsed["named_boolean_candidates"], [])

    def test_der_rejects_nonminimal_indefinite_and_truncated_fields(self):
        for data in ['3000ff', '30800000', '010101', '02020001', '04810100', '1f1e00', '03020101', '060180']:
            with self.subTest(data=data):
                self.assertEqual(probe.analyze_bytes(bytes.fromhex(data))["formats"]["asn1_tlv"]["status"], "NOT_ACCEPTED")

    def test_compressed_json_and_crc_validation(self):
        data = b'{"rid":{"enabled":false}}'
        for name, compressed in [('zlib', zlib.compress(data)), ('gzip', gzip.compress(data, mtime=0))]:
            fmt = probe.analyze_bytes(compressed)["formats"][name]
            self.assertEqual(fmt["status"], "SYNTAX_VALID")
            self.assertEqual(fmt["uncompressed"]["formats"]["json"]["status"], "SYNTAX_VALID")
            self.assertEqual(probe.analyze_bytes(compressed + b'X')["formats"][name]["status"], "NOT_ACCEPTED")

    def test_decompression_bomb_is_bounded(self):
        result = probe.analyze_bytes(zlib.compress(b'A' * 1000), probe.Limits(payload_bytes=100))
        self.assertEqual(result["formats"]["zlib"]["reason"], "DECOMPRESSION_LIMIT")

    def test_fields_depth_and_payload_limits(self):
        self.assertEqual(probe.analyze_bytes(b'\x08\x00' * 10, probe.Limits(fields=4))["formats"]["protobuf"]["reason"], "LIMIT_EXCEEDED")
        raw = b'\x08\x01'
        for _ in range(5): raw = b'\x12' + varint(len(raw)) + raw
        self.assertEqual(probe.analyze_bytes(raw, probe.Limits(depth=2))["formats"]["protobuf"]["reason"], "LIMIT_EXCEEDED")
        with self.assertRaises(probe.Invalid): probe.analyze_bytes(b'AB', probe.Limits(payload_bytes=1))

    def test_hex_rejects_noncanonical_and_odd_and_limits(self):
        for raw in ['ABC', '00 11', '0x11', 'GG']:
            with self.assertRaises(probe.Invalid): probe.strict_hex(raw, probe.Limits())
        with self.assertRaises(probe.Invalid): probe.strict_hex('0001', probe.Limits(payload_bytes=1))
        self.assertEqual(probe.strict_hex('aAbB', probe.Limits()), b'\xaa\xbb')

    def test_pair_difference_varint_zero_one_not_switch(self):
        result = probe.analyze_pair('0801', '0800', default_present=True, matching_row_count=3)
        self.assertEqual(result["matching_row_count"], 3)
        self.assertEqual(result["byte_difference"]["changed_ranges"], [[1, 2]])
        changes = result["structure_difference"]["protobuf"]["changed_structural_fields"]
        self.assertEqual(changes[0]["matched"]["value_kind"], "ONE")
        self.assertEqual(changes[0]["default"]["value_kind"], "ZERO")
        self.assertIsNone(result["matched"]["rid_switch_field"])

    def test_absent_empty_and_uncaptured_default_are_distinct(self):
        self.assertEqual(probe.analyze_pair('0801', default_present=False)["default_state"], "MISSING")
        self.assertEqual(probe.analyze_pair('0801', '', default_present=True)["default_state"], "EMPTY")
        self.assertEqual(probe.analyze_pair('0801', default_present=True)["default_state"], "UNCAPTURED")
        with self.assertRaises(probe.Invalid): probe.analyze_pair('0801', '0800', default_present=False)
        with self.assertRaises(probe.Invalid): probe.analyze_pair('0801', default_present='true')

    def test_bounded_random_inputs_never_raise_outside_invalid(self):
        rng = random.Random(55)
        for _ in range(300):
            data = bytes(rng.randrange(256) for _ in range(rng.randrange(1, 80)))
            result = probe.analyze_bytes(data, probe.Limits(fields=100, depth=5))
            self.assertIsNone(result["rid_switch_field"])


if __name__ == '__main__': unittest.main()
