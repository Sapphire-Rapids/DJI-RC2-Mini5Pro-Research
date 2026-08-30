"""Exercise the real CLI/session paths with in-memory USB fixtures only."""

import contextlib
import importlib.util
import io
import itertools
import json
from pathlib import Path
import struct
import sys
import types
import unittest
from unittest.mock import patch

from index_protocol_guard import validate_response, verify_table_identity


HERE = Path(__file__).parent
USB = types.ModuleType("usb1")
USB.USBError = type("USBError", (Exception,), {})
USB.USBErrorTimeout = type("USBErrorTimeout", (USB.USBError,), {})


def load(name):
    sys.modules["usb1"] = USB
    spec = importlib.util.spec_from_file_location("session_test_" + name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HASH_TOOLS = (load("rid_switch_control"), load("rid_eu_by_hash_switch_control"))
INDEX_TOOL = load("rid_index_switch_control")
INDEX_READ = load("rid_param_index_readonly")
TOOLS = (*HASH_TOOLS, INDEX_TOOL)


class MemoryUSB:
    """A tiny board model: packet parsing is real, endpoint I/O stays in memory."""

    def __init__(self, tool, *, forward_error=None, restore_error=None,
                 restore_applied=True, positive_ok=True, baseline=b"\x00",
                 type_id=0, size=1, minimum=0, maximum=1, table_ok=True,
                 table_count=1557, corrupt_first=False, bridge_error=False,
                 bridge_value=None):
        self.tool = tool
        self.duml = tool.load_duml_module()
        self.hash_protocol = HASH_TOOLS[0].load_protocol_module()
        self.raw = baseline
        self.forward_error = forward_error
        self.restore_error = restore_error
        self.restore_applied = restore_applied
        self.positive_ok = positive_ok
        self.type_id = type_id
        self.size = size
        self.minimum = minimum
        self.maximum = maximum
        self.table_ok = table_ok
        self.table_count = table_count
        self.corrupt_first = corrupt_first
        self.bridge_error = bridge_error
        self.bridge_value = bridge_value
        self.bridge_hash = getattr(tool, "INDEX_BRIDGE_HASH", getattr(
            tool, "RID_CTRL_BRIDGE_HASH", getattr(tool, "HASH_BRIDGE_HASH", None)))
        self.sent = []
        self.pending = b""
        self.write_count = 0
        self.released = self.handle_closed = self.context_closed = False

    def getByVendorIDAndProductID(self, vid, pid):
        return self

    def open(self):
        return self

    def claimInterface(self, interface):
        pass

    def releaseInterface(self, interface):
        self.released = True

    def close(self):
        # The real program closes both the handle and context; count both.
        if self.handle_closed:
            self.context_closed = True
        self.handle_closed = True

    def bulkWrite(self, endpoint, frame, timeout):
        body = frame[9:-2]
        if frame[8] & 7 == 3:
            body = self.hash_protocol.simple_filter(body, int.from_bytes(frame[6:8], "little"))
        command, payload = body[1], body[2:]
        self.sent.append((command, payload))
        if command in (0xF9, 0xE3):
            self.write_count += 1
            if self.write_count == 1 or self.restore_applied:
                self.raw = payload[4:] if command == 0xF9 else payload[6:]
            error = self.forward_error if self.write_count == 1 else self.restore_error
            if error == "drop":
                return len(frame)  # Delivered to the board; its reply never arrives.
            if error is not None:
                raise error("fixture ACK unavailable")
            reply = b"\x00" if command == 0xF9 else bytes(4)
        elif command == 0xE0:
            crc = 0x5F8B2AE1 if self.table_ok else 0
            reply = struct.pack("<HHII", 0, 0, crc, self.table_count)
        elif command == 0xE1:
            index = int.from_bytes(payload[2:4], "little")
            names = {1306: "EU_CE_enable_c0_rid", 1308: "EU_CE_Reg_RID_Enable",
                     1315: "eu_ce_support_remote_set_level"}
            reply = struct.pack("<HHHHHI", 0, 0, index, self.type_id, self.size, 0)
            reply += self.minimum.to_bytes(4, "little", signed=self.type_id == 4)
            reply += self.maximum.to_bytes(4, "little", signed=self.type_id == 4)
            reply += names[index].encode() + b"\x00"
        elif command == 0xE2:
            reply = bytes(4) + payload[4:6] + self.raw
        elif command == 0xF7:
            parameter_hash = int.from_bytes(payload, "little")
            positive = parameter_hash == 0x0371238A
            if (positive and not self.positive_ok) or (
                    self.bridge_error and parameter_hash == self.bridge_hash):
                reply = b"\x03"
            else:
                name = {0x0371238A: "g_config.flying_limit.max_height_0",
                        0x3CBD864F: "rid_ctrl_enable_0",
                        0xF80992FE: "EU_CE_enable_c0_rid_0"}[parameter_hash]
                type_id, size = (1, 2) if positive else (self.type_id, self.size)
                minimum, maximum = (0, 1) if positive else (self.minimum, self.maximum)
                reply = b"\x00" + struct.pack("<HHH", type_id, size, 3)
                reply += minimum.to_bytes(4, "little", signed=type_id == 4)
                reply += maximum.to_bytes(4, "little", signed=type_id == 4) + bytes(4)
                reply += name.encode() + b"\x00"
        elif command == 0xF8:
            value = b"\x78\x00" if int.from_bytes(payload, "little") == 0x0371238A else self.raw
            if self.bridge_value is not None and int.from_bytes(payload, "little") == self.bridge_hash:
                value = self.bridge_value
            reply = payload + value
        else:
            raise AssertionError("fixture received unexpected command")
        response = self.duml.build_packet(frame[5], frame[4], 0x80, 0x03, command,
                                          reply, int.from_bytes(frame[6:8], "little"))
        if self.corrupt_first:
            bad_crc = bytearray(response)
            bad_crc[-1] ^= 1
            request_echo = self.duml.build_packet(frame[5], frame[4], 0x40, 0x03, command,
                                                 bytes(12), int.from_bytes(frame[6:8], "little"))
            self.pending += bytes(bad_crc) + request_echo
        self.pending += response
        return len(frame)

    def bulkRead(self, endpoint, size, timeout):
        if not self.pending:
            raise USB.USBErrorTimeout()
        result, self.pending = self.pending, b""
        return result


def invoke(tool, board, args=()):
    output = io.StringIO()
    clock = itertools.count(0, 0.25)
    with patch.object(tool.usb1, "USBContext", return_value=board, create=True):
        with contextlib.redirect_stdout(output), patch.object(
                tool.time, "monotonic", side_effect=lambda: next(clock)):
            code = tool.main(list(args))
    return code, json.loads(output.getvalue())


class TransitionTests(unittest.TestCase):
    def test_success_uses_one_forward_and_one_exact_restore(self):
        for tool in TOOLS:
            with self.subTest(tool=tool.__name__):
                board = MemoryUSB(tool)
                code, report = invoke(tool, board, ("--target", "on"))
                self.assertEqual((code, report["state"]), (0, "A_B_A_complete"))
                self.assertEqual((board.write_count, board.raw), (2, b"\x00"))
                self.assertTrue(board.released and board.handle_closed and board.context_closed)

    def test_lost_ack_and_interrupt_after_application_still_restore(self):
        for tool in TOOLS:
            for error in (TimeoutError, KeyboardInterrupt, "drop"):
                with self.subTest(tool=tool.__name__, error=error):
                    board = MemoryUSB(tool, forward_error=error)
                    code, report = invoke(tool, board, ("--target", "on"))
                    self.assertEqual((code, report["state"]), (1, "restored_forward_unverified"))
                    self.assertEqual((board.write_count, board.raw), (2, b"\x00"))

    def test_restore_ack_loss_still_gets_exact_final_readback(self):
        for tool in TOOLS:
            with self.subTest(tool=tool.__name__):
                board = MemoryUSB(tool, restore_error=TimeoutError)
                code, report = invoke(tool, board, ("--target", "on"))
                self.assertEqual((code, report["state"]), (0, "A_B_A_complete"))
                self.assertIn({"step": "restore_write", "outcome": "fail", "error_type": "TimeoutError"}, report["steps"])
                self.assertEqual(report["steps"][-1]["outcome"], "match")

    def test_unrestored_device_is_never_reported_complete(self):
        for tool in TOOLS:
            with self.subTest(tool=tool.__name__):
                board = MemoryUSB(tool, restore_error=TimeoutError, restore_applied=False)
                code, report = invoke(tool, board, ("--target", "on"))
                self.assertEqual((code, report["state"]), (1, "restore_unverified"))
                self.assertEqual((board.write_count, board.raw), (2, b"\x01"))

    def test_readonly_and_noop_emit_json_without_writes(self):
        for tool in TOOLS:
            for args, state in (((), "probe_only"), (("--target", "off"), "already_target")):
                with self.subTest(tool=tool.__name__, args=args):
                    board = MemoryUSB(tool)
                    code, report = invoke(tool, board, args)
                    self.assertEqual((code, report["state"], board.write_count), (0, state, 0))
                    self.assertIn("requested_target", report)
                    if tool in HASH_TOOLS:
                        self.assertEqual(report["route_target"], "0x03")

    def test_positive_control_failure_prevents_target_query(self):
        for tool in HASH_TOOLS:
            board = MemoryUSB(tool, positive_ok=False)
            code, report = invoke(tool, board, ("--target", "on"))
            self.assertEqual((code, report["state"]), (1, "route_not_verified"))
            self.assertEqual(board.sent, [(0xF7, (0x0371238A).to_bytes(4, "little"))])

    def test_invalid_baseline_prevents_all_writes(self):
        for tool in TOOLS:
            board = MemoryUSB(tool, baseline=b"\x02")
            code, report = invoke(tool, board, ("--target", "on"))
            self.assertEqual((code, board.write_count), (1, 0))
            self.assertEqual(report["state"], "baseline_unavailable")

    def test_multibyte_baseline_can_be_read_but_not_written(self):
        for tool in HASH_TOOLS:
            for type_id, size in ((1, 2), (2, 4), (8, 4), (9, 8)):
                board = MemoryUSB(tool, baseline=bytes(size), type_id=type_id, size=size)
                code, report = invoke(tool, board, ("--target", "on"))
                self.assertEqual((code, board.write_count), (1, 0))
                self.assertEqual(report["state"], "write_encoding_not_admitted")

    def test_zero_range_metadata_is_readable_but_never_writes_or_restores(self):
        for tool in TOOLS:
            for type_id in (0, 4, 11):
                for args in ((), ("--target", "on"), ("--target", "off")):
                    with self.subTest(tool=tool.__name__, type_id=type_id, args=args):
                        board = MemoryUSB(tool, type_id=type_id, minimum=0, maximum=0)
                        code, report = invoke(tool, board, args)
                        self.assertEqual(board.write_count, 0)
                        self.assertFalse(any(s["step"].startswith("restore") for s in report["steps"]))
                        self.assertEqual((code, report["state"]),
                                         (1, "write_encoding_not_admitted") if args else (0, "probe_only"))

    def test_inverted_or_noncanonical_bounds_prevent_writes(self):
        for tool in TOOLS:
            for type_id, minimum, maximum in ((0, 2, 1), (0, 0, 256),
                                             (4, -129, 1), (4, 0, 128), (11, 0, 2)):
                with self.subTest(tool=tool.__name__, bounds=(type_id, minimum, maximum)):
                    board = MemoryUSB(tool, type_id=type_id, minimum=minimum, maximum=maximum)
                    code, report = invoke(tool, board, ("--target", "on"))
                    self.assertEqual((code, report["state"], board.write_count),
                                     (1, "write_encoding_not_admitted", 0))

    def test_canonical_integer_bounds_covering_both_values_allow_exact_restore(self):
        for tool in TOOLS:
            for type_id, minimum, maximum in ((0, 0, 255), (4, -128, 127), (11, 0, 1)):
                with self.subTest(tool=tool.__name__, type_id=type_id):
                    board = MemoryUSB(tool, type_id=type_id, minimum=minimum, maximum=maximum)
                    code, report = invoke(tool, board, ("--target", "on"))
                    self.assertEqual((code, report["state"], board.write_count, board.raw),
                                     (0, "A_B_A_complete", 2, b"\x00"))

    def test_requested_bridge_failure_preserves_baseline_but_prevents_writes(self):
        for tool, flag in ((HASH_TOOLS[0], "--index-bridge"),
                           (HASH_TOOLS[1], "--rid-ctrl-bridge"),
                           (INDEX_TOOL, "--hash-bridge")):
            for args in ((flag,), (flag, "--target", "on")):
                with self.subTest(tool=tool.__name__, args=args):
                    board = MemoryUSB(tool, bridge_error=True)
                    code, report = invoke(tool, board, args)
                    self.assertEqual((code, report["state"], board.write_count),
                                     (1, "partial_bridge_unverified", 0))
                    self.assertTrue(any(s["step"] == "baseline" and s["outcome"] == "read"
                                        for s in report["steps"]))

    def test_usb_open_failure_still_emits_json(self):
        for tool in (*TOOLS, INDEX_READ):
            board = MemoryUSB(tool)
            with patch.object(board, "open", side_effect=USB.USBError("fixture")):
                code, report = invoke(tool, board)
            self.assertEqual(code, 1)
            self.assertEqual(report["error_type"], "USBError")

    def test_cleanup_failure_does_not_hide_report_or_skip_other_cleanup(self):
        for tool in (*TOOLS, INDEX_READ):
            board = MemoryUSB(tool)
            with patch.object(board, "releaseInterface", side_effect=USB.USBError("fixture")):
                code, report = invoke(tool, board)
            self.assertEqual(code, 1)
            self.assertEqual(report["cleanup_errors"][0]["stage"], "release_interface")
            self.assertTrue(board.handle_closed and board.context_closed)


class IndexBoundaryTests(unittest.TestCase):
    def test_count_mismatch_is_not_a_verified_table(self):
        for count in (1556, 1558):
            with self.assertRaises(RuntimeError):
                verify_table_identity(types.SimpleNamespace(crc=0x5F8B2AE1, count=count))

    def test_live_1558_count_stops_after_table_reply(self):
        for tool in (INDEX_TOOL, INDEX_READ):
            board = MemoryUSB(tool, table_count=1558)
            code, report = invoke(tool, board)
            self.assertEqual(code, 1)
            self.assertEqual([cmd for cmd, _ in board.sent], [0xE0])

    def test_table_mismatch_stops_before_info_read_or_write(self):
        for tool in (INDEX_TOOL, INDEX_READ):
            board = MemoryUSB(tool, table_ok=False)
            code, report = invoke(tool, board)
            self.assertEqual(code, 1)
            self.assertEqual([cmd for cmd, _ in board.sent], [0xE0])

    def test_corrupt_crc_and_request_echo_are_skipped(self):
        for tool in (INDEX_TOOL, INDEX_READ):
            board = MemoryUSB(tool, corrupt_first=True)
            code, report = invoke(tool, board)
            self.assertEqual(code, 0)

    def test_hash_bridge_sends_only_fixed_read_requests(self):
        board = MemoryUSB(INDEX_TOOL)
        code, report = invoke(INDEX_TOOL, board, ("--hash-bridge",))
        self.assertEqual(code, 0)
        self.assertEqual(board.sent[-2:], [(0xF7, bytes.fromhex("fe9209f8")),
                                         (0xF8, bytes.fromhex("fe9209f8"))])
        self.assertEqual(board.write_count, 0)

    def test_hash_bridge_value_disagreement_stops_before_write(self):
        board = MemoryUSB(INDEX_TOOL, bridge_value=b"\x01")
        code, report = invoke(INDEX_TOOL, board, ("--hash-bridge", "--target", "on"))
        self.assertEqual((code, report["state"], board.write_count),
                         (1, "partial_bridge_unverified", 0))

    def test_response_identity_crc_and_type_are_all_enforced(self):
        duml = INDEX_TOOL.load_duml_module()
        base = duml.build_packet(3, 10, 0x80, 3, 0xE0, bytes(12), 123)
        cases = []
        for offset in (3, len(base) - 1):
            changed = bytearray(base)
            changed[offset] ^= 1
            cases.append(bytes(changed))
        for sender, receiver, kind, command, sequence in (
            (4, 10, 0x80, 0xE0, 123), (3, 11, 0x80, 0xE0, 123),
            (3, 10, 0x40, 0xE0, 123), (3, 10, 0x83, 0xE0, 123),
            (3, 10, 0x80, 0xE1, 123), (3, 10, 0x80, 0xE0, 124),
        ):
            cases.append(duml.build_packet(sender, receiver, kind, 3, command, bytes(12), sequence))
        for frame in cases:
            with self.subTest(frame=frame):
                with self.assertRaises(RuntimeError):
                    validate_response(frame, duml=duml, sender=3, receiver=10,
                                      sequence=123, command=0xE0)

    def test_bridge_rejects_other_hash_and_write_before_io(self):
        session = object.__new__(INDEX_TOOL.IndexSession)
        session.protocol = INDEX_TOOL.load_protocol_module()
        for command, payload in ((0xF7, bytes(4)), (0xF9, bytes.fromhex("fe9209f800"))):
            with self.assertRaises(AssertionError):
                session.exchange(command, payload)


if __name__ == "__main__":
    unittest.main()
