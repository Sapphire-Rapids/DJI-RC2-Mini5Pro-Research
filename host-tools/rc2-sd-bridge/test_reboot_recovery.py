import json
from pathlib import Path
import tempfile
import unittest

import bridge
import test_bridge as base_tests


class RebootTransport(base_tests.FakeTransport):
    def __init__(self):
        super().__init__()
        self.archive_timeout = None
        self.mkdir_timeout = False

    def archive_after_reboot(self, sid):
        self.calls.append(("archive-after-reboot", sid))
        if self.archive_timeout == "before":
            self.archive_timeout = None
            raise bridge.BridgeError("TRANSPORT_TIMEOUT_UNCERTAIN")
        active = bridge.BASE + "/active.session"
        destination = f"{bridge.BASE}/{sid}/active.session"
        if active in self.files:
            if destination in self.files or self.files[active] != bridge.session_text(sid):
                raise bridge.BridgeError("ARCHIVE_CONFLICT")
            self.files[destination] = self.files.pop(active)
        elif self.files.get(destination) != bridge.session_text(sid):
            raise bridge.BridgeError("ARCHIVE_CONTENT_MISMATCH")
        if self.archive_timeout == "after":
            self.archive_timeout = None
            raise bridge.BridgeError("TRANSPORT_TIMEOUT_UNCERTAIN")

    def mkdir(self, remote):
        super().mkdir(remote)
        if self.mkdir_timeout:
            self.mkdir_timeout = False
            raise bridge.BridgeError("TRANSPORT_TIMEOUT_UNCERTAIN")


