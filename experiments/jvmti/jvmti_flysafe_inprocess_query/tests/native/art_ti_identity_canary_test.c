#include <android/log.h>
#include <errno.h>
#include <fcntl.h>
#include <jni.h>
#include <jvmti.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

JNIEXPORT jint JNICALL Agent_OnAttach(JavaVM *vm, char *options, void *reserved);

static const char *test_name;
#define CHECK(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "FAIL %s:%d: %s\n", test_name, __LINE__, #condition); \
        exit(EXIT_FAILURE); \
    } \
} while (0)

static char sid[] = "0123456789abcdef";
static char logs[32][1024];
static int log_count;
static int env_calls, version_calls, dispose_calls;
static jint env_result;
static int nonnull_env;
static jvmtiError version_result, dispose_result;
static int disposed;
static int missing_version, missing_dispose, null_env_table;

struct input_file {
    unsigned char bytes[4096];
    size_t size, offset, chunk;
    int open_error, read_error_call, close_error, interrupts;
    int opens, reads, closes;
};
static struct input_file context_file, stat_file;

static jint JNICALL fake_get_env(JavaVM *vm, void **environment, jint version);
static jvmtiError JNICALL fake_get_version(jvmtiEnv *env, jint *version);
static jvmtiError JNICALL fake_dispose(jvmtiEnv *env);
static jvmtiError JNICALL reject_classes(jvmtiEnv *env, jint *count, jclass **classes);
static const struct JNIInvokeInterface_ vm_functions = {.GetEnv = fake_get_env};
static JavaVM fake_vm = &vm_functions;
static struct jvmtiInterface_1_ art_functions;
static jvmtiEnv fake_env;

pid_t finduas_test_getpid(void) { return (pid_t)4242; }
uid_t finduas_test_getuid(void) { return (uid_t)10000; }
gid_t finduas_test_getgid(void) { return (gid_t)10000; }

int finduas_test_open(const char *path, int flags, ...) {
    CHECK(flags == (O_RDONLY | O_CLOEXEC));
    struct input_file *file = NULL;
    int fd = 0;
    if (strcmp(path, "/proc/self/attr/current") == 0) {
        file = &context_file; fd = 101;
    } else if (strcmp(path, "/proc/self/stat") == 0) {
        file = &stat_file; fd = 102;
    }
    CHECK(file != NULL);
    CHECK(++file->opens == 1);
    if (file->open_error) { errno = EACCES; return -1; }
    return fd;
}

static struct input_file *file_for(int fd) {
    CHECK(fd == 101 || fd == 102);
    return fd == 101 ? &context_file : &stat_file;
}

ssize_t finduas_test_read(int fd, void *buffer, size_t count) {
    struct input_file *file = file_for(fd);
    CHECK(file->closes == 0);
    CHECK(count > 0 && count <= (fd == 101 ? 255u : 2048u));
    CHECK(++file->reads <= 32);
    if (file->interrupts > 0) { --file->interrupts; errno = EINTR; return -1; }
    if (file->reads == file->read_error_call) { errno = EIO; return -1; }
    size_t copied = file->size - file->offset;
    if (copied > count) copied = count;
    if (file->chunk != 0 && copied > file->chunk) copied = file->chunk;
    memcpy(buffer, file->bytes + file->offset, copied);
    file->offset += copied;
    CHECK(file->offset <= (fd == 101 ? 256u : 2049u));
    return (ssize_t)copied;
}

int finduas_test_close(int fd) {
    struct input_file *file = file_for(fd);
    CHECK(++file->closes == 1);
    if (file->close_error) { errno = EIO; return -1; }
    return 0;
}

static jint JNICALL fake_get_env(JavaVM *vm, void **environment, jint version) {
    CHECK(vm == &fake_vm);
    CHECK(environment != NULL && version == (jint)0x70010200);
    CHECK(++env_calls == 1 && !disposed);
    art_functions.GetVersionNumber = missing_version ? NULL : fake_get_version;
    art_functions.DisposeEnvironment = missing_dispose ? NULL : fake_dispose;
    art_functions.GetLoadedClasses = reject_classes;
    fake_env = null_env_table ? NULL : &art_functions;
    *environment = nonnull_env ? &fake_env : NULL;
    return env_result;
}

static jvmtiError JNICALL fake_get_version(jvmtiEnv *env, jint *version) {
    CHECK(env == &fake_env && version != NULL);
    CHECK(env_result == JNI_OK && nonnull_env && !disposed);
    CHECK(++version_calls == 1);
    if (version_result == JVMTI_ERROR_NONE) *version = (jint)0x30010200;
    return version_result;
}

