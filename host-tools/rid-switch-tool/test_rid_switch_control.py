"""Offline tests for the bounded RID switch tool.

These tests import the control module with a fake ``usb1`` module, so no USB
device is opened and no packet is transmitted. They cover the pure value-width
helper and the fail-closed gate that refuses a write without a positive control
and baseline.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types
import unittest


HERE = pathlib.Path(__file__).resolve().parent

# The control module imports `usb1` at module scope.  Provide a stub so the
# module can be loaded without a live device.
fake_usb1 = types.ModuleType("usb1")


class USBError(Exception):
    pass


class USBErrorTimeout(USBError):
    pass


fake_usb1.USBError = USBError
fake_usb1.USBErrorTimeout = USBErrorTimeout
sys.modules["usb1"] = fake_usb1

spec = importlib.util.spec_from_file_location(
    "rid_switch_control_under_test", HERE / "rid_switch_control.py"
)
assert spec is not None and spec.loader is not None
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


class BuildTargetRawTests(unittest.TestCase):
    def test_preserves_width_for_on(self):
        self.assertEqual(control.build_target_raw(b"\x00", True), b"\x01")

    def test_preserves_width_for_off(self):
        self.assertEqual(control.build_target_raw(b"\x01", False), b"\x00")

    def test_multi_byte_write_encoding_is_not_admitted(self):
        for baseline in (b"\x01\x00\x00\x00", b"\x00\x00", b"\x00\x00\x80\x3f"):
            for target in (False, True):
                with self.subTest(baseline=baseline, target=target):
                    with self.assertRaises(ValueError):
                        control.build_target_raw(baseline, target)

    def test_empty_baseline_is_rejected(self):
        with self.assertRaises(ValueError):
            control.build_target_raw(b"", True)


class GateTests(unittest.TestCase):
    """The write gate is fail-closed: no positive control means no RID write."""

    def test_exchange_refuses_unlisted_command(self):
        session = object.__new__(control.FCSession)
        session.protocol = control.load_protocol_module()
        with self.assertRaises(AssertionError):
            control.FCSession.exchange(session, 0xFA, b"")

    def test_transport_config_is_fixed_allowlist(self):
        self.assertEqual(control.transport_config("aircraft")["pid"], 0x0020)
        self.assertEqual(control.transport_config("rc2")["pid"], 0x1021)
        with self.assertRaises(ValueError):
            control.transport_config("unknown")

    def test_positive_control_name_matches_its_hash(self):
        hash_module = control.load_hash_module()
        self.assertEqual(
            hash_module.dji_flyc_parameter_hash(control.POSITIVE_CONTROL_NAME),
            control.POSITIVE_CONTROL_HASH,
        )
        self.assertEqual(
            control.POSITIVE_CONTROL_NAME,
            "g_config.flying_limit.max_height_0",
        )

    def test_index_bridge_name_matches_its_hash(self):
        hash_module = control.load_hash_module()
        self.assertEqual(
            hash_module.dji_flyc_parameter_hash(control.INDEX_BRIDGE_NAME),
            control.INDEX_BRIDGE_HASH,
        )
        self.assertEqual(control.INDEX_BRIDGE_NAME, "EU_CE_enable_c0_rid_0")


if __name__ == "__main__":
    unittest.main()
