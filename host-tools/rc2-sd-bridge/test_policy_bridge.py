import json
from pathlib import Path
import unittest

import bridge
import test_bridge as base_tests


class PolicyClientTest(unittest.TestCase):
    setUp = base_tests.ClientTest.setUp
    ready = base_tests.ClientTest.ready
    result = base_tests.ClientTest.result

    def policy_ready(self):
        sid = self.ready()
        self.remote.files[f"{bridge.BASE}/{sid}/session.receiver"] = (
            f"B1 RECEIVER {sid} B4 END\n".encode())
        return sid

    def body(self, sid, operation, ready=True):
        return (f"schema=finduas-rc2-cloud-policy-loader/v1\nsid={sid}\noperation={operation}\n"
                f"report_begin=true\npreflight_ready={str(ready).lower()}\n"
                "attach_dispatch_count=0\ntest_file_created=false\ntest_file_removed=false\n"
                "native_result_observed=false\nreport_end=true\n").encode()

    def baseline(self, sid, seq="0001", rc=0, ready=True):
        self.client.submit("POLICY_BASELINE")
        self.result(sid, seq, rc, self.body(sid, "POLICY_BASELINE", ready))
        self.client.collect(seq)

    def test_b4_marker_is_required_and_other_lanes_cannot_substitute(self):
        sid = self.ready()
        receiver = f"{bridge.BASE}/{sid}/session.receiver"
        for marker in (None, f"B1 RECEIVER {sid} B2 END\n".encode(),
                       b"B1 RECEIVER 0123456789abcdef B4 END\n",
                       f"B1 RECEIVER {sid} B4 END\r\n".encode()):
            if marker is not None:
                self.remote.files[receiver] = marker
            for operation in bridge.POLICY_OPS:
                with self.subTest(marker=marker, operation=operation):
                    with self.assertRaises(bridge.BridgeError):
                        self.client.submit(operation)
                    self.assertFalse(self.client.task_path(sid, "0001", ".job").exists())
        self.remote.files[receiver] = f"B1 RECEIVER {sid} B4 END\n".encode()
        with self.assertRaises(bridge.BridgeError):
            self.client.submit("RID_BASELINE")
        self.assertEqual("TASK_SUBMITTED seq=0001", self.client.submit("POLICY_BASELINE"))

    def test_read_needs_latest_collected_valid_successful_baseline(self):
        sid = self.policy_ready()
        with self.assertRaisesRegex(bridge.BridgeError, "SUCCESSFUL_POLICY_BASELINE_REQUIRED"):
            self.client.submit("POLICY_READ")
        self.baseline(sid)
        self.client.submit("POLICY_BASELINE")
        self.result(sid, "0002", 0, self.body(sid, "POLICY_BASELINE"))
        with self.assertRaisesRegex(bridge.BridgeError, "SUCCESSFUL_POLICY_BASELINE_REQUIRED"):
            self.client.submit("POLICY_READ")
        self.client.collect("0002")
        self.baseline(sid, "0003", 10)
        with self.assertRaisesRegex(bridge.BridgeError, "SUCCESSFUL_POLICY_BASELINE_REQUIRED"):
            self.client.submit("POLICY_READ")
        self.baseline(sid, "0004", ready=False)
        with self.assertRaisesRegex(bridge.BridgeError, "SUCCESSFUL_POLICY_BASELINE_REQUIRED"):
            self.client.submit("POLICY_READ")
        self.baseline(sid, "0005")
        self.assertEqual("TASK_SUBMITTED seq=0006", self.client.submit("POLICY_READ"))

    def test_uncertain_transfer_reuses_job_and_terminal_read_is_not_repeated(self):
        sid = self.policy_ready()
        self.baseline(sid)
        self.remote.fail_put = f"{bridge.BASE}/{sid}/inbox/0002.ready"
        with self.assertRaisesRegex(bridge.BridgeError, "TIMEOUT"):
            self.client.submit("POLICY_READ")
        saved = self.client.task_path(sid, "0002", ".job").read_bytes()
        with self.assertRaisesRegex(bridge.BridgeError, "PENDING_DIFFERENT_OPERATION"):
            self.client.submit("POLICY_CLEANUP")
        self.assertEqual("TASK_SUBMITTED seq=0002", self.client.submit("POLICY_READ"))
        self.assertEqual(saved, self.client.task_path(sid, "0002", ".job").read_bytes())
        self.result(sid, "0002", 10, self.body(sid, "POLICY_READ"))
        self.client.collect("0002")
        with self.assertRaisesRegex(bridge.BridgeError, "POLICY_READ_ALREADY_CREATED"):
            self.client.submit("POLICY_READ")
        self.assertEqual("TASK_SUBMITTED seq=0003", self.client.submit("POLICY_CLEANUP"))

    def test_incomplete_read_can_be_cleaned_up_but_not_replayed(self):
        sid = self.policy_ready()
        self.baseline(sid)
        self.client.submit("POLICY_READ")
        partial = self.body(sid, "POLICY_READ").removesuffix(b"report_end=true\n")
        self.result(sid, "0002", 124, partial)
        self.client.collect("0002")
        summary = json.loads(self.client.task_path(sid, "0002", ".collected.json").read_bytes())
        self.assertEqual("incomplete_envelope", summary["policy_validation"])
        self.assertFalse(summary["policy_preflight_ready"])
        with self.assertRaisesRegex(bridge.BridgeError, "POLICY_READ_ALREADY_CREATED"):
            self.client.submit("POLICY_READ")
        self.assertEqual("TASK_SUBMITTED seq=0003", self.client.submit("POLICY_CLEANUP"))

    def test_inner_command_text_cannot_supply_preflight_ready(self):
        sid = self.policy_ready()
        self.client.submit("POLICY_BASELINE")
        body = self.body(sid, "POLICY_BASELINE").replace(b"preflight_ready=true\n",
            b"BEGIN fixture\npreflight_ready=true\ncommand.fixture.rc=0\nEND fixture\n")
        self.result(sid, body=body)
        self.client.collect("0001")
        with self.assertRaisesRegex(bridge.BridgeError, "SUCCESSFUL_POLICY_BASELINE_REQUIRED"):
            self.client.submit("POLICY_READ")
        self.assertEqual("TASK_SUBMITTED seq=0002", self.client.submit("POLICY_CLEANUP"))

    def test_zero_rc_foreign_envelope_is_terminal_not_a_successful_baseline(self):
        sid = self.policy_ready()
        self.client.submit("POLICY_BASELINE")
        body = self.body(sid, "POLICY_BASELINE").replace(
            b"schema=finduas-rc2-cloud-policy-loader/v1", b"schema=finduas-rc2-canary-loader/v1")
        self.result(sid, body=body)
        self.client.collect("0001")
        summary = json.loads(self.client.task_path(sid, "0001", ".collected.json").read_bytes())
        self.assertEqual("invalid_envelope", summary["policy_validation"])
        with self.assertRaisesRegex(bridge.BridgeError, "SUCCESSFUL_POLICY_BASELINE_REQUIRED"):
            self.client.submit("POLICY_READ")

    def test_stage_only_transports_three_fixed_files(self):
        inputs = []
        for index in range(3):
            path = Path(self.temp.name) / f"TEST-rid-input-{index}"
            path.write_bytes(f"TEST independent source {index}\n".encode())
            inputs.append(path)
        self.assertEqual("SCRIPTS_STAGED_VERIFIED", self.client.stage_policy(*inputs))
        self.assertEqual(["Download/B4.sh", "Download/L3.sh", "Download/FindUAS_CLOUD_POLICY.so"],
                         [call[1] for call in self.remote.calls])
        self.assertIsNone(self.state.current())


if __name__ == "__main__":
    unittest.main()
