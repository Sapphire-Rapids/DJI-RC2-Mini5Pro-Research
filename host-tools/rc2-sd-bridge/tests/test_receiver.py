"""Real mksh/Java receiver integration with synthetic SD paths; no device access.

Set MKSH to a host mksh binary; java and javac are resolved through PATH.
Only the receiver's fixed filesystem paths, PATH and TTL are adapted in fixtures.
"""

import base64
import hashlib
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "experiments/jvmti/jvmti_flysafe_inprocess_query/scripts/rc2_sd_bridge.sh"
F4_SOURCE = SOURCE.with_name("rc2_fuli_baseline.sh")
SID = "aaaaaaaaaaaaaaaa"
REQUESTED_MKSH = os.environ.get("MKSH", "")
MKSH = shutil.which(REQUESTED_MKSH)
JAVA = shutil.which("java")
JAVAC = shutil.which("javac")
JAVA_SOURCE = r"""
import java.io.ByteArrayOutputStream;
import java.util.Base64;
public final class Launch {
  public static void main(String[] args) throws Exception {
    long start = System.nanoTime();
    Process child = Runtime.getRuntime().exec(args[0]);
    ByteArrayOutputStream output = new ByteArrayOutputStream();
    child.getInputStream().transferTo(output);
    int result = child.waitFor();
    System.out.println("rc=" + result);
    System.out.println("eof_ms=" + ((System.nanoTime() - start) / 1000000));
    System.out.println("output=" + Base64.getEncoder().encodeToString(output.toByteArray()));
  }
}
"""


