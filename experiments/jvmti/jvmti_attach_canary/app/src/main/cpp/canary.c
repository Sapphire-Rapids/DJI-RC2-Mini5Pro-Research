#include <android/log.h>
#include <jni.h>
#include <jvmti.h>
#include <stddef.h>

#if !defined(__aarch64__)
#error "FindUAS JVMTI canary V0 must be built for AArch64"
#endif

#define FINDUAS_LOG_TAG "FindUAS-JVMTI-Canary"

enum CanaryError {
    CANARY_ERROR_NONE = 0,
    CANARY_ERROR_OPTIONS_NOT_EMPTY = 1,
    CANARY_ERROR_VM_UNAVAILABLE = 2,
    CANARY_ERROR_JVMTI_ENV_UNAVAILABLE = 3,
    CANARY_ERROR_VERSION_READ_FAILED = 4,
    CANARY_ERROR_ENV_DISPOSAL_FAILED = 5,
};

static void emit_result(enum CanaryError error, jint jvmti_version) {
    __android_log_print(
        ANDROID_LOG_INFO,
        FINDUAS_LOG_TAG,
        "FINDUAS_JVMTI_CANARY_V0 abi=arm64 error_code=%d jvmti_version=0x%08x",
        (int)error,
        (unsigned int)jvmti_version);
}

JNIEXPORT jint JNICALL Agent_OnAttach(JavaVM *vm, char *options, void *reserved) {
    (void)reserved;

    if (options != NULL && options[0] != '\0') {
        emit_result(CANARY_ERROR_OPTIONS_NOT_EMPTY, 0);
        return JNI_ERR;
    }
    if (vm == NULL) {
        emit_result(CANARY_ERROR_VM_UNAVAILABLE, 0);
        return JNI_ERR;
    }

    jvmtiEnv *jvmti = NULL;
    if ((*vm)->GetEnv(vm, (void **)&jvmti, JVMTI_VERSION_1_2) != JNI_OK || jvmti == NULL) {
        emit_result(CANARY_ERROR_JVMTI_ENV_UNAVAILABLE, 0);
        return JNI_ERR;
    }

    jint jvmti_version = 0;
    if ((*jvmti)->GetVersionNumber(jvmti, &jvmti_version) != JVMTI_ERROR_NONE) {
        jvmti_version = 0;
        if ((*jvmti)->DisposeEnvironment(jvmti) != JVMTI_ERROR_NONE) {
            emit_result(CANARY_ERROR_ENV_DISPOSAL_FAILED, 0);
            return JNI_ERR;
        }
        emit_result(CANARY_ERROR_VERSION_READ_FAILED, 0);
        return JNI_ERR;
    }

    if ((*jvmti)->DisposeEnvironment(jvmti) != JVMTI_ERROR_NONE) {
        emit_result(CANARY_ERROR_ENV_DISPOSAL_FAILED, 0);
        return JNI_ERR;
    }

    emit_result(CANARY_ERROR_NONE, jvmti_version);
    return JNI_OK;
}
