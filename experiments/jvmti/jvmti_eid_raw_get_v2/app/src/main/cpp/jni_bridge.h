#ifndef FINDUAS_EID_RAW_GET_V2_JNI_BRIDGE_H
#define FINDUAS_EID_RAW_GET_V2_JNI_BRIDGE_H

#include <jni.h>
#include <jvmti.h>

#include "route_snapshot.h"
#include "state.h"

enum BridgeError {
    BRIDGE_ERROR_NONE = 0,
    BRIDGE_ERROR_ATTEMPT_ALREADY_BEGUN = 1,
    BRIDGE_ERROR_ROUTE_INVALID = 2,
    BRIDGE_ERROR_PLATFORM_CLASS = 3,
    BRIDGE_ERROR_DIRECT_BUFFER = 4,
    BRIDGE_ERROR_HELPER_LOADER = 5,
    BRIDGE_ERROR_HELPER_CLASS = 6,
    BRIDGE_ERROR_HELPER_LOADER_IDENTITY = 7,
    BRIDGE_ERROR_REGISTER_NATIVES = 8,
    BRIDGE_ERROR_CALLBACK_OBJECT = 9,
    BRIDGE_ERROR_CALLBACK_TYPE = 10,
    BRIDGE_ERROR_SEND_METHOD = 11,
    BRIDGE_ERROR_BODY = 12,
    BRIDGE_ERROR_SEND_GUARD = 13,
    BRIDGE_ERROR_SEND_EXCEPTION = 14,
    BRIDGE_ERROR_ZERO_HANDLE = 15,
    BRIDGE_ERROR_LOCAL_DEADLINE = 16,
    BRIDGE_ERROR_REMOTE_TIMEOUT = 17,
    BRIDGE_ERROR_MALFORMED_RESPONSE = 18,
    BRIDGE_ERROR_HANDLE_MISMATCH = 19,
    BRIDGE_ERROR_PROTOCOL_RESULT = 20,
    BRIDGE_ERROR_CANCEL = 21,
    BRIDGE_ERROR_CALLBACK_CARDINALITY = 22,
};

enum BridgeError jni_bridge_send_once(
    JNIEnv *jni,
    jvmtiEnv *jvmti,
    jobject semantic_anchor_loader,
    jclass raw_data_class,
    jclass send_interface_class,
    const RouteSnapshot *route,
    AttemptState *attempt);

#endif
