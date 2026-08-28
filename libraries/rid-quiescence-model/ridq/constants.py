"""Closed vocabulary for the offline quiescence trace model."""

from enum import IntEnum


SCHEMA = "finduas-ridq-trace/v1"
MODEL_VERSION = "0.1.1"
FIXED_PROFILE = "LAB_SINGLE_SHOT"
FIXED_TRANSPORT_RETRY = 0


EVENT_INTEGER_FIELDS = (
    "seq",
    "monotonic_ns",
    "op_generation",
    "session_epoch",
    "connection_epoch",
    "before_count",
    "after_count",
)


EVENT_STRING_FIELDS = (
    "phase",
    "thread_identity",
    "worker_identity",
    "handle_tag",
    "pending_node_tag",
    "callback_owner_tag",
    "event_type",
)


# `details` remains extensible only through this closed, exactly typed table.  In particular,
# Python bool values are not integers for this schema even though bool subclasses int.
DETAIL_FIELD_TYPES = (
    ("active_mutators", "int"),
    ("after_callback_and_remove", "bool"),
    ("callback_path_covered", "bool"),
    ("completion_gate", "bool"),
    ("core_post_attempted", "bool"),
    ("entry_has_exit_witness", "bool"),
    ("exact_registration", "bool"),
    ("exact_worker_witness", "bool"),
    ("head_task_crossed_tail", "bool"),
    ("helper_callback_inflight", "int"),
    ("in_callback", "bool"),
    ("independent_owner_witness", "bool"),
    ("logical_identity", "str"),
    ("mapping_and_binding_process_lifetime", "bool"),
    ("membership_positive", "bool"),
    ("new_connection_epoch", "int"),
    ("new_logical_identity", "str"),
    ("new_owner_identity", "str"),
    ("new_route_hash", "str"),
    ("new_session_epoch", "int"),
    ("new_worker", "str"),
    ("new_worker_control", "str"),
    ("new_worker_thread", "str"),
    ("owner_copied_before_increment", "bool"),
    ("owner_copies", "int"),
    ("owner_identity", "str"),
    ("payload_valid", "bool"),
    ("pending_absent", "bool"),
    ("pending_cleared", "bool"),
    ("possibly_inserted", "bool"),
    ("profile", "str"),
    ("protocol_ok", "bool"),
    ("registration_generation", "int"),
    ("request_fingerprint_match", "bool"),
    ("route_hash", "str"),
    ("same_stopper_mutex", "bool"),
    ("sdk_callback_admitted", "int"),
    ("stopper_absent", "bool"),
    ("stopper_remove_before_core_post", "bool"),
    ("transport_retry", "int"),
    ("worker_control", "str"),
    ("worker_thread", "str"),
    ("zero_dispatch_exit", "bool"),
)


STATES = (
    "Q0_DORMANT",
    "Q1_PREFLIGHT",
    "Q2_MAPPING_RETAINED",
    "Q3_TASK_QUEUED",
    "Q4_REGISTERING",
    "Q5_REGISTERED",
    "Q6_WAIT_TERMINAL",
    "Q7_TERMINAL_RECORDED",
    "Q8_FENCE_QUEUED",
    "Q9_FENCE_RUNNING",
    "QC_CANCEL_REQUIRED",
    "QC_CANCEL_POSTED",
    "QC_CANCEL_FENCE_QUEUED",
    "QC_CANCEL_FENCE_RUNNING",
    "QA_PRESTART_ABORTED",
    "QS_QUIESCENT_VALID_RESPONSE",
    "QF_NOT_ADMITTED",
    "QF_QUIESCENT_REJECTED",
    "QF_QUIESCENT_CANCELLED",
    "QF_ABORTED_NO_DISPATCH",
    "QX_UNKNOWN_RETAINED",
)


PREFIX_CLASSES = (
    "ACTIVE",
    "QUIESCENT_REJECTED",
    "UNKNOWN_RETAINED",
)


