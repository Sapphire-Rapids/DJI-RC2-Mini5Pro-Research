"""RID-005B product-139 payload checks with a synthetic tag."""
import unittest
import oid_identifier_message as m


class OidPayloadTest(unittest.TestCase):
    def test_set_copy_limit_and_padding(self):
        self.assertEqual(m.build(b"TEST1234"), b"\x01\x01TEST1234" + bytes(8))
        self.assertEqual(m.build(b"TEST1234EXCESS"), m.build(b"TEST1234"))
        self.assertEqual(m.build(b"TEST"), b"\x01\x01TEST" + bytes(12))

    def test_clear_and_deterministic_get(self):
        self.assertEqual(m.build(b""), b"\x01\x03" + bytes(16))
        self.assertEqual(m.build_get(), b"\x01\x02" + bytes(16))


if __name__ == "__main__":
    unittest.main()
