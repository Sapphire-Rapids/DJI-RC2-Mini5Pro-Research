from __future__ import annotations

import inspect
from pathlib import Path
import unittest

import flysafe_license_inventory_readonly as probe
import flysafe_license_protocol as protocol


BASE_DIR = Path(__file__).resolve().parent


def record_payload(
    *,
    total: int = 1,
    enabled: int = 1,
    valid_status: int = 0,
    type_code: int = 0,
    level: int = 2,
) -> bytes:
    payload = bytearray(protocol.RESPONSE_RECORD_LENGTH)
    payload[0] = protocol.RESULT_RECORD
    payload[1] = total
    payload[2] = enabled
    payload[3] = valid_status
    payload[4:24] = b"private-text".ljust(20, b"_")
    payload[24:32] = bytes.fromhex("1122334455667788")
    payload[32:34] = bytes.fromhex("99aa")
    payload[34] = type_code
    payload[35] = level
    payload[36:40] = bytes.fromhex("efbeadde")
    payload[40:80] = bytes((index ^ 0xA5 for index in range(40)))
    return bytes(payload)


def build_response_frame(
    payload: bytes,
    *,
    receiver: int = protocol.SOURCE_DIRECT_AIRCRAFT,
    sender: int = protocol.TARGET_FLIGHT_CONTROLLER,
    sequence: int = 0x1234,
    command_type: int = protocol.CMD_TYPE_RESPONSE,
    command_set: int = protocol.CMD_SET_ADSB_WHITELIST,
    command_id: int = protocol.CMD_REQUEST_LICENSE,
    version: int = protocol.DUML_PROTOCOL_VERSION,
) -> bytes:
    length = protocol.DUML_MIN_LENGTH + len(payload)
    frame = bytearray(
        (
            protocol.DUML_SOF,
            length & 0xFF,
            ((length >> 8) & 0x03) | (version << 2),
        )
    )
    frame.append(protocol.calc_crc8(bytes(frame)))
    frame.extend((sender, receiver))
    frame.extend(sequence.to_bytes(2, "little"))
    frame.extend((command_type, command_set, command_id))
    frame.extend(payload)
    frame.extend(protocol.calc_crc16(bytes(frame)).to_bytes(2, "little"))
    return bytes(frame)


def summary(type_code=0, level=0, enabled=False, valid=False):
    return protocol.LicenseSummary(
        type_code=type_code, level=level, enabled=enabled, valid=valid
    )


