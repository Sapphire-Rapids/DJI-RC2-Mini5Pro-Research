#include "identity_core.h"

#include <limits.h>
#include <string.h>

#define Elf64_Ehdr FinduasElf64Ehdr
#define Elf64_Phdr FinduasElf64Phdr
#define ET_DYN FINDUAS_ET_DYN
#define EM_AARCH64 FINDUAS_EM_AARCH64
#define EV_CURRENT FINDUAS_EV_CURRENT
#define PT_LOAD FINDUAS_PT_LOAD

static int checked_add_uint64(uint64_t left, uint64_t right, uint64_t *output) {
    if (output == NULL || left > UINT64_MAX - right) {
        return 0;
    }
    *output = left + right;
    return 1;
}

static int checked_add_uintptr(uintptr_t left, uintptr_t right, uintptr_t *output) {
    if (output == NULL || left > UINTPTR_MAX - right) {
        return 0;
    }
    *output = left + right;
    return 1;
}

static int text_contains(const char *text, size_t text_size, const char *needle) {
    size_t needle_size = 0u;
    while (needle[needle_size] != '\0') {
        ++needle_size;
    }
    if (needle_size == 0u || needle_size > text_size) {
        return 0;
    }
    for (size_t index = 0u; index <= text_size - needle_size; ++index) {
        if (memcmp(text + index, needle, needle_size) == 0) {
            return 1;
        }
    }
    return 0;
}

int finduas_identity_source_path_is_exact_extracted(
    const char *path,
    size_t path_length) {
    if (path == NULL || path_length == 0u || path_length >= 4096u ||
        path[path_length] != '\0') {
        return 0;
    }
    if (path[0] != '/') {
        return 0;
    }
    if (text_contains(path, path_length, "!/") ||
        text_contains(path, path_length, " (deleted)") ||
        text_contains(path, path_length, "/memfd:") ||
        text_contains(path, path_length, "[anon:")) {
        return 0;
    }
    return 1;
}

static int phdr_file_range_is_valid(
    const FinduasModuleProfile *profile,
    const Elf64_Phdr *header) {
    uint64_t end = 0u;
    return header->p_filesz <= header->p_memsz &&
           checked_add_uint64(header->p_offset, header->p_filesz, &end) &&
           end <= profile->exact_file_size;
}

