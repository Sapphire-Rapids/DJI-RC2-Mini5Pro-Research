#!/usr/bin/env python3
"""Independent packaged-artifact checks with literal expected tables."""

from __future__ import annotations

import ast
import hashlib
import json
import sys
import zipfile
from pathlib import Path


EXPECTED_STATES = [
    "Q0_DORMANT", "Q1_PREFLIGHT", "Q2_MAPPING_RETAINED", "Q3_TASK_QUEUED",
    "Q4_REGISTERING", "Q5_REGISTERED", "Q6_WAIT_TERMINAL", "Q7_TERMINAL_RECORDED",
    "Q8_FENCE_QUEUED", "Q9_FENCE_RUNNING", "QC_CANCEL_REQUIRED", "QC_CANCEL_POSTED",
    "QC_CANCEL_FENCE_QUEUED", "QC_CANCEL_FENCE_RUNNING", "QA_PRESTART_ABORTED",
    "QS_QUIESCENT_VALID_RESPONSE", "QF_NOT_ADMITTED", "QF_QUIESCENT_REJECTED",
    "QF_QUIESCENT_CANCELLED", "QF_ABORTED_NO_DISPATCH", "QX_UNKNOWN_RETAINED",
]
EXPECTED_PREFIX_CLASSES = ["ACTIVE", "QUIESCENT_REJECTED", "UNKNOWN_RETAINED"]
EXPECTED_EVENT_INTEGER_FIELDS = [
    "seq", "monotonic_ns", "op_generation", "session_epoch", "connection_epoch",
    "before_count", "after_count",
]
EXPECTED_EVENT_STRING_FIELDS = [
    "phase", "thread_identity", "worker_identity", "handle_tag", "pending_node_tag",
    "callback_owner_tag", "event_type",
]
EXPECTED_DETAIL_FIELD_TYPES = [
    ["active_mutators", "int"], ["after_callback_and_remove", "bool"],
    ["callback_path_covered", "bool"], ["completion_gate", "bool"],
    ["core_post_attempted", "bool"], ["entry_has_exit_witness", "bool"],
    ["exact_registration", "bool"], ["exact_worker_witness", "bool"],
    ["head_task_crossed_tail", "bool"], ["helper_callback_inflight", "int"],
    ["in_callback", "bool"], ["independent_owner_witness", "bool"],
    ["logical_identity", "str"], ["mapping_and_binding_process_lifetime", "bool"],
    ["membership_positive", "bool"], ["new_connection_epoch", "int"],
    ["new_logical_identity", "str"], ["new_owner_identity", "str"],
    ["new_route_hash", "str"], ["new_session_epoch", "int"],
    ["new_worker", "str"], ["new_worker_control", "str"],
    ["new_worker_thread", "str"], ["owner_copied_before_increment", "bool"],
    ["owner_copies", "int"], ["owner_identity", "str"], ["payload_valid", "bool"],
    ["pending_absent", "bool"], ["pending_cleared", "bool"],
    ["possibly_inserted", "bool"], ["profile", "str"], ["protocol_ok", "bool"],
    ["registration_generation", "int"], ["request_fingerprint_match", "bool"],
    ["route_hash", "str"], ["same_stopper_mutex", "bool"],
    ["sdk_callback_admitted", "int"], ["stopper_absent", "bool"],
    ["stopper_remove_before_core_post", "bool"], ["transport_retry", "int"],
    ["worker_control", "str"], ["worker_thread", "str"],
    ["zero_dispatch_exit", "bool"],
]
EXPECTED_TRANSITIONS = [
    ["Q0_DORMANT", "Q1_PREFLIGHT"], ["Q1_PREFLIGHT", "Q2_MAPPING_RETAINED"],
    ["Q2_MAPPING_RETAINED", "Q3_TASK_QUEUED"], ["Q3_TASK_QUEUED", "Q4_REGISTERING"],
    ["Q3_TASK_QUEUED", "QA_PRESTART_ABORTED"], ["Q4_REGISTERING", "Q5_REGISTERED"],
    ["Q5_REGISTERED", "Q6_WAIT_TERMINAL"], ["Q6_WAIT_TERMINAL", "Q7_TERMINAL_RECORDED"],
    ["Q6_WAIT_TERMINAL", "QC_CANCEL_REQUIRED"], ["Q7_TERMINAL_RECORDED", "Q8_FENCE_QUEUED"],
    ["Q8_FENCE_QUEUED", "Q9_FENCE_RUNNING"],
    ["Q9_FENCE_RUNNING", "QS_QUIESCENT_VALID_RESPONSE"],
    ["Q9_FENCE_RUNNING", "QF_QUIESCENT_REJECTED"],
    ["Q9_FENCE_RUNNING", "QX_UNKNOWN_RETAINED"],
    ["QC_CANCEL_REQUIRED", "QC_CANCEL_POSTED"],
    ["QC_CANCEL_POSTED", "QC_CANCEL_FENCE_QUEUED"],
    ["QC_CANCEL_FENCE_QUEUED", "QC_CANCEL_FENCE_RUNNING"],
    ["QC_CANCEL_FENCE_RUNNING", "QF_QUIESCENT_CANCELLED"],
    ["QC_CANCEL_FENCE_RUNNING", "QX_UNKNOWN_RETAINED"],
    ["QA_PRESTART_ABORTED", "QF_ABORTED_NO_DISPATCH"],
]
EXPECTED_INVARIANTS = [
    "I01_MONOTONIC_PHASE", "I02_ONE_GENERATION", "I03_ONE_DISPATCH",
    "I04_NO_TRANSPORT_RETRY", "I05_ONE_CANCEL", "I06_REG_BEFORE_WAIT",
    "I07_NO_EARLY_CALLBACK", "I08_BALANCED_SDK_ADMISSION", "I09_BALANCED_HELPER_INFLIGHT",
    "I10_FIRST_WINNER_IMMUTABLE", "I11_HANDLE_GENERATION_MATCH", "I12_FENCE_EXTERNAL_POST",
    "I13_FENCE_AFTER_TERMINAL", "I14_EXACT_ABSENCE", "I15_ZERO_INFLIGHT_AT_FENCE",
    "I16_STABLE_SESSION", "I17_STABLE_CONNECTION", "I18_STABLE_ROUTE",
    "I19_COVERAGE_CLEAN", "I20_MAPPING_BEFORE_POINTER_ESCAPE", "I21_STATE_NOT_FREED_EARLY",
    "I22_CANCEL_NEVER_SUCCESS", "I23_RESULT_ONLY_AT_FENCE", "I24_NO_REENTRY",
    "I25_TERMINAL_FREEZE",
]
EXPECTED_FAILURE_CODES = [
    ["Q_QUIESCENT_VALID_RESPONSE", 0],
    ["Q_IDENTITY_UNPROVEN", 1001], ["Q_EXCEPTION_BOUNDARY_UNPROVEN", 1002],
    ["Q_MAPPING_LEASE_UNAVAILABLE", 1003], ["Q_WORKER_IDENTITY_UNPROVEN", 1004],
    ["Q_SESSION_HOOK_COVERAGE_UNPROVEN", 1005], ["Q_CONNECTION_HOOK_COVERAGE_UNPROVEN", 1006],
    ["Q_PENDING_WITNESS_UNAVAILABLE", 1007], ["Q_STOPPER_WITNESS_UNAVAILABLE", 1008],
    ["Q_FENCE_CARRIER_UNPROVEN", 1009], ["Q_NATIVE_BINDING_LEASE_UNPROVEN", 1010],
    ["Q_INITIAL_TASK_POST_FAILED", 1101], ["Q_PRESTART_ABORT_UNDRAINED", 1102],
    ["Q_REGISTRATION_STUCK", 1103], ["Q_DISPATCH_CARDINALITY", 1104],
    ["Q_TRANSPORT_RETRY_OBSERVED", 1105], ["Q_ZERO_OR_UNKNOWN_HANDLE", 1106],
    ["Q_REGISTRATION_UNPROVEN", 1107], ["Q_PENDING_NOT_PRESENT_AFTER_REG", 1108],
    ["Q_STOPPER_NOT_PRESENT_AFTER_REG", 1109], ["Q_CALLBACK_BEFORE_REGISTRATION", 1110],
    ["Q_NEW_GLOBAL_REF_UNCERTAIN", 1111], ["Q_REGISTRATION_EPOCH_CHANGED", 1112],
    ["Q_LOCAL_DEADLINE", 1201], ["Q_REMOTE_TIMEOUT", 1202],
    ["Q_MALFORMED_RESPONSE", 1203], ["Q_PROTOCOL_REJECTED", 1204],
    ["Q_CALLBACK_HANDLE_MISMATCH", 1205], ["Q_CALLBACK_GENERATION_MISMATCH", 1206],
    ["Q_DUPLICATE_CALLBACK", 1207], ["Q_CALLBACK_JNI_EXCEPTION", 1208],
    ["Q_CALLBACK_COUNTER_UNBALANCED", 1209], ["Q_CALLBACK_THREAD_UNPROVEN", 1210],
    ["Q_AMBIGUOUS_AFTER_CANCEL", 1211], ["Q_CANCEL_BEFORE_REGISTRATION", 1301],
    ["Q_CANCEL_CARDINALITY", 1302], ["Q_CANCEL_POST_UNPROVEN", 1303],
    ["Q_CANCEL_API_ERROR", 1304], ["Q_FENCE_POST_FAILED", 1305],
    ["Q_FENCE_COMPLETION_TIMEOUT", 1306], ["Q_PENDING_STILL_PRESENT_OR_UNKNOWN", 1307],
    ["Q_STOPPER_STILL_PRESENT_OR_UNKNOWN", 1308], ["Q_SDK_CALLBACK_ADMITTED", 1309],
    ["Q_HELPER_CALLBACK_INFLIGHT", 1310], ["Q_SESSION_EPOCH_CHANGED", 1311],
    ["Q_CONNECTION_EPOCH_CHANGED", 1312], ["Q_ROUTE_IDENTITY_CHANGED", 1313],
    ["Q_COVERAGE_BROKEN", 1314], ["Q_NATIVE_UNREGISTRATION_FAILED", 1315],
    ["Q_MAPPING_RETENTION_LOST", 1316], ["Q_OWNER_DESTRUCTION_UNPROVEN", 1317],
]
EXPECTED_ENTRIES = {
    "__main__.py", "model_manifest.json", "ridq/__init__.py", "ridq/__main__.py",
    "ridq/constants.py", "ridq/fixtures.py", "ridq/model.py",
}
ALLOWED_IMPORT_ROOTS = {
    "__future__", "argparse", "copy", "dataclasses", "enum", "json", "pathlib", "sys", "typing",
    "constants", "fixtures", "model",
}
FORBIDDEN_BYTES = (
    b"JNIRawData", b"native_SendData", b"native_CancelSend", b"CancleSendData",
    b"dlopen", b"ctypes", b"cffi", b"android.os.IBinder", b"/dev/", b"127.0.0.1",
)
FORBIDDEN_CALL_NAMES = {"connect", "recv", "send", "system", "popen", "fork", "execve", "CDLL"}