class FixedRequestBuilderTests(unittest.TestCase):
    def test_direct_aircraft_request_is_fixed_command_with_one_byte_index(self):
        frame = protocol.build_license_request_frame(
            source=protocol.SOURCE_DIRECT_AIRCRAFT,
            request_id=7,
            sequence=0xBEEF,
        )
        self.assertEqual(len(frame), 14)
        self.assertEqual(
            frame[4:11], bytes.fromhex("0a03efbe401111")
        )
        self.assertEqual(frame[11:-2], b"\x07")
        self.assertEqual(protocol.calc_crc8(frame[:3]), frame[3])
        self.assertEqual(
            protocol.calc_crc16(frame[:-2]),
            int.from_bytes(frame[-2:], "little"),
        )

    def test_rc2_proxy_route_changes_only_the_allow_listed_source(self):
        frame = protocol.build_license_request_frame(
            source=protocol.SOURCE_RC2_PROXY,
            request_id=19,
            sequence=1,
        )
        self.assertEqual(frame[4], protocol.SOURCE_RC2_PROXY)
        self.assertEqual(frame[5], protocol.TARGET_FLIGHT_CONTROLLER)
        self.assertEqual(frame[8:11], bytes.fromhex("401111"))
        self.assertEqual(frame[11:-2], b"\x13")

    def test_request_bounds_and_routes_fail_closed(self):
        cases = (
            dict(source=0x01, request_id=0, sequence=0),
            dict(source=protocol.SOURCE_DIRECT_AIRCRAFT, request_id=-1, sequence=0),
            dict(source=protocol.SOURCE_DIRECT_AIRCRAFT, request_id=21, sequence=0),
            dict(source=protocol.SOURCE_DIRECT_AIRCRAFT, request_id=0, sequence=-1),
            dict(source=protocol.SOURCE_DIRECT_AIRCRAFT, request_id=0, sequence=0x10000),
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaises(protocol.LicenseProtocolError):
                    protocol.build_license_request_frame(**arguments)

    def test_builder_has_no_command_parameter(self):
        parameters = inspect.signature(
            protocol.build_license_request_frame
        ).parameters
        self.assertEqual(set(parameters), {"source", "request_id", "sequence"})
        self.assertEqual(
            protocol.READ_ONLY_COMMANDS, frozenset({protocol.CMD_REQUEST_LICENSE})
        )


class ResponseParserTests(unittest.TestCase):
    def setUp(self):
        self.payload = record_payload(
            total=3,
            enabled=1,
            valid_status=0,
            type_code=3,
            level=9,
        )
        self.frame = build_response_frame(self.payload)

    def parse(self, frame=None):
        return protocol.parse_license_response_frame(
            self.frame if frame is None else frame,
            expected_source=protocol.SOURCE_DIRECT_AIRCRAFT,
            expected_sequence=0x1234,
        )

    def test_maps_only_approved_summary_fields(self):
        response = self.parse()
        self.assertEqual(response.total_count, 3)
        self.assertIsNotNone(response.license)
        assert response.license is not None
        self.assertEqual(response.license.type_name, "PARAMETER_CONFIGURATION")
        self.assertEqual(response.license.level, 9)
        self.assertTrue(response.license.enabled)
        self.assertTrue(response.license.valid)

        output = protocol.deidentified_inventory_summary(
            protocol.LicenseInventory(3, (response.license,))
        )
        rendered = repr(output).lower()
        for forbidden in (
            "private-text",
            "deadbeef",
            "description",
            "license_id",
            "licenseid",
            "start_time",
            "end_time",
            "frame_hex",
            "payload_hex",
            "serial",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_valid_nonzero_means_false_without_guessing_an_enum(self):
        response = self.parse(
            build_response_frame(record_payload(valid_status=7))
        )
        assert response.license is not None
        self.assertFalse(response.license.valid)

    def test_unknown_type_is_preserved_as_non_sensitive_type_state(self):
        response = self.parse(
            build_response_frame(record_payload(type_code=42))
        )
        assert response.license is not None
        self.assertEqual(response.license.type_name, "UNKNOWN(42)")

    def test_current_power_and_rid_unlock_type_names_are_known(self):
        for type_code, expected in ((5, "POWER_UNLOCK"), (6, "RID_UNLOCK")):
            with self.subTest(type_code=type_code):
                response = self.parse(
                    build_response_frame(record_payload(type_code=type_code))
                )
                assert response.license is not None
                self.assertEqual(response.license.type_name, expected)

    def test_end_marker_requires_only_the_proven_result_byte(self):
        response = self.parse(build_response_frame(b"\x01"))
        self.assertEqual(response.result, protocol.RESULT_END)
        self.assertEqual(response.total_count, 0)
        self.assertIsNone(response.license)
        for payload in (b"\x01\x00", b"\x01\x00\x00\x00"):
            with self.subTest(payload=payload):
                extended = self.parse(build_response_frame(payload))
                self.assertEqual(extended.result, protocol.RESULT_END)
                self.assertIsNone(extended.license)

    def test_record_requires_80_bytes_but_ignores_unknown_extension_tail(self):
        with self.assertRaisesRegex(
            protocol.LicenseProtocolError, "shorter than 80 bytes"
        ):
            self.parse(build_response_frame(self.payload[:-1]))
        extended = self.parse(build_response_frame(self.payload + b"private-tail"))
        assert extended.license is not None
        self.assertEqual(extended.license.type_name, "PARAMETER_CONFIGURATION")

    def test_error_status_uses_only_the_proven_result_byte(self):
        with self.assertRaises(protocol.LicenseStatusError):
            self.parse(build_response_frame(b"\x05"))
        with self.assertRaises(protocol.LicenseStatusError):
            self.parse(build_response_frame(b"\x05\x00"))

    def test_zero_total_record_and_non_boolean_enabled_are_rejected(self):
        for payload in (
            record_payload(total=0),
            record_payload(enabled=2),
        ):
            with self.subTest(payload=payload[:4]):
                with self.assertRaises(protocol.LicenseProtocolError):
                    self.parse(build_response_frame(payload))

    def test_route_sequence_type_and_command_are_strict(self):
        changes = (
            dict(sender=0x04),
            dict(receiver=protocol.SOURCE_RC2_PROXY),
            dict(sequence=0x1235),
            dict(command_type=0xC0),
            dict(command_type=0x83),
            dict(command_set=0x12),
            dict(command_id=0x10),
            dict(command_id=0x12),
        )
        for change in changes:
            with self.subTest(change=change):
                with self.assertRaises(protocol.LicenseProtocolError):
                    self.parse(build_response_frame(self.payload, **change))

    def test_version_header_crc_body_crc_and_length_are_strict(self):
        with self.assertRaisesRegex(protocol.LicenseProtocolError, "version"):
            self.parse(build_response_frame(self.payload, version=2))

        bad_header = bytearray(self.frame)
        bad_header[3] ^= 1
        with self.assertRaisesRegex(protocol.LicenseProtocolError, "header CRC"):
            self.parse(bytes(bad_header))

        bad_body = bytearray(self.frame)
        bad_body[-1] ^= 1
        with self.assertRaisesRegex(protocol.LicenseProtocolError, "body CRC"):
            self.parse(bytes(bad_body))

        bad_length = bytearray(self.frame)
        bad_length[1] -= 1
        with self.assertRaisesRegex(protocol.LicenseProtocolError, "length"):
            self.parse(bytes(bad_length))


class InventoryTraversalTests(unittest.TestCase):
    def test_index_zero_first_and_exact_reported_count(self):
        calls = []

        def fetch(request_id):
            calls.append(request_id)
            if request_id == 3:
                return protocol.LicenseResponse(1, 0, None)
            return protocol.LicenseResponse(
                result=0,
                total_count=3,
                license=summary(type_code=request_id, level=request_id),
            )

        inventory = protocol.collect_inventory(fetch)
        self.assertEqual(calls, [0, 1, 2, 3])
        self.assertEqual(inventory.count, 3)
        self.assertEqual(len(inventory.licenses), 3)
        self.assertFalse(inventory.truncated)

    def test_reported_count_is_hard_capped_at_twenty_requests(self):
        calls = []

        def fetch(request_id):
            calls.append(request_id)
            return protocol.LicenseResponse(
                result=0,
                total_count=25,
                license=summary(type_code=request_id),
            )

        inventory = protocol.collect_inventory(fetch)
        self.assertEqual(calls, list(range(20)))
        self.assertEqual(inventory.count, 25)
        self.assertEqual(len(inventory.licenses), 20)
        self.assertTrue(inventory.truncated)

    def test_twenty_records_use_request_twenty_only_as_end_marker(self):
        calls = []

        def fetch(request_id):
            calls.append(request_id)
            if request_id == 20:
                return protocol.LicenseResponse(1, 0, None)
            return protocol.LicenseResponse(0, 20, summary())

        inventory = protocol.collect_inventory(fetch)
        self.assertEqual(calls, list(range(21)))
        self.assertEqual(len(inventory.licenses), 20)
        self.assertFalse(inventory.truncated)

    def test_empty_inventory_uses_index_zero_end_marker(self):
        calls = []

        def fetch(request_id):
            calls.append(request_id)
            return protocol.LicenseResponse(1, 0, None)

        inventory = protocol.collect_inventory(fetch)
        self.assertEqual(calls, [0])
        self.assertEqual(inventory, protocol.LicenseInventory(0, ()))

    def test_total_change_or_early_end_fails_closed(self):
        for second in (
            protocol.LicenseResponse(0, 3, summary()),
            protocol.LicenseResponse(1, 0, None),
        ):
            with self.subTest(second=second):
                responses = iter(
                    (
                        protocol.LicenseResponse(0, 2, summary()),
                        second,
                    )
                )
                with self.assertRaises(protocol.LicenseProtocolError):
                    protocol.collect_inventory(lambda _: next(responses))


class ProbeSyntheticExchangeTests(unittest.TestCase):
    class FakeUSB:
        class USBErrorTimeout(Exception):
            pass

    class FakeHandle:
        def __init__(self, reply):
            self.reply = reply
            self.writes = []

        def bulkWrite(self, endpoint, data, timeout):
            self.writes.append((endpoint, bytes(data), timeout))
            return len(data)

        def bulkRead(self, endpoint, size, timeout):
            reply, self.reply = self.reply, b""
            return reply

    def test_exchange_transmits_only_fixed_request_and_accepts_fixture(self):
        sequence = 0x4567
        fixture = build_response_frame(
            record_payload(type_code=2, level=4),
            receiver=protocol.SOURCE_RC2_PROXY,
            sequence=sequence,
        )
        handle = self.FakeHandle(fixture)
        response = probe._exchange_license_record(
            handle=handle,
            usb1_module=self.FakeUSB,
            transport=probe.TRANSPORTS["rc2"],
            pending=bytearray(),
            request_id=0,
            sequence=sequence,
            reply_seconds=0.25,
        )
        self.assertEqual(len(handle.writes), 1)
        endpoint, request, timeout = handle.writes[0]
        self.assertEqual(endpoint, 0x01)
        self.assertEqual(timeout, 1000)
        self.assertEqual(request[8:12], bytes.fromhex("40111100"))
        assert response.license is not None
        self.assertEqual(response.license.type_name, "COUNTRY_UNLOCK")

    def test_probe_declares_only_two_expected_transports(self):
        self.assertEqual(set(probe.TRANSPORTS), {"aircraft", "rc2"})
        for transport in probe.TRANSPORTS.values():
            self.assertEqual(transport.endpoint_in & 0x80, 0x80)
            self.assertEqual(transport.endpoint_out & 0x80, 0)
            self.assertIn(transport.source, protocol.ALLOWED_SOURCES)

    def test_output_function_source_has_no_sensitive_field_access(self):
        source = inspect.getsource(protocol.deidentified_inventory_summary).lower()
        for forbidden in (
            "description",
            "license_id",
            "licenseid",
            "start_time",
            "end_time",
            "serial",
            "frame_hex",
            "payload_hex",
        ):
            self.assertNotIn(forbidden, source)

    def test_probe_never_names_mutating_command_builders(self):
        source = (
            BASE_DIR / "flysafe_license_inventory_readonly.py"
        ).read_text()
        for forbidden in (
            "SendWhiteList",
            "SetLicenseEnabled",
            "CMD_UPLOAD",
            "CMD_ENABLE",
            "CMD_DISABLE",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
