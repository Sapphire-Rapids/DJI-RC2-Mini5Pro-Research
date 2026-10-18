"""RID-005 action schema; fixture is synthetic and is not a valid OPID."""
import unittest
import opid_message as m


class OpidPayloadTest(unittest.TestCase):
    def test_distinct_get_delete_and_set(self):
        self.assertEqual(m.build_get(), b"\x02")
        self.assertEqual(m.build(b""), b"\x01")
        self.assertEqual(m.build(b"TESTONLY00000000"), b"\x00\x10TESTONLY00000000")

    def test_rejects_incomplete_or_full_registration_input(self):
        for size in (1, 15, 17, 20):
            with self.subTest(size=size), self.assertRaises(ValueError):
                m.build(b"T" * size)


if __name__ == "__main__":
    unittest.main()
