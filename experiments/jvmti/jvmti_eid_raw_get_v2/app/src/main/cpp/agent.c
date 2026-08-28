#include <android/log.h>
#include <jni.h>
#include <jvmti.h>
#include <pthread.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdatomic.h>

#include "jni_bridge.h"
#include "route_snapshot.h"
#include "state.h"

#if !defined(__aarch64__)
#error "FindUAS EID raw GET V2 must be built for AArch64"
#endif

#define FINDUAS_LOG_TAG "FindUAS-EID-Raw-Get-V2"
#define FINDUAS_MAX_LOADED_CLASSES 200000

static const char kEidOnAnchor[] =
    "Lcom/uav/flymodel/generated/impl/flight/regulation/"
    "RemoteIDModelImpl$electronicIDBroadcastOn$2$1;";
static const char kEidGateAnchor[] =
    "Lcom/uav/flymodel/generated/impl/flight/regulation/"
    "RemoteIDModelImpl$electronicIDBroadcastExisted$2$1;";
static const char kRawDataClass[] = "Luav/raw/jni/JNIRawData;";
static const char kSendInterfaceClass[] = "Luav/raw/jni/callback/SendInterface;";

enum AgentError {
    AGENT_ERROR_NONE = 0,
    AGENT_ERROR_OPTIONS_NOT_EMPTY = 1,
    AGENT_ERROR_ALREADY_ATTACHED = 2,
    AGENT_ERROR_VM_UNAVAILABLE = 3,
    AGENT_ERROR_JVMTI_ENV_UNAVAILABLE = 4,
    AGENT_ERROR_JNI_ENV_UNAVAILABLE = 5,
    AGENT_ERROR_STATE_INIT = 6,
    AGENT_ERROR_PENDING_JNI_EXCEPTION = 7,
    AGENT_ERROR_CLASS_ENUMERATION = 8,
    AGENT_ERROR_CLASS_COUNT_RANGE = 9,
    AGENT_ERROR_CLASS_SIGNATURE = 10,
    AGENT_ERROR_CLASS_GLOBAL_REF = 11,
    AGENT_ERROR_CLASS_LOADER = 12,
    AGENT_ERROR_DEALLOCATION = 13,
    AGENT_ERROR_TARGET_CARDINALITY = 14,
    AGENT_ERROR_LOADER_IDENTITY = 15,
    AGENT_ERROR_RAW_CLASS_STATUS = 16,
    AGENT_ERROR_INTERFACE_CLASS_STATUS = 17,
    AGENT_ERROR_ROUTE_UNRESOLVED = 18,
    AGENT_ERROR_ROUTE_EPOCH = 19,
    AGENT_ERROR_JVMTI_DISPOSAL = 20,
    AGENT_ERROR_BRIDGE_BASE = 100,
};

typedef struct TargetSet {
    jint loaded_count;
    jint on_anchor_count;
    jint gate_anchor_count;
    jint raw_data_count;
    jint send_interface_count;
    jint unique_anchor_loader_count;
    jclass on_anchor;
    jclass gate_anchor;
    jclass raw_data;
    jclass send_interface;
    jobject on_loader;
    jobject gate_loader;
    jobject raw_loader;
    jobject interface_loader;
    int raw_initialized;
} TargetSet;

static atomic_bool g_ever_attached = ATOMIC_VAR_INIT(false);
static pthread_once_t g_attempt_once = PTHREAD_ONCE_INIT;
static AttemptState g_attempt;
static int g_attempt_init_error = -1;

static void initialize_attempt_once(void) {
    g_attempt_init_error = attempt_state_init(&g_attempt);
}

static int exact_text_equal(const char *left, const char *right) {
    if (left == NULL || right == NULL) {
        return 0;
    }
    while (*left != '\0' && *right != '\0') {
        if (*left != *right) {
            return 0;
        }
        ++left;
        ++right;
    }
    return *left == '\0' && *right == '\0';
}

static void set_error_once(enum AgentError *error, enum AgentError candidate) {
    if (*error == AGENT_ERROR_NONE) {
        *error = candidate;
    }
}

static int clear_owned_exception(JNIEnv *jni) {
    if ((*jni)->ExceptionCheck(jni) == JNI_TRUE) {
        (*jni)->ExceptionClear(jni);
        return 1;
    }
    return 0;
}

