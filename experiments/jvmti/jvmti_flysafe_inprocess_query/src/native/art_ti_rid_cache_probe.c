#define _GNU_SOURCE
#include <android/log.h>
#include <dlfcn.h>
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

#define RID_TAG "FindUAS-RID-Cache"
#define RID_SCHEMA "finduas-rid-cache/v1"
#define ART_TI_VERSION ((jint)0x70010200)
#define CLASS_LIMIT 131072
#define MEMBER_LIMIT 4096
#define VALUE_LIMIT 4096
#define ACC_STATIC 0x0008
#define ACC_NATIVE 0x0100

/* JNI serialization, not the aircraft's radio packet. String content is skipped. */
struct rid_value {
    int rid_support, rid_normal, eid_support, eid_normal;
    uint32_t fail_reason;
};

static atomic_flag entered = ATOMIC_FLAG_INIT;

static uint32_t le32(const unsigned char *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static int decode_value(const unsigned char header[8], const unsigned char tail[8],
                        size_t size, struct rid_value *value) {
    if (size < 16 || size > VALUE_LIMIT) return 2;
    uint32_t area_length = le32(header + 4);
    if (area_length > VALUE_LIMIT - 16 || size != (size_t)area_length + 16) return 2;
    for (unsigned int i = 0; i < 4; ++i) if (header[i] > 1) return 3;
    value->eid_support = header[0];
    value->rid_support = header[1];
    value->eid_normal = header[2];
    value->rid_normal = header[3];
    value->fail_reason = le32(tail + 4);
    return 0;
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

static jmethodID sync_method(jvmtiEnv *ti, jclass cls) {
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
        if (valid && strcmp(n, "native_get_sync") == 0 &&
            strcmp(s, "(IIIIILjava/lang/String;)[B") == 0) {
            if ((*ti)->GetMethodModifiers(ti, ids[i], &modifiers) != JVMTI_ERROR_NONE ||
                (modifiers & (ACC_STATIC | ACC_NATIVE)) != (ACC_STATIC | ACC_NATIVE)) valid = 0;
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

#if defined(FINDUAS_RID_HOST_TEST)
static int native_owner_open(struct owner_guard *guard);
static int native_owner_same(const struct owner_guard *guard);
static void native_owner_close(struct owner_guard *guard);
#elif defined(__ANDROID__)
static int copy_self(uintptr_t address, void *out, size_t length) {
    struct iovec local = {out, length};
    struct iovec remote = {(void *)address, length};
    return address != 0 && process_vm_readv(getpid(), &local, 1, &remote, 1, 0) == (ssize_t)length;
}

struct image_check { uintptr_t base; int matches, build_id_ok; };
static int inspect_image(struct dl_phdr_info *info, size_t size, void *opaque) {
    (void)size;
    struct image_check *check = opaque;
    if ((uintptr_t)info->dlpi_addr != check->base) return 0;
    ++check->matches;
    static const unsigned char build_id[20] = {
        0xba,0xc2,0x70,0xa9,0x52,0xc8,0xdd,0xfb,0xec,0xf1,
        0xbc,0xdb,0x42,0x98,0xd3,0x2e,0x5b,0xf9,0xc3,0x87
    };
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
                if (memcmp(owner, "GNU", 4) == 0 && memcmp(actual, build_id, 20) == 0)
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
    struct image_check check = {(uintptr_t)image.dli_fbase, 0, 0};
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

JNIEXPORT jint JNICALL Agent_OnAttach(JavaVM *vm, char *options, void *reserved) {
    (void)reserved;
    char sid[17];
    if (!valid_sid(options, sid) || vm == NULL || *vm == NULL || (*vm)->GetEnv == NULL)
        return JNI_ERR;
    if (atomic_flag_test_and_set_explicit(&entered, memory_order_acq_rel)) return JNI_OK;
    pid_t pid = getpid();
    uid_t uid = getuid();
    gid_t gid = getgid();
    __android_log_print(ANDROID_LOG_INFO, RID_TAG,
        "schema=" RID_SCHEMA " phase=enter sid=%s pid=%ld uid=%lu gid=%lu abi_bits=%u",
        sid, (long)pid, (unsigned long)uid, (unsigned long)gid, (unsigned int)(sizeof(void *) * 8));

    JNIEnv *jni = NULL;
    jvmtiEnv *ti = NULL;
    jclass *classes = NULL;
    jint count = 0;
    jclass selected[4] = {NULL, NULL, NULL, NULL};
    const char *wanted[4] = {
        "Luav/jni/JNIKeyValue;", "Luav/sdk/keyvalue/key/UAVFlightControllerKey;",
        "Luav/sdk/keyvalue/key/UAVKeyInfo;", "Luav/sdk/keyvalue/key/UAVKeyInfoBase;"
    };
    int matches[4] = {0, 0, 0, 0};
    jobject loader = NULL, key = NULL;
    jstring identifier = NULL, native_name = NULL;
    jbyteArray bytes = NULL;
    int stage = 1, exception = 0, query_count = 0, value_present = 0;
    int parse_rc = -1, dispose_attempted = 0;
    jint jni_rc = (*vm)->GetEnv(vm, (void **)&jni, JNI_VERSION_1_6);
    jint env_rc = JNI_ERR;
    jvmtiError dispose_rc = (jvmtiError)-1;
    struct rid_value value = {-1, -1, -1, -1, 0};
    struct owner_guard guard = {0};
    if (jni_rc != JNI_OK || jni == NULL || *jni == NULL) goto done;
    if (clear_exception(jni)) { exception = 1; goto done; }
    stage = 2;
    env_rc = (*vm)->GetEnv(vm, (void **)&ti, ART_TI_VERSION);
    if (env_rc != JNI_OK || ti == NULL || *ti == NULL) { ti = NULL; goto done; }
    stage = 3;
    if ((*ti)->GetLoadedClasses(ti, &count, &classes) != JVMTI_ERROR_NONE ||
        count < 0 || count > CLASS_LIMIT || (count && classes == NULL)) goto done;
    for (jint i = 0; i < count; ++i) {
        char *signature = NULL;
        if ((*ti)->GetClassSignature(ti, classes[i], &signature, NULL) != JVMTI_ERROR_NONE ||
            signature == NULL) { release(ti, signature); goto done; }
        for (int j = 0; j < 4; ++j) {
            if (strcmp(signature, wanted[j]) == 0) { selected[j] = classes[i]; ++matches[j]; }
        }
        release(ti, signature);
    }
    stage = 4;
    for (int i = 0; i < 4; ++i) {
        jint status = 0;
        if (matches[i] != 1 || (*ti)->GetClassStatus(ti, selected[i], &status) != JVMTI_ERROR_NONE ||
            !(status & JVMTI_CLASS_STATUS_INITIALIZED) || (status & JVMTI_CLASS_STATUS_ERROR)) goto done;
        jobject other_loader = NULL;
        if ((*ti)->GetClassLoader(ti, selected[i], &other_loader) != JVMTI_ERROR_NONE ||
            other_loader == NULL) goto done;
        if (i == 0) loader = other_loader;
        else {
            int same = (*jni)->IsSameObject(jni, loader, other_loader);
            (*jni)->DeleteLocalRef(jni, other_loader);
            if (!same) goto done;
        }
    }
    stage = 5;
    jfieldID key_field = field(ti, selected[1], "o8", "Luav/sdk/keyvalue/key/UAVKeyInfo;", 1);
    jfieldID component_field = field(ti, selected[3], "a", "I", 0);
    jfieldID subcomponent_field = field(ti, selected[3], "b", "I", 0);
    jfieldID identifier_field = field(ti, selected[3], "i", "Ljava/lang/String;", 0);
    jfieldID native_name_field = field(ti, selected[3], "j", "Ljava/lang/String;", 0);
    jfieldID get_field = field(ti, selected[3], "d", "Z", 0);
    jfieldID set_field = field(ti, selected[3], "e", "Z", 0);
    jfieldID listen_field = field(ti, selected[3], "f", "Z", 0);
    jfieldID action_field = field(ti, selected[3], "g", "Z", 0);
    jfieldID event_field = field(ti, selected[3], "h", "Z", 0);
    jmethodID method = sync_method(ti, selected[0]);
    if (!key_field || !component_field || !subcomponent_field || !identifier_field ||
        !native_name_field || !get_field || !set_field || !listen_field || !action_field ||
        !event_field || !method) goto done;
    stage = 6;
    key = (*jni)->GetStaticObjectField(jni, selected[1], key_field);
    if (key == NULL || (*jni)->ExceptionCheck(jni)) goto done;
    jclass key_class = (*jni)->GetObjectClass(jni, key);
    int key_exact = key_class != NULL && (*jni)->IsSameObject(jni, key_class, selected[2]);
    if (key_class != NULL) (*jni)->DeleteLocalRef(jni, key_class);
    if (!key_exact || (*jni)->ExceptionCheck(jni)) goto done;
    jint component = (*jni)->GetIntField(jni, key, component_field);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    jint subcomponent = (*jni)->GetIntField(jni, key, subcomponent_field);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    identifier = (jstring)(*jni)->GetObjectField(jni, key, identifier_field);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    native_name = (jstring)(*jni)->GetObjectField(jni, key, native_name_field);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    jboolean can_get = (*jni)->GetBooleanField(jni, key, get_field);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    jboolean can_set = (*jni)->GetBooleanField(jni, key, set_field);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    jboolean can_listen = (*jni)->GetBooleanField(jni, key, listen_field);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    jboolean can_action = (*jni)->GetBooleanField(jni, key, action_field);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    jboolean is_event = (*jni)->GetBooleanField(jni, key, event_field);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    if (component != 4 || subcomponent != 65534 || can_get != JNI_TRUE ||
        can_set != JNI_FALSE || can_listen != JNI_TRUE || can_action != JNI_FALSE ||
        is_event != JNI_FALSE || !exact_string(jni, identifier, "RidWorkingStatusPush") ||
        !exact_string(jni, native_name, "RidWorkingStatusPush")) goto done;
    stage = 7;
    if (!native_owner_open(&guard)) goto done;
    stage = 8;
    jvalue arguments[6];
    arguments[0].i = 0; arguments[1].i = component; arguments[2].i = 0;
    arguments[3].i = subcomponent; arguments[4].i = 65534; arguments[5].l = native_name;
    query_count = 1;
    bytes = (jbyteArray)(*jni)->CallStaticObjectMethodA(jni, selected[0], method, arguments);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    if (!native_owner_same(&guard)) { stage = 10; goto done; }
    if (bytes == NULL) { parse_rc = 1; stage = 0; goto done; }
    stage = 9;
    jsize size = (*jni)->GetArrayLength(jni, bytes);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    if (size < 16 || size > VALUE_LIMIT) { parse_rc = 2; goto done; }
    unsigned char header[8], tail[8];
    (*jni)->GetByteArrayRegion(jni, bytes, 0, 8, (jbyte *)header);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    (*jni)->GetByteArrayRegion(jni, bytes, size - 8, 8, (jbyte *)tail);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    parse_rc = decode_value(header, tail, (size_t)size, &value);
    if (parse_rc != 0) goto done;
    value_present = 1;
    stage = 0;

done:
    native_owner_close(&guard);
    if (jni != NULL && *jni != NULL) {
        exception |= clear_exception(jni);
        if (bytes != NULL) (*jni)->DeleteLocalRef(jni, bytes);
        if (native_name != NULL) (*jni)->DeleteLocalRef(jni, native_name);
        if (identifier != NULL) (*jni)->DeleteLocalRef(jni, identifier);
        if (key != NULL) (*jni)->DeleteLocalRef(jni, key);
        if (loader != NULL) (*jni)->DeleteLocalRef(jni, loader);
        if (classes != NULL && count > 0) {
            for (jint i = 0; i < count; ++i) (*jni)->DeleteLocalRef(jni, classes[i]);
        }
    }
    if (ti != NULL) {
        release(ti, classes);
        dispose_attempted = 1;
        dispose_rc = (*ti)->DisposeEnvironment(ti);
        ti = NULL;
        if (dispose_rc != JVMTI_ERROR_NONE && stage == 0) stage = 13;
    }
    if (exception && stage == 0) stage = 14;
    if (stage != 0) {
        value_present = 0;
        value = (struct rid_value){-1, -1, -1, -1, 0};
    }
    int ready = stage == 0 && !exception && jni_rc == JNI_OK && env_rc == JNI_OK &&
                dispose_attempted && dispose_rc == JVMTI_ERROR_NONE;
    __android_log_print(ANDROID_LOG_INFO, RID_TAG,
        "schema=" RID_SCHEMA " phase=result sid=%s pid=%ld uid=%lu gid=%lu abi_bits=%u"
        " ready=%d stage=%d exception=%d query_count=%d value_present=%d"
        " rid_support=%d rid_normal=%d eid_support=%d eid_normal=%d fail_reason=%u"
        " jni_rc=%d env_rc=%d parse_rc=%d dispose_attempted=%d dispose_rc=%d",
        sid, (long)pid, (unsigned long)uid, (unsigned long)gid, (unsigned int)(sizeof(void *) * 8),
        ready, stage, exception, query_count, value_present,
        value.rid_support, value.rid_normal, value.eid_support, value.eid_normal, value.fail_reason,
        (int)jni_rc, (int)env_rc, parse_rc, dispose_attempted, (int)dispose_rc);
    return JNI_OK;
}
