#include <android/log.h>
#include <jni.h>
#include <jvmti.h>
#include <stddef.h>

#if !defined(__aarch64__)
#error "FindUAS EID resolver V1 must be built for AArch64"
#endif

#define FINDUAS_LOG_TAG "FindUAS-EID-Resolver-V1"
#define FINDUAS_MAX_LOADED_CLASSES 200000
#define FINDUAS_MAX_TRACKED_LOADERS 2

static const char kEidOnAnchor[] =
    "Lcom/uav/flymodel/generated/impl/flight/regulation/"
    "RemoteIDModelImpl$electronicIDBroadcastOn$2$1;";
static const char kEidGateAnchor[] =
    "Lcom/uav/flymodel/generated/impl/flight/regulation/"
    "RemoteIDModelImpl$electronicIDBroadcastExisted$2$1;";

enum ResolverError {
    RESOLVER_ERROR_NONE = 0,
    RESOLVER_ERROR_OPTIONS_NOT_EMPTY = 1,
    RESOLVER_ERROR_VM_UNAVAILABLE = 2,
    RESOLVER_ERROR_JVMTI_ENV_UNAVAILABLE = 3,
    RESOLVER_ERROR_JNI_ENV_UNAVAILABLE = 4,
    RESOLVER_ERROR_PENDING_JNI_EXCEPTION = 5,
    RESOLVER_ERROR_CLASS_ENUMERATION_FAILED = 6,
    RESOLVER_ERROR_CLASS_COUNT_OUT_OF_RANGE = 7,
    RESOLVER_ERROR_CLASS_SIGNATURE_FAILED = 8,
    RESOLVER_ERROR_CLASS_LOADER_FAILED = 9,
    RESOLVER_ERROR_GLOBAL_REF_FAILED = 10,
    RESOLVER_ERROR_DEALLOCATION_FAILED = 11,
    RESOLVER_ERROR_ANCHOR_CARDINALITY = 12,
    RESOLVER_ERROR_LOADER_CARDINALITY = 13,
    RESOLVER_ERROR_ENV_DISPOSAL_FAILED = 14,
};

typedef struct ResolverResult {
    enum ResolverError error;
    jint loaded_count;
    jint on_anchor_count;
    jint gate_anchor_count;
    jint unique_loader_count;
} ResolverResult;