static int keep_class(JNIEnv *jni, jclass source, jclass *destination) {
    if (*destination != NULL) {
        return 1;
    }
    *destination = (jclass)(*jni)->NewGlobalRef(jni, source);
    return *destination != NULL && !clear_owned_exception(jni);
}

static int keep_loader(
    JNIEnv *jni,
    jvmtiEnv *jvmti,
    jclass source,
    jobject *destination) {
    if (*destination != NULL) {
        return 1;
    }
    jobject loader_local = NULL;
    if ((*jvmti)->GetClassLoader(jvmti, source, &loader_local) != JVMTI_ERROR_NONE ||
        loader_local == NULL) {
        return 0;
    }
    *destination = (*jni)->NewGlobalRef(jni, loader_local);
    (*jni)->DeleteLocalRef(jni, loader_local);
    return *destination != NULL && !clear_owned_exception(jni);
}

static void release_targets(JNIEnv *jni, TargetSet *targets) {
    jobject references[] = {
        targets->on_anchor,
        targets->gate_anchor,
        targets->raw_data,
        targets->send_interface,
        targets->on_loader,
        targets->gate_loader,
        targets->raw_loader,
        targets->interface_loader,
    };
    const size_t reference_count = sizeof(references) / sizeof(references[0]);
    for (size_t index = 0; index < reference_count; ++index) {
        if (references[index] != NULL) {
            (*jni)->DeleteGlobalRef(jni, references[index]);
        }
    }
}

static enum AgentError discover_targets(JNIEnv *jni, jvmtiEnv *jvmti, TargetSet *targets) {
    enum AgentError error = AGENT_ERROR_NONE;
    jclass *classes = NULL;

    if ((*jvmti)->GetLoadedClasses(jvmti, &targets->loaded_count, &classes) != JVMTI_ERROR_NONE) {
        targets->loaded_count = 0;
        return AGENT_ERROR_CLASS_ENUMERATION;
    }
    if (targets->loaded_count < 0 ||
        (targets->loaded_count > 0 && classes == NULL)) {
        error = AGENT_ERROR_CLASS_ENUMERATION;
    } else if (targets->loaded_count > FINDUAS_MAX_LOADED_CLASSES) {
        error = AGENT_ERROR_CLASS_COUNT_RANGE;
    }

    const bool inspect = error == AGENT_ERROR_NONE;
    for (jint index = 0; index < targets->loaded_count; ++index) {
        if (inspect) {
            char *signature = NULL;
            const jvmtiError signature_error =
                (*jvmti)->GetClassSignature(jvmti, classes[index], &signature, NULL);
            if (signature_error != JVMTI_ERROR_NONE || signature == NULL) {
                signature = NULL;
                set_error_once(&error, AGENT_ERROR_CLASS_SIGNATURE);
            } else {
                if (exact_text_equal(signature, kEidOnAnchor)) {
                    ++targets->on_anchor_count;
                    if (!keep_class(jni, classes[index], &targets->on_anchor)) {
                        set_error_once(&error, AGENT_ERROR_CLASS_GLOBAL_REF);
                    }
                    if (!keep_loader(jni, jvmti, classes[index], &targets->on_loader)) {
                        set_error_once(&error, AGENT_ERROR_CLASS_LOADER);
                    }
                } else if (exact_text_equal(signature, kEidGateAnchor)) {
                    ++targets->gate_anchor_count;
                    if (!keep_class(jni, classes[index], &targets->gate_anchor)) {
                        set_error_once(&error, AGENT_ERROR_CLASS_GLOBAL_REF);
                    }
                    if (!keep_loader(jni, jvmti, classes[index], &targets->gate_loader)) {
                        set_error_once(&error, AGENT_ERROR_CLASS_LOADER);
                    }
                } else if (exact_text_equal(signature, kRawDataClass)) {
                    ++targets->raw_data_count;
                    if (!keep_class(jni, classes[index], &targets->raw_data)) {
                        set_error_once(&error, AGENT_ERROR_CLASS_GLOBAL_REF);
                    }
                    if (!keep_loader(jni, jvmti, classes[index], &targets->raw_loader)) {
                        set_error_once(&error, AGENT_ERROR_CLASS_LOADER);
                    }
                } else if (exact_text_equal(signature, kSendInterfaceClass)) {
                    ++targets->send_interface_count;
                    if (!keep_class(jni, classes[index], &targets->send_interface)) {
                        set_error_once(&error, AGENT_ERROR_CLASS_GLOBAL_REF);
                    }
                    if (!keep_loader(jni, jvmti, classes[index], &targets->interface_loader)) {
                        set_error_once(&error, AGENT_ERROR_CLASS_LOADER);
                    }
                }

                if ((*jvmti)->Deallocate(jvmti, (unsigned char *)signature) != JVMTI_ERROR_NONE) {
                    set_error_once(&error, AGENT_ERROR_DEALLOCATION);
                }
            }
        }
        (*jni)->DeleteLocalRef(jni, classes[index]);
    }

