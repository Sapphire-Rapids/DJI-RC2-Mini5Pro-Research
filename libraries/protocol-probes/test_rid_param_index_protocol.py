"""Synthetic tests for the by-index FLYC parameter codec (0xE0--0xE3)."""

from __future__ import annotations

import unittest
from dataclasses import replace

import rid_param_index_protocol as p


def info_u8(name: str = "EU_CE_enable_c0_rid") -> p.ParamInfo:
    return p.ParamInfo(
        name=name,
        type_id=0,
        size=1,
        default_raw=b"\x00",
        minimum_raw=b"\x00",
        maximum_raw=b"\x01",
    )


class RequestTests(unittest.TestCase):
    def test_table_attributes_request(self):
        self.assertEqual(p.build_table_attributes_request(0), b"\x00\x00")

    def test_get_info_request(self):
        self.assertEqual(p.build_get_info_request(0, 1306), b"\x00\x00\x1a\x05")

    def test_read_value_request(self):
        self.assertEqual(p.build_read_value_request(0, 1306), b"\x00\x00\x01\x00\x1a\x05")

    def test_write_value_request(self):
        self.assertEqual(
            p.build_write_value_request(0, 1306, b"\x01", info=info_u8()),
            b"\x00\x00\x01\x00\x1a\x05\x01",
        )

    def test_write_value_width_is_enforced(self):
        with self.assertRaises(p.ParamIndexError):
            p.build_write_value_request(0, 1306, b"\x01\x00", info=info_u8())

    def test_index_out_of_range(self):
        with self.assertRaises(p.ParamIndexError):
            p.build_get_info_request(0, 0x10000)


class TableAttributesTests(unittest.TestCase):
    def test_valid(self):
        payload = b"\x00\x00" + b"\x00\x00" + (0x5F8B2AE1).to_bytes(4, "little") + (1557).to_bytes(4, "little")
        attrs = p.parse_table_attributes(payload)
        self.assertEqual(attrs.crc, 0x5F8B2AE1)
        self.assertEqual(attrs.count, 1557)

    def test_status_error(self):
        payload = b"\x03\x00" + b"\x00\x00" + bytes(8)
        with self.assertRaises(p.ParamIndexStatusError):
            p.parse_table_attributes(payload)

    def test_short_reply(self):
        with self.assertRaises(p.ParamIndexError):
            p.parse_table_attributes(b"\x00\x00")


class GetInfoTests(unittest.TestCase):
    def _payload(self, *, name=b"EU_CE_enable_c0_rid\x00", index=1306, type_id=0, size=1):
        return (
            b"\x00\x00"
            + b"\x00\x00"
            + index.to_bytes(2, "little")
            + type_id.to_bytes(2, "little")
            + size.to_bytes(2, "little")
            + b"\x00\x00\x00\x00"  # default
            + b"\x00\x00\x00\x00"  # min
            + b"\x01\x00\x00\x00"  # max
            + name
        )

    def test_valid_name_and_index(self):
        info = p.parse_get_info(
            self._payload(), expected_name="EU_CE_enable_c0_rid", expected_index=1306
        )
        self.assertEqual(info.name, "EU_CE_enable_c0_rid")
        self.assertEqual(info.type_id, 0)
        self.assertEqual(info.size, 1)

    def test_name_mismatch_fails(self):
        with self.assertRaises(p.ParamIndexError):
            p.parse_get_info(
                self._payload(name=b"other_param\x00"),
                expected_name="EU_CE_enable_c0_rid",
                expected_index=1306,
            )

    def test_index_mismatch_fails(self):
        with self.assertRaises(p.ParamIndexError):
            p.parse_get_info(
                self._payload(index=1307),
                expected_name="EU_CE_enable_c0_rid",
                expected_index=1306,
            )

    def test_status_error(self):
        payload = b"\x02\x00" + bytes(20)
        with self.assertRaises(p.ParamIndexStatusError):
            p.parse_get_info(payload, expected_name="x", expected_index=0)

    def test_missing_terminator_fails(self):
        payload = self._payload(name=b"EU_CE_enable_c0_rid")
        with self.assertRaises(p.ParamIndexError):
            p.parse_get_info(payload, expected_name="EU_CE_enable_c0_rid", expected_index=1306)


class ReadValueTests(unittest.TestCase):
    def _payload(self, *, value=b"\x01", index=1306):
        return b"\x00\x00\x00\x00" + index.to_bytes(2, "little") + value

    def test_valid_boolean(self):
        value = p.parse_read_value(self._payload(), index=1306, info=info_u8())
        self.assertEqual(value.decoded, 1)
        self.assertEqual(value.raw, b"\x01")

    def test_status_error(self):
        with self.assertRaises(p.ParamIndexStatusError):
            p.parse_read_value(b"\x01\x00\x00\x00" + bytes(3), index=1306, info=info_u8())

    def test_index_mismatch(self):
        with self.assertRaises(p.ParamIndexError):
            p.parse_read_value(self._payload(index=1307), index=1306, info=info_u8())

    def test_width_mismatch(self):
        with self.assertRaises(p.ParamIndexError):
            p.parse_read_value(self._payload(value=b"\x01\x00"), index=1306, info=info_u8())


class WriteTests(unittest.TestCase):
    def test_boolean_encoding(self):
        self.assertEqual(p.encode_boolean_value(True, info=info_u8()), b"\x01")
        self.assertEqual(p.encode_boolean_value(False, info=info_u8()), b"\x00")

    def test_unestablished_numeric_boolean_writes_are_rejected(self):
        for type_id, width in ((1, 2), (2, 4), (3, 8), (5, 2), (8, 4), (9, 8)):
            with self.subTest(type_id=type_id), self.assertRaises(p.ParamIndexError):
                p.encode_boolean_value(True, info=replace(info_u8(), type_id=type_id, size=width))

    def test_malformed_width_and_truthy_nonboolean_are_rejected(self):
        with self.assertRaises(p.ParamIndexError):
            p.encode_boolean_value(True, info=replace(info_u8(), type_id=11, size=4))
        with self.assertRaises(p.ParamIndexError):
            p.encode_boolean_value(2, info=info_u8())

    def test_write_status_ok(self):
        self.assertEqual(p.parse_write_status(b"\x00\x00\x00\x00"), 0)

    def test_write_status_error(self):
        with self.assertRaises(p.ParamIndexStatusError):
            p.parse_write_status(b"\x05\x00\x00\x00")


if __name__ == "__main__":
    unittest.main()
