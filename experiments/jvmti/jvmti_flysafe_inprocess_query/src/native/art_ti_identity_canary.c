#include <android/log.h>
#include <errno.h>
#include <fcntl.h>
#include <jni.h>
#include <jvmti.h>
#include <stdatomic.h>
#include <stddef.h>
#include <string.h>
#include <unistd.h>

#define IDENTITY_TAG "FindUAS-ARTTI-Identity"
#define IDENTITY_SCHEMA "finduas-artti-identity/v1"
#define ART_TI_VERSION ((jint)0x70010200)
#define CONTEXT_LIMIT 255u
#define STAT_LIMIT 2048u
#define READ_CALL_LIMIT 32u

enum read_status {
    READ_OK = 0,
    READ_OPEN_FAILED = 1,
    READ_FAILED = 2,
    READ_TRUNCATED = 3,
    READ_EMPTY = 4,
    READ_INVALID = 5,
    READ_CLOSE_FAILED = 6,
    READ_LIMIT_REACHED = 7
};

struct read_result {
    int status;
    int error_number;
    size_t length;
};

static atomic_flag identity_entered = ATOMIC_FLAG_INIT;

static int valid_sid(const char *options, char sid[17]) {
    if (options == NULL) return 0;
    for (size_t i = 0; i < 16; ++i) {
        unsigned char value = (unsigned char)options[i];
        if (!((value >= '0' && value <= '9') || (value >= 'a' && value <= 'f'))) return 0;
        sid[i] = (char)value;
    }
    if (options[16] != '\0') return 0;
    sid[16] = '\0';
    return 1;
}

/* At most limit+1 input bytes and a fixed number of read calls. No partial value
 * is exposed on error; each successfully opened descriptor is closed once. */
static struct read_result read_self_file(const char *path, char *buffer, size_t limit) {
    struct read_result result = {READ_OK, 0, 0};
    buffer[0] = '\0';
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        result.status = READ_OPEN_FAILED;
        result.error_number = errno;
        return result;
    }
    int complete = 0;
    for (unsigned int call = 0; call < READ_CALL_LIMIT; ++call) {
        char extra;
        int probing = result.length == limit;
        ssize_t count = read(fd, probing ? &extra : buffer + result.length,
                             probing ? 1u : limit - result.length);
        if (count < 0) {
            if (errno == EINTR) continue;
            result.status = READ_FAILED;
            result.error_number = errno;
            complete = 1;
            break;
        }
        if (count == 0) {
            complete = 1;
            break;
        }
        if (probing) {
            result.status = READ_TRUNCATED;
            complete = 1;
            break;
        }
        result.length += (size_t)count;
    }
    if (!complete) result.status = READ_LIMIT_REACHED;
    if (close(fd) != 0 && result.status == READ_OK) {
        result.status = READ_CLOSE_FAILED;
        result.error_number = errno;
    }
    if (result.status == READ_OK && result.length == 0) result.status = READ_EMPTY;
    if (result.status != READ_OK) result.length = 0;
    buffer[result.length] = '\0';
    return result;
}

static int normalize_context(char *context, size_t length) {
    /* proc security attributes may include their terminating NUL. */
    if (length != 0 && context[length - 1] == '\0') --length;
    if (length != 0 && context[length - 1] == '\n') --length;
    if (length == 0) return 0;
    for (size_t i = 0; i < length; ++i) {
        unsigned char c = (unsigned char)context[i];
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '_' || c == ':' || c == ',' ||
              c == '.' || c == '-')) return 0;
    }
    context[length] = '\0';
    return 1;
}

static int stat_starttime(const char *stat, size_t length, char token[21]) {
    if (length == 0 || memchr(stat, '\0', length) != NULL) return 0;
    size_t prefix = 0;
    while (prefix < length && stat[prefix] >= '0' && stat[prefix] <= '9') ++prefix;
    if (prefix == 0 || prefix > 20 || prefix + 2 >= length ||
        stat[0] == '0' || stat[prefix] != ' ' || stat[prefix + 1] != '(') return 0;
    size_t closing = length;
    while (closing > prefix + 1 && stat[closing - 1] != ')') --closing;
    if (closing <= prefix + 1 || closing >= length || stat[closing] != ' ') return 0;
    size_t cursor = closing;
    for (unsigned int field = 3; field <= 22; ++field) {
        while (cursor < length && stat[cursor] == ' ') ++cursor;
        size_t start = cursor;
        while (cursor < length && stat[cursor] != ' ' && stat[cursor] != '\n') ++cursor;
        size_t size = cursor - start;
        if (size == 0) return 0;
        if (field == 22) {
            if (size > 20) return 0;
            for (size_t i = start; i < cursor; ++i) {
                if (stat[i] < '0' || stat[i] > '9') return 0;
            }
            if (size == 20 && memcmp(stat + start, "18446744073709551615", 20) > 0) return 0;
            memcpy(token, stat + start, size);
            token[size] = '\0';
            return 1;
        }
    }
    return 0;
}

