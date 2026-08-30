"""B2 dispatch composition through real mksh/Java; synthetic helpers, no USB."""
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

import test_receiver as common

B2 = common.SOURCE.with_name("rc2_sd_canary_bridge.sh")


@unittest.skipUnless(common.MKSH and common.JAVA and common.JAVAC, "set MKSH and provide a JDK")
class CanaryReceiverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.java_temp = tempfile.TemporaryDirectory(prefix="finduas-b2-java-")
        cls.classes = cls.java_temp.name
        source = Path(cls.classes) / "Launch.java"
        source.write_text(common.JAVA_SOURCE)
        subprocess.run([common.JAVAC, str(source)], check=True, capture_output=True, timeout=30)

    @classmethod
    def tearDownClass(cls):
        cls.java_temp.cleanup()

    def make_session(self, valid_hash=True):
        session = common.Session(self.classes, source=B2, script_name="B2.sh",
                                 start_marker="B2_START_REQUESTED", ttl=300)
        self.addCleanup(session.cleanup)
        helper = ("printf 'TEST_L1 argc=%s op=%s sid=%s\\n' \"$#\" \"$1\" \"$2\"\n"
                  "case \"$1\" in CANARY_BASELINE) exit 0 ;; CANARY_LOAD) exit 10 ;; "
                  "CANARY_CLEANUP) exit 0 ;; *) exit 99 ;; esac\n").encode()
        (session.base / "L1.sh").write_bytes(helper)
        expected = hashlib.sha256(helper).hexdigest() if valid_hash else "0" * 64
        session.script.write_text(re.sub(r"B1_L1_EXPECTED_SHA=[^\n]+",
                                        "B1_L1_EXPECTED_SHA=" + expected,
                                        session.script.read_text()))
        session.launch()
        self.assertEqual((session.session / "session.receiver").read_text(),
                         "B1 RECEIVER " + common.SID + " B2 END\n")
        return session

    def test_three_fixed_operations_keep_sid_and_only_two_helper_arguments(self):
        session = self.make_session()
        for seq, op, result in ((1, "CANARY_BASELINE", 0), (2, "CANARY_LOAD", 10),
                                (3, "CANARY_CLEANUP", 0)):
            session.put(seq, op)
            rc, report = session.result(seq)
            self.assertEqual(rc, result)
            self.assertIn("TEST_L1 argc=2 op=" + op + " sid=" + common.SID, report)
        session.put(4, "STOP")
        session.result(4)
        session.closed("STOP")

    def test_unpinned_helper_never_runs_and_can_stop(self):
        session = self.make_session(valid_hash=False)
        session.put(1, "CANARY_LOAD")
        rc, report = session.result(1)
        self.assertEqual(rc, 65)
        self.assertIn("HELPER_HASH_MISMATCH", report)
        self.assertNotIn("TEST_L1", report)
        session.put(2, "STOP")
        session.result(2)
        session.closed("STOP")


if __name__ == "__main__":
    unittest.main()
