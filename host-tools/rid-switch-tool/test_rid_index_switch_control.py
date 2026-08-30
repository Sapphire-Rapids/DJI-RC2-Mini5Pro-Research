"""Offline tests for the bounded by-index RID switch tool.

The control module is imported with a fake ``usb1`` so no device is opened and
no packet is sent. These tests pin the single fixed parameter target (index,
name, table identity) and verify the fail-closed command gate and transport
allow-list.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types
import unittest


HERE = pathlib.Path(__file__).resolve().parent

fake_usb1 = types.ModuleType("usb1")


class USBError(Exception):
    pass


class USBErrorTimeout(USBError):
    pass


fake_usb1.USBError = USBError
fake_usb1.USBErrorTimeout = USBErrorTimeout
sys.modules["usb1"] = fake_usb1

spec = importlib.util.spec_from_file_location(
    "rid_index_switch_control_under_test", HERE / "rid_index_switch_control.py"
)
assert spec is not None and spec.loader is not None
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


class TargetTests(unittest.TestCase):
    def test_single_fixed_parameter(self):
        self.assertEqual(control.RID_INDEX, 1306)
        self.assertEqual(control.RID_NAME, "EU_CE_enable_c0_rid")

    def test_wa150_table_identity_constants(self):
        self.assertEqual(control.WA150_TABLE_CRC, 0x5F8B2AE1)
        self.assertEqual(control.WA150_TABLE_COUNT, 1557)

    def test_hash_bridge_name_matches_its_hash(self):
        hash_module = control.load_hash_module()
        self.assertEqual(
            hash_module.dji_flyc_parameter_hash(control.HASH_BRIDGE_NAME),
            control.HASH_BRIDGE_HASH,
        )
        self.assertEqual(control.HASH_BRIDGE_NAME, "EU_CE_enable_c0_rid_0")

    def test_transport_config_is_fixed_allowlist(self):
        self.assertEqual(control.transport_config("aircraft")["pid"], 0x0020)
        self.assertEqual(control.transport_config("rc2")["pid"], 0x1021)
        with self.assertRaises(ValueError):
            control.transport_config("unknown")


class GateTests(unittest.TestCase):
    def test_exchange_refuses_unlisted_command(self):
        session = object.__new__(control.IndexSession)
        session.protocol = control.load_protocol_module()
        with self.assertRaises(AssertionError):
            control.IndexSession.exchange(session, 0xF9, b"")


if __name__ == "__main__":
    unittest.main()
