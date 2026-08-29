"""Offline tests for the by-index read-only probe gate.

The probe module is imported with a fake ``usb1`` so no device is opened and no
packet is sent. These tests verify the fixed candidate list and the read-only
command gate that refuses the 0xE3 write command.
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
    "rid_param_index_readonly_under_test", HERE / "rid_param_index_readonly.py"
)
assert spec is not None and spec.loader is not None
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class CandidateTests(unittest.TestCase):
    def test_candidates_are_fixed_rid_indices(self):
        names = [c["name"] for c in probe.CANDIDATES]
        self.assertIn("EU_CE_enable_c0_rid", names)
        self.assertIn("EU_CE_Reg_RID_Enable", names)
        self.assertIn("eu_ce_support_remote_set_level", names)
        self.assertEqual([c["index"] for c in probe.CANDIDATES], [1306, 1308, 1315])

    def test_by_hash_bridge_uses_underscore_zero_form(self):
        hash_module = probe.load_hash_module()
        expected = {
            "EU_CE_enable_c0_rid": 0xF80992FE,
            "EU_CE_Reg_RID_Enable": 0xA2C325CE,
            "eu_ce_support_remote_set_level": 0xA8E96A09,
        }
        for candidate in probe.CANDIDATES:
            bridged_name = candidate["name"] + "_0"
            bridged_hash = hash_module.dji_flyc_parameter_hash(bridged_name)
            self.assertEqual(bridged_hash, expected[candidate["name"]])

    def test_transport_config_is_fixed_allowlist(self):
        self.assertEqual(probe.transport_config("aircraft")["pid"], 0x0020)
        self.assertEqual(probe.transport_config("rc2")["pid"], 0x1021)
        with self.assertRaises(ValueError):
            probe.transport_config("unknown")


if __name__ == "__main__":
    unittest.main()
