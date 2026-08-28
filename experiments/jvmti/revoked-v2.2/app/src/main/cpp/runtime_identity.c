#include "runtime_identity.h"

#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <unistd.h>

#include "sha256.h"

#define Elf64_Ehdr FinduasElf64Ehdr
#define Elf64_Phdr FinduasElf64Phdr

#define FINDUAS_FILE_BUFFER_SIZE (64u * 1024u)
#define FINDUAS_MAPS_READ_SIZE 4096u

typedef struct FinduasFileState {
    uint64_t inode;
    uint64_t size;
    uint64_t nlink;
    uint32_t dev_major;
    uint32_t dev_minor;
    uint32_t mode;
    uint32_t uid;
    uint32_t gid;
    int64_t mtime_seconds;
    int64_t mtime_nanoseconds;
    int64_t ctime_seconds;
    int64_t ctime_nanoseconds;
} FinduasFileState;

typedef struct FinduasIdentityWorkspace {
    uint8_t file_buffer[FINDUAS_FILE_BUFFER_SIZE];
    FinduasMapsSnapshot first[FINDUAS_MODULE_COUNT];
    FinduasMapsSnapshot second[FINDUAS_MODULE_COUNT];
} FinduasIdentityWorkspace;

static FinduasIdentityWorkspace g_identity_workspace;

static int path_contains(const char *path, size_t path_length, const char *needle) {
    size_t needle_length = 0u;
    while (needle[needle_length] != '\0') {
        ++needle_length;
    }
    if (needle_length == 0u || needle_length > path_length) {
        return 0;
    }
    for (size_t index = 0u; index <= path_length - needle_length; ++index) {
        if (memcmp(path + index, needle, needle_length) == 0) {
            return 1;
        }
    }
    return 0;
}

static void set_error(
    FinduasIdentityDiagnostic *diagnostic,
    enum FinduasIdentityError error,
    uint32_t module_id,
    uint32_t stage) {
    diagnostic->error = error;
    diagnostic->module_id = module_id;
    diagnostic->stage = stage;
    diagnostic->errno_value = errno;
}

static int capture_file_state(const struct stat *status, FinduasFileState *state) {
    if (status == NULL || state == NULL || status->st_ino == 0 || status->st_size < 0 ||
        status->st_nlink <= 0) {
        return 0;
    }
    memset(state, 0, sizeof(*state));
    state->inode = (uint64_t)status->st_ino;
    state->size = (uint64_t)status->st_size;
    state->nlink = (uint64_t)status->st_nlink;
    state->dev_major = (uint32_t)major(status->st_dev);
    state->dev_minor = (uint32_t)minor(status->st_dev);
    state->mode = (uint32_t)status->st_mode;
    state->uid = (uint32_t)status->st_uid;
    state->gid = (uint32_t)status->st_gid;
    state->mtime_seconds = (int64_t)status->st_mtim.tv_sec;
    state->mtime_nanoseconds = (int64_t)status->st_mtim.tv_nsec;
    state->ctime_seconds = (int64_t)status->st_ctim.tv_sec;
    state->ctime_nanoseconds = (int64_t)status->st_ctim.tv_nsec;
    return 1;
}

static int file_states_equal(const FinduasFileState *left, const FinduasFileState *right) {
    return left != NULL && right != NULL &&
           left->inode == right->inode &&
           left->size == right->size &&
           left->nlink == right->nlink &&
           left->dev_major == right->dev_major &&
           left->dev_minor == right->dev_minor &&
           left->mode == right->mode &&
           left->uid == right->uid &&
           left->gid == right->gid &&
           left->mtime_seconds == right->mtime_seconds &&
           left->mtime_nanoseconds == right->mtime_nanoseconds &&
           left->ctime_seconds == right->ctime_seconds &&
           left->ctime_nanoseconds == right->ctime_nanoseconds;
}

static int pread_exact(int fd, void *output, size_t size, uint64_t offset) {
    uint8_t *cursor = (uint8_t *)output;
    size_t remaining = size;
    while (remaining != 0u) {
        if (offset > INT64_MAX || (uint64_t)(size - remaining) > INT64_MAX - offset) {
            errno = EOVERFLOW;
            return 0;
        }
        const off64_t position = (off64_t)(offset + (uint64_t)(size - remaining));
        const ssize_t result = pread64(fd, cursor, remaining, position);
        if (result < 0 && errno == EINTR) {
            continue;
        }
        if (result <= 0 || (size_t)result > remaining) {
            if (result == 0) {
                errno = EIO;
            }
            return 0;
        }
        cursor += (size_t)result;
        remaining -= (size_t)result;
    }
    return 1;
}

