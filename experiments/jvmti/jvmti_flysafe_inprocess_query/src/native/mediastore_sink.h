#ifndef FINDUAS_MEDIASTORE_SINK_H
#define FINDUAS_MEDIASTORE_SINK_H

#include <jni.h>
#include <stddef.h>

#define MEDIASTORE_SINK_MAX_BYTES 32768u

enum mediastore_sink_code {
    MEDIASTORE_SINK_SAVED = 0,
    MEDIASTORE_SINK_INVALID_ARGUMENT = 1,
    MEDIASTORE_SINK_TOO_LARGE = 2,
    MEDIASTORE_SINK_ENTRY_EXCEPTION = 3,
    MEDIASTORE_SINK_API_UNAVAILABLE = 4,
    MEDIASTORE_SINK_VOLUME_DISCOVERY_FAILED = 5,
    MEDIASTORE_SINK_NO_VOLUME = 6,
    MEDIASTORE_SINK_MULTIPLE_VOLUMES = 7,
    MEDIASTORE_SINK_VOLUME_UNAVAILABLE = 8,
    MEDIASTORE_SINK_PREPARE_FAILED = 9,
    MEDIASTORE_SINK_INSERT_FAILED = 10,
    MEDIASTORE_SINK_URI_INVALID = 11,
    MEDIASTORE_SINK_OPEN_FAILED = 12,
    MEDIASTORE_SINK_WRITE_FAILED = 13,
    MEDIASTORE_SINK_FLUSH_FAILED = 14,
    MEDIASTORE_SINK_CLOSE_FAILED = 15,
    MEDIASTORE_SINK_PUBLISH_FAILED = 16
};

enum mediastore_sink_cleanup {
    MEDIASTORE_SINK_CLEANUP_NOT_NEEDED = 0,
    MEDIASTORE_SINK_CLEANUP_REMOVED = 1,
    MEDIASTORE_SINK_CLEANUP_FAILED = 2,
    MEDIASTORE_SINK_CLEANUP_UNVERIFIED_URI = 3
};

struct mediastore_sink_result {
    int code;
    int cleanup_status;
    int insert_count;
    int write_count;
    int close_count;
    int publish_count;
    int delete_count;
    int close_failed;
    size_t saved_bytes;
};

/* Android30 standard storage APIs only. Caller supplies Application context and
 * a complete UTF-8 JSON document, at most32768 bytes. SID is exactly16 lowercase
 * hex characters. No text/URI/volume/exception is logged or returned.
 * Creates only FindUAS_A057_policy_<SID>.json in Download/FindUAS/Probe/ on the
 * unique mounted removable, nonprimary, nonemulated volume. Caller ensures SID
 * uniqueness; this helper never queries/replaces older reports. An unexpected
 * insert URI is not opened or deleted. Entry exceptions are left untouched;
 * exceptions raised by this helper are consumed and represented by codes.
 */
int mediastore_sink_write(JNIEnv *jni, jobject application_context,
                          const char *sid, const unsigned char *json_utf8,
                          size_t bytes, struct mediastore_sink_result *out);

#endif
