#include "jni_bridge.h"

#include <limits.h>
#include <stdint.h>
#include <stdatomic.h>

#include "helper_dex.inc"

static const char kHelperBinaryName[] = "com.finduas.ridv2.RawCallback";
static const char kSendMethodName[] = "native_SendData";
static const char kSendMethodDescriptor[] =
    "(IIIIIIZIIIIII[BLuav/raw/jni/callback/SendInterface;)J";
static const char kCancelMethodName[] = "native_CancelSend";
static const char kCancelMethodDescriptor[] = "(J)V";
static const int kCallbackDeadlineMs = 2000;
static const int kCallbackQuietWindowMs = 100;

static _Atomic(AttemptState *) g_callback_attempt = NULL;

static int clear_exception(JNIEnv *jni) {
    if ((*jni)->ExceptionCheck(jni) == JNI_TRUE) {
        (*jni)->ExceptionClear(jni);
        return 1;
    }
    return 0;
}

static void JNICALL native_callback_received(
    JNIEnv *jni,
    jobject callback,
    jlong handle,
    jbyteArray payload) {
    (void)callback;
    AttemptState *attempt = atomic_load_explicit(&g_callback_attempt, memory_order_acquire);
    if (attempt == NULL || jni == NULL) {
        return;
    }

    if (payload == NULL) {
        attempt_state_on_response(attempt, (int64_t)handle, NULL, -1);
        return;
    }

    const jsize payload_len = (*jni)->GetArrayLength(jni, payload);
    if (clear_exception(jni) || payload_len != 2) {
        attempt_state_on_response(attempt, (int64_t)handle, NULL, (int)payload_len);
        return;
    }

    jbyte raw[2] = {0, 0};
    (*jni)->GetByteArrayRegion(jni, payload, 0, 2, raw);
    if (clear_exception(jni)) {
        attempt_state_on_response(attempt, (int64_t)handle, NULL, 2);
        return;
    }

    const uint8_t copy[2] = {(uint8_t)raw[0], (uint8_t)raw[1]};
    attempt_state_on_response(attempt, (int64_t)handle, copy, 2);
}

static void JNICALL native_callback_timeout(JNIEnv *jni, jobject callback, jlong handle) {
    (void)jni;
    (void)callback;
    AttemptState *attempt = atomic_load_explicit(&g_callback_attempt, memory_order_acquire);
    if (attempt != NULL) {
        attempt_state_on_timeout(attempt, (int64_t)handle);
    }
}

static enum BridgeError cancel_after_deadline(
    JNIEnv *jni,
    jclass raw_data_class,
    jlong handle,
    AttemptState *attempt) {
    if (handle == 0 || !attempt_state_note_cancel_call(attempt)) {
        return BRIDGE_ERROR_CANCEL;
    }
    jmethodID cancel_method = (*jni)->GetStaticMethodID(
        jni,
        raw_data_class,
        kCancelMethodName,
        kCancelMethodDescriptor);
    if (cancel_method == NULL || clear_exception(jni)) {
        return BRIDGE_ERROR_CANCEL;
    }
    jvalue cancel_arguments[1];
    cancel_arguments[0].j = handle;
    (*jni)->CallStaticVoidMethodA(jni, raw_data_class, cancel_method, cancel_arguments);
    if (clear_exception(jni)) {
        return BRIDGE_ERROR_CANCEL;
    }
    return BRIDGE_ERROR_LOCAL_DEADLINE;
}

