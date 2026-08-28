import importlib.util
import pathlib
import struct
import unittest


MODULE_PATH = pathlib.Path(__file__).with_name("rc2_adb_handshake_probe.py")
SPEC = importlib.util.spec_from_file_location("probe", MODULE_PATH)
probe = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(probe)


class PacketTests(unittest.TestCase):
    def test_known_rc331_usb_compositions_are_explicit(self):
        self.assertEqual(
            probe.USB_TARGETS,
            {(0x2CA3, 0x1021), (0x18D1, 0x4EE2), (0x05C6, 0x901D)},
        )

    def test_drmuh_cnxn_vector(self):
        header = probe.packet_header(probe.A_CNXN, probe.VERSION, probe.MAXDATA, probe.BANNER)
        fields = struct.unpack("<6I", header)
        self.assertEqual(fields[0], probe.A_CNXN)
        self.assertEqual(fields[1], 0x01000000)
        self.assertEqual(fields[2], 256 * 1024)
        self.assertEqual(fields[3], len(b"host::pydevice\0"))
        self.assertEqual(fields[4], sum(b"host::pydevice\0"))
        self.assertEqual(fields[5], probe.A_CNXN ^ 0xFFFFFFFF)

    def test_public_key_auth_vector(self):
        payload = b"public-key\0"
        fields = struct.unpack(
            "<6I",
            probe.packet_header(probe.A_AUTH, probe.AUTH_RSAPUBLICKEY, 0, payload),
        )
        self.assertEqual(fields[1], probe.AUTH_RSAPUBLICKEY)
        self.assertEqual(fields[2], 0)
        self.assertEqual(fields[3], len(payload))

    def test_zero_checksum_is_an_explicit_variant(self):
        fields = struct.unpack(
            "<6I",
            probe.packet_header(
                probe.A_CNXN,
                probe.VERSION,
                probe.MAXDATA,
                probe.BANNER,
                checksum_mode="zero",
            ),
        )
        self.assertEqual(fields[4], 0)

    def test_command_names_cover_requested_trace_types(self):
        self.assertEqual(
            {probe.COMMAND_NAMES[value] for value in probe.COMMAND_NAMES},
            {"CNXN", "AUTH", "OPEN", "OKAY", "WRTE", "CLSE"},
        )


if __name__ == "__main__":
    unittest.main()
