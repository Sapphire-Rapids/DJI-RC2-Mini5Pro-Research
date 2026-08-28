#ifndef FINDUAS_EID_ROUTE_V23_IDENTITY_CORE_H
#define FINDUAS_EID_ROUTE_V23_IDENTITY_CORE_H

#include <stddef.h>
#include <stdint.h>

#include "target_profile.h"

#define FINDUAS_RUNTIME_PAGE_SIZE 4096u
#define FINDUAS_MAPS_TOTAL_BYTE_LIMIT (16u * 1024u * 1024u)
#define FINDUAS_MAPS_LINE_LIMIT 65536u
#define FINDUAS_MAPS_LINE_SIZE_LIMIT 8192u
#define FINDUAS_RELEVANT_VMA_LIMIT 256u

enum FinduasIdentityError {
    FINDUAS_IDENTITY_OK = 0,
    FINDUAS_IDENTITY_PATH_EMPTY_OR_TRUNCATED = 1,
    FINDUAS_IDENTITY_PATH_NOT_ABSOLUTE = 2,
    FINDUAS_IDENTITY_SOURCE_KIND_MISMATCH = 3,
    FINDUAS_IDENTITY_OPEN_FAILED = 4,
    FINDUAS_IDENTITY_NOT_REGULAR = 5,
    FINDUAS_IDENTITY_SIZE_MISMATCH = 6,
    FINDUAS_IDENTITY_STAT_CHANGED = 7,
    FINDUAS_IDENTITY_MAPS_OPEN_FAILED = 8,
    FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT = 9,
    FINDUAS_IDENTITY_MAP_CARDINALITY = 10,
    FINDUAS_IDENTITY_MAP_INODE_MISMATCH = 11,
    FINDUAS_IDENTITY_MAP_OFFSET_MISMATCH = 12,
    FINDUAS_IDENTITY_MAP_PERMISSION_MISMATCH = 13,
    FINDUAS_IDENTITY_PHDR_MISMATCH = 14,
    FINDUAS_IDENTITY_FILE_READ_FAILED = 15,
    FINDUAS_IDENTITY_WHOLE_SHA256_MISMATCH = 16,
    FINDUAS_IDENTITY_NONWRITABLE_LOAD_MISMATCH = 17,
    FINDUAS_IDENTITY_LINKER_EPOCH_CHANGED = 18,
    FINDUAS_IDENTITY_CLOSE_FAILED = 19,
    FINDUAS_IDENTITY_ZIP_UNSUPPORTED_CURRENT_PROFILE = 20,
    FINDUAS_IDENTITY_WRITABLE_ORIGINAL_NONWRITABLE_LOAD = 21,
};

typedef struct FinduasRelevantVma {
    uintptr_t start;
    uintptr_t end;
    uint64_t file_offset;
    uint64_t inode;
    uint32_t dev_major;
    uint32_t dev_minor;
    uint8_t readable;
    uint8_t writable;
    uint8_t executable;
    uint8_t private_mapping;
} FinduasRelevantVma;

typedef struct FinduasMapsSnapshot {
    FinduasRelevantVma entries[FINDUAS_RELEVANT_VMA_LIMIT];
    size_t count;
} FinduasMapsSnapshot;

typedef struct FinduasMapsParser {
    const FinduasModuleProfile *profile;
    uintptr_t load_bias;
    uint32_t expected_dev_major;
    uint32_t expected_dev_minor;
    uint64_t expected_inode;
    FinduasMapsSnapshot *snapshot;
    enum FinduasIdentityError error;
    uint64_t total_bytes;
    uint64_t line_count;
    size_t line_size;
    uint8_t saw_final_newline;
    char line[FINDUAS_MAPS_LINE_SIZE_LIMIT + 1u];
} FinduasMapsParser;

int finduas_identity_source_path_is_exact_extracted(
    const char *path,
    size_t path_length);

int finduas_identity_profile_is_well_formed(const FinduasModuleProfile *profile);

int finduas_identity_header_phdr_match(
    const FinduasModuleProfile *profile,
    const uint8_t file_header[FINDUAS_ELF_HEADER_SIZE],
    const FinduasElf64Phdr *file_phdrs,
    size_t file_phnum);

void finduas_maps_parser_init(
    FinduasMapsParser *parser,
    const FinduasModuleProfile *profile,
    uintptr_t load_bias,
    uint32_t expected_dev_major,
    uint32_t expected_dev_minor,
    uint64_t expected_inode,
    FinduasMapsSnapshot *snapshot);

int finduas_maps_parser_feed(
    FinduasMapsParser *parser,
    const uint8_t *data,
    size_t size);

enum FinduasIdentityError finduas_maps_parser_finish(FinduasMapsParser *parser);

int finduas_maps_snapshots_equal(
    const FinduasMapsSnapshot *left,
    const FinduasMapsSnapshot *right);

int finduas_snapshot_contains_readable_range(
    const FinduasMapsSnapshot *snapshot,
    uintptr_t start,
    size_t size);

int finduas_snapshot_contains_readable_nonwritable_range(
    const FinduasMapsSnapshot *snapshot,
    uintptr_t start,
    size_t size);

int finduas_identity_compare_nonwritable_chunk(
    uintptr_t load_bias,
    const FinduasModuleProfile *profile,
    const FinduasMapsSnapshot *snapshot,
    uint64_t chunk_offset,
    const uint8_t *chunk,
    size_t chunk_size);

#endif
