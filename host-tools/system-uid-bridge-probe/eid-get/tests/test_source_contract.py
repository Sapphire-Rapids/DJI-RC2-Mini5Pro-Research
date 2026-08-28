#!/usr/bin/env python3
from pathlib import Path
import re
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/main/java/com/finduas/bridge/FranceEidGetMain.java"
RUNNER = ROOT / "runner/run-france-eid-get-readonly.sh"
ARTIFACT = ROOT / "FindUAS-France-EID-GET-readonly.jar"


def compact_method(source: str, name: str) -> str:
    start = source.index(name)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return re.sub(r"\s+", " ", source[brace + 1:index]).strip()
    raise AssertionError(f"unterminated method {name}")


class SourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.runner = RUNNER.read_text(encoding="utf-8")

    def test_fixed_protocol_constants(self):
        expected = {
            "SENDER_TYPE": "0x02",
            "SENDER_ID": "0x04",
            "RECEIVER_TYPE": "0x12",
            "RECEIVER_ID": "0x04",
            "CMD_SET": "0x03",
            "CMD_ID": "0x77",
            "NEED_ACK_AFTER_EXEC": "2",
            "ENCRYPTION_NONE": "0",
            "TIMEOUT_MS": "500",
            "GET_OPERATION": "0x02",
            "TRANSACTION_SEND_WITH_LISTEN": "4",
        }
        for name, value in expected.items():
            self.assertRegex(
                self.source,
                rf"private static final (?:int|byte) {name} = {re.escape(value)};",
            )

    def test_exact_descriptors(self):
        self.assertIn('PROTOCOL_DESCRIPTOR = "com.dji.protocol.IProtocolManager"', self.source)
        self.assertIn('LISTENER_DESCRIPTOR = "com.dji.protocol.IPackListener"', self.source)
        self.assertIn('SERVICE_NAME = "protocol"', self.source)

    def test_only_one_outbound_binder_transaction(self):
        method = compact_method(self.source, "static int run(String[] args)")
        self.assertEqual(method.count(".transact("), 1)
        self.assertIn("TRANSACTION_SEND_WITH_LISTEN, request, reply, 0", method)
        self.assertNotIn("transact(3", self.source)

    def test_request_parcel_order_matches_adjacent_pack_abi(self):
        method = compact_method(self.source, "void writeHardCodedGetPack(Parcel parcel)")
        calls = re.findall(r"parcel\.write(?:Byte|Int|ByteArray)\((.*?)\);", method)
        self.assertEqual(
            calls,
            [
                "(byte) 0x55",
                "1",
                "0",
                "0",
                "SENDER_ID",
                "SENDER_TYPE",
                "RECEIVER_ID",
                "RECEIVER_TYPE",
                "-1",
                "CMD_TYPE_REQUEST",
                "NEED_ACK_AFTER_EXEC",
                "CMD_TYPE_REQUEST",
                "ENCRYPTION_NONE",
                "CMD_SET",
                "CMD_ID",
                "1",
                "new byte[]{GET_OPERATION}",
                "0",
                "0",
                "TIMEOUT_MS",
                "0",
            ],
        )

    def test_callback_codes_are_exact_and_closed(self):
        self.assertIn("CALLBACK_SUCCESS = 1", self.source)
        self.assertIn("CALLBACK_FAILURE = 2", self.source)
        callback = compact_method(self.source, "boolean onTransact(int code")
        self.assertIn("code == CALLBACK_SUCCESS", callback)
        self.assertIn("code == CALLBACK_FAILURE", callback)
        self.assertIn("super.onTransact(code, data, reply, flags)", callback)

    def test_ack_is_fail_closed(self):
        method = compact_method(self.source, "String validateAck(ParsedPack pack)")
        for token in (
            "pack.length != 15",
            "pack.senderType != RECEIVER_TYPE",
            "pack.receiverType != SENDER_TYPE",
            "pack.cmdType != CMD_TYPE_ACK",
            "pack.encryptType != ENCRYPTION_NONE",
            "pack.cmdSet != CMD_SET",
            "pack.cmdId != CMD_ID",
            "pack.ccode != 0",
            "pack.data.length != 1",
            "state != 0 && state != 1",
        ):
            self.assertIn(token, method)

    def test_no_generic_input_or_mutating_transport(self):
        forbidden = (
            "java.net.",
            "Socket",
            "OutputStream",
            "FileOutputStream",
            "RandomAccessFile",
            "ProcessBuilder",
            "Runtime.getRuntime",
            "startActivity",
            "setprop",
            "40007",
            "40009",
        )
        for token in forbidden:
            self.assertNotIn(token, self.source)
        self.assertIn("args.length != 0", self.source)
        self.assertNotIn("args[", self.source)

    def test_system_uid_gate_precedes_service_lookup(self):
        uid_gate = self.source.index("Process.myUid() != SYSTEM_UID")
        lookup = self.source.index("service = checkService(SERVICE_NAME)")
        transact = self.source.index("boolean dispatched = service.transact")
        self.assertLess(uid_gate, lookup)
        self.assertLess(lookup, transact)

    def test_runner_is_fixed_and_argument_free(self):
        self.assertIn('[ "$#" -ne 0 ]', self.runner)
        self.assertIn('[ "$(/system/bin/id -u)" != "1000" ]', self.runner)
        self.assertIn(
            "export CLASSPATH=/sdcard/Download/FindUAS-France-EID-GET-readonly.jar",
            self.runner,
        )
        self.assertIn(
            "exec /system/bin/app_process /system/bin com.finduas.bridge.FranceEidGetMain",
            self.runner,
        )
        self.assertNotIn('"$@"', self.runner)

    def test_artifact_is_dex_only(self):
        self.assertTrue(ARTIFACT.is_file(), "run build.sh first")
        with zipfile.ZipFile(ARTIFACT) as archive:
            self.assertEqual(archive.namelist(), ["classes.dex"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
