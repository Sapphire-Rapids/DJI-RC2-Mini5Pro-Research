#include <android/log.h>
#include <jni.h>
#include <jvmti.h>
#include <stddef.h>
#include <stdatomic.h>
#include <stdint.h>
#include <string.h>

#include "route_resolver.h"

#if !defined(__aarch64__)
#error "FindUAS EID route resolver V2.1 must be built for AArch64"
#endif

#define FINDUAS_LOG_TAG "FindUAS-EID-Route-V21"
#define FINDUAS_MAX_LOADED_CLASSES 200000

static const char kEidOnAnchor[] =
    "Lcom/uav/flymodel/generated/impl/flight/regulation/"
    "RemoteIDModelImpl$electronicIDBroadcastOn$2$1;";
static const char kEidGateAnchor[] =
    "Lcom/uav/flymodel/generated/impl/flight/regulation/"
    "RemoteIDModelImpl$electronicIDBroadcastExisted$2$1;";

enum FinduasAgentError {
    FINDUAS_AGENT_ERROR_NONE = 0,
    FINDUAS_AGENT_ERROR_OPTIONS_NOT_EMPTY = 1,
    FINDUAS_AGENT_ERROR_ALREADY_ATTACHED = 2,
    FINDUAS_AGENT_ERROR_VM_UNAVAILABLE = 3,
    FINDUAS_AGENT_ERROR_JVMTI_UNAVAILABLE = 4,
    FINDUAS_AGENT_ERROR_JNI_UNAVAILABLE = 5,
    FINDUAS_AGENT_ERROR_PENDING_EXCEPTION = 6,
    FINDUAS_AGENT_ERROR_CLASS_ENUMERATION = 7,
    FINDUAS_AGENT_ERROR_CLASS_COUNT_RANGE = 8,
    FINDUAS_AGENT_ERROR_CLASS_SIGNATURE = 9,
    FINDUAS_AGENT_ERROR_CLASS_LOADER = 10,
    FINDUAS_AGENT_ERROR_GLOBAL_REFERENCE = 11,
    FINDUAS_AGENT_ERROR_DEALLOCATION = 12,
    FINDUAS_AGENT_ERROR_ANCHOR_CARDINALITY = 13,
    FINDUAS_AGENT_ERROR_LOADER_IDENTITY = 14,
    FINDUAS_AGENT_ERROR_ROUTE_NOT_RESOLVED = 15,
    FINDUAS_AGENT_ERROR_JVMTI_DISPOSAL = 16,
};

typedef struct FinduasAnchorResult {
    jint loaded_count;
    jint on_anchor_count;
    jint gate_anchor_count;
    jint unique_loader_count;
    jobject on_loader;
    jobject gate_loader;
} FinduasAnchorResult;

typedef struct FinduasAgentResult {
    enum FinduasAgentError error;
    FinduasAnchorResult anchors;
    FinduasRouteDiagnostic route;
} FinduasAgentResult;

static atomic_bool g_ever_attached = ATOMIC_VAR_INIT(false);

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

static void set_error_once(FinduasAgentResult *result, enum FinduasAgentError error) {
    if (result->error == FINDUAS_AGENT_ERROR_NONE) {
        result->error = error;
    }
}

static int clear_owned_exception(JNIEnv *jni) {
    if ((*jni)->ExceptionCheck(jni) == JNI_TRUE) {
        (*jni)->ExceptionClear(jni);
        return 1;
    }
    return 0;
}

static int capture_loader(
    JNIEnv *jni,
    jvmtiEnv *jvmti,
    jclass target_class,
    jobject *destination) {
    if (*destination != NULL) {
        return 1;
    }
    jobject local_loader = NULL;
    if ((*jvmti)->GetClassLoader(jvmti, target_class, &local_loader) != JVMTI_ERROR_NONE ||
        local_loader == NULL) {
        return 0;
    }
    *destination = (*jni)->NewGlobalRef(jni, local_loader);
    (*jni)->DeleteLocalRef(jni, local_loader);
    return *destination != NULL && !clear_owned_exception(jni);
}

static void release_anchor_loaders(JNIEnv *jni, FinduasAnchorResult *anchors) {
    if (anchors->gate_loader != NULL) {
        (*jni)->DeleteGlobalRef(jni, anchors->gate_loader);
        anchors->gate_loader = NULL;
    }
    if (anchors->on_loader != NULL) {
        (*jni)->DeleteGlobalRef(jni, anchors->on_loader);
        anchors->on_loader = NULL;
    }
}

