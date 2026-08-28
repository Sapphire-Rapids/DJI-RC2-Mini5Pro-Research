from __future__ import annotations

import itertools
import unittest
from copy import deepcopy
from dataclasses import replace

from ridq.constants import FAILURE_CODES, INVARIANTS, PREFIX_CLASSES, STATES, FailureCode
from ridq.__main__ import _events
from ridq.fixtures import (
    CALLBACK_THREAD,
    CONNECTION_EPOCH,
    COORDINATOR_THREAD,
    REJECT_DESCRIPTIONS,
    WORKER_THREAD,
    minimal_accept_raw,
    minimal_accept_trace,
    raw,
    rejected_traces,
    seal_trace,
)
from ridq.model import QuiescenceVerifier, TraceEvent, verify_trace


def prefix_raw(event_type: str) -> list[dict]:
    items = minimal_accept_raw()
    index = next(i for i, item in enumerate(items) if item["event_type"] == event_type)
    return deepcopy(items[: index + 1])


class VocabularyTests(unittest.TestCase):
    def test_closed_tables(self) -> None:
        self.assertEqual(25, len(INVARIANTS))
        self.assertEqual(25, len(set(INVARIANTS)))
        self.assertEqual(21, len(STATES))
        self.assertEqual(51, len(FAILURE_CODES))
        self.assertEqual(0, int(FailureCode.Q_QUIESCENT_VALID_RESPONSE))
        self.assertEqual(
            ("ACTIVE", "QUIESCENT_REJECTED", "UNKNOWN_RETAINED"),
            PREFIX_CLASSES,
        )


class AcceptanceTests(unittest.TestCase):
    def test_minimal_trace_is_accepted_only_after_explicit_retention_decision(self) -> None:
        trace = minimal_accept_trace()
        verifier = QuiescenceVerifier()
        reports = [verifier.consume(event) for event in trace]
        self.assertTrue(reports[-1].accepted)
        self.assertEqual("Q_QUIESCENT_VALID_RESPONSE", reports[-1].primary_name)
        self.assertEqual("PROVEN", reports[-1].quiescence)
        self.assertEqual("RELEASED_AFTER_DRAIN", reports[-1].retention)
        self.assertTrue(all(not report.accepted for report in reports[:-1]))
        self.assertTrue(all(report.classification in PREFIX_CLASSES for report in reports))

    def test_no_event_means_no_new_evidence(self) -> None:
        trace = minimal_accept_trace()[:20]
        verifier = QuiescenceVerifier()
        for event in trace:
            verifier.consume(event)
        before = verifier.report()
        after = verifier.report()
        self.assertEqual(before, after)
        self.assertFalse(after.accepted)
        self.assertEqual("NOT_STARTED", after.quiescence)

    def test_all_24_required_interleavings_are_rejected(self) -> None:
        traces = rejected_traces()
        self.assertEqual(24, len(traces))
        self.assertEqual(24, len(REJECT_DESCRIPTIONS))
        for index, trace in enumerate(traces, start=1):
            with self.subTest(index=index, description=REJECT_DESCRIPTIONS[index - 1]):
                report = verify_trace(trace)
                self.assertFalse(report.accepted)
                self.assertIn(report.classification, PREFIX_CLASSES)

    def test_every_prefix_of_all_fixed_traces_has_closed_classification(self) -> None:
        for trace in [minimal_accept_trace(), *rejected_traces()]:
            verifier = QuiescenceVerifier()
            for event in trace:
                report = verifier.consume(event)
                self.assertIn(report.classification, PREFIX_CLASSES)

    def test_deleting_any_success_witness_never_accepts(self) -> None:
        source = minimal_accept_raw()
        self.assertGreaterEqual(len(source), 20)
        for index, event in enumerate(source):
            with self.subTest(index=index, event_type=event["event_type"]):
                mutation = deepcopy(source)
                del mutation[index]
                self.assertFalse(verify_trace(seal_trace(mutation)).accepted)


