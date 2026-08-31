#include "mediastore_sink.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int exception(JNIEnv *jni) {
    if (!(*jni)->ExceptionCheck(jni)) return 0;
    (*jni)->ExceptionClear(jni);
    return 1;
}

static int sid_ok(const char *sid) {
    if (sid == NULL) return 0;
    for (unsigned i = 0; i < 16; ++i)
        if (!((sid[i] >= '0' && sid[i] <= '9') || (sid[i] >= 'a' && sid[i] <= 'f'))) return 0;
    return sid[16] == 0;
}

static int ascii(JNIEnv *jni, jstring value, char *out, size_t capacity) {
    if (value == NULL || capacity > 320u) return 0;
    jsize count = (*jni)->GetStringLength(jni, value);
    if ((*jni)->ExceptionCheck(jni) || count < 0 || (size_t)count >= capacity) return 0;
    jchar chars[320];
    (*jni)->GetStringRegion(jni, value, 0, count, chars);
    if ((*jni)->ExceptionCheck(jni)) return 0;
    for (jsize i = 0; i < count; ++i) {
        if (chars[i] == 0 || chars[i] > 127) return 0;
        out[i] = (char)chars[i];
    }
    out[count] = 0;
    return 1;
}

static int name_ok(const char *name) {
    if (name[0] == 0 || strcmp(name, "external") == 0 || strcmp(name, "external_primary") == 0) return 0;
    for (size_t i = 0; name[i]; ++i) {
        char c = name[i];
        if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || (i && (c == '-' || c == '_')))) return 0;
    }
    return 1;
}

static int child_uri(const char *collection, const char *inserted) {
    size_t length = strlen(collection);
    if (strncmp(collection, inserted, length) != 0 || inserted[length] != '/') return 0;
    const char *id = inserted + length + 1;
    if (*id < '1' || *id > '9') return 0;
    uint64_t number = 0;
    for (; *id; ++id) {
        if (*id < '0' || *id > '9') return 0;
        unsigned digit = (unsigned)(*id - '0');
        if (number > ((uint64_t)INT64_MAX - digit) / 10u) return 0;
        number = number * 10u + digit;
    }
    return number != 0;
}

struct api {
    jclass context, manager, volume, list, set, media, downloads;
    jclass values, integer, resolver, stream, uri;
    jmethodID service, content_resolver, volumes, list_size, list_get;
    jmethodID removable, primary, emulated, state, volume_name, contains, external_names;
    jmethodID content_uri, values_init, put_string, put_integer, integer_value;
    jmethodID insert, open, write, flush, close, update, remove, to_string;
};

static int load_api(JNIEnv *jni, struct api *a) {
#define CLASS(member, name) do { a->member = (*jni)->FindClass(jni, name); if (!a->member || (*jni)->ExceptionCheck(jni)) return 0; } while (0)
#define METHOD(member, cls, name, sig) do { a->member = (*jni)->GetMethodID(jni, a->cls, name, sig); if (!a->member || (*jni)->ExceptionCheck(jni)) return 0; } while (0)
#define STATIC(member, cls, name, sig) do { a->member = (*jni)->GetStaticMethodID(jni, a->cls, name, sig); if (!a->member || (*jni)->ExceptionCheck(jni)) return 0; } while (0)
    CLASS(context, "android/content/Context");
    CLASS(manager, "android/os/storage/StorageManager");
    CLASS(volume, "android/os/storage/StorageVolume");
    CLASS(list, "java/util/List"); CLASS(set, "java/util/Set");
    CLASS(media, "android/provider/MediaStore"); CLASS(downloads, "android/provider/MediaStore$Downloads");
    CLASS(values, "android/content/ContentValues"); CLASS(integer, "java/lang/Integer");
    CLASS(resolver, "android/content/ContentResolver"); CLASS(stream, "java/io/OutputStream");
    CLASS(uri, "android/net/Uri");
    METHOD(service, context, "getSystemService", "(Ljava/lang/String;)Ljava/lang/Object;");
    METHOD(content_resolver, context, "getContentResolver", "()Landroid/content/ContentResolver;");
    METHOD(volumes, manager, "getStorageVolumes", "()Ljava/util/List;");
    METHOD(list_size, list, "size", "()I");
    METHOD(list_get, list, "get", "(I)Ljava/lang/Object;");
    METHOD(removable, volume, "isRemovable", "()Z");
    METHOD(primary, volume, "isPrimary", "()Z");
    METHOD(emulated, volume, "isEmulated", "()Z");
    METHOD(state, volume, "getState", "()Ljava/lang/String;");
    METHOD(volume_name, volume, "getMediaStoreVolumeName", "()Ljava/lang/String;");
    METHOD(contains, set, "contains", "(Ljava/lang/Object;)Z");
    STATIC(external_names, media, "getExternalVolumeNames", "(Landroid/content/Context;)Ljava/util/Set;");
    STATIC(content_uri, downloads, "getContentUri", "(Ljava/lang/String;)Landroid/net/Uri;");
    METHOD(values_init, values, "<init>", "()V");
    METHOD(put_string, values, "put", "(Ljava/lang/String;Ljava/lang/String;)V");
    METHOD(put_integer, values, "put", "(Ljava/lang/String;Ljava/lang/Integer;)V");
    STATIC(integer_value, integer, "valueOf", "(I)Ljava/lang/Integer;");
    METHOD(insert, resolver, "insert", "(Landroid/net/Uri;Landroid/content/ContentValues;)Landroid/net/Uri;");
    METHOD(open, resolver, "openOutputStream", "(Landroid/net/Uri;Ljava/lang/String;)Ljava/io/OutputStream;");
    METHOD(write, stream, "write", "([B)V");
    METHOD(flush, stream, "flush", "()V"); METHOD(close, stream, "close", "()V");
    METHOD(update, resolver, "update", "(Landroid/net/Uri;Landroid/content/ContentValues;Ljava/lang/String;[Ljava/lang/String;)I");
    METHOD(remove, resolver, "delete", "(Landroid/net/Uri;Ljava/lang/String;[Ljava/lang/String;)I");
    METHOD(to_string, uri, "toString", "()Ljava/lang/String;");
#undef CLASS
#undef METHOD
#undef STATIC
    return 1;
}

