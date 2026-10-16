import unittest
from wb_aes_bridge import encrypt_block, decrypt_block


class WbAesBridgeTest(unittest.TestCase):
    def test_roundtrip(self):
        block = bytes(range(16))
        self.assertEqual(decrypt_block(encrypt_block(block)), block)

    def test_block_size(self):
        with self.assertRaises(ValueError):
            encrypt_block(b"short")

    def test_zero_and_ff(self):
        for b in (bytes(16), b"\xff" * 16):
            self.assertEqual(decrypt_block(encrypt_block(b)), b)


if __name__ == "__main__":
    unittest.main()
