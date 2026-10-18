"""Maximum-height query has no payload or fabricated transport header."""
import unittest
import height_message as m


class HeightPayloadTest(unittest.TestCase):
    def test_empty_payload(self):
        self.assertEqual(m.build(), b"")


if __name__ == "__main__":
    unittest.main()