static enum FinduasAgentError discover_exact_anchors(
    JNIEnv *jni,
    jvmtiEnv *jvmti,
    FinduasAnchorResult *anchors) {
    jclass *classes = NULL;
    if ((*jvmti)->GetLoadedClasses(jvmti, &anchors->loaded_count, &classes) !=
            JVMTI_ERROR_NONE) {
        anchors->loaded_count = 0;
        return FINDUAS_AGENT_ERROR_CLASS_ENUMERATION;
    }
    if (anchors->loaded_count < 0 ||
        (anchors->loaded_count > 0 && classes == NULL)) {
        return FINDUAS_AGENT_ERROR_CLASS_ENUMERATION;
    }

    enum FinduasAgentError error = FINDUAS_AGENT_ERROR_NONE;
    const int inspect = anchors->loaded_count <= FINDUAS_MAX_LOADED_CLASSES;
    if (!inspect) {
        error = FINDUAS_AGENT_ERROR_CLASS_COUNT_RANGE;
    }

    for (jint index = 0; index < anchors->loaded_count; ++index) {
        if (inspect) {
            char *signature = NULL;
            const jvmtiError signature_error =
                (*jvmti)->GetClassSignature(jvmti, classes[index], &signature, NULL);
            if (signature_error != JVMTI_ERROR_NONE || signature == NULL) {
                signature = NULL;
                if (error == FINDUAS_AGENT_ERROR_NONE) {
                    error = FINDUAS_AGENT_ERROR_CLASS_SIGNATURE;
                }
            } else {
                if (exact_text_equal(signature, kEidOnAnchor)) {
                    ++anchors->on_anchor_count;
                    if (!capture_loader(jni, jvmti, classes[index], &anchors->on_loader) &&
                        error == FINDUAS_AGENT_ERROR_NONE) {
                        error = FINDUAS_AGENT_ERROR_CLASS_LOADER;
                    }
                } else if (exact_text_equal(signature, kEidGateAnchor)) {
                    ++anchors->gate_anchor_count;
                    if (!capture_loader(jni, jvmti, classes[index], &anchors->gate_loader) &&
                        error == FINDUAS_AGENT_ERROR_NONE) {
                        error = FINDUAS_AGENT_ERROR_CLASS_LOADER;
                    }
                }
                if ((*jvmti)->Deallocate(jvmti, (unsigned char *)signature) !=
                        JVMTI_ERROR_NONE &&
                    error == FINDUAS_AGENT_ERROR_NONE) {
                    error = FINDUAS_AGENT_ERROR_DEALLOCATION;
                }
            }
        }
        (*jni)->DeleteLocalRef(jni, classes[index]);
    }

    if (classes != NULL &&
        (*jvmti)->Deallocate(jvmti, (unsigned char *)classes) != JVMTI_ERROR_NONE &&
        error == FINDUAS_AGENT_ERROR_NONE) {
        error = FINDUAS_AGENT_ERROR_DEALLOCATION;
    }
    if (clear_owned_exception(jni) && error == FINDUAS_AGENT_ERROR_NONE) {
        error = FINDUAS_AGENT_ERROR_PENDING_EXCEPTION;
    }
    if (error != FINDUAS_AGENT_ERROR_NONE) {
        return error;
    }
    if (anchors->on_anchor_count != 1 || anchors->gate_anchor_count != 1 ||
        anchors->on_loader == NULL || anchors->gate_loader == NULL) {
        return FINDUAS_AGENT_ERROR_ANCHOR_CARDINALITY;
    }
    if ((*jni)->IsSameObject(jni, anchors->on_loader, anchors->gate_loader) != JNI_TRUE) {
        return FINDUAS_AGENT_ERROR_LOADER_IDENTITY;
    }
    anchors->unique_loader_count = 1;
    return FINDUAS_AGENT_ERROR_NONE;
}

