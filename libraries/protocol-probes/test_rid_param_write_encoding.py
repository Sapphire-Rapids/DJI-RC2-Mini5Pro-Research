"""Prevent unestablished multi-byte Boolean writes in the standalone codec."""

import unittest

import rid_param_protocol as protocol


class BooleanWriteEncodingTests(unittest.TestCase):
    def test_one_byte_payload_preserves_hash(self):
        for value in (b"\x00", b"\x01"):
            self.assertEqual(
                protocol.build_write_request_body(value, parameter_hash=0xF80992FE),
                b"\xfe\x92\x09\xf8" + value,
            )

    def test_integer_and_float_read_values_do_not_admit_writes(self):
        for raw in (b"\x00\x00", b"\x01\x00", b"\x01\x01\x01\x01", b"\x00\x00\x80\x3f"):
            with self.subTest(raw=raw), self.assertRaises(protocol.ParamProtocolError):
                protocol.build_write_request_body(raw, parameter_hash=0xF80992FE)

    def test_invalid_boolean_is_rejected(self):
        for raw in (b"", b"\x02"):
            with self.subTest(raw=raw), self.assertRaises(protocol.ParamProtocolError):
                protocol.build_write_request_body(raw, parameter_hash=0xF80992FE)


if __name__ == "__main__":
    unittest.main()
