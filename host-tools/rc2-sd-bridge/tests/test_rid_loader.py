"""Real mksh L2 lifecycle tests using synthetic payloads and command responses.

The old L1 fixture is reused without changing it. The new loader's actual
exclusive copy, descriptor checks, receipts and unlink remain intact.
"""
import hashlib
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import unittest

import test_canary_loader as common


SOURCE = common.SOURCE.with_name("rc2_rid_cache_loader.sh")
SID = common.SID


def native_text(sid=SID, pid=4242, uid=10123, mode="value"):
    base = f"schema=finduas-rid-cache/v1 phase={{phase}} sid={sid} pid={pid} uid={uid} gid={uid} abi_bits=32"
    values = dict(ready=1, stage=0, exception=0, query_count=1, value_present=1,
                  rid_support=1, rid_normal=1, eid_support=0, eid_normal=0,
                  fail_reason=0, jni_rc=0, env_rc=0, parse_rc=0,
                  dispose_attempted=1, dispose_rc=0)
    if mode in ("null", "failure", "dispose_failure"):
        values.update(value_present=0, rid_support=-1, rid_normal=-1,
                      eid_support=-1, eid_normal=-1, fail_reason=0)
    if mode == "null": values["parse_rc"] = 1
    if mode == "failure": values.update(ready=0, stage=6, exception=1, query_count=0, parse_rc=-1)
    if mode == "dispose_failure": values.update(ready=0, stage=13, dispose_rc=113)
    if mode == "zero_value": values.update(rid_support=0, rid_normal=0, eid_support=0, eid_normal=0, fail_reason=7)
    if mode == "bad_count": values["query_count"] = 2
    if mode == "bad_null": values.update(value_present=0, parse_rc=1)
    if mode == "bad_ready": values["ready"] = 0
    enter = base.format(phase="enter") + "\n"
    result = base.format(phase="result") + " " + " ".join(f"{key}={value}" for key, value in values.items()) + "\n"
    if mode == "malformed": result = result.replace(" dispose_rc=0", "")
    if mode == "no_enter": return result
    if mode == "duplicate": return enter + result + result
    return enter + result


class Fixture(common.Fixture):
    def __init__(self):
        super().__init__()
        self.target = self.root / "data/app/finduas_A051_rid_cache.so"
        source = self.base / "FindUAS_RID_CACHE.so"
        self.payload.rename(source); self.payload = source
        self.receipt = self.probe / "A051_copy.receipt"
        self.marker = self.probe / "A051_attach.attempted"
        mock_source = common.MOCK_SOURCE
        for old, new in (("L1_TEST_ROOT", "L2_TEST_ROOT"),
                         ("finduas_A048_identity.so", "finduas_A051_rid_cache.so"),
                         ("FindUAS_ARTTI_V2.so", "FindUAS_RID_CACHE.so"),
                         ("A048_copy.receipt", "A051_copy.receipt"),
                         ("A048_attach.attempted", "A051_attach.attempted"),
                         ("FindUAS-ARTTI-Identity:I", "FindUAS-RID-Cache:I"),
                         ("FindUAS-Loader", "FindUAS-RID-Loader")):
            mock_source = mock_source.replace(old, new)
        (self.bin / "mock.py").write_text("#!" + sys.executable + "\n" + mock_source)
        text = SOURCE.read_text()
        text = re.sub(r"^L2_SHA=.*$", "L2_SHA=" + hashlib.sha256(common.PAYLOAD).hexdigest(), text, flags=re.M)
        text = re.sub(r"^L2_SIZE=.*$", "L2_SIZE=" + str(len(common.PAYLOAD)), text, flags=re.M)
        text = re.sub(r"^L2_APK_SHA=.*$", "L2_APK_SHA=" + hashlib.sha256(common.APK).hexdigest(), text, flags=re.M)
        text = text.replace("/storage/", str(self.root / "storage") + "/")
        text = text.replace("/data/app", str(self.root / "data/app"))
        text = text.replace("/proc/sys/kernel/random/boot_id", str(self.boot))
        path = str(self.bin) + os.pathsep + "/usr/bin:/bin"
        text = text.replace("PATH=/system/bin", "PATH=" + shlex.quote(path) +
                            "\ncat() { " + shlex.quote(str(self.bin / "cat")) + ' "$@"; }')
        self.script = self.base / "L2.sh"; self.script.write_text(text)
        self.env["L2_TEST_ROOT"] = str(self.root)

    def set_native(self, **kwargs):
        (self.root / "result.fixture").write_text(native_text(**kwargs))

    def publish_native(self, **kwargs):
        (self.root / "native.log").write_text(native_text(**kwargs))

    def run(self, operation, sid=SID):
        result = subprocess.run([common.MKSH, str(self.script), operation, sid], env=self.env,
                                text=True, capture_output=True, timeout=30)
        if result.stderr: raise AssertionError(result.stderr)
        expected = f"schema=finduas-rc2-rid-cache-loader/v1\nsid={sid}\noperation={operation}\n"
        if not result.stdout.startswith(expected) or not result.stdout.endswith("report_end=true\n"):
            raise AssertionError(result.stdout)
        return result.returncode, result.stdout


