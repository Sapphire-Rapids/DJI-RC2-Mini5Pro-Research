import ctypes
import json
from pathlib import Path
import random
import subprocess
import tempfile
import unittest


class Summary(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int) for name in (
        "policy_rc", "row_count", "distinct_nonempty_count", "nonempty_row_count",
        "duplicate_country_row_count", "default_row_count", "first_default_present",
        "first_default_nonempty", "first_default_row_index", "blocked_row_count",
        "invalid_hex_row_index", "json_length")]


def row(country="TEST-A", data="AA", blocks=None, **unknown):
    return dict(country_code=country, data=data, block_device=[] if blocks is None else blocks, **unknown)


def namespace(rows, **extra):
    return json.dumps(dict(country_and_device_type=json.dumps(rows, ensure_ascii=False), **extra),
                      ensure_ascii=False).encode()


class GlobalPayloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="TEST-global-policy-")
        source = Path(__file__).resolve().parents[1] / "src/native/global_payload_extract.c"
        lib = Path(cls.temp.name) / "TEST-extractor.dylib"
        subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC", "-O1",
                        str(source), "-o", str(lib)], check=True, capture_output=True)
        cls.library = ctypes.CDLL(str(lib))
        cls.call = cls.library.global_payload_extract
        cls.call.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int64,
                             ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(Summary)]
        cls.call.restype = ctypes.c_int
        cls.free = ctypes.CDLL(None).free
        cls.free.argtypes = [ctypes.c_void_p]
        cls.free.restype = None

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def extract(self, raw, product=139, expected=0):
        output = ctypes.c_void_p(1)
        length = ctypes.c_size_t(999)
        summary = Summary()
        rc = self.call(raw, len(raw) if raw is not None else 0, product,
                       ctypes.byref(output), ctypes.byref(length), ctypes.byref(summary))
        self.assertEqual(rc, expected)
        if rc:
            self.assertIsNone(output.value)
            self.assertEqual(length.value, 0)
            self.assertEqual(summary.json_length, 0)
            return None, summary
        try:
            self.assertLessEqual(length.value, 32768)
            encoded = ctypes.string_at(output, length.value)
            self.assertEqual(ctypes.string_at(output, length.value + 1)[-1], 0)
            self.assertEqual(summary.json_length, length.value)
            parsed = json.loads(encoded)
            self.assertEqual(parsed["schema"], "finduas-rid-policy-set/v1")
            self.assertNotIn("country_and_device_type", parsed)
            self.assertEqual(set(parsed["rows"][0]) if parsed["rows"] else set(),
                             {"country_code", "data_hex", "blocked_for_product"} if parsed["rows"] else set())
            return parsed, summary
        finally: self.free(output)

    def test_order_duplicates_case_and_block_membership_retained(self):
        rows = [row("TEST-B", "aA", [139]), row("DEFAULT", "", [139]), row("TEST-B", "AA"),
                row("DEFAULT", "BB"), row("default", "aA"), row("TEST-C", "")]
        output, summary = self.extract(namespace(rows))
        self.assertEqual(output["rows"], [dict(country_code=r["country_code"], data_hex=r["data"],
                                             blocked_for_product=139 in r["block_device"]) for r in rows])
        self.assertEqual(summary.row_count, 6)
        self.assertEqual(summary.nonempty_row_count, 4)
        self.assertEqual(summary.distinct_nonempty_count, 3)
        self.assertEqual(summary.duplicate_country_row_count, 2)
        self.assertEqual(summary.blocked_row_count, 2)
        self.assertEqual(summary.default_row_count, 2)
        self.assertEqual(summary.first_default_present, 1)
        self.assertEqual(summary.first_default_nonempty, 0)
        self.assertEqual(summary.first_default_row_index, 1)

    def test_all_raw_rows_counted_including_blocked_and_later_duplicates(self):
        output, summary = self.extract(namespace([row("TEST-A", "AA", [139]), row("TEST-A", "BB"), row("TEST-B", "CC", [139])]))
        self.assertEqual(summary.distinct_nonempty_count, 3)
        self.assertEqual(len(output["rows"]), 3)
        self.assertEqual(summary.default_row_count, 0)
        self.assertEqual(summary.first_default_present, 0)
        self.assertEqual(summary.first_default_nonempty, 0)
        self.assertEqual(summary.first_default_row_index, -1)

    def test_unknown_fields_and_outer_names_never_exported(self):
        output, _ = self.extract(namespace([row("TEST-X", "Aa", ignored={"TEST-secret": ["TEST-PRIVATE", 123]})],
                                          **{"TEST-namespace": "TEST-OUTER-PRIVATE"}))
        encoded = json.dumps(output)
        for unknown in ("TEST-secret", "TEST-PRIVATE", "TEST-OUTER", "TEST-namespace", "ignored", "matched", "actual_area"):
            self.assertNotIn(unknown, encoded)
        self.assertEqual(output["rows"][0]["country_code"], "TEST-X")

    def test_unicode_controls_quotes_backslashes_and_surrogate_pairs(self):
        labels = ['TEST-"quote"\\path\n\t\b\f\r\x01', "TEST-中文😀", "TEST-é", "TEST-e\u0301", ""]
        rows = [row(label, "A0") for label in labels]
        for ascii_only in (False, True):
            raw = json.dumps({"country_and_device_type": json.dumps(rows, ensure_ascii=ascii_only)}, ensure_ascii=ascii_only).encode()
            output, summary = self.extract(raw)
            self.assertEqual([r["country_code"] for r in output["rows"]], labels)
            self.assertEqual(summary.duplicate_country_row_count, 0)

    def test_escape_decoding_applies_to_hex_before_validation(self):
        inner = '[{"country_code":"TEST-ESCAPED","data":"\\u0041\\u0061","block_device":[]}]'
        output, _ = self.extract(json.dumps({"country_and_device_type": inner}).encode())
        self.assertEqual(output["rows"][0]["data_hex"], "Aa")

    def test_missing_null_empty_namespace_states(self):
        cases = [(None, 1), (b"{}", 2), (b'{"country_and_device_type":null}', 3),
                 (b'{"country_and_device_type":"null"}', 4), (b'{"country_and_device_type":""}', 5)]
        for raw, policy_rc in cases:
            _, summary = self.extract(raw, expected=2)
            self.assertEqual(summary.policy_rc, policy_rc)
            self.assertEqual(summary.row_count, -1)
        _, summary = self.extract(namespace([]), product=-1, expected=5)
        self.assertEqual(summary.policy_rc, 9)

    def test_empty_array_and_empty_data_are_valid(self):
        output, summary = self.extract(namespace([]))
        self.assertEqual(output["rows"], [])
        self.assertEqual(summary.distinct_nonempty_count, 0)
        output, summary = self.extract(namespace([row("DEFAULT", "")]))
        self.assertEqual(output["rows"][0]["data_hex"], "")
        self.assertEqual(summary.first_default_present, 1)
        self.assertEqual(summary.first_default_nonempty, 0)

    def test_every_row_hex_validated_even_later_duplicate_or_blocked(self):
        for data in ("A", "GG", "AA BB ", "0x12", "ＡＡ", "AA\n", "AA\x01"):
            with self.subTest(data=data):
                _, summary = self.extract(namespace([row(), row("TEST-A", data, [139])]), expected=6)
                self.assertEqual(summary.invalid_hex_row_index, 1)
                self.assertEqual(summary.row_count, 2)
                self.assertEqual(summary.distinct_nonempty_count, -1)

    def test_per_row_hex_limit_exact_and_exceeded(self):
        output, _ = self.extract(namespace([row(data="AB" * 2048)]))
        self.assertEqual(len(output["rows"][0]["data_hex"]), 4096)
        _, summary = self.extract(namespace([row(data="AB" * 2049)]), expected=7)
        self.assertEqual(summary.invalid_hex_row_index, 0)

    def test_row_limit_and_block_list_limit(self):
        output, summary = self.extract(namespace([row(f"TEST-{i}", "") for i in range(256)]))
        self.assertEqual(len(output["rows"]), 256)
        self.assertEqual(summary.row_count, 256)
        self.extract(namespace([row(f"TEST-{i}", "") for i in range(257)]), expected=4)
        self.extract(namespace([row(blocks=[139] * 4097)]), expected=4)

    def test_output_limit_all_or_nothing_and_exact_boundary(self):
        # Nonempty data rows individually valid but the complete report is too large.
        self.extract(namespace([row(f"TEST-{i}", "AB" * 2048) for i in range(8)]), expected=8)
        initial, summary = self.extract(namespace([row("TEST-X", "AA")]))
        pad = 32768 - summary.json_length
        label = "TEST-X" + "X" * pad
        _, exact = self.extract(namespace([row(label, "AA")]))
        self.assertEqual(exact.json_length, 32768)
        self.extract(namespace([row(label + "X", "AA")]), expected=8)

    def test_namespace_limit_and_deep_unknown_fields(self):
        raw = namespace([row()])
        self.extract(raw + b" " * (65536 - len(raw)))
        self.extract(raw + b" " * (65537 - len(raw)), expected=4)
        nested = None
        for _ in range(13): nested = [nested]
        self.extract(namespace([row(unknown=nested)]), expected=4)

    def test_malformed_schema_duplicate_fields_and_unicode_rejected(self):
        bad_rows = [[{"country_code": "TEST-X", "data": "AA"}],
                    [row(blocks=[139.0])], [row(blocks=[True])], [row(data=None)], [row(country=None)]]
        for rows in bad_rows: self.extract(namespace(rows), expected=3)
        for inner in ('[{"country_code":"TEST-X","data":"AA","data":"BB","block_device":[]}]',
                      '[{"country_code":"TEST-X","data":"AA","block_device":[],"x":{"a":1,"a":2}}]',
                      '[{"country_code":"\\ud800","data":"AA","block_device":[]}]',
                      '[{"country_code":"TEST-\\u0000","data":"AA","block_device":[]}]'):
            self.extract(json.dumps({"country_and_device_type": inner}).encode(), expected=3)
        self.extract(namespace([row()]) + b"\xff", expected=3)

    def test_product_type_bounds_and_raw_membership(self):
        for product in (0, 65535):
            output, _ = self.extract(namespace([row(blocks=[product, -1, 139])]), product=product)
            self.assertTrue(output["rows"][0]["blocked_for_product"])
        self.extract(namespace([row()]), product=65536, expected=1)

    def test_random_valid_sets_agree_with_independent_python_expectation(self):
        rng = random.Random(6001)
        labels = ["TEST-A", "TEST-B", "TEST-中文😀", "DEFAULT", "default", ""]
        values = ["", "AA", "aa", "ABCD", "00", "Ff"]
        for _ in range(160):
            product = rng.choice([0, 139, 158])
            rows = [row(rng.choice(labels), rng.choice(values), rng.choice([[], [139], [158], [0, 139]]))
                    for _ in range(rng.randrange(0, 30))]
            output, summary = self.extract(namespace(rows), product)
            self.assertEqual(output["rows"], [dict(country_code=r["country_code"], data_hex=r["data"],
                                                 blocked_for_product=product in r["block_device"]) for r in rows])
            self.assertEqual(summary.distinct_nonempty_count, len({r["data"] for r in rows if r["data"]}))
            self.assertEqual(summary.duplicate_country_row_count, len(rows) - len({r["country_code"] for r in rows}))
            defaults = [i for i, r in enumerate(rows) if r["country_code"] == "DEFAULT"]
            self.assertEqual(summary.default_row_count, len(defaults))
            self.assertEqual(summary.first_default_row_index, defaults[0] if defaults else -1)


if __name__ == "__main__": unittest.main()
