#include "note_parser.h"

#include <string.h>

#define FINDUAS_NT_GNU_BUILD_ID 3u

static int add_size(size_t left, size_t right, size_t *output) {
    if (left > SIZE_MAX - right) {
        return 0;
    }
    *output = left + right;
    return 1;
}

static int align_four(size_t value, size_t *output) {
    size_t adjusted = 0;
    if (!add_size(value, 3u, &adjusted)) {
        return 0;
    }
    *output = adjusted & ~(size_t)3u;
    return 1;
}

static uint32_t read_u32_le(const uint8_t *source) {
    return ((uint32_t)source[0]) |
           ((uint32_t)source[1] << 8u) |
           ((uint32_t)source[2] << 16u) |
           ((uint32_t)source[3] << 24u);
}

int finduas_parse_unique_gnu_build_id(
    const uint8_t *notes,
    size_t notes_size,
    uint8_t output[FINDUAS_GNU_BUILD_ID_SIZE]) {
    if (notes == NULL || output == NULL) {
        return 0;
    }

    size_t offset = 0;
    unsigned int match_count = 0;
    uint8_t candidate[FINDUAS_GNU_BUILD_ID_SIZE] = {0};

    while (offset < notes_size) {
        size_t header_end = 0;
        if (!add_size(offset, 12u, &header_end) || header_end > notes_size) {
            return 0;
        }

        const uint32_t name_size_u32 = read_u32_le(notes + offset);
        const uint32_t description_size_u32 = read_u32_le(notes + offset + 4u);
        const uint32_t note_type = read_u32_le(notes + offset + 8u);
        const size_t name_size = (size_t)name_size_u32;
        const size_t description_size = (size_t)description_size_u32;
        size_t aligned_name_size = 0;
        size_t aligned_description_size = 0;
        size_t name_offset = header_end;
        size_t description_offset = 0;
        size_t next_offset = 0;

        if (!align_four(name_size, &aligned_name_size) ||
            !align_four(description_size, &aligned_description_size) ||
            !add_size(name_offset, aligned_name_size, &description_offset) ||
            !add_size(description_offset, aligned_description_size, &next_offset) ||
            next_offset > notes_size || next_offset <= offset) {
            return 0;
        }

        const int is_gnu_name =
            name_size == 4u && memcmp(notes + name_offset, "GNU\0", 4u) == 0;
        if (is_gnu_name && note_type == FINDUAS_NT_GNU_BUILD_ID) {
            if (description_size != FINDUAS_GNU_BUILD_ID_SIZE || match_count != 0u) {
                return 0;
            }
            memcpy(candidate, notes + description_offset, FINDUAS_GNU_BUILD_ID_SIZE);
            ++match_count;
        }

        offset = next_offset;
    }

    if (match_count != 1u) {
        return 0;
    }
    memcpy(output, candidate, FINDUAS_GNU_BUILD_ID_SIZE);
    return 1;
}
