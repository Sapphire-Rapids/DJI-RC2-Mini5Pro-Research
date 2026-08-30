"""Cross-check native candidate summaries against the Python A054 profile."""

import ctypes
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parents[2] / "host-tools" / "rid-switch-tool"))
import rid_cloud_policy_audit as offline
from test_rid_cloud_policy_audit import row, namespace, cache


FIELDS = ("row_count", "effective_row_count", "duplicate_row_count", "default_row_count",
          "blocked_row_count", "nonempty_candidate_count", "matching_candidate_count",
          "default_match", "receiver_match")


class Summary(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int) for name in FIELDS]


class NativePythonAgreement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        library = Path(cls.temp.name) / "parser-library.so"
        mode = "-dynamiclib" if sys.platform == "darwin" else "-shared"
        subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-Oz", "-Wall", "-Wextra", "-Werror",
                        "-fPIC", mode, str(PROJECT / "src/native/cloud_policy_parser.c"), "-o", str(library)], check=True)
        cls.library = ctypes.CDLL(str(library))
        cls.audit = cls.library.cloud_policy_audit
        cls.audit.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int64,
                             ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int,
                             ctypes.c_int, ctypes.POINTER(Summary)]
        cls.audit.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def native(self, ns, product, cached, *, escape_outer=False):
        raw = json.dumps(ns, ensure_ascii=escape_outer, separators=(",", ":")).encode("utf-8")
        data = cached["data"].encode("utf-8") if cached is not None else None
        out = Summary()
        rc = self.audit(raw, len(raw), product, data, len(data) if data is not None else 0,
                        cached["receiver_type"] if cached is not None else 18,
                        cached["receiver_index"] if cached is not None else 4, ctypes.byref(out))
        return rc, {name: getattr(out, name) for name in FIELDS}

    def agreement(self, ns, product, cached, *, escape_outer=False):
        expected = offline.audit_possible_candidates(ns, product, cached, limits=offline.A054_LIMITS)
        self.assertEqual(expected["policy_state"], "VALID")
        rc, actual = self.native(ns, product, cached, escape_outer=escape_outer)
        self.assertEqual(rc, 0)
        for key in FIELDS:
            py_key = {"default_match": "matches_default_candidate", "receiver_match": "cache_receiver_matches"}.get(key, key)
            value = expected[py_key]
            self.assertEqual(actual[key], -1 if value is None else int(value), key)

    def test_shared_selection_fixtures(self):
        fixtures = [namespace(), namespace(row()),
                    namespace(row(data=""), row("DEFAULT", "TEST-FALLBACK")),
                    namespace(row(blocked=[139]), row(data="TEST-LATER"), row("DEFAULT", "TEST-FALLBACK", [139])),
                    namespace(row(), row("TEST-OTHER"), row("DEFAULT", "")),
                    namespace(row("TEST-AREA", "TEST-UPPER"), row("test-area", "TEST-LOWER"), row("default", "TEST-LOWER-DEFAULT")),
                    namespace(row(data="TEST-FIRST"), row(data="TEST-LATER"), row("DEFAULT", "TEST-DEFAULT-FIRST"), row("DEFAULT", "TEST-DEFAULT-LATER"))]
        for ns in fixtures:
            for cached in [cache(), cache(""), cache("TEST-FALLBACK"), cache(receiver_type=4), None]:
                self.agreement(ns, 139, cached)

    def test_utf8_escaped_unicode_and_duplicate_decoded_strings(self):
        policies = [row("TEST-中", "TEST-🚀\nA"), row("TEST-中", "TEST-LATER"), row("DEFAULT", "TEST-é")]
        policies[0]["explanation"] = {"说明": ["Unicode", True, None, 1.5]}
        for escape_inner in [False, True]:
            ns = {offline.POLICY_KEY: json.dumps(policies, ensure_ascii=escape_inner)}
            for escape_outer in [False, True]:
                self.agreement(ns, 139, cache("TEST-🚀\nA"), escape_outer=escape_outer)
                self.agreement(ns, 139, cache("TEST-é"), escape_outer=escape_outer)

    def test_generated_candidate_sets(self):
        rng = random.Random(54)
        for _ in range(384):
            rows = [row(rng.choice(["TEST-A", "TEST-B", "test-a", "TEST-中", "DEFAULT"]),
                        rng.choice(["TEST-1", "TEST-2", "", " ", "TEST-🚀", 'TEST-"\\\n']),
                        rng.choice([[], [139], [138], [138, 139]])) for _ in range(rng.randrange(17))]
            self.agreement(namespace(*rows), rng.choice([138, 139]),
                           cache(rng.choice(["TEST-1", "TEST-2", "", " ", "TEST-🚀"]),
                                 receiver_type=rng.choice([18, 4]), receiver_index=rng.choice([4, 0])))

    def test_resource_profile_agrees_on_rejections(self):
        deep = 0
        for _ in range(14): deep = [deep]
        extended = row()
        extended["unknown"] = deep
        wide = row()
        wide.update({f"TEST-{i}": 0 for i in range(65)})
        fixtures = [namespace(*(row() for _ in range(257))), namespace(row(blocked=[139] * 4097)),
                    namespace(extended), namespace(wide), namespace(row(data="\0"))]
        for ns in fixtures:
            expected = offline.audit_possible_candidates(ns, 139, cache(), limits=offline.A054_LIMITS)
            self.assertNotEqual(expected["policy_state"], "VALID")
            rc, actual = self.native(ns, 139, cache())
            self.assertNotEqual(rc, 0)
            self.assertTrue(all(value == -1 for value in actual.values()))


if __name__ == "__main__":
    unittest.main()
