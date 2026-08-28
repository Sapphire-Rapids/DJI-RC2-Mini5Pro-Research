from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

import rid_param_protocol as protocol


BASE_DIR = Path(__file__).resolve().parent


def load_duml():
    path = BASE_DIR / "third-party" / "duml.py"
    spec = importlib.util.spec_from_file_location("rid_test_duml", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def f7_payload(
    name: str,
    *,
    status: int = 0,
    data_type: int = 2,
    size: int = 4,
    attribute: int = 3,
) -> bytes:
    return b"".join(
        (
            bytes((status,)),
            data_type.to_bytes(2, "little"),
            size.to_bytes(2, "little"),
            attribute.to_bytes(2, "little"),
            (0).to_bytes(4, "little"),
            (18).to_bytes(4, "little"),
            (1).to_bytes(4, "little"),
            name.encode("ascii") + b"\x00",
        )
    )


class MetadataTests(unittest.TestCase):
    def test_valid_integer_metadata(self):
        name = "ccc_broadcast_signal_quality_0"
        result = protocol.parse_f7_metadata(
            f7_payload(name), expected_name=name, semantic_kind="int"
        )
        self.assertEqual(result.size, 4)
        self.assertEqual(result.data_type, 2)

    def test_bool_key_may_use_integer_wire_type(self):
        name = "EU_CE_enable_c0_rid_0"
        result = protocol.parse_f7_metadata(
            f7_payload(name, data_type=0, size=1),
            expected_name=name,
            semantic_kind="bool",
        )
        self.assertEqual(result.size, 1)

    def test_bool_key_may_use_float_wire_type(self):
        name = "EU_CE_enable_c0_rid_0"
        result = protocol.parse_f7_metadata(
            f7_payload(name, data_type=8, size=4),
            expected_name=name,
            semantic_kind="bool",
        )
        value = protocol.parse_f8_value(
            (0xF80992FE).to_bytes(4, "little") + b"\x00\x00\x80\x3f",
            expected_hash=0xF80992FE,
            metadata=result,
            semantic_kind="bool",
        )
        self.assertIs(value.decoded, True)

    def test_wrong_name_fails_closed(self):
        with self.assertRaises(protocol.ParamProtocolError):
            protocol.parse_f7_metadata(
                f7_payload("another_parameter"),
                expected_name="ccc_broadcast_signal_quality_0",
                semantic_kind="int",
            )

    def test_nonzero_status_is_not_metadata(self):
        with self.assertRaises(protocol.ParamStatusError):
            protocol.parse_f7_metadata(
                f7_payload("EU_CE_enable_c0_rid_0", status=2),
                expected_name="EU_CE_enable_c0_rid_0",
                semantic_kind="bool",
            )

    def test_status_only_error_is_reported(self):
        with self.assertRaises(protocol.ParamStatusError):
            protocol.parse_f7_metadata(
                b"\x02",
                expected_name="EU_CE_enable_c0_rid_0",
                semantic_kind="bool",
            )

    def test_missing_name_terminator_fails_closed(self):
        payload = f7_payload("ccc_broadcast_signal_quality_0").rstrip(b"\x00")
        with self.assertRaises(protocol.ParamProtocolError):
            protocol.parse_f7_metadata(
                payload,
                expected_name="ccc_broadcast_signal_quality_0",
                semantic_kind="int",
            )

    def test_type_size_mismatch_fails_closed(self):
        with self.assertRaises(protocol.ParamProtocolError):
            protocol.parse_f7_metadata(
                f7_payload("ccc_broadcast_signal_quality_0", size=2),
                expected_name="ccc_broadcast_signal_quality_0",
                semantic_kind="int",
            )


class ValueTests(unittest.TestCase):
    def setUp(self):
        self.name = "ccc_broadcast_signal_quality_0"
        self.metadata = protocol.parse_f7_metadata(
            f7_payload(self.name), expected_name=self.name, semantic_kind="int"
        )
        self.param_hash = 0xD7757AD2

    def test_status_hash_value_layout(self):
        payload = (
            b"\x00"
            + self.param_hash.to_bytes(4, "little")
            + (0x0312).to_bytes(4, "little")
        )
        result = protocol.parse_f8_value(
            payload,
            expected_hash=self.param_hash,
            metadata=self.metadata,
            semantic_kind="int",
        )
        self.assertEqual(result.layout, "status_hash_value")
        self.assertEqual(result.decoded, 0x0312)

    def test_hash_value_layout(self):
        payload = self.param_hash.to_bytes(4, "little") + (7).to_bytes(4, "little")
        result = protocol.parse_f8_value(
            payload,
            expected_hash=self.param_hash,
            metadata=self.metadata,
            semantic_kind="int",
        )
        self.assertEqual(result.layout, "hash_value")
        self.assertEqual(result.decoded, 7)

    def test_wrong_hash_fails_closed(self):
        payload = b"\x00" + (1).to_bytes(4, "little") + bytes(4)
        with self.assertRaises(protocol.ParamProtocolError):
            protocol.parse_f8_value(
                payload,
                expected_hash=self.param_hash,
                metadata=self.metadata,
                semantic_kind="int",
            )

    def test_status_only_error_is_reported(self):
        with self.assertRaises(protocol.ParamStatusError):
            protocol.parse_f8_value(
                b"\x03",
                expected_hash=self.param_hash,
                metadata=self.metadata,
                semantic_kind="int",
            )

    def test_extra_byte_fails_closed(self):
        payload = self.param_hash.to_bytes(4, "little") + bytes(5)
        with self.assertRaises(protocol.ParamProtocolError):
            protocol.parse_f8_value(
                payload,
                expected_hash=self.param_hash,
                metadata=self.metadata,
                semantic_kind="int",
            )

    def test_boolean_must_be_zero_or_one(self):
        name = "EU_CE_enable_c0_rid_0"
        metadata = protocol.parse_f7_metadata(
            f7_payload(name, data_type=0, size=1),
            expected_name=name,
            semantic_kind="bool",
        )
        payload = (0xF80992FE).to_bytes(4, "little") + b"\x02"
        with self.assertRaises(protocol.ParamProtocolError):
            protocol.parse_f8_value(
                payload,
                expected_hash=0xF80992FE,
                metadata=metadata,
                semantic_kind="bool",
            )


class FrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.duml = load_duml()

    def make_frame(self, **overrides):
        values = {
            "source": 0x03,
            "target": 0xAA,
            "cmd_type": 0x80,
            "cmd_set": 0x03,
            "cmd_id": 0xF7,
            "payload": b"metadata",
            "sequence": 0x1234,
        }
        values.update(overrides)
        return self.duml.build_packet(**values)

    def make_simple_response(self, *, cmd_type=0x80, **overrides):
        frame = bytearray(self.make_frame(cmd_type=cmd_type, **overrides))
        sequence = int.from_bytes(frame[6:8], "little")
        frame[9:-2] = protocol.simple_filter(bytes(frame[9:-2]), sequence)
        frame[8] |= 0x03
        checksum = self.duml.calc_crc16(frame, len(frame) - 2)
        frame[-2:] = checksum.to_bytes(2, "little")
        return bytes(frame)

    def validate(self, frame: bytes):
        return protocol.validate_response_frame(
            frame,
            duml=self.duml,
            expected_sender=0x03,
            expected_receiver=0xAA,
            expected_sequence=0x1234,
            expected_command_id=0xF7,
        )

    def test_validated_frame_returns_payload(self):
        self.assertEqual(self.validate(self.make_frame()), b"metadata")

    def test_crc_mutation_is_rejected(self):
        frame = bytearray(self.make_frame())
        frame[11] ^= 1
        with self.assertRaises(protocol.ParamProtocolError):
            self.validate(bytes(frame))

    def test_wrong_route_is_rejected(self):
        with self.assertRaises(protocol.ParamProtocolError):
            self.validate(self.make_frame(target=0x0A))

    def test_wrong_sequence_is_rejected(self):
        with self.assertRaises(protocol.ParamProtocolError):
            self.validate(self.make_frame(sequence=0x1235))

    def test_wrong_response_type_is_rejected(self):
        with self.assertRaises(protocol.ParamProtocolError):
            self.validate(self.make_frame(cmd_type=0x40))

    def test_simple_filter_matches_recovered_vector_and_is_self_inverse(self):
        plaintext = bytes.fromhex("03f978563412f401")
        encrypted = bytes.fromhex("4bca4d7e7c52b222")
        self.assertEqual(protocol.simple_filter(plaintext, 7), encrypted)
        self.assertEqual(protocol.simple_filter(encrypted, 7), plaintext)

    def test_simple_encrypted_response_is_validated_after_decryption(self):
        self.assertEqual(
            self.validate(self.make_simple_response()),
            b"metadata",
        )

    def test_simple_encrypted_ack_response_variant_is_accepted(self):
        self.assertEqual(
            self.validate(self.make_simple_response(cmd_type=0xC0)),
            b"metadata",
        )

    def test_unknown_encryption_type_is_rejected(self):
        frame = bytearray(self.make_frame(cmd_type=0x81))
        checksum = self.duml.calc_crc16(frame, len(frame) - 2)
        frame[-2:] = checksum.to_bytes(2, "little")
        with self.assertRaises(protocol.ParamProtocolError):
            self.validate(bytes(frame))

    def test_read_request_can_be_simple_encrypted(self):
        frame = self.duml.build_packet(
            source=0xAA,
            target=0x03,
            cmd_type=0x40,
            cmd_set=0x03,
            cmd_id=0xF7,
            payload=(0xD7757AD2).to_bytes(4, "little"),
            sequence=0x1234,
        )
        encrypted = protocol.encrypt_read_request_frame(frame, duml=self.duml)
        self.assertEqual(encrypted[8], 0x43)
        self.assertEqual(
            self.duml.calc_crc16(encrypted, len(encrypted) - 2),
            int.from_bytes(encrypted[-2:], "little"),
        )
        self.assertEqual(
            protocol.simple_filter(encrypted[9:-2], 0x1234),
            frame[9:-2],
        )

    def test_simple_packet_helper_refuses_write_command(self):
        frame = self.duml.build_packet(
            source=0xAA,
            target=0x03,
            cmd_type=0x40,
            cmd_set=0x03,
            cmd_id=0xF9,
            payload=(0xD7757AD2).to_bytes(4, "little") + bytes(4),
            sequence=0x1234,
        )
        with self.assertRaises(protocol.ParamProtocolError):
            protocol.encrypt_read_request_frame(frame, duml=self.duml)


class SafetyBoundaryTests(unittest.TestCase):
    def test_only_f7_and_f8_are_reachable_protocol_commands(self):
        self.assertEqual(protocol.READ_ONLY_COMMANDS, frozenset({0xF7, 0xF8}))

    def test_strict_probe_contains_no_write_or_reset_command_constants(self):
        source = (BASE_DIR / "rid_policy_params_readonly.py").read_text("utf-8")
        self.assertNotIn("CMD_SET_PARAM", source)
        self.assertNotIn("CMD_RESET_PARAM", source)
        self.assertNotIn("0xF9", source)
        self.assertNotIn("0xFA", source)


if __name__ == "__main__":
    unittest.main()
