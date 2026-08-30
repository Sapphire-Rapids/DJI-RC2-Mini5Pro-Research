"""Synthetic auditor regressions; no SDK, device, file output or APK execution."""

import unittest
from unittest.mock import patch

import audit_artifact as audit


def class_dump(owner, operation, number=1):
    return (f"Class #{number} -\n  Class descriptor  : '{owner}'\n"
            f"|0000: {operation}\n")


class ReportAuditTests(unittest.TestCase):
    def setUp(self):
        self.accepted = class_dump(
            audit.REPORT_WRITE_OWNER,
            "invoke-virtual {v0, v1, v2}, Landroid/content/ContentResolver;.openOutputStream:"
            "(Landroid/net/Uri;Ljava/lang/String;)Ljava/io/OutputStream;",
        ) + '|0001: const-string v0, "Download/FindUAS/Probe/"\n'
        descriptors, digest = audit.report_dex_fingerprint(self.accepted)
        self.profile_patch = patch.dict(audit.PROFILES["v11"], {
            "report_descriptors": descriptors, "report_dex_sha256": digest,
        })
        self.profile_patch.start()
        self.addCleanup(self.profile_patch.stop)

    def check(self, dump, profile="v11"):
        audit.audit_app_dex_safety(dump, enforce_frozen_surface=False, profile=profile)

    def test_reviewed_owner_and_exact_call_are_accepted(self):
        self.check(self.accepted)

    def test_v10_does_not_inherit_report_exception(self):
        with self.assertRaises(audit.AuditFailure):
            self.check(self.accepted, "v10")

    def test_other_classes_cannot_open_or_write_streams(self):
        for owner in ("Lcom/finduas/ridobserver/MainActivity;",
                      audit.REPORT_DESCRIPTOR + "$OtherWriter;"):
            for operation in (
                "invoke-virtual {v0, v1}, Ljava/io/OutputStream;.write:([B)V",
                "invoke-virtual {v0, v1, v2}, Landroid/content/ContentResolver;.openOutputStream:"
                "(Landroid/net/Uri;Ljava/lang/String;)Ljava/io/OutputStream;",
            ):
                with self.subTest(owner=owner, operation=operation):
                    with self.assertRaises(audit.AuditFailure):
                        self.check(self.accepted + class_dump(owner, operation, 2))

    def test_alternate_api_signature_is_not_in_the_exception(self):
        with self.assertRaises(audit.AuditFailure):
            self.check(self.accepted.replace(
                "(Landroid/net/Uri;Ljava/lang/String;)", "(Landroid/net/Uri;)"))

    def test_same_calls_with_different_output_literal_are_rejected(self):
        for value in ("/data/local/tmp/", "content://other/resource", "external_primary"):
            with self.subTest(value=value):
                with self.assertRaises(audit.AuditFailure):
                    self.check(self.accepted.replace("Download/FindUAS/Probe/", value))

    def test_unreviewed_new_writer_is_fail_closed(self):
        with patch.dict(audit.PROFILES["v11"], {"report_dex_sha256": None}):
            with self.assertRaisesRegex(audit.AuditFailure, "manual safety review"):
                self.check(self.accepted)

    def test_old_native_syscall_and_file_bans_apply_inside_writer(self):
        for operation in (
            "invoke-static {v0}, Ljava/lang/System;.load:(Ljava/lang/String;)V",
            "invoke-static {v0, v1, v2, v3}, Landroid/system/Os;.write:(Ljava/io/FileDescriptor;[BII)I",
            "new-instance v0, Ljava/io/FileOutputStream;",
            "new-instance v0, Ljava/util/zip/ZipOutputStream;",
        ):
            with self.subTest(operation=operation):
                with self.assertRaises(audit.AuditFailure):
                    self.check(self.accepted + f"|0002: {operation}\n")

    def test_legacy_profile_keeps_frozen_artifact_and_invoke_identity(self):
        self.assertEqual(audit.PROFILES["v10"]["external_count"], 2361)
        self.assertEqual(audit.PROFILES["v10"]["external_sha256"],
                         "c3b4ed26b563e2be2e4806b57ba0d21b8ea15ee3e6fa276d4223e0749d32ed29")
        self.assertEqual(audit.PROFILES["v10"]["sealed_sha256"],
                         "fdad29bfb1237bc224a805d6eb5a99358a044bd226610d9f0fc33975d94b606c")


if __name__ == "__main__":
    unittest.main()
