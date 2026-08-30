"""Synthetic offline policy-selection, lifecycle, comparison and privacy tests."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

import rid_cloud_policy_audit as audit


def row(area="TEST-AREA", data="TEST-PAYLOAD", blocked=None):
    return {"country_code": area, "data": data, "block_device": blocked or []}


def namespace(*rows):
    return {audit.POLICY_KEY: json.dumps(list(rows))}


def cache(data="TEST-PAYLOAD", receiver_type=18, receiver_index=4):
    return {"receiver_type": receiver_type, "receiver_index": receiver_index, "data": data}


class SelectionTests(unittest.TestCase):
    def test_duplicate_area_and_default_use_first(self):
        ns = namespace(row(data="TEST-FIRST"), row(data="TEST-LATER"),
                       row("DEFAULT", "TEST-DEFAULT-FIRST"), row("DEFAULT", "TEST-DEFAULT-LATER"))
        selected = audit.audit_policy(ns, "TEST-AREA", 139, cache("TEST-FIRST"))
        self.assertTrue(selected["matches_selected_candidate"])
        self.assertEqual((selected["area_match_count"], selected["default_match_count"]), (2, 2))
        default = audit.audit_policy(ns, "TEST-OTHER", 139, cache("TEST-DEFAULT-FIRST"))
        self.assertEqual(default["selection"], "DEFAULT_AREA_MISSING")
        self.assertTrue(default["matches_selected_candidate"])

    def test_first_blocked_row_falls_back_without_checking_later_area(self):
        ns = namespace(row(blocked=[139]), row(data="TEST-LATER"),
                       row("DEFAULT", "TEST-FALLBACK", [139]))
        result = audit.audit_policy(ns, "TEST-AREA", 139, cache("TEST-FALLBACK"))
        self.assertEqual(result["selection"], "DEFAULT_PRODUCT_BLOCKED")
        self.assertTrue(result["selected_area_blocked"])
        self.assertTrue(result["matches_selected_candidate"])

    def test_block_list_is_product_type_membership(self):
        ns = namespace(row(blocked=[139]), row("DEFAULT", "TEST-FALLBACK"))
        self.assertEqual(audit.audit_policy(ns, "TEST-AREA", 138)["selection"], "AREA")
        self.assertEqual(audit.audit_policy(ns, "TEST-AREA", 139)["selection"], "DEFAULT_PRODUCT_BLOCKED")

    def test_area_and_default_are_case_sensitive(self):
        ns = namespace(row(), row("default", "TEST-LOWERCASE"))
        result = audit.audit_policy(ns, "test-area", 139, cache("TEST-LOWERCASE"))
        self.assertEqual(result["area_match_count"], 0)
        self.assertEqual(result["default_match_count"], 0)
        self.assertEqual(result["emission"], "FILTERED_EMPTY")
        self.assertFalse(result["matches_selected_candidate"])

    def test_selected_empty_is_filtered_without_falling_back(self):
        result = audit.audit_policy(namespace(row(data=""), row("DEFAULT", "TEST-FALLBACK")),
                                    "TEST-AREA", 139, cache("TEST-FALLBACK"))
        self.assertEqual(result["selection"], "AREA")
        self.assertEqual(result["emission"], "FILTERED_EMPTY")
        self.assertFalse(result["matches_selected_candidate"])

    def test_whitespace_payload_is_not_trimmed(self):
        result = audit.audit_policy(namespace(row(data=" ")), "TEST-AREA", 139, cache(" "))
        self.assertEqual(result["emission"], "EMIT")
        self.assertTrue(result["matches_selected_candidate"])

    def test_empty_valid_list_and_absent_default(self):
        result = audit.audit_policy(namespace(), "TEST-AREA", 139, cache(""))
        self.assertEqual(result["policy_state"], "VALID")
        self.assertEqual(result["row_count"], 0)
        self.assertEqual(result["emission"], "FILTERED_EMPTY")
        self.assertFalse(result["matches_selected_candidate"])


class LifecycleAndCacheTests(unittest.TestCase):
    def test_distinct_tracks_last_nonempty_string_within_one_lifecycle(self):
        session = audit.PolicyAuditSession()
        states = []
        for payload in ["TEST-A", "", "TEST-A", "TEST-B", "TEST-A"]:
            states.append(session.observe(namespace(row(data=payload)), "TEST-AREA", 139)["emission"])
        self.assertEqual(states, ["EMIT", "FILTERED_EMPTY", "SUPPRESSED_DUPLICATE", "EMIT", "EMIT"])
        session.reset()
        result = session.observe(namespace(row(data="TEST-A")), "TEST-AREA", 139)
        self.assertEqual((result["emission"], result["observation_count"], result["emission_count"]), ("EMIT", 1, 1))

    def test_distinct_is_string_based_even_if_area_or_product_changes(self):
        session = audit.PolicyAuditSession()
        ns = namespace(row(), row("TEST-OTHER"))
        self.assertEqual(session.observe(ns, "TEST-AREA", 139)["emission"], "EMIT")
        self.assertEqual(session.observe(ns, "TEST-OTHER", 138)["emission"], "SUPPRESSED_DUPLICATE")
        self.assertEqual(audit.PolicyAuditSession().observe(ns, "TEST-OTHER", 138)["emission"], "EMIT")

    def test_shared_cache_requires_exact_receiver_and_string(self):
        for supplied in [cache(receiver_type=4), cache(receiver_index=0), cache("TEST-OTHER-WRITER"), cache("TEST-PAYLOAD ")]:
            with self.subTest(supplied=supplied):
                self.assertFalse(audit.audit_policy(namespace(row()), "TEST-AREA", 139, supplied)["matches_selected_candidate"])
        result = audit.audit_policy(namespace(row()), "TEST-AREA", 139, cache())
        self.assertTrue(result["matches_selected_candidate"])
        self.assertNotIn("writer", result)
        self.assertNotIn("applied", result)

    def test_cache_missing_null_and_malformed_are_separate(self):
        for supplied, expected in [(audit.MISSING, "MISSING"), (None, "NULL"), ({}, "MALFORMED"),
                                   (cache(receiver_type=True), "MALFORMED"), (cache(data=None), "MALFORMED")]:
            result = audit.audit_policy(namespace(row()), "TEST-AREA", 139, supplied)
            self.assertEqual(result["cache_state"], expected)
            self.assertIsNone(result["matches_selected_candidate"])


class ValidationTests(unittest.TestCase):
    def test_missing_null_bad_json_are_distinct(self):
        cases = [(audit.MISSING, "NAMESPACE_MISSING"), (None, "NAMESPACE_NULL"), ([], "NAMESPACE_MALFORMED"),
                 ({}, "POLICY_MISSING"), ({audit.POLICY_KEY: None}, "POLICY_NULL"),
                 ({audit.POLICY_KEY: ""}, "POLICY_EMPTY_TEXT"), ({audit.POLICY_KEY: "null"}, "POLICY_JSON_NULL"),
                 ({audit.POLICY_KEY: "{"}, "BAD_JSON"), ({audit.POLICY_KEY: "{}"}, "POLICY_WRONG_TYPE")]
        for ns, expected in cases:
            with self.subTest(expected=expected):
                result = audit.audit_policy(ns, "TEST-AREA", 139, cache())
                self.assertEqual(result["policy_state"], expected)
                self.assertEqual(result["emission"], "UNAVAILABLE")
                self.assertIsNone(result["matches_selected_candidate"])

    def test_strict_entry_types_reject_gson_coercion_cases(self):
        invalid_rows = [None, {}, row(data=None), row(area=7), row(blocked=[True]),
                        row(blocked=[139.0]), row(blocked=["139"]), row(blocked=[1 << 63])]
        malformed = row()
        malformed["block_device"] = None
        invalid_rows.append(malformed)
        for item in invalid_rows:
            self.assertEqual(audit.audit_policy(namespace(item), "TEST-AREA", 139)["policy_state"], "INVALID_ENTRY")

    def test_duplicate_object_keys_and_non_json_constants_rejected(self):
        raw = '[{"country_code":"TEST-AREA","data":"TEST-A","data":"TEST-B","block_device":[]}]'
        self.assertEqual(audit.audit_policy({audit.POLICY_KEY: raw}, "TEST-AREA", 139)["policy_state"], "DUPLICATE_KEY")
        for constant in ["NaN", "Infinity", "-Infinity"]:
            self.assertEqual(audit.audit_policy({audit.POLICY_KEY: constant}, "TEST-AREA", 139)["policy_state"], "BAD_JSON")

    def test_limits_apply_to_bytes_rows_block_entries_depth_and_unicode(self):
        cases = [(namespace(row(), row()), audit.Limits(rows=1)),
                 (namespace(row(blocked=[1, 2])), audit.Limits(block_entries=1)),
                 (namespace(row()), audit.Limits(policy_bytes=4)),
                 ({audit.POLICY_KEY: "[" * 20 + "]" * 20}, audit.Limits(depth=8)),
                 (namespace(row(data="测试")), audit.Limits(text_bytes=5))]
        for ns, limits in cases:
            self.assertEqual(audit.audit_policy(ns, "TEST-AREA", 139, limits=limits)["policy_state"], "LIMIT_EXCEEDED")
        self.assertEqual(audit.audit_policy(namespace(row(data="\ud800")), "TEST-AREA", 139)["policy_state"], "BAD_UNICODE")

    def test_context_rejects_bool_null_missing_and_out_of_range(self):
        for area, product, expected in [(audit.MISSING, 139, "MISSING"), (None, 139, "NULL"),
                                        ("TEST-AREA", True, "MALFORMED"), ("TEST-AREA", 1 << 63, "MALFORMED")]:
            result = audit.audit_policy(namespace(row()), area, product)
            self.assertEqual(result["context_state"], expected)
            self.assertEqual(result["emission"], "UNAVAILABLE")

    def test_namespace_aggregate_bytes_nodes_and_cycles_are_bounded(self):
        ns = {"TEST-ONE": "X" * 40, "TEST-TWO": "Y" * 40}
        result = audit.audit_policy(ns, "TEST-AREA", 139, limits=audit.Limits(document_bytes=80))
        self.assertEqual(result["policy_state"], "LIMIT_EXCEEDED")
        result = audit.audit_policy(namespace(row()), "TEST-AREA", 139, limits=audit.Limits(nodes=3))
        self.assertEqual(result["policy_state"], "LIMIT_EXCEEDED")
        cyclic = {}
        cyclic["TEST-CYCLE"] = cyclic
        result = audit.audit_policy(cyclic, "TEST-AREA", 139, limits=audit.Limits(depth=4))
        self.assertEqual(result["policy_state"], "LIMIT_EXCEEDED")


class PossibleCandidateTests(unittest.TestCase):
    def test_duplicate_first_blocked_and_default_selection(self):
        ns = namespace(row(data="TEST-BLOCKED", blocked=[139]), row(data="TEST-LATER"),
                       row("TEST-OTHER", "TEST-OTHER-PAYLOAD"),
                       row("DEFAULT", "TEST-DEFAULT"), row("DEFAULT", "TEST-LATER-DEFAULT"))
        result = audit.audit_possible_candidates(ns, 139, cache("TEST-DEFAULT"))
        self.assertEqual(result["selected_actual_area"], "UNOBSERVED")
        self.assertEqual((result["row_count"], result["effective_row_count"], result["duplicate_row_count"]), (5, 3, 2))
        self.assertEqual(result["nonempty_candidate_count"], 2)
        self.assertTrue(result["matches_default_candidate"])
        self.assertEqual(result["matching_candidate_count"], 1)
        for unavailable in ["TEST-BLOCKED", "TEST-LATER", "TEST-LATER-DEFAULT"]:
            self.assertFalse(audit.audit_possible_candidates(ns, 139, cache(unavailable))["matches_any_possible_candidate"])

    def test_strings_form_set_not_row_count_and_empty_is_excluded(self):
        ns = namespace(row(data="TEST-SAME"), row("TEST-OTHER", "TEST-SAME"), row("DEFAULT", ""))
        result = audit.audit_possible_candidates(ns, 139, cache("TEST-SAME"))
        self.assertEqual(result["nonempty_candidate_count"], 1)
        self.assertEqual(result["matching_candidate_count"], 1)
        self.assertFalse(result["matches_default_candidate"])
        self.assertFalse(audit.audit_possible_candidates(ns, 139, cache(""))["matches_any_possible_candidate"])

    def test_wrong_receiver_and_bad_cache_do_not_become_candidate_match(self):
        ns = namespace(row())
        wrong = audit.audit_possible_candidates(ns, 139, cache(receiver_type=4))
        self.assertFalse(wrong["matches_any_possible_candidate"])
        self.assertEqual(wrong["matching_candidate_count"], 0)
        bad = audit.audit_possible_candidates(ns, 139, None)
        self.assertIsNone(bad["matching_candidate_count"])
        self.assertIsNone(bad["matches_any_possible_candidate"])

    def test_case_sensitive_country_dedup_and_default(self):
        ns = namespace(row("TEST-AREA", "TEST-UPPER"), row("test-area", "TEST-LOWER"),
                       row("default", "TEST-LOWER-DEFAULT"))
        result = audit.audit_possible_candidates(ns, 139, cache("TEST-LOWER-DEFAULT"))
        self.assertEqual(result["effective_row_count"], 3)
        self.assertEqual(result["default_row_count"], 0)
        self.assertTrue(result["matches_any_possible_candidate"])
        self.assertFalse(result["matches_default_candidate"])

    def test_unknown_area_does_not_claim_selected_candidate_or_emission(self):
        doc = {"namespace": namespace(row()), "product_type": 139, "cache": cache()}
        result = audit.audit_document(json.dumps(doc).encode())
        self.assertEqual(result["mode"], "POSSIBLE_CANDIDATES")
        self.assertEqual(result["selected_actual_area"], "UNOBSERVED")
        self.assertNotIn("matches_selected_candidate", result)
        self.assertNotIn("emission", result)
        self.assertNotIn("TEST-", json.dumps(result))
        doc["area"] = None
        self.assertEqual(audit.audit_document(json.dumps(doc).encode())["context_state"], "NULL")

    def test_missing_policy_or_product_remain_unavailable(self):
        self.assertEqual(audit.audit_possible_candidates({}, 139)["policy_state"], "POLICY_MISSING")
        result = audit.audit_possible_candidates(namespace(row()), cache=cache())
        self.assertEqual(result["context_state"], "MISSING")
        self.assertIsNone(result["matching_candidate_count"])


class PrivacyTests(unittest.TestCase):
    def test_summary_and_errors_never_include_sensitive_input(self):
        marker = "TEST-OPAQUE-PRIVATE-MARKER"
        ns = namespace(row("TEST-PRIVATE-AREA", marker, [139]), row("DEFAULT", marker))
        result = audit.audit_policy(ns, "TEST-PRIVATE-AREA", 139, cache(marker))
        text = json.dumps(result)
        for forbidden in [marker, "TEST-PRIVATE-AREA", "139", "country_and_device_type"]:
            self.assertNotIn(forbidden, text)
        result = audit.audit_document(("{\"" + marker + "\":").encode())
        self.assertNotIn(marker, json.dumps(result))
        self.assertEqual(result["input_state"], "BAD_JSON")

    def test_cli_prints_only_sanitized_summary(self):
        doc = {"namespace": namespace(row(data="TEST-PRIVATE-PAYLOAD")), "area": "TEST-AREA", "product_type": 139,
               "cache": cache("TEST-PRIVATE-PAYLOAD")}
        tool = Path(__file__).with_name("rid_cloud_policy_audit.py")
        completed = subprocess.run([sys.executable, str(tool), "-"], input=json.dumps(doc), text=True, capture_output=True)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, "")
        self.assertNotIn("TEST-PRIVATE-PAYLOAD", completed.stdout)
        self.assertNotIn("TEST-AREA", completed.stdout)
        self.assertTrue(json.loads(completed.stdout)["matches_selected_candidate"])

    def test_document_budget_and_bad_utf8_report_fixed_error_codes(self):
        self.assertEqual(audit.audit_document(b"x" * 20, limits=audit.Limits(document_bytes=10))["input_state"], "LIMIT_EXCEEDED")
        self.assertEqual(audit.audit_document(b"\xff")["input_state"], "BAD_UNICODE")

    def test_cli_malformed_cache_fails_without_printing_payload(self):
        doc = {"namespace": namespace(row()), "product_type": 139,
               "cache": {"data": "TEST-PRIVATE-MALFORMED"}}
        tool = Path(__file__).with_name("rid_cloud_policy_audit.py")
        completed = subprocess.run([sys.executable, str(tool), "-"], input=json.dumps(doc), text=True, capture_output=True)
        self.assertEqual(completed.returncode, 2)
        self.assertNotIn("TEST-PRIVATE-MALFORMED", completed.stdout + completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["cache_state"], "MALFORMED")


if __name__ == "__main__":
    unittest.main()
