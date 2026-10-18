import os
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

import stue_plaintext_probe as probe


def checksum(data):
    return sum(int.from_bytes(data[i:i + 4], "little")
               for i in range(0, len(data), 4)) & 0xFFFFFFFF


def metadata(size=32):
    return {"head_size": 0, "sig_size": 0, "chunks": [(0, size)],
            "scram": bytes([0x91]) * 16, "plain_cksum": 0}


class StueProbeTests(unittest.TestCase):
    def test_checksum_includes_partial_word(self):
        for size in range(8):
            data = bytes(range(1, size + 1))
            with self.subTest(size=size):
                expected = (checksum(data) + 0xFFFFFFFE) & 0xFFFFFFFF
                self.assertEqual(probe._checksum(data, 0xFFFFFFFE), expected)
                self.assertEqual(probe._checksum(data, 0xFFFFFFFE, negate=True),
                                 (-expected) & 0xFFFFFFFF)

    def test_encrypted_ranges_include_padding_and_reject_truncation(self):
        header = bytearray(224)
        header[:4] = b"IM*H"
        for offset, value in ((16, 224), (20, 384), (156, 1), (200, 30)):
            struct.pack_into("<I", header, offset, value)
        payload = bytes(range(32))
        struct.pack_into("<I", header, 108, (-checksum(header + payload)) & 0xFFFFFFFF)
        sig = bytes(header) + bytes(384) + payload
        self.assertTrue(probe.validate_ranges(sig, probe.parse(sig)))
        changed = sig[:-1] + b"\xff"
        self.assertFalse(probe.validate_ranges(changed, probe.parse(changed)))
        with self.assertRaisesRegex(ValueError, "truncated"):
            probe.validate_ranges(sig[:-1], probe.parse(sig))

    def test_ctr_checksums_padded_plaintext_for_nonword_chunk(self):
        data = bytes(range(30)) + b"\x55\xaa"
        meta = metadata(size=30)
        stream = bytes(16) + bytes(15) + b"\x01"
        plain = bytes(a ^ b for a, b in zip(data, stream))
        meta["plain_cksum"] = checksum(plain)
        self.assertNotEqual(checksum(plain[:30]), meta["plain_cksum"])
        with patch.object(probe, "encrypt_block", lambda b: b), \
             patch.object(probe, "decrypt_block", lambda b: b):
            hits = probe.try_schemes(data, meta)
        self.assertIn("ctr primitive=e order=big", hits)
        self.assertIn("ctr primitive=d order=big", hits)

    def test_ecb_tests_both_primitive_directions(self):
        data = bytes([0x50]) * 32
        encrypt = lambda b: bytes((x + 1) & 255 for x in b)
        decrypt = lambda b: bytes((x - 1) & 255 for x in b)
        for direction, primitive in (("e", encrypt), ("d", decrypt)):
            meta = metadata()
            meta["plain_cksum"] = checksum(primitive(data))
            with self.subTest(direction=direction), \
                 patch.object(probe, "encrypt_block", encrypt), \
                 patch.object(probe, "decrypt_block", decrypt):
                self.assertIn(f"ecb primitive={direction}", probe.try_schemes(data, meta))

    def test_cbc_resets_iv_for_each_padded_chunk(self):
        data = bytes(range(64))
        meta = metadata()
        meta["chunks"] = [(0, 12), (32, 12)]
        plain = data[:16] + bytes([16]) * 16 + data[32:48] + bytes([16]) * 16
        meta["plain_cksum"] = checksum(plain)
        with patch.object(probe, "encrypt_block", lambda b: b), \
             patch.object(probe, "decrypt_block", lambda b: b):
            hits = probe.try_schemes(data, meta)
        self.assertIn("cbc primitive=e iv=zero", hits)
        self.assertIn("cbc primitive=d iv=zero", hits)

    def test_fixed_primitive_probe_does_not_unwrap_scram(self):
        meta = metadata()
        def primitive(block):
            self.assertNotEqual(block, meta["scram"])
            return block
        with patch.object(probe, "encrypt_block", primitive), \
             patch.object(probe, "decrypt_block", primitive):
            hits = probe.try_schemes(bytes(range(32)), meta)
        self.assertTrue(all("ck=" not in hit for hit in hits))

    def test_rosetta_restart_selects_x86_64(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(probe.platform, "machine", return_value="arm64"), \
             patch.object(probe, "build_mirror", return_value=Path("/TEST-mirror")), \
             patch.object(probe.os, "execv") as execute:
            probe._reexec_under_rosetta("TEST.sig")
            executable, args = execute.call_args.args
            self.assertEqual(executable, "/usr/bin/arch")
            self.assertEqual(args[:3], ["arch", "-x86_64", "/TEST-mirror/MacOS/Python"])
            self.assertEqual(args[-1], "TEST.sig")
            self.assertEqual(os.environ["FIND_UAS_ROSETTA_REEXEC"], "1")

    def test_failed_rosetta_restart_cannot_loop(self):
        with patch.dict(os.environ, {"FIND_UAS_ROSETTA_REEXEC": "1"}), \
             patch.object(probe.platform, "machine", return_value="arm64"), \
             patch.object(probe, "build_mirror") as build:
            with self.assertRaisesRegex(RuntimeError, "did not select x86_64"):
                probe._reexec_under_rosetta("TEST.sig")
            build.assert_not_called()


if __name__ == "__main__":
    unittest.main()