    if (classes != NULL &&
        (*jvmti)->Deallocate(jvmti, (unsigned char *)classes) != JVMTI_ERROR_NONE) {
        set_error_once(&error, AGENT_ERROR_DEALLOCATION);
    }
    if (clear_owned_exception(jni)) {
        set_error_once(&error, AGENT_ERROR_PENDING_JNI_EXCEPTION);
    }
    if (error != AGENT_ERROR_NONE) {
        return error;
    }

    if (targets->on_anchor_count != 1 || targets->gate_anchor_count != 1 ||
        targets->raw_data_count != 1 || targets->send_interface_count != 1 ||
        targets->on_anchor == NULL || targets->gate_anchor == NULL ||
        targets->raw_data == NULL || targets->send_interface == NULL) {
        return AGENT_ERROR_TARGET_CARDINALITY;
    }
    if (targets->on_loader == NULL || targets->gate_loader == NULL ||
        targets->raw_loader == NULL || targets->interface_loader == NULL ||
        (*jni)->IsSameObject(jni, targets->on_loader, targets->gate_loader) != JNI_TRUE ||
        (*jni)->IsSameObject(jni, targets->on_loader, targets->raw_loader) != JNI_TRUE ||
        (*jni)->IsSameObject(jni, targets->on_loader, targets->interface_loader) != JNI_TRUE) {
        targets->unique_anchor_loader_count = 0;
        return AGENT_ERROR_LOADER_IDENTITY;
    }
    targets->unique_anchor_loader_count = 1;

    jint raw_status = 0;
    if ((*jvmti)->GetClassStatus(jvmti, targets->raw_data, &raw_status) != JVMTI_ERROR_NONE ||
        (raw_status & JVMTI_CLASS_STATUS_INITIALIZED) == 0) {
        return AGENT_ERROR_RAW_CLASS_STATUS;
    }
    targets->raw_initialized = 1;

    jint interface_status = 0;
    if ((*jvmti)->GetClassStatus(jvmti, targets->send_interface, &interface_status) !=
            JVMTI_ERROR_NONE ||
        (interface_status & JVMTI_CLASS_STATUS_PREPARED) == 0) {
        return AGENT_ERROR_INTERFACE_CLASS_STATUS;
    }
    return AGENT_ERROR_NONE;
}

static void emit_result(
    enum AgentError error,
    enum RouteStatus route_status,
    enum BridgeError bridge_error,
    const TargetSet *targets,
    const AttemptSnapshot *attempt) {
    __android_log_print(
        ANDROID_LOG_INFO,
        FINDUAS_LOG_TAG,
        "FINDUAS_EID_RAW_GET_V2 error_code=%d route_status=%d bridge_error=%d "
        "loaded_count=%d on_anchor_count=%d gate_anchor_count=%d raw_data_count=%d "
        "send_interface_count=%d unique_loader_count=%d raw_initialized=%d "
        "send_call_count=%u callback_count=%u duplicate_count=%u cancel_call_count=%u "
        "terminal=%d handle_nonzero=%d callback_handle_present=%d handle_match=%d "
        "payload_len=%d protocol_result=%d state=%d",
        (int)error,
        (int)route_status,
        (int)bridge_error,
        (int)targets->loaded_count,
        (int)targets->on_anchor_count,
        (int)targets->gate_anchor_count,
        (int)targets->raw_data_count,
        (int)targets->send_interface_count,
        (int)targets->unique_anchor_loader_count,
        targets->raw_initialized,
        attempt->send_call_count,
        attempt->callback_count,
        attempt->duplicate_count,
        attempt->cancel_call_count,
        (int)attempt->terminal,
        attempt->returned_handle_nonzero,
        attempt->callback_handle_present,
        attempt->handle_match,
        attempt->payload_len,
        attempt->protocol_result,
        attempt->state);
}

