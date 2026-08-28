#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "identity_core.h"
#include "note_parser.h"
#include "route_policy.h"
#include "sha256.h"
#include "target_profile.h"

#ifndef FINDUAS_RESEARCH_DIR
#error "FINDUAS_RESEARCH_DIR is required for exact-file host tests"
#endif

static void decode_hex(const char *hex, uint8_t output[32]) {
    for (size_t index = 0u; index < 32u; ++index) {
        unsigned int value = 0u;
        assert(sscanf(hex + index * 2u, "%2x", &value) == 1);
        output[index] = (uint8_t)value;
    }
}

static void sha_vector(size_t size, const char *expected_hex, int abc) {
    uint8_t input[65];
    memset(input, 'a', sizeof(input));
    if (abc) {
        memcpy(input, "abc", 3u);
    }
    FinduasSha256Context context;
    uint8_t digest[32];
    uint8_t expected[32];
    finduas_sha256_init(&context);
    assert(finduas_sha256_update(&context, input, size) == 1);
    assert(finduas_sha256_finish(&context, digest) == 1);
    decode_hex(expected_hex, expected);
    assert(finduas_constant_time_equal(digest, expected, sizeof(digest)) == 1);
    expected[31] ^= 1u;
    assert(finduas_constant_time_equal(digest, expected, sizeof(digest)) == 0);
}