static void set_error_once(ResolverResult *result, enum ResolverError error) {
    if (result->error == RESOLVER_ERROR_NONE) {
        result->error = error;
    }
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

static void emit_result(const ResolverResult *result) {
    __android_log_print(
        ANDROID_LOG_INFO,
        FINDUAS_LOG_TAG,
        "FINDUAS_EID_RESOLVER_V1 error_code=%d loaded_count=%d on_anchor_count=%d "
        "gate_anchor_count=%d unique_loader_count=%d",
        (int)result->error,
        (int)result->loaded_count,
        (int)result->on_anchor_count,
        (int)result->gate_anchor_count,
        (int)result->unique_loader_count);
}

static void clear_owned_exception(JNIEnv *jni, ResolverResult *result) {
    if ((*jni)->ExceptionCheck(jni) == JNI_TRUE) {
        (*jni)->ExceptionClear(jni);
        set_error_once(result, RESOLVER_ERROR_PENDING_JNI_EXCEPTION);
    }
}

static void record_loader(JNIEnv *jni,
                          jvmtiEnv *jvmti,
                          jclass anchor_class,
                          jobject loader_globals[FINDUAS_MAX_TRACKED_LOADERS],
                          ResolverResult *result) {
    jobject loader_local = NULL;
    const jvmtiError loader_error =
        (*jvmti)->GetClassLoader(jvmti, anchor_class, &loader_local);
    if (loader_error != JVMTI_ERROR_NONE) {
        /* JVMTI output parameters are undefined on error; no local reference was created. */
        loader_local = NULL;
        set_error_once(result, RESOLVER_ERROR_CLASS_LOADER_FAILED);
        return;
    }
    if (loader_local == NULL) {
        set_error_once(result, RESOLVER_ERROR_CLASS_LOADER_FAILED);
        return;
    }

    for (jint index = 0;
         index < result->unique_loader_count && index < FINDUAS_MAX_TRACKED_LOADERS;
         ++index) {
        if ((*jni)->IsSameObject(jni, loader_local, loader_globals[index]) == JNI_TRUE) {
            (*jni)->DeleteLocalRef(jni, loader_local);
            return;
        }
    }

    if (result->unique_loader_count >= FINDUAS_MAX_TRACKED_LOADERS) {
        (*jni)->DeleteLocalRef(jni, loader_local);
        set_error_once(result, RESOLVER_ERROR_LOADER_CARDINALITY);
        return;
    }

    jobject loader_global = (*jni)->NewGlobalRef(jni, loader_local);
    (*jni)->DeleteLocalRef(jni, loader_local);
    if (loader_global == NULL || (*jni)->ExceptionCheck(jni) == JNI_TRUE) {
        if (loader_global != NULL) {
            (*jni)->DeleteGlobalRef(jni, loader_global);
        }
        set_error_once(result, RESOLVER_ERROR_GLOBAL_REF_FAILED);
        clear_owned_exception(jni, result);
        return;
    }

    loader_globals[result->unique_loader_count] = loader_global;
    ++result->unique_loader_count;
}

JNIEXPORT jint JNICALL Agent_OnAttach(JavaVM *vm, char *options, void *reserved) {
    (void)reserved;

    ResolverResult result = {RESOLVER_ERROR_NONE, 0, 0, 0, 0};
    jvmtiEnv *jvmti = NULL;
    JNIEnv *jni = NULL;
    jclass *classes = NULL;
    jobject loader_globals[FINDUAS_MAX_TRACKED_LOADERS] = {NULL, NULL};

    if (options != NULL && options[0] != '\0') {
        result.error = RESOLVER_ERROR_OPTIONS_NOT_EMPTY;
        emit_result(&result);
        return JNI_ERR;
    }
    if (vm == NULL) {
        result.error = RESOLVER_ERROR_VM_UNAVAILABLE;
        emit_result(&result);
        return JNI_ERR;
    }
    if ((*vm)->GetEnv(vm, (void **)&jvmti, JVMTI_VERSION_1_2) != JNI_OK || jvmti == NULL) {
        result.error = RESOLVER_ERROR_JVMTI_ENV_UNAVAILABLE;
        emit_result(&result);
        return JNI_ERR;
    }
    if ((*vm)->GetEnv(vm, (void **)&jni, JNI_VERSION_1_6) != JNI_OK || jni == NULL) {
        result.error = RESOLVER_ERROR_JNI_ENV_UNAVAILABLE;
        goto dispose_environment;
    }
    if ((*jni)->ExceptionCheck(jni) == JNI_TRUE) {
        result.error = RESOLVER_ERROR_PENDING_JNI_EXCEPTION;
        goto dispose_environment;
    }

    const jvmtiError classes_error =
        (*jvmti)->GetLoadedClasses(jvmti, &result.loaded_count, &classes);
    if (classes_error != JVMTI_ERROR_NONE) {
        /* JVMTI guarantees no allocation on error, and both outputs are undefined. */
        result.loaded_count = 0;
        classes = NULL;
        result.error = RESOLVER_ERROR_CLASS_ENUMERATION_FAILED;
        goto dispose_environment;
    }
    if (result.loaded_count < 0 || (result.loaded_count > 0 && classes == NULL)) {
        result.error = RESOLVER_ERROR_CLASS_ENUMERATION_FAILED;
        goto dispose_environment;
    }

    const int inspect_signatures = result.loaded_count <= FINDUAS_MAX_LOADED_CLASSES;
    if (!inspect_signatures) {
        result.error = RESOLVER_ERROR_CLASS_COUNT_OUT_OF_RANGE;
    }

    for (jint index = 0; index < result.loaded_count; ++index) {
        if (inspect_signatures) {
            char *signature = NULL;
            const jvmtiError signature_error =
                (*jvmti)->GetClassSignature(jvmti, classes[index], &signature, NULL);

            if (signature_error != JVMTI_ERROR_NONE) {
                /* JVMTI guarantees no allocation on error; the output is undefined. */
                signature = NULL;
                set_error_once(&result, RESOLVER_ERROR_CLASS_SIGNATURE_FAILED);
            } else {
                if (signature == NULL) {
                    set_error_once(&result, RESOLVER_ERROR_CLASS_SIGNATURE_FAILED);
                } else if (exact_text_equal(signature, kEidOnAnchor)) {
                    ++result.on_anchor_count;
                    record_loader(jni, jvmti, classes[index], loader_globals, &result);
                } else if (exact_text_equal(signature, kEidGateAnchor)) {
                    ++result.gate_anchor_count;
                    record_loader(jni, jvmti, classes[index], loader_globals, &result);
                }

                if (signature != NULL &&
                    (*jvmti)->Deallocate(jvmti, (unsigned char *)signature) != JVMTI_ERROR_NONE) {
                    set_error_once(&result, RESOLVER_ERROR_DEALLOCATION_FAILED);
                }
            }
        }
        (*jni)->DeleteLocalRef(jni, classes[index]);
    }

    if (classes != NULL &&
        (*jvmti)->Deallocate(jvmti, (unsigned char *)classes) != JVMTI_ERROR_NONE) {
        set_error_once(&result, RESOLVER_ERROR_DEALLOCATION_FAILED);
    }

    for (jint index = 0;
         index < result.unique_loader_count && index < FINDUAS_MAX_TRACKED_LOADERS;
         ++index) {
        if (loader_globals[index] != NULL) {
            (*jni)->DeleteGlobalRef(jni, loader_globals[index]);
        }
    }
    clear_owned_exception(jni, &result);

    if (result.error == RESOLVER_ERROR_NONE &&
        (result.on_anchor_count != 1 || result.gate_anchor_count != 1)) {
        result.error = RESOLVER_ERROR_ANCHOR_CARDINALITY;
    }
    if (result.error == RESOLVER_ERROR_NONE && result.unique_loader_count != 1) {
        result.error = RESOLVER_ERROR_LOADER_CARDINALITY;
    }

dispose_environment:
    if ((*jvmti)->DisposeEnvironment(jvmti) != JVMTI_ERROR_NONE) {
        set_error_once(&result, RESOLVER_ERROR_ENV_DISPOSAL_FAILED);
    }
    emit_result(&result);
    return result.error == RESOLVER_ERROR_NONE ? JNI_OK : JNI_ERR;
}