def fail(message: str) -> None:
    raise SystemExit(f"AUDIT FAIL: {message}")


def audit(path: Path) -> None:
    data = path.read_bytes()
    if data.startswith(b"\x7fELF") or b"dex\n" in data:
        fail("native or DEX payload detected")
    for needle in FORBIDDEN_BYTES:
        if needle in data:
            fail(f"forbidden packaged token: {needle!r}")

    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        if names != EXPECTED_ENTRIES:
            fail(f"entry set mismatch: {sorted(names ^ EXPECTED_ENTRIES)}")
        if any(name.endswith((".so", ".dex", ".class", ".pyc")) for name in names):
            fail("executable native/bytecode entry detected")
        for info in archive.infolist():
            if info.date_time != (1980, 1, 1, 0, 0, 0) or info.compress_type != zipfile.ZIP_STORED:
                fail(f"non-reproducible ZIP metadata for {info.filename}")

        manifest = json.loads(archive.read("model_manifest.json"))
        if manifest.get("artifact_schema") != "finduas-ridq-model-artifact/v1":
            fail("artifact schema mismatch")
        if manifest.get("model_version") != "0.1.1":
            fail("model version mismatch")
        if manifest.get("fixed_profile") != "LAB_SINGLE_SHOT":
            fail("profile is not fixed")
        if manifest.get("fixed_transport_retry") != 0:
            fail("transport retry is not fixed to zero")
        if manifest.get("states") != EXPECTED_STATES:
            fail("state table mismatch")
        if manifest.get("transitions") != EXPECTED_TRANSITIONS:
            fail("transition table mismatch")
        if manifest.get("prefix_classes") != EXPECTED_PREFIX_CLASSES:
            fail("prefix classifier vocabulary mismatch")
        if manifest.get("event_integer_fields") != EXPECTED_EVENT_INTEGER_FIELDS:
            fail("integer event-field schema mismatch")
        if manifest.get("event_string_fields") != EXPECTED_EVENT_STRING_FIELDS:
            fail("string event-field schema mismatch")
        if manifest.get("detail_field_types") != EXPECTED_DETAIL_FIELD_TYPES:
            fail("details field schema mismatch")
        if manifest.get("invariants") != EXPECTED_INVARIANTS:
            fail("invariant table mismatch")
        if manifest.get("failure_codes") != EXPECTED_FAILURE_CODES:
            fail("failure-code table mismatch")

        digest = hashlib.sha256()
        for name in sorted(item for item in names if item.startswith("ridq/") and item.endswith(".py")):
            source = archive.read(name)
            digest.update(name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(source)
            digest.update(b"\0")
            tree = ast.parse(source, filename=name)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots = {alias.name.split(".", 1)[0] for alias in node.names}
                    if not roots <= ALLOWED_IMPORT_ROOTS:
                        fail(f"unapproved import in {name}: {sorted(roots)}")
                elif isinstance(node, ast.ImportFrom):
                    root = (node.module or "").split(".", 1)[0]
                    if node.level == 0 and root not in ALLOWED_IMPORT_ROOTS:
                        fail(f"unapproved from-import in {name}: {root}")
                elif isinstance(node, ast.Call):
                    called = None
                    if isinstance(node.func, ast.Name):
                        called = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        called = node.func.attr
                    if called in FORBIDDEN_CALL_NAMES:
                        fail(f"forbidden callable in {name}: {called}")
        if digest.hexdigest() != manifest.get("source_set_sha256"):
            fail("source-set digest mismatch")

    print(f"AUDIT PASS: {path}")
    print(f"SHA-256 {hashlib.sha256(data).hexdigest()}")
    print(f"SOURCE-SET SHA-256 {manifest['source_set_sha256']}")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: audit_artifact.py ARTIFACT", file=sys.stderr)
        return 2
    audit(Path(argv[1]).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
