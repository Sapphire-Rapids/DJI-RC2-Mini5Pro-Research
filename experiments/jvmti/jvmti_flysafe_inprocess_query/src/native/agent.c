#include <android/log.h>
#include <jni.h>
#include <jvmti.h>
#include <string.h>

#include "helper_dex.inc"

#define FINDUAS_ART_TI_VERSION 0x70010200
#define FINDUAS_LOG_TAG "FindUAS-FlySafe-Raw"
#define UNLOCK_SIGNATURE "Luav/fscore/jni/unlock/JNIFSUnlockManager;"
#define EVENT_SIGNATURE "Luav/fscore/jni/JNIFSEventManager;"

static void callback_failure(JNIEnv *env, jclass callback_class, jint error_code) {
    (void)env;
    (void)callback_class;
    __android_log_print(
        ANDROID_LOG_INFO,
        FINDUAS_LOG_TAG,
        "FLYSAFE_RAW_QUERY callback=failure error_code=%d",
        (int)error_code);
}

static void callback_inventory(
    JNIEnv *env,
    jclass callback_class,
    jint parse_code,
    jint declared_count,
    jint record_count,
    jint rid_count,
    jint rid_license_id,
    jint rid_level,
    jboolean enabled,
    jboolean in_valid_date,
    jboolean invalid) {
    (void)env;
    (void)callback_class;
    (void)rid_license_id;
    __android_log_print(
        ANDROID_LOG_INFO,
        FINDUAS_LOG_TAG,
        "FLYSAFE_RAW_QUERY callback=success parse=%d declared=%d records=%d rid_count=%d unique=%d level=%d enabled=%d in_valid_date=%d invalid=%d",
        (int)parse_code,
        (int)declared_count,
        (int)record_count,
        (int)rid_count,
        rid_count == 1 && rid_license_id != 0 ? 1 : 0,
        (int)rid_level,
        enabled == JNI_TRUE ? 1 : 0,
        in_valid_date == JNI_TRUE ? 1 : 0,
        invalid == JNI_TRUE ? 1 : 0);
}

static int clear_exception(JNIEnv *env) {
    if ((*env)->ExceptionCheck(env) == JNI_FALSE) return 0;
    (*env)->ExceptionClear(env);
    return 1;
}