static int put_text(JNIEnv *jni, const struct api *a, jobject values,
                    const char *key, const char *text) {
    jvalue args[2];
    args[0].l = (*jni)->NewStringUTF(jni, key);
    if (!args[0].l || (*jni)->ExceptionCheck(jni)) return 0;
    args[1].l = (*jni)->NewStringUTF(jni, text);
    if (!args[1].l || (*jni)->ExceptionCheck(jni)) return 0;
    (*jni)->CallVoidMethodA(jni, values, a->put_string, args);
    (*jni)->DeleteLocalRef(jni, args[0].l); (*jni)->DeleteLocalRef(jni, args[1].l);
    return !(*jni)->ExceptionCheck(jni);
}

static int put_pending(JNIEnv *jni, const struct api *a, jobject values, int pending) {
    jvalue value = {.i = pending};
    jobject integer = (*jni)->CallStaticObjectMethodA(jni, a->integer, a->integer_value, &value);
    if (!integer || (*jni)->ExceptionCheck(jni)) return 0;
    jvalue args[2]; args[1].l = integer;
    args[0].l = (*jni)->NewStringUTF(jni, "is_pending");
    if (!args[0].l || (*jni)->ExceptionCheck(jni)) return 0;
    (*jni)->CallVoidMethodA(jni, values, a->put_integer, args);
    (*jni)->DeleteLocalRef(jni, args[0].l); (*jni)->DeleteLocalRef(jni, integer);
    return !(*jni)->ExceptionCheck(jni);
}