static void emit_numeric_result(const FinduasAgentResult *result) {
    __android_log_print(
        ANDROID_LOG_INFO,
        FINDUAS_LOG_TAG,
        "FINDUAS_EID_ROUTE_V21 error=%u route=%u loaded=%d on=%d gate=%d loaders=%d "
        "module_error=%u modules=%u handles=%u symbols=%u mediator=%u exception_gate=%u "
        "framework=%u hardware=%u semantic=%u prefixes=%u abstraction=%u characteristics=%u "
        "same_owner=%u weak_acq=%u weak_rel=%u shared_acq=%u shared_rel=%u string_init=%u "
        "string_dtor=%u key_init=%u key_dtor=%u product=%u component_type=%u "
        "component_index=%u abstraction_id=%u device_id=%u",
        (unsigned int)result->error,
        (unsigned int)result->route.status,
        (int)result->anchors.loaded_count,
        (int)result->anchors.on_anchor_count,
        (int)result->anchors.gate_anchor_count,
        (int)result->anchors.unique_loader_count,
        (unsigned int)result->route.module_error,
        (unsigned int)result->route.validated_module_count,
        (unsigned int)result->route.opened_handle_count,
        (unsigned int)result->route.validated_symbol_count,
        (unsigned int)result->route.mediator_present,
        (unsigned int)result->route.exception_boundary_admitted,
        (unsigned int)result->route.framework_pinned,
        (unsigned int)result->route.hardware_validated,
        (unsigned int)result->route.semantic_tuple_validated,
        (unsigned int)result->route.prefixes_validated,
        (unsigned int)result->route.abstraction_type_validated,
        (unsigned int)result->route.characteristics_present,
        (unsigned int)result->route.same_owner_before_after,
        (unsigned int)result->route.acquired_weak_count,
        (unsigned int)result->route.released_weak_count,
        (unsigned int)result->route.acquired_shared_count,
        (unsigned int)result->route.released_shared_count,
        (unsigned int)result->route.initialized_string_count,
        (unsigned int)result->route.destroyed_string_count,
        (unsigned int)result->route.initialized_cache_key_count,
        (unsigned int)result->route.destroyed_cache_key_count,
        (unsigned int)result->route.product_id,
        (unsigned int)result->route.component_type,
        (unsigned int)result->route.component_index,
        (unsigned int)result->route.abstraction_id,
        (unsigned int)result->route.device_id);
}

JNIEXPORT jint JNICALL Agent_OnAttach(JavaVM *vm, char *options, void *reserved) {
    (void)reserved;
    FinduasAgentResult result;
    memset(&result, 0, sizeof(result));
    jvmtiEnv *jvmti = NULL;
    JNIEnv *jni = NULL;

    if (options != NULL && options[0] != '\0') {
        result.error = FINDUAS_AGENT_ERROR_OPTIONS_NOT_EMPTY;
        emit_numeric_result(&result);
        return JNI_ERR;
    }
    if (atomic_exchange_explicit(&g_ever_attached, true, memory_order_acq_rel)) {
        result.error = FINDUAS_AGENT_ERROR_ALREADY_ATTACHED;
        emit_numeric_result(&result);
        return JNI_ERR;
    }
    if (vm == NULL) {
        result.error = FINDUAS_AGENT_ERROR_VM_UNAVAILABLE;
        emit_numeric_result(&result);
        return JNI_ERR;
    }
    if ((*vm)->GetEnv(vm, (void **)&jvmti, JVMTI_VERSION_1_2) != JNI_OK || jvmti == NULL) {
        result.error = FINDUAS_AGENT_ERROR_JVMTI_UNAVAILABLE;
        emit_numeric_result(&result);
        return JNI_ERR;
    }
    if ((*vm)->GetEnv(vm, (void **)&jni, JNI_VERSION_1_6) != JNI_OK || jni == NULL) {
        result.error = FINDUAS_AGENT_ERROR_JNI_UNAVAILABLE;
        goto dispose_environment;
    }
    if ((*jni)->ExceptionCheck(jni) == JNI_TRUE) {
        result.error = FINDUAS_AGENT_ERROR_PENDING_EXCEPTION;
        goto dispose_environment;
    }

    result.error = discover_exact_anchors(jni, jvmti, &result.anchors);
    if (result.error == FINDUAS_AGENT_ERROR_NONE) {
        result.route.status = finduas_route_resolver_run(&result.route);
        if (result.route.status != FINDUAS_ROUTE_STATUS_RESOLVED) {
            result.error = FINDUAS_AGENT_ERROR_ROUTE_NOT_RESOLVED;
        }
    }
    release_anchor_loaders(jni, &result.anchors);
    if (clear_owned_exception(jni)) {
        set_error_once(&result, FINDUAS_AGENT_ERROR_PENDING_EXCEPTION);
    }

dispose_environment:
    if ((*jvmti)->DisposeEnvironment(jvmti) != JVMTI_ERROR_NONE) {
        set_error_once(&result, FINDUAS_AGENT_ERROR_JVMTI_DISPOSAL);
    }
    emit_numeric_result(&result);
    return result.error == FINDUAS_AGENT_ERROR_NONE ? JNI_OK : JNI_ERR;
}