static jvmtiError JNICALL fake_dispose(jvmtiEnv *env) {
    CHECK(env == &fake_env && env_result == JNI_OK && nonnull_env && !disposed);
    CHECK(++dispose_calls == 1);
    disposed = 1;
    /* Any later indirect access through this environment fails immediately. */
    fake_env = NULL;
    return dispose_result;
}

static jvmtiError JNICALL reject_classes(jvmtiEnv *env, jint *count, jclass **classes) {
    (void)env; (void)count; (void)classes;
    CHECK(!"identity canary must not enumerate classes");
    return JVMTI_ERROR_INTERNAL;
}

int __android_log_print(int priority, const char *tag, const char *format, ...) {
    CHECK(priority == ANDROID_LOG_INFO && strcmp(tag, "FindUAS-ARTTI-Identity") == 0);
    CHECK(log_count < 32);
    va_list args;
    va_start(args, format);
    int length = vsnprintf(logs[log_count], sizeof(logs[0]), format, args);
    va_end(args);
    CHECK(length > 0 && (size_t)length < sizeof(logs[0]));
    CHECK(strchr(logs[log_count], '\n') == NULL && strchr(logs[log_count], '\r') == NULL);
    CHECK(strncmp(logs[log_count], "schema=finduas-artti-identity/v1 ", 32) == 0);
    ++log_count;
    return length;
}

static int field(const char *line, const char *key, const char *value) {
    char expected[320];
    int size = snprintf(expected, sizeof(expected), " %s=%s", key, value);
    CHECK(size > 0 && (size_t)size < sizeof(expected));
    const char *found = strstr(line, expected);
    return found != NULL && (found[size] == '\0' || found[size] == ' ');
}

static void expect_number(const char *line, const char *key, int value) {
    char expected[32];
    CHECK(snprintf(expected, sizeof(expected), "%d", value) > 0);
    CHECK(field(line, key, expected));
}

static void set_context(const void *bytes, size_t size) {
    CHECK(size <= sizeof(context_file.bytes));
    memcpy(context_file.bytes, bytes, size);
    context_file.size = size;
}

static void set_stat(const char *starttime) {
    char value[4096] = "4242 (TEST app (worker)) R";
    for (int f = 4; f < 22; ++f) strcat(value, " 0");
    strcat(value, " ");
    strcat(value, starttime);
    strcat(value, " 0 0\n");
    stat_file.size = strlen(value);
    memcpy(stat_file.bytes, value, stat_file.size);
}

static void defaults(void) {
    env_result = JNI_OK; nonnull_env = 1;
    version_result = dispose_result = JVMTI_ERROR_NONE;
    set_context("u:r:TEST_APP:s0\n", strlen("u:r:TEST_APP:s0\n"));
    set_stat("987654321");
}

static void expect_result(int identity_ok, int art_ok, int disposal_ok, int context_rc, int stat_rc) {
    CHECK(log_count == 2);
    CHECK(field(logs[0], "phase", "enter"));
    const char *result = logs[1];
    CHECK(field(result, "phase", "result"));
    for (int i = 0; i < 2; ++i) {
        CHECK(field(logs[i], "sid", sid));
        CHECK(field(logs[i], "pid", "4242"));
        CHECK(field(logs[i], "uid", "10000") && field(logs[i], "gid", "10000"));
        expect_number(logs[i], "abi_bits", (int)(sizeof(void *) * 8));
    }
    expect_number(result, "ready", identity_ok && art_ok && disposal_ok);
    expect_number(result, "identity_ok", identity_ok);
    expect_number(result, "artti_ok", art_ok);
    expect_number(result, "dispose_ok", disposal_ok);
    expect_number(result, "context_rc", context_rc);
    expect_number(result, "stat_rc", stat_rc);
    expect_number(result, "env_rc", env_result);
    expect_number(result, "version_called", version_calls);
    expect_number(result, "version_rc", version_calls ? (int)version_result : -1);
    expect_number(result, "dispose_attempted", dispose_calls);
    expect_number(result, "dispose_rc", dispose_calls ? (int)dispose_result : -1);
    CHECK(field(result, "interface_version", version_calls && version_result == JVMTI_ERROR_NONE ?
                "0x30010200" : "0x00000000"));
    if (context_rc != 0) CHECK(field(result, "context", "UNAVAILABLE"));
    if (stat_rc != 0) CHECK(field(result, "starttime", "UNAVAILABLE"));
    CHECK(env_calls == 1);
    CHECK(context_file.opens == 1 && stat_file.opens == 1);
    CHECK(context_file.closes == (context_file.open_error ? 0 : 1));
    CHECK(stat_file.closes == (stat_file.open_error ? 0 : 1));
}