int mediastore_sink_write(JNIEnv *jni, jobject application_context,
                          const char *sid, const unsigned char *json_utf8,
                          size_t bytes, struct mediastore_sink_result *out) {
    if (out == NULL) return MEDIASTORE_SINK_INVALID_ARGUMENT;
    *out = (struct mediastore_sink_result){0};
    out->code = MEDIASTORE_SINK_INVALID_ARGUMENT;
    if (jni == NULL || *jni == NULL || application_context == NULL || !sid_ok(sid) || json_utf8 == NULL || bytes == 0) return out->code;
    if (bytes > MEDIASTORE_SINK_MAX_BYTES) return out->code = MEDIASTORE_SINK_TOO_LARGE;
    if ((*jni)->ExceptionCheck(jni)) return out->code = MEDIASTORE_SINK_ENTRY_EXCEPTION;
    if ((*jni)->PushLocalFrame(jni, 64) != JNI_OK) {
        exception(jni);
        return out->code = MEDIASTORE_SINK_API_UNAVAILABLE;
    }
    struct api a = {0};
    jobject resolver = NULL, inserted = NULL, stream = NULL;
    int owned = 0, stream_closed = 0, published = 0;
    int code = MEDIASTORE_SINK_API_UNAVAILABLE;
    if (!load_api(jni, &a)) goto done;
    code = MEDIASTORE_SINK_VOLUME_DISCOVERY_FAILED;
    jvalue arg = {.l = (*jni)->NewStringUTF(jni, "storage")};
    if (!arg.l || (*jni)->ExceptionCheck(jni)) goto done;
    jobject manager = (*jni)->CallObjectMethodA(jni, application_context, a.service, &arg);
    if (!manager || (*jni)->ExceptionCheck(jni)) goto done;
    jobject volumes = (*jni)->CallObjectMethodA(jni, manager, a.volumes, NULL);
    if (!volumes || (*jni)->ExceptionCheck(jni)) goto done;
    jint count = (*jni)->CallIntMethodA(jni, volumes, a.list_size, NULL);
    if ((*jni)->ExceptionCheck(jni) || count < 0 || count > 64) goto done;
    int candidates = 0;
    jstring volume_name = NULL;
    for (jint i = 0; i < count; ++i) {
        jvalue index = {.i = i};
        jobject volume = (*jni)->CallObjectMethodA(jni, volumes, a.list_get, &index);
        if (!volume || (*jni)->ExceptionCheck(jni)) goto done;
        jboolean removable = (*jni)->CallBooleanMethodA(jni, volume, a.removable, NULL);
        if ((*jni)->ExceptionCheck(jni)) goto done;
        jboolean primary = (*jni)->CallBooleanMethodA(jni, volume, a.primary, NULL);
        if ((*jni)->ExceptionCheck(jni)) goto done;
        jboolean emulated = (*jni)->CallBooleanMethodA(jni, volume, a.emulated, NULL);
        if ((*jni)->ExceptionCheck(jni)) goto done;
        jstring state = (jstring)(*jni)->CallObjectMethodA(jni, volume, a.state, NULL);
        if ((*jni)->ExceptionCheck(jni)) goto done;
        char state_text[32];
        int mounted = ascii(jni, state, state_text, sizeof(state_text)) && strcmp(state_text, "mounted") == 0;
        if ((*jni)->ExceptionCheck(jni)) goto done;
        if (removable && !primary && !emulated && mounted) {
            if (++candidates > 1) { code = MEDIASTORE_SINK_MULTIPLE_VOLUMES; goto done; }
            volume_name = (jstring)(*jni)->CallObjectMethodA(jni, volume, a.volume_name, NULL);
            if ((*jni)->ExceptionCheck(jni)) goto done;
        }
        if (state) (*jni)->DeleteLocalRef(jni, state);
        (*jni)->DeleteLocalRef(jni, volume);
    }
    if (candidates == 0) { code = MEDIASTORE_SINK_NO_VOLUME; goto done; }
    code = MEDIASTORE_SINK_VOLUME_UNAVAILABLE;
    char selected_name[129];
    if (!ascii(jni, volume_name, selected_name, sizeof(selected_name)) || !name_ok(selected_name)) goto done;
    arg.l = application_context;
    jobject names = (*jni)->CallStaticObjectMethodA(jni, a.media, a.external_names, &arg);
    if (!names || (*jni)->ExceptionCheck(jni)) goto done;
    arg.l = volume_name;
    jboolean available = (*jni)->CallBooleanMethodA(jni, names, a.contains, &arg);
    if ((*jni)->ExceptionCheck(jni) || !available) goto done;
    jobject collection = (*jni)->CallStaticObjectMethodA(jni, a.downloads, a.content_uri, &arg);
    if (!collection || (*jni)->ExceptionCheck(jni)) goto done;
    jstring collection_string = (jstring)(*jni)->CallObjectMethodA(jni, collection, a.to_string, NULL);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    char collection_text[256], expected_collection[256];
    snprintf(expected_collection, sizeof(expected_collection), "content://media/%s/downloads", selected_name);
    if (!ascii(jni, collection_string, collection_text, sizeof(collection_text)) || strcmp(collection_text, expected_collection) != 0) goto done;
    code = MEDIASTORE_SINK_PREPARE_FAILED;
    resolver = (*jni)->CallObjectMethodA(jni, application_context, a.content_resolver, NULL);
    if (!resolver || (*jni)->ExceptionCheck(jni)) goto done;
    jobject pending = (*jni)->NewObjectA(jni, a.values, a.values_init, NULL);
    if (!pending || (*jni)->ExceptionCheck(jni)) goto done;
    jobject final_values = (*jni)->NewObjectA(jni, a.values, a.values_init, NULL);
    if (!final_values || (*jni)->ExceptionCheck(jni)) goto done;
    char display_name[64];
    snprintf(display_name, sizeof(display_name), "FindUAS_A060_policyset_%s.json", sid);
    if (!put_text(jni, &a, pending, "_display_name", display_name) ||
        !put_text(jni, &a, pending, "mime_type", "application/json") ||
        !put_text(jni, &a, pending, "relative_path", "Download/FindUAS/Probe/") ||
        !put_pending(jni, &a, pending, 1) || !put_pending(jni, &a, final_values, 0)) goto done;
    jbyteArray content = (*jni)->NewByteArray(jni, (jsize)bytes);
    if (!content || (*jni)->ExceptionCheck(jni)) goto done;
    (*jni)->SetByteArrayRegion(jni, content, 0, (jsize)bytes, (const jbyte *)json_utf8);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    jstring write_mode = (*jni)->NewStringUTF(jni, "w");
    if (!write_mode || (*jni)->ExceptionCheck(jni)) goto done;
    code = MEDIASTORE_SINK_INSERT_FAILED;
    jvalue insert_args[2] = {{.l = collection}, {.l = pending}};
    ++out->insert_count;
    inserted = (*jni)->CallObjectMethodA(jni, resolver, a.insert, insert_args);
    if (!inserted || (*jni)->ExceptionCheck(jni)) goto done;
    code = MEDIASTORE_SINK_URI_INVALID;
    jstring inserted_string = (jstring)(*jni)->CallObjectMethodA(jni, inserted, a.to_string, NULL);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    char inserted_text[288];
    if (!ascii(jni, inserted_string, inserted_text, sizeof(inserted_text)) || !child_uri(collection_text, inserted_text)) goto done;
    owned = 1;
    code = MEDIASTORE_SINK_OPEN_FAILED;
    jvalue open_args[2] = {{.l = inserted}, {.l = write_mode}};
    stream = (*jni)->CallObjectMethodA(jni, resolver, a.open, open_args);
    if (!stream || (*jni)->ExceptionCheck(jni)) goto done;
    code = MEDIASTORE_SINK_WRITE_FAILED;
    arg.l = content;
    ++out->write_count;
    (*jni)->CallVoidMethodA(jni, stream, a.write, &arg);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    code = MEDIASTORE_SINK_FLUSH_FAILED;
    (*jni)->CallVoidMethodA(jni, stream, a.flush, NULL);
    if ((*jni)->ExceptionCheck(jni)) goto done;
    code = MEDIASTORE_SINK_CLOSE_FAILED;
    ++out->close_count; stream_closed = 1;
    (*jni)->CallVoidMethodA(jni, stream, a.close, NULL);
    if ((*jni)->ExceptionCheck(jni)) { out->close_failed = 1; goto done; }
    code = MEDIASTORE_SINK_PUBLISH_FAILED;
    jvalue update_args[4] = {{.l = inserted}, {.l = final_values}, {.l = NULL}, {.l = NULL}};
    ++out->publish_count;
    jint updated = (*jni)->CallIntMethodA(jni, resolver, a.update, update_args);
    if ((*jni)->ExceptionCheck(jni) || updated != 1) goto done;
    published = 1; code = MEDIASTORE_SINK_SAVED; out->saved_bytes = bytes;

done:
    exception(jni);
    if (stream != NULL && !stream_closed) {
        ++out->close_count;
        (*jni)->CallVoidMethodA(jni, stream, a.close, NULL);
        if (exception(jni)) out->close_failed = 1;
    }
    if (!published && inserted != NULL) {
        if (owned) {
            jvalue remove_args[3] = {{.l = inserted}, {.l = NULL}, {.l = NULL}};
            ++out->delete_count;
            jint removed = (*jni)->CallIntMethodA(jni, resolver, a.remove, remove_args);
            out->cleanup_status = !exception(jni) && removed == 1 ? MEDIASTORE_SINK_CLEANUP_REMOVED : MEDIASTORE_SINK_CLEANUP_FAILED;
        } else out->cleanup_status = MEDIASTORE_SINK_CLEANUP_UNVERIFIED_URI;
    }
    (*jni)->PopLocalFrame(jni, NULL);
    out->code = code;
    return code;
}