__attribute__((visibility("default")))
JNIEXPORT jint JNICALL Agent_OnAttach(JavaVM *vm, char *options, void *reserved) {
    (void)reserved;
    JNIEnv *env = NULL;
    jvmtiEnv *jvmti = NULL;
    jclass *classes = NULL;
    jint class_count = 0;
    jclass unlock_class = NULL;
    jclass event_class = NULL;
    jobject event_instance = NULL;
    jobject parent_loader = NULL;
    jobject dex_buffer = NULL;
    jobject helper_loader = NULL;
    jclass helper_class = NULL;
    jobject callback = NULL;
    jbyteArray dex_bytes = NULL;
    jstring helper_name = NULL;
    jint device_id = 0;
    int stage = 0;
    int exception = 0;
    int unlock_matches = 0;
    int event_matches = 0;
    int query_dispatched = 0;

    if (vm == NULL || (options != NULL && options[0] != '\0')) return JNI_ERR;
    if ((*vm)->GetEnv(vm, (void **)&env, JNI_VERSION_1_6) != JNI_OK || env == NULL) {
        stage = 1;
        goto done;
    }
    if ((*vm)->GetEnv(vm, (void **)&jvmti, FINDUAS_ART_TI_VERSION) != JNI_OK || jvmti == NULL) {
        stage = 2;
        goto done;
    }
    if ((*jvmti)->GetLoadedClasses(jvmti, &class_count, &classes) != JVMTI_ERROR_NONE ||
        classes == NULL) {
        stage = 3;
        goto done;
    }

    for (jint index = 0; index < class_count; index++) {
        char *signature = NULL;
        jvmtiError error = (*jvmti)->GetClassSignature(
            jvmti, classes[index], &signature, NULL);
        if (error == JVMTI_ERROR_NONE && signature != NULL) {
            if (strcmp(signature, UNLOCK_SIGNATURE) == 0) {
                unlock_matches++;
                if (unlock_class == NULL) unlock_class = classes[index];
            } else if (strcmp(signature, EVENT_SIGNATURE) == 0) {
                event_matches++;
                if (event_class == NULL) event_class = classes[index];
            }
            (*jvmti)->Deallocate(jvmti, (unsigned char *)signature);
        }
    }
    if (unlock_matches != 1 || event_matches != 1) {
        stage = 4;
        goto done;
    }

    jclass class_class = (*env)->FindClass(env, "java/lang/Class");
    jclass byte_buffer_class = (*env)->FindClass(env, "java/nio/ByteBuffer");
    jclass in_memory_loader_class = (*env)->FindClass(env, "dalvik/system/InMemoryDexClassLoader");
    jclass class_loader_class = (*env)->FindClass(env, "java/lang/ClassLoader");
    exception |= clear_exception(env);
    if (class_class == NULL || byte_buffer_class == NULL ||
        in_memory_loader_class == NULL || class_loader_class == NULL) {
        stage = 5;
        goto done;
    }

    jmethodID get_class_loader = (*env)->GetMethodID(
        env, class_class, "getClassLoader", "()Ljava/lang/ClassLoader;");
    jmethodID wrap = (*env)->GetStaticMethodID(
        env, byte_buffer_class, "wrap", "([B)Ljava/nio/ByteBuffer;");
    jmethodID loader_constructor = (*env)->GetMethodID(
        env,
        in_memory_loader_class,
        "<init>",
        "(Ljava/nio/ByteBuffer;Ljava/lang/ClassLoader;)V");
    jmethodID load_class = (*env)->GetMethodID(
        env, class_loader_class, "loadClass", "(Ljava/lang/String;)Ljava/lang/Class;");
    exception |= clear_exception(env);
    if (get_class_loader == NULL || wrap == NULL || loader_constructor == NULL ||
        load_class == NULL) {
        stage = 6;
        goto done;
    }

    parent_loader = (*env)->CallObjectMethod(env, unlock_class, get_class_loader);
    dex_bytes = (*env)->NewByteArray(env, (jsize)build_dex_classes_dex_len);
    if (dex_bytes != NULL) {
        (*env)->SetByteArrayRegion(
            env,
            dex_bytes,
            0,
            (jsize)build_dex_classes_dex_len,
            (const jbyte *)build_dex_classes_dex);
    }
    dex_buffer = dex_bytes == NULL
                     ? NULL
                     : (*env)->CallStaticObjectMethod(env, byte_buffer_class, wrap, dex_bytes);
    helper_loader = dex_buffer == NULL
                        ? NULL
                        : (*env)->NewObject(
                              env,
                              in_memory_loader_class,
                              loader_constructor,
                              dex_buffer,
                              parent_loader);
    helper_name = (*env)->NewStringUTF(env, "com.finduas.rid.FlySafeRawCallback");
    helper_class = helper_loader == NULL || helper_name == NULL
                       ? NULL
                       : (jclass)(*env)->CallObjectMethod(
                             env, helper_loader, load_class, helper_name);
    exception |= clear_exception(env);
    if (parent_loader == NULL || helper_class == NULL) {
        stage = 7;
        goto done;
    }

    JNINativeMethod methods[] = {
        {"nativeOnFailure", "(I)V", (void *)callback_failure},
        {"nativeOnInventory", "(IIIIIIZZZ)V", (void *)callback_inventory},
    };
    if ((*env)->RegisterNatives(env, helper_class, methods, 2) != JNI_OK) {
        exception |= clear_exception(env);
        stage = 8;
        goto done;
    }
    jmethodID callback_constructor = (*env)->GetMethodID(env, helper_class, "<init>", "()V");
    callback = callback_constructor == NULL
                   ? NULL
                   : (*env)->NewObject(env, helper_class, callback_constructor);
    exception |= clear_exception(env);
    if (callback == NULL) {
        stage = 9;
        goto done;
    }

    jmethodID event_get_instance = (*env)->GetStaticMethodID(
        env, event_class, "getInstance", "()Luav/fscore/jni/JNIFSEventManager;");
    jmethodID current_device_id = (*env)->GetMethodID(
        env, event_class, "getCurrentDeviceId", "()I");
    jmethodID native_query = (*env)->GetStaticMethodID(
        env,
        unlock_class,
        "native_queryFCLicense",
        "(ILuav/component/flightrestrict/listener/JNIUnlockCommonCallbacks$JNIUnlockCommonCallbackWith;)V");
    exception |= clear_exception(env);
    if (event_get_instance == NULL || current_device_id == NULL || native_query == NULL) {
        stage = 10;
        goto done;
    }

    event_instance = (*env)->CallStaticObjectMethod(env, event_class, event_get_instance);
    if (event_instance != NULL) {
        device_id = (*env)->CallIntMethod(env, event_instance, current_device_id);
    }
    exception |= clear_exception(env);
    if (event_instance == NULL || exception != 0 || device_id == 0 || device_id == -1) {
        stage = 11;
        goto done;
    }

    (*env)->CallStaticVoidMethod(env, unlock_class, native_query, device_id, callback);
    exception |= clear_exception(env);
    if (exception != 0) {
        stage = 12;
        goto done;
    }
    query_dispatched = 1;

done:
    __android_log_print(
        ANDROID_LOG_INFO,
        FINDUAS_LOG_TAG,
        "FLYSAFE_RAW_AGENT stage=%d exception=%d classes=%d unlock=%d event=%d device_id_nonzero=%d dispatched=%d",
        stage,
        exception,
        (int)class_count,
        unlock_matches,
        event_matches,
        device_id != 0 ? 1 : 0,
        query_dispatched);

    if (env != NULL) {
        if (event_instance != NULL) (*env)->DeleteLocalRef(env, event_instance);
        if (callback != NULL) (*env)->DeleteLocalRef(env, callback);
        if (helper_class != NULL) (*env)->DeleteLocalRef(env, helper_class);
        if (helper_name != NULL) (*env)->DeleteLocalRef(env, helper_name);
        if (helper_loader != NULL) (*env)->DeleteLocalRef(env, helper_loader);
        if (dex_buffer != NULL) (*env)->DeleteLocalRef(env, dex_buffer);
        if (dex_bytes != NULL) (*env)->DeleteLocalRef(env, dex_bytes);
        if (classes != NULL) {
            for (jint index = 0; index < class_count; index++) {
                if (classes[index] != NULL) (*env)->DeleteLocalRef(env, classes[index]);
            }
        }
    }
    if (jvmti != NULL) {
        if (classes != NULL) (*jvmti)->Deallocate(jvmti, (unsigned char *)classes);
        (*jvmti)->DisposeEnvironment(jvmti);
    }
    return stage == 0 ? JNI_OK : JNI_ERR;
}
