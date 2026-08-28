#!/usr/bin/env python3
"""Regression checks for the non-flashable IMaH integrity probe."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from imah_nonflashable_patch_probe import NONFLASHABLE_SUFFIX, create_probe, validate_paths


ROOT = Path(__file__).resolve().parent
WA_GNSS = ROOT / "firmware/wa150/01.00.0700/2603/original/wa150_2603_v01.05.03.01_20260508_uc6580.pro.fw.sig"


class NonflashablePatchProbeTests(unittest.TestCase):
    def require_artifact(self, path: Path) -> None:
        if not path.is_file():
            self.skipTest("local firmware artifact is absent")

    def test_rejects_ambiguous_output_name_without_firmware_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "synthetic-source.dat"
            source.write_bytes(b"synthetic")
            with self.assertRaisesRegex(ValueError, "must end"):
                validate_paths(source, Path(directory) / "probe.dat")

    def test_rejects_output_inside_repository_without_firmware_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "synthetic-source.dat"
            source.write_bytes(b"synthetic")
            with self.assertRaisesRegex(ValueError, "repository"):
                validate_paths(source, ROOT / f"probe{NONFLASHABLE_SUFFIX}")

    def test_rejects_ambiguous_output_name(self) -> None:
        self.require_artifact(WA_GNSS)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "must end"):
                validate_paths(WA_GNSS, Path(directory) / "probe.bin")

    def test_one_byte_probe_repairs_only_public_ciphertext_fields(self) -> None:
        self.require_artifact(WA_GNSS)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / f"wa150_2603_integrity-probe{NONFLASHABLE_SUFFIX}"
            report = create_probe(WA_GNSS, output, payload_offset=0x1000, xor_mask=1)

            self.assertTrue(report["public_integrity_fields_recomputed"]["payload_digest_matches"])
            self.assertTrue(report["public_integrity_fields_recomputed"]["encrypted_checksum_matches"])
            self.assertTrue(report["signature"]["bytes_preserved"])
            self.assertTrue(report["signature"]["signed_region_changed"])
            self.assertFalse(report["signature"]["private_signing_key_available"])
            self.assertFalse(report["device_network_or_flash_capability"])
            self.assertFalse(report["safe_flashable_patch_ready"])
            self.assertNotEqual(report["source_sha256"], report["output_sha256"])
            self.assertEqual(os.stat(output).st_mode & 0o777, 0o444)

    def test_refuses_overwrite(self) -> None:
        self.require_artifact(WA_GNSS)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / f"existing{NONFLASHABLE_SUFFIX}"
            output.touch()
            with self.assertRaises(FileExistsError):
                validate_paths(WA_GNSS, output)

    def test_rejects_alternate_parser_module(self) -> None:
        self.require_artifact(WA_GNSS)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / f"alternate-tool{NONFLASHABLE_SUFFIX}"
            with self.assertRaisesRegex(ValueError, "pinned default"):
                create_probe(
                    WA_GNSS,
                    output,
                    payload_offset=0x1000,
                    tool_path=Path(__file__),
                )


if __name__ == "__main__":
    unittest.main()
