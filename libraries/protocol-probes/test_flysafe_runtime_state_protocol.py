from __future__ import annotations

from pathlib import Path
import unittest

import flysafe_runtime_state_protocol as protocol
import flysafe_runtime_state_listener as listener


BASE_DIR = Path(__file__).resolve().parent


def area_payload(raw_version: int) -> bytes:
    payload = bytearray(8)
    payload[3:5] = (raw_version << 14).to_bytes(2, "little")
    return bytes(payload)


class AreaVersionTests(unittest.TestCase):
    def test_all_two_bit_values(self):
        self.assertEqual(protocol.decode_area_unlock_version(area_payload(0)), 0)
        self.assertEqual(protocol.decode_area_unlock_version(area_payload(1)), 1)
        self.assertEqual(protocol.decode_area_unlock_version(area_payload(2)), 2)
        self.assertEqual(protocol.decode_area_unlock_version(area_payload(3)), 255)

    def test_short_payload_fails_closed(self):
        for length in range(8):
            with self.subTest(length=length):
                with self.assertRaises(protocol.FlySafeStateError):
                    protocol.decode_area_unlock_version(bytes(length))


class WhiteListSupportTests(unittest.TestCase):
    def test_version_byte_encoding(self):
        self.assertTrue(protocol.decode_whitelist_support(bytes((10,))).supported)
        self.assertTrue(protocol.decode_whitelist_support(bytes((254,))).supported)
        result = protocol.decode_whitelist_support(bytes((255,)))
        self.assertTrue(result.usable)
        self.assertFalse(result.supported)
        self.assertEqual(result.encoding, "version_byte")

    def test_legacy_flag_encoding(self):
        payload = bytearray(28)
        payload[0] = 9
        payload[3] = 1
        result = protocol.decode_whitelist_support(bytes(payload))
        self.assertTrue(result.usable)
        self.assertTrue(result.supported)
        payload[3] = 0
        self.assertFalse(protocol.decode_whitelist_support(bytes(payload)).supported)

    def test_short_legacy_form_does_not_become_false(self):
        result = protocol.decode_whitelist_support(bytes((9, 0, 0, 0)))
        self.assertFalse(result.usable)
        self.assertIsNone(result.supported)

    def test_empty_payload_fails_closed(self):
        with self.assertRaises(protocol.FlySafeStateError):
            protocol.decode_whitelist_support(b"")


class ReceiverTests(unittest.TestCase):
    def test_mini_5_pro_route(self):
        self.assertEqual(
            protocol.select_inventory_receiver(unlock_version=0, product=139),
            0x92,
        )
        self.assertEqual(
            protocol.select_inventory_receiver(unlock_version=1, product=139),
            0x92,
        )
        self.assertEqual(
            protocol.select_inventory_receiver(unlock_version=2, product=139),
            0x92,
        )

    def test_only_proven_retain_products_keep_version_session_receiver(self):
        for version, expected in ((0, 0x03), (1, 0x03), (2, 0xB1)):
            for product in protocol.PRODUCTS_RETAINING_VERSION_SESSION_RECEIVER:
                with self.subTest(version=version, product=product):
                    self.assertEqual(
                        protocol.select_inventory_receiver(
                            unlock_version=version, product=product
                        ),
                        expected,
                    )

    def test_tree_miss_and_override_products_use_0x92(self):
        for product in (1, 77, 103, 120, 126, 137, 139, 152, 182, 185):
            for version in (0, 1, 2):
                with self.subTest(product=product, version=version):
                    self.assertEqual(
                        protocol.select_inventory_receiver(
                            unlock_version=version, product=product
                        ),
                        0x92,
                    )

    def test_unknown_version_fails_closed(self):
        for version in (-1, 3, 255):
            with self.subTest(version=version):
                with self.assertRaises(protocol.FlySafeStateError):
                    protocol.select_inventory_receiver(
                        unlock_version=version, product=139
                    )


class ListenerSafetyTests(unittest.TestCase):
    def test_all_configured_sources_use_input_endpoints(self):
        self.assertEqual(set(listener.SOURCES), {"aircraft", "rc2"})
        for spec in listener.SOURCES.values():
            self.assertEqual(spec.endpoint_in & 0x80, 0x80)

    def test_listener_contains_no_write_or_send_call(self):
        source = (BASE_DIR / "flysafe_runtime_state_listener.py").read_text()
        for forbidden in (
            "bulk" + "Write",
            "control" + "Write",
            "interrupt" + "Write",
            "send" + "_data",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