class Session:
    def __init__(self, java_classes, ttl=90):
        self.temp = tempfile.TemporaryDirectory(prefix="finduas-b1-test-")
        self.root = Path(self.temp.name).resolve()
        self.base = self.root / "storage/ABCD-1234/Download"
        self.bridge = self.base / "FindUAS/Bridge"
        self.session = self.bridge / SID
        self.inbox = self.session / "inbox"
        self.outbox = self.session / "outbox"
        self.inbox.mkdir(parents=True)
        self.outbox.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        (self.bin / "sh").symlink_to(str(Path(MKSH).resolve()))
        self.env = dict(os.environ)
        self.env["PATH"] = str(self.bin) + os.pathsep + os.environ.get("PATH", "")
        self.env["B1_TEST_ID_COUNT"] = str(self.root / "identity.calls")
        self.env["B1_TEST_TIMEOUT_COUNT"] = str(self.root / "timeout.calls")
        self._tool("id", """from pathlib import Path
import os
p=Path(os.environ['B1_TEST_ID_COUNT'])
with p.open('a') as f: f.write('id\\n')
print('uid=1000(system) gid=1000(system)')
""")
        self._tool("sha256sum", """import hashlib, sys
from pathlib import Path
data=Path(sys.argv[1]).read_bytes() if len(sys.argv)>1 else sys.stdin.buffer.read()
print(hashlib.sha256(data).hexdigest()+'  '+(sys.argv[1] if len(sys.argv)>1 else '-'))
""")
        self._tool("stat", """import os, sys
assert sys.argv[1:3]==['-c','%s']
print(os.stat(sys.argv[3]).st_size)
""")
        self._tool("timeout", """import os, subprocess, sys
from pathlib import Path
with Path(os.environ['B1_TEST_TIMEOUT_COUNT']).open('a') as f: f.write('timeout\\n')
if os.environ.get('B1_TEST_REPLACE_F4'):
    Path(os.environ['B1_TEST_REPLACE_F4']).write_text('printf UNVERIFIED_FILE_EXECUTED\\n')
try:
    rc=subprocess.run(sys.argv[2:], timeout=float(sys.argv[1])).returncode
except subprocess.TimeoutExpired:
    rc=124
sys.exit(rc if rc>=0 else 128-rc)
""")
        self.script = self.base / "B1.sh"
        text = SOURCE.read_text()
        text = text.replace("/storage/", str(self.root / "storage") + "/")
        text = text.replace("/proc/uptime", str(self.root / "uptime"))
        text = text.replace("PATH=/system/bin", "PATH=" + shlex.quote(self.env["PATH"]))
        text = text.replace("-ge 3600", "-ge " + str(ttl))
        text = text.replace("-lt 3555", "-lt " + str(max(ttl - 45, 0)))
        self.script.write_text(text)
        (self.bridge / "active.session").write_text("B1 SESSION " + SID + " END\n")
        self.java_classes = java_classes
        self.started = time.monotonic()
        self.clock_stop = threading.Event()
        self._clock_write()
        self.clock_thread = threading.Thread(target=self._clock, daemon=True)
        self.clock_thread.start()

    def _tool(self, name, body):
        path = self.bin / name
        path.write_text("#!" + sys.executable + "\n" + body)
        path.chmod(0o700)

    def _clock_write(self):
        value = "%.2f 0.00\n" % (time.monotonic() - self.started)
        temporary = self.root / "uptime.tmp"
        temporary.write_text(value)
        temporary.replace(self.root / "uptime")

    def _clock(self):
        while not self.clock_stop.wait(0.025):
            self._clock_write()

    def wait_file(self, path, timeout=6):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if path.is_file():
                content = path.read_bytes()
                if content.endswith(b"\n"):
                    return content
            time.sleep(0.025)
        log = self.session / "worker.log"
        raise AssertionError("Timed out: " + path.name + "; log=" +
                             (log.read_text() if log.exists() else "<none>"))

    def launch(self, fd3=False):
        if fd3:
            wrapper = self.root / "fd3-launch.sh"
            wrapper.write_text("exec 3>&1\nexec sh " + shlex.quote(str(self.script)) + "\n")
            command = "sh " + str(wrapper)
        else:
            command = "sh -c (sh${IFS}" + str(self.script) + ")2>&1"
        result = subprocess.run([JAVA, "-cp", self.java_classes, "Launch", command],
                                env=self.env, capture_output=True, text=True, timeout=4)
        if result.returncode:
            raise AssertionError(result.stderr)
        fields = dict(line.split("=", 1) for line in result.stdout.splitlines())
        assert fields["rc"] == "0", fields
        assert int(fields["eof_ms"]) < 2500, fields
        output = base64.b64decode(fields["output"]).decode()
        assert output == "B1_START_REQUESTED sid=" + SID + "\n", output
        ready = self.wait_file(self.session / "session.ready").decode().split()
        assert ready[:3] == ["B1", "READY_SESSION", SID] and ready[-1] == "END", ready
        assert len(ready) == 6 and ready[3].isdigit() and ready[4].isdigit(), ready
        return ready

    def put(self, number, op, digest=None, partial=False):
        seq = "%04d" % number
        job = ("B1 JOB %s %s %s END\n" % (SID, seq, op)).encode()
        (self.inbox / (seq + ".job")).write_bytes(job)
        sha = digest or hashlib.sha256(job).hexdigest()
        ready = ("B1 READY %s %s %s %s END\n" % (SID, seq, len(job), sha)).encode()
        (self.inbox / (seq + ".ready")).write_bytes(ready[:-1] if partial else ready)

    def result(self, number, timeout=8):
        seq = "%04d" % number
        done = self.wait_file(self.outbox / (seq + ".done"), timeout).decode().split()
        assert len(done) == 8 and done[:4] == ["B1", "DONE", SID, seq] and done[-1] == "END", done
        report = (self.outbox / (seq + ".report")).read_bytes()
        assert len(report) == int(done[5]), done
        assert hashlib.sha256(report).hexdigest() == done[6], done
        assert report.endswith(b"report_end=true\n"), report
        assert ("handler_rc=" + done[4] + "\n").encode() in report, report
        return int(done[4]), report.decode()

    def closed(self, reason, timeout=6):
        expected = ("B1 CLOSED %s %s END\n" % (SID, reason)).encode()
        assert self.wait_file(self.session / "session.closed", timeout) == expected

    def identity_calls(self):
        p = self.root / "identity.calls"
        return len(p.read_text().splitlines()) if p.exists() else 0

    def cleanup(self):
        ready = self.session / "session.ready"
        if ready.exists():
            parts = ready.read_text().split()
            if len(parts) == 6 and parts[3].isdigit():
                pid = int(parts[3])
                command = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                                         capture_output=True, text=True).stdout
                # Terminate only this fixture's still-running host worker, never a device.
                if str(self.script) in command and "--worker" in command:
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
        self.clock_stop.set()
        self.clock_thread.join(timeout=1)
        self.temp.cleanup()


