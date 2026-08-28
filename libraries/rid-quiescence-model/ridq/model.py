"""Pure reducer for synthetic Remote ID quiescence traces.

The reducer has no clock, thread, device, native-library, or transport dependency.  End of
input is deliberately not an event and therefore cannot prove absence or cleanup.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from .constants import (
    DETAIL_FIELD_TYPES,
    EVENT_TYPES,
    EVENT_INTEGER_FIELDS,
    EVENT_STRING_FIELDS,
    FIXED_PROFILE,
    FIXED_TRANSPORT_RETRY,
    INVARIANTS,
    PREFIX_CLASSES,
    SCHEMA,
    STATES,
    TERMINAL_STATES,
    TRANSITIONS,
    FailureCode,
)


@dataclass(frozen=True)
class TraceEvent:
    seq: int
    monotonic_ns: int
    op_generation: int
    phase: str
    thread_identity: str
    worker_identity: str
    session_epoch: int
    connection_epoch: int
    handle_tag: str
    pending_node_tag: str
    callback_owner_tag: str
    event_type: str
    before_count: int
    after_count: int
    coverage_latches: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Reject non-canonical or ambiguously typed synthetic input."""
        for name in EVENT_INTEGER_FIELDS:
            if type(getattr(self, name)) is not int:
                raise ValueError(f"{name} must be an integer (bool is not accepted)")
        for name in EVENT_STRING_FIELDS:
            if type(getattr(self, name)) is not str:
                raise ValueError(f"{name} must be a string")
        if self.phase not in STATES:
            raise ValueError(f"unknown phase {self.phase}")
        if self.event_type not in EVENT_TYPES:
            raise ValueError(f"unknown event_type {self.event_type}")
        if type(self.coverage_latches) is not tuple or any(
            type(item) is not str for item in self.coverage_latches
        ):
            raise ValueError("coverage_latches must contain only strings")
        if len(set(self.coverage_latches)) != len(self.coverage_latches):
            raise ValueError("coverage_latches must not contain duplicates")
        if type(self.details) is not dict or any(type(key) is not str for key in self.details):
            raise ValueError("details must be an object with string keys")

        type_table = {name: type_name for name, type_name in DETAIL_FIELD_TYPES}
        unknown = sorted(set(self.details) - set(type_table))
        if unknown:
            raise ValueError(f"unknown details fields: {unknown}")
        python_types = {"bool": bool, "int": int, "str": str}
        for name, value in self.details.items():
            expected_name = type_table[name]
            if type(value) is not python_types[expected_name]:
                raise ValueError(f"details.{name} must be {expected_name}")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "TraceEvent":
        if type(value) is not dict:
            raise ValueError("each event must be an object")
        required = {
            "seq",
            "monotonic_ns",
            "op_generation",
            "phase",
            "thread_identity",
            "worker_identity",
            "session_epoch",
            "connection_epoch",
            "handle_tag",
            "pending_node_tag",
            "callback_owner_tag",
            "event_type",
            "before_count",
            "after_count",
            "coverage_latches",
        }
        missing = sorted(required - value.keys())
        extra = sorted(value.keys() - required - {"details"})
        if missing or extra:
            raise ValueError(f"invalid event fields missing={missing} extra={extra}")
        if type(value["coverage_latches"]) is not list:
            raise ValueError("coverage_latches must be an array")
        if type(value.get("details", {})) is not dict:
            raise ValueError("details must be an object")
        event = cls(
            seq=value["seq"],
            monotonic_ns=value["monotonic_ns"],
            op_generation=value["op_generation"],
            phase=value["phase"],
            thread_identity=value["thread_identity"],
            worker_identity=value["worker_identity"],
            session_epoch=value["session_epoch"],
            connection_epoch=value["connection_epoch"],
            handle_tag=value["handle_tag"],
            pending_node_tag=value["pending_node_tag"],
            callback_owner_tag=value["callback_owner_tag"],
            event_type=value["event_type"],
            before_count=value["before_count"],
            after_count=value["after_count"],
            coverage_latches=tuple(value["coverage_latches"]),
            details=dict(value.get("details", {})),
        )
        event.validate()
        return event

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["coverage_latches"] = list(self.coverage_latches)
        return result


@dataclass
class ModelState:
    phase: str = "Q0_DORMANT"
    op_generation: int | None = None
    last_seq: int = -1
    last_ns: int = -1

    preflight: bool = False
    mapping_lease: bool = False
    native_binding: bool = False
    queued_task_live: bool = False
    dispatch_invocations: int = 0
    transport_retry_events: int = 0
    cancel_invocations: int = 0

    registration_hook: bool = False
    registration_hook_events: int = 0
    registration_complete: bool = False
    returned_handle: str = ""
    pending_node: str = ""
    callback_owner: str = ""
    pending_status: str = "UNKNOWN"
    stopper_status: str = "UNKNOWN"
    callback_owner_bound: bool = False

    sdk_callback_admitted: int = 0
    helper_callback_inflight: int = 0
    owner_copies: int = 0
    callback_thread_identity: str = ""
    callback_total: int = 0
    response_total: int = 0
    timeout_total: int = 0
    duplicate_total: int = 0
    terminal_winner: str = "NONE"
    response_disposition: str = "NONE"

    token_worker: str = ""
    token_worker_control: str = ""
    token_worker_thread: str = ""
    token_session_epoch: int = -1
    token_connection_epoch: int = -1
    token_route_hash: str = ""
    token_owner_identity: str = ""
    token_logical_identity: str = ""
    current_session_epoch: int = -1
    current_connection_epoch: int = -1
    current_worker: str = ""
    current_worker_control: str = ""
    current_worker_thread: str = ""
    current_route_hash: str = ""
    current_owner_identity: str = ""
    current_logical_identity: str = ""
    active_mutators: int = 0

    fence_posted: bool = False
    fence_started: bool = False
    fence_completed: bool = False
    quiescence: str = "NOT_STARTED"
    retention: str = "LEASE_HELD"
    accepted: bool = False

    invariant_failures: dict[str, list[int]] = field(
        default_factory=lambda: {name: [] for name in INVARIANTS}
    )
    primary_code: FailureCode | None = None
    unknown_latch: bool = False
    rejection_latch: bool = False
    coverage_broken: bool = False