int finduas_identity_profile_is_well_formed(const FinduasModuleProfile *profile) {
    if (profile == NULL || profile->basename == NULL ||
        profile->source_kind != FINDUAS_SOURCE_EXTRACTED_ELF_V1 ||
        profile->exact_file_size == 0u ||
        profile->exact_phnum != FINDUAS_PROFILE_PHDR_COUNT ||
        profile->elf_header[0] != 0x7fu ||
        profile->elf_header[1] != 'E' ||
        profile->elf_header[2] != 'L' ||
        profile->elf_header[3] != 'F' ||
        profile->elf_header[4] != 2u ||
        profile->elf_header[5] != 1u) {
        return 0;
    }
    Elf64_Ehdr header;
    memcpy(&header, profile->elf_header, sizeof(header));
    if (header.e_type != ET_DYN || header.e_machine != EM_AARCH64 ||
        header.e_version != EV_CURRENT || header.e_ehsize != sizeof(Elf64_Ehdr) ||
        header.e_phoff != sizeof(Elf64_Ehdr) ||
        header.e_phentsize != sizeof(Elf64_Phdr) ||
        header.e_phnum != FINDUAS_PROFILE_PHDR_COUNT) {
        return 0;
    }

    size_t load_count = 0u;
    for (size_t index = 0u; index < FINDUAS_PROFILE_PHDR_COUNT; ++index) {
        const Elf64_Phdr *phdr = &profile->phdrs[index];
        if (!phdr_file_range_is_valid(profile, phdr)) {
            return 0;
        }
        if (phdr->p_type == PT_LOAD) {
            ++load_count;
            if (phdr->p_filesz == 0u ||
                phdr->p_align < FINDUAS_RUNTIME_PAGE_SIZE ||
                (phdr->p_align % FINDUAS_RUNTIME_PAGE_SIZE) != 0u ||
                (phdr->p_offset & (FINDUAS_RUNTIME_PAGE_SIZE - 1u)) !=
                    (phdr->p_vaddr & (FINDUAS_RUNTIME_PAGE_SIZE - 1u))) {
                return 0;
            }
        }
    }
    if (load_count != 4u) {
        return 0;
    }

    for (size_t left = 0u; left < FINDUAS_PROFILE_PHDR_COUNT; ++left) {
        const Elf64_Phdr *a = &profile->phdrs[left];
        if (a->p_type != PT_LOAD || a->p_filesz == 0u) {
            continue;
        }
        const uint64_t a_start = a->p_vaddr & ~(uint64_t)(FINDUAS_RUNTIME_PAGE_SIZE - 1u);
        uint64_t a_raw_end = 0u;
        if (!checked_add_uint64(a->p_vaddr, a->p_filesz, &a_raw_end) ||
            a_raw_end > UINT64_MAX - (FINDUAS_RUNTIME_PAGE_SIZE - 1u)) {
            return 0;
        }
        const uint64_t a_end =
            (a_raw_end + FINDUAS_RUNTIME_PAGE_SIZE - 1u) &
            ~(uint64_t)(FINDUAS_RUNTIME_PAGE_SIZE - 1u);
        for (size_t right = left + 1u; right < FINDUAS_PROFILE_PHDR_COUNT; ++right) {
            const Elf64_Phdr *b = &profile->phdrs[right];
            if (b->p_type != PT_LOAD || b->p_filesz == 0u) {
                continue;
            }
            const uint64_t b_start = b->p_vaddr & ~(uint64_t)(FINDUAS_RUNTIME_PAGE_SIZE - 1u);
            uint64_t b_raw_end = 0u;
            if (!checked_add_uint64(b->p_vaddr, b->p_filesz, &b_raw_end) ||
                b_raw_end > UINT64_MAX - (FINDUAS_RUNTIME_PAGE_SIZE - 1u)) {
                return 0;
            }
            const uint64_t b_end =
                (b_raw_end + FINDUAS_RUNTIME_PAGE_SIZE - 1u) &
                ~(uint64_t)(FINDUAS_RUNTIME_PAGE_SIZE - 1u);
            const uint64_t overlap_start = a_start > b_start ? a_start : b_start;
            const uint64_t overlap_end = a_end < b_end ? a_end : b_end;
            if (overlap_start < overlap_end) {
                const uint64_t a_offset =
                    (a->p_offset & ~(uint64_t)(FINDUAS_RUNTIME_PAGE_SIZE - 1u)) +
                    (overlap_start - a_start);
                const uint64_t b_offset =
                    (b->p_offset & ~(uint64_t)(FINDUAS_RUNTIME_PAGE_SIZE - 1u)) +
                    (overlap_start - b_start);
                if (a_offset != b_offset) {
                    return 0;
                }
            }
        }
    }
    return 1;
}

int finduas_identity_header_phdr_match(
    const FinduasModuleProfile *profile,
    const uint8_t file_header[FINDUAS_ELF_HEADER_SIZE],
    const Elf64_Phdr *file_phdrs,
    size_t file_phnum) {
    return finduas_identity_profile_is_well_formed(profile) &&
           file_header != NULL && file_phdrs != NULL &&
           file_phnum == profile->exact_phnum &&
           memcmp(file_header, profile->elf_header, FINDUAS_ELF_HEADER_SIZE) == 0 &&
           memcmp(
               file_phdrs,
               profile->phdrs,
               sizeof(Elf64_Phdr) * FINDUAS_PROFILE_PHDR_COUNT) == 0;
}