static enum FinduasIdentityError read_maps_snapshot(
    const FinduasModuleProfile *profile,
    uintptr_t load_bias,
    const FinduasFileState *state,
    FinduasMapsSnapshot *snapshot,
    int32_t *saved_errno) {
    FinduasMapsParser parser;
    finduas_maps_parser_init(
        &parser,
        profile,
        load_bias,
        state->dev_major,
        state->dev_minor,
        state->inode,
        snapshot);
    if (parser.error != FINDUAS_IDENTITY_OK) {
        return parser.error;
    }

    const int maps_fd = openat(AT_FDCWD, "/proc/self/maps", O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (maps_fd < 0) {
        *saved_errno = errno;
        return FINDUAS_IDENTITY_MAPS_OPEN_FAILED;
    }
    enum FinduasIdentityError error = FINDUAS_IDENTITY_OK;
    for (;;) {
        const ssize_t count = read(maps_fd, g_identity_workspace.file_buffer, FINDUAS_MAPS_READ_SIZE);
        if (count < 0 && errno == EINTR) {
            continue;
        }
        if (count < 0) {
            *saved_errno = errno;
            error = FINDUAS_IDENTITY_MAPS_PARSE_OR_LIMIT;
            break;
        }
        if (count == 0) {
            error = finduas_maps_parser_finish(&parser);
            break;
        }
        if (!finduas_maps_parser_feed(
                &parser,
                g_identity_workspace.file_buffer,
                (size_t)count)) {
            error = parser.error;
            break;
        }
    }
    if (close(maps_fd) != 0) {
        *saved_errno = errno;
        error = FINDUAS_IDENTITY_CLOSE_FAILED;
    }
    memset(&parser, 0, sizeof(parser));
    return error;
}

static int runtime_headers_match(
    const FinduasLoadedModule *module,
    const FinduasModuleProfile *profile,
    const FinduasMapsSnapshot *snapshot,
    int fd) {
    uint8_t file_header[FINDUAS_ELF_HEADER_SIZE];
    Elf64_Phdr file_phdrs[FINDUAS_PROFILE_PHDR_COUNT];
    memset(file_header, 0, sizeof(file_header));
    memset(file_phdrs, 0, sizeof(file_phdrs));
    if (!pread_exact(fd, file_header, sizeof(file_header), 0u) ||
        !pread_exact(
            fd,
            file_phdrs,
            sizeof(file_phdrs),
            sizeof(Elf64_Ehdr)) ||
        !finduas_identity_header_phdr_match(
            profile,
            file_header,
            file_phdrs,
            FINDUAS_PROFILE_PHDR_COUNT)) {
        return 0;
    }
    uintptr_t expected_phdr = 0u;
    if (module->base > UINTPTR_MAX - sizeof(Elf64_Ehdr)) {
        return 0;
    }
    expected_phdr = module->base + sizeof(Elf64_Ehdr);
    if (module->runtime_phdr != (const void *)expected_phdr ||
        module->runtime_phnum != FINDUAS_PROFILE_PHDR_COUNT ||
        !finduas_snapshot_contains_readable_range(
            snapshot,
            expected_phdr,
            sizeof(file_phdrs)) ||
        memcmp(module->runtime_phdr, profile->phdrs, sizeof(file_phdrs)) != 0) {
        return 0;
    }
    memset(file_header, 0, sizeof(file_header));
    memset(file_phdrs, 0, sizeof(file_phdrs));
    return 1;
}

static enum FinduasIdentityError hash_and_compare_file(
    int fd,
    const FinduasLoadedModule *module,
    const FinduasModuleProfile *profile,
    const FinduasMapsSnapshot *snapshot,
    FinduasIdentityDiagnostic *diagnostic) {
    FinduasSha256Context sha;
    uint8_t digest[FINDUAS_SHA256_DIGEST_SIZE];
    finduas_sha256_init(&sha);
    memset(digest, 0, sizeof(digest));
    uint64_t offset = 0u;
    while (offset < profile->exact_file_size) {
        const uint64_t remaining = profile->exact_file_size - offset;
        const size_t chunk_size =
            remaining < FINDUAS_FILE_BUFFER_SIZE ? (size_t)remaining : FINDUAS_FILE_BUFFER_SIZE;
        if (!pread_exact(fd, g_identity_workspace.file_buffer, chunk_size, offset)) {
            memset(&sha, 0, sizeof(sha));
            memset(g_identity_workspace.file_buffer, 0, sizeof(g_identity_workspace.file_buffer));
            return FINDUAS_IDENTITY_FILE_READ_FAILED;
        }
        if (!finduas_identity_compare_nonwritable_chunk(
                module->base,
                profile,
                snapshot,
                offset,
                g_identity_workspace.file_buffer,
                chunk_size)) {
            memset(&sha, 0, sizeof(sha));
            memset(g_identity_workspace.file_buffer, 0, sizeof(g_identity_workspace.file_buffer));
            return FINDUAS_IDENTITY_NONWRITABLE_LOAD_MISMATCH;
        }
        if (!finduas_sha256_update(&sha, g_identity_workspace.file_buffer, chunk_size)) {
            memset(&sha, 0, sizeof(sha));
            memset(g_identity_workspace.file_buffer, 0, sizeof(g_identity_workspace.file_buffer));
            return FINDUAS_IDENTITY_FILE_READ_FAILED;
        }
        offset += chunk_size;
        diagnostic->hashed_bytes += chunk_size;
    }

    ssize_t eof_result = 0;
    do {
        eof_result = pread64(
            fd,
            g_identity_workspace.file_buffer,
            1u,
            (off64_t)profile->exact_file_size);
    } while (eof_result < 0 && errno == EINTR);
    if (eof_result != 0) {
        memset(&sha, 0, sizeof(sha));
        memset(g_identity_workspace.file_buffer, 0, sizeof(g_identity_workspace.file_buffer));
        return FINDUAS_IDENTITY_FILE_READ_FAILED;
    }
    if (!finduas_sha256_finish(&sha, digest)) {
        memset(g_identity_workspace.file_buffer, 0, sizeof(g_identity_workspace.file_buffer));
        return FINDUAS_IDENTITY_FILE_READ_FAILED;
    }
    const int digest_match = finduas_constant_time_equal(
        digest,
        profile->whole_file_sha256,
        sizeof(digest));
    memset(digest, 0, sizeof(digest));
    memset(g_identity_workspace.file_buffer, 0, sizeof(g_identity_workspace.file_buffer));
    return digest_match ? FINDUAS_IDENTITY_OK : FINDUAS_IDENTITY_WHOLE_SHA256_MISMATCH;
}

enum FinduasIdentityError finduas_runtime_identity_verify(
    const FinduasModuleSet *modules,
    FinduasIdentityDiagnostic *diagnostic) {
    if (diagnostic == NULL) {
        return FINDUAS_IDENTITY_SOURCE_KIND_MISMATCH;
    }
    memset(diagnostic, 0, sizeof(*diagnostic));
    memset(&g_identity_workspace, 0, sizeof(g_identity_workspace));
    if (modules == NULL || modules->validated_module_count != FINDUAS_MODULE_COUNT ||
        modules->opened_handle_count != FINDUAS_MODULE_COUNT ||
        getpagesize() != (int)FINDUAS_RUNTIME_PAGE_SIZE) {
        set_error(diagnostic, FINDUAS_IDENTITY_SOURCE_KIND_MISMATCH, 0u, 1u);
        return diagnostic->error;
    }

    FinduasFileState states[FINDUAS_MODULE_COUNT];
    memset(states, 0, sizeof(states));
    for (uint32_t index = 0u; index < FINDUAS_MODULE_COUNT; ++index) {
        const FinduasLoadedModule *module = &modules->modules[index];
        const FinduasModuleProfile *profile = &kFinduasModuleProfiles[index];
        diagnostic->module_id = index;
        if (!finduas_identity_profile_is_well_formed(profile) ||
            profile->source_kind != FINDUAS_SOURCE_EXTRACTED_ELF_V1) {
            set_error(diagnostic, FINDUAS_IDENTITY_SOURCE_KIND_MISMATCH, index, 2u);
            goto cleanup;
        }
        if (!finduas_identity_source_path_is_exact_extracted(
                module->path,
                module->path_length)) {
            const enum FinduasIdentityError error =
                module->path_length != 0u && module->path[0] != '/'
                    ? FINDUAS_IDENTITY_PATH_NOT_ABSOLUTE
                    : (path_contains(module->path, module->path_length, "!/")
                           ? FINDUAS_IDENTITY_ZIP_UNSUPPORTED_CURRENT_PROFILE
                           : FINDUAS_IDENTITY_PATH_EMPTY_OR_TRUNCATED);
            set_error(diagnostic, error, index, 3u);
            goto cleanup;
        }

        errno = 0;
        const int fd = openat(
            AT_FDCWD,
            module->path,
            O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
        if (fd < 0) {
            set_error(diagnostic, FINDUAS_IDENTITY_OPEN_FAILED, index, 4u);
            goto cleanup;
        }
        ++diagnostic->opened_fd_count;
        enum FinduasIdentityError module_error = FINDUAS_IDENTITY_OK;
        uint32_t stage = 5u;
        struct stat pre_status;
        struct stat post_status;
        FinduasFileState post_state;
        memset(&pre_status, 0, sizeof(pre_status));
        memset(&post_status, 0, sizeof(post_status));
        memset(&post_state, 0, sizeof(post_state));
        if (fstat(fd, &pre_status) != 0 || !capture_file_state(&pre_status, &states[index]) ||
            !S_ISREG(pre_status.st_mode)) {
            module_error = FINDUAS_IDENTITY_NOT_REGULAR;
        } else if (states[index].size != profile->exact_file_size) {
            module_error = FINDUAS_IDENTITY_SIZE_MISMATCH;
        } else {
            int32_t maps_errno = 0;
            stage = 6u;
            module_error = read_maps_snapshot(
                profile,
                module->base,
                &states[index],
                &g_identity_workspace.first[index],
                &maps_errno);
            if (maps_errno != 0) {
                errno = maps_errno;
            }
        }
        if (module_error == FINDUAS_IDENTITY_OK) {
            stage = 7u;
            if (!runtime_headers_match(
                    module,
                    profile,
                    &g_identity_workspace.first[index],
                    fd)) {
                module_error = FINDUAS_IDENTITY_PHDR_MISMATCH;
            }
        }
        if (module_error == FINDUAS_IDENTITY_OK) {
            stage = 8u;
            module_error = hash_and_compare_file(
                fd,
                module,
                profile,
                &g_identity_workspace.first[index],
                diagnostic);
        }
        if (module_error == FINDUAS_IDENTITY_OK) {
            stage = 9u;
            if (fstat(fd, &post_status) != 0 ||
                !capture_file_state(&post_status, &post_state) ||
                !file_states_equal(&states[index], &post_state)) {
                module_error = FINDUAS_IDENTITY_STAT_CHANGED;
            }
        }
        if (close(fd) != 0) {
            module_error = FINDUAS_IDENTITY_CLOSE_FAILED;
            stage = 10u;
        } else {
            ++diagnostic->closed_fd_count;
        }
        if (module_error != FINDUAS_IDENTITY_OK) {
            set_error(diagnostic, module_error, index, stage);
            goto cleanup;
        }
        diagnostic->relevant_vma_count +=
            (uint32_t)g_identity_workspace.first[index].count;
        ++diagnostic->verified_module_count;
    }

    for (uint32_t index = 0u; index < FINDUAS_MODULE_COUNT; ++index) {
        int32_t maps_errno = 0;
        const enum FinduasIdentityError error = read_maps_snapshot(
            &kFinduasModuleProfiles[index],
            modules->modules[index].base,
            &states[index],
            &g_identity_workspace.second[index],
            &maps_errno);
        if (error != FINDUAS_IDENTITY_OK ||
            !finduas_maps_snapshots_equal(
                &g_identity_workspace.first[index],
                &g_identity_workspace.second[index])) {
            if (maps_errno != 0) {
                errno = maps_errno;
            }
            set_error(
                diagnostic,
                error != FINDUAS_IDENTITY_OK ? error : FINDUAS_IDENTITY_MAP_CARDINALITY,
                index,
                11u);
            goto cleanup;
        }
    }
    if (finduas_modules_recheck(modules) != FINDUAS_MODULE_ERROR_NONE) {
        set_error(diagnostic, FINDUAS_IDENTITY_LINKER_EPOCH_CHANGED, 0u, 12u);
        goto cleanup;
    }
    if (diagnostic->opened_fd_count != diagnostic->closed_fd_count ||
        diagnostic->opened_fd_count != FINDUAS_MODULE_COUNT) {
        set_error(diagnostic, FINDUAS_IDENTITY_CLOSE_FAILED, 0u, 13u);
        goto cleanup;
    }
    diagnostic->error = FINDUAS_IDENTITY_OK;

cleanup:
    memset(states, 0, sizeof(states));
    memset(&g_identity_workspace, 0, sizeof(g_identity_workspace));
    return diagnostic->error;
}