static void test_sha256(void) {
    sha_vector(0u, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", 0);
    sha_vector(1u, "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb", 0);
    sha_vector(3u, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", 1);
    sha_vector(55u, "9f4390f8d30c2dd92ec9f095b65e2b9ae9b0a925a5258e241c9f1e910f734318", 0);
    sha_vector(56u, "b35439a4ac6f0948b6d6f9e3c6af0f5f590ce20f1bde7090ef7970686ec6738a", 0);
    sha_vector(63u, "7d3e74a05d7db15bce4ad9ec0658ea98e3f06eeecf16b4c6fff2da457ddc2f34", 0);
    sha_vector(64u, "ffe054fe7ae0cb6dc65c3af9b61d5209f439851db43d0ba5997337df154668eb", 0);
    sha_vector(65u, "635361c48bb9eab14198e76ea8ab7f1a41685d6ad62aa9146d301d4f17eb0ae0", 0);
    assert(finduas_sha256_update(NULL, NULL, 0u) == 0);
    assert(finduas_constant_time_equal(NULL, NULL, 0u) == 1);
    assert(finduas_constant_time_equal(NULL, (const uint8_t *)"x", 1u) == 0);
}

static const char *exact_module_path(int module_id) {
    switch (module_id) {
        case FINDUAS_MODULE_SDK_JNI:
            return FINDUAS_RESEARCH_DIR "/official_dji_fly_20260827/working/extracted/libsdk_jni.so";
        case FINDUAS_MODULE_SDK_KEY_VALUE:
            return FINDUAS_RESEARCH_DIR "/official_dji_fly_20260827/working/sdk_native/libsdk_key_value.so";
        case FINDUAS_MODULE_SDK_BASE:
            return FINDUAS_RESEARCH_DIR "/official_dji_fly_20260827/working/sdk_native/libsdk_base.so";
        default:
            return NULL;
    }
}

static void sha_update_with_flip(
    FinduasSha256Context *context,
    const uint8_t *data,
    size_t size,
    uint64_t chunk_offset,
    uint64_t flip_offset) {
    if (flip_offset < chunk_offset || flip_offset >= chunk_offset + size) {
        assert(finduas_sha256_update(context, data, size) == 1);
        return;
    }
    const size_t local = (size_t)(flip_offset - chunk_offset);
    assert(finduas_sha256_update(context, data, local) == 1);
    const uint8_t flipped = (uint8_t)(data[local] ^ 1u);
    assert(finduas_sha256_update(context, &flipped, 1u) == 1);
    assert(finduas_sha256_update(context, data + local + 1u, size - local - 1u) == 1);
}

static void test_exact_target_files(void) {
    uint8_t buffer[65536];
    for (int module_id = 0; module_id < FINDUAS_MODULE_COUNT; ++module_id) {
        const FinduasModuleProfile *profile = &kFinduasModuleProfiles[module_id];
        assert(finduas_identity_profile_is_well_formed(profile) == 1);
        const int fd = open(exact_module_path(module_id), O_RDONLY);
        assert(fd >= 0);
        struct stat status;
        assert(fstat(fd, &status) == 0);
        assert((uint64_t)status.st_size == profile->exact_file_size);

        uint8_t header[FINDUAS_ELF_HEADER_SIZE];
        FinduasElf64Phdr phdrs[FINDUAS_PROFILE_PHDR_COUNT];
        assert(pread(fd, header, sizeof(header), 0) == (ssize_t)sizeof(header));
        assert(pread(fd, phdrs, sizeof(phdrs), sizeof(header)) == (ssize_t)sizeof(phdrs));
        assert(finduas_identity_header_phdr_match(
                   profile,
                   header,
                   phdrs,
                   FINDUAS_PROFILE_PHDR_COUNT) == 1);

        FinduasSha256Context exact;
        FinduasSha256Context first;
        FinduasSha256Context middle;
        FinduasSha256Context last;
        finduas_sha256_init(&exact);
        finduas_sha256_init(&first);
        finduas_sha256_init(&middle);
        finduas_sha256_init(&last);
        uint64_t offset = 0u;
        while (offset < profile->exact_file_size) {
            const uint64_t remaining = profile->exact_file_size - offset;
            const size_t wanted = remaining < sizeof(buffer) ? (size_t)remaining : sizeof(buffer);
            const ssize_t count = pread(fd, buffer, wanted, (off_t)offset);
            assert(count == (ssize_t)wanted);
            assert(finduas_sha256_update(&exact, buffer, wanted) == 1);
            sha_update_with_flip(&first, buffer, wanted, offset, 0u);
            sha_update_with_flip(
                &middle,
                buffer,
                wanted,
                offset,
                profile->exact_file_size / 2u);
            sha_update_with_flip(
                &last,
                buffer,
                wanted,
                offset,
                profile->exact_file_size - 1u);
            offset += wanted;
        }
        uint8_t exact_digest[32];
        uint8_t mutated_digest[32];
        assert(finduas_sha256_finish(&exact, exact_digest) == 1);
        assert(finduas_constant_time_equal(
                   exact_digest,
                   profile->whole_file_sha256,
                   sizeof(exact_digest)) == 1);
        assert(finduas_sha256_finish(&first, mutated_digest) == 1);
        assert(finduas_constant_time_equal(
                   mutated_digest,
                   profile->whole_file_sha256,
                   sizeof(mutated_digest)) == 0);
        assert(finduas_sha256_finish(&middle, mutated_digest) == 1);
        assert(finduas_constant_time_equal(
                   mutated_digest,
                   profile->whole_file_sha256,
                   sizeof(mutated_digest)) == 0);
        assert(finduas_sha256_finish(&last, mutated_digest) == 1);
        assert(finduas_constant_time_equal(
                   mutated_digest,
                   profile->whole_file_sha256,
                   sizeof(mutated_digest)) == 0);
        assert(close(fd) == 0);

        FinduasModuleProfile changed = *profile;
        changed.elf_header[24] ^= 1u;
        assert(finduas_identity_header_phdr_match(
                   &changed,
                   header,
                   phdrs,
                   FINDUAS_PROFILE_PHDR_COUNT) == 0);
        changed = *profile;
        changed.phdrs[6].p_offset = changed.phdrs[6].p_vaddr;
        assert(finduas_identity_profile_is_well_formed(&changed) == 0);
        changed = *profile;
        changed.exact_phnum = 6u;
        assert(finduas_identity_profile_is_well_formed(&changed) == 0);
    }
}

enum MapsMutation {
    MAPS_EXACT = 0,
    MAPS_WRONG_INODE,
    MAPS_WRONG_DEVICE,
    MAPS_WRONG_OFFSET,
    MAPS_SHARED,
    MAPS_UNREADABLE,
    MAPS_GAP,
    MAPS_HIGH_LOAD_VADDR_OFFSET,
    MAPS_SPLIT_FIRST,
    MAPS_DELETED_SOURCE,
};

static size_t append_map_line(
    char *output,
    size_t used,
    size_t capacity,
    uintptr_t start,
    uintptr_t end,
    char readable,
    char writable,
    char executable,
    char sharing,
    uint64_t offset,
    uint32_t major_value,
    uint32_t minor_value,
    uint64_t inode,
    const char *path) {
    const int count = snprintf(
        output + used,
        capacity - used,
        "%llx-%llx %c%c%c%c %llx %x:%x %llu %s\n",
        (unsigned long long)start,
        (unsigned long long)end,
        readable,
        writable,
        executable,
        sharing,
        (unsigned long long)offset,
        major_value,
        minor_value,
        (unsigned long long)inode,
        path);
    assert(count > 0 && (size_t)count < capacity - used);
    return used + (size_t)count;
}

static size_t build_maps_fixture(
    const FinduasModuleProfile *profile,
    uintptr_t base,
    enum MapsMutation mutation,
    char *output,
    size_t capacity) {
    size_t used = 0u;
    size_t load_number = 0u;
    for (size_t index = 0u; index < profile->exact_phnum; ++index) {
        const FinduasElf64Phdr *phdr = &profile->phdrs[index];
        if (phdr->p_type != FINDUAS_PT_LOAD || phdr->p_filesz == 0u) {
            continue;
        }
        const uintptr_t start = base + (uintptr_t)(phdr->p_vaddr & ~UINT64_C(0xfff));
        uintptr_t end = base +
            (uintptr_t)((phdr->p_vaddr + phdr->p_filesz + UINT64_C(0xfff)) & ~UINT64_C(0xfff));
        uint64_t offset = phdr->p_offset & ~UINT64_C(0xfff);
        uint64_t inode = mutation == MAPS_WRONG_INODE && load_number == 0u ? 43u : 42u;
        uint32_t major_value =
            mutation == MAPS_WRONG_DEVICE && load_number == 0u ? 0xfeu : 0xfdu;
        char sharing = mutation == MAPS_SHARED && load_number == 0u ? 's' : 'p';
        char readable = mutation == MAPS_UNREADABLE && load_number == 0u ? '-' : 'r';
        if (mutation == MAPS_WRONG_OFFSET && load_number == 0u) {
            offset += FINDUAS_RUNTIME_PAGE_SIZE;
        }
        if (mutation == MAPS_HIGH_LOAD_VADDR_OFFSET && load_number == 3u) {
            offset = phdr->p_vaddr & ~UINT64_C(0xfff);
        }
        if (mutation == MAPS_GAP && load_number == 0u) {
            end -= FINDUAS_RUNTIME_PAGE_SIZE;
        }
        const char writable = (phdr->p_flags & FINDUAS_PF_W) != 0u ? 'w' : '-';
        const char executable = (phdr->p_flags & FINDUAS_PF_X) != 0u ? 'x' : '-';
        const char *path = mutation == MAPS_DELETED_SOURCE && load_number == 0u
            ? "/data/app/lib/arm64/module.so (deleted)"
            : "/data/app/a b/lib/arm64/module.so";
        if (mutation == MAPS_SPLIT_FIRST && load_number == 0u) {
            const uintptr_t split = start + 2u * FINDUAS_RUNTIME_PAGE_SIZE;
            used = append_map_line(
                output, used, capacity, start, split, readable, writable, executable, sharing,
                offset, major_value, 1u, inode, path);
            used = append_map_line(
                output, used, capacity, split, end, readable, writable, executable, sharing,
                offset + 2u * FINDUAS_RUNTIME_PAGE_SIZE,
                major_value, 1u, inode, path);
        } else {
            used = append_map_line(
                output, used, capacity, start, end, readable, writable, executable, sharing,
                offset, major_value, 1u, inode, path);
        }
        ++load_number;
    }
    return used;
}

static enum FinduasIdentityError parse_maps_fixture(
    enum MapsMutation mutation,
    FinduasMapsSnapshot *snapshot,
    int remove_final_newline) {
    char text[2048];
    const FinduasModuleProfile *profile =
        &kFinduasModuleProfiles[FINDUAS_MODULE_SDK_JNI];
    const uintptr_t base = UINT64_C(0x100000000);
    size_t size = build_maps_fixture(profile, base, mutation, text, sizeof(text));
    if (remove_final_newline) {
        --size;
    }
    FinduasMapsParser parser;
    finduas_maps_parser_init(&parser, profile, base, 0xfdu, 1u, 42u, snapshot);
    for (size_t offset = 0u; offset < size;) {
        const size_t remaining = size - offset;
        const size_t chunk = remaining < 17u ? remaining : 17u;
        if (!finduas_maps_parser_feed(&parser, (const uint8_t *)text + offset, chunk)) {
            return parser.error;
        }
        offset += chunk;
    }
    return finduas_maps_parser_finish(&parser);
}

static void test_maps_and_paths(void) {
    const char *exact_path = "/data/app/pkg/lib/arm64/libsdk_jni.so";
    assert(finduas_identity_source_path_is_exact_extracted(
               exact_path, strlen(exact_path)) == 1);
    const char *apk = "/data/app/base.apk!/lib/arm64-v8a/libsdk_jni.so";
    assert(finduas_identity_source_path_is_exact_extracted(apk, strlen(apk)) == 0);
    const char *deleted = "/data/app/libsdk_jni.so (deleted)";
    assert(finduas_identity_source_path_is_exact_extracted(deleted, strlen(deleted)) == 0);
    const char *memfd = "/memfd:libsdk_jni.so";
    assert(finduas_identity_source_path_is_exact_extracted(memfd, strlen(memfd)) == 0);
    assert(finduas_identity_source_path_is_exact_extracted("relative.so", 11u) == 0);

    FinduasMapsSnapshot exact;
    FinduasMapsSnapshot split;
    assert(parse_maps_fixture(MAPS_EXACT, &exact, 0) == FINDUAS_IDENTITY_OK);
    assert(parse_maps_fixture(MAPS_SPLIT_FIRST, &split, 0) == FINDUAS_IDENTITY_OK);
    assert(exact.count == 4u && split.count == 5u);
    assert(parse_maps_fixture(MAPS_WRONG_INODE, &split, 0) ==
           FINDUAS_IDENTITY_MAP_INODE_MISMATCH);
    assert(parse_maps_fixture(MAPS_WRONG_DEVICE, &split, 0) ==
           FINDUAS_IDENTITY_MAP_INODE_MISMATCH);
    assert(parse_maps_fixture(MAPS_WRONG_OFFSET, &split, 0) ==
           FINDUAS_IDENTITY_MAP_OFFSET_MISMATCH);
    assert(parse_maps_fixture(MAPS_SHARED, &split, 0) ==
           FINDUAS_IDENTITY_MAP_PERMISSION_MISMATCH);
    assert(parse_maps_fixture(MAPS_UNREADABLE, &split, 0) ==
           FINDUAS_IDENTITY_MAP_PERMISSION_MISMATCH);
    assert(parse_maps_fixture(MAPS_GAP, &split, 0) == FINDUAS_IDENTITY_MAP_CARDINALITY);
    assert(parse_maps_fixture(MAPS_HIGH_LOAD_VADDR_OFFSET, &split, 0) ==
           FINDUAS_IDENTITY_MAP_OFFSET_MISMATCH);
    assert(parse_maps_fixture(MAPS_DELETED_SOURCE, &split, 0) ==
           FINDUAS_IDENTITY_SOURCE_KIND_MISMATCH);
    assert(parse_maps_fixture(MAPS_EXACT, &split, 1) ==
           FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT);

    split = exact;
    assert(finduas_maps_snapshots_equal(&exact, &split) == 1);
    split.entries[0].file_offset += FINDUAS_RUNTIME_PAGE_SIZE;
    assert(finduas_maps_snapshots_equal(&exact, &split) == 0);
    assert(finduas_snapshot_contains_readable_range(
               &exact,
               exact.entries[0].start,
               FINDUAS_RUNTIME_PAGE_SIZE) == 1);
    assert(finduas_snapshot_contains_readable_range(
               &exact,
               exact.entries[0].start - FINDUAS_RUNTIME_PAGE_SIZE,
               FINDUAS_RUNTIME_PAGE_SIZE) == 0);

    FinduasMapsParser parser;
    char overlong[FINDUAS_MAPS_LINE_SIZE_LIMIT + 1u];
    memset(overlong, 'a', sizeof(overlong));
    finduas_maps_parser_init(
        &parser,
        &kFinduasModuleProfiles[FINDUAS_MODULE_SDK_JNI],
        UINT64_C(0x100000000),
        0xfdu,
        1u,
        42u,
        &split);
    assert(finduas_maps_parser_feed(
               &parser,
               (const uint8_t *)overlong,
               sizeof(overlong)) == 0);
    assert(parser.error == FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT);
}

static void test_nonwritable_memory_compare(void) {
    const FinduasModuleProfile *profile =
        &kFinduasModuleProfiles[FINDUAS_MODULE_SDK_JNI];
    uint8_t file_bytes[64];
    uint8_t memory_bytes[64];
    for (size_t index = 0u; index < sizeof(file_bytes); ++index) {
        file_bytes[index] = (uint8_t)(index * 3u + 1u);
    }
    memcpy(memory_bytes, file_bytes, sizeof(memory_bytes));
    FinduasMapsSnapshot snapshot;
    memset(&snapshot, 0, sizeof(snapshot));
    snapshot.count = 1u;
    snapshot.entries[0].start = (uintptr_t)memory_bytes;
    snapshot.entries[0].end = (uintptr_t)memory_bytes + sizeof(memory_bytes);
    snapshot.entries[0].readable = 1u;
    snapshot.entries[0].private_mapping = 1u;
    assert(finduas_identity_compare_nonwritable_chunk(
               (uintptr_t)memory_bytes,
               profile,
               &snapshot,
               0u,
               file_bytes,
               sizeof(file_bytes)) == 1);
    memory_bytes[31] ^= 1u;
    assert(finduas_identity_compare_nonwritable_chunk(
               (uintptr_t)memory_bytes,
               profile,
               &snapshot,
               0u,
               file_bytes,
               sizeof(file_bytes)) == 0);
    memory_bytes[31] ^= 1u;

    const FinduasElf64Phdr *writable = &profile->phdrs[1];
    assert((writable->p_flags & FINDUAS_PF_W) != 0u);
    assert(finduas_identity_compare_nonwritable_chunk(
               1u,
               profile,
               &snapshot,
               writable->p_offset,
               file_bytes,
               sizeof(file_bytes)) == 1);

    const FinduasElf64Phdr *high = &profile->phdrs[6];
    assert((high->p_flags & FINDUAS_PF_W) == 0u && high->p_offset != high->p_vaddr);
    assert((uintptr_t)memory_bytes > (uintptr_t)high->p_vaddr);
    const uintptr_t high_bias = (uintptr_t)memory_bytes - (uintptr_t)high->p_vaddr;
    assert(finduas_identity_compare_nonwritable_chunk(
               high_bias,
               profile,
               &snapshot,
               high->p_offset,
               file_bytes,
               sizeof(file_bytes)) == 1);
    memory_bytes[0] ^= 1u;
    assert(finduas_identity_compare_nonwritable_chunk(
               high_bias,
               profile,
               &snapshot,
               high->p_offset,
               file_bytes,
               sizeof(file_bytes)) == 0);
}

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
    assert(kFinduasModuleProfiles[FINDUAS_MODULE_SDK_JNI].exact_file_size == UINT64_C(87313856));
    assert(kFinduasModuleProfiles[FINDUAS_MODULE_SDK_KEY_VALUE].exact_file_size == UINT64_C(12684576));
    assert(kFinduasModuleProfiles[FINDUAS_MODULE_SDK_BASE].exact_file_size == UINT64_C(7720240));
    for (int index = 0; index < FINDUAS_MODULE_COUNT; ++index) {
        assert(finduas_identity_profile_is_well_formed(&kFinduasModuleProfiles[index]) == 1);
        assert(kFinduasModuleProfiles[index].source_kind == FINDUAS_SOURCE_EXTRACTED_ELF_V1);
        assert(kFinduasModuleProfiles[index].exact_phnum == FINDUAS_PROFILE_PHDR_COUNT);
        assert(kFinduasModuleProfiles[index].phdrs[6].p_offset !=
               kFinduasModuleProfiles[index].phdrs[6].p_vaddr);
    }

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
    test_sha256();
    test_build_id_parser();
    test_semantic_and_route_policy();
    test_target_profile_shape();
    test_exact_target_files();
    test_maps_and_paths();
    test_nonwritable_memory_compare();
    return 0;
}