static int parse_unsigned(
    const char *line,
    size_t size,
    size_t *cursor,
    unsigned int base,
    uint64_t *value) {
    if (line == NULL || cursor == NULL || value == NULL ||
        (base != 10u && base != 16u) || *cursor >= size) {
        return 0;
    }
    uint64_t result = 0u;
    size_t count = 0u;
    while (*cursor < size) {
        const unsigned char character = (unsigned char)line[*cursor];
        unsigned int digit = UINT_MAX;
        if (character >= '0' && character <= '9') {
            digit = (unsigned int)(character - '0');
        } else if (base == 16u && character >= 'a' && character <= 'f') {
            digit = 10u + (unsigned int)(character - 'a');
        } else if (base == 16u && character >= 'A' && character <= 'F') {
            digit = 10u + (unsigned int)(character - 'A');
        }
        if (digit >= base) {
            break;
        }
        if (result > (UINT64_MAX - digit) / base) {
            return 0;
        }
        result = result * base + digit;
        ++*cursor;
        ++count;
    }
    if (count == 0u) {
        return 0;
    }
    *value = result;
    return 1;
}

static int consume_character(
    const char *line,
    size_t size,
    size_t *cursor,
    char expected) {
    if (*cursor >= size || line[*cursor] != expected) {
        return 0;
    }
    ++*cursor;
    return 1;
}

static int range_for_load(
    uintptr_t load_bias,
    const Elf64_Phdr *phdr,
    uintptr_t *start,
    uintptr_t *end,
    uint64_t *offset) {
    const uintptr_t page_mask = (uintptr_t)FINDUAS_RUNTIME_PAGE_SIZE - 1u;
    const uintptr_t vaddr_page = (uintptr_t)phdr->p_vaddr & ~page_mask;
    uint64_t raw_end64 = 0u;
    if (phdr->p_type != PT_LOAD || phdr->p_filesz == 0u ||
        phdr->p_vaddr > UINTPTR_MAX || phdr->p_filesz > UINTPTR_MAX ||
        !checked_add_uint64(phdr->p_vaddr, phdr->p_filesz, &raw_end64) ||
        raw_end64 > UINTPTR_MAX ||
        raw_end64 > UINTPTR_MAX - page_mask ||
        !checked_add_uintptr(load_bias, vaddr_page, start)) {
        return 0;
    }
    const uintptr_t end_page = ((uintptr_t)raw_end64 + page_mask) & ~page_mask;
    if (!checked_add_uintptr(load_bias, end_page, end) || *end <= *start) {
        return 0;
    }
    *offset = phdr->p_offset & ~(uint64_t)page_mask;
    return 1;
}

static int ranges_overlap(uintptr_t a_start, uintptr_t a_end, uintptr_t b_start, uintptr_t b_end) {
    return a_start < b_end && b_start < a_end;
}

