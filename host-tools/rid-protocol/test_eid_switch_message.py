"""France EID payload schema checks; no global RID or device claim."""
import unittest
import eid_switch_message as m


class EidPayloadTest(unittest.TestCase):
    def test_get_and_set_bodies(self):
        self.assertEqual(m.build_get(), b"\x02")
        self.assertEqual(m.build(0), b"\x00")
        self.assertEqual(m.build(1), b"\x01")

    def test_rejects_unknown_actions(self):
        for value in (-1, 2, 256):
            with self.subTest(value=value), self.assertRaises(ValueError):
                m.build(value)


if __name__ == "__main__":
    unittest.main()
