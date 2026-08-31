import contextlib
import io
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest import mock

import rid_cloud_payload_signature as probe


def run_openssl(*args):
    result = subprocess.run(["openssl", *map(str, args)], stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    if result.returncode:
        raise AssertionError("TEST OpenSSL command failed")
    return result.stdout


def der_to_raw(der):
    # Test-only decoder for OpenSSL's short ECDSA SEQUENCE(INTEGER,INTEGER).
    assert der[0] == 0x30 and der[1] == len(der) - 2
    at = 2
    integers = []
    for _ in range(2):
        assert der[at] == 2
        length = der[at + 1]
        value = int.from_bytes(der[at + 2:at + 2 + length], "big")
        integers.append(value.to_bytes(32, "big"))
        at += 2 + length
    assert at == len(der)
    return b"".join(integers)


@unittest.skipUnless(shutil.which("openssl"), "OpenSSL required for independent signature tests")
class SignatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="TEST-policy-signature-")
        cls.directory = Path(cls.temp.name)
        cls.keys = []
        for name, curve in (("TEST-A", "prime256v1"), ("TEST-B", "prime256v1"), ("TEST-C", "secp384r1")):
            private = cls.directory / (name + "-private.pem")
            public = cls.directory / (name + "-public.pem")
            run_openssl("ecparam", "-name", curve, "-genkey", "-noout", "-out", private)
            run_openssl("pkey", "-in", private, "-pubout", "-out", public)
            cls.keys.append((private, public.read_bytes()))
        cls.matched = cls.signed(b"TEST-CURRENT-POLICY")
        cls.default = cls.signed(b"TEST-DEFAULT-POLICY")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def signed(cls, body, digest="sha256"):
        header = struct.pack("<IHHIIHH", probe.envelope.MAGIC_LE32, 7, 11, 123456, 234567, 13, len(body))
        message = header + body
        source = cls.directory / "TEST-message.bin"
        signature = cls.directory / "TEST-signature.der"
        source.write_bytes(message)
        run_openssl("dgst", "-" + digest, "-sign", cls.keys[0][0], "-out", signature, source)
        return message + der_to_raw(signature.read_bytes())

    def test_verifies_existing_big_endian_r_s_over_header_and_body(self):
        result = probe.verify_bytes(self.matched, self.keys[0][1])
        self.assertTrue(result["verified_with_supplied_key"])
        self.assertTrue(result["verification_ran"])
        self.assertTrue(result["signature_scalar_range_valid"])
        self.assertEqual(result["algorithm"], "ECDSA_P256_SHA256")
        self.assertEqual(result["signed_bytes"], len(self.matched) - 64)
        self.assertEqual(result["header_bytes"], 20)
        self.assertEqual(result["signature_bytes"], 64)

    def test_same_supplied_key_verifies_both_capture_members(self):
        capture = {"matched_hex": self.matched.hex(), "default_hex": self.default.hex(),
                   "default_present": True, "default_nonempty": True, "matching_row_count": 1,
                   "TEST-unrelated": "TEST-PRIVATE-ACCOUNT"}
        result = probe.verify_capture(capture, self.keys[0][1])
        self.assertTrue(result["matched"]["verified_with_supplied_key"])
        self.assertTrue(result["default"]["verified_with_supplied_key"])
        self.assertEqual(result["default_state"], "NONEMPTY")
        encoded = json.dumps(result)
        for private in ("TEST-PRIVATE", self.matched.hex(), self.default.hex(), "PUBLIC KEY", "TEST-CURRENT"):
            self.assertNotIn(private, encoded)

    def test_wrong_key_is_a_false_verification(self):
        result = probe.verify_bytes(self.matched, self.keys[1][1])
        self.assertTrue(result["verification_ran"])
        self.assertFalse(result["verified_with_supplied_key"])

    def test_sha384_signature_is_not_accepted_as_sha256(self):
        data = self.signed(b"TEST-DIFFERENT-DIGEST", digest="sha384")
        self.assertFalse(probe.verify_bytes(data, self.keys[0][1])["verified_with_supplied_key"])

    def test_header_body_and_trailer_tampering_detected(self):
        for offset in (8, 20, len(self.matched) - 1):
            with self.subTest(offset=offset):
                changed = bytearray(self.matched)
                changed[offset] ^= 1
                result = probe.verify_bytes(bytes(changed), self.keys[0][1])
                self.assertFalse(result["verified_with_supplied_key"])

    def test_r_s_order_and_scalar_byte_order_are_not_interchangeable(self):
        r, s = self.matched[-64:-32], self.matched[-32:]
        for tail in (s + r, r[::-1] + s[::-1]):
            result = probe.verify_bytes(self.matched[:-64] + tail, self.keys[0][1])
            self.assertFalse(result["verified_with_supplied_key"])

    def test_zero_or_out_of_range_scalars_skip_verification(self):
        for r in (0, probe.P256_ORDER, (1 << 256) - 1):
            raw = r.to_bytes(32, "big") + (1).to_bytes(32, "big")
            result = probe.verify_bytes(self.matched[:-64] + raw, self.keys[0][1])
            self.assertFalse(result["signature_scalar_range_valid"])
            self.assertFalse(result["verification_ran"])
            self.assertFalse(result["verified_with_supplied_key"])

    def test_reencoding_minimal_unsigned_integers(self):
        raw = (1).to_bytes(32, "big") + (2).to_bytes(32, "big")
        self.assertEqual(probe.raw_signature_to_der(raw), bytes.fromhex("3006020101020102"))
        raw = (128).to_bytes(32, "big") + (255).to_bytes(32, "big")
        self.assertEqual(probe.raw_signature_to_der(raw), bytes.fromhex("300802020080020200ff"))
        edge = (probe.P256_ORDER - 1).to_bytes(32, "big") * 2
        self.assertEqual(der_to_raw(probe.raw_signature_to_der(edge)), edge)

    def test_raw_signature_and_envelope_length_errors(self):
        for raw in (None, bytearray(64), b"", bytes(63), bytes(65)):
            with self.assertRaisesRegex(probe.Invalid, "SIGNATURE_LENGTH"):
                probe.raw_signature_to_der(raw)
        for data in (self.matched[:-1], self.matched + b"X", b"TEST" + self.matched[4:]):
            with self.assertRaises(probe.Invalid):
                probe.verify_bytes(data, self.keys[0][1])

    def test_public_key_must_be_named_p256(self):
        with self.assertRaisesRegex(probe.Invalid, "PUBLIC_KEY_NOT_NAMED_P256"):
            probe.verify_bytes(self.matched, self.keys[2][1])
        with self.assertRaisesRegex(probe.Invalid, "PUBLIC_KEY_PARSE_FAILED"):
            probe.verify_bytes(self.matched, b"TEST-INVALID-PEM")
        with self.assertRaisesRegex(probe.Invalid, "PUBLIC_KEY_PARSE_FAILED"):
            probe.verify_bytes(self.matched, self.keys[0][0].read_bytes())

    def test_compressed_p256_public_key_supported(self):
        public = self.directory / "TEST-compressed-public.pem"
        run_openssl("ec", "-in", self.keys[0][0], "-pubout", "-conv_form", "compressed", "-out", public)
        self.assertTrue(probe.verify_bytes(self.matched, public.read_bytes())["verified_with_supplied_key"])

    def test_missing_and_oversized_public_keys_rejected_before_openssl(self):
        with mock.patch.object(probe, "_openssl") as openssl:
            for key in (None, b"", b"X" * (probe.MAX_PUBLIC_KEY_BYTES + 1)):
                with self.assertRaises(probe.Invalid): probe.verify_bytes(self.matched, key)
            openssl.assert_not_called()

    def test_absent_empty_and_uncaptured_default_do_not_add_verification(self):
        for extra, state in (({"default_present": False}, "MISSING"),
                             ({"default_present": True}, "UNCAPTURED"),
                             ({"default_hex": "", "default_present": True}, "EMPTY")):
            result = probe.verify_capture({"matched_hex": self.matched.hex()} | extra, self.keys[0][1])
            self.assertEqual(result["default_state"], state)
            self.assertNotIn("default", result)
            self.assertTrue(result["matched"]["verified_with_supplied_key"])

    def test_openssl_unavailable_timeout_and_other_failures_are_sanitized(self):
        for failure, expected in ((FileNotFoundError("TEST-private-path"), "OPENSSL_UNAVAILABLE"),
                                  (subprocess.TimeoutExpired("TEST-secret-command", 5), "OPENSSL_TIMEOUT"),
                                  (OSError("TEST-private-path"), "OPENSSL_EXECUTION_FAILED")):
            with mock.patch.object(probe.subprocess, "run", side_effect=failure):
                with self.assertRaisesRegex(probe.Invalid, "^" + expected + "$"):
                    probe.verify_bytes(self.matched, self.keys[0][1])

    def test_cli_returns_only_summary_and_exit_status(self):
        source = self.directory / "TEST-capture.json"
        public = self.directory / "TEST-verification.pem"
        public.write_bytes(self.keys[0][1])
        source.write_text(json.dumps({"matched_hex": self.matched.hex(), "default_present": False}))
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(probe.main([str(source), "--public-key", str(public)]), 0)
        self.assertTrue(json.loads(stdout.getvalue())["matched"]["verified_with_supplied_key"])
        self.assertNotIn("TEST", stdout.getvalue())
        public.write_bytes(self.keys[1][1])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(probe.main([str(source), "--public-key", str(public)]), 1)
        source.write_text('{"matched_hex":"", "matched_hex":""}')
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(probe.main([str(source), "--public-key", str(public)]), 2)
        self.assertEqual(stdout.getvalue(), "signature verification failed: invalid input or verifier unavailable\n")


if __name__ == "__main__":
    unittest.main()