static enum FinduasIdentityError process_maps_line(
    FinduasMapsParser *parser,
    const char *line,
    size_t size) {
    size_t cursor = 0u;
    uint64_t start64 = 0u;
    uint64_t end64 = 0u;
    uint64_t offset = 0u;
    uint64_t dev_major64 = 0u;
    uint64_t dev_minor64 = 0u;
    uint64_t inode = 0u;
    if (!parse_unsigned(line, size, &cursor, 16u, &start64) ||
        !consume_character(line, size, &cursor, '-') ||
        !parse_unsigned(line, size, &cursor, 16u, &end64) ||
        !consume_character(line, size, &cursor, ' ') ||
        cursor + 4u > size) {
        return FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT;
    }
    const char read_flag = line[cursor++];
    const char write_flag = line[cursor++];
    const char execute_flag = line[cursor++];
    const char share_flag = line[cursor++];
    if ((read_flag != 'r' && read_flag != '-') ||
        (write_flag != 'w' && write_flag != '-') ||
        (execute_flag != 'x' && execute_flag != '-') ||
        (share_flag != 'p' && share_flag != 's') ||
        !consume_character(line, size, &cursor, ' ') ||
        !parse_unsigned(line, size, &cursor, 16u, &offset) ||
        !consume_character(line, size, &cursor, ' ') ||
        !parse_unsigned(line, size, &cursor, 16u, &dev_major64) ||
        !consume_character(line, size, &cursor, ':') ||
        !parse_unsigned(line, size, &cursor, 16u, &dev_minor64) ||
        !consume_character(line, size, &cursor, ' ') ||
        !parse_unsigned(line, size, &cursor, 10u, &inode) ||
        (cursor < size && line[cursor] != ' ') ||
        start64 >= end64 || start64 > UINTPTR_MAX || end64 > UINTPTR_MAX ||
        dev_major64 > UINT32_MAX || dev_minor64 > UINT32_MAX) {
        return FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT;
    }

    FinduasRelevantVma record = {
        .start = (uintptr_t)start64,
        .end = (uintptr_t)end64,
        .file_offset = offset,
        .inode = inode,
        .dev_major = (uint32_t)dev_major64,
        .dev_minor = (uint32_t)dev_minor64,
        .readable = read_flag == 'r' ? 1u : 0u,
        .writable = write_flag == 'w' ? 1u : 0u,
        .executable = execute_flag == 'x' ? 1u : 0u,
        .private_mapping = share_flag == 'p' ? 1u : 0u,
    };

    int relevant = 0;
    for (size_t index = 0u; index < parser->profile->exact_phnum; ++index) {
        const Elf64_Phdr *phdr = &parser->profile->phdrs[index];
        uintptr_t segment_start = 0u;
        uintptr_t segment_end = 0u;
        uint64_t segment_offset = 0u;
        if (phdr->p_type != PT_LOAD || phdr->p_filesz == 0u) {
            continue;
        }
        if (!range_for_load(
                parser->load_bias,
                phdr,
                &segment_start,
                &segment_end,
                &segment_offset)) {
            return FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT;
        }
        if (!ranges_overlap(record.start, record.end, segment_start, segment_end)) {
            continue;
        }
        relevant = 1;
        if (record.readable == 0u || record.private_mapping == 0u) {
            return FINDUAS_IDENTITY_MAP_PERMISSION_MISMATCH;
        }
        if ((phdr->p_flags & FINDUAS_PF_W) == 0u && record.writable != 0u) {
            return FINDUAS_IDENTITY_WRITABLE_ORIGINAL_NONWRITABLE_LOAD;
        }
        if (record.inode == 0u || record.inode != parser->expected_inode ||
            record.dev_major != parser->expected_dev_major ||
            record.dev_minor != parser->expected_dev_minor) {
            return FINDUAS_IDENTITY_MAP_INODE_MISMATCH;
        }
        const uintptr_t intersection =
            record.start > segment_start ? record.start : segment_start;
        uint64_t observed_offset = 0u;
        uint64_t expected_offset = 0u;
        if (!checked_add_uint64(
                record.file_offset,
                (uint64_t)(intersection - record.start),
                &observed_offset) ||
            !checked_add_uint64(
                segment_offset,
                (uint64_t)(intersection - segment_start),
                &expected_offset) ||
            observed_offset != expected_offset) {
            return FINDUAS_IDENTITY_MAP_OFFSET_MISMATCH;
        }
    }
    if (!relevant) {
        return FINDUAS_IDENTITY_OK;
    }
    if (text_contains(line + cursor, size - cursor, " (deleted)")) {
        return FINDUAS_IDENTITY_SOURCE_KIND_MISMATCH;
    }
    if (parser->snapshot->count >= FINDUAS_RELEVANT_VMA_LIMIT) {
        return FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT;
    }
    if (parser->snapshot->count != 0u &&
        parser->snapshot->entries[parser->snapshot->count - 1u].end > record.start) {
        return FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT;
    }
    parser->snapshot->entries[parser->snapshot->count++] = record;
    return FINDUAS_IDENTITY_OK;
}

void finduas_maps_parser_init(
    FinduasMapsParser *parser,
    const FinduasModuleProfile *profile,
    uintptr_t load_bias,
    uint32_t expected_dev_major,
    uint32_t expected_dev_minor,
    uint64_t expected_inode,
    FinduasMapsSnapshot *snapshot) {
    if (parser == NULL) {
        return;
    }
    memset(parser, 0, sizeof(*parser));
    parser->profile = profile;
    parser->load_bias = load_bias;
    parser->expected_dev_major = expected_dev_major;
    parser->expected_dev_minor = expected_dev_minor;
    parser->expected_inode = expected_inode;
    parser->snapshot = snapshot;
    if (snapshot != NULL) {
        memset(snapshot, 0, sizeof(*snapshot));
    }
    if (!finduas_identity_profile_is_well_formed(profile) ||
        load_bias == 0u ||
        (expected_dev_major == 0u && expected_dev_minor == 0u) ||
        expected_inode == 0u || snapshot == NULL) {
        parser->error = FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT;
    }
}