@dataclass(frozen=True)
class VerificationReport:
    schema: str
    classification: str
    accepted: bool
    phase: str
    primary_code: int | None
    primary_name: str | None
    response_disposition: str
    quiescence: str
    retention: str
    dispatch_invocations: int
    transport_retry_events: int
    cancel_invocations: int
    callback_total: int
    sdk_callback_admitted: int
    helper_callback_inflight: int
    owner_copies: int
    registration_complete: bool
    pending_status: str
    stopper_status: str
    invariant_failures: dict[str, list[int]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class QuiescenceVerifier:
    """Deterministic state reducer.  It never invents an event at EOF."""

    def __init__(self, *, strict_phase: bool = True) -> None:
        self.state = ModelState()
        self.strict_phase = strict_phase

    def _primary(self, code: FailureCode) -> None:
        if self.state.primary_code is None:
            self.state.primary_code = code

    def _violate(
        self,
        invariant: str,
        event: TraceEvent,
        code: FailureCode,
        *,
        unknown: bool = False,
    ) -> None:
        if invariant not in self.state.invariant_failures:
            raise AssertionError(f"unknown invariant {invariant}")
        self.state.invariant_failures[invariant].append(event.seq)
        self.state.rejection_latch = True
        self.state.unknown_latch = self.state.unknown_latch or unknown
        self._primary(code)

    def _transition(self, event: TraceEvent, destination: str) -> bool:
        if destination not in STATES or (self.state.phase, destination) not in TRANSITIONS:
            self._violate(
                "I01_MONOTONIC_PHASE",
                event,
                FailureCode.Q_COVERAGE_BROKEN,
                unknown=True,
            )
            return False
        self.state.phase = destination
        return True

    def _same_token_identity(self, event: TraceEvent) -> bool:
        details = event.details
        return (
            event.worker_identity == self.state.token_worker
            and event.session_epoch == self.state.token_session_epoch
            and event.connection_epoch == self.state.token_connection_epoch
            and details.get("worker_control") == self.state.token_worker_control
            and details.get("worker_thread") == self.state.token_worker_thread
            and details.get("route_hash") == self.state.token_route_hash
            and details.get("owner_identity") == self.state.token_owner_identity
            and details.get("logical_identity") == self.state.token_logical_identity
        )

    def _check_worker_context(self, event: TraceEvent) -> bool:
        details = event.details
        stable_session = (
            event.thread_identity == self.state.token_worker_thread
            and event.worker_identity == self.state.token_worker
            and event.session_epoch == self.state.token_session_epoch
            and details.get("worker_control") == self.state.token_worker_control
            and details.get("worker_thread") == self.state.token_worker_thread
        )
        stable_connection = event.connection_epoch == self.state.token_connection_epoch
        stable_route = (
            details.get("route_hash") == self.state.token_route_hash
            and details.get("owner_identity") == self.state.token_owner_identity
            and details.get("logical_identity") == self.state.token_logical_identity
        )
        if not stable_session:
            self._violate(
                "I16_STABLE_SESSION",
                event,
                FailureCode.Q_REGISTRATION_EPOCH_CHANGED,
                unknown=True,
            )
        if not stable_connection:
            self._violate(
                "I17_STABLE_CONNECTION",
                event,
                FailureCode.Q_REGISTRATION_EPOCH_CHANGED,
                unknown=True,
            )
        if not stable_route:
            self._violate(
                "I18_STABLE_ROUTE",
                event,
                FailureCode.Q_REGISTRATION_EPOCH_CHANGED,
                unknown=True,
            )
        return stable_session and stable_connection and stable_route

    def _check_callback_context(self, event: TraceEvent) -> bool:
        self._check_callback_identity(event)
        covered_thread = (
            bool(self.state.callback_thread_identity)
            and event.thread_identity == self.state.callback_thread_identity
        )
        if not covered_thread:
            self._violate(
                "I11_HANDLE_GENERATION_MATCH",
                event,
                FailureCode.Q_CALLBACK_THREAD_UNPROVEN,
                unknown=True,
            )
        stable_token = self._same_token_identity(event)
        if not stable_token:
            self._violate(
                "I11_HANDLE_GENERATION_MATCH",
                event,
                FailureCode.Q_CALLBACK_GENERATION_MISMATCH,
                unknown=True,
            )
        return covered_thread and stable_token

    def _check_counter(
        self,
        event: TraceEvent,
        current: int,
        expected_after: int,
        invariant: str,
    ) -> bool:
        if event.before_count != current or event.after_count != expected_after or expected_after < 0:
            self._violate(
                invariant,
                event,
                FailureCode.Q_CALLBACK_COUNTER_UNBALANCED,
                unknown=True,
            )
            return False
        return True

    def _check_callback_identity(self, event: TraceEvent) -> None:
        if event.op_generation != self.state.op_generation:
            self._violate(
                "I11_HANDLE_GENERATION_MATCH",
                event,
                FailureCode.Q_CALLBACK_GENERATION_MISMATCH,
                unknown=True,
            )
        if event.handle_tag != self.state.returned_handle:
            self._violate(
                "I11_HANDLE_GENERATION_MATCH",
                event,
                FailureCode.Q_CALLBACK_HANDLE_MISMATCH,
                unknown=True,
            )
        if (
            event.pending_node_tag != self.state.pending_node
            or event.callback_owner_tag != self.state.callback_owner
        ):
            self._violate(
                "I11_HANDLE_GENERATION_MATCH",
                event,
                FailureCode.Q_CALLBACK_GENERATION_MISMATCH,
                unknown=True,
            )

    def _record_terminal(self, event: TraceEvent, winner: str, disposition: str) -> None:
        if self.state.terminal_winner == "NONE":
            self.state.terminal_winner = winner
            self.state.response_disposition = disposition
            if self.state.phase == "Q6_WAIT_TERMINAL":
                self._transition(event, "Q7_TERMINAL_RECORDED")
            elif self.state.cancel_invocations or self.state.phase.startswith("QC_"):
                if winner == "RESPONSE":
                    self.state.response_disposition = "AMBIGUOUS_AFTER_CANCEL"
                    self._violate(
                        "I22_CANCEL_NEVER_SUCCESS",
                        event,
                        FailureCode.Q_AMBIGUOUS_AFTER_CANCEL,
                    )
            else:
                self._violate(
                    "I01_MONOTONIC_PHASE",
                    event,
                    FailureCode.Q_CALLBACK_THREAD_UNPROVEN,
                    unknown=True,
                )
        else:
            self.state.duplicate_total += 1
            if self.state.cancel_invocations and winner == "RESPONSE":
                self.state.response_disposition = "AMBIGUOUS_AFTER_CANCEL"
                code = FailureCode.Q_AMBIGUOUS_AFTER_CANCEL
                invariant = "I22_CANCEL_NEVER_SUCCESS"
            else:
                code = FailureCode.Q_DUPLICATE_CALLBACK
                invariant = "I10_FIRST_WINNER_IMMUTABLE"
            self._violate(invariant, event, code)

    def _finalize_fence(self, event: TraceEvent, *, cleanup: bool) -> None:
        details = event.details
        self.state.fence_completed = bool(details.get("completion_gate"))
        if not self.state.fence_completed:
            self._violate(
                "I12_FENCE_EXTERNAL_POST",
                event,
                FailureCode.Q_FENCE_COMPLETION_TIMEOUT,
                unknown=True,
            )

        if event.thread_identity != self.state.token_worker_thread:
            self._violate(
                "I12_FENCE_EXTERNAL_POST",
                event,
                FailureCode.Q_FENCE_CARRIER_UNPROVEN,
                unknown=True,
            )

        pending_absent = (
            self.state.pending_status == "ABSENT"
            and details.get("pending_absent") is True
            and event.handle_tag == self.state.returned_handle
            and event.pending_node_tag == self.state.pending_node
        )
        stopper_absent = (
            self.state.stopper_status == "ABSENT"
            and details.get("stopper_absent") is True
            and event.handle_tag == self.state.returned_handle
            and event.callback_owner_tag == self.state.callback_owner
        )
        if not pending_absent:
            self._violate(
                "I14_EXACT_ABSENCE",
                event,
                FailureCode.Q_PENDING_STILL_PRESENT_OR_UNKNOWN,
                unknown=True,
            )
        if not stopper_absent:
            self._violate(
                "I14_EXACT_ABSENCE",
                event,
                FailureCode.Q_STOPPER_STILL_PRESENT_OR_UNKNOWN,
                unknown=True,
            )

        zero_inflight = (
            self.state.sdk_callback_admitted == 0
            and self.state.helper_callback_inflight == 0
            and details.get("sdk_callback_admitted") == 0
            and details.get("helper_callback_inflight") == 0
        )
        if not zero_inflight:
            code = (
                FailureCode.Q_SDK_CALLBACK_ADMITTED
                if self.state.sdk_callback_admitted or details.get("sdk_callback_admitted")
                else FailureCode.Q_HELPER_CALLBACK_INFLIGHT
            )
            self._violate("I15_ZERO_INFLIGHT_AT_FENCE", event, code, unknown=True)

        owner_drained = self.state.owner_copies == 0 and details.get("owner_copies") == 0
        if not owner_drained:
            self._violate(
                "I21_STATE_NOT_FREED_EARLY",
                event,
                FailureCode.Q_OWNER_DESTRUCTION_UNPROVEN,
                unknown=True,
            )

        stable_session = (
            event.session_epoch == self.state.token_session_epoch
            and event.worker_identity == self.state.token_worker
            and details.get("worker_control") == self.state.token_worker_control
            and details.get("worker_thread") == self.state.token_worker_thread
            and self.state.current_session_epoch == self.state.token_session_epoch
            and self.state.current_worker == self.state.token_worker
            and self.state.current_worker_control == self.state.token_worker_control
            and self.state.current_worker_thread == self.state.token_worker_thread
        )
        if not stable_session:
            self._violate(
                "I16_STABLE_SESSION",
                event,
                FailureCode.Q_SESSION_EPOCH_CHANGED,
            )

        stable_connection = (
            event.connection_epoch == self.state.token_connection_epoch
            and self.state.current_connection_epoch == self.state.token_connection_epoch
            and self.state.active_mutators == 0
            and details.get("active_mutators") == 0
        )
        if not stable_connection:
            self._violate(
                "I17_STABLE_CONNECTION",
                event,
                FailureCode.Q_CONNECTION_EPOCH_CHANGED,
                unknown=self.state.active_mutators != 0,
            )

        stable_route = (
            details.get("route_hash") == self.state.token_route_hash
            and details.get("owner_identity") == self.state.token_owner_identity
            and details.get("logical_identity") == self.state.token_logical_identity
            and self.state.current_route_hash == self.state.token_route_hash
            and self.state.current_owner_identity == self.state.token_owner_identity
            and self.state.current_logical_identity == self.state.token_logical_identity
        )
        if not stable_route:
            self._violate(
                "I18_STABLE_ROUTE",
                event,
                FailureCode.Q_ROUTE_IDENTITY_CHANGED,
            )

        if self.state.coverage_broken or event.coverage_latches:
            self._violate(
                "I19_COVERAGE_CLEAN",
                event,
                FailureCode.Q_COVERAGE_BROKEN,
                unknown=True,
            )

        drain_proven = (
            self.state.fence_completed
            and pending_absent
            and stopper_absent
            and zero_inflight
            and owner_drained
            and stable_session
            and stable_connection
            and stable_route
            and not self.state.coverage_broken
            and not event.coverage_latches
            and self.state.registration_complete
            and self.state.mapping_lease
            and self.state.native_binding
        )
        if not drain_proven or self.state.unknown_latch:
            self.state.phase = "QX_UNKNOWN_RETAINED"
            self.state.quiescence = "UNPROVEN"
            return

        self.state.quiescence = "PROVEN"
        if cleanup or self.state.cancel_invocations:
            self.state.phase = "QF_QUIESCENT_CANCELLED"
            return

        success_predicate = (
            self.state.preflight
            and self.state.dispatch_invocations == 1
            and self.state.transport_retry_events == FIXED_TRANSPORT_RETRY
            and self.state.terminal_winner == "RESPONSE"
            and self.state.response_disposition == "VALID"
            and self.state.callback_total == 1
            and self.state.response_total == 1
            and self.state.timeout_total == 0
            and self.state.duplicate_total == 0
            and self.state.cancel_invocations == 0
            and not self.state.rejection_latch
        )
        if success_predicate:
            self.state.phase = "QS_QUIESCENT_VALID_RESPONSE"
        else:
            self.state.phase = "QF_QUIESCENT_REJECTED"

    def consume(self, event: TraceEvent) -> VerificationReport:
        event.validate()
        if event.seq <= self.state.last_seq or event.monotonic_ns <= self.state.last_ns:
            self._violate(
                "I01_MONOTONIC_PHASE",
                event,
                FailureCode.Q_COVERAGE_BROKEN,
                unknown=True,
            )
        self.state.last_seq = max(self.state.last_seq, event.seq)
        self.state.last_ns = max(self.state.last_ns, event.monotonic_ns)

        if self.state.op_generation is None:
            self.state.op_generation = event.op_generation
        elif event.op_generation != self.state.op_generation:
            self._violate(
                "I02_ONE_GENERATION",
                event,
                FailureCode.Q_CALLBACK_GENERATION_MISMATCH,
                unknown=True,
            )

        if event.coverage_latches:
            self.state.coverage_broken = True
            self._violate(
                "I19_COVERAGE_CLEAN",
                event,
                FailureCode.Q_COVERAGE_BROKEN,
                unknown=True,
            )

        if self.state.phase in TERMINAL_STATES:
            allowed_cleanup = {
                "UNREGISTER_BINDING",
                "LEASE_RELEASE",
                "PROCESS_RETENTION",
            }
            if self.state.phase != "QS_QUIESCENT_VALID_RESPONSE" or event.event_type not in allowed_cleanup:
                self._violate(
                    "I25_TERMINAL_FREEZE",
                    event,
                    FailureCode.Q_COVERAGE_BROKEN,
                    unknown=True,
                )
                self.state.phase = "QX_UNKNOWN_RETAINED"
                self.state.accepted = False
                return self.report()

        self._apply(event)

        if self.strict_phase and event.phase != self.state.phase:
            self._violate(
                "I01_MONOTONIC_PHASE",
                event,
                FailureCode.Q_COVERAGE_BROKEN,
                unknown=True,
            )
        return self.report()

    def _apply(self, event: TraceEvent) -> None:
        kind = event.event_type
        details = event.details
        state = self.state

        callback_reentry = details.get("in_callback") is True or (
            state.helper_callback_inflight > 0
            and bool(state.callback_thread_identity)
            and event.thread_identity == state.callback_thread_identity
        )
        if callback_reentry and kind in {
            "DISPATCH",
            "CLEANUP_RETURN",
            "FENCE_POST",
            "CLEANUP_FENCE_POST",
            "WAIT_BEGIN",
            "ROUTE_CHANGE",
        }:
            self._violate(
                "I24_NO_REENTRY",
                event,
                FailureCode.Q_CALLBACK_THREAD_UNPROVEN,
                unknown=True,
            )

        if kind == "PREFLIGHT_PASS":
            if state.phase != "Q0_DORMANT":
                self._violate("I01_MONOTONIC_PHASE", event, FailureCode.Q_IDENTITY_UNPROVEN)
                return
            if details.get("profile") != FIXED_PROFILE:
                self._violate("I04_NO_TRANSPORT_RETRY", event, FailureCode.Q_IDENTITY_UNPROVEN)
                state.phase = "QF_NOT_ADMITTED"
                return
            if details.get("transport_retry") != FIXED_TRANSPORT_RETRY:
                self._violate(
                    "I04_NO_TRANSPORT_RETRY",
                    event,
                    FailureCode.Q_TRANSPORT_RETRY_OBSERVED,
                )
                state.phase = "QF_NOT_ADMITTED"
                return
            required_identity = (
                event.worker_identity,
                details.get("worker_control"),
                details.get("worker_thread"),
                details.get("route_hash"),
                details.get("owner_identity"),
                details.get("logical_identity"),
            )
            if not all(type(item) is str and item for item in required_identity):
                self._violate(
                    "I16_STABLE_SESSION",
                    event,
                    FailureCode.Q_WORKER_IDENTITY_UNPROVEN,
                    unknown=True,
                )
                state.phase = "QF_NOT_ADMITTED"
                return
            state.preflight = True
            state.token_worker = event.worker_identity
            state.token_worker_control = str(details.get("worker_control", ""))
            state.token_worker_thread = str(details.get("worker_thread", ""))
            state.token_session_epoch = event.session_epoch
            state.token_connection_epoch = event.connection_epoch
            state.token_route_hash = str(details.get("route_hash", ""))
            state.token_owner_identity = str(details.get("owner_identity", ""))
            state.token_logical_identity = str(details.get("logical_identity", ""))
            state.current_worker = state.token_worker
            state.current_worker_control = state.token_worker_control
            state.current_worker_thread = state.token_worker_thread
            state.current_session_epoch = state.token_session_epoch
            state.current_connection_epoch = state.token_connection_epoch
            state.current_route_hash = state.token_route_hash
            state.current_owner_identity = state.token_owner_identity
            state.current_logical_identity = state.token_logical_identity
            self._transition(event, "Q1_PREFLIGHT")

        elif kind == "LEASE_ACQUIRE":
            if state.phase != "Q1_PREFLIGHT" or not state.preflight:
                self._violate(
                    "I20_MAPPING_BEFORE_POINTER_ESCAPE",
                    event,
                    FailureCode.Q_MAPPING_LEASE_UNAVAILABLE,
                    unknown=True,
                )
                return
            state.mapping_lease = True
            state.retention = "LEASE_HELD"
            self._transition(event, "Q2_MAPPING_RETAINED")

        elif kind == "BINDING_REGISTER":
            if state.phase != "Q2_MAPPING_RETAINED" or not state.mapping_lease:
                self._violate(
                    "I20_MAPPING_BEFORE_POINTER_ESCAPE",
                    event,
                    FailureCode.Q_NATIVE_BINDING_LEASE_UNPROVEN,
                    unknown=True,
                )
                return
            state.native_binding = True

        elif kind == "TASK_POST":
            if state.phase != "Q2_MAPPING_RETAINED" or not state.mapping_lease or not state.native_binding:
                self._violate(
                    "I20_MAPPING_BEFORE_POINTER_ESCAPE",
                    event,
                    FailureCode.Q_MAPPING_RETENTION_LOST,
                    unknown=True,
                )
                return
            state.queued_task_live = True
            self._transition(event, "Q3_TASK_QUEUED")

        elif kind == "INITIAL_ENTER":
            if state.phase != "Q3_TASK_QUEUED":
                self._violate("I01_MONOTONIC_PHASE", event, FailureCode.Q_REGISTRATION_STUCK, unknown=True)
                return
            self._check_worker_context(event)
            state.queued_task_live = False
            self._transition(event, "Q4_REGISTERING")

        elif kind == "DISPATCH":
            if state.phase != "Q4_REGISTERING":
                self._violate("I03_ONE_DISPATCH", event, FailureCode.Q_DISPATCH_CARDINALITY, unknown=True)
                return
            self._check_worker_context(event)
            state.dispatch_invocations += 1
            if state.dispatch_invocations != 1:
                self._violate("I03_ONE_DISPATCH", event, FailureCode.Q_DISPATCH_CARDINALITY, unknown=True)

        elif kind == "TRANSPORT_RETRY":
            state.transport_retry_events += 1
            self._violate(
                "I04_NO_TRANSPORT_RETRY",
                event,
                FailureCode.Q_TRANSPORT_RETRY_OBSERVED,
                unknown=True,
            )

        elif kind == "REG_HOOK":
            if state.phase != "Q4_REGISTERING" or state.dispatch_invocations != 1:
                self._violate("I06_REG_BEFORE_WAIT", event, FailureCode.Q_REGISTRATION_UNPROVEN, unknown=True)
                return
            state.registration_hook_events += 1
            if state.registration_hook_events != 1:
                self._violate(
                    "I06_REG_BEFORE_WAIT",
                    event,
                    FailureCode.Q_REGISTRATION_UNPROVEN,
                    unknown=True,
                )
                return
            context_exact = self._check_worker_context(event)
            state.returned_handle = event.handle_tag
            state.pending_node = event.pending_node_tag
            state.callback_owner = event.callback_owner_tag
            hook_exact = (
                details.get("exact_registration") is True
                and details.get("request_fingerprint_match") is True
                and details.get("registration_generation") == state.op_generation
                and bool(state.returned_handle)
                and bool(state.pending_node)
                and bool(state.callback_owner)
                and context_exact
            )
            state.registration_hook = hook_exact
            if not hook_exact:
                self._violate(
                    "I06_REG_BEFORE_WAIT",
                    event,
                    FailureCode.Q_REGISTRATION_UNPROVEN,
                    unknown=True,
                )
            if details.get("possibly_inserted") and not state.registration_hook:
                state.unknown_latch = True

        elif kind == "PENDING_PRESENT":
            exact = (
                state.phase == "Q4_REGISTERING"
                and state.registration_hook
                and self._check_worker_context(event)
                and details.get("exact_worker_witness") is True
                and event.handle_tag == state.returned_handle
                and event.pending_node_tag == state.pending_node
                and event.callback_owner_tag == state.callback_owner
                and bool(event.pending_node_tag)
            )
            if not exact:
                self._violate("I11_HANDLE_GENERATION_MATCH", event, FailureCode.Q_PENDING_NOT_PRESENT_AFTER_REG, unknown=True)
            else:
                state.pending_status = "PRESENT"

        elif kind == "STOPPER_PRESENT":
            exact = (
                state.phase == "Q4_REGISTERING"
                and state.registration_hook
                and self._check_worker_context(event)
                and details.get("same_stopper_mutex") is True
                and details.get("membership_positive") is True
                and event.handle_tag == state.returned_handle
                and event.pending_node_tag == state.pending_node
                and event.callback_owner_tag == state.callback_owner
            )
            if not exact:
                self._violate("I11_HANDLE_GENERATION_MATCH", event, FailureCode.Q_STOPPER_NOT_PRESENT_AFTER_REG, unknown=True)
            else:
                state.stopper_status = "PRESENT"

        elif kind == "OWNER_BOUND":
            exact = (
                state.phase == "Q4_REGISTERING"
                and state.registration_hook
                and self._check_worker_context(event)
                and details.get("independent_owner_witness") is True
                and event.handle_tag == state.returned_handle
                and event.pending_node_tag == state.pending_node
                and event.callback_owner_tag == state.callback_owner
                and bool(event.callback_owner_tag)
            )
            if not exact:
                self._violate("I11_HANDLE_GENERATION_MATCH", event, FailureCode.Q_NEW_GLOBAL_REF_UNCERTAIN, unknown=True)
            else:
                state.callback_owner_bound = True

        elif kind == "REG_COMPLETE":
            complete = (
                state.phase == "Q4_REGISTERING"
                and state.dispatch_invocations == 1
                and state.transport_retry_events == FIXED_TRANSPORT_RETRY
                and state.registration_hook
                and bool(state.returned_handle)
                and state.pending_status == "PRESENT"
                and state.stopper_status == "PRESENT"
                and state.callback_owner_bound
                and state.callback_total == 0
                and state.sdk_callback_admitted == 0
                and state.helper_callback_inflight == 0
                and state.terminal_winner == "NONE"
                and state.active_mutators == 0
                and not state.coverage_broken
                and self._check_worker_context(event)
                and event.handle_tag == state.returned_handle
                and event.pending_node_tag == state.pending_node
                and event.callback_owner_tag == state.callback_owner
            )
            if not complete:
                code = (
                    FailureCode.Q_PENDING_NOT_PRESENT_AFTER_REG
                    if state.pending_status != "PRESENT"
                    else FailureCode.Q_STOPPER_NOT_PRESENT_AFTER_REG
                    if state.stopper_status != "PRESENT"
                    else FailureCode.Q_REGISTRATION_UNPROVEN
                )
                self._violate("I06_REG_BEFORE_WAIT", event, code, unknown=True)
                return
            state.registration_complete = True
            self._transition(event, "Q5_REGISTERED")

        elif kind == "WAIT_BEGIN":
            if state.phase != "Q5_REGISTERED" or not state.registration_complete:
                self._violate("I06_REG_BEFORE_WAIT", event, FailureCode.Q_REGISTRATION_UNPROVEN, unknown=True)
                return
            self._transition(event, "Q6_WAIT_TERMINAL")

        elif kind == "SDK_ADMIT_ENTER":
            if not state.registration_complete:
                self._violate(
                    "I07_NO_EARLY_CALLBACK",
                    event,
                    FailureCode.Q_CALLBACK_BEFORE_REGISTRATION,
                )
            self._check_callback_identity(event)
            callback_path_covered = (
                details.get("callback_path_covered") is True
                and bool(event.thread_identity)
                and self._same_token_identity(event)
            )
            if not callback_path_covered:
                self._violate(
                    "I11_HANDLE_GENERATION_MATCH",
                    event,
                    FailureCode.Q_CALLBACK_THREAD_UNPROVEN,
                    unknown=True,
                )
            if state.sdk_callback_admitted != 0:
                self._violate(
                    "I10_FIRST_WINNER_IMMUTABLE",
                    event,
                    FailureCode.Q_DUPLICATE_CALLBACK,
                )
            if not state.callback_thread_identity:
                state.callback_thread_identity = event.thread_identity
            elif event.thread_identity != state.callback_thread_identity:
                self._violate(
                    "I11_HANDLE_GENERATION_MATCH",
                    event,
                    FailureCode.Q_CALLBACK_THREAD_UNPROVEN,
                    unknown=True,
                )
            expected = state.sdk_callback_admitted + 1
            valid = self._check_counter(event, state.sdk_callback_admitted, expected, "I08_BALANCED_SDK_ADMISSION")
            if (
                state.stopper_status != "PRESENT"
                or details.get("same_stopper_mutex") is not True
                or details.get("membership_positive") is not True
                or details.get("owner_copied_before_increment") is not False
            ):
                self._violate(
                    "I08_BALANCED_SDK_ADMISSION",
                    event,
                    FailureCode.Q_CALLBACK_COUNTER_UNBALANCED,
                    unknown=True,
                )
            if valid:
                state.sdk_callback_admitted = expected

        elif kind == "HELPER_ENTER":
            expected = state.helper_callback_inflight + 1
            valid = self._check_counter(event, state.helper_callback_inflight, expected, "I09_BALANCED_HELPER_INFLIGHT")
            if not state.registration_complete:
                self._violate(
                    "I07_NO_EARLY_CALLBACK",
                    event,
                    FailureCode.Q_CALLBACK_BEFORE_REGISTRATION,
                )
            self._check_callback_context(event)
            if state.sdk_callback_admitted <= 0:
                self._violate(
                    "I08_BALANCED_SDK_ADMISSION",
                    event,
                    FailureCode.Q_CALLBACK_COUNTER_UNBALANCED,
                    unknown=True,
                )
            if valid:
                state.helper_callback_inflight = expected
            state.callback_total += 1
            if state.callback_total > 1:
                self._violate("I10_FIRST_WINNER_IMMUTABLE", event, FailureCode.Q_DUPLICATE_CALLBACK)

        elif kind in {"RESPONSE_VALID", "REMOTE_TIMEOUT", "MALFORMED_RESPONSE", "PROTOCOL_REJECTED"}:
            if state.helper_callback_inflight <= 0:
                self._violate(
                    "I09_BALANCED_HELPER_INFLIGHT",
                    event,
                    FailureCode.Q_CALLBACK_COUNTER_UNBALANCED,
                    unknown=True,
                )
            self._check_callback_context(event)
            if kind == "RESPONSE_VALID":
                state.response_total += 1
                valid_payload = details.get("payload_valid") is True and details.get("protocol_ok") is True
                if not valid_payload:
                    self._violate("I10_FIRST_WINNER_IMMUTABLE", event, FailureCode.Q_MALFORMED_RESPONSE)
                self._record_terminal(event, "RESPONSE", "VALID" if valid_payload else "REJECTED")
            elif kind == "REMOTE_TIMEOUT":
                state.timeout_total += 1
                self._primary(FailureCode.Q_REMOTE_TIMEOUT)
                state.rejection_latch = True
                self._record_terminal(event, "REMOTE_TIMEOUT", "REJECTED")
            elif kind == "MALFORMED_RESPONSE":
                self._primary(FailureCode.Q_MALFORMED_RESPONSE)
                state.rejection_latch = True
                self._record_terminal(event, "MALFORMED", "REJECTED")
            else:
                self._primary(FailureCode.Q_PROTOCOL_REJECTED)
                state.rejection_latch = True
                self._record_terminal(event, "PROTOCOL_REJECTED", "REJECTED")

        elif kind == "HELPER_EXIT":
            self._check_callback_context(event)
            expected = state.helper_callback_inflight - 1
            if self._check_counter(event, state.helper_callback_inflight, expected, "I09_BALANCED_HELPER_INFLIGHT"):
                state.helper_callback_inflight = expected

        elif kind == "STOPPER_ABSENT":
            self._check_callback_context(event)
            if (
                details.get("same_stopper_mutex") is not True
                or event.handle_tag != state.returned_handle
                or event.callback_owner_tag != state.callback_owner
            ):
                self._violate("I14_EXACT_ABSENCE", event, FailureCode.Q_STOPPER_STILL_PRESENT_OR_UNKNOWN, unknown=True)
            if state.terminal_winner == "RESPONSE" and state.helper_callback_inflight != 0:
                self._violate(
                    "I09_BALANCED_HELPER_INFLIGHT",
                    event,
                    FailureCode.Q_HELPER_CALLBACK_INFLIGHT,
                    unknown=True,
                )
            state.stopper_status = "ABSENT"

        elif kind == "SDK_ADMIT_EXIT":
            self._check_callback_context(event)
            expected = state.sdk_callback_admitted - 1
            if (
                state.stopper_status != "ABSENT"
                or state.helper_callback_inflight != 0
                or details.get("after_callback_and_remove") is not True
            ):
                self._violate(
                    "I08_BALANCED_SDK_ADMISSION",
                    event,
                    FailureCode.Q_CALLBACK_COUNTER_UNBALANCED,
                    unknown=True,
                )
            if self._check_counter(event, state.sdk_callback_admitted, expected, "I08_BALANCED_SDK_ADMISSION"):
                state.sdk_callback_admitted = expected

        elif kind == "PENDING_ABSENT":
            if (
                not self._check_worker_context(event)
                or details.get("exact_worker_witness") is not True
                or event.handle_tag != state.returned_handle
                or event.pending_node_tag != state.pending_node
                or event.callback_owner_tag != state.callback_owner
            ):
                self._violate("I14_EXACT_ABSENCE", event, FailureCode.Q_PENDING_STILL_PRESENT_OR_UNKNOWN, unknown=True)
            if state.terminal_winner == "RESPONSE" and (
                state.helper_callback_inflight != 0
                or state.sdk_callback_admitted != 0
                or state.stopper_status != "ABSENT"
            ):
                self._violate(
                    "I21_STATE_NOT_FREED_EARLY",
                    event,
                    FailureCode.Q_OWNER_DESTRUCTION_UNPROVEN,
                    unknown=True,
                )
            state.pending_status = "ABSENT"

        elif kind == "OWNER_COPY_ACQUIRE":
            state.owner_copies += 1

        elif kind == "OWNER_COPY_RELEASE":
            state.owner_copies -= 1
            if state.owner_copies < 0:
                self._violate("I21_STATE_NOT_FREED_EARLY", event, FailureCode.Q_OWNER_DESTRUCTION_UNPROVEN, unknown=True)

        elif kind == "FENCE_POST":
            if state.phase != "Q7_TERMINAL_RECORDED":
                self._violate("I13_FENCE_AFTER_TERMINAL", event, FailureCode.Q_FENCE_POST_FAILED, unknown=True)
                return
            if event.thread_identity == state.token_worker_thread or details.get("completion_gate") is not True:
                self._violate("I12_FENCE_EXTERNAL_POST", event, FailureCode.Q_FENCE_CARRIER_UNPROVEN, unknown=True)
            state.fence_posted = True
            self._transition(event, "Q8_FENCE_QUEUED")

        elif kind == "FENCE_START":
            if state.phase != "Q8_FENCE_QUEUED" or event.thread_identity != state.token_worker_thread:
                self._violate("I12_FENCE_EXTERNAL_POST", event, FailureCode.Q_FENCE_CARRIER_UNPROVEN, unknown=True)
                return
            self._check_worker_context(event)
            state.fence_started = True
            self._transition(event, "Q9_FENCE_RUNNING")

        elif kind == "FENCE_SNAPSHOT":
            if state.phase == "Q9_FENCE_RUNNING":
                self._finalize_fence(event, cleanup=False)
            elif state.phase == "QC_CANCEL_FENCE_RUNNING":
                self._finalize_fence(event, cleanup=True)
            else:
                self._violate("I23_RESULT_ONLY_AT_FENCE", event, FailureCode.Q_FENCE_CARRIER_UNPROVEN, unknown=True)

        elif kind == "DEADLINE":
            if state.phase == "Q3_TASK_QUEUED":
                state.terminal_winner = "LOCAL_DEADLINE"
                self._primary(FailureCode.Q_LOCAL_DEADLINE)
                self._transition(event, "QA_PRESTART_ABORTED")
            elif state.phase == "Q6_WAIT_TERMINAL":
                state.terminal_winner = "LOCAL_DEADLINE"
                self._primary(FailureCode.Q_LOCAL_DEADLINE)
                self._transition(event, "QC_CANCEL_REQUIRED")
            elif state.phase == "Q4_REGISTERING":
                state.terminal_winner = "LOCAL_DEADLINE"
                self._primary(FailureCode.Q_LOCAL_DEADLINE)
                state.unknown_latch = True
            else:
                self._violate("I05_ONE_CANCEL", event, FailureCode.Q_CANCEL_BEFORE_REGISTRATION, unknown=True)

        elif kind == "CLEANUP_RETURN":
            if state.phase != "QC_CANCEL_REQUIRED" or not state.registration_complete:
                self._violate("I05_ONE_CANCEL", event, FailureCode.Q_CANCEL_BEFORE_REGISTRATION, unknown=True)
                return
            state.cancel_invocations += 1
            if state.cancel_invocations != 1:
                self._violate("I05_ONE_CANCEL", event, FailureCode.Q_CANCEL_CARDINALITY, unknown=True)

        elif kind == "CLEANUP_ORDER_WITNESS":
            if (
                state.phase != "QC_CANCEL_REQUIRED"
                or state.cancel_invocations != 1
                or details.get("stopper_remove_before_core_post") is not True
                or details.get("core_post_attempted") is not True
            ):
                self._violate("I13_FENCE_AFTER_TERMINAL", event, FailureCode.Q_CANCEL_POST_UNPROVEN, unknown=True)
                return
            self._transition(event, "QC_CANCEL_POSTED")

        elif kind == "CLEANUP_FENCE_POST":
            if state.phase != "QC_CANCEL_POSTED":
                self._violate("I13_FENCE_AFTER_TERMINAL", event, FailureCode.Q_CANCEL_POST_UNPROVEN, unknown=True)
                return
            if event.thread_identity == state.token_worker_thread or details.get("completion_gate") is not True:
                self._violate("I12_FENCE_EXTERNAL_POST", event, FailureCode.Q_FENCE_CARRIER_UNPROVEN, unknown=True)
            self._transition(event, "QC_CANCEL_FENCE_QUEUED")

        elif kind == "CLEANUP_FENCE_START":
            if state.phase != "QC_CANCEL_FENCE_QUEUED" or event.thread_identity != state.token_worker_thread:
                self._violate("I12_FENCE_EXTERNAL_POST", event, FailureCode.Q_FENCE_CARRIER_UNPROVEN, unknown=True)
                return
            self._check_worker_context(event)
            self._transition(event, "QC_CANCEL_FENCE_RUNNING")

        elif kind == "PRESTART_ABORT":
            if state.phase != "Q3_TASK_QUEUED":
                self._violate("I01_MONOTONIC_PHASE", event, FailureCode.Q_PRESTART_ABORT_UNDRAINED, unknown=True)
                return
            state.terminal_winner = "LOCAL_DEADLINE"
            self._primary(FailureCode.Q_LOCAL_DEADLINE)
            self._transition(event, "QA_PRESTART_ABORTED")

        elif kind == "QUEUED_TASK_EXIT":
            if state.phase != "QA_PRESTART_ABORTED" or details.get("zero_dispatch_exit") is not True:
                self._violate("I21_STATE_NOT_FREED_EARLY", event, FailureCode.Q_PRESTART_ABORT_UNDRAINED, unknown=True)
                return
            state.queued_task_live = False
            state.quiescence = "PROVEN"
            self._transition(event, "QF_ABORTED_NO_DISPATCH")

        elif kind == "UNREGISTER_BINDING":
            if (
                state.phase != "QS_QUIESCENT_VALID_RESPONSE"
                or state.quiescence != "PROVEN"
                or state.sdk_callback_admitted
                or state.helper_callback_inflight
                or state.owner_copies
                or state.pending_status != "ABSENT"
                or state.stopper_status != "ABSENT"
            ):
                self._violate(
                    "I21_STATE_NOT_FREED_EARLY",
                    event,
                    FailureCode.Q_NATIVE_UNREGISTRATION_FAILED,
                    unknown=True,
                )
                return
            state.native_binding = False

        elif kind == "LEASE_RELEASE":
            safe = (
                state.phase == "QS_QUIESCENT_VALID_RESPONSE"
                and state.quiescence == "PROVEN"
                and not state.native_binding
                and not state.queued_task_live
                and not state.sdk_callback_admitted
                and not state.helper_callback_inflight
                and not state.owner_copies
                and state.pending_status == "ABSENT"
                and state.stopper_status == "ABSENT"
            )
            if not safe:
                self._violate("I20_MAPPING_BEFORE_POINTER_ESCAPE", event, FailureCode.Q_MAPPING_RETENTION_LOST, unknown=True)
                self._violate("I21_STATE_NOT_FREED_EARLY", event, FailureCode.Q_OWNER_DESTRUCTION_UNPROVEN, unknown=True)
                return
            state.mapping_lease = False
            state.retention = "RELEASED_AFTER_DRAIN"
            state.accepted = True
            state.primary_code = FailureCode.Q_QUIESCENT_VALID_RESPONSE

        elif kind == "PROCESS_RETENTION":
            safe = (
                state.phase == "QS_QUIESCENT_VALID_RESPONSE"
                and state.quiescence == "PROVEN"
                and state.mapping_lease
                and state.native_binding
                and details.get("mapping_and_binding_process_lifetime") is True
            )
            if not safe:
                self._violate("I20_MAPPING_BEFORE_POINTER_ESCAPE", event, FailureCode.Q_MAPPING_RETENTION_LOST, unknown=True)
                return
            state.retention = "PROCESS_LIFETIME"
            state.accepted = True
            state.primary_code = FailureCode.Q_QUIESCENT_VALID_RESPONSE

        elif kind == "SESSION_MUTATION":
            state.current_session_epoch = int(details.get("new_session_epoch", state.current_session_epoch + 1))
            if details.get("pending_cleared"):
                state.pending_status = "ABSENT"
            self._violate("I16_STABLE_SESSION", event, FailureCode.Q_SESSION_EPOCH_CHANGED)

        elif kind == "CONNECTION_MUTATION":
            state.current_connection_epoch = int(details.get("new_connection_epoch", state.current_connection_epoch + 1))
            self._violate("I17_STABLE_CONNECTION", event, FailureCode.Q_CONNECTION_EPOCH_CHANGED)

        elif kind == "WORKER_REPLACE":
            state.current_worker = str(details.get("new_worker", state.current_worker))
            state.current_worker_control = str(details.get("new_worker_control", state.current_worker_control))
            state.current_worker_thread = str(details.get("new_worker_thread", state.current_worker_thread))
            self._violate("I16_STABLE_SESSION", event, FailureCode.Q_SESSION_EPOCH_CHANGED)

        elif kind == "ROUTE_CHANGE":
            state.current_route_hash = str(details.get("new_route_hash", state.current_route_hash))
            state.current_owner_identity = str(details.get("new_owner_identity", state.current_owner_identity))
            state.current_logical_identity = str(details.get("new_logical_identity", state.current_logical_identity))
            self._violate("I18_STABLE_ROUTE", event, FailureCode.Q_ROUTE_IDENTITY_CHANGED)

        elif kind == "COVERAGE_BREAK":
            state.coverage_broken = True
            self._violate("I19_COVERAGE_CLEAN", event, FailureCode.Q_COVERAGE_BROKEN, unknown=True)

        elif kind == "MUTATOR_ENTER":
            state.active_mutators += 1
            if details.get("entry_has_exit_witness") is not True:
                state.coverage_broken = True
                self._violate("I19_COVERAGE_CLEAN", event, FailureCode.Q_COVERAGE_BROKEN, unknown=True)

        elif kind == "MUTATOR_EXIT":
            state.active_mutators -= 1
            if state.active_mutators < 0:
                state.coverage_broken = True
                self._violate("I19_COVERAGE_CLEAN", event, FailureCode.Q_COVERAGE_BROKEN, unknown=True)
            else:
                state.current_connection_epoch += 1

        elif kind == "HANDLE_REUSE":
            self._violate("I02_ONE_GENERATION", event, FailureCode.Q_CALLBACK_GENERATION_MISMATCH, unknown=True)
            self._violate("I11_HANDLE_GENERATION_MATCH", event, FailureCode.Q_CALLBACK_GENERATION_MISMATCH, unknown=True)

        elif kind == "JNI_EXCEPTION":
            self._violate("I19_COVERAGE_CLEAN", event, FailureCode.Q_CALLBACK_JNI_EXCEPTION, unknown=True)

        elif kind == "FENCE_COMPLETION_LOST":
            self._violate("I12_FENCE_EXTERNAL_POST", event, FailureCode.Q_FENCE_COMPLETION_TIMEOUT, unknown=True)

        elif kind == "STATE_DESTROY":
            if (
                state.queued_task_live
                or state.pending_status == "PRESENT"
                or state.stopper_status == "PRESENT"
                or state.sdk_callback_admitted
                or state.helper_callback_inflight
                or state.owner_copies
            ):
                self._violate("I21_STATE_NOT_FREED_EARLY", event, FailureCode.Q_OWNER_DESTRUCTION_UNPROVEN, unknown=True)

    def report(self) -> VerificationReport:
        state = self.state
        if state.phase.startswith("QF_"):
            classification = "QUIESCENT_REJECTED"
        elif state.phase == "QX_UNKNOWN_RETAINED" or state.unknown_latch:
            classification = "UNKNOWN_RETAINED"
        else:
            classification = "ACTIVE"
        if classification not in PREFIX_CLASSES:
            raise AssertionError("invalid prefix classification")
        code = state.primary_code
        return VerificationReport(
            schema=SCHEMA,
            classification=classification,
            accepted=state.accepted,
            phase=state.phase,
            primary_code=None if code is None else int(code),
            primary_name=None if code is None else code.name,
            response_disposition=state.response_disposition,
            quiescence=state.quiescence,
            retention=state.retention,
            dispatch_invocations=state.dispatch_invocations,
            transport_retry_events=state.transport_retry_events,
            cancel_invocations=state.cancel_invocations,
            callback_total=state.callback_total,
            sdk_callback_admitted=state.sdk_callback_admitted,
            helper_callback_inflight=state.helper_callback_inflight,
            owner_copies=state.owner_copies,
            registration_complete=state.registration_complete,
            pending_status=state.pending_status,
            stopper_status=state.stopper_status,
            invariant_failures={
                name: list(seqs)
                for name, seqs in state.invariant_failures.items()
                if seqs
            },
        )


def verify_trace(events: Iterable[TraceEvent], *, strict_phase: bool = True) -> VerificationReport:
    verifier = QuiescenceVerifier(strict_phase=strict_phase)
    for event in events:
        verifier.consume(event)
    return verifier.report()
