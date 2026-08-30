#include <android/log.h>
#include <jni.h>
#include <jvmti.h>
#include <unistd.h>

#define FINDUAS_ART_TI_VERSION 0x70010200

JNIEXPORT jint JNICALL Agent_OnAttach(JavaVM *vm, char *options, void *reserved) {
    (void)reserved;
    if (vm == NULL || (options != NULL && options[0] != '\0')) return JNI_ERR;

    jvmtiEnv *art_ti = NULL;
    jint interface_version = 0;
    jint env_result = (*vm)->GetEnv(vm, (void **)&art_ti, FINDUAS_ART_TI_VERSION);
    jvmtiError version_result = JVMTI_ERROR_INTERNAL;
    if (env_result == JNI_OK && art_ti != NULL) {
        version_result = (*art_ti)->GetVersionNumber(art_ti, &interface_version);
    }
    int ready = env_result == JNI_OK && art_ti != NULL && version_result == JVMTI_ERROR_NONE;
    __android_log_print(
        ANDROID_LOG_INFO,
        "FindUAS-ARTTI-Canary",
        "ARTTI_CANARY ready=%d abi_bits=%u pid=%ld uid=%lu env=%d version_result=%d version=0x%08x",
        ready,
        (unsigned int)(sizeof(void *) * 8),
        (long)getpid(),
        (unsigned long)getuid(),
        (int)env_result,
        (int)version_result,
        (unsigned int)interface_version);
    return ready ? JNI_OK : JNI_ERR;
}
