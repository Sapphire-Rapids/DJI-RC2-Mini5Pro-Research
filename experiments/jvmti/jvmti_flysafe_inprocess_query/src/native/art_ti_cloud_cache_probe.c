#define _GNU_SOURCE
#include <android/log.h>
#include <dlfcn.h>
#include <stdlib.h>
#include <pthread.h>
#if defined(__ANDROID__)
#include <link.h>
#include <sys/uio.h>
#endif
#include <jni.h>
#include <jvmti.h>
#include <stdatomic.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>

#define CLOUD_TAG "FindUAS-Cloud-Cache"
#define CLOUD_SCHEMA "finduas-cloud-cache/v1"
#define ART_TI_VERSION ((jint)0x70010200)
#define CLASS_LIMIT 131072
#define MEMBER_LIMIT 4096
#define VALUE_LIMIT 4096
#define ACC_STATIC 0x0008
#define ACC_NATIVE 0x0100

static atomic_flag entered = ATOMIC_FLAG_INIT;

static uint32_t le32(const unsigned char *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static int valid_sid(const char *options, char sid[17]) {
    if (options == NULL) return 0;
    for (size_t i = 0; i < 16; ++i) {
        unsigned char c = (unsigned char)options[i];
        if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return 0;
        sid[i] = (char)c;
    }
    if (options[16] != '\0') return 0;
    sid[16] = '\0';
    return 1;
}

static int clear_exception(JNIEnv *jni) {
    if ((*jni)->ExceptionCheck(jni) == JNI_FALSE) return 0;
    (*jni)->ExceptionClear(jni);
    return 1;
}

static void release(jvmtiEnv *ti, void *memory) {
    if (memory != NULL) (*ti)->Deallocate(ti, (unsigned char *)memory);
}

/* Metadata IDs avoid factory calls, reflective lookup and class initialization. */
static jfieldID field(jvmtiEnv *ti, jclass cls, const char *name, const char *sig,
                     int want_static) {
    jfieldID *ids = NULL, result = NULL;
    jint count = 0;
    if ((*ti)->GetClassFields(ti, cls, &count, &ids) != JVMTI_ERROR_NONE ||
        count < 0 || count > MEMBER_LIMIT || (count && ids == NULL)) {
        release(ti, ids);
        return NULL;
    }
    int matches = 0, valid = 1;
    for (jint i = 0; i < count; ++i) {
        char *n = NULL, *s = NULL;
        jint modifiers = 0;
        jvmtiError rc = (*ti)->GetFieldName(ti, cls, ids[i], &n, &s, NULL);
        if (rc != JVMTI_ERROR_NONE || n == NULL || s == NULL) valid = 0;
        if (valid && strcmp(n, name) == 0 && strcmp(s, sig) == 0) {
            if ((*ti)->GetFieldModifiers(ti, cls, ids[i], &modifiers) != JVMTI_ERROR_NONE ||
                !!(modifiers & ACC_STATIC) != want_static) valid = 0;
            result = ids[i];
            ++matches;
        }
        release(ti, n); release(ti, s);
        if (!valid) break;
    }
    release(ti, ids);
    return valid && matches == 1 ? result : NULL;
}

static jmethodID method(jvmtiEnv *ti, jclass cls, const char *name, const char *sig, jint flags) {
    jmethodID *ids = NULL, result = NULL;
    jint count = 0;
    if ((*ti)->GetClassMethods(ti, cls, &count, &ids) != JVMTI_ERROR_NONE ||
        count < 0 || count > MEMBER_LIMIT || (count && ids == NULL)) {
        release(ti, ids);
        return NULL;
    }
    int matches = 0, valid = 1;
    for (jint i = 0; i < count; ++i) {
        char *n = NULL, *s = NULL;
        jint modifiers = 0;
        jvmtiError rc = (*ti)->GetMethodName(ti, ids[i], &n, &s, NULL);
        if (rc != JVMTI_ERROR_NONE || n == NULL || s == NULL) valid = 0;
        if (valid && strcmp(n, name) == 0 && strcmp(s, sig) == 0) {
            if ((*ti)->GetMethodModifiers(ti, ids[i], &modifiers) != JVMTI_ERROR_NONE ||
                (modifiers & (ACC_STATIC | ACC_NATIVE)) != flags) valid = 0;
            result = ids[i];
            ++matches;
        }
        release(ti, n); release(ti, s);
        if (!valid) break;
    }
    release(ti, ids);
    return valid && matches == 1 ? result : NULL;
}

static int exact_string(JNIEnv *jni, jstring value, const char *expected) {
    if (value == NULL) return 0;
    size_t length = strlen(expected);
    if ((*jni)->GetStringLength(jni, value) != (jsize)length || length > 64) return 0;
    jchar chars[64];
    (*jni)->GetStringRegion(jni, value, 0, (jsize)length, chars);
    if ((*jni)->ExceptionCheck(jni)) return 0;
    for (size_t i = 0; i < length; ++i) if (chars[i] != (unsigned char)expected[i]) return 0;
    return 1;
}

struct owner_guard {
    void *handle;
    uintptr_t slot, mediator, framework, cache;
    uintptr_t framework_vtable, cache_vtable;
};

#if defined(FINDUAS_CLOUD_HOST_TEST)
static int native_owner_open(struct owner_guard *guard);
static int native_owner_same(const struct owner_guard *guard);
static void native_owner_close(struct owner_guard *guard);
#elif defined(__ANDROID__)
static int copy_self(uintptr_t address, void *out, size_t length) {
    struct iovec local = {out, length};
    struct iovec remote = {(void *)address, length};
    return address != 0 && process_vm_readv(getpid(), &local, 1, &remote, 1, 0) == (ssize_t)length;
}

struct image_check { uintptr_t base; int matches, build_id_ok; const unsigned char *expected; };
static int inspect_image(struct dl_phdr_info *info, size_t size, void *opaque) {
    (void)size;
    struct image_check *check = opaque;
    if ((uintptr_t)info->dlpi_addr != check->base) return 0;
    ++check->matches;
    for (ElfW(Half) i = 0; i < info->dlpi_phnum; ++i) {
        const ElfW(Phdr) *p = &info->dlpi_phdr[i];
        if (p->p_type != PT_NOTE || p->p_memsz > 65536) continue;
        uintptr_t cursor = check->base + p->p_vaddr;
        size_t left = p->p_memsz;
        while (left >= 12) {
            uint32_t header[3];
            if (!copy_self(cursor, header, sizeof(header))) return 1;
            if (header[0] > left - 12 || header[1] > left - 12) return 1;
            size_t name = ((size_t)header[0] + 3u) & ~(size_t)3u;
            size_t desc = ((size_t)header[1] + 3u) & ~(size_t)3u;
            if (name > left - 12 || desc > left - 12 - name) return 1;
            if (header[0] == 4 && header[1] == 20 && header[2] == NT_GNU_BUILD_ID) {
                unsigned char owner[4], actual[20];
                if (!copy_self(cursor + 12, owner, 4) ||
                    !copy_self(cursor + 12 + name, actual, 20)) return 1;
                if (memcmp(owner, "GNU", 4) == 0 && memcmp(actual, check->expected, 20) == 0)
                    check->build_id_ok = 1;
            }
            cursor += 12 + name + desc;
            left -= 12 + name + desc;
        }
    }
    return 0;
}

static int native_owner_same(const struct owner_guard *guard) {
    uintptr_t mediator = 0, framework = 0, cache = 0, vtable = 0;
    unsigned char initialized = 0;
    if (!copy_self(guard->slot, &mediator, sizeof(mediator)) || mediator == 0 ||
        mediator != guard->mediator ||
        !copy_self(mediator + 0x4c, &initialized, 1) || !(initialized & 1) ||
        !copy_self(mediator + 0x1d0, &framework, sizeof(framework)) ||
        framework != guard->framework || framework == 0 ||
        !copy_self(framework, &vtable, sizeof(vtable)) || vtable != guard->framework_vtable ||
        !copy_self(framework + 0x1c, &cache, sizeof(cache)) || cache != guard->cache || cache == 0 ||
        !copy_self(cache, &vtable, sizeof(vtable)) || vtable != guard->cache_vtable) return 0;
    return 1;
}

static int native_owner_open(struct owner_guard *guard) {
    if (sizeof(void *) != 4) return 0;
    guard->handle = dlopen("libsdk_jni.so", RTLD_NOW | RTLD_LOCAL | RTLD_NOLOAD);
    if (guard->handle == NULL) return 0;
    void *slot = dlsym(guard->handle, "_ZN3uav3sdk17g_pModuleMediatorE");
    void *framework_table = dlsym(guard->handle, "_ZTVN3uav3sdk16SDKFrameworkCoreE");
    void *cache_table = dlsym(guard->handle, "_ZTVN3uav3sdk10CacheLayerE");
    Dl_info image, framework_image, cache_image;
    if (slot == NULL || framework_table == NULL || cache_table == NULL ||
        !dladdr(slot, &image) || image.dli_fbase == NULL ||
        !dladdr(framework_table, &framework_image) || !dladdr(cache_table, &cache_image) ||
        framework_image.dli_fbase != image.dli_fbase || cache_image.dli_fbase != image.dli_fbase) return 0;
    static const unsigned char sdk_build_id[20] = {
        0xba,0xc2,0x70,0xa9,0x52,0xc8,0xdd,0xfb,0xec,0xf1,
        0xbc,0xdb,0x42,0x98,0xd3,0x2e,0x5b,0xf9,0xc3,0x87
    };
    struct image_check check = {(uintptr_t)image.dli_fbase, 0, 0, sdk_build_id};
    dl_iterate_phdr(inspect_image, &check);
    if (check.matches != 1 || !check.build_id_ok) return 0;
    guard->slot = (uintptr_t)slot;
    guard->framework_vtable = (uintptr_t)framework_table + 8;
    guard->cache_vtable = (uintptr_t)cache_table + 8;
    if (!copy_self(guard->slot, &guard->mediator, sizeof(guard->mediator)) ||
        guard->mediator == 0 ||
        !copy_self(guard->mediator + 0x1d0, &guard->framework, sizeof(guard->framework)) ||
        guard->framework == 0 ||
        !copy_self(guard->framework + 0x1c, &guard->cache, sizeof(guard->cache)) ||
        guard->cache == 0) return 0;
    return native_owner_same(guard);
}

static void native_owner_close(struct owner_guard *guard) {
    if (guard->handle != NULL) dlclose(guard->handle);
    guard->handle = NULL;
}
#else
static int native_owner_open(struct owner_guard *guard) { (void)guard; return 0; }
static int native_owner_same(const struct owner_guard *guard) { (void)guard; return 0; }
static void native_owner_close(struct owner_guard *guard) { (void)guard; }
#endif


#define CLOUD_TEXT_LIMIT 65536
#define MMKV_INSTANCE_LIMIT 128
struct mmkv_guard {
    void *handle;
    uintptr_t instance, map_slot;
    pthread_mutex_t *global_lock, *instance_lock;
    int global_locked, instance_locked;
};

#if defined(FINDUAS_CLOUD_HOST_TEST)
static int mmkv_open(struct mmkv_guard *guard);
static void mmkv_release(struct mmkv_guard *guard);
#elif defined(__ANDROID__)
static int default_instance_key(uintptr_t address) {
    uint32_t words[3];
    unsigned char text[12];
    if (!copy_self(address, words, sizeof(words))) return -1;
    size_t size = words[0] & 1 ? words[1] : (words[0] & 255u) >> 1;
    if (size != sizeof(text)) return 0;
    uintptr_t chars = words[0] & 1 ? words[2] : address + 1;
    if (!copy_self(chars, text, sizeof(text))) return -1;
    return memcmp(text, "mmkv.default", sizeof(text)) == 0;
}

static int mmkv_open(struct mmkv_guard *guard) {
    static const unsigned char mmkv_build_id[20] = {
        0x42,0x24,0x36,0x32,0x44,0x1b,0x28,0xff,0xee,0x60,
        0x0d,0x44,0x22,0xd9,0x76,0x8b,0xf0,0x51,0xea,0x85
    };
    guard->handle = dlopen("libmmkv.so", RTLD_NOW | RTLD_LOCAL | RTLD_NOLOAD);
    if (guard->handle == NULL) return 1;
    void *entry = dlsym(guard->handle, "JNI_OnLoad");
    Dl_info image;
    if (entry == NULL || !dladdr(entry, &image) || image.dli_fbase == NULL) return 2;
    struct image_check check = {(uintptr_t)image.dli_fbase, 0, 0, mmkv_build_id};
    dl_iterate_phdr(inspect_image, &check);
    if (check.matches != 1 || !check.build_id_ok) return 2;
    guard->global_lock = (pthread_mutex_t *)(check.base + 0x152a0);
    guard->map_slot = check.base + 0x152b4;
    if (pthread_mutex_trylock(guard->global_lock) != 0) return 3;
    guard->global_locked = 1;
    uintptr_t map = 0, node = 0;
    uint32_t count = 0;
    if (!copy_self(guard->map_slot, &map, sizeof(map)) || map == 0) return 4;
    if (!copy_self(map + 8, &node, sizeof(node)) || !copy_self(map + 12, &count, sizeof(count))) return 10;
    if (count > MMKV_INSTANCE_LIMIT) return 10;
    unsigned int visited = 0, matches = 0;
    while (node != 0 && visited < count) {
        int matched = default_instance_key(node + 8);
        if (matched < 0) return 10;
        if (matched) {
            if (!copy_self(node + 0x14, &guard->instance, sizeof(guard->instance))) return 10;
            ++matches;
        }
        if (!copy_self(node, &node, sizeof(node))) return 10;
        ++visited;
    }
    if (node != 0 || visited != count || matches > 1) return 10;
    if (matches != 1 || guard->instance == 0) return 5;
    if (default_instance_key(guard->instance + 0x14) != 1) return 10;
    guard->instance_lock = (pthread_mutex_t *)(guard->instance + 0x94);
    if (pthread_mutex_trylock(guard->instance_lock) != 0) return 6;
    guard->instance_locked = 1;
    unsigned char needs_load = 1, multi = 1, ashmem = 1;
    if (!copy_self(guard->instance + 0x50, &needs_load, 1) ||
        !copy_self(guard->instance + 0xbc, &multi, 1) ||
        !copy_self(guard->instance + 0xbd, &ashmem, 1)) return 10;
    if (needs_load != 0) return 7;
    if (multi != 0 || ashmem != 0) return 8;
    return 0;
}

static void mmkv_release(struct mmkv_guard *guard) {
    if (guard->instance_locked) pthread_mutex_unlock(guard->instance_lock);
    if (guard->global_locked) pthread_mutex_unlock(guard->global_lock);
    if (guard->handle != NULL) dlclose(guard->handle);
    guard->instance_locked = guard->global_locked = 0;
    guard->handle = NULL;
}
#else
static int mmkv_open(struct mmkv_guard *guard) { (void)guard; return 1; }
static void mmkv_release(struct mmkv_guard *guard) { (void)guard; }
#endif

static char *utf8_string(JNIEnv *jni, jstring str, size_t limit, int *code, size_t *length) {
    *code = 0; *length = 0;
    if (str == NULL) return NULL;
    jsize size = (*jni)->GetStringLength(jni, str);
    if ((*jni)->ExceptionCheck(jni)) { *code = 4; return NULL; }
    if (size < 0 || (size_t)size > limit) { *code = 3; return NULL; }
    jchar *units = size == 0 ? NULL : malloc((size_t)size * sizeof(jchar));
    char *result = malloc(limit + 1);
    if ((size != 0 && units == NULL) || result == NULL) { free(units); free(result); *code = 3; return NULL; }
    if (size != 0) (*jni)->GetStringRegion(jni, str, 0, size, units);
    if ((*jni)->ExceptionCheck(jni)) { free(units); free(result); *code = 4; return NULL; }
    size_t used = 0;
    for (jsize i = 0; i < size; ++i) {
        uint32_t cp = units[i];
        if (cp >= 0xd800 && cp <= 0xdbff) {
            if (++i == size || units[i] < 0xdc00 || units[i] > 0xdfff) { *code = 5; break; }
            cp = 0x10000 + ((cp - 0xd800) << 10) + units[i] - 0xdc00;
        } else if (cp == 0 || (cp >= 0xdc00 && cp <= 0xdfff)) { *code = 5; break; }
        size_t needed = cp < 0x80 ? 1 : cp < 0x800 ? 2 : cp < 0x10000 ? 3 : 4;
        if (needed > limit - used) { *code = 3; break; }
        if (needed == 1) result[used++] = (char)cp;
        else {
            if (needed == 4) result[used++] = (char)(0xf0 | (cp >> 18));
            if (needed >= 3) result[used++] = (char)((needed == 3 ? 0xe0 : 0x80) | ((cp >> 12) & 0x3f));
            result[used++] = (char)((needed == 2 ? 0xc0 : 0x80) | ((cp >> 6) & 0x3f));
            result[used++] = (char)(0x80 | (cp & 0x3f));
        }
    }
    free(units);
    if (*code != 0) { free(result); return NULL; }
    result[used] = '\0'; *length = used;
    return result;
}

static int exact_key(JNIEnv *jni, jvmtiEnv *ti, jclass owner, jclass key_class,
                     jclass base, const char *field_name, const char *key_name,
                     int want_get, int want_set, int want_listen, jstring *native_name_out) {
    jfieldID source = field(ti, owner, field_name, "Luav/sdk/keyvalue/key/UAVKeyInfo;", 1);
    jfieldID fields[9];
    const char *names[9] = {"a", "b", "i", "j", "d", "e", "f", "g", "h"};
    const char *sigs[9] = {"I", "I", "Ljava/lang/String;", "Ljava/lang/String;", "Z", "Z", "Z", "Z", "Z"};
    if (source == NULL) return 0;
    for (int i = 0; i < 9; ++i) if ((fields[i] = field(ti, base, names[i], sigs[i], 0)) == NULL) return 0;
    jobject key = (*jni)->GetStaticObjectField(jni, owner, source);
    if (key == NULL || (*jni)->ExceptionCheck(jni)) return 0;
    jclass actual = (*jni)->GetObjectClass(jni, key);
    int valid = actual != NULL && (*jni)->IsSameObject(jni, actual, key_class);
    if (actual != NULL) (*jni)->DeleteLocalRef(jni, actual);
    jstring name = NULL, native = NULL;
    if (!valid || (*jni)->ExceptionCheck(jni)) goto end;
    jint component = (*jni)->GetIntField(jni, key, fields[0]);
    if ((*jni)->ExceptionCheck(jni)) { valid = 0; goto end; }
    jint sub = (*jni)->GetIntField(jni, key, fields[1]);
    if ((*jni)->ExceptionCheck(jni)) { valid = 0; goto end; }
    name = (jstring)(*jni)->GetObjectField(jni, key, fields[2]);
    if ((*jni)->ExceptionCheck(jni)) { valid = 0; goto end; }
    native = (jstring)(*jni)->GetObjectField(jni, key, fields[3]);
    if ((*jni)->ExceptionCheck(jni)) { valid = 0; goto end; }
    const int expected[5] = {want_get, want_set, want_listen, 0, 0};
    for (int i = 0; i < 5; ++i) {
        jboolean value = (*jni)->GetBooleanField(jni, key, fields[i + 4]);
        if ((*jni)->ExceptionCheck(jni) || value != expected[i]) { valid = 0; goto end; }
    }
    valid = component == 65534 && sub == 65534 && exact_string(jni, name, key_name) && exact_string(jni, native, key_name);
    if (valid) { *native_name_out = native; native = NULL; }
end:
    if (name != NULL) (*jni)->DeleteLocalRef(jni, name);
    if (native != NULL) (*jni)->DeleteLocalRef(jni, native);
    (*jni)->DeleteLocalRef(jni, key);
    return valid;
}

#include "cloud_policy_parser.h"

static jbyteArray sdk_cache(JNIEnv *jni, jclass cls, jmethodID id, jstring name, int *count) {
    jvalue args[6];
    args[0].i = 0; args[1].i = 65534; args[2].i = 0;
    args[3].i = 65534; args[4].i = 65534; args[5].l = name;
    ++*count;
    return (jbyteArray)(*jni)->CallStaticObjectMethodA(jni, cls, id, args);
}

JNIEXPORT jint JNICALL Agent_OnAttach(JavaVM *vm, char *options, void *reserved) {
    (void)reserved;
    char sid[17];
    if (!valid_sid(options, sid) || vm == NULL || *vm == NULL || (*vm)->GetEnv == NULL) return JNI_ERR;
    if (atomic_flag_test_and_set_explicit(&entered, memory_order_acq_rel)) return JNI_OK;
    pid_t pid = getpid(); uid_t uid = getuid(); gid_t gid = getgid();
    __android_log_print(ANDROID_LOG_INFO, CLOUD_TAG,
        "schema=" CLOUD_SCHEMA " phase=enter sid=%s pid=%ld uid=%lu gid=%lu abi_bits=%u",
        sid, (long)pid, (unsigned long)uid, (unsigned long)gid, (unsigned int)(sizeof(void *) * 8));
    JNIEnv *jni = NULL; jvmtiEnv *ti = NULL;
    jclass *classes = NULL; jint class_count = 0;
    jclass selected[6] = {0}; int matches[6] = {0};
    const char *wanted[6] = {
        "Luav/jni/JNIKeyValue;", "Luav/sdk/keyvalue/key/UAVProductKey;",
        "Luav/sdk/keyvalue/key/UAVKeyInfo;", "Luav/sdk/keyvalue/key/UAVKeyInfoBase;",
        "Luav/component/CloudControl/CloudControlNamespaces;", "Lcom/tencent/mmkv/MMKV;"
    };
    jobject loader = NULL, namespace_enum = NULL, mmkv_wrapper = NULL;
    jstring namespace_text = NULL, root_dir = NULL, storage_key = NULL, stored = NULL;
    jstring cloud_name = NULL, product_name = NULL;
    jbyteArray cloud_bytes = NULL, product_bytes = NULL;
    char *namespace_ascii = NULL, *policy_ascii = NULL, *cloud_ascii = NULL;
    size_t namespace_length = 0, policy_length = 0, cloud_length = 0;
    struct owner_guard sdk_guard = {0}; struct mmkv_guard mmkv_guard = {0};
    struct cloud_policy_summary summary = {-1,-1,-1,-1,-1,-1,-1,-1,-1};
    int stage = 1, exception = 0, cloud_count = 0, product_count = 0, mmkv_count = 0;
    int namespace_present = -1, mmkv_present = -1, cloud_present = -1, product_present = -1;
    int product_type = -1, receiver_type = -1, receiver_index = -1;
    int json_rc = -1, guard_rc = -1, dispose_attempted = 0, text_rc = 0;
    jint jni_rc = (*vm)->GetEnv(vm, (void **)&jni, JNI_VERSION_1_6), env_rc = JNI_ERR;
    jvmtiError dispose_rc = (jvmtiError)-1;
    if (jni_rc != JNI_OK || jni == NULL || *jni == NULL) goto done;
    if (clear_exception(jni)) { exception = 1; goto done; }
    stage = 2;
    env_rc = (*vm)->GetEnv(vm, (void **)&ti, ART_TI_VERSION);
    if (env_rc != JNI_OK || ti == NULL || *ti == NULL) { ti = NULL; goto done; }
    stage = 3;
    if ((*ti)->GetLoadedClasses(ti, &class_count, &classes) != JVMTI_ERROR_NONE ||
        class_count < 0 || class_count > CLASS_LIMIT || (class_count && classes == NULL)) goto done;
    for (jint i = 0; i < class_count; ++i) {
        char *signature = NULL;
        if ((*ti)->GetClassSignature(ti, classes[i], &signature, NULL) != JVMTI_ERROR_NONE || signature == NULL) {
            release(ti, signature); goto done;
        }
        for (int j = 0; j < 6; ++j) if (strcmp(signature, wanted[j]) == 0) { selected[j] = classes[i]; ++matches[j]; }
        release(ti, signature);
    }
    stage = 4;
    for (int i = 0; i < 6; ++i) {
        jint status = 0; jobject other_loader = NULL;
        if (matches[i] != 1 || (*ti)->GetClassStatus(ti, selected[i], &status) != JVMTI_ERROR_NONE ||
            !(status & JVMTI_CLASS_STATUS_INITIALIZED) || (status & JVMTI_CLASS_STATUS_ERROR)) goto done;
        if ((*ti)->GetClassLoader(ti, selected[i], &other_loader) != JVMTI_ERROR_NONE || other_loader == NULL) goto done;
        if (i == 0) loader = other_loader;
        else {
            int same = (*jni)->IsSameObject(jni, loader, other_loader);
            (*jni)->DeleteLocalRef(jni, other_loader);
            if (!same) goto done;
        }
    }
    stage = 5;
    jfieldID enum_field = field(ti, selected[4], "r", "Luav/component/CloudControl/CloudControlNamespaces;", 1);
    jfieldID namespace_field = field(ti, selected[4], "namespace", "Ljava/lang/String;", 0);
    jfieldID root_field = field(ti, selected[5], "rootDir", "Ljava/lang/String;", 1);
    jfieldID handle_field = field(ti, selected[5], "nativeHandle", "J", 0);
    jmethodID sync = method(ti, selected[0], "native_get_sync", "(IIIIILjava/lang/String;)[B", ACC_STATIC | ACC_NATIVE);
    jmethodID mmkv_default = method(ti, selected[5], "defaultMMKV", "()Lcom/tencent/mmkv/MMKV;", ACC_STATIC);
    jmethodID mmkv_size = method(ti, selected[5], "getValueActualSize", "(Ljava/lang/String;)I", 0);
    jmethodID mmkv_decode = method(ti, selected[5], "decodeString", "(Ljava/lang/String;)Ljava/lang/String;", 0);
    if (!enum_field || !namespace_field || !root_field || !handle_field || !sync || !mmkv_default || !mmkv_size || !mmkv_decode) goto done;
    if (!exact_key(jni, ti, selected[1], selected[2], selected[3], "U", "CloudControlData", 0, 1, 0, &cloud_name) ||
        (*jni)->ExceptionCheck(jni)) goto done;
    if (!exact_key(jni, ti, selected[1], selected[2], selected[3], "o", "ProductType", 1, 0, 1, &product_name) ||
        (*jni)->ExceptionCheck(jni)) goto done;
    stage = 6;
    namespace_enum = (*jni)->GetStaticObjectField(jni, selected[4], enum_field);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    if (namespace_enum == NULL) { namespace_present = 0; guard_rc = 11; goto done; }
    namespace_text = (jstring)(*jni)->GetObjectField(jni, namespace_enum, namespace_field);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    namespace_ascii = utf8_string(jni, namespace_text, 128, &text_rc, &namespace_length);
    if (namespace_ascii == NULL || namespace_length == 0) { namespace_present = 0; guard_rc = 11; goto done; }
    namespace_present = 1;
    root_dir = (jstring)(*jni)->GetStaticObjectField(jni, selected[5], root_field);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    if (root_dir == NULL || (*jni)->GetStringLength(jni, root_dir) == 0) { guard_rc = 4; goto done; }
    if ((*jni)->ExceptionCheck(jni)) goto done;
    static const char key_prefix[] = "cloud_control_mmkv_prefix_";
    jchar key_units[160];
    size_t prefix_length = sizeof(key_prefix) - 1;
    jsize namespace_units = (*jni)->GetStringLength(jni, namespace_text);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    if (namespace_units < 1 || namespace_units > 128 || prefix_length + (size_t)namespace_units > 160) { guard_rc = 11; goto done; }
    for (size_t i = 0; i < prefix_length; ++i) key_units[i] = (unsigned char)key_prefix[i];
    (*jni)->GetStringRegion(jni, namespace_text, 0, namespace_units, key_units + prefix_length);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    storage_key = (*jni)->NewString(jni, key_units, (jsize)prefix_length + namespace_units);
    if (storage_key == NULL || (*jni)->ExceptionCheck(jni)) goto done;
    stage = 10;
    if (!native_owner_open(&sdk_guard)) { guard_rc = 12; goto done; }
    stage = 7;
    guard_rc = mmkv_open(&mmkv_guard);
    if (guard_rc != 0) goto done;
    stage = 8;
    mmkv_wrapper = (*jni)->CallStaticObjectMethodA(jni, selected[5], mmkv_default, NULL);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    if (mmkv_wrapper == NULL) { guard_rc = 9; goto done; }
    jlong native_handle = (*jni)->GetLongField(jni, mmkv_wrapper, handle_field);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    if (native_handle <= 0 || (uint64_t)native_handle != mmkv_guard.instance) { guard_rc = 9; goto done; }
    jvalue one_argument[1]; one_argument[0].l = storage_key;
    jint value_size = (*jni)->CallIntMethodA(jni, mmkv_wrapper, mmkv_size, one_argument);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    if (value_size < 0 || value_size > CLOUD_TEXT_LIMIT) { guard_rc = 13; goto done; }
    mmkv_count = 1;
    stored = (jstring)(*jni)->CallObjectMethodA(jni, mmkv_wrapper, mmkv_decode, one_argument);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    mmkv_present = stored == NULL ? 0 : 1;
    mmkv_release(&mmkv_guard);
    policy_ascii = utf8_string(jni, stored, CLOUD_TEXT_LIMIT, &text_rc, &policy_length);
    if (text_rc != 0) { stage = 9; json_rc = text_rc == 5 ? 8 : 7; goto done; }
    if (!native_owner_same(&sdk_guard)) { stage = 10; guard_rc = 12; goto done; }
    cloud_bytes = sdk_cache(jni, selected[0], sync, cloud_name, &cloud_count);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    if (!native_owner_same(&sdk_guard)) { stage = 10; guard_rc = 12; goto done; }
    cloud_present = cloud_bytes == NULL ? 0 : 1;
    if (cloud_bytes != NULL) {
        jsize size = (*jni)->GetArrayLength(jni, cloud_bytes);
        if ((*jni)->ExceptionCheck(jni)) goto done;
        if (size < 12 || size > CLOUD_TEXT_LIMIT + 12) { guard_rc = 14; goto done; }
        unsigned char header[12];
        (*jni)->GetByteArrayRegion(jni, cloud_bytes, 0, 12, (jbyte *)header);
        if ((*jni)->ExceptionCheck(jni)) goto done;
        uint32_t type = le32(header), index = le32(header + 4), length = le32(header + 8);
        if (type > 255 || index > 255 || length != (uint32_t)size - 12u) { guard_rc = 14; goto done; }
        receiver_type = (int)type; receiver_index = (int)index; cloud_length = length;
        cloud_ascii = malloc(cloud_length + 1);
        if (cloud_ascii == NULL) { guard_rc = 14; goto done; }
        (*jni)->GetByteArrayRegion(jni, cloud_bytes, 12, (jsize)length, (jbyte *)cloud_ascii);
        if ((*jni)->ExceptionCheck(jni)) goto done;
        cloud_ascii[length] = '\0';
        for (size_t i = 0; i < cloud_length; ++i) if ((unsigned char)cloud_ascii[i] > 127 || cloud_ascii[i] == '\0') { guard_rc = 14; goto done; }
    }
    product_bytes = sdk_cache(jni, selected[0], sync, product_name, &product_count);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    if (!native_owner_same(&sdk_guard)) { stage = 10; guard_rc = 12; goto done; }
    product_present = product_bytes == NULL ? 0 : 1;
    if (product_bytes != NULL) {
        jsize size = (*jni)->GetArrayLength(jni, product_bytes);
        if ((*jni)->ExceptionCheck(jni)) goto done;
        if (size != 4) { guard_rc = 15; goto done; }
        unsigned char bytes[4];
        (*jni)->GetByteArrayRegion(jni, product_bytes, 0, 4, (jbyte *)bytes);
        if ((*jni)->ExceptionCheck(jni)) goto done;
        uint32_t number = le32(bytes);
        if (number > 65535) { guard_rc = 15; goto done; }
        product_type = (int)number;
    }
    stage = 9;
    json_rc = (int)cloud_policy_audit(policy_ascii, policy_length, product_type, cloud_ascii, cloud_length, receiver_type, receiver_index, &summary);
    if (json_rc != CLOUD_POLICY_OK && json_rc != CLOUD_POLICY_NAMESPACE_NULL && json_rc != CLOUD_POLICY_PRODUCT_UNOBSERVED) goto done;
    stage = 0;

done:
    mmkv_release(&mmkv_guard);
    native_owner_close(&sdk_guard);
    free(namespace_ascii); free(policy_ascii); free(cloud_ascii);
    if (jni != NULL && *jni != NULL) {
        exception |= clear_exception(jni);
        jobject refs[] = {loader,namespace_enum,namespace_text,root_dir,storage_key,stored,cloud_name,product_name,mmkv_wrapper,cloud_bytes,product_bytes};
        for (unsigned int i = 0; i < sizeof(refs) / sizeof(refs[0]); ++i) if (refs[i]) (*jni)->DeleteLocalRef(jni, refs[i]);
        if (classes != NULL && class_count > 0) for (jint i = 0; i < class_count; ++i) (*jni)->DeleteLocalRef(jni, classes[i]);
    }
    if (ti != NULL) {
        release(ti, classes); dispose_attempted = 1; dispose_rc = (*ti)->DisposeEnvironment(ti); ti = NULL;
        if (dispose_rc != JVMTI_ERROR_NONE && stage == 0) stage = 13;
    }
    if (exception && stage == 0) stage = 14;
    int ready = stage == 0 && !exception && jni_rc == JNI_OK && env_rc == JNI_OK && dispose_attempted && dispose_rc == JVMTI_ERROR_NONE;
    __android_log_print(ANDROID_LOG_INFO, CLOUD_TAG,
        "schema=" CLOUD_SCHEMA " phase=result sid=%s pid=%ld uid=%lu gid=%lu abi_bits=%u"
        " ready=%d stage=%d exception=%d cloud_query_count=%d product_query_count=%d mmkv_decode_count=%d"
        " namespace_present=%d mmkv_present=%d cloud_present=%d product_present=%d product_type=%d receiver_type=%d receiver_index=%d"
        " json_rc=%d entry_count=%d duplicate_count=%d candidate_count=%d match_count=%d default_match=%d product_blocked_count=%d"
        " jni_rc=%d env_rc=%d guard_rc=%d dispose_attempted=%d dispose_rc=%d",
        sid,(long)pid,(unsigned long)uid,(unsigned long)gid,(unsigned int)(sizeof(void *) * 8),
        ready,stage,exception,cloud_count,product_count,mmkv_count,
        namespace_present,mmkv_present,cloud_present,product_present,product_type,receiver_type,receiver_index,
        json_rc,summary.row_count,summary.duplicate_row_count,summary.nonempty_candidate_count,summary.matching_candidate_count,summary.default_match,summary.blocked_row_count,
        (int)jni_rc,(int)env_rc,guard_rc,dispose_attempted,(int)dispose_rc);
    return JNI_OK;
}
