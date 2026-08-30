import importlib.util
from pathlib import Path
import sys
import types
import unittest


spec = importlib.util.spec_from_file_location(
    "passive_snapshot_test_subject", Path(__file__).with_name("usb_rid_passive_snapshot.py")
)
subject = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = subject
sys.modules.setdefault("usb1", types.ModuleType("usb1"))
spec.loader.exec_module(subject)


class RidExtensionTests(unittest.TestCase):
    def test_short_prefix_is_rejected(self):
        for length in range(7):
            self.assertIsNone(subject.parse_rid_status(bytes(length)))

    def test_extension_is_preserved_without_becoming_log_text(self):
        tail = b"TEST-PRIVATE-EXTENSION"
        snapshot = subject.parse_rid_status(bytes(7) + tail)
        self.assertEqual(snapshot.trailing_bytes, tail)
        self.assertIn("rid_supported=false", snapshot.summary)
        self.assertIn("trailing_length=22", str(snapshot))
        self.assertNotIn(tail.decode(), str(snapshot))
        self.assertNotIn(tail.decode(), repr(snapshot))
        self.assertNotIn(tail.hex(), subject.rid_summary(bytes(7) + tail))


if __name__ == "__main__":
    unittest.main()
