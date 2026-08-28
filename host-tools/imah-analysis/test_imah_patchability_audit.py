#!/usr/bin/env python3
"""Regression checks for the read-only IMaH patchability audit."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from imah_patchability_audit import (
    DEFAULT_TOOL,
    DEFAULT_TOOL_COMMIT,
    audit,
    checksum_words,
)


ROOT = Path(__file__).resolve().parent
RC_POSITIVE = ROOT / "firmware/rc331/10.00.0700/0200/original/rc331_0200_v12.14.13.85_20260610.pro.fw.sig"
WA_ORIGINAL = ROOT / "firmware/wa150/01.00.0700/0802/original/wa150_0802_v10.00.15.17_20260723.ar2.pro.fw.sig"
WA_DONGLE = ROOT / "firmware/wa150/01.00.0700/0806/original/wa150_0806_v00.38.20.18_20251107_4GG4CN.pro.fw.sig"
WA_GNSS = ROOT / "firmware/wa150/01.00.0700/2603/original/wa150_2603_v01.05.03.01_20260508_uc6580.pro.fw.sig"


class PatchabilityAuditTests(unittest.TestCase):
    def require_artifacts(self, *paths: Path) -> None:
        missing = [str(path) for path in paths if not path.is_file()]
        if missing:
            self.skipTest("local firmware artifacts are absent")

    def test_pinned_upstream_identity(self) -> None:
        self.assertEqual(
            DEFAULT_TOOL_COMMIT,
            "195692263c2684cf1ddc4995f2736be6c0fb135e",
        )

    def test_checksum_words_is_little_endian_and_zero_pads_tail(self) -> None:
        self.assertEqual(checksum_words(b"\x01\x02\x03\x04"), 0x04030201)
        self.assertEqual(checksum_words(b"\x01\x02\x03\x04\x05"), 0x04030206)

    def test_public_key_positive_control(self) -> None:
        self.require_artifacts(RC_POSITIVE)
        report = audit(RC_POSITIVE, DEFAULT_TOOL)
        self.assertEqual(report["verified_public_auth_variants"], ["PRAK-2020-01"])
        self.assertTrue(report["payload_digest_matches"])
        self.assertTrue(report["encrypted_checksum_matches"])
        self.assertTrue(report["plaintext_bytes_available_without_decryption"])
        self.assertFalse(report["plaintext_checksum_verified"])
        self.assertFalse(report["verified_plaintext_available"])

    def test_wa150_original_stops_at_crypto_boundary(self) -> None:
        self.require_artifacts(WA_ORIGINAL)
        report = audit(WA_ORIGINAL, DEFAULT_TOOL)
        self.assertEqual(report["type"], "E3")
        self.assertEqual(report["anti_version"], 2)
        self.assertEqual(report["enc_key_fourcc"], "STUE")
        self.assertEqual(report["signature_size"], 384)
        self.assertTrue(report["payload_digest_matches"])
        self.assertTrue(report["encrypted_checksum_matches"])
        self.assertEqual(report["verified_public_auth_variants"], [])
        self.assertFalse(report["verified_plaintext_available"])
        self.assertFalse(report["safe_flashable_patch_ready"])

    def test_one_byte_probe_breaks_both_integrity_fields(self) -> None:
        self.require_artifacts(WA_GNSS)
        with tempfile.TemporaryDirectory() as directory:
            mutated = Path(directory) / "wa150_2603_one-byte-mutated.nonflashable.bin"
            shutil.copyfile(WA_GNSS, mutated)
            with mutated.open("r+b") as handle:
                handle.seek(608 + 0x1000)
                original = handle.read(1)
                self.assertEqual(len(original), 1)
                handle.seek(-1, 1)
                handle.write(bytes([original[0] ^ 0x01]))
            report = audit(mutated, DEFAULT_TOOL)
            self.assertFalse(report["payload_digest_matches"])
            self.assertFalse(report["encrypted_checksum_matches"])
            self.assertFalse(report["safe_flashable_patch_ready"])

    def test_wa150_0806_is_protected_dongle_module(self) -> None:
        self.require_artifacts(WA_DONGLE)
        report = audit(WA_DONGLE, DEFAULT_TOOL)
        self.assertEqual(report["type"], "DONG")
        self.assertEqual(report["enc_key_fourcc"], "STUE")
        self.assertEqual(report["signature_size"], 384)
        self.assertTrue(report["payload_digest_matches"])
        self.assertTrue(report["encrypted_checksum_matches"])
        self.assertEqual(report["verified_public_auth_variants"], [])
        self.assertFalse(report["verified_plaintext_available"])
        self.assertFalse(report["safe_flashable_patch_ready"])


if __name__ == "__main__":
    unittest.main()