@unittest.skipUnless(common.REQUESTED_MKSH, "Set MKSH to run L2 host integration")
class RidLoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not common.MKSH: raise RuntimeError("MKSH must be executable")

    def fixture(self):
        fixture = Fixture(); self.addCleanup(fixture.temp.cleanup)
        return fixture

    def test_value_read_once_and_cleanup(self):
        f = self.fixture()
        self.assertEqual(f.run("RID_BASELINE")[0], 0)
        self.assertFalse(f.target.exists()); self.assertEqual(f.count("attach"), 0)
        rc, output = f.run("RID_READ")
        self.assertEqual(rc, 0, output)
        self.assertIn("rid_cache_state=VALUE_RECEIVED\n", output)
        self.assertIn("native_query_count=1\n", output)
        self.assertIn("rid_support=1\nrid_normal=1\neid_support=0\neid_normal=0\n", output)
        self.assertEqual(f.count("descriptor_stat"), 1)
        self.assertEqual(f.count("attach"), 1); self.assertEqual(f.count("remove"), 1)
        self.assertFalse(f.target.exists()); self.assertTrue(f.marker.exists()); self.assertTrue(f.receipt.exists())
        self.assertNotEqual(f.run("RID_READ")[0], 0)
        self.assertEqual(f.count("attach"), 1)

    def test_null_cache_is_terminal_unknown_and_does_not_block_cleanup(self):
        f = self.fixture(); f.set_native(mode="null")
        rc, output = f.run("RID_READ")
        self.assertEqual(rc, 10, output)
        self.assertIn("rid_cache_state=UNKNOWN\n", output)
        self.assertIn("native_value_present=0\nnative_query_count=1\n", output)
        self.assertIn("rid_support=-1\nrid_normal=-1\neid_support=-1\neid_normal=-1\n", output)
        self.assertFalse(f.target.exists()); self.assertTrue(f.marker.exists())
        self.assertEqual(f.run("RID_CLEANUP")[0], 0)
        self.assertEqual(f.count("attach"), 1)

    def test_present_zero_values_are_not_confused_with_absence(self):
        f = self.fixture(); f.set_native(mode="zero_value")
        rc, output = f.run("RID_READ")
        self.assertEqual(rc, 0, output)
        self.assertIn("native_value_present=1\n", output)
        self.assertIn("rid_support=0\nrid_normal=0\neid_support=0\neid_normal=0\nfail_reason=7\n", output)

    def test_unpinned_probe_and_failed_baseline_never_create_or_dispatch(self):
        f = self.fixture()
        f.script.write_text(re.sub(r"^L2_SHA=.*$", "L2_SHA=UNSET", f.script.read_text(), flags=re.M))
        self.assertEqual(f.run("RID_READ")[0], 69)
        self.assertFalse(f.target.exists()); self.assertFalse(f.marker.exists())
        for mode in ("bad_caller", "network_active", "apk_changed", "pid_changed", "uid_changed"):
            with self.subTest(mode=mode):
                f = self.fixture(); f.configure(mode=mode)
                rc, output = f.run("RID_READ")
                self.assertEqual(rc, 10, output); self.assertEqual(f.count("attach"), 0)
                self.assertFalse(f.target.exists()); self.assertFalse(f.marker.exists())

    def test_no_native_result_preserves_file_then_late_cleanup(self):
        f = self.fixture(); f.configure(mode="no_result")
        self.assertEqual(f.run("RID_READ")[0], 75)
        self.assertTrue(f.target.exists()); self.assertEqual(f.count("attach"), 1)
        self.assertEqual(f.run("RID_CLEANUP")[0], 75)
        f.publish_native(mode="null")
        self.assertEqual(f.run("RID_CLEANUP")[0], 0)
        self.assertFalse(f.target.exists()); self.assertEqual(f.count("attach"), 1)

    def test_failed_native_stages_are_terminal_but_never_return_a_value(self):
        for mode in ("failure", "dispose_failure"):
            with self.subTest(mode=mode):
                f = self.fixture(); f.set_native(mode=mode)
                rc, output = f.run("RID_READ")
                self.assertNotEqual(rc, 0, output)
                self.assertIn("rid_cache_state=UNKNOWN\n", output)
                self.assertIn("native_value_present=0\n", output)
                self.assertFalse(f.target.exists()); self.assertEqual(f.count("attach"), 1)

    def test_wrong_identity_malformed_or_repeated_query_never_authorizes_cleanup(self):
        for values in ({"uid":10124}, {"sid":common.OTHER_SID}, {"mode":"bad_count"},
                       {"mode":"bad_null"}, {"mode":"bad_ready"}, {"mode":"malformed"},
                       {"mode":"no_enter"}, {"mode":"duplicate"}):
            with self.subTest(values=values):
                f = self.fixture(); f.set_native(**values)
                rc, output = f.run("RID_READ")
                self.assertEqual(rc, 75, output)
                self.assertTrue(f.target.exists()); self.assertEqual(f.count("remove"), 0)

    def test_changed_file_and_record_read_errors_preserve_owned_candidate(self):
        for mode in ("inode_changed", "hash_changed"):
            with self.subTest(mode=mode):
                f = self.fixture(); f.configure(mode=mode)
                self.assertEqual(f.run("RID_READ")[0], 74)
                self.assertEqual(f.run("RID_CLEANUP")[0], 73)
                self.assertTrue(f.target.exists()); self.assertEqual(f.count("remove"), 0)
        f = self.fixture(); f.configure(mode="no_result")
        self.assertEqual(f.run("RID_READ")[0], 75)
        f.publish_native(); f.configure(record_read_error=True)
        self.assertEqual(f.run("RID_CLEANUP")[0], 73)
        self.assertTrue(f.target.exists())

    def test_cross_session_new_boot_cleanup_does_not_reread_cache(self):
        f = self.fixture(); f.configure(mode="no_result")
        self.assertEqual(f.run("RID_READ")[0], 75)
        f.boot.write_text(common.OTHER_BOOT + "\n")
        self.assertEqual(f.run("RID_CLEANUP", common.OTHER_SID)[0], 0)
        self.assertFalse(f.target.exists()); self.assertTrue(f.marker.exists())
        self.assertEqual(f.count("attach"), 1)


if __name__ == "__main__":
    unittest.main()