JNIEXPORT jint JNICALL Agent_OnAttach(JavaVM *vm, char *options, void *reserved) {
    (void)reserved;
    char sid[17];
    pid_t pid = getpid();
    if (!valid_sid(options, sid)) {
        __android_log_print(ANDROID_LOG_INFO, IDENTITY_TAG,
            "schema=" IDENTITY_SCHEMA " phase=reject sid=INVALID pid=%ld ready=0 reason=OPTIONS",
            (long)pid);
        return JNI_ERR;
    }
    if (vm == NULL || *vm == NULL || (*vm)->GetEnv == NULL) {
        __android_log_print(ANDROID_LOG_INFO, IDENTITY_TAG,
            "schema=" IDENTITY_SCHEMA " phase=reject sid=%s pid=%ld ready=0 reason=VM",
            sid, (long)pid);
        return JNI_ERR;
    }
    if (atomic_flag_test_and_set_explicit(&identity_entered, memory_order_acq_rel)) {
        __android_log_print(ANDROID_LOG_INFO, IDENTITY_TAG,
            "schema=" IDENTITY_SCHEMA " phase=duplicate sid=%s pid=%ld ready=0",
            sid, (long)pid);
        return JNI_OK;
    }

    uid_t uid = getuid();
    gid_t gid = getgid();
    __android_log_print(ANDROID_LOG_INFO, IDENTITY_TAG,
        "schema=" IDENTITY_SCHEMA " phase=enter sid=%s pid=%ld uid=%lu gid=%lu abi_bits=%u",
        sid, (long)pid, (unsigned long)uid, (unsigned long)gid, (unsigned int)(sizeof(void *) * 8));

    char context[CONTEXT_LIMIT + 1];
    char stat[STAT_LIMIT + 1];
    char starttime[21] = "UNAVAILABLE";
    struct read_result context_read = read_self_file("/proc/self/attr/current", context, CONTEXT_LIMIT);
    if (context_read.status == READ_OK && !normalize_context(context, context_read.length)) {
        context_read.status = READ_INVALID;
    }
    struct read_result stat_read = read_self_file("/proc/self/stat", stat, STAT_LIMIT);
    if (stat_read.status == READ_OK && !stat_starttime(stat, stat_read.length, starttime)) {
        stat_read.status = READ_INVALID;
    }
    int identity_ok = pid > 0 && context_read.status == READ_OK && stat_read.status == READ_OK;

    jvmtiEnv *art_ti = NULL;
    jint interface_version = 0;
    jint env_rc = (*vm)->GetEnv(vm, (void **)&art_ti, ART_TI_VERSION);
    jvmtiError version_rc = (jvmtiError)-1;
    jvmtiError dispose_rc = (jvmtiError)-1;
    int version_called = 0;
    int dispose_attempted = 0;
    if (env_rc == JNI_OK && art_ti != NULL && *art_ti != NULL) {
        if ((*art_ti)->GetVersionNumber != NULL) {
            version_called = 1;
            version_rc = (*art_ti)->GetVersionNumber(art_ti, &interface_version);
        }
        /* Exact Android 11 ART TI GetEnv allocates a new environment for this call.
         * Dispose it once even if version reading failed; do not touch it afterwards. */
        if ((*art_ti)->DisposeEnvironment != NULL) {
            dispose_attempted = 1;
            dispose_rc = (*art_ti)->DisposeEnvironment(art_ti);
        }
    }
    art_ti = NULL;
    int art_ti_ok = env_rc == JNI_OK && version_called && version_rc == JVMTI_ERROR_NONE;
    int dispose_ok = dispose_attempted && dispose_rc == JVMTI_ERROR_NONE;
    int ready = identity_ok && art_ti_ok && dispose_ok;
    __android_log_print(ANDROID_LOG_INFO, IDENTITY_TAG,
        "schema=" IDENTITY_SCHEMA " phase=result sid=%s pid=%ld uid=%lu gid=%lu abi_bits=%u"
        " ready=%d identity_ok=%d artti_ok=%d dispose_ok=%d"
        " context_rc=%d context_errno=%d context=%s stat_rc=%d stat_errno=%d starttime=%s"
        " env_rc=%d version_called=%d version_rc=%d interface_version=0x%08x"
        " dispose_attempted=%d dispose_rc=%d",
        sid, (long)pid, (unsigned long)uid, (unsigned long)gid, (unsigned int)(sizeof(void *) * 8),
        ready, identity_ok, art_ti_ok, dispose_ok,
        context_read.status, context_read.error_number,
        context_read.status == READ_OK ? context : "UNAVAILABLE",
        stat_read.status, stat_read.error_number,
        stat_read.status == READ_OK ? starttime : "UNAVAILABLE",
        (int)env_rc, version_called, (int)version_rc, (unsigned int)interface_version,
        dispose_attempted, (int)dispose_rc);
    /* Keep the DSO loaded after any valid entry. JNI_ERR may cause ActivityThread to
     * unload and retry, resetting this DSO's once flag. The log's ready is the result. */
    return JNI_OK;
}
