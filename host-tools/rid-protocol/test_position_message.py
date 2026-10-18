"""Synthetic codec checks; no device key, identifiers or transport."""
import hashlib
import hmac
import struct
import unittest

from Crypto.Cipher import AES
import position_message as m


class PositionPayloadTest(unittest.TestCase):
    def setUp(self):
        self.key = bytes(range(32))
        self.iv = bytes(range(16))
        self.plain = bytes(range(22))

    def test_independent_openssl_fixture(self):
        # Frozen outputs from openssl enc -aes-256-cbc and dgst -sha256 -mac HMAC.
        expected = bytes.fromhex(
            "50000000f29000b62a499fd0a9f39a6add2e7780"
            "66cd38c6a5d1be88377235c01425ed06"
            "000102030405060708090a0b0c0d0e0f"
            "cddce378263ab2ed727535c5f4e46fc2f7ce3903643b2d68b14019e83ed32f10"
        )
        self.assertEqual(m.build(self.plain, self.key, self.iv), expected)

    def test_payload_sections_and_authentication(self):
        result = m.build(self.plain, self.key, self.iv)
        self.assertEqual(len(result), 84)
        self.assertEqual(struct.unpack_from("<I", result)[0], 80)
        self.assertEqual(result[36:52], self.iv)
        self.assertEqual(AES.new(self.key, AES.MODE_CBC, self.iv).decrypt(result[4:36]),
                         self.plain + bytes([10]) * 10)
        self.assertEqual(result[52:], hmac.new(self.key, result[4:52], hashlib.sha256).digest())

    def test_rejects_old_wrapped_key_and_invalid_lengths(self):
        for plain, key, iv in [(bytes(21), self.key, self.iv),
                               (bytes(23), self.key, self.iv),
                               (self.plain, bytes(48), self.iv),
                               (self.plain, bytes(31), self.iv),
                               (self.plain, self.key, bytes(15))]:
            with self.subTest(lengths=tuple(map(len, (plain, key, iv)))):
                with self.assertRaises(ValueError):
                    m.build(plain, key, iv)

    def test_different_iv_changes_ciphertext_and_authenticator(self):
        first = m.build(self.plain, self.key, self.iv)
        second = m.build(self.plain, self.key, bytes(16))
        self.assertNotEqual(first[4:36], second[4:36])
        self.assertNotEqual(first[52:], second[52:])


if __name__ == "__main__":
    unittest.main()