class InterleavingPropertyTests(unittest.TestCase):
    def test_registration_witness_permutations_remain_safe(self) -> None:
        source = minimal_accept_raw()
        positions = [7, 8, 9]
        witnesses = [deepcopy(source[index]) for index in positions]
        accepted = 0
        for permutation in itertools.permutations(witnesses):
            mutation = deepcopy(source)
            mutation[7:10] = list(permutation)
            report = verify_trace(seal_trace(mutation))
            self.assertIn(report.classification, PREFIX_CLASSES)
            accepted += int(report.accepted)
        self.assertEqual(6, accepted)

    def test_response_drain_permutations_have_one_valid_order(self) -> None:
        source = minimal_accept_raw()
        positions = [15, 16, 17, 18]
        witnesses = [deepcopy(source[index]) for index in positions]
        accepted = 0
        for permutation in itertools.permutations(witnesses):
            mutation = deepcopy(source)
            mutation[15:19] = list(permutation)
            report = verify_trace(seal_trace(mutation))
            self.assertIn(report.classification, PREFIX_CLASSES)
            accepted += int(report.accepted)
        self.assertEqual(1, accepted)

    def test_sdk_admission_before_registration_complete_is_never_accepted(self) -> None:
        source = minimal_accept_raw()
        admission = source.pop(12)
        source.insert(10, admission)
        report = verify_trace(seal_trace(source))
        self.assertFalse(report.accepted)
        self.assertIn("I07_NO_EARLY_CALLBACK", report.invariant_failures)

    def test_sdk_admission_identity_and_covered_path_are_required(self) -> None:
        for field, value in (
            ("handle_tag", "wrong-handle"),
            ("pending_node_tag", "wrong-node"),
            ("callback_owner_tag", "wrong-owner"),
        ):
            with self.subTest(field=field):
                source = minimal_accept_raw()
                source[12][field] = value
                report = verify_trace(seal_trace(source))
                self.assertFalse(report.accepted)
                self.assertIn("I11_HANDLE_GENERATION_MATCH", report.invariant_failures)

        source = minimal_accept_raw()
        source[12]["details"]["callback_path_covered"] = False
        report = verify_trace(seal_trace(source))
        self.assertFalse(report.accepted)
        self.assertEqual(FailureCode.Q_CALLBACK_THREAD_UNPROVEN, report.primary_code)

        source = minimal_accept_raw()
        source[14]["thread_identity"] = "thread-uncovered-B"
        report = verify_trace(seal_trace(source))
        self.assertFalse(report.accepted)
        self.assertEqual(FailureCode.Q_CALLBACK_THREAD_UNPROVEN, report.primary_code)

    def test_registration_witnesses_must_run_on_the_exact_worker(self) -> None:
        for index in (6, 10):
            with self.subTest(event_type=minimal_accept_raw()[index]["event_type"]):
                source = minimal_accept_raw()
                source[index]["thread_identity"] = COORDINATOR_THREAD
                report = verify_trace(seal_trace(source))
                self.assertFalse(report.accepted)
                self.assertIn("I16_STABLE_SESSION", report.invariant_failures)

        source = minimal_accept_raw()
        source[6]["details"]["request_fingerprint_match"] = False
        report = verify_trace(seal_trace(source))
        self.assertFalse(report.accepted)
        self.assertEqual(FailureCode.Q_REGISTRATION_UNPROVEN, report.primary_code)

    def test_all_bounded_witness_subsets_reject_if_incomplete(self) -> None:
        source = minimal_accept_raw()
        witness_positions = [6, 7, 8, 9, 16, 18, 21, 22, 23]
        for missing_count in (1, 2):
            for removed in itertools.combinations(witness_positions, missing_count):
                mutation = [
                    deepcopy(item)
                    for index, item in enumerate(source)
                    if index not in set(removed)
                ]
                self.assertFalse(verify_trace(seal_trace(mutation)).accepted)


