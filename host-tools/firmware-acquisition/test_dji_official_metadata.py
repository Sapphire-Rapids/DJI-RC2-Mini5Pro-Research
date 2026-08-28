import hashlib
import struct
import unittest

import dji_official_metadata as subject


class MetadataClientTests(unittest.TestCase):
    def test_recovered_signature_orders_firmware_ends_in_token(self):
        secret = b"synthetic-test-secret"
        self.assertEqual(
            subject.signature_getallfile(secret, "wa150", "tok"),
            hashlib.md5(secret + b"wa150tok").hexdigest(),
        )
        self.assertEqual(
            subject.signature_download(secret, "wa150", "01.00.0600", "tok"),
            hashlib.md5(secret + b"wa15001.00.0600tok").hexdigest(),
        )
        # Final firmware-signature item is token, not account.
        self.assertEqual(
            subject.signature_firmware_evidence_only(
                secret, "wa150", "01.00.0600", "0100", "02.03", "tok"
            ),
            hashlib.md5(secret + b"wa15001.00.0600010002.03tok").hexdigest(),
        )

    def test_module_body_path_is_blocked_before_network(self):
        client = subject.AllowlistedMetadataHttp()
        with self.assertRaises(subject.SafetyError):
            client.get(
                "/getfile/firmware",
                [],
                max_bytes=subject.MAX_CONFIG_BYTES,
            )

    def test_config_redirect_second_layer_allowlist(self):
        host, target, public_path = (
            subject.AllowlistedMetadataHttp._validated_config_redirect(
                "https://a.b.djicdn.com/release/wa150.pro.cfg.sig?opaque=1"
            )
        )
        self.assertEqual(host, "a.b.djicdn.com")
        self.assertEqual(target, "/release/wa150.pro.cfg.sig?opaque=1")
        self.assertEqual(public_path, "/release/wa150.pro.cfg.sig")

        refused = (
            "http://a.djicdn.com/release/wa150.pro.cfg.sig",
            "https://djicdn.com/release/wa150.pro.cfg.sig",
            "https://a.djicdn.com.evil.example/release/wa150.pro.cfg.sig",
            "https://a.djicdn.com/release/wa150.pro.fw.sig",
            "https://a.djicdn.com/release/%2e%2e/wa150.pro.cfg.sig",
            "https://user@a.djicdn.com/release/wa150.pro.cfg.sig",
            "https://a.djicdn.com:444/release/wa150.pro.cfg.sig",
            "https://a.djicdn.com:invalid/release/wa150.pro.cfg.sig",
            "https://a.djicdn.com/release/wa150.pro.cfg.sig#fragment",
        )
        for location in refused:
            with self.subTest(location=location):
                with self.assertRaises(subject.SafetyError):
                    subject.AllowlistedMetadataHttp._validated_config_redirect(location)

    def test_imah_payload_bounds(self):
        xml = (
            b'<root><module id="0100" version="1.2" size="3" '
            b'md5="900150983cd24fb0d6963f7d28e17f72">m.bin</module></root>'
        )
        header_size = 0xD0
        signature_size = 16
        payload_size = len(xml)
        body = bytearray(header_size + signature_size + payload_size)
        body[:4] = b"IM*H"
        struct.pack_into("<I", body, 8, len(body))
        struct.pack_into("<III", body, 0x10, header_size, signature_size, payload_size)
        struct.pack_into("<I", body, 0xC8, payload_size)
        body[header_size + signature_size :] = xml
        recovered, kind = subject._extract_config_xml(bytes(body))
        self.assertEqual(kind, "imah")
        self.assertEqual(recovered, xml)

    def test_xml_summary(self):
        xml = (
            b'<root><module id="0100" version="1.2" size="3" '
            b'md5="900150983cd24fb0d6963f7d28e17f72" group="ac">m.bin</module></root>'
        )
        summary = subject.summarize_config(xml, "01.00.0600", "xml")
        self.assertEqual(summary["module_count"], 1)
        self.assertEqual(summary["modules"][0]["filename"], "m.bin")


if __name__ == "__main__":
    unittest.main()
