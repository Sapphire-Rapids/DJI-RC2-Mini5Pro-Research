from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import aes_decode_bridge as bridge


class AesDecodeBridgeTests(unittest.TestCase):
    def test_rejects_short_or_long_keys_before_native_call(self):
        with patch.object(bridge.subprocess, "run") as run, \
             patch.object(bridge.wb_aes_bridge, "build_mirror") as build:
            for size in (0, 16, 31, 33):
                with self.subTest(size=size), self.assertRaisesRegex(ValueError, "32 key bytes"):
                    bridge.decode2ex(bytes(16), bytes(size))
            run.assert_not_called()
            build.assert_not_called()

    def test_rejects_partial_ciphertext_blocks(self):
        with self.assertRaisesRegex(ValueError, "whole 16-byte"):
            bridge.decode2ex(bytes(15), bytes(32))

    def test_binary_transport_keeps_payload_and_key_out_of_argv(self):
        data = bytes(range(256)) * 2400
        key = bytes(range(32))
        output = b"\x00\xff\n\r "
        completed = subprocess.CompletedProcess([], 0, stdout=output, stderr=b"")
        with patch.object(bridge, "_ROOT", Path("/TEST-mirror")), \
             patch.object(bridge.subprocess, "run", return_value=completed) as run:
            self.assertEqual(bridge.decode2ex(data, key), output)
        args = run.call_args.args[0]
        kwargs = run.call_args.kwargs
        self.assertEqual(args[:2], ["/usr/bin/arch", "-x86_64"])
        self.assertEqual(len(args), 6)
        self.assertEqual(kwargs["input"], key + data)
        self.assertNotIn("text", kwargs)


class NativeAesDecodeBridgeTests(unittest.TestCase):
    def test_aes256_known_answer_with_zero_iv(self):
        # FIPS 197 AES-256 block vector; zero-IV CBC has the same first block.
        ciphertext = bytes.fromhex("8ea2b7ca516745bfeafc49904b496089")
        plaintext = bytes.fromhex("00112233445566778899aabbccddeeff")
        self.assertEqual(bridge.decode2ex(ciphertext, bytes(range(32))), plaintext)

    def test_payload_larger_than_previous_argument_limit(self):
        key = bytes(range(32))
        block = bridge.decode2ex(bytes(16), key)
        result = bridge.decode2ex(bytes(600000), key)
        self.assertEqual(result, block * (600000 // 16))


if __name__ == "__main__":
    unittest.main()
