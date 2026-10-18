from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import wb_aes_bridge
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

    def test_build_mirror_preserves_existing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "TEST-existing-file"
            marker.write_bytes(b"keep")
            with patch.object(wb_aes_bridge, "MIRROR", root), \
                 self.assertRaises(FileExistsError):
                wb_aes_bridge.build_mirror()
            self.assertEqual(marker.read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
