"""Run production L1 in real mksh against a synthetic Android filesystem.

Set MKSH to a host mksh executable. Only fixed paths, pinned hashes/sizes and
PATH are rewritten; native output and Android metadata come from command mocks.
Exclusive creation, descriptor identity, byte copy, receipts and unlink are real.
No libmtp, USB, Android process or vendor binary is used.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "experiments/jvmti/jvmti_flysafe_inprocess_query/scripts/rc2_canary_loader.sh"
REQUESTED_MKSH = os.environ.get("MKSH", "")
MKSH = shutil.which(REQUESTED_MKSH)
SID = "aaaaaaaaaaaaaaaa"
OTHER_SID = "bbbbbbbbbbbbbbbb"
BOOT = "11111111-2222-3333-4444-555555555555"
OTHER_BOOT = "66666666-7777-8888-9999-aaaaaaaaaaaa"
PAYLOAD = b"TEST-INDEPENDENT-CANARY\n" * 23
APK = b"TEST-INDEPENDENT-PACKAGE\n"


def native_text(sid=SID, pid=4242, uid=10123, mode="ready"):
    prefix = f"schema=finduas-artti-identity/v1 phase={{phase}} sid={sid} pid={pid} uid={uid} gid={uid} abi_bits=32"
    enter = prefix.format(phase="enter") + "\n"
    flags = "ready=1 identity_ok=1 artti_ok=1 dispose_ok=1 context_rc=0 context_errno=0 context=u:r:TEST_app:s0"
    if mode == "ready_zero":
        flags = "ready=0 identity_ok=0 artti_ok=1 dispose_ok=1 context_rc=1 context_errno=13 context=UNAVAILABLE"
    result = prefix.format(phase="result") + " " + flags + (
        " stat_rc=0 stat_errno=0 starttime=123456 env_rc=0 version_called=1 version_rc=0"
        " interface_version=0x30010200 dispose_attempted=1 dispose_rc=0\n")
    if mode == "malformed": result = result.replace(" dispose_rc=0", "")
    if mode == "bad_flags": result = result.replace("identity_ok=1", "identity_ok=0")
    if mode == "art_ti_version": result = result.replace("0x30010200", "0x70010200")
    if mode == "no_enter": return result
    if mode == "duplicate": return enter + result + result
    return enter + result


MOCK_SOURCE = r'''
import hashlib, json, os, stat, sys
from pathlib import Path
root=Path(os.environ["L1_TEST_ROOT"])
config=json.loads((root/"config.json").read_text())
mode=config.get("mode", "ready")
name=Path(sys.argv[0]).name
a=sys.argv[1:]
with (root/"calls.jsonl").open("a") as f: f.write(json.dumps([name]+a)+"\n")
target=root/"data/app/finduas_A048_identity.so"
source=root/"storage/ABCD-1234/Download/FindUAS_ARTTI_V2.so"
apk=root/"data/app/DJI_FLY/DJI_FLY.apk"
def count(label):
    path=root/(label+".count")
    value=int(path.read_text())+1 if path.exists() else 1
    path.write_text(str(value));return value
if name=="timeout":
    os.execvp(a[1],a[1:])
elif name=="sleep":
    pass
elif name=="id":
    if a==["-u"]: print("9999" if mode=="bad_caller" else "1000")
    elif a==["-Z"]: print("u:r:system_app:s0")
    else: raise AssertionError(a)
elif name=="getenforce": print("Permissive")
elif name=="getprop":
    assert len(a)==1
    if a[0]=="ro.debuggable": print("1")
    else:
        assert a[0] in ("sys.upgrade.app_self.path","persist.dji.upgrade.app_update","persist.upgrade.app_self","sys.upgrade.app_self")
        print("1" if mode=="update_active" else "0")
elif name=="settings":
    assert a==["get","global","wifi_on"];print("0")
elif name=="dumpsys":
    if a==["wifi"]:
        print("Wi-Fi is disabled")
        print("ignored historical detail\n"*2000)
        if mode=="wifi_error":sys.exit(5)
    elif a==["connectivity"]:
        print("Active default network: none")
        if mode!="missing_network_start":print("Current Networks:")
        if mode=="network_active":print("  TEST active network")
        if mode!="missing_network_end":print("Restrict background: false")
        print("ignored historical NetworkAgentInfo{old}\n"*2000)
        if mode=="connectivity_error":sys.exit(5)
    else:
        assert a==["activity","-p","dji.go.v5","lru"]
        call=count("ams")
        pid=4343 if mode=="pid_changed" and call>=3 else 4242
        uid="u0a124" if mode=="uid_changed" and call>=3 else config.get("ams_uid","u0a123")
        print("ACTIVITY MANAGER LRU PROCESSES (dumpsys activity lru)")
        print(f"  #10: home HOME --- {pid}:dji.go.v5/{uid} act:activities")
        if mode=="duplicate_ams":print(f"  #11: home HOME --- {pid}:dji.go.v5/{uid} act:activities")
elif name=="pm":
    assert a==["path","dji.go.v5"];print("package:"+str(apk))
elif name=="stat":
    if a[:2]==["-Lc","%d:%i"]:
        assert a[2]=="/proc/self/fd/3"
        info=os.fstat(3)
        assert stat.S_ISREG(info.st_mode)
        count("descriptor_stat")
        print(f"{info.st_dev}:{info.st_ino}")
    elif a[:2]==["-c","%a:%u:%g"]:
        assert Path(a[2])==root/"data/app";print("771:1000:1000")
    elif a[:2]==["-c","%d:%i:%a:%u:%g:%s"]:
        info=os.stat(a[2]);print(f"{info.st_dev}:{info.st_ino}:{stat.S_IMODE(info.st_mode):o}:1000:1000:{info.st_size}")
    elif a[:2]==["-c","%s"]: print(os.stat(a[2]).st_size)
    else:raise AssertionError(a)
elif name=="ls":
    assert a[0]=="-ldZ"
    print("-rw-r--r-- system system u:object_r:apk_data_file:s0 "+a[1])
elif name=="sha256sum":
    path=Path(a[0])
    if path==apk and count("apk_hash")==2 and mode=="apk_changed":apk.write_bytes(b"TEST-CHANGED-PACKAGE")
    print(hashlib.sha256(path.read_bytes()).hexdigest()+"  "+str(path))
elif name=="log":
    assert a[:4]==["-p","i","-t","FindUAS-Loader"]
    with (root/"control.log").open("a") as f:f.write(a[4]+"\n")
elif name=="logcat":
    if "FindUAS-Loader:I" in a: print((root/"control.log").read_text(),end="")
    elif "FindUAS-ARTTI-Identity:I" in a:
        assert "--pid=4242" in a
        path=root/"native.log"
        if path.exists():print(path.read_text(),end="")
    else:
        assert "--pid=4242" in a and "-t" in a
        amount=a[a.index("-t")+1]
        if amount=="16":print("I/TEST(4242): synthetic target log control")
        else:
            assert amount=="64" and "ActivityThread:W" in a and "linker:W" in a
            print("W/TEST(4242): synthetic loader diagnostic, not native completion")
elif name=="cmd":
    count("attach")
    assert a[:3]==["activity","attach-agent","dji.go.v5"] and len(a)==4
    path,sid=a[3].split("=")
    assert Path(path)==target and len(sid)==16
    assert target.read_bytes()==source.read_bytes()
    assert (root/"storage/ABCD-1234/Download/FindUAS/Probe/A048_attach.attempted").is_file()
    if mode not in ("no_result","attach_timeout"):
        (root/"native.log").write_text((root/"result.fixture").read_text())
    if mode=="inode_changed":
        replacement=target.with_name("TEST-replacement")
        replacement.write_bytes(target.read_bytes());replacement.chmod(0o644);replacement.replace(target)
    if mode=="hash_changed":
        value=bytearray(target.read_bytes());value[-1]^=1;target.write_bytes(value)
    if mode=="attach_timeout":sys.exit(124)
elif name=="head":
    if Path(a[-1])==source and mode=="source_grows":
        with source.open("ab") as f:f.write(b"X"*100000)
    if Path(a[-1])==source and mode=="copy_error":
        sys.stdout.buffer.write(source.read_bytes()[:7]);sys.exit(5)
    if a[-1].endswith("A048_copy.receipt") and config.get("record_read_error"):
        sys.stdout.buffer.write(Path(a[-1]).read_bytes());sys.exit(5)
    os.execv("/usr/bin/head",["head"]+a)
elif name=="cat":
    os.execv("/bin/cat",["cat"]+a)
elif name=="rm":
    assert a==["--",str(target)]
    count("remove");os.unlink(target)
else:raise AssertionError(name)
'''


class Fixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix="finduas-l1-test-")
        self.root = Path(self.temp.name).resolve()
        self.base = self.root / "storage/ABCD-1234/Download"
        self.probe = self.base / "FindUAS/Probe"
        self.probe.mkdir(parents=True)
        self.target = self.root / "data/app/finduas_A048_identity.so"
        self.apk = self.root / "data/app/DJI_FLY/DJI_FLY.apk"
        self.apk.parent.mkdir(parents=True)
        self.apk.write_bytes(APK)
        self.payload = self.base / "FindUAS_ARTTI_V2.so"
        self.payload.write_bytes(PAYLOAD)
        self.boot = self.root / "boot_id"
        self.boot.write_text(BOOT + "\n")
        self.receipt = self.probe / "A048_copy.receipt"
        self.marker = self.probe / "A048_attach.attempted"
        self.bin = self.root / "bin"; self.bin.mkdir()
        mock = self.bin / "mock.py"
        mock.write_text("#!" + sys.executable + "\n" + MOCK_SOURCE); mock.chmod(0o700)
        for name in ("timeout", "sleep", "id", "getenforce", "getprop", "settings", "dumpsys", "pm", "stat", "ls", "sha256sum", "log", "logcat", "cmd", "head", "cat", "rm"):
            (self.bin / name).symlink_to(mock)
        (self.bin / "sh").symlink_to(str(Path(MKSH).resolve()))
        self.config = {}; self.configure()
        self.set_native()
        text = SOURCE.read_text()
        text = re.sub(r"^L1_SHA=.*$", "L1_SHA=" + hashlib.sha256(PAYLOAD).hexdigest(), text, flags=re.M)
        text = re.sub(r"^L1_SIZE=.*$", "L1_SIZE=" + str(len(PAYLOAD)), text, flags=re.M)
        text = re.sub(r"^L1_APK_SHA=.*$", "L1_APK_SHA=" + hashlib.sha256(APK).hexdigest(), text, flags=re.M)
        text = text.replace("/storage/", str(self.root / "storage") + "/")
        text = text.replace("/data/app", str(self.root / "data/app"))
        text = text.replace("/proc/sys/kernel/random/boot_id", str(self.boot))
        path = str(self.bin) + os.pathsep + "/usr/bin:/bin"
        # Darwin builds expose builtin cat; Android's build excludes that builtin.
        text = text.replace("PATH=/system/bin", "PATH=" + shlex.quote(path) +
                            "\ncat() { " + shlex.quote(str(self.bin / "cat")) + ' "$@"; }')
        self.script = self.base / "L1.sh"; self.script.write_text(text)
        self.env = dict(os.environ, PATH=path, L1_TEST_ROOT=str(self.root), TMPDIR=str(self.root / "missing-tmp"))

    def configure(self, **changes):
        self.config.update(changes)
        (self.root / "config.json").write_text(json.dumps(self.config))

    def set_native(self, **kwargs):
        (self.root / "result.fixture").write_text(native_text(**kwargs))

    def publish_native(self, **kwargs):
        (self.root / "native.log").write_text(native_text(**kwargs))

    def run(self, operation, sid=SID):
        result = subprocess.run([MKSH, str(self.script), operation, sid], env=self.env,
                                text=True, capture_output=True, timeout=30)
        if result.stderr:
            raise AssertionError(result.stderr)
        if not result.stdout.startswith("schema=finduas-rc2-canary-loader/v1\nsid=" + sid + "\noperation=" + operation + "\n") or not result.stdout.endswith("report_end=true\n"):
            raise AssertionError(result.stdout)
        return result.returncode, result.stdout

    def count(self, label):
        path = self.root / (label + ".count")
        return int(path.read_text()) if path.exists() else 0


@unittest.skipUnless(REQUESTED_MKSH, "Set MKSH to run L1 host integration")
class CanaryLoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not MKSH: raise RuntimeError("MKSH must be executable")

    def fixture(self):
        fixture = Fixture(); self.addCleanup(fixture.temp.cleanup)
        return fixture

    def test_baseline_load_cleanup_and_permanent_dispatch_marker(self):
        f = self.fixture()
        self.assertEqual(f.run("CANARY_BASELINE")[0], 0)
        self.assertFalse(f.target.exists()); self.assertEqual(f.count("attach"), 0)
        rc, output = f.run("CANARY_LOAD")
        self.assertEqual(rc, 0, output)
        self.assertEqual(f.count("descriptor_stat"), 1)
        self.assertEqual(f.count("attach"), 1); self.assertEqual(f.count("remove"), 1)
        self.assertIn("BEGIN framework_loader_log\n", output)
        self.assertFalse(f.target.exists()); self.assertTrue(f.marker.is_file()); self.assertTrue(f.receipt.is_file())
        self.assertNotEqual(f.run("CANARY_LOAD")[0], 0)
        self.assertEqual(f.count("attach"), 1)

    def test_failed_preflight_never_copies_or_attaches(self):
        for mode in ("bad_caller", "update_active", "network_active", "missing_network_start", "missing_network_end", "wifi_error", "connectivity_error", "duplicate_ams"):
            with self.subTest(mode=mode):
                f = self.fixture(); f.configure(mode=mode)
                rc, output = f.run("CANARY_LOAD")
                self.assertEqual(rc, 10, output)
                self.assertEqual(f.count("descriptor_stat"), 0); self.assertEqual(f.count("attach"), 0)
                self.assertFalse(f.target.exists()); self.assertFalse(f.receipt.exists()); self.assertFalse(f.marker.exists())

    def test_source_and_path_collisions_fail_before_copy(self):
        for collision in ("target", "receipt", "marker", "source_hash"):
            with self.subTest(collision=collision):
                f = self.fixture()
                path = f.payload if collision=="source_hash" else getattr(f,collision)
                path.write_bytes(b"TEST-DO-NOT-OVERWRITE")
                self.assertEqual(f.run("CANARY_LOAD")[0], 10)
                self.assertEqual(path.read_bytes(), b"TEST-DO-NOT-OVERWRITE")
                self.assertEqual(f.count("attach"), 0)

    def test_ams_uid_zero_is_valid_and_malformed_uids_are_rejected(self):
        f = self.fixture(); f.configure(ams_uid="u0a0")
        rc, output = f.run("CANARY_BASELINE")
        self.assertEqual(rc, 0, output); self.assertIn("target_uid=10000\n", output)
        for uid in ("u0a", "u0a01", "u0a999999999999", "u1a123", "u0a123/extra"):
            with self.subTest(uid=uid):
                f = self.fixture(); f.configure(ams_uid=uid)
                self.assertEqual(f.run("CANARY_LOAD")[0], 10)
                self.assertEqual(f.count("attach"), 0)

    def test_apk_pid_or_uid_change_between_copy_and_dispatch_stops(self):
        for mode in ("apk_changed", "pid_changed", "uid_changed"):
            with self.subTest(mode=mode):
                f = self.fixture(); f.configure(mode=mode)
                rc, output = f.run("CANARY_LOAD")
                self.assertEqual(rc, 10, output); self.assertEqual(f.count("attach"), 0)
                self.assertEqual(f.count("descriptor_stat"), 1)
                self.assertFalse(f.marker.exists()); self.assertFalse(f.target.exists())

    def test_missing_result_or_dispatch_timeout_keeps_file_then_cleanup(self):
        for mode in ("no_result", "attach_timeout"):
            with self.subTest(mode=mode):
                f = self.fixture(); f.configure(mode=mode)
                rc, output = f.run("CANARY_LOAD")
                self.assertEqual(rc, 75, output); self.assertTrue(f.target.exists())
                self.assertIn("BEGIN framework_loader_log\n", output)
                self.assertEqual(f.count("attach"), 1); self.assertEqual(f.count("remove"), 0)
                self.assertEqual(f.run("CANARY_CLEANUP")[0], 75)
                f.publish_native()
                self.assertEqual(f.run("CANARY_CLEANUP")[0], 0)
                self.assertFalse(f.target.exists()); self.assertTrue(f.marker.exists())
                self.assertEqual(f.count("attach"), 1)

    def test_changed_inode_or_hash_is_never_deleted(self):
        for mode in ("inode_changed", "hash_changed"):
            with self.subTest(mode=mode):
                f = self.fixture(); f.configure(mode=mode)
                self.assertEqual(f.run("CANARY_LOAD")[0], 74)
                self.assertTrue(f.target.exists()); self.assertEqual(f.count("remove"), 0)
                self.assertEqual(f.run("CANARY_CLEANUP")[0], 73)
                self.assertTrue(f.target.exists()); self.assertEqual(f.count("attach"), 1)

    def test_record_read_error_cannot_become_successful_cleanup(self):
        f = self.fixture(); f.configure(mode="no_result")
        self.assertEqual(f.run("CANARY_LOAD")[0], 75)
        f.publish_native(); f.configure(record_read_error=True)
        self.assertEqual(f.run("CANARY_CLEANUP")[0], 73)
        self.assertTrue(f.target.exists()); self.assertEqual(f.count("remove"), 0)
        f.configure(record_read_error=False)
        self.assertEqual(f.run("CANARY_CLEANUP")[0], 0)

    def test_cross_sid_and_new_boot_cleanup_never_dispatch(self):
        f = self.fixture(); f.configure(mode="no_result")
        self.assertEqual(f.run("CANARY_LOAD")[0], 75)
        f.boot.write_text(OTHER_BOOT+"\n")
        self.assertEqual(f.run("CANARY_CLEANUP", OTHER_SID)[0], 0)
        self.assertFalse(f.target.exists()); self.assertTrue(f.marker.exists())
        self.assertEqual(f.count("attach"), 1)

    def test_partial_or_growing_source_is_bounded_and_not_dispatched(self):
        for mode in ("copy_error", "source_grows"):
            with self.subTest(mode=mode):
                f = self.fixture(); f.configure(mode=mode)
                rc, output = f.run("CANARY_LOAD")
                self.assertEqual(rc, 74, output); self.assertEqual(f.count("attach"), 0)
                self.assertLessEqual(f.target.stat().st_size, len(PAYLOAD)+1)
                self.assertTrue(f.receipt.exists()); self.assertFalse(f.marker.exists())
                self.assertNotEqual(f.run("CANARY_CLEANUP")[0], 0)
                self.assertTrue(f.target.exists())

    def test_malformed_duplicate_or_wrong_identity_log_never_cleans(self):
        cases = ({"mode":"malformed"}, {"mode":"bad_flags"}, {"mode":"no_enter"},
                 {"mode":"duplicate"}, {"uid":10124}, {"pid":4343}, {"sid":OTHER_SID})
        for values in cases:
            with self.subTest(values=values):
                f = self.fixture(); f.set_native(**values)
                rc, output = f.run("CANARY_LOAD")
                self.assertEqual(rc, 75, output); self.assertTrue(f.target.exists())
                self.assertEqual(f.count("remove"), 0); self.assertEqual(f.count("attach"), 1)

    def test_valid_failed_native_result_closes_file_without_claiming_success(self):
        for mode in ("ready_zero",):
            with self.subTest(mode=mode):
                f = self.fixture(); f.set_native(mode=mode)
                rc, output = f.run("CANARY_LOAD")
                self.assertNotEqual(rc, 0, output); self.assertFalse(f.target.exists())
                self.assertEqual(f.count("remove"), 1); self.assertTrue(f.marker.exists())

    def test_reported_version_is_not_confused_with_getenv_selector(self):
        f = self.fixture(); f.set_native(mode="art_ti_version")
        rc, output = f.run("CANARY_LOAD")
        self.assertEqual(rc, 0, output)
        self.assertIn("interface_version=0x70010200", output)
        self.assertFalse(f.target.exists())


if __name__ == "__main__":
    unittest.main()