static void attach(void) { CHECK(Agent_OnAttach(&fake_vm, sid, NULL) == JNI_OK); }

static void test_success(void) {
    attach(); expect_result(1, 1, 1, 0, 0);
    CHECK(field(logs[1], "context", "u:r:TEST_APP:s0"));
    CHECK(field(logs[1], "starttime", "987654321"));
    CHECK(version_calls == 1 && dispose_calls == 1);
}

static void test_options(void) {
    const char *bad[] = {NULL, "", "0123456789abcde", "0123456789abcdef0", "0123456789abcdeF",
        "run=0123456789abcdef", "0123456789abcdeg", "TEST\nINJECTED=1"};
    for (size_t i = 0; i < sizeof(bad) / sizeof(bad[0]); ++i) {
        CHECK(Agent_OnAttach(&fake_vm, (char *)bad[i], NULL) == JNI_ERR);
        CHECK(field(logs[log_count - 1], "phase", "reject"));
        CHECK(field(logs[log_count - 1], "sid", "INVALID"));
        CHECK(field(logs[log_count - 1], "reason", "OPTIONS"));
        CHECK(strstr(logs[log_count - 1], "INJECTED") == NULL);
    }
    CHECK(env_calls == 0 && context_file.opens == 0 && stat_file.opens == 0);
    log_count = 0;
    test_success(); /* Rejection did not consume the guard. */
}

static void test_vm_reject(void) {
    JavaVM empty_vm = NULL;
    const struct JNIInvokeInterface_ no_get_env = {0};
    JavaVM absent_call_vm = &no_get_env;
    CHECK(Agent_OnAttach(NULL, sid, NULL) == JNI_ERR);
    CHECK(Agent_OnAttach(&empty_vm, sid, NULL) == JNI_ERR);
    CHECK(Agent_OnAttach(&absent_call_vm, sid, NULL) == JNI_ERR);
    for (int i = 0; i < log_count; ++i) CHECK(field(logs[i], "reason", "VM"));
    CHECK(env_calls == 0 && context_file.opens == 0 && stat_file.opens == 0);
    log_count = 0; test_success();
}

