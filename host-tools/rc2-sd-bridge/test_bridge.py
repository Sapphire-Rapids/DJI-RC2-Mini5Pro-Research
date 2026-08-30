import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import bridge


class FakeTransport:
    def __init__(self):
        self.files = {}
        self.calls = []
        self.fail_put = None

    def get(self, remote):
        self.calls.append(("get", remote))
        return self.files.get(remote)

    def put(self, remote, local):
        data = local.read_bytes()
        self.calls.append(("put", remote, data))
        if remote in self.files and self.files[remote] != data:
            raise bridge.BridgeError("REMOTE_CONTENT_CONFLICT")
        self.files[remote] = data
        if self.fail_put == remote:
            self.fail_put = None
            raise bridge.BridgeError("TRANSPORT_TIMEOUT_UNCERTAIN")

    def mkdir(self, remote):
        self.calls.append(("mkdir", remote))

    def archive(self, sid):
        self.calls.append(("archive", sid))
        active = bridge.BASE + "/active.session"
        destination = f"{bridge.BASE}/{sid}/active.session"
        if destination in self.files or self.files[active] != bridge.session_text(sid):
            raise bridge.BridgeError("ARCHIVE_CONFLICT")
        bridge.record(self.files[f"{bridge.BASE}/{sid}/session.closed"], "CLOSED", sid)
        self.files[destination] = self.files.pop(active)


class ClientTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = bridge.State(Path(self.temp.name))
        self.remote = FakeTransport()
        self.client = bridge.Client(self.state, self.remote)

    def ready(self):
        self.assertEqual("SESSION_PREPARED", self.client.prepare())
        sid = self.state.current()
        self.remote.files[f"{bridge.BASE}/{sid}/session.ready"] = f"B1 READY_SESSION {sid} 123 456 END\n".encode()
        return sid

    def canary_ready(self):
        sid = self.ready()
        self.remote.files[f"{bridge.BASE}/{sid}/session.receiver"] = f"B1 RECEIVER {sid} B2 END\n".encode()
        return sid

    def canary_body(self, sid, operation):
        return (f"schema=finduas-rc2-canary-loader/v1\nsid={sid}\noperation={operation}\n"
                "report_begin=true\npreflight_ready=true\nattach_dispatch_count=0\n"
                "test_file_created=false\ntest_file_removed=false\nnative_result_observed=false\n"
                "report_end=true\n").encode()

    def collected_baseline(self, sid, seq="0001", rc=0):
        self.assertEqual(f"TASK_SUBMITTED seq={seq}", self.client.submit("CANARY_BASELINE"))
        self.result(sid, seq, rc, self.canary_body(sid, "CANARY_BASELINE"))
        self.assertEqual(f"TASK_COLLECTED seq={seq} handler_rc={rc}", self.client.collect(seq))

    def result(self, sid, seq="0001", rc=0, body=b"TEST diagnostic\n", op=None):
        job = self.client.task_path(sid, seq, ".job").read_bytes()
        task = bridge.record(job, "JOB")
        op = op or task["op"]
        report = (f"schema=finduas-sd-bridge/v1\nsid={sid}\nseq={seq}\nop={op}\nhandler_begin=true\n".encode()
                  + body + f"handler_end=true\nhandler_rc={rc}\nreport_end=true\n".encode())
        prefix = f"{bridge.BASE}/{sid}/outbox/{seq}"
        self.remote.files[prefix + ".accepted"] = f"B1 ACCEPTED {sid} {seq} {len(job)} {bridge.digest(job)} END\n".encode()
        self.remote.files[prefix + ".done"] = f"B1 DONE {sid} {seq} {rc} {len(report)} {bridge.digest(report)} END\n".encode()
        self.remote.files[prefix + ".report"] = report
        return prefix

    def test_prepare_persists_sid_before_last_active_put(self):
        self.ready()
        puts = [call for call in self.remote.calls if call[0] == "put"]
        self.assertEqual(1, len(puts))
        self.assertEqual(bridge.BASE + "/active.session", puts[0][1])
        self.assertEqual(bridge.session_text(self.state.current()), puts[0][2])
        self.assertEqual("SESSION_REUSED", self.client.prepare())
        self.assertEqual(1, len([call for call in self.remote.calls if call[0] == "put"]))

    def test_unknown_active_requires_original_state(self):
        sid = "0123456789abcdef"
        self.remote.files[bridge.BASE + "/active.session"] = bridge.session_text(sid)
        with self.assertRaisesRegex(bridge.BridgeError, "ORIGINAL_STATE"):
            self.client.prepare()
        self.assertIsNone(self.state.current())
        self.assertFalse(any(call[0] == "put" for call in self.remote.calls))

    def test_all_five_orphan_remote_slot_files_prevent_new_job(self):
        sid = self.ready()
        for area, suffix in (("inbox", ".job"), ("inbox", ".ready"),
                             ("outbox", ".accepted"), ("outbox", ".report"), ("outbox", ".done")):
            with self.subTest(area=area, suffix=suffix):
                path = f"{bridge.BASE}/{sid}/{area}/0001{suffix}"
                self.remote.files[path] = b"TEST orphan record"
                before = len([c for c in self.remote.calls if c[0] == "put"])
                with self.assertRaisesRegex(bridge.BridgeError, "REMOTE_HISTORY"):
                    self.client.submit("PING")
                self.assertEqual(before, len([c for c in self.remote.calls if c[0] == "put"]))
                self.assertFalse(self.client.task_path(sid, "0001", ".job").exists())
                del self.remote.files[path]

    def test_uncertain_job_put_resumes_same_immutable_sequence(self):
        sid = self.ready()
        remote_job = f"{bridge.BASE}/{sid}/inbox/0001.job"
        self.remote.fail_put = remote_job
        with self.assertRaisesRegex(bridge.BridgeError, "TIMEOUT"):
            self.client.submit("PING")
        saved = self.client.task_path(sid, "0001", ".job").read_bytes()
        self.assertNotIn(f"{bridge.BASE}/{sid}/inbox/0001.ready", self.remote.files)
        recovered = bridge.Client(bridge.State(self.state.root), self.remote)
        self.assertEqual("TASK_SUBMITTED seq=0001", recovered.submit("PING"))
        self.assertEqual(saved, recovered.task_path(sid, "0001", ".job").read_bytes())
        self.assertEqual(1, len(recovered.history(sid)))
        puts = [call[1] for call in self.remote.calls if call[0] == "put"]
        self.assertEqual([remote_job, remote_job, remote_job[:-4] + ".ready"], puts[-3:])

    def test_uncertain_ready_does_not_allocate_or_change_operation(self):
        sid = self.ready()
        self.remote.fail_put = f"{bridge.BASE}/{sid}/inbox/0001.ready"
        with self.assertRaises(bridge.BridgeError):
            self.client.submit("PING")
        with self.assertRaisesRegex(bridge.BridgeError, "PENDING_DIFFERENT"):
            self.client.submit("STOP")
        self.assertEqual("TASK_SUBMITTED seq=0001", self.client.submit("PING"))
        self.assertFalse(self.client.task_path(sid, "0002", ".job").exists())

    def test_verified_collection_allows_next_sequence(self):
        sid = self.ready()
        self.client.submit("PING")
        self.result(sid)
        self.assertEqual("TASK_COLLECTED seq=0001 handler_rc=0", self.client.collect("0001"))
        self.assertEqual("TASK_ALREADY_COLLECTED seq=0001", self.client.collect("0001"))
        self.assertEqual("TASK_SUBMITTED seq=0002", self.client.submit("SNAPSHOT"))

    def test_canary_operations_require_exact_b2_receiver_before_job_creation(self):
        sid = self.ready()
        receiver_path = f"{bridge.BASE}/{sid}/session.receiver"
        for marker in (None, f"B1 RECEIVER {sid} B1 END\n".encode(),
                       b"B1 RECEIVER 0123456789abcdef B2 END\n",
                       f"B1 RECEIVER {sid} B2 END\r\n".encode()):
            if marker is not None:
                self.remote.files[receiver_path] = marker
            for operation in bridge.CANARY_OPS:
                with self.subTest(marker=marker, operation=operation):
                    before = len([call for call in self.remote.calls if call[0] == "put"])
                    with self.assertRaises(bridge.BridgeError):
                        self.client.submit(operation)
                    self.assertFalse(self.client.task_path(sid, "0001", ".job").exists())
                    self.assertEqual(before, len([call for call in self.remote.calls if call[0] == "put"]))

    def test_load_requires_latest_baseline_successfully_collected(self):
        sid = self.canary_ready()
        with self.assertRaisesRegex(bridge.BridgeError, "SUCCESSFUL_CANARY_BASELINE_REQUIRED"):
            self.client.submit("CANARY_LOAD")
        self.client.submit("CANARY_BASELINE")
        self.result(sid, body=self.canary_body(sid, "CANARY_BASELINE"))
        with self.assertRaisesRegex(bridge.BridgeError, "SUCCESSFUL_CANARY_BASELINE_REQUIRED"):
            self.client.submit("CANARY_LOAD")
        self.client.collect("0001")
        self.collected_baseline(sid, "0002", rc=10)
        with self.assertRaisesRegex(bridge.BridgeError, "SUCCESSFUL_CANARY_BASELINE_REQUIRED"):
            self.client.submit("CANARY_LOAD")
        self.assertFalse(self.client.task_path(sid, "0003", ".job").exists())

    def test_load_uncertain_puts_retry_same_sequence_and_never_second_load(self):
        sid = self.canary_ready()
        self.collected_baseline(sid)
        remote_prefix = f"{bridge.BASE}/{sid}/inbox/0002"
        saved = None
        for suffix in (".job", ".ready"):
            self.remote.fail_put = remote_prefix + suffix
            with self.assertRaisesRegex(bridge.BridgeError, "TIMEOUT"):
                self.client.submit("CANARY_LOAD")
            current = self.client.task_path(sid, "0002", ".job").read_bytes()
            if saved is not None:
                self.assertEqual(saved, current)
            saved = current
            self.assertEqual(2, len(self.client.history(sid)))
            with self.assertRaisesRegex(bridge.BridgeError, "PENDING_DIFFERENT_OPERATION"):
                self.client.submit("CANARY_CLEANUP")
        recovered = bridge.Client(bridge.State(self.state.root), self.remote)
        self.assertEqual("TASK_SUBMITTED seq=0002", recovered.submit("CANARY_LOAD"))
        self.result(sid, "0002", rc=10, body=self.canary_body(sid, "CANARY_LOAD"))
        self.assertEqual("TASK_COLLECTED seq=0002 handler_rc=10", recovered.collect("0002"))
        with self.assertRaisesRegex(bridge.BridgeError, "CANARY_LOAD_ALREADY_CREATED"):
            recovered.submit("CANARY_LOAD")
        self.assertEqual("TASK_SUBMITTED seq=0003", recovered.submit("CANARY_CLEANUP"))
        self.result(sid, "0003", body=self.canary_body(sid, "CANARY_CLEANUP"))
        recovered.collect("0003")
        with self.assertRaisesRegex(bridge.BridgeError, "CANARY_LOAD_ALREADY_CREATED"):
            recovered.submit("CANARY_LOAD")
        self.assertEqual(["CANARY_BASELINE", "CANARY_LOAD", "CANARY_CLEANUP"],
                         [task["op"] for task in recovered.history(sid)])
        self.assertFalse(self.client.task_path(sid, "0004", ".job").exists())

    def test_cleanup_can_be_requested_without_implicitly_loading(self):
        sid = self.canary_ready()
        self.assertEqual("TASK_SUBMITTED seq=0001", self.client.submit("CANARY_CLEANUP"))
        self.result(sid, rc=10, body=self.canary_body(sid, "CANARY_CLEANUP"))
        self.assertEqual("TASK_COLLECTED seq=0001 handler_rc=10", self.client.collect("0001"))
        self.assertEqual(["CANARY_CLEANUP"], [task["op"] for task in self.client.history(sid)])
        with self.assertRaisesRegex(bridge.BridgeError, "SUCCESSFUL_CANARY_BASELINE_REQUIRED"):
            self.client.submit("CANARY_LOAD")

    def test_canary_envelope_binds_sid_operation_and_complete_boundaries(self):
        sid = self.canary_ready()
        self.client.submit("CANARY_BASELINE")
        body = self.canary_body(sid, "CANARY_BASELINE")
        bad_bodies = (body.replace(b"loader/v1", b"loader/v2"),
                      body.replace(sid.encode(), b"0123456789abcdef"),
                      body.replace(b"operation=CANARY_BASELINE", b"operation=CANARY_LOAD"),
                      body.replace(b"report_begin=true\n", b""),
                      body[:-1], body + b"TEST trailing bytes\n")
        for changed in bad_bodies:
            with self.subTest(body=changed):
                prefix = self.result(sid, rc=10, body=changed)
                summary = bridge.validate_result(self.client.task_path(sid, "0001", ".job").read_bytes(),
                    *[self.remote.files[prefix + suffix] for suffix in (".accepted", ".done", ".report")])
                self.assertEqual("incomplete_envelope", summary["canary_validation"])
                self.assertFalse(summary["canary_preflight_ready"])
                self.assertFalse(self.client.task_path(sid, "0001", ".collected.json").exists())
        self.result(sid, rc=10, body=body)
        self.assertEqual("TASK_COLLECTED seq=0001 handler_rc=10", self.client.collect("0001"))
        summary = json.loads(self.client.task_path(sid, "0001", ".collected.json").read_bytes())
        self.assertEqual("envelope_received_only", summary["canary_validation"])
        self.assertIsNone(summary["snapshot"])
        self.assertFalse(any(call[0] == "get" and call[1].startswith("Download/FindUAS/Probe/")
                             for call in self.remote.calls))

    def test_timed_out_load_keeps_partial_report_and_allows_explicit_cleanup(self):
        sid = self.canary_ready()
        self.collected_baseline(sid)
        self.client.submit("CANARY_LOAD")
        body = self.canary_body(sid, "CANARY_LOAD").removesuffix(b"report_end=true\n")
        body += b"BEGIN copy_file\ncommand.copy_file.rc=0\nEND copy_file\nattach_dispatch_count=1\n"
        prefix = self.result(sid, "0002", rc=124, body=body)
        self.assertEqual("TASK_COLLECTED seq=0002 handler_rc=124", self.client.collect("0002"))
        self.assertEqual(self.remote.files[prefix + ".report"], self.client.task_path(sid, "0002", ".report").read_bytes())
        summary = json.loads(self.client.task_path(sid, "0002", ".collected.json").read_bytes())
        self.assertEqual("incomplete_envelope", summary["canary_validation"])
        with self.assertRaisesRegex(bridge.BridgeError, "CANARY_LOAD_ALREADY_CREATED"):
            self.client.submit("CANARY_LOAD")
        self.assertEqual("TASK_SUBMITTED seq=0003", self.client.submit("CANARY_CLEANUP"))

    def test_zero_rc_invalid_baseline_is_terminal_but_never_admits_load(self):
        sid = self.canary_ready()
        self.client.submit("CANARY_BASELINE")
        self.result(sid, body=b"TEST unexpected helper output\n")
        self.assertEqual("TASK_COLLECTED seq=0001 handler_rc=0", self.client.collect("0001"))
        summary = json.loads(self.client.task_path(sid, "0001", ".collected.json").read_bytes())
        self.assertEqual("invalid_envelope", summary["canary_validation"])
        with self.assertRaisesRegex(bridge.BridgeError, "SUCCESSFUL_CANARY_BASELINE_REQUIRED"):
            self.client.submit("CANARY_LOAD")
        self.assertEqual("TASK_SUBMITTED seq=0002", self.client.submit("CANARY_CLEANUP"))

    def test_baseline_gate_uses_unique_outer_preflight_not_command_output(self):
        section = b"BEGIN test_read\npreflight_ready=true\ncommand.test_read.rc=0\nEND test_read\n"
        for content in (section, section + b"preflight_ready=false\n",
                        b"preflight_ready=true\npreflight_ready=true\n",
                        b"preflight_ready=true\r\n", b"BEGIN test_read\npreflight_ready=true\n",
                        b"preflight_ready=true\nBEGIN test_read\nEND test_read\n"):
            with self.subTest(content=content):
                self.assertFalse(bridge.canary_preflight_ready(content))
        self.assertTrue(bridge.canary_preflight_ready(section + b"preflight_ready=true\n"))
        self.assertTrue(bridge.canary_preflight_ready(
            b"BEGIN update_sys.upgrade.app_self.path\n\ncommand.update_sys.upgrade.app_self.path.rc=0\n"
            b"END update_sys.upgrade.app_self.path\npreflight_ready=true\n"))
        sid = self.canary_ready()
        self.client.submit("CANARY_BASELINE")
        body = self.canary_body(sid, "CANARY_BASELINE").replace(b"preflight_ready=true\n", section)
        self.result(sid, body=body)
        self.client.collect("0001")
        with self.assertRaisesRegex(bridge.BridgeError, "SUCCESSFUL_CANARY_BASELINE_REQUIRED"):
            self.client.submit("CANARY_LOAD")
        self.collected_baseline(sid, "0002")
        self.assertEqual("TASK_SUBMITTED seq=0003", self.client.submit("CANARY_LOAD"))

    def test_rejected_load_still_consumes_the_one_load_allocation(self):
        sid = self.canary_ready()
        self.collected_baseline(sid)
        self.client.submit("CANARY_LOAD")
        self.result(sid, "0002", rc=65, op="REJECTED", body=b"job_error=TEST_REJECTED\n")
        self.client.collect("0002")
        with self.assertRaisesRegex(bridge.BridgeError, "CANARY_LOAD_ALREADY_CREATED"):
            self.client.submit("CANARY_LOAD")

    def test_stage_canary_and_original_stage_use_only_fixed_destinations(self):
        inputs = []
        for index in range(5):
            source = Path(self.temp.name) / f"TEST-input-{index}"
            source.write_bytes(f"TEST independent fixture {index}\n".encode())
            inputs.append(source)
        self.assertEqual("SCRIPTS_STAGED_VERIFIED", self.client.stage_canary(*inputs[:3]))
        self.assertEqual("SCRIPTS_STAGED_VERIFIED", self.client.stage(*inputs[3:]))
        puts = [call for call in self.remote.calls if call[0] == "put"]
        self.assertEqual(["Download/B2.sh", "Download/L1.sh", "Download/FindUAS_ARTTI_V2.so",
                          "Download/B1.sh", "Download/F4.sh"], [call[1] for call in puts])
        self.assertEqual([source.read_bytes() for source in inputs], [call[2] for call in puts])
        self.assertIsNone(self.state.current())
        self.assertEqual(5, len(self.remote.calls))

    def test_receiver_rejected_job_is_terminal_failure_not_replayed(self):
        sid = self.ready()
        self.client.submit("PING")
        self.result(sid, rc=65, op="REJECTED", body=b"job_error=SNAPSHOT_OR_CANONICAL_CHECK_FAILED\n")
        self.assertEqual("TASK_COLLECTED seq=0001 handler_rc=65", self.client.collect("0001"))
        self.assertEqual("TASK_ALREADY_COLLECTED seq=0001", self.client.collect("0001"))
        self.assertEqual("TASK_SUBMITTED seq=0002", self.client.submit("PING"))

    def test_accepted_digest_mismatch_never_marks_collected(self):
        sid = self.ready()
        self.client.submit("PING")
        prefix = self.result(sid)
        ack = self.remote.files[prefix + ".accepted"]
        fields = bridge.record(ack, "ACCEPTED")
        self.remote.files[prefix + ".accepted"] = ack.replace(fields["sha"].encode(), b"0" * 64)
        with self.assertRaisesRegex(bridge.BridgeError, "ACCEPTED_JOB_MISMATCH"):
            self.client.collect("0001")
        self.assertFalse(self.client.task_path(sid, "0001", ".collected.json").exists())

    def test_report_rc_end_and_digest_are_bound_to_done(self):
        sid = self.ready()
        self.client.submit("PING")
        prefix = self.result(sid)
        job = self.client.task_path(sid, "0001", ".job").read_bytes()
        ack, done, report = [self.remote.files[prefix + ext] for ext in (".accepted", ".done", ".report")]
        for changed in (report + b"EXTRA", report.replace(b"handler_rc=0", b"handler_rc=1"), report[:-1]):
            with self.subTest(changed=changed[-40:]), self.assertRaises(bridge.BridgeError):
                bridge.validate_result(job, ack, done, changed)
        rc_report = report.replace(b"handler_rc=0", b"handler_rc=1")
        consistent_digest = f"B1 DONE {sid} 0001 0 {len(rc_report)} {bridge.digest(rc_report)} END\n".encode()
        with self.assertRaisesRegex(bridge.BridgeError, "ENVELOPE"):
            bridge.validate_result(job, ack, consistent_digest, rc_report)

    def test_snapshot_rc10_fetches_only_fixed_f4_report(self):
        sid = self.ready()
        self.client.submit("SNAPSHOT")
        name = "FindUAS_F4_20200101T000000Z_123.txt"
        body = ("F4_SAVED state=INCOMPLETE\nreport=/storage/ABCD-1234/Download/FindUAS/Probe/"
                + name + "\nF4_END\n").encode()
        self.result(sid, rc=10, body=body)
        snapshot = b"schema=finduas-rc2-fuli-baseline/v4\nreport_begin=true\nrun_state=INCOMPLETE\nreport_end=true\n"
        self.remote.files["Download/FindUAS/Probe/" + name] = snapshot
        self.assertEqual("TASK_COLLECTED seq=0001 handler_rc=10", self.client.collect("0001"))
        summary = json.loads(self.client.task_path(sid, "0001", ".collected.json").read_bytes())
        self.assertEqual("envelope_received_only", summary["snapshot_validation"])
        self.assertEqual(snapshot, self.client.task_path(sid, "0001", ".snapshot.txt").read_bytes())

    def test_snapshot_path_escape_rejected_before_fetch(self):
        sid = self.ready()
        self.client.submit("SNAPSHOT")
        for path in ("/data/private.txt", "/storage/ABCD-1234/Download/FindUAS/Probe/../secret.txt",
                     "/storage/ABCD-1234/Download/FindUAS/Probe/FindUAS_F3_20200101T000000Z_123.txt"):
            self.result(sid, body=f"F4_SAVED state=COMPLETE\nreport={path}\nF4_END\n".encode())
            before = len(self.remote.calls)
            with self.assertRaisesRegex(bridge.BridgeError, "SNAPSHOT_PATH"):
                self.client.collect("0001")
            self.assertEqual(3, len(self.remote.calls) - before)

    def test_closed_pending_becomes_unknown_without_replay_then_rotates(self):
        sid = self.ready()
        self.client.submit("PING")
        self.remote.files[f"{bridge.BASE}/{sid}/session.closed"] = f"B1 CLOSED {sid} TTL END\n".encode()
        with self.assertRaisesRegex(bridge.BridgeError, "COLLECT_PENDING"):
            self.client.prepare()
        puts = len([call for call in self.remote.calls if call[0] == "put"])
        self.assertEqual("TASK_UNAVAILABLE seq=0001 outcome=UNKNOWN", self.client.collect("0001"))
        self.assertEqual(puts, len([call for call in self.remote.calls if call[0] == "put"]))
        with self.assertRaisesRegex(bridge.BridgeError, "MUST_ROTATE"):
            self.client.submit("PING")
        self.assertEqual("SESSION_PREPARED", self.client.prepare())
        self.assertNotEqual(sid, self.state.current())
        self.assertEqual(bridge.session_text(sid), self.remote.files[f"{bridge.BASE}/{sid}/active.session"])

    def test_closed_other_active_does_not_forget_current_pending(self):
        sid = self.ready()
        self.client.submit("PING")
        other = "fedcba9876543210"
        self.remote.files[bridge.BASE + "/active.session"] = bridge.session_text(other)
        self.remote.files[f"{bridge.BASE}/{other}/session.closed"] = f"B1 CLOSED {other} STOP END\n".encode()
        with self.assertRaisesRegex(bridge.BridgeError, "CONFLICT"):
            self.client.prepare()
        self.assertEqual(sid, self.state.current())
        self.assertFalse(any(call[0] == "archive" for call in self.remote.calls))

    def test_done_created_before_closed_read_is_collected_not_unknown(self):
        sid = self.ready()
        self.client.submit("STOP")
        original_get = self.remote.get
        def get(remote):
            if remote == f"{bridge.BASE}/{sid}/session.closed":
                self.result(sid, body=b"stop_requested=true\n")
                self.remote.files[remote] = f"B1 CLOSED {sid} STOP END\n".encode()
            return original_get(remote)
        self.remote.get = get
        self.assertEqual("TASK_COLLECTED seq=0001 handler_rc=0", self.client.collect("0001"))
        self.assertFalse(self.client.task_path(sid, "0001", ".unavailable.json").exists())

    def test_second_flock_caller_is_rejected(self):
        with self.state.lock():
            with self.assertRaisesRegex(bridge.BridgeError, "STATE_BUSY"):
                with bridge.State(self.state.root).lock():
                    self.fail("concurrent state access")

    def test_noncanonical_and_out_of_range_records_rejected(self):
        sid = "0123456789abcdef"
        for data, kind in ((f"B1 SESSION {sid} END\r\n".encode(), "SESSION"),
                           (f"B1 SESSION {sid} END\nEXTRA\n".encode(), "SESSION"),
                           (f"B1 JOB {sid} 0000 PING END\n".encode(), "JOB"),
                           (f"B1 JOB {sid} 0065 PING END\n".encode(), "JOB"),
                           (f"B1 JOB {sid} 0001 SHELL END\n".encode(), "JOB"),
                           (f"B1 DONE {sid} 0001 256 12 {'0' * 64} END\n".encode(), "DONE")):
            with self.subTest(kind=kind, data=data), self.assertRaises(bridge.BridgeError):
                bridge.record(data, kind)

    def test_local_collected_report_tamper_blocks_sequence_advance(self):
        sid = self.ready()
        self.client.submit("PING")
        self.result(sid)
        self.client.collect("0001")
        self.client.task_path(sid, "0001", ".report").write_bytes(b"TEST changed after collection")
        with self.assertRaisesRegex(bridge.BridgeError, "REPORT_DIGEST"):
            self.client.submit("SNAPSHOT")
        self.assertFalse(self.client.task_path(sid, "0002", ".job").exists())

    def test_get_uses_fresh_paths_and_only_exit3_means_missing(self):
        transport = bridge.Transport(Path("TEST-mtp-bridge"), self.state)
        destinations = []
        def call(operation, remote, local):
            self.assertEqual("get", operation)
            path = Path(local)
            self.assertFalse(path.exists())
            destinations.append(path)
            if len(destinations) == 1:
                return 3
            path.write_bytes(b"TEST payload")
            return 0 if len(destinations) == 2 else 3
        transport.call = call
        self.assertIsNone(transport.get("Download/B1.sh"))
        self.assertEqual(b"TEST payload", transport.get("Download/B1.sh"))
        with self.assertRaisesRegex(bridge.BridgeError, "MISSING_WITH_LOCAL"):
            transport.get("Download/B1.sh")
        self.assertEqual(3, len(set(destinations)))

    def test_transport_cooldown_and_timeout_logging_without_retry(self):
        clock = [10.0]
        slept = []
        def sleep(seconds):
            slept.append(seconds)
            clock[0] += seconds
        def run(args, **kwargs):
            self.assertLessEqual(kwargs["timeout"], 30)
            self.assertIsInstance(args, list)
            kwargs["stdout"].write(b"TEST raw stdout")
            kwargs["stderr"].write(b"TEST raw stderr")
            clock[0] += 0.2
            if len(slept) == 2:
                raise subprocess.TimeoutExpired(args, kwargs["timeout"])
            return subprocess.CompletedProcess(args, 0)
        with patch.object(bridge.time, "monotonic", side_effect=lambda: clock[0]), \
             patch.object(bridge.time, "sleep", side_effect=sleep), \
             patch.object(bridge.subprocess, "run", side_effect=run) as invoked:
            transport = bridge.Transport(Path("TEST-mtp-bridge"), self.state)
            transport.call("mkdir", "Download/FindUAS/Bridge")
            with self.assertRaisesRegex(bridge.BridgeError, "TIMEOUT_UNCERTAIN"):
                transport.call("mkdir", "Download/FindUAS/Bridge")
            transport.call("mkdir", "Download/FindUAS/Bridge")
            self.assertEqual(3, invoked.call_count)
        self.assertEqual([1.0, 1.0, 1.0], slept)
        self.assertEqual(3, len(list((self.state.root / "logs").glob("*.stdout"))))
        self.assertEqual(3, len(list((self.state.root / "logs").glob("*.stderr"))))
        results = [json.loads(p.read_text()) for p in (self.state.root / "logs").glob("*.json")]
        self.assertEqual(1, sum(result.get("timeout", False) for result in results))
        self.assertTrue(all("ended_monotonic" in result for result in results))


if __name__ == "__main__":
    unittest.main()
