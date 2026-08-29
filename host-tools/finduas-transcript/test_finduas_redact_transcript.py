from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import finduas_redact_transcript as tool


class FindUASRedactTranscriptTest(unittest.TestCase):
    def record(self) -> dict:
        return {
            "uasID": "REAL-UAS-ID-DO-NOT-PUBLISH",
            "registrationID": "REAL-REGISTRATION-ID",
            "latitude": 12.345678,
            "longitude": 123.456789,
            "operatorLatitude": 12.345679,
            "operatorLongitude": 123.456788,
            "monitorID": "REAL-RECEIVER-ID",
            "operatorRegistrationPhone": "13800000000",
            "manufacturer": "Sensitive Manufacturer",
            "model": "Sensitive Model",
            "ridStandard": "GB42590-2023",
            "firstSeen": "2026-08-30T10:00:00Z",
            "lastSeen": "2026-08-30T10:01:00Z",
        }

    def test_summary_preserves_only_public_fields(self):
        record = self.record()
        summary = tool.summarize([record], digest_prefix=False)
        self.assertIn("Receiver-reported RID standard: GB42590-2023", summary)
        self.assertIn("Input records: 1", summary)
        self.assertIn("UAS ID present: yes", summary)
        self.assertIn("Location fields present: true", summary)
        self.assertIn("air bearer", summary)

    def test_summary_does_not_leak_private_values(self):
        record = self.record()
        summary = tool.summarize([record], digest_prefix=False)
        tool.assert_no_sensitive_values(summary, [record])
        for value in (
            record["uasID"],
            record["registrationID"],
            record["monitorID"],
            record["operatorRegistrationPhone"],
            record["manufacturer"],
            record["model"],
        ):
            self.assertNotIn(value, summary)
        self.assertNotIn("12.345678", summary)
        self.assertNotIn("123.456789", summary)

    def test_digest_is_stable_and_short(self):
        record = self.record()
        summary = tool.summarize([record], digest_prefix=True)
        prefix = tool.sha256_prefix(record["uasID"])
        self.assertIn(f"UAS ID digest prefix: {prefix}", summary)
        self.assertNotIn(record["uasID"], summary)

    def test_records_are_grouped_without_identity_order_dependence(self):
        first = self.record()
        second = self.record()
        second["uasID"] = "SECOND-REAL-UAS-ID"
        second["firstSeen"] = "2026-08-30T10:02:00Z"
        second["lastSeen"] = "2026-08-30T10:03:00Z"
        summary = tool.summarize([first, second], digest_prefix=False)
        self.assertIn("Distinct targets: 2", summary)
        self.assertIn("Target 1", summary)
        self.assertIn("Target 2", summary)

    def test_load_records_rejects_invalid_json_and_missing_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "telemetry.jsonl"
            path.write_text(json.dumps(self.record()) + "\n", encoding="utf-8")
            self.assertEqual(len(tool.load_records(path)), 1)

            path.write_text("{bad json}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid JSON"):
                tool.load_records(path)

            path.write_text(json.dumps({"latitude": 1.0}) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no non-empty uasID"):
                tool.load_records(path)

            path.write_text(json.dumps(["not", "an", "object"]) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not a JSON object"):
                tool.load_records(path)

    def test_sensitive_guard_rejects_direct_leak(self):
        record = self.record()
        with self.assertRaisesRegex(ValueError, "leaked value"):
            tool.assert_no_sensitive_values(record["uasID"], [record])


if __name__ == "__main__":
    unittest.main()