enum BridgeError jni_bridge_send_once(
    JNIEnv *jni,
    jvmtiEnv *jvmti,
    jobject semantic_anchor_loader,
    jclass raw_data_class,
    jclass send_interface_class,
    const RouteSnapshot *route,
    AttemptState *attempt) {
    enum BridgeError error = BRIDGE_ERROR_NONE;
    jclass in_memory_loader_class = NULL;
    jclass class_loader_class = NULL;
    jobject dex_buffer = NULL;
    jobject helper_loader = NULL;
    jstring helper_name = NULL;
    jclass helper_class = NULL;
    jobject helper_loader_identity = NULL;
    jobject callback = NULL;
    jbyteArray body = NULL;
    jlong returned_handle = 0;

    if (jni == NULL || jvmti == NULL || semantic_anchor_loader == NULL ||
        raw_data_class == NULL || send_interface_class == NULL || route == NULL || attempt == NULL ||
        !route->product_139_identity_proven || !route->france_eid_capability_proven ||
        !route->host_route_proven || !route_snapshot_epoch_unchanged(route)) {
        return BRIDGE_ERROR_ROUTE_INVALID;
    }
    if (!attempt_state_begin(attempt)) {
        return BRIDGE_ERROR_ATTEMPT_ALREADY_BEGUN;
    }

    in_memory_loader_class = (*jni)->FindClass(jni, "dalvik/system/InMemoryDexClassLoader");
    class_loader_class = (*jni)->FindClass(jni, "java/lang/ClassLoader");
    if (in_memory_loader_class == NULL || class_loader_class == NULL || clear_exception(jni)) {
        error = BRIDGE_ERROR_PLATFORM_CLASS;
        goto cleanup;
    }

    dex_buffer = (*jni)->NewDirectByteBuffer(
        jni,
        (void *)(uintptr_t)kFinduasRawCallbackDex,
        (jlong)kFinduasRawCallbackDexLength);
    if (dex_buffer == NULL || clear_exception(jni)) {
        error = BRIDGE_ERROR_DIRECT_BUFFER;
        goto cleanup;
    }

    jmethodID loader_constructor = (*jni)->GetMethodID(
        jni,
        in_memory_loader_class,
        "<init>",
        "(Ljava/nio/ByteBuffer;Ljava/lang/ClassLoader;)V");
    if (loader_constructor == NULL || clear_exception(jni)) {
        error = BRIDGE_ERROR_HELPER_LOADER;
        goto cleanup;
    }
    jvalue loader_arguments[2];
    loader_arguments[0].l = dex_buffer;
    loader_arguments[1].l = semantic_anchor_loader;
    helper_loader = (*jni)->NewObjectA(
        jni,
        in_memory_loader_class,
        loader_constructor,
        loader_arguments);
    if (helper_loader == NULL || clear_exception(jni)) {
        error = BRIDGE_ERROR_HELPER_LOADER;
        goto cleanup;
    }

    jmethodID load_class_method = (*jni)->GetMethodID(
        jni,
        class_loader_class,
        "loadClass",
        "(Ljava/lang/String;)Ljava/lang/Class;");
    helper_name = (*jni)->NewStringUTF(jni, kHelperBinaryName);
    if (load_class_method == NULL || helper_name == NULL || clear_exception(jni)) {
        error = BRIDGE_ERROR_HELPER_CLASS;
        goto cleanup;
    }
    jvalue load_arguments[1];
    load_arguments[0].l = helper_name;
    helper_class = (jclass)(*jni)->CallObjectMethodA(
        jni,
        helper_loader,
        load_class_method,
        load_arguments);
    if (helper_class == NULL || clear_exception(jni)) {
        error = BRIDGE_ERROR_HELPER_CLASS;
        goto cleanup;
    }

    if ((*jvmti)->GetClassLoader(jvmti, helper_class, &helper_loader_identity) != JVMTI_ERROR_NONE ||
        helper_loader_identity == NULL ||
        (*jni)->IsSameObject(jni, helper_loader, helper_loader_identity) != JNI_TRUE) {
        error = BRIDGE_ERROR_HELPER_LOADER_IDENTITY;
        goto cleanup;
    }

    JNINativeMethod callback_methods[2] = {
        {"onReceivedData", "(J[B)V", (void *)native_callback_received},
        {"onTimeout", "(J)V", (void *)native_callback_timeout},
    };
    if ((*jni)->RegisterNatives(jni, helper_class, callback_methods, 2) != JNI_OK ||
        clear_exception(jni)) {
        error = BRIDGE_ERROR_REGISTER_NATIVES;
        goto cleanup;
    }

    jmethodID callback_constructor =
        (*jni)->GetMethodID(jni, helper_class, "<init>", "()V");
    if (callback_constructor == NULL || clear_exception(jni)) {
        error = BRIDGE_ERROR_CALLBACK_OBJECT;
        goto cleanup;
    }
    callback = (*jni)->NewObjectA(jni, helper_class, callback_constructor, NULL);
    if (callback == NULL || clear_exception(jni)) {
        error = BRIDGE_ERROR_CALLBACK_OBJECT;
        goto cleanup;
    }
    if ((*jni)->IsInstanceOf(jni, callback, send_interface_class) != JNI_TRUE ||
        clear_exception(jni)) {
        error = BRIDGE_ERROR_CALLBACK_TYPE;
        goto cleanup;
    }

    jmethodID send_method = (*jni)->GetStaticMethodID(
        jni,
        raw_data_class,
        kSendMethodName,
        kSendMethodDescriptor);
    if (send_method == NULL || clear_exception(jni)) {
        error = BRIDGE_ERROR_SEND_METHOD;
        goto cleanup;
    }

    body = (*jni)->NewByteArray(jni, 1);
    const jbyte selector = 0x02;
    if (body == NULL || clear_exception(jni)) {
        error = BRIDGE_ERROR_BODY;
        goto cleanup;
    }
    (*jni)->SetByteArrayRegion(jni, body, 0, 1, &selector);
    if (clear_exception(jni)) {
        error = BRIDGE_ERROR_BODY;
        goto cleanup;
    }

    atomic_store_explicit(&g_callback_attempt, attempt, memory_order_release);
    if (!attempt_state_note_send_call(attempt)) {
        error = BRIDGE_ERROR_SEND_GUARD;
        goto cleanup;
    }

    jvalue send_arguments[15];
    send_arguments[0].i = route->product_id;
    send_arguments[1].i = route->device_id;
    send_arguments[2].i = 1;
    send_arguments[3].i = 3;
    send_arguments[4].i = 0x77;
    send_arguments[5].i = 2;
    send_arguments[6].z = JNI_FALSE;
    send_arguments[7].i = 3;
    send_arguments[8].i = route->sender_index;
    send_arguments[9].i = route->receiver_type;
    send_arguments[10].i = route->receiver_index;
    send_arguments[11].i = 0;
    send_arguments[12].i = 500;
    send_arguments[13].l = body;
    send_arguments[14].l = callback;

    returned_handle = (*jni)->CallStaticLongMethodA(
        jni,
        raw_data_class,
        send_method,
        send_arguments);
    if (clear_exception(jni)) {
        attempt_state_set_returned_handle(attempt, 0);
        error = BRIDGE_ERROR_SEND_EXCEPTION;
        goto cleanup;
    }
    attempt_state_set_returned_handle(attempt, (int64_t)returned_handle);
    if (returned_handle == 0) {
        error = BRIDGE_ERROR_ZERO_HANDLE;
        goto cleanup;
    }

    const enum AttemptTerminal terminal =
        attempt_state_wait_until_deadline(attempt, kCallbackDeadlineMs);
    if (terminal == ATTEMPT_TERMINAL_LOCAL_DEADLINE) {
        error = cancel_after_deadline(jni, raw_data_class, returned_handle, attempt);
        goto cleanup;
    }
    if (terminal == ATTEMPT_TERMINAL_REMOTE_TIMEOUT) {
        error = BRIDGE_ERROR_REMOTE_TIMEOUT;
        goto cleanup;
    }
    if (terminal != ATTEMPT_TERMINAL_RESPONSE) {
        error = BRIDGE_ERROR_MALFORMED_RESPONSE;
        goto cleanup;
    }

    const AttemptSnapshot snapshot = attempt_state_snapshot(attempt);
    if (snapshot.callback_count != 1u || snapshot.duplicate_count != 0u ||
        snapshot.payload_len != 2 || !snapshot.callback_handle_present) {
        error = BRIDGE_ERROR_CALLBACK_CARDINALITY;
        goto cleanup;
    }
    if (!snapshot.handle_match) {
        error = BRIDGE_ERROR_HANDLE_MISMATCH;
        goto cleanup;
    }
    if (snapshot.protocol_result != 0) {
        error = BRIDGE_ERROR_PROTOCOL_RESULT;
        goto cleanup;
    }
    if (!attempt_state_wait_for_quiet_window(attempt, kCallbackQuietWindowMs)) {
        error = BRIDGE_ERROR_CALLBACK_CARDINALITY;
        goto cleanup;
    }

cleanup:
    if (body != NULL) {
        (*jni)->DeleteLocalRef(jni, body);
    }
    if (callback != NULL) {
        (*jni)->DeleteLocalRef(jni, callback);
    }
    if (helper_loader_identity != NULL) {
        (*jni)->DeleteLocalRef(jni, helper_loader_identity);
    }
    if (helper_class != NULL) {
        (*jni)->DeleteLocalRef(jni, helper_class);
    }
    if (helper_name != NULL) {
        (*jni)->DeleteLocalRef(jni, helper_name);
    }
    if (helper_loader != NULL) {
        (*jni)->DeleteLocalRef(jni, helper_loader);
    }
    if (dex_buffer != NULL) {
        (*jni)->DeleteLocalRef(jni, dex_buffer);
    }
    if (class_loader_class != NULL) {
        (*jni)->DeleteLocalRef(jni, class_loader_class);
    }
    if (in_memory_loader_class != NULL) {
        (*jni)->DeleteLocalRef(jni, in_memory_loader_class);
    }
    (void)clear_exception(jni);
    return error;
}