int finduas_maps_parser_feed(
    FinduasMapsParser *parser,
    const uint8_t *data,
    size_t size) {
    if (parser == NULL || (size != 0u && data == NULL) ||
        parser->error != FINDUAS_IDENTITY_OK) {
        return 0;
    }
    if ((uint64_t)size > FINDUAS_MAPS_TOTAL_BYTE_LIMIT - parser->total_bytes) {
        parser->error = FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT;
        return 0;
    }
    parser->total_bytes += (uint64_t)size;
    for (size_t index = 0u; index < size; ++index) {
        const uint8_t character = data[index];
        if (character == '\0') {
            parser->error = FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT;
            return 0;
        }
        if (character != '\n') {
            parser->saw_final_newline = 0u;
            if (parser->line_size >= FINDUAS_MAPS_LINE_SIZE_LIMIT) {
                parser->error = FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT;
                return 0;
            }
            parser->line[parser->line_size++] = (char)character;
            continue;
        }
        parser->saw_final_newline = 1u;
        if (parser->line_size == 0u || parser->line_count >= FINDUAS_MAPS_LINE_LIMIT) {
            parser->error = FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT;
            return 0;
        }
        parser->line[parser->line_size] = '\0';
        ++parser->line_count;
        parser->error = process_maps_line(parser, parser->line, parser->line_size);
        parser->line_size = 0u;
        if (parser->error != FINDUAS_IDENTITY_OK) {
            return 0;
        }
    }
    return 1;
}

enum FinduasIdentityError finduas_maps_parser_finish(FinduasMapsParser *parser) {
    if (parser == NULL || parser->error != FINDUAS_IDENTITY_OK) {
        return parser == NULL ? FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT : parser->error;
    }
    if (parser->total_bytes == 0u || parser->line_count == 0u ||
        parser->line_size != 0u || parser->saw_final_newline == 0u) {
        return FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT;
    }

    for (size_t index = 0u; index < parser->profile->exact_phnum; ++index) {
        const Elf64_Phdr *phdr = &parser->profile->phdrs[index];
        uintptr_t segment_start = 0u;
        uintptr_t segment_end = 0u;
        uint64_t segment_offset = 0u;
        if (phdr->p_type != PT_LOAD || phdr->p_filesz == 0u) {
            continue;
        }
        if (!range_for_load(
                parser->load_bias,
                phdr,
                &segment_start,
                &segment_end,
                &segment_offset)) {
            return FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT;
        }
        (void)segment_offset;
        uintptr_t cursor = segment_start;
        for (size_t entry_index = 0u;
             entry_index < parser->snapshot->count && cursor < segment_end;
             ++entry_index) {
            const FinduasRelevantVma *entry = &parser->snapshot->entries[entry_index];
            if (!ranges_overlap(entry->start, entry->end, segment_start, segment_end)) {
                continue;
            }
            const uintptr_t overlap_start =
                entry->start > segment_start ? entry->start : segment_start;
            const uintptr_t overlap_end =
                entry->end < segment_end ? entry->end : segment_end;
            if (overlap_start > cursor || overlap_end <= cursor) {
                return FINDUAS_IDENTITY_MAP_CARDINALITY;
            }
            cursor = overlap_end;
        }
        if (cursor != segment_end) {
            return FINDUAS_IDENTITY_MAP_CARDINALITY;
        }
    }
    return FINDUAS_IDENTITY_OK;
}

