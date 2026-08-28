#include "target_profile.h"

const FinduasModuleProfile kFinduasModuleProfiles[FINDUAS_MODULE_COUNT] = {
    [FINDUAS_MODULE_SDK_JNI] = {
        "libsdk_jni.so",
        {0xc8, 0x92, 0xb3, 0xc0, 0x66, 0x64, 0xdf, 0x91, 0xd6, 0x43,
         0xf8, 0x4a, 0xe9, 0xe5, 0x9a, 0x90, 0x63, 0x87, 0x06, 0x8b},
    },
    [FINDUAS_MODULE_SDK_KEY_VALUE] = {
        "libsdk_key_value.so",
        {0x87, 0x7a, 0x01, 0xa5, 0xb4, 0xb1, 0x7e, 0x0a, 0x0f, 0x1b,
         0x91, 0x53, 0xcc, 0xfe, 0x24, 0x89, 0x1f, 0xb3, 0xc2, 0x30},
    },
    [FINDUAS_MODULE_SDK_BASE] = {
        "libsdk_base.so",
        {0xde, 0x10, 0x4d, 0xda, 0xca, 0x91, 0x43, 0x88, 0x07, 0xb2,
         0x16, 0x88, 0xba, 0xf0, 0x84, 0x55, 0xd5, 0xad, 0xe2, 0x0c},
    },
};

#define FUNCTION_PROFILE( \
    module_value, symbol_name, rva_value, symbol_size_value, signature_size_value, ...) \
    {module_value, FINDUAS_SYMBOL_FUNCTION, symbol_name, rva_value, symbol_size_value, \
     signature_size_value, {__VA_ARGS__}}
#define OBJECT_PROFILE(module_value, symbol_name, rva_value, size_value) \
    {module_value, FINDUAS_SYMBOL_OBJECT, symbol_name, rva_value, size_value, 0u, {0}}