JNIEXPORT jint JNICALL Agent_OnAttach(JavaVM *vm, char *options, void *reserved) {
    (void)reserved;

    enum AgentError error = AGENT_ERROR_NONE;
    enum RouteStatus route_status = ROUTE_STATUS_UNRESOLVED;
    enum BridgeError bridge_error = BRIDGE_ERROR_NONE;
    TargetSet targets = {
        0, 0, 0, 0, 0, 0,
        NULL, NULL, NULL, NULL,
        NULL, NULL, NULL, NULL,
        0};
    RouteSnapshot route = {0, 0, 0, 0, 0, 0, false, false, false};
    AttemptSnapshot attempt_snapshot = {
        0u, 0u, 0u, 0u, ATTEMPT_TERMINAL_NONE, 0, 0, 0, -1, -1, -1};
    jvmtiEnv *jvmti = NULL;
    JNIEnv *jni = NULL;

    bool expected = false;
    if (!atomic_compare_exchange_strong_explicit(
            &g_ever_attached,
            &expected,
            true,
            memory_order_acq_rel,
            memory_order_acquire)) {
        error = AGENT_ERROR_ALREADY_ATTACHED;
        emit_result(error, route_status, bridge_error, &targets, &attempt_snapshot);
        return JNI_ERR;
    }
    if (options != NULL && options[0] != '\0') {
        error = AGENT_ERROR_OPTIONS_NOT_EMPTY;
        emit_result(error, route_status, bridge_error, &targets, &attempt_snapshot);
        return JNI_ERR;
    }
    if (vm == NULL) {
        error = AGENT_ERROR_VM_UNAVAILABLE;
        emit_result(error, route_status, bridge_error, &targets, &attempt_snapshot);
        return JNI_ERR;
    }

    (void)pthread_once(&g_attempt_once, initialize_attempt_once);
    if (g_attempt_init_error != 0) {
        error = AGENT_ERROR_STATE_INIT;
        emit_result(error, route_status, bridge_error, &targets, &attempt_snapshot);
        return JNI_ERR;
    }
    attempt_snapshot = attempt_state_snapshot(&g_attempt);

    if ((*vm)->GetEnv(vm, (void **)&jvmti, JVMTI_VERSION_1_2) != JNI_OK || jvmti == NULL) {
        error = AGENT_ERROR_JVMTI_ENV_UNAVAILABLE;
        goto finish;
    }
    if ((*vm)->GetEnv(vm, (void **)&jni, JNI_VERSION_1_6) != JNI_OK || jni == NULL) {
        error = AGENT_ERROR_JNI_ENV_UNAVAILABLE;
        goto dispose_environment;
    }
    if (clear_owned_exception(jni)) {
        error = AGENT_ERROR_PENDING_JNI_EXCEPTION;
        goto dispose_environment;
    }

    error = discover_targets(jni, jvmti, &targets);
    if (error != AGENT_ERROR_NONE) {
        goto release_targets;
    }

    route_status = route_snapshot_resolve(&route);
    if (route_status != ROUTE_STATUS_RESOLVED) {
        error = AGENT_ERROR_ROUTE_UNRESOLVED;
        goto release_targets;
    }
    if (!route_snapshot_epoch_unchanged(&route)) {
        error = AGENT_ERROR_ROUTE_EPOCH;
        goto release_targets;
    }

    bridge_error = jni_bridge_send_once(
        jni,
        jvmti,
        targets.on_loader,
        targets.raw_data,
        targets.send_interface,
        &route,
        &g_attempt);
    if (bridge_error != BRIDGE_ERROR_NONE) {
        error = (enum AgentError)(AGENT_ERROR_BRIDGE_BASE + (int)bridge_error);
    }

release_targets:
    attempt_snapshot = attempt_state_snapshot(&g_attempt);
    release_targets(jni, &targets);
    if (clear_owned_exception(jni)) {
        set_error_once(&error, AGENT_ERROR_PENDING_JNI_EXCEPTION);
    }

dispose_environment:
    if ((*jvmti)->DisposeEnvironment(jvmti) != JVMTI_ERROR_NONE) {
        set_error_once(&error, AGENT_ERROR_JVMTI_DISPOSAL);
    }

finish:
    emit_result(error, route_status, bridge_error, &targets, &attempt_snapshot);
    return error == AGENT_ERROR_NONE ? JNI_OK : JNI_ERR;
}
