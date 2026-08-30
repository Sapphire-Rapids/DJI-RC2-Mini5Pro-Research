#include <android/log.h>
#include <jni.h>
#include <jvmti.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

JNIEXPORT jint JNICALL Agent_OnAttach(JavaVM *vm, char *options, void *reserved);

static const char *test_name;
#define CHECK(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "FAIL %s:%d: %s\n", test_name, __LINE__, #condition); \
        exit(EXIT_FAILURE); \
    } \
} while (0)

static jint configured_env_result;
static int configured_nonnull_env;
static jvmtiError configured_version_result;
static jint configured_version;
static int env_calls;
static int version_calls;
static int log_calls;
static char captured_log[512];

static jint JNICALL fake_get_env(JavaVM *vm, void **environment, jint version);
static jvmtiError JNICALL fake_get_version(jvmtiEnv *env, jint *version);
static jvmtiError JNICALL reject_class_enumeration(
    jvmtiEnv *env, jint *class_count, jclass **classes);

/* All other table slots stay NULL: an unexpected VM/JVMTI call cannot pass silently. */
static const struct JNIInvokeInterface_ fake_vm_functions = {
    .GetEnv = fake_get_env,
};
static JavaVM fake_vm = &fake_vm_functions;
static const struct jvmtiInterface_1_ fake_art_functions = {
    .GetVersionNumber = fake_get_version,
    .GetLoadedClasses = reject_class_enumeration,
};
static jvmtiEnv fake_art_environment = &fake_art_functions;

static jint JNICALL fake_get_env(JavaVM *vm, void **environment, jint version) {
    CHECK(vm == &fake_vm);
    CHECK(environment != NULL);
    /* A JNI environment request, or the previously rejected standard JVMTI request, fails. */
    CHECK(version == (jint)0x70010200);
    CHECK(++env_calls == 1);
    *environment = configured_nonnull_env ? &fake_art_environment : NULL;
    return configured_env_result;
}

static jvmtiError JNICALL fake_get_version(jvmtiEnv *env, jint *version) {
    CHECK(env == &fake_art_environment);
    CHECK(configured_env_result == JNI_OK);
    CHECK(configured_nonnull_env);
    CHECK(version != NULL);
    CHECK(++version_calls == 1);
    if (configured_version_result == JVMTI_ERROR_NONE) *version = configured_version;
    return configured_version_result;
}

static jvmtiError JNICALL reject_class_enumeration(
    jvmtiEnv *env, jint *class_count, jclass **classes) {
    (void)env;
    (void)class_count;
    (void)classes;
    CHECK(!"class enumeration is forbidden in the pure canary");
    return JVMTI_ERROR_INTERNAL;
}

int __android_log_print(int priority, const char *tag, const char *format, ...) {
    CHECK(priority == ANDROID_LOG_INFO);
    CHECK(strcmp(tag, "FindUAS-ARTTI-Canary") == 0);
    CHECK(++log_calls == 1);
    va_list args;
    va_start(args, format);
    int length = vsnprintf(captured_log, sizeof(captured_log), format, args);
    va_end(args);
    CHECK(length >= 0 && (size_t)length < sizeof(captured_log));
    return length;
}

static void reset(const char *name) {
    test_name = name;
    configured_env_result = JNI_OK;
    configured_nonnull_env = 1;
    configured_version_result = JVMTI_ERROR_NONE;
    /* GetVersionNumber reports a version; it is not the GetEnv interface selector. */
    configured_version = (jint)0x30010200;
    env_calls = version_calls = log_calls = 0;
    captured_log[0] = '\0';
}

static void check_log(int expected_ready, int expected_version_calls) {
    int ready = -1, env_result = 0, version_result = 0, consumed = -1;
    unsigned int bits = 0, version = 0;
    long pid = 0;
    unsigned long uid = 0;
    CHECK(env_calls == 1);
    CHECK(version_calls == expected_version_calls);
    CHECK(log_calls == 1);
    CHECK(sscanf(captured_log,
        "ARTTI_CANARY ready=%d abi_bits=%u pid=%ld uid=%lu env=%d version_result=%d version=0x%x%n",
        &ready, &bits, &pid, &uid, &env_result, &version_result, &version, &consumed) == 7);
    CHECK(consumed >= 0 && captured_log[consumed] == '\0');
    CHECK(ready == expected_ready);
    CHECK(bits == sizeof(void *) * 8);
    CHECK(pid == (long)getpid());
    CHECK(uid == (unsigned long)getuid());
    CHECK(env_result == configured_env_result);
    CHECK(version_result == (int)(expected_version_calls ? configured_version_result : JVMTI_ERROR_INTERNAL));
    CHECK(version == (expected_ready ? (unsigned int)configured_version : 0));
}

static void check_no_work(void) {
    CHECK(env_calls == 0);
    CHECK(version_calls == 0);
    CHECK(log_calls == 0);
}

int main(void) {
    int passed = 0;

    reset("success with null options");
    CHECK(Agent_OnAttach(&fake_vm, NULL, NULL) == JNI_OK);
    check_log(1, 1);
    ++passed;

    reset("success with empty options and ignored reserved pointer");
    char empty_options[] = "";
    CHECK(Agent_OnAttach(&fake_vm, empty_options, &passed) == JNI_OK);
    check_log(1, 1);
    ++passed;

    reset("null VM rejected before logging or any VM call");
    CHECK(Agent_OnAttach(NULL, NULL, NULL) == JNI_ERR);
    check_no_work();
    ++passed;

    reset("nonempty options rejected before any VM call");
    char options[] = "TEST-NOT-AN-OPTION";
    CHECK(Agent_OnAttach(&fake_vm, options, NULL) == JNI_ERR);
    CHECK(strcmp(options, "TEST-NOT-AN-OPTION") == 0);
    check_no_work();
    ++passed;

    reset("JNI_OK with NULL environment is failure");
    configured_nonnull_env = 0;
    CHECK(Agent_OnAttach(&fake_vm, NULL, NULL) == JNI_ERR);
    check_log(0, 0);
    ++passed;

    const jint env_errors[] = {JNI_ERR, JNI_EDETACHED, JNI_EVERSION};
    for (size_t i = 0; i < sizeof(env_errors) / sizeof(env_errors[0]); ++i) {
        reset("GetEnv error with NULL environment");
        configured_env_result = env_errors[i];
        configured_nonnull_env = 0;
        CHECK(Agent_OnAttach(&fake_vm, NULL, NULL) == JNI_ERR);
        check_log(0, 0);
        ++passed;
    }

    reset("GetEnv error with nonnull environment must not call through it");
    configured_env_result = JNI_EVERSION;
    CHECK(Agent_OnAttach(&fake_vm, NULL, NULL) == JNI_ERR);
    check_log(0, 0);
    ++passed;

    reset("GetVersionNumber failure remains failure");
    configured_version_result = JVMTI_ERROR_WRONG_PHASE;
    CHECK(Agent_OnAttach(&fake_vm, NULL, NULL) == JNI_ERR);
    check_log(0, 1);
    ++passed;

    printf("ART TI canary host tests: %d passed\n", passed);
    return EXIT_SUCCESS;
}