const FinduasSymbolProfile kFinduasSymbolProfiles[FINDUAS_TARGET_SYMBOL_COUNT] = {
    [FINDUAS_SYMBOL_GLOBAL_MEDIATOR] = OBJECT_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZN3uav3sdk17g_pModuleMediatorE",
        0x05344600u,
        8u),
    [FINDUAS_SYMBOL_GET_FRAMEWORK_CORE] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZN3uav3sdk14ModuleMediator16GetFrameworkCoreEv",
        0x01d54ff8u,
        56u,
        16u,
        0x09, 0x18, 0x42, 0xf9, 0x69, 0x01, 0x00, 0xb4,
        0x09, 0x01, 0x00, 0xf9, 0x09, 0x1c, 0x42, 0xf9),
    [FINDUAS_SYMBOL_CORE_GET_KEY] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZN3uav3sdk16SDKFrameworkCore6GetKeyEjjjjjRKNSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEE",
        0x025006bcu,
        52u,
        16u,
        0x29, 0x69, 0x01, 0x90, 0x29, 0x09, 0x40, 0xf9,
        0xe0, 0x03, 0x08, 0xaa, 0x29, 0x01, 0x40, 0x79),
    [FINDUAS_SYMBOL_HARDWARE_GET_ABSTRACTION] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZN3uav3sdk13HardwareLayer14GetAbstractionERKNSt6__ndk16vectorIjNS2_9allocatorIjEEEE",
        0x0250d6c0u,
        8u,
        8u,
        0x00, 0x80, 0x00, 0x91, 0xaf, 0x8a, 0xad, 0x14,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    [FINDUAS_SYMBOL_GET_CHARACTERISTICS] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZN3uav3sdk15BaseAbstraction18GetCharacteristicsERKNS0_8CacheKeyE",
        0x02515d94u,
        52u,
        16u,
        0xfd, 0x7b, 0xbe, 0xa9, 0xf3, 0x0b, 0x00, 0xf9,
        0xfd, 0x03, 0x00, 0x91, 0xf3, 0x03, 0x00, 0xaa),
    [FINDUAS_SYMBOL_GET_DEVICE_ID] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZNK3uav3sdk15BaseAbstraction11GetDeviceIDEv",
        0x025194c8u,
        8u,
        8u,
        0x00, 0xe0, 0x40, 0xb9, 0xc0, 0x03, 0x5f, 0xd6,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    [FINDUAS_SYMBOL_GET_PRODUCT_ID] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZNK3uav3sdk15BaseAbstraction12GetProductIDEv",
        0x025194d0u,
        8u,
        8u,
        0x00, 0x98, 0x40, 0xb9, 0xc0, 0x03, 0x5f, 0xd6,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    [FINDUAS_SYMBOL_GET_ABSTRACTION_ID] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZNK3uav3sdk15BaseAbstraction16GetAbstractionIDEv",
        0x025194d8u,
        8u,
        8u,
        0x00, 0xa0, 0x40, 0xb9, 0xc0, 0x03, 0x5f, 0xd6,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    [FINDUAS_SYMBOL_GET_COMPONENT_INDEX] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZNK3uav3sdk15BaseAbstraction17GetComponentIndexEv",
        0x02519b10u,
        8u,
        8u,
        0x00, 0xe4, 0x40, 0xb9, 0xc0, 0x03, 0x5f, 0xd6,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    [FINDUAS_SYMBOL_WEAK_LOCK] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZNSt6__ndk119__shared_weak_count4lockEv",
        0x01d2f300u,
        84u,
        16u,
        0x5f, 0x24, 0x03, 0xd5, 0x08, 0x20, 0x00, 0x91,
        0x0a, 0xfd, 0xdf, 0xc8, 0x5f, 0x05, 0x00, 0xb1),
    [FINDUAS_SYMBOL_RELEASE_SHARED] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZNSt6__ndk119__shared_weak_count16__release_sharedEv",
        0x01d2f244u,
        136u,
        16u,
        0x3f, 0x23, 0x03, 0xd5, 0xfd, 0x7b, 0xbe, 0xa9,
        0xf4, 0x4f, 0x01, 0xa9, 0xfd, 0x03, 0x00, 0x91),
    [FINDUAS_SYMBOL_RELEASE_WEAK] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZNSt6__ndk119__shared_weak_count14__release_weakEv",
        0x01d2f2ccu,
        52u,
        16u,
        0x5f, 0x24, 0x03, 0xd5, 0x08, 0x40, 0x00, 0x91,
        0x09, 0xfd, 0xdf, 0xc8, 0xe9, 0x00, 0x00, 0xb4),
    [FINDUAS_SYMBOL_STRING_INIT] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZNSt6__ndk112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEE6__initEPKcm",
        0x01d30ee8u,
        144u,
        16u,
        0x3f, 0x23, 0x03, 0xd5, 0xfd, 0x7b, 0xbd, 0xa9,
        0xf6, 0x57, 0x01, 0xa9, 0xf4, 0x4f, 0x02, 0xa9),
    [FINDUAS_SYMBOL_STRING_DTOR] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZNSt6__ndk112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEED2Ev",
        0x01d30bccu,
        24u,
        16u,
        0x5f, 0x24, 0x03, 0xd5, 0x08, 0x00, 0x40, 0x39,
        0x48, 0x00, 0x00, 0x37, 0xc0, 0x03, 0x5f, 0xd6),
    [FINDUAS_SYMBOL_CACHE_KEY_DTOR] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZN3uav3sdk8CacheKeyD2Ev",
        0x04a32a48u,
        68u,
        16u,
        0xfd, 0x7b, 0xbe, 0xa9, 0xf3, 0x0b, 0x00, 0xf9,
        0xfd, 0x03, 0x00, 0x91, 0xf3, 0x03, 0x00, 0xaa),
    [FINDUAS_SYMBOL_HARDWARE_VTABLE] = OBJECT_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZTVN3uav3sdk13HardwareLayerE",
        0x050f1250u,
        0x70u),
    [FINDUAS_SYMBOL_MIX139_VTABLE] = OBJECT_PROFILE(
        FINDUAS_MODULE_SDK_JNI,
        "_ZTVN3uav3sdk3key6MixAbsINS0_32UAV77FlightControllerAbstractionENS1_11UAV139FCAbsEEE",
        0x05100f88u,
        0x20u),
    [FINDUAS_SYMBOL_CACHE_KEY_GET_PREFIXES] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_KEY_VALUE,
        "_ZNK3uav3sdk8CacheKey11GetPrefixesEv",
        0x007eab64u,
        8u,
        8u,
        0x00, 0xc0, 0x00, 0x91, 0xc0, 0x03, 0x5f, 0xd6,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    [FINDUAS_SYMBOL_CHARACTERISTICS_INVALID] = OBJECT_PROFILE(
        FINDUAS_MODULE_SDK_KEY_VALUE,
        "_ZN3uav3sdk15Characteristics7InvalidE",
        0x00c19d78u,
        56u),
    [FINDUAS_SYMBOL_GLOBAL_PACKET_STATUS_INSTANCE] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_BASE,
        "_ZN3uav4core18GlobalPacketStatus8instanceEv",
        0x002ec280u,
        168u,
        16u,
        0xfd, 0x7b, 0xbe, 0xa9, 0xf4, 0x4f, 0x01, 0xa9,
        0xfd, 0x03, 0x00, 0x91, 0x88, 0x23, 0x00, 0x90),
    [FINDUAS_SYMBOL_GLOBAL_PACKET_STATUS_GET_SENDER_INDEX] = FUNCTION_PROFILE(
        FINDUAS_MODULE_SDK_BASE,
        "_ZN3uav4core18GlobalPacketStatus20GetGlobalSenderIndexEv",
        0x002ec328u,
        24u,
        16u,
        0x08, 0x00, 0x40, 0xf9, 0x68, 0x00, 0x00, 0xb4,
        0x00, 0xfd, 0xdf, 0x08, 0xc0, 0x03, 0x5f, 0xd6),
};

#undef FUNCTION_PROFILE
#undef OBJECT_PROFILE