@unittest.skipUnless(REQUESTED_MKSH, "Set MKSH to run host receiver integration")
class ReceiverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not MKSH or not JAVA or not JAVAC:
            raise RuntimeError("MKSH must be executable, with java and javac available on PATH")
        cls.java_temp = tempfile.TemporaryDirectory(prefix="finduas-b1-java-")
        source = Path(cls.java_temp.name) / "Launch.java"
        source.write_text(JAVA_SOURCE)
        subprocess.run([JAVAC, str(source)], check=True, capture_output=True, timeout=30)

    @classmethod
    def tearDownClass(cls):
        cls.java_temp.cleanup()

    def session(self, **kwargs):
        session = Session(self.java_temp.name, **kwargs)
        self.addCleanup(session.cleanup)
        return session

    def test_java_eof_ready_ping_stop(self):
        s = self.session()
        s.launch()
        s.put(1, "PING")
        rc, report = s.result(1)
        self.assertEqual(rc, 0)
        self.assertIn("uptime_seconds=", report)
        self.assertEqual(s.identity_calls(), 1)
        s.put(2, "STOP")
        self.assertEqual(s.result(2)[0], 0)
        s.closed("STOP")

    def test_inherited_fd3_does_not_hold_java_stdout(self):
        s = self.session()
        s.launch(fd3=True)
        s.put(1, "STOP")
        self.assertEqual(s.result(1)[0], 0)
        s.closed("STOP")

    def test_partial_ready_does_not_execute(self):
        s = self.session()
        s.launch()
        s.put(1, "PING", partial=True)
        time.sleep(1.2)
        self.assertFalse((s.outbox / "0001.accepted").exists())
        self.assertEqual(s.identity_calls(), 0)
        s.put(1, "PING")
        self.assertEqual(s.result(1)[0], 0)
        s.put(2, "STOP")
        s.result(2)
        s.closed("STOP")

    def test_bad_digest_and_unknown_operation_report_then_continue(self):
        for op, digest in [("PING", "0" * 64), ("EXEC", None)]:
            with self.subTest(op=op):
                s = self.session()
                s.launch()
                s.put(1, op, digest=digest)
                rc, report = s.result(1)
                self.assertEqual(rc, 65)
                self.assertIn("op=REJECTED\n", report)
                self.assertEqual(s.identity_calls(), 0)
                s.put(2, "STOP")
                s.result(2)
                s.closed("STOP")

    def test_existing_accepted_or_report_never_executes_or_creates_done(self):
        for suffix in ["accepted", "report"]:
            with self.subTest(suffix=suffix):
                s = self.session()
                previous = b"old-data\nreport_end=true\n"
                output = s.outbox / ("0001." + suffix)
                output.write_bytes(previous)
                s.launch()
                s.put(1, "PING")
                s.closed("ERROR")
                self.assertFalse((s.outbox / "0001.done").exists())
                self.assertEqual(output.read_bytes(), previous)
                self.assertEqual(s.identity_calls(), 0)

    def test_failed_job_read_cannot_admit_even_complete_matching_bytes(self):
        s = self.session()
        real_head = shutil.which("head")
        s._tool("head", "import subprocess, sys\n"
                + "rc=subprocess.run([" + repr(real_head) + "]+sys.argv[1:]).returncode\n"
                + "sys.exit(5 if sys.argv[-1].endswith('/0001.job') else rc)\n")
        s.launch()
        s.put(1, "PING")
        self.assertEqual(s.result(1)[0], 65)
        self.assertEqual(s.identity_calls(), 0)
        s.put(2, "STOP")
        s.result(2)
        s.closed("STOP")

    def test_duplicate_launcher_does_not_replace_worker(self):
        s = self.session()
        first = s.launch()
        self.assertEqual(s.launch(), first)
        self.assertFalse((s.session / "session.closed").exists())
        s.put(1, "STOP")
        s.result(1)
        s.closed("STOP")

    def test_snapshot_hash_rejection_keeps_session_alive(self):
        s = self.session()
        (s.base / "F4.sh").write_text("printf UNVERIFIED_FILE_EXECUTED\n")
        s.launch()
        s.put(1, "SNAPSHOT")
        rc, report = s.result(1)
        self.assertEqual(rc, 65)
        self.assertIn("HELPER_HASH_MISMATCH", report)
        self.assertFalse((s.root / "timeout.calls").exists())
        s.put(2, "STOP")
        s.result(2)
        s.closed("STOP")

    def test_verified_snapshot_executes_ram_despite_file_change(self):
        s = self.session()
        helper = F4_SOURCE.read_bytes()
        expected = re.search(r"B1_F4_EXPECTED_SHA=([0-9a-f]{64})", SOURCE.read_text()).group(1)
        self.assertEqual(hashlib.sha256(helper).hexdigest(), expected)
        (s.base / "F4.sh").write_bytes(helper)
        s.env["B1_TEST_REPLACE_F4"] = str(s.base / "F4.sh")
        s.launch()
        s.put(1, "SNAPSHOT")
        rc, report = s.result(1)
        # Unmodified approved F4 refuses our synthetic non-/storage path. Its fixed
        # /system/bin PATH may also prevent printing that error on a host machine.
        self.assertEqual(rc, 64)
        self.assertNotIn("UNVERIFIED_FILE_EXECUTED", report)
        self.assertTrue((s.root / "timeout.calls").exists())
        s.put(2, "STOP")
        s.result(2)
        s.closed("STOP")

    def test_ttl_without_a_job(self):
        s = self.session(ttl=3)
        s.launch()
        s.closed("TTL", timeout=6)
        self.assertEqual(list(s.outbox.iterdir()), [])

    def test_limit_of_64_sequential_jobs(self):
        # Real mksh can implement sleep as a builtin, so retain the actual 1s pace.
        s = self.session(ttl=240)
        s.launch()
        for number in range(1, 66):
            s.put(number, "PING")
        self.assertEqual(s.result(64, timeout=180)[0], 0)
        s.closed("LIMIT")
        self.assertEqual(s.identity_calls(), 64)
        self.assertFalse((s.outbox / "0065.accepted").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
