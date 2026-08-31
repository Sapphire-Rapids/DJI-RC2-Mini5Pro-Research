"""B6 fixed policy dispatch through real mksh/Java, with no device access."""
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

import test_receiver as common


B6 = common.SOURCE.with_name("rc2_sd_catalog_bridge.sh")


@unittest.skipUnless(common.MKSH and common.JAVA and common.JAVAC, "set MKSH and provide a JDK")
class CatalogReceiverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.java_temp = tempfile.TemporaryDirectory(prefix="finduas-b4-java-")
        cls.classes = cls.java_temp.name
        source = Path(cls.classes) / "Launch.java"
        source.write_text(common.JAVA_SOURCE)
        subprocess.run([common.JAVAC, str(source)], check=True, capture_output=True, timeout=30)

    @classmethod
    def tearDownClass(cls):
        cls.java_temp.cleanup()

    def session(self, valid_hash=True, replace_helper=False):
        session = common.Session(self.classes, source=B6, script_name="B6.sh",
                                 start_marker="B6_START_REQUESTED", ttl=300)
        self.addCleanup(session.cleanup)
        helper = ("printf 'TEST_L5 argc=%s op=%s sid=%s\\n' \"$#\" \"$1\" \"$2\"\n"
                  "case \"$1\" in CATALOG_BASELINE) exit 0 ;; CATALOG_READ) exit 10 ;; "
                  "CATALOG_CLEANUP) exit 0 ;; *) exit 99 ;; esac\n").encode()
        (session.base / "L5.sh").write_bytes(helper)
        expected = hashlib.sha256(helper).hexdigest() if valid_hash else "0" * 64
        session.script.write_text(re.sub(r"B1_L5_EXPECTED_SHA=[^\n]+",
                                        "B1_L5_EXPECTED_SHA=" + expected, session.script.read_text()))
        if replace_helper: session.env["B1_TEST_REPLACE_F4"] = str(session.base / "L5.sh")
        session.launch()
        self.assertEqual((session.session / "session.receiver").read_text(),
                         "B1 RECEIVER " + common.SID + " B6 END\n")
        return session

    def test_fixed_policy_operations_and_old_canary_operation_rejected(self):
        session = self.session()
        for seq, op, result in ((1, "PING", 0), (2, "CATALOG_BASELINE", 0),
                                (3, "CATALOG_READ", 10), (4, "CATALOG_CLEANUP", 0),
                                (5, "CANARY_LOAD", 65), (6, "RID_READ", 65)):
            session.put(seq, op)
            rc, report = session.result(seq)
            self.assertEqual(rc, result)
            if op.startswith("CATALOG_"):
                self.assertIn("TEST_L5 argc=2 op=" + op + " sid=" + common.SID, report)
            elif op in ("CANARY_LOAD", "RID_READ"): self.assertNotIn("TEST_L5", report)
        session.put(7, "STOP"); session.result(7); session.closed("STOP")

    def test_wrong_helper_hash_never_executes(self):
        session = self.session(valid_hash=False)
        session.put(1, "CATALOG_READ")
        rc, report = session.result(1)
        self.assertEqual(rc, 65); self.assertNotIn("TEST_L5", report)
        self.assertIn("HELPER_HASH_MISMATCH", report)
        session.put(2, "STOP"); session.result(2); session.closed("STOP")

    def test_verified_ram_snapshot_survives_file_replacement(self):
        session = self.session(replace_helper=True)
        session.put(1, "CATALOG_BASELINE")
        rc, report = session.result(1)
        self.assertEqual(rc, 0)
        self.assertIn("TEST_L5 argc=2 op=CATALOG_BASELINE", report)
        self.assertNotIn("UNVERIFIED_FILE_EXECUTED", report)
        self.assertIn("UNVERIFIED_FILE_EXECUTED", (session.base / "L5.sh").read_text())
        session.put(2, "STOP"); session.result(2); session.closed("STOP")


if __name__ == "__main__":
    unittest.main()