class InvariantTests(unittest.TestCase):
    def _report_with_extra(self, through: str, *events: dict):
        items = prefix_raw(through)
        items.extend(deepcopy(list(events)))
        return verify_trace(seal_trace(items))

    def test_required_fixtures_and_targeted_mutations_exercise_all_invariants(self) -> None:
        observed: set[str] = set()
        for trace in rejected_traces():
            observed.update(verify_trace(trace).invariant_failures)

        # I05: a second cleanup invocation.
        report = self._report_with_extra(
            "WAIT_BEGIN",
            raw("DEADLINE", thread_identity=COORDINATOR_THREAD),
            raw("CLEANUP_RETURN", thread_identity=COORDINATOR_THREAD),
            raw("CLEANUP_RETURN", thread_identity=COORDINATOR_THREAD),
        )
        observed.update(report.invariant_failures)

        # I09: helper exit counter does not match the actual counter.
        items = prefix_raw("HELPER_ENTER")
        items.append(raw("HELPER_EXIT", thread_identity=CALLBACK_THREAD, before_count=0, after_count=-1))
        observed.update(verify_trace(seal_trace(items)).invariant_failures)

        # I18: the route changes after registration.
        items = prefix_raw("PENDING_ABSENT")
        items += [
            raw("ROUTE_CHANGE", details={"new_route_hash": "route-hash-B"}),
            deepcopy(minimal_accept_raw()[19]),
            deepcopy(minimal_accept_raw()[20]),
            deepcopy(minimal_accept_raw()[21]),
        ]
        observed.update(verify_trace(seal_trace(items)).invariant_failures)

        # I23: a snapshot is submitted outside fence-running state.
        report = self._report_with_extra(
            "WAIT_BEGIN",
            raw("FENCE_SNAPSHOT", thread_identity=WORKER_THREAD, details={"completion_gate": True}),
        )
        observed.update(report.invariant_failures)

        # I24: callback code attempts to post a fence reentrantly.
        report = self._report_with_extra(
            "WAIT_BEGIN",
            raw(
                "FENCE_POST",
                thread_identity=CALLBACK_THREAD,
                details={"completion_gate": True, "in_callback": True},
            ),
        )
        observed.update(report.invariant_failures)

        self.assertEqual(set(INVARIANTS), observed)

    def test_phase_field_is_checked_not_trusted(self) -> None:
        trace = minimal_accept_trace()
        trace[3] = replace(trace[3], phase="QS_QUIESCENT_VALID_RESPONSE")
        report = verify_trace(trace)
        self.assertFalse(report.accepted)
        self.assertIn("I01_MONOTONIC_PHASE", report.invariant_failures)

    def test_generation_and_identity_tags_are_not_handle_aliases(self) -> None:
        trace = minimal_accept_trace()
        callback_index = next(i for i, event in enumerate(trace) if event.event_type == "HELPER_ENTER")
        trace[callback_index] = replace(
            trace[callback_index],
            op_generation=trace[callback_index].op_generation + 1,
            pending_node_tag="different-node",
        )
        report = verify_trace(trace)
        self.assertFalse(report.accepted)
        self.assertIn("I02_ONE_GENERATION", report.invariant_failures)
        self.assertIn("I11_HANDLE_GENERATION_MATCH", report.invariant_failures)

    def test_trace_event_schema_rejects_missing_and_extra_fields(self) -> None:
        value = minimal_accept_trace()[0].to_dict()
        del value["seq"]
        with self.assertRaises(ValueError):
            TraceEvent.from_dict(value)

    def test_trace_event_schema_rejects_type_coercion_and_unknown_details(self) -> None:
        canonical = minimal_accept_trace()[0].to_dict()
        for field, value in (
            ("seq", "1"),
            ("seq", True),
            ("thread_identity", 7),
        ):
            with self.subTest(field=field, value=value):
                mutation = deepcopy(canonical)
                mutation[field] = value
                with self.assertRaises(ValueError):
                    TraceEvent.from_dict(mutation)

        mutation = deepcopy(canonical)
        mutation["coverage_latches"] = [True]
        with self.assertRaises(ValueError):
            TraceEvent.from_dict(mutation)

        mutation = deepcopy(canonical)
        mutation["details"]["transport_retry"] = False
        with self.assertRaises(ValueError):
            TraceEvent.from_dict(mutation)

        mutation = deepcopy(canonical)
        mutation["details"]["unregistered_field"] = "value"
        with self.assertRaises(ValueError):
            TraceEvent.from_dict(mutation)

        direct = replace(minimal_accept_trace()[0], seq=True)
        with self.assertRaises(ValueError):
            QuiescenceVerifier().consume(direct)

        with self.assertRaises(ValueError):
            _events({"schema": "finduas-ridq-trace/v1", "events": [], "extra": True})
        value = minimal_accept_trace()[0].to_dict()
        value["unexpected"] = 1
        with self.assertRaises(ValueError):
            TraceEvent.from_dict(value)


if __name__ == "__main__":
    unittest.main()