INVARIANTS = (
    "I01_MONOTONIC_PHASE",
    "I02_ONE_GENERATION",
    "I03_ONE_DISPATCH",
    "I04_NO_TRANSPORT_RETRY",
    "I05_ONE_CANCEL",
    "I06_REG_BEFORE_WAIT",
    "I07_NO_EARLY_CALLBACK",
    "I08_BALANCED_SDK_ADMISSION",
    "I09_BALANCED_HELPER_INFLIGHT",
    "I10_FIRST_WINNER_IMMUTABLE",
    "I11_HANDLE_GENERATION_MATCH",
    "I12_FENCE_EXTERNAL_POST",
    "I13_FENCE_AFTER_TERMINAL",
    "I14_EXACT_ABSENCE",
    "I15_ZERO_INFLIGHT_AT_FENCE",
    "I16_STABLE_SESSION",
    "I17_STABLE_CONNECTION",
    "I18_STABLE_ROUTE",
    "I19_COVERAGE_CLEAN",
    "I20_MAPPING_BEFORE_POINTER_ESCAPE",
    "I21_STATE_NOT_FREED_EARLY",
    "I22_CANCEL_NEVER_SUCCESS",
    "I23_RESULT_ONLY_AT_FENCE",
    "I24_NO_REENTRY",
    "I25_TERMINAL_FREEZE",
)


class FailureCode(IntEnum):
    Q_QUIESCENT_VALID_RESPONSE = 0

    Q_IDENTITY_UNPROVEN = 1001
    Q_EXCEPTION_BOUNDARY_UNPROVEN = 1002
    Q_MAPPING_LEASE_UNAVAILABLE = 1003
    Q_WORKER_IDENTITY_UNPROVEN = 1004
    Q_SESSION_HOOK_COVERAGE_UNPROVEN = 1005
    Q_CONNECTION_HOOK_COVERAGE_UNPROVEN = 1006
    Q_PENDING_WITNESS_UNAVAILABLE = 1007
    Q_STOPPER_WITNESS_UNAVAILABLE = 1008
    Q_FENCE_CARRIER_UNPROVEN = 1009
    Q_NATIVE_BINDING_LEASE_UNPROVEN = 1010

    Q_INITIAL_TASK_POST_FAILED = 1101
    Q_PRESTART_ABORT_UNDRAINED = 1102
    Q_REGISTRATION_STUCK = 1103
    Q_DISPATCH_CARDINALITY = 1104
    Q_TRANSPORT_RETRY_OBSERVED = 1105
    Q_ZERO_OR_UNKNOWN_HANDLE = 1106
    Q_REGISTRATION_UNPROVEN = 1107
    Q_PENDING_NOT_PRESENT_AFTER_REG = 1108
    Q_STOPPER_NOT_PRESENT_AFTER_REG = 1109
    Q_CALLBACK_BEFORE_REGISTRATION = 1110
    Q_NEW_GLOBAL_REF_UNCERTAIN = 1111
    Q_REGISTRATION_EPOCH_CHANGED = 1112

    Q_LOCAL_DEADLINE = 1201
    Q_REMOTE_TIMEOUT = 1202
    Q_MALFORMED_RESPONSE = 1203
    Q_PROTOCOL_REJECTED = 1204
    Q_CALLBACK_HANDLE_MISMATCH = 1205
    Q_CALLBACK_GENERATION_MISMATCH = 1206
    Q_DUPLICATE_CALLBACK = 1207
    Q_CALLBACK_JNI_EXCEPTION = 1208
    Q_CALLBACK_COUNTER_UNBALANCED = 1209
    Q_CALLBACK_THREAD_UNPROVEN = 1210
    Q_AMBIGUOUS_AFTER_CANCEL = 1211

    Q_CANCEL_BEFORE_REGISTRATION = 1301
    Q_CANCEL_CARDINALITY = 1302
    Q_CANCEL_POST_UNPROVEN = 1303
    Q_CANCEL_API_ERROR = 1304
    Q_FENCE_POST_FAILED = 1305
    Q_FENCE_COMPLETION_TIMEOUT = 1306
    Q_PENDING_STILL_PRESENT_OR_UNKNOWN = 1307
    Q_STOPPER_STILL_PRESENT_OR_UNKNOWN = 1308
    Q_SDK_CALLBACK_ADMITTED = 1309
    Q_HELPER_CALLBACK_INFLIGHT = 1310
    Q_SESSION_EPOCH_CHANGED = 1311
    Q_CONNECTION_EPOCH_CHANGED = 1312
    Q_ROUTE_IDENTITY_CHANGED = 1313
    Q_COVERAGE_BROKEN = 1314
    Q_NATIVE_UNREGISTRATION_FAILED = 1315
    Q_MAPPING_RETENTION_LOST = 1316
    Q_OWNER_DESTRUCTION_UNPROVEN = 1317