int finduas_maps_snapshots_equal(
    const FinduasMapsSnapshot *left,
    const FinduasMapsSnapshot *right) {
    if (left == NULL || right == NULL || left->count != right->count) {
        return 0;
    }
    for (size_t index = 0u; index < left->count; ++index) {
        const FinduasRelevantVma *a = &left->entries[index];
        const FinduasRelevantVma *b = &right->entries[index];
        if (a->start != b->start || a->end != b->end ||
            a->file_offset != b->file_offset || a->inode != b->inode ||
            a->dev_major != b->dev_major || a->dev_minor != b->dev_minor ||
            a->readable != b->readable || a->writable != b->writable ||
            a->executable != b->executable || a->private_mapping != b->private_mapping) {
            return 0;
        }
    }
    return 1;
}

static int snapshot_contains_range(
    const FinduasMapsSnapshot *snapshot,
    uintptr_t start,
    size_t size,
    int require_nonwritable) {
    if (snapshot == NULL || size == 0u || start > UINTPTR_MAX - size) {
        return 0;
    }
    const uintptr_t end = start + size;
    uintptr_t cursor = start;
    for (size_t index = 0u; index < snapshot->count && cursor < end; ++index) {
        const FinduasRelevantVma *entry = &snapshot->entries[index];
        if (entry->end <= cursor || entry->start >= end) {
            continue;
        }
        if (entry->start > cursor || entry->readable == 0u ||
            (require_nonwritable != 0 && entry->writable != 0u)) {
            return 0;
        }
        cursor = entry->end < end ? entry->end : end;
    }
    return cursor == end;
}

int finduas_snapshot_contains_readable_range(
    const FinduasMapsSnapshot *snapshot,
    uintptr_t start,
    size_t size) {
    return snapshot_contains_range(snapshot, start, size, 0);
}

int finduas_snapshot_contains_readable_nonwritable_range(
    const FinduasMapsSnapshot *snapshot,
    uintptr_t start,
    size_t size) {
    return snapshot_contains_range(snapshot, start, size, 1);
}

int finduas_identity_compare_nonwritable_chunk(
    uintptr_t load_bias,
    const FinduasModuleProfile *profile,
    const FinduasMapsSnapshot *snapshot,
    uint64_t chunk_offset,
    const uint8_t *chunk,
    size_t chunk_size) {
    uint64_t chunk_end = 0u;
    if (load_bias == 0u || profile == NULL || snapshot == NULL || chunk == NULL ||
        !finduas_identity_profile_is_well_formed(profile) ||
        !checked_add_uint64(chunk_offset, chunk_size, &chunk_end)) {
        return 0;
    }
    for (size_t index = 0u; index < profile->exact_phnum; ++index) {
        const Elf64_Phdr *phdr = &profile->phdrs[index];
        if (phdr->p_type != PT_LOAD || phdr->p_filesz == 0u ||
            (phdr->p_flags & FINDUAS_PF_W) != 0u) {
            continue;
        }
        uint64_t segment_file_end = 0u;
        if (!checked_add_uint64(phdr->p_offset, phdr->p_filesz, &segment_file_end)) {
            return 0;
        }
        const uint64_t overlap_start =
            chunk_offset > phdr->p_offset ? chunk_offset : phdr->p_offset;
        const uint64_t overlap_end = chunk_end < segment_file_end ? chunk_end : segment_file_end;
        if (overlap_start >= overlap_end) {
            continue;
        }
        const uint64_t segment_delta = overlap_start - phdr->p_offset;
        const uint64_t chunk_delta = overlap_start - chunk_offset;
        const uint64_t length64 = overlap_end - overlap_start;
        if (phdr->p_vaddr > UINTPTR_MAX || segment_delta > UINTPTR_MAX ||
            length64 > SIZE_MAX || load_bias > UINTPTR_MAX - (uintptr_t)phdr->p_vaddr ||
            load_bias + (uintptr_t)phdr->p_vaddr > UINTPTR_MAX - (uintptr_t)segment_delta) {
            return 0;
        }
        const uintptr_t memory =
            load_bias + (uintptr_t)phdr->p_vaddr + (uintptr_t)segment_delta;
        const size_t length = (size_t)length64;
        if (!finduas_snapshot_contains_readable_nonwritable_range(
                snapshot,
                memory,
                length) ||
            memcmp((const void *)memory, chunk + (size_t)chunk_delta, length) != 0) {
            return 0;
        }
    }
    return 1;
}
