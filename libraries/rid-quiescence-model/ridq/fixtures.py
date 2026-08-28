"""Deterministic synthetic traces used by tests and the command-line demo."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Any

from .constants import FIXED_PROFILE, FIXED_TRANSPORT_RETRY
from .model import QuiescenceVerifier, TraceEvent


GENERATION = 41
WORKER = "worker-object-A"
WORKER_CONTROL = "worker-control-A"
WORKER_THREAD = "thread-worker-A"
COORDINATOR_THREAD = "thread-coordinator-A"
CALLBACK_THREAD = "thread-callback-A"
SESSION_EPOCH = 7
CONNECTION_EPOCH = 11
HANDLE = "handle-0000000000000042"
PENDING_NODE = "pending-node-generation-41"
CALLBACK_OWNER = "callback-owner-generation-41"
ROUTE_HASH = "route-hash-A"
OWNER_IDENTITY = "owners-A"
LOGICAL_IDENTITY = "logical-route-A"


def raw(event_type: str, **overrides: Any) -> dict[str, Any]:
    value: dict[str, Any] = {"event_type": event_type}
    value.update(overrides)
    return value


def minimal_accept_raw() -> list[dict[str, Any]]:
    """Every event is a required positive witness; no event is inferred from silence."""
    return [
        raw(
            "PREFLIGHT_PASS",
            details={
                "profile": FIXED_PROFILE,
                "transport_retry": FIXED_TRANSPORT_RETRY,
            },
        ),
        raw("LEASE_ACQUIRE"),
        raw("BINDING_REGISTER"),
        raw("TASK_POST"),
        raw("INITIAL_ENTER", thread_identity=WORKER_THREAD),
        raw("DISPATCH", thread_identity=WORKER_THREAD),
        raw(
            "REG_HOOK",
            thread_identity=WORKER_THREAD,
            handle_tag=HANDLE,
            pending_node_tag=PENDING_NODE,
            callback_owner_tag=CALLBACK_OWNER,
            details={
                "exact_registration": True,
                "request_fingerprint_match": True,
                "registration_generation": GENERATION,
            },
        ),
        raw(
            "PENDING_PRESENT",
            thread_identity=WORKER_THREAD,
            details={"exact_worker_witness": True},
        ),
        raw(
            "STOPPER_PRESENT",
            thread_identity=WORKER_THREAD,
            details={"same_stopper_mutex": True, "membership_positive": True},
        ),
        raw(
            "OWNER_BOUND",
            thread_identity=WORKER_THREAD,
            details={"independent_owner_witness": True},
        ),
        raw("REG_COMPLETE", thread_identity=WORKER_THREAD),
        raw("WAIT_BEGIN", thread_identity=COORDINATOR_THREAD),
        raw(
            "SDK_ADMIT_ENTER",
            thread_identity=CALLBACK_THREAD,
            before_count=0,
            after_count=1,
            details={
                "same_stopper_mutex": True,
                "membership_positive": True,
                "owner_copied_before_increment": False,
                "callback_path_covered": True,
            },
        ),
        raw(
            "HELPER_ENTER",
            thread_identity=CALLBACK_THREAD,
            before_count=0,
            after_count=1,
        ),
        raw(
            "RESPONSE_VALID",
            thread_identity=CALLBACK_THREAD,
            details={"payload_valid": True, "protocol_ok": True},
        ),
        raw(
            "HELPER_EXIT",
            thread_identity=CALLBACK_THREAD,
            before_count=1,
            after_count=0,
        ),
        raw(
            "STOPPER_ABSENT",
            thread_identity=CALLBACK_THREAD,
            details={"same_stopper_mutex": True},
        ),
        raw(
            "SDK_ADMIT_EXIT",
            thread_identity=CALLBACK_THREAD,
            before_count=1,
            after_count=0,
            details={"after_callback_and_remove": True},
        ),
        raw(
            "PENDING_ABSENT",
            thread_identity=WORKER_THREAD,
            details={"exact_worker_witness": True},
        ),
        raw(
            "FENCE_POST",
            thread_identity=COORDINATOR_THREAD,
            details={"completion_gate": True},
        ),
        raw("FENCE_START", thread_identity=WORKER_THREAD),
        raw(
            "FENCE_SNAPSHOT",
            thread_identity=WORKER_THREAD,
            details={
                "completion_gate": True,
                "pending_absent": True,
                "stopper_absent": True,
                "sdk_callback_admitted": 0,
                "helper_callback_inflight": 0,
                "owner_copies": 0,
                "active_mutators": 0,
            },
        ),
        raw("UNREGISTER_BINDING", thread_identity=COORDINATOR_THREAD),
        raw("LEASE_RELEASE", thread_identity=COORDINATOR_THREAD),
    ]


def _prefix(items: list[dict[str, Any]], event_type: str, *, include: bool = True) -> list[dict[str, Any]]:
    for index, item in enumerate(items):
        if item["event_type"] == event_type:
            return deepcopy(items[: index + (1 if include else 0)])
    raise KeyError(event_type)


def _remove(items: list[dict[str, Any]], event_type: str) -> list[dict[str, Any]]:
    result = deepcopy(items)
    for index, item in enumerate(result):
        if item["event_type"] == event_type:
            del result[index]
            return result
    raise KeyError(event_type)


REJECT_DESCRIPTIONS = (
    "callback before returned handle and registration completion",
    "nonzero handle without pending and Stopper witnesses",
    "response recorded while pending owner remains",
    "timeout copied owner remains active",
    "cleanup call returned before core cleanup ordering witness",
    "wrapper admitted before cleanup and helper entered afterward",
    "helper exited while wrapper and Stopper owner remain",
    "duplicate callback after a valid response",
    "only pending absence is observed",
    "both absence witnesses but callback counters remain nonzero",
    "same route value after connection epoch changed",
    "session teardown clears pending without a callback terminal",
    "worker object stable but control and thread identities changed",
    "deadline loses the queued-closure compare-and-swap race",
    "zero handle and exception with possible registration",
    "local deadline and valid response race",
    "tail fence is posted but never completes",
    "mapping lease released while queued task remains",
    "native binding removed while callback admission is nonzero",
    "second dispatch and a transport retry",
    "handle value reused by a different generation and owner",
    "coverage entry has no paired exit",
    "later head mutation changes epoch before tail snapshot",
    "prestart abort is followed by unload before queued closure exit",
)


def rejected_raw_traces() -> list[list[dict[str, Any]]]:
    base = minimal_accept_raw()
    traces: list[list[dict[str, Any]]] = []

    # 01
    t = _prefix(base, "TASK_POST")
    t += [
        raw(
            "SDK_ADMIT_ENTER",
            thread_identity=CALLBACK_THREAD,
            before_count=0,
            after_count=1,
            details={
                "same_stopper_mutex": True,
                "membership_positive": True,
                "owner_copied_before_increment": False,
                "callback_path_covered": True,
            },
        ),
        raw("HELPER_ENTER", thread_identity=CALLBACK_THREAD, before_count=0, after_count=1),
    ]
    traces.append(t)

    # 02
    t = _prefix(base, "REG_HOOK")
    t += [raw("OWNER_BOUND", thread_identity=WORKER_THREAD), raw("REG_COMPLETE", thread_identity=WORKER_THREAD)]
    traces.append(t)

    # 03
    traces.append(_remove(base, "PENDING_ABSENT"))

    # 04
    t = deepcopy(base)
    response_index = next(i for i, item in enumerate(t) if item["event_type"] == "RESPONSE_VALID")
    t[response_index] = raw("REMOTE_TIMEOUT", thread_identity=CALLBACK_THREAD)
    helper_exit_index = next(i for i, item in enumerate(t) if item["event_type"] == "HELPER_EXIT")
    t.insert(helper_exit_index + 1, raw("OWNER_COPY_ACQUIRE", thread_identity=WORKER_THREAD))
    traces.append(t)

    # 05
    t = _prefix(base, "WAIT_BEGIN")
    t += [
        raw("DEADLINE", thread_identity=COORDINATOR_THREAD),
        raw("CLEANUP_RETURN", thread_identity=COORDINATOR_THREAD),
        raw("FENCE_POST", thread_identity=COORDINATOR_THREAD, details={"completion_gate": True}),
    ]
    traces.append(t)

    # 06
    t = _prefix(base, "WAIT_BEGIN")
    t += [
        deepcopy(base[12]),
        raw("DEADLINE", thread_identity=COORDINATOR_THREAD),
        raw("CLEANUP_RETURN", thread_identity=COORDINATOR_THREAD),
        raw(
            "CLEANUP_ORDER_WITNESS",
            thread_identity=COORDINATOR_THREAD,
            details={"stopper_remove_before_core_post": True, "core_post_attempted": True},
        ),
        deepcopy(base[16]),
        deepcopy(base[13]),
        deepcopy(base[14]),
        deepcopy(base[15]),
        deepcopy(base[17]),
        deepcopy(base[18]),
        raw("CLEANUP_FENCE_POST", thread_identity=COORDINATOR_THREAD, details={"completion_gate": True}),
        raw("CLEANUP_FENCE_START", thread_identity=WORKER_THREAD),
        deepcopy(base[21]),
    ]
    traces.append(t)

    # 07
    t = _prefix(base, "HELPER_EXIT")
    t += [deepcopy(base[18]), deepcopy(base[19]), deepcopy(base[20]), deepcopy(base[21])]
    traces.append(t)

    # 08
    t = deepcopy(base)
    first_exit = next(i for i, item in enumerate(t) if item["event_type"] == "HELPER_EXIT")
    t[first_exit:first_exit] = [
        raw("HELPER_ENTER", thread_identity=CALLBACK_THREAD, before_count=1, after_count=2),
        raw(
            "RESPONSE_VALID",
            thread_identity=CALLBACK_THREAD,
            details={"payload_valid": True, "protocol_ok": True},
        ),
        raw("HELPER_EXIT", thread_identity=CALLBACK_THREAD, before_count=2, after_count=1),
    ]
    traces.append(t)

    # 09
    traces.append(_remove(base, "STOPPER_ABSENT"))

    # 10
    t = _prefix(base, "RESPONSE_VALID")
    t += [deepcopy(base[16]), deepcopy(base[18]), deepcopy(base[19]), deepcopy(base[20]), deepcopy(base[21])]
    traces.append(t)

    # 11
    t = deepcopy(base)
    fence_index = next(i for i, item in enumerate(t) if item["event_type"] == "FENCE_POST")
    t.insert(
        fence_index,
        raw(
            "CONNECTION_MUTATION",
            thread_identity="thread-mutator-A",
            details={"new_connection_epoch": CONNECTION_EPOCH + 1},
        ),
    )
    traces.append(t)

    # 12
    t = _prefix(base, "WAIT_BEGIN")
    t += [
        raw(
            "SESSION_MUTATION",
            thread_identity="thread-session-A",
            details={"new_session_epoch": SESSION_EPOCH + 1, "pending_cleared": True},
        ),
        raw("FENCE_POST", thread_identity=COORDINATOR_THREAD, details={"completion_gate": True}),
    ]
    traces.append(t)

    # 13
    t = deepcopy(base)
    fence_index = next(i for i, item in enumerate(t) if item["event_type"] == "FENCE_POST")
    t.insert(
        fence_index,
        raw(
            "WORKER_REPLACE",
            thread_identity="thread-session-A",
            details={
                "new_worker": WORKER,
                "new_worker_control": "worker-control-B",
                "new_worker_thread": "thread-worker-B",
            },
        ),
    )
    traces.append(t)

    # 14
    t = _prefix(base, "INITIAL_ENTER")
    t.append(raw("PRESTART_ABORT", thread_identity=COORDINATOR_THREAD))
    traces.append(t)

    # 15
    t = _prefix(base, "DISPATCH")
    t += [
        raw("JNI_EXCEPTION", thread_identity=WORKER_THREAD),
        raw(
            "REG_HOOK",
            thread_identity=WORKER_THREAD,
            handle_tag="",
            pending_node_tag="possibly-inserted-node",
            callback_owner_tag="unknown-owner",
            details={"exact_registration": False, "possibly_inserted": True},
        ),
    ]
    traces.append(t)

    # 16
    t = _prefix(base, "WAIT_BEGIN")
    t += [
        raw("DEADLINE", thread_identity=COORDINATOR_THREAD),
        raw("CLEANUP_RETURN", thread_identity=COORDINATOR_THREAD),
        deepcopy(base[12]),
        deepcopy(base[13]),
        deepcopy(base[14]),
    ]
    traces.append(t)

    # 17
    t = _prefix(base, "FENCE_POST")
    t.append(raw("FENCE_COMPLETION_LOST", thread_identity=COORDINATOR_THREAD))
    traces.append(t)

    # 18
    t = _prefix(base, "TASK_POST")
    t.append(raw("LEASE_RELEASE", thread_identity=COORDINATOR_THREAD))
    traces.append(t)

    # 19
    t = _prefix(base, "SDK_ADMIT_ENTER")
    t.append(raw("UNREGISTER_BINDING", thread_identity=COORDINATOR_THREAD))
    traces.append(t)

    # 20
    t = _prefix(base, "DISPATCH")
    t += [raw("DISPATCH", thread_identity=WORKER_THREAD), raw("TRANSPORT_RETRY", thread_identity=WORKER_THREAD)]
    traces.append(t)

    # 21
    t = _prefix(base, "REG_COMPLETE")
    t.append(
        raw(
            "HANDLE_REUSE",
            op_generation=GENERATION + 1,
            handle_tag=HANDLE,
            pending_node_tag="pending-node-generation-42",
            callback_owner_tag="callback-owner-generation-42",
        )
    )
    traces.append(t)

    # 22
    t = deepcopy(base)
    fence_index = next(i for i, item in enumerate(t) if item["event_type"] == "FENCE_POST")
    t.insert(
        fence_index,
        raw(
            "MUTATOR_ENTER",
            thread_identity="thread-mutator-A",
            details={"entry_has_exit_witness": False},
        ),
    )
    traces.append(t)

    # 23
    t = deepcopy(base)
    fence_start_index = next(i for i, item in enumerate(t) if item["event_type"] == "FENCE_START")
    t.insert(
        fence_start_index,
        raw(
            "CONNECTION_MUTATION",
            thread_identity="thread-head-task-A",
            details={"new_connection_epoch": CONNECTION_EPOCH + 1, "head_task_crossed_tail": True},
        ),
    )
    traces.append(t)

    # 24
    t = _prefix(base, "TASK_POST")
    t += [
        raw("PRESTART_ABORT", thread_identity=COORDINATOR_THREAD),
        raw("LEASE_RELEASE", thread_identity=COORDINATOR_THREAD),
    ]
    traces.append(t)

    if len(traces) != len(REJECT_DESCRIPTIONS):
        raise AssertionError("fixture count mismatch")
    return traces


def _default_details() -> dict[str, Any]:
    return {
        "worker_control": WORKER_CONTROL,
        "worker_thread": WORKER_THREAD,
        "route_hash": ROUTE_HASH,
        "owner_identity": OWNER_IDENTITY,
        "logical_identity": LOGICAL_IDENTITY,
    }


def seal_trace(raw_events: list[dict[str, Any]]) -> list[TraceEvent]:
    """Fill the fixed schema and stamp the phase actually reached by each prefix."""
    verifier = QuiescenceVerifier(strict_phase=False)
    result: list[TraceEvent] = []
    for index, partial in enumerate(deepcopy(raw_events), start=1):
        details = _default_details()
        details.update(dict(partial.get("details", {})))
        state = verifier.state
        event = TraceEvent(
            seq=int(partial.get("seq", index)),
            monotonic_ns=int(partial.get("monotonic_ns", index * 1_000)),
            op_generation=int(partial.get("op_generation", GENERATION)),
            phase=state.phase,
            thread_identity=str(partial.get("thread_identity", COORDINATOR_THREAD)),
            worker_identity=str(partial.get("worker_identity", state.current_worker or WORKER)),
            session_epoch=int(
                partial.get(
                    "session_epoch",
                    state.current_session_epoch if state.current_session_epoch >= 0 else SESSION_EPOCH,
                )
            ),
            connection_epoch=int(
                partial.get(
                    "connection_epoch",
                    state.current_connection_epoch if state.current_connection_epoch >= 0 else CONNECTION_EPOCH,
                )
            ),
            handle_tag=str(partial.get("handle_tag", state.returned_handle or HANDLE)),
            pending_node_tag=str(partial.get("pending_node_tag", state.pending_node or PENDING_NODE)),
            callback_owner_tag=str(partial.get("callback_owner_tag", state.callback_owner or CALLBACK_OWNER)),
            event_type=str(partial["event_type"]),
            before_count=int(partial.get("before_count", 0)),
            after_count=int(partial.get("after_count", 0)),
            coverage_latches=tuple(partial.get("coverage_latches", ())),
            details=details,
        )
        report = verifier.consume(event)
        stamped = replace(event, phase=report.phase)
        result.append(stamped)
    return result


def minimal_accept_trace() -> list[TraceEvent]:
    return seal_trace(minimal_accept_raw())


def rejected_traces() -> list[list[TraceEvent]]:
    return [seal_trace(items) for items in rejected_raw_traces()]


def trace_to_json_value(trace: list[TraceEvent]) -> dict[str, Any]:
    return {
        "schema": "finduas-ridq-trace/v1",
        "events": [event.to_dict() for event in trace],
    }