FAILURE_CODES = tuple((item.name, int(item)) for item in FailureCode)


TRANSITIONS = (
    ("Q0_DORMANT", "Q1_PREFLIGHT"),
    ("Q1_PREFLIGHT", "Q2_MAPPING_RETAINED"),
    ("Q2_MAPPING_RETAINED", "Q3_TASK_QUEUED"),
    ("Q3_TASK_QUEUED", "Q4_REGISTERING"),
    ("Q3_TASK_QUEUED", "QA_PRESTART_ABORTED"),
    ("Q4_REGISTERING", "Q5_REGISTERED"),
    ("Q5_REGISTERED", "Q6_WAIT_TERMINAL"),
    ("Q6_WAIT_TERMINAL", "Q7_TERMINAL_RECORDED"),
    ("Q6_WAIT_TERMINAL", "QC_CANCEL_REQUIRED"),
    ("Q7_TERMINAL_RECORDED", "Q8_FENCE_QUEUED"),
    ("Q8_FENCE_QUEUED", "Q9_FENCE_RUNNING"),
    ("Q9_FENCE_RUNNING", "QS_QUIESCENT_VALID_RESPONSE"),
    ("Q9_FENCE_RUNNING", "QF_QUIESCENT_REJECTED"),
    ("Q9_FENCE_RUNNING", "QX_UNKNOWN_RETAINED"),
    ("QC_CANCEL_REQUIRED", "QC_CANCEL_POSTED"),
    ("QC_CANCEL_POSTED", "QC_CANCEL_FENCE_QUEUED"),
    ("QC_CANCEL_FENCE_QUEUED", "QC_CANCEL_FENCE_RUNNING"),
    ("QC_CANCEL_FENCE_RUNNING", "QF_QUIESCENT_CANCELLED"),
    ("QC_CANCEL_FENCE_RUNNING", "QX_UNKNOWN_RETAINED"),
    ("QA_PRESTART_ABORTED", "QF_ABORTED_NO_DISPATCH"),
)


TERMINAL_STATES = frozenset(
    state for state in STATES if state.startswith(("QS_", "QF_", "QX_"))
)


EVENT_TYPES = (
    "PREFLIGHT_PASS",
    "LEASE_ACQUIRE",
    "BINDING_REGISTER",
    "TASK_POST",
    "INITIAL_ENTER",
    "DISPATCH",
    "REG_HOOK",
    "PENDING_PRESENT",
    "STOPPER_PRESENT",
    "OWNER_BOUND",
    "REG_COMPLETE",
    "WAIT_BEGIN",
    "SDK_ADMIT_ENTER",
    "HELPER_ENTER",
    "RESPONSE_VALID",
    "REMOTE_TIMEOUT",
    "MALFORMED_RESPONSE",
    "PROTOCOL_REJECTED",
    "HELPER_EXIT",
    "STOPPER_ABSENT",
    "SDK_ADMIT_EXIT",
    "PENDING_ABSENT",
    "OWNER_COPY_ACQUIRE",
    "OWNER_COPY_RELEASE",
    "FENCE_POST",
    "FENCE_START",
    "FENCE_SNAPSHOT",
    "DEADLINE",
    "CLEANUP_RETURN",
    "CLEANUP_ORDER_WITNESS",
    "CLEANUP_FENCE_POST",
    "CLEANUP_FENCE_START",
    "PRESTART_ABORT",
    "QUEUED_TASK_EXIT",
    "UNREGISTER_BINDING",
    "LEASE_RELEASE",
    "PROCESS_RETENTION",
    "SESSION_MUTATION",
    "CONNECTION_MUTATION",
    "WORKER_REPLACE",
    "ROUTE_CHANGE",
    "COVERAGE_BREAK",
    "MUTATOR_ENTER",
    "MUTATOR_EXIT",
    "TRANSPORT_RETRY",
    "HANDLE_REUSE",
    "JNI_EXCEPTION",
    "FENCE_COMPLETION_LOST",
    "STATE_DESTROY",
)
