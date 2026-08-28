#ifndef FINDUAS_EID_ROUTE_V23_FILE_STATE_H
#define FINDUAS_EID_ROUTE_V23_FILE_STATE_H

#include <stdint.h>
#include <sys/stat.h>

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

/* Pure metadata gate shared by production and the zero-device host fixture. */
int finduas_capture_file_state(
    const struct stat *status,
    FinduasFileState *state);

int finduas_file_states_equal(
    const FinduasFileState *left,
    const FinduasFileState *right);

#endif
