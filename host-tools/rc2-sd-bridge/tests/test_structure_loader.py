"""Real mksh L4 lifecycle tests using synthetic payloads and command responses.

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


SOURCE = common.SOURCE.with_name("rc2_policy_structure_loader.sh")
SID = common.SID


def native_text(sid=SID, pid=4242, uid=10123, mode="value", **changes):
    base = f"schema=finduas-policy-structure/v1 phase={{phase}} sid={sid} pid={pid} uid={uid} gid={uid} abi_bits=32"
    values = dict(ready=1, stage=0, exception=0, cloud_query_count=1, product_query_count=1,
                  mmkv_decode_count=1, namespace_present=1, mmkv_present=1, cloud_present=1,
                  product_present=1, product_type=139, receiver_type=18, receiver_index=4,
                  json_rc=0, entry_count=3, duplicate_count=0, candidate_count=1, match_count=1,
                  default_match=0, product_blocked_count=0, jni_rc=0, env_rc=0, guard_rc=0,
                  dispose_attempted=1, dispose_rc=0)
    if mode == "namespace_absent":
        values.update(ready=0, stage=6, namespace_present=0, mmkv_present=-1, mmkv_decode_count=0,
                      cloud_query_count=0, product_query_count=0, cloud_present=-1, product_present=-1,
                      product_type=-1, receiver_type=-1, receiver_index=-1, json_rc=-1, guard_rc=11)
    if mode == "mmkv_absent": values.update(mmkv_present=0, json_rc=1)
    if mode in ("namespace_absent", "mmkv_absent", "product_absent", "failure", "json_failure"):
        values.update(entry_count=-1, duplicate_count=-1, candidate_count=-1, match_count=-1,
                      default_match=-1, product_blocked_count=-1)
    if mode == "cloud_absent": values.update(cloud_present=0, receiver_type=-1, receiver_index=-1, match_count=-1, default_match=-1)
    if mode == "product_absent": values.update(product_present=0, product_type=-1, json_rc=9)
    if mode == "no_match": values.update(candidate_count=0, match_count=0)
    if mode == "failure": values.update(ready=0, stage=7, mmkv_decode_count=0, mmkv_present=-1,
                                       json_rc=-1, guard_rc=3)
    if mode == "json_failure": values.update(ready=0, stage=9, json_rc=6)
    if mode == "dispose_failure": values.update(ready=0, stage=13, dispose_rc=113)
    values.update(changes)
    enter = base.format(phase="enter") + "\n"
    export = f"schema=finduas-policy-structure/v1 phase=export sid={sid} pid={pid} export_rc=0 export_bytes=200 matched_rows=1 default_present=1 default_nonempty=1 matched_hex_length=2 default_hex_length=2\n"
    result = base.format(phase="result") + " " + " ".join(f"{key}={value}" for key, value in values.items()) + "\n"
    if mode == "malformed": result = result.replace(" dispose_rc=0", "")
    if mode == "no_enter": return result
    if mode == "duplicate": return enter + export + result + result
    return enter + export + result


class Fixture(common.Fixture):
    def __init__(self):
        super().__init__()
        self.target = self.root / "data/app/finduas_A057_policy_structure.so"
        source = self.base / "FindUAS_POLICY_STRUCTURE.so"
        self.payload.rename(source); self.payload = source
        self.receipt = self.probe / "A057_copy.receipt"
        self.marker = self.probe / "A057_attach.attempted"
        mock_source = common.MOCK_SOURCE
        for old, new in (("L1_TEST_ROOT", "L4_TEST_ROOT"),
                         ("finduas_A048_identity.so", "finduas_A057_policy_structure.so"),
                         ("FindUAS_ARTTI_V2.so", "FindUAS_POLICY_STRUCTURE.so"),
                         ("A048_copy.receipt", "A057_copy.receipt"),
                         ("A048_attach.attempted", "A057_attach.attempted"),
                         ("FindUAS-ARTTI-Identity:I", "FindUAS-Policy-Structure:I"),
                         ("FindUAS-Loader", "FindUAS-Structure-Loader")):
            mock_source = mock_source.replace(old, new)
        (self.bin / "mock.py").write_text("#!" + sys.executable + "\n" + mock_source)
        text = SOURCE.read_text()
        text = re.sub(r"^L4_SHA=.*$", "L4_SHA=" + hashlib.sha256(common.PAYLOAD).hexdigest(), text, flags=re.M)
        text = re.sub(r"^L4_SIZE=.*$", "L4_SIZE=" + str(len(common.PAYLOAD)), text, flags=re.M)
        text = re.sub(r"^L4_APK_SHA=.*$", "L4_APK_SHA=" + hashlib.sha256(common.APK).hexdigest(), text, flags=re.M)
        text = text.replace("/storage/", str(self.root / "storage") + "/")
        text = text.replace("/data/app", str(self.root / "data/app"))
        text = text.replace("/proc/sys/kernel/random/boot_id", str(self.boot))
        path = str(self.bin) + os.pathsep + "/usr/bin:/bin"
        text = text.replace("PATH=/system/bin", "PATH=" + shlex.quote(path) +
                            "\ncat() { " + shlex.quote(str(self.bin / "cat")) + ' "$@"; }')
        self.script = self.base / "L4.sh"; self.script.write_text(text)
        self.env["L4_TEST_ROOT"] = str(self.root)

    def set_native(self, **kwargs):
        (self.root / "result.fixture").write_text(native_text(**kwargs))

    def publish_native(self, **kwargs):
        (self.root / "native.log").write_text(native_text(**kwargs))

    def run(self, operation, sid=SID):
        result = subprocess.run([common.MKSH, str(self.script), operation, sid], env=self.env,
                                text=True, capture_output=True, timeout=30)
        if result.stderr: raise AssertionError(result.stderr)
        expected = f"schema=finduas-rc2-policy-structure-loader/v1\nsid={sid}\noperation={operation}\n"
        if not result.stdout.startswith(expected) or not result.stdout.endswith("report_end=true\n"):
            raise AssertionError(result.stdout)
        return result.returncode, result.stdout


@unittest.skipUnless(common.REQUESTED_MKSH, "Set MKSH to run L4 host integration")
class StructureLoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not common.MKSH: raise RuntimeError("MKSH must be executable")

    def fixture(self):
        fixture = Fixture(); self.addCleanup(fixture.temp.cleanup)
        return fixture

    def test_observed_relation_read_once_and_cleanup(self):
        f = self.fixture()
        self.assertEqual(f.run("STRUCTURE_BASELINE")[0], 0)
        self.assertFalse(f.target.exists()); self.assertEqual(f.count("attach"), 0)
        rc, output = f.run("STRUCTURE_READ")
        self.assertEqual(rc, 0, output)
        self.assertIn("policy_structure_state=OBSERVED\n", output)
        self.assertIn("native_match_count=1\n", output)
        for name in ("cloud_query_count", "product_query_count", "mmkv_decode_count"):
            self.assertIn(f"native_{name}=1\n", output)
        self.assertEqual(f.count("descriptor_stat"), 1)
        self.assertEqual(f.count("attach"), 1); self.assertEqual(f.count("remove"), 1)
        self.assertFalse(f.target.exists()); self.assertTrue(f.marker.exists()); self.assertTrue(f.receipt.exists())
        self.assertNotEqual(f.run("STRUCTURE_READ")[0], 0)
        self.assertEqual(f.count("attach"), 1)

    def test_absent_inputs_are_terminal_unknown_with_owned_file_cleanup(self):
        for mode in ("namespace_absent", "mmkv_absent", "cloud_absent", "product_absent"):
            with self.subTest(mode=mode):
                f = self.fixture(); f.set_native(mode=mode)
                rc, output = f.run("STRUCTURE_READ")
                self.assertEqual(rc, 1 if mode == "namespace_absent" else 10, output)
                self.assertIn("policy_structure_state=UNKNOWN\n", output)
                self.assertIn("native_result_observed=true\n", output)
                self.assertFalse(f.target.exists()); self.assertTrue(f.marker.exists())
                self.assertEqual(f.count("attach"), 1); self.assertEqual(f.count("remove"), 1)

    def test_zero_match_is_observed_but_not_claimed_as_applied_policy(self):
        f = self.fixture(); f.set_native(mode="no_match")
        rc, output = f.run("STRUCTURE_READ")
        self.assertEqual(rc, 0, output)
        self.assertIn("policy_structure_state=OBSERVED\n", output)
        self.assertIn("native_match_count=0\n", output)

    def test_unpinned_and_preflight_identity_changes_never_dispatch(self):
        f = self.fixture()
        f.script.write_text(re.sub(r"^L4_SHA=.*$", "L4_SHA=UNSET", f.script.read_text(), flags=re.M))
        self.assertEqual(f.run("STRUCTURE_READ")[0], 69)
        self.assertFalse(f.target.exists()); self.assertFalse(f.marker.exists())
        for mode in ("bad_caller", "network_active", "apk_changed", "uid_changed"):
            with self.subTest(mode=mode):
                f = self.fixture(); f.configure(mode=mode)
                rc, output = f.run("STRUCTURE_READ")
                self.assertEqual(rc, 10, output); self.assertEqual(f.count("attach"), 0)
                self.assertFalse(f.target.exists()); self.assertFalse(f.marker.exists())

    def test_no_native_result_preserves_file_then_late_unknown_cleanup(self):
        f = self.fixture(); f.configure(mode="no_result")
        self.assertEqual(f.run("STRUCTURE_READ")[0], 75)
        self.assertTrue(f.target.exists()); self.assertEqual(f.count("attach"), 1)
        self.assertEqual(f.run("STRUCTURE_CLEANUP")[0], 75)
        f.publish_native(mode="mmkv_absent")
        self.assertEqual(f.run("STRUCTURE_CLEANUP")[0], 0)
        self.assertFalse(f.target.exists()); self.assertEqual(f.count("attach"), 1)

    def test_failed_native_stages_are_terminal_unknown(self):
        for mode in ("failure", "dispose_failure", "json_failure"):
            with self.subTest(mode=mode):
                f = self.fixture(); f.set_native(mode=mode)
                rc, output = f.run("STRUCTURE_READ")
                self.assertEqual(rc, 1, output)
                self.assertIn("policy_structure_state=UNKNOWN\n", output)
                self.assertFalse(f.target.exists()); self.assertEqual(f.count("attach"), 1)

    def test_wrong_identity_never_authorizes_cleanup(self):
        f = self.fixture(); f.set_native(uid=10124)
        rc, output = f.run("STRUCTURE_READ")
        self.assertEqual(rc, 75, output)
        self.assertTrue(f.target.exists()); self.assertEqual(f.count("remove"), 0)

    def test_changed_file_and_record_read_errors_preserve_candidate(self):
        for mode in ("inode_changed", "hash_changed", "copy_error"):
            with self.subTest(mode=mode):
                f = self.fixture(); f.configure(mode=mode)
                self.assertEqual(f.run("STRUCTURE_READ")[0], 74)
                self.assertEqual(f.run("STRUCTURE_CLEANUP")[0], 73)
                self.assertTrue(f.target.exists()); self.assertEqual(f.count("remove"), 0)
        f = self.fixture(); f.configure(mode="no_result")
        self.assertEqual(f.run("STRUCTURE_READ")[0], 75)
        f.publish_native(); f.configure(record_read_error=True)
        self.assertEqual(f.run("STRUCTURE_CLEANUP")[0], 73)
        self.assertTrue(f.target.exists())

    def test_cross_session_new_boot_cleanup_does_not_read_again(self):
        f = self.fixture(); f.configure(mode="no_result")
        self.assertEqual(f.run("STRUCTURE_READ")[0], 75)
        f.boot.write_text(common.OTHER_BOOT + "\n")
        self.assertEqual(f.run("STRUCTURE_CLEANUP", common.OTHER_SID)[0], 0)
        self.assertFalse(f.target.exists()); self.assertTrue(f.marker.exists())
        self.assertEqual(f.count("attach"), 1)

    def test_parser_rejects_bad_contract_without_synthetic_loader_handler(self):
        text = SOURCE.read_text()
        functions = text[text.index("bounded_native_number() {"):text.index("\nnetwork_stream() {")]
        command = "set -f\nL4_SID=" + SID + "\nL4_PID=4242\nL4_TARGET_UID=10123\n" + functions + "\nnative_stream\n"
        vectors = [dict(mode="malformed"), dict(mode="no_enter"), dict(mode="duplicate"),
                   dict(sid=common.OTHER_SID), dict(pid=4243), dict(cloud_query_count=2),
                   dict(product_query_count=2), dict(mmkv_decode_count=2), dict(stage=11),
                   dict(ready=0), dict(exception=1), dict(dispose_attempted=0),
                   dict(entry_count=257), dict(receiver_index=256), dict(product_type=65536),
                   dict(match_count=2), dict(default_match=2), dict(guard_rc=16), dict(json_rc=12),
                   dict(json_rc=6)]
        for values in vectors:
            with self.subTest(values=values):
                result = subprocess.run([common.MKSH, "-c", command], input=native_text(**values),
                                        text=True, capture_output=True, timeout=5)
                self.assertNotEqual(result.returncode, 0)
        for values in (dict(mode="no_match"), dict(mode="mmkv_absent"), dict(mode="failure"),
                       dict(mode="product_absent"), dict(mode="json_failure")):
            result = subprocess.run([common.MKSH, "-c", command], input=native_text(**values),
                                    text=True, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