class RebootRecoveryTest(unittest.TestCase):
    ready = base_tests.ClientTest.ready
    result = base_tests.ClientTest.result

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = bridge.State(Path(self.temp.name))
        self.remote = RebootTransport()
        self.client = bridge.Client(self.state, self.remote)

    def baseline(self):
        sid = self.ready()
        self.remote.files[f"{bridge.BASE}/{sid}/session.receiver"] = f"B1 RECEIVER {sid} B5 END\n".encode()
        self.client.submit("STRUCTURE_BASELINE")
        body = (f"schema=finduas-rc2-policy-structure-loader/v1\nsid={sid}\n"
                "operation=STRUCTURE_BASELINE\nreport_begin=true\n"
                "preflight_ready=true\nreport_end=true\n").encode()
        self.result(sid, body=body)
        self.client.collect("0001")
        return sid

    def recover(self, sid):
        return self.client.recover_after_reboot(sid, True)

    def plan(self, sid):
        return json.loads((self.state.session(sid) / "reboot-recovery.request.json").read_bytes())

    def mutating_calls(self):
        return [call for call in self.remote.calls if call[0] in ("put", "mkdir", "archive-after-reboot")]

    def restart_client(self):
        self.state = bridge.State(Path(self.temp.name))
        self.client = bridge.Client(self.state, self.remote)

    def test_success_preserves_history_and_does_not_forge_closed_or_start_worker(self):
        sid = self.baseline()
        records = {path.name: path.read_bytes() for path in (self.state.session(sid) / "tasks").iterdir()}
        remote_before = dict(self.remote.files)
        self.remote.calls.clear()
        self.assertEqual("SESSION_RECOVERED_AFTER_REBOOT", self.recover(sid))
        new_sid = self.state.current()
        self.assertNotEqual(sid, new_sid)
        self.assertEqual("operator-confirmed-reboot", self.plan(sid)["reason"])
        self.assertEqual(bridge.session_text(sid), self.remote.files[f"{bridge.BASE}/{sid}/active.session"])
        for path, content in remote_before.items():
            if path != bridge.BASE + "/active.session":
                self.assertEqual(content, self.remote.files[path])
        self.assertEqual(records, {path.name: path.read_bytes()
                                  for path in (self.state.session(sid) / "tasks").iterdir()})
        self.assertFalse((self.state.session(sid) / "closed.session").exists())
        self.assertFalse(any(path.endswith("session.closed") for path in self.remote.files))
        self.assertNotIn(f"{bridge.BASE}/{new_sid}/worker.lock", self.remote.files)
        self.assertEqual([], self.client.history(new_sid))
        self.assertEqual(("put", bridge.BASE + "/active.session", bridge.session_text(new_sid)),
                         self.mutating_calls()[-1])
        calls = len(self.remote.calls)
        self.assertEqual("SESSION_ALREADY_RECOVERED_AFTER_REBOOT", self.recover(sid))
        self.assertEqual(calls, len(self.remote.calls))
        self.assertEqual(new_sid, self.state.current())

    def test_explicit_operator_confirmation_is_required_before_transport(self):
        sid = self.baseline()
        self.remote.calls.clear()
        with self.assertRaisesRegex(bridge.BridgeError, "OPERATOR_CONFIRMED_REBOOT_REQUIRED"):
            self.client.recover_after_reboot(sid)
        self.assertEqual([], self.remote.calls)

    def test_original_owned_state_is_required(self):
        sid = self.baseline()
        (self.state.session(sid) / "owned.session").unlink()
        self.remote.calls.clear()
        with self.assertRaisesRegex(bridge.BridgeError, "ORIGINAL_STATE_DIR_REQUIRED"):
            self.recover(sid)
        self.assertEqual([], self.remote.calls)

    def test_uncollected_result_is_rejected(self):
        sid = self.baseline()
        self.client.submit("PING")
        self.result(sid, "0002")
        self.remote.calls.clear()
        with self.assertRaisesRegex(bridge.BridgeError, "COLLECT_ALL_RESULTS_FIRST"):
            self.recover(sid)
        self.assertEqual([], self.remote.calls)

    def test_unavailable_terminal_is_not_a_collected_result(self):
        sid = self.baseline()
        self.client.submit("PING")
        self.remote.files[f"{bridge.BASE}/{sid}/session.closed"] = f"B1 CLOSED {sid} TTL END\n".encode()
        self.client.collect("0002")
        self.remote.calls.clear()
        with self.assertRaisesRegex(bridge.BridgeError, "COLLECT_ALL_RESULTS_FIRST"):
            self.recover(sid)
        self.assertEqual([], self.remote.calls)

    def test_every_allocated_read_or_load_rejects_even_after_collection(self):
        for op in ("CANARY_LOAD", "RID_READ", "POLICY_READ", "STRUCTURE_READ"):
            for collected in (False, True):
                with self.subTest(operation=op, collected=collected):
                    with tempfile.TemporaryDirectory() as temp:
                        original = self.state, self.remote, self.client
                        try:
                            self.state = bridge.State(Path(temp))
                            self.remote = RebootTransport()
                            self.client = bridge.Client(self.state, self.remote)
                            sid = self.baseline()
                            bridge.immutable(self.client.task_path(sid, "0002", ".job"),
                                             bridge.job_text(sid, "0002", op))
                            if collected:
                                self.result(sid, "0002", rc=10)
                                self.client.collect("0002")
                            self.remote.calls.clear()
                            with self.assertRaisesRegex(bridge.BridgeError, "DIAGNOSTIC_ONLY_SESSION_REQUIRED"):
                                self.recover(sid)
                            self.assertEqual([], self.remote.calls)
                        finally:
                            self.state, self.remote, self.client = original

    def archive_timeout_case(self, timing):
        sid = self.baseline()
        self.remote.archive_timeout = timing
        with self.assertRaisesRegex(bridge.BridgeError, "TIMEOUT_UNCERTAIN"):
            self.recover(sid)
        plan = self.plan(sid)
        self.restart_client()
        self.assertEqual("SESSION_RECOVERED_AFTER_REBOOT", self.recover(sid))
        self.assertEqual(plan, self.plan(sid))
        self.assertEqual(plan["new_sid"], self.state.current())

    def test_archive_timeout_before_move_reuses_same_mapping(self):
        self.archive_timeout_case("before")

    def test_archive_timeout_after_move_reuses_same_mapping(self):
        self.archive_timeout_case("after")

    def test_new_active_upload_timeout_is_idempotent(self):
        sid = self.baseline()
        self.remote.fail_put = bridge.BASE + "/active.session"
        with self.assertRaisesRegex(bridge.BridgeError, "TIMEOUT_UNCERTAIN"):
            self.recover(sid)
        new_sid = self.plan(sid)["new_sid"]
        self.assertEqual(new_sid, self.state.current())
        self.restart_client()
        self.assertEqual("SESSION_RECOVERED_AFTER_REBOOT", self.recover(sid))
        self.assertEqual(new_sid, self.state.current())
        self.assertEqual(1, len([call for call in self.remote.calls if call[0] == "archive-after-reboot"]))

    def test_new_mailbox_creation_timeout_keeps_mapping(self):
        sid = self.baseline()
        self.remote.mkdir_timeout = True
        with self.assertRaisesRegex(bridge.BridgeError, "TIMEOUT_UNCERTAIN"):
            self.recover(sid)
        plan = self.plan(sid)
        self.restart_client()
        self.assertEqual("SESSION_RECOVERED_AFTER_REBOOT", self.recover(sid))
        self.assertEqual(plan["new_sid"], self.state.current())

    def test_orphan_next_slot_prevents_archive(self):
        sid = self.baseline()
        self.remote.files[f"{bridge.BASE}/{sid}/inbox/0002.job"] = b"TEST unexpected job"
        self.remote.calls.clear()
        with self.assertRaisesRegex(bridge.BridgeError, "REMOTE_HISTORY_REQUIRES_ORIGINAL_STATE"):
            self.recover(sid)
        self.assertEqual([], self.mutating_calls())

    def test_other_active_and_archive_collision_are_rejected(self):
        sid = self.baseline()
        active = bridge.BASE + "/active.session"
        self.remote.files[active] = bridge.session_text("0123456789abcdef")
        self.remote.calls.clear()
        with self.assertRaisesRegex(bridge.BridgeError, "ACTIVE_MISMATCH"):
            self.recover(sid)
        self.assertEqual([], self.mutating_calls())
        self.remote.files[active] = bridge.session_text(sid)
        self.remote.files[f"{bridge.BASE}/{sid}/active.session"] = bridge.session_text(sid)
        with self.assertRaisesRegex(bridge.BridgeError, "ARCHIVE_CONFLICT"):
            self.recover(sid)
        self.assertEqual(bridge.session_text(sid), self.remote.files[active])

    def test_tampered_recovery_request_is_rejected(self):
        sid = self.baseline()
        self.remote.archive_timeout = "after"
        with self.assertRaises(bridge.BridgeError):
            self.recover(sid)
        path = self.state.session(sid) / "reboot-recovery.request.json"
        plan = self.plan(sid)
        plan["reason"] = "TEST fake CLOSED STOP"
        path.write_text(json.dumps(plan))
        self.remote.calls.clear()
        with self.assertRaisesRegex(bridge.BridgeError, "REQUEST_CONFLICT"):
            self.recover(sid)
        self.assertEqual([], self.remote.calls)

    def test_transport_uses_explicit_reboot_archive_command(self):
        transport = bridge.Transport(Path("TEST-transport"), self.state)
        calls = []
        transport.call = lambda *args: calls.append(args)
        transport.archive_after_reboot("0123456789abcdef")
        self.assertEqual([("archive-after-reboot", "0123456789abcdef")], calls)


if __name__ == "__main__":
    unittest.main()
