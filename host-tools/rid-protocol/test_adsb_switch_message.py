"""AirSense Boolean payload checks; no RID transmitter claim."""
import unittest
import adsb_switch_message as m


class AdsbPayloadTest(unittest.TestCase):
    def test_boolean_payload(self):
        self.assertEqual(m.build(0), b"\x00")
        self.assertEqual(m.build(1), b"\x01")
        self.assertEqual(m.build(7), b"\x01")


if __name__ == "__main__":
    unittest.main()
