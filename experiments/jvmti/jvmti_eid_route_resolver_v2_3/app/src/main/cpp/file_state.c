#include "file_state.h"

#include <string.h>
#if defined(__APPLE__)
#include <sys/types.h>
#else
#include <sys/sysmacros.h>
#endif

int finduas_capture_file_state(
    const struct stat *status,
    FinduasFileState *state) {
    if (status == NULL || state == NULL || status->st_dev == 0 ||
        status->st_ino == 0 || status->st_size < 0 || status->st_nlink <= 0) {
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
#if defined(__APPLE__)
    state->mtime_seconds = (int64_t)status->st_mtimespec.tv_sec;
    state->mtime_nanoseconds = (int64_t)status->st_mtimespec.tv_nsec;
    state->ctime_seconds = (int64_t)status->st_ctimespec.tv_sec;
    state->ctime_nanoseconds = (int64_t)status->st_ctimespec.tv_nsec;
#else
    state->mtime_seconds = (int64_t)status->st_mtim.tv_sec;
    state->mtime_nanoseconds = (int64_t)status->st_mtim.tv_nsec;
    state->ctime_seconds = (int64_t)status->st_ctim.tv_sec;
    state->ctime_nanoseconds = (int64_t)status->st_ctim.tv_nsec;
#endif
    return 1;
}

int finduas_file_states_equal(
    const FinduasFileState *left,
    const FinduasFileState *right) {
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
