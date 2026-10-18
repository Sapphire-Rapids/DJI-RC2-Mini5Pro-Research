import hashlib
import struct
import unittest

import imah_v2_key_probe as m


def mixed_chunk_fixture():
    # Frozen OpenSSL AES-128-CTR output, zero IV, content key bytes(range(16)).
    # Encrypted plaintexts: b"ABC" + b"\xa5" * 29, then
    # bytes(range(35)) + b"\x71" * 29. Clear b"LMNOP" and its 27-byte
    # storage gap are inserted afterward and must not advance the counter.
    payload = bytes.fromhex(
        "87e37892222afe27caea24c7046d7ddcd6e3b630306511bbecde1846c05188af"
        "4c4d4e4f50cccccccccccccccccccccccccccccccccccccccccccccccccccccc"
        "49d785509d9ea08beb8070636c8cbe92a9bc393d207fd42f48442c4580aae249"
        "104294ae7b5daac1f46320a3b718a0ceeaf3e8f81503f030312f52acee6ca16a"
    )
    header = bytearray(288)
    header[:4] = b"IM*H"
    struct.pack_into("<I", header, 4, 2)
    struct.pack_into("<I", header, 8, 800)
    struct.pack_into("<IIII", header, 16, 288, 384, 128, 800)
    struct.pack_into("<I", header, 36, 0x40003)
    header[40:48] = b"TESTTEST"
    # Frozen OpenSSL AES-256-ECB wrap under synthetic KEK bytes(range(32)).
    header[48:64] = bytes.fromhex("5a6e045708fb7196f02e553d02c3a692")
    # Checksums computed independently as little-endian word sums.
    struct.pack_into("<I", header, 108, 0xC019038D)
    struct.pack_into("<II", header, 152, 0x8FD5CB07, 3)
    header[160:192] = bytes.fromhex(
        "a2f08a1a00789a0cb83b7918afcdd1001b78fa66937f6a030badb6c9beba9473"
    )
    for i, fields in enumerate(((0, 3, 2), (32, 5, 3), (64, 35, 0))):
        struct.pack_into("<III", header, 196 + 32 * i, *fields)
    signature = bytes(range(256)) + bytes(range(128))
    return bytes(header) + signature + payload


class V2ProbeTest(unittest.TestCase):
    def test_aes_known_answer(self):
        # FIPS 197 AES-256 example, independent of the firmware/key hypothesis.
        key = bytes(range(32))
        plain = bytes.fromhex("00112233445566778899aabbccddeeff")
        encrypted = bytes.fromhex("8ea2b7ca516745bfeafc49904b496089")
        self.assertEqual(m.aes_ecb(plain, key), encrypted)
        self.assertEqual(m.aes_ecb(encrypted, key, decrypt=True), plain)

    def test_ctr_known_counter_blocks(self):
        # AES-128(0-key, counter=0) and AES-128(0-key, counter=1).
        expected = bytes.fromhex("66e94bd4ef8a2c3b884cfa59ca342b2e58e2fccefa7e3061367f1d57a4e7455a")
        self.assertEqual(m.ctr(bytes(32), bytes(16)), (expected, 2))
        self.assertEqual(m.ctr(bytes(16), bytes(16), 1), (expected[16:], 2))

    def test_wrapped_key_and_padding_checksum(self):
        # A two-byte logical chunk consumes/checksums all 32 decrypted bytes.
        content_key = bytes(16)
        kek = bytes(range(32))
        plain = b"AB" + b"Z" * 30
        encrypted, _ = m.ctr(plain, content_key)
        header = bytearray(224)
        header[:4] = b"IM*H"
        struct.pack_into("<I", header, 4, 2)
        struct.pack_into("<III", header, 16, 224, 0, 32)
        header[44:48] = b"TEST"
        header[48:64] = m.aes_ecb(content_key, kek)
        struct.pack_into("<II", header, 152, m.checksum(plain), 1)
        header[160:192] = hashlib.sha256(encrypted).digest()
        struct.pack_into("<III", header, 196, 0, 2, 0)
        struct.pack_into("<I", header, 108, (-(m.checksum(header) + m.checksum(encrypted))) & 0xFFFFFFFF)
        image = bytes(header) + encrypted
        self.assertTrue(m.probe(image, kek)["checksum_match"])
        self.assertTrue(m.probe(image, content_key, "content")["checksum_match"])
        self.assertFalse(m.probe(image, bytes(32))["checksum_match"])
        self.assertEqual(m.probe(image, kek)["ctr_blocks"], 2)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            m.probe(image[:-1] + bytes([image[-1] ^ 1]), kek)

    def test_mixed_chunks_keep_counter_and_checksum_boundaries(self):
        image = mixed_chunk_fixture()
        for kind, key in (("kek", bytes(range(32))), ("content", bytes(range(16)))):
            with self.subTest(kind=kind):
                result = m.probe(image, key, kind)
                self.assertTrue(result["checksum_match"])
                self.assertEqual(result["observed_plain_checksum"], "0x8fd5cb07")
                self.assertEqual(result["ctr_blocks"], 6)
                self.assertEqual(result["chunks"], [
                    {"index": 0, "logical_size": 3, "stored_size": 32, "encrypted": True},
                    {"index": 1, "logical_size": 5, "stored_size": 5, "encrypted": False},
                    {"index": 2, "logical_size": 35, "stored_size": 64, "encrypted": True},
                ])
                self.assertEqual(result["logical_output_sha256"],
                                 "bb86b92382e50d3a33ee6d264ef118c3133dd9530a0e7edaf156dc31a4467b30")
        changed_signature = bytearray(image)
        changed_signature[288] ^= 1
        self.assertTrue(m.probe(bytes(changed_signature), bytes(range(32)))["checksum_match"])

    def test_encrypted_checksum_rejects_tamper_after_digest_refresh(self):
        image = bytearray(mixed_chunk_fixture())
        image[-1] ^= 1
        image[160:192] = hashlib.sha256(image[288 + 384:]).digest()
        with self.assertRaisesRegex(ValueError, "Encrypted checksum mismatch"):
            m.probe(bytes(image), bytes(range(32)))

    def test_short_keys_rejected(self):
        with self.assertRaises(ValueError):
            m.aes_ecb(bytes(16), b"short")
        with self.assertRaises(ValueError):
            m.ctr(bytes(16), bytes(32))


if __name__ == "__main__":
    unittest.main()
