#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "note_parser.h"
#include "route_policy.h"
#include "target_profile.h"

static void test_build_id_parser(void) {
    const uint8_t expected[FINDUAS_GNU_BUILD_ID_SIZE] = {
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09,
        0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, 0x11, 0x12, 0x13,
    };
    uint8_t note[36] = {
        0x04, 0x00, 0x00, 0x00,
        0x14, 0x00, 0x00, 0x00,
        0x03, 0x00, 0x00, 0x00,
        'G', 'N', 'U', '\0',
    };
    memcpy(note + 16u, expected, sizeof(expected));

    uint8_t output[FINDUAS_GNU_BUILD_ID_SIZE] = {0};
    assert(finduas_parse_unique_gnu_build_id(note, sizeof(note), output) == 1);
    assert(memcmp(output, expected, sizeof(expected)) == 0);

    assert(finduas_parse_unique_gnu_build_id(note, sizeof(note) - 1u, output) == 0);
    assert(finduas_parse_unique_gnu_build_id(NULL, sizeof(note), output) == 0);
    assert(finduas_parse_unique_gnu_build_id(note, sizeof(note), NULL) == 0);

    uint8_t duplicate[72] = {0};
    memcpy(duplicate, note, sizeof(note));
    memcpy(duplicate + sizeof(note), note, sizeof(note));
    assert(finduas_parse_unique_gnu_build_id(duplicate, sizeof(duplicate), output) == 0);

    uint8_t wrong_name[36];
    memcpy(wrong_name, note, sizeof(note));
    wrong_name[12] = 'X';
    assert(finduas_parse_unique_gnu_build_id(wrong_name, sizeof(wrong_name), output) == 0);
}

static void test_semantic_and_route_policy(void) {
    FinduasSemanticTuple semantic = {
        FINDUAS_EID_PRODUCT_ID,
        FINDUAS_EID_COMPONENT_TYPE,
        FINDUAS_EID_COMPONENT_INDEX,
        FINDUAS_EID_IGNORE_SENTINEL,
        FINDUAS_EID_IGNORE_SENTINEL,
    };
    const uint32_t prefixes[3] = {0u, 4u, 0u};
    FinduasLiveRouteScalars route = {0u, 4u, 0u, 0u, 0u, 0u};

    assert(finduas_semantic_tuple_is_exact(&semantic) == 1);
    assert(finduas_prefixes_are_exact(prefixes, 3u, &semantic) == 1);
    assert(finduas_live_route_scalars_match(&route, prefixes, 3u, &semantic) == 1);

    semantic.product_id = 1u;
    assert(finduas_semantic_tuple_is_exact(&semantic) == 0);
    semantic.product_id = 0u;
    route.ready_state = 1u;
    assert(finduas_live_route_scalars_match(&route, prefixes, 3u, &semantic) == 0);
    route.ready_state = 0u;
    route.device_id = 1u;
    assert(finduas_live_route_scalars_match(&route, prefixes, 3u, &semantic) == 0);
    route.device_id = 0u;
    route.component_type = 3u;
    assert(finduas_live_route_scalars_match(&route, prefixes, 3u, &semantic) == 0);
}

static void test_target_profile_shape(void) {
    assert(FINDUAS_MODULE_COUNT == 3);
    assert(FINDUAS_TARGET_SYMBOL_COUNT == 21);
    assert(strcmp(kFinduasModuleProfiles[FINDUAS_MODULE_SDK_JNI].basename, "libsdk_jni.so") == 0);
    assert(strcmp(
               kFinduasModuleProfiles[FINDUAS_MODULE_SDK_KEY_VALUE].basename,
               "libsdk_key_value.so") == 0);
    assert(strcmp(kFinduasModuleProfiles[FINDUAS_MODULE_SDK_BASE].basename, "libsdk_base.so") == 0);

    size_t function_count = 0u;
    size_t object_count = 0u;
    for (int index = 0; index < FINDUAS_TARGET_SYMBOL_COUNT; ++index) {
        const FinduasSymbolProfile *profile = &kFinduasSymbolProfiles[index];
        assert(profile->name != NULL && profile->name[0] == '_');
        assert(profile->expected_rva != 0u);
        assert(profile->symbol_size != 0u);
        if (profile->kind == FINDUAS_SYMBOL_FUNCTION) {
            ++function_count;
            assert(profile->signature_size > 0u);
            assert(profile->signature_size <= profile->symbol_size);
            assert(profile->signature_size <= FINDUAS_INSTRUCTION_SIGNATURE_SIZE);
            assert((profile->signature_size % 4u) == 0u);
        } else {
            ++object_count;
            assert(profile->signature_size == 0u);
        }
    }
    assert(function_count == 17u);
    assert(object_count == 4u);
}

int main(void) {
    test_build_id_parser();
    test_semantic_and_route_policy();
    test_target_profile_shape();
    return 0;
}