static void test_env_error(void) {
    env_result = JNI_EVERSION;
    attach(); expect_result(1, 0, 0, 0, 0);
    CHECK(version_calls == 0 && dispose_calls == 0);
}
static void test_env_null(void) {
    nonnull_env = 0; attach(); expect_result(1, 0, 0, 0, 0);
    CHECK(version_calls == 0 && dispose_calls == 0);
}
static void test_env_table_null(void) {
    null_env_table = 1; attach(); expect_result(1, 0, 0, 0, 0);
}
static void test_version_error(void) {
    version_result = JVMTI_ERROR_WRONG_PHASE;
    attach(); expect_result(1, 0, 1, 0, 0);
    CHECK(dispose_calls == 1);
}
static void test_missing_version(void) {
    missing_version = 1; attach(); expect_result(1, 0, 1, 0, 0);
    CHECK(dispose_calls == 1);
}
static void test_dispose_error(void) {
    dispose_result = JVMTI_ERROR_INTERNAL;
    attach(); expect_result(1, 1, 0, 0, 0);
    CHECK(dispose_calls == 1);
}
static void test_missing_dispose(void) {
    missing_dispose = 1; attach(); expect_result(1, 1, 0, 0, 0);
}
static void duplicate(void) {
    int reads = context_file.reads + stat_file.reads;
    int calls = version_calls + dispose_calls;
    attach();
    CHECK(log_count == 3 && field(logs[2], "phase", "duplicate"));
    CHECK(field(logs[2], "ready", "0") && field(logs[2], "sid", sid));
    CHECK(field(logs[2], "pid", "4242"));
    CHECK(context_file.reads + stat_file.reads == reads);
    CHECK(env_calls == 1 && version_calls + dispose_calls == calls);
}
static void test_duplicate_success(void) { test_success(); duplicate(); }
static void test_duplicate_failure(void) { test_env_error(); duplicate(); }
static void test_context_nul(void) {
    const char value[] = "u:r:TEST_APP:s0";
    set_context(value, sizeof(value)); test_success();
}
static void test_context_exact_limit(void) {
    memset(context_file.bytes, 'a', 255); context_file.size = 255;
    attach(); expect_result(1, 1, 1, 0, 0);
    CHECK(context_file.offset == 255 && context_file.reads == 2);
}
static void test_context_truncated(void) {
    memset(context_file.bytes, 'a', 256); context_file.size = 256;
    attach(); expect_result(0, 1, 1, 3, 0);
    CHECK(context_file.offset == 256 && context_file.reads == 2);
}
static void test_context_injection(void) {
    set_context("u:r:TEST_APP:s0\nready=1", strlen("u:r:TEST_APP:s0\nready=1"));
    attach(); expect_result(0, 1, 1, 5, 0);
}
static void test_context_embedded_nul(void) {
    const char value[] = "u:r:TEST_APP:s0\0FORGED";
    set_context(value, sizeof(value) - 1); attach(); expect_result(0, 1, 1, 5, 0);
}
static void test_context_empty(void) {
    context_file.size = 0; attach(); expect_result(0, 1, 1, 4, 0);
}
static void test_context_open_error(void) {
    context_file.open_error = 1; attach(); expect_result(0, 1, 1, 1, 0);
    expect_number(logs[1], "context_errno", EACCES);
}
static void test_context_partial_error(void) {
    context_file.chunk = 4; context_file.read_error_call = 2;
    attach(); expect_result(0, 1, 1, 2, 0);
    expect_number(logs[1], "context_errno", EIO);
}
static void test_context_close_error(void) {
    context_file.close_error = 1; attach(); expect_result(0, 1, 1, 6, 0);
    expect_number(logs[1], "context_errno", EIO);
}
static void test_read_interrupted(void) {
    context_file.interrupts = 2; context_file.chunk = 2;
    attach(); expect_result(1, 1, 1, 0, 0);
}
static void test_read_budget(void) {
    context_file.interrupts = 40; attach(); expect_result(0, 1, 1, 7, 0);
    CHECK(context_file.reads == 32);
}
static void test_stat_error(void) {
    stat_file.read_error_call = 1; attach(); expect_result(0, 1, 1, 0, 2);
    expect_number(logs[1], "stat_errno", EIO);
}
static void test_stat_truncated(void) {
    memset(stat_file.bytes, '0', 2049); stat_file.size = 2049;
    attach(); expect_result(0, 1, 1, 0, 3);
    CHECK(stat_file.offset == 2049);
}
static void test_stat_nonnumeric(void) {
    set_stat("123a45"); attach(); expect_result(0, 1, 1, 0, 5);
}
static void test_stat_overflow(void) {
    set_stat("18446744073709551616"); attach(); expect_result(0, 1, 1, 0, 5);
}
static void test_stat_long(void) {
    set_stat("123456789012345678901"); attach(); expect_result(0, 1, 1, 0, 5);
}
static void test_stat_uint64_max(void) {
    set_stat("18446744073709551615"); attach(); expect_result(1, 1, 1, 0, 0);
    CHECK(field(logs[1], "starttime", "18446744073709551615"));
}
static void test_stat_short(void) {
    stat_file.size = 30; attach(); expect_result(0, 1, 1, 0, 5);
}
static void test_stat_nul(void) {
    stat_file.bytes[10] = '\0'; attach(); expect_result(0, 1, 1, 0, 5);
}
static void test_both_read_fail(void) {
    context_file.open_error = 1; stat_file.open_error = 1;
    attach(); expect_result(0, 1, 1, 1, 1);
    CHECK(version_calls == 1 && dispose_calls == 1);
}

struct test_case { const char *name; void (*run)(void); };
#define CASE(name) {#name, test_##name}
int main(void) {
    const struct test_case tests[] = {
        CASE(success), CASE(options), CASE(vm_reject), CASE(env_error), CASE(env_null),
        CASE(env_table_null), CASE(version_error), CASE(missing_version), CASE(dispose_error),
        CASE(missing_dispose), CASE(duplicate_success), CASE(duplicate_failure),
        CASE(context_nul), CASE(context_exact_limit), CASE(context_truncated),
        CASE(context_injection), CASE(context_embedded_nul), CASE(context_empty),
        CASE(context_open_error), CASE(context_partial_error), CASE(context_close_error),
        CASE(read_interrupted), CASE(read_budget), CASE(stat_error), CASE(stat_truncated),
        CASE(stat_nonnumeric), CASE(stat_overflow), CASE(stat_long), CASE(stat_uint64_max),
        CASE(stat_short), CASE(stat_nul), CASE(both_read_fail)
    };
    size_t passed = 0;
    for (size_t i = 0; i < sizeof(tests) / sizeof(tests[0]); ++i) {
        test_name = tests[i].name;
        pid_t child = fork();
        CHECK(child >= 0);
        if (child == 0) {
            defaults(); tests[i].run(); _exit(EXIT_SUCCESS);
        }
        int status;
        CHECK(waitpid(child, &status, 0) == child);
        CHECK(WIFEXITED(status) && WEXITSTATUS(status) == EXIT_SUCCESS);
        ++passed;
    }
    printf("ART TI identity canary host tests: %zu passed\n", passed);
    return EXIT_SUCCESS;
}
