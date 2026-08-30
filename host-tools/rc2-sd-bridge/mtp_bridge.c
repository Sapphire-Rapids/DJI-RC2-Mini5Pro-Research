#define _POSIX_C_SOURCE 200809L
#define _DARWIN_C_SOURCE 1
#include <libmtp.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#define PUT_LIMIT 32768u
#define GET_LIMIT 131072u
#define PATH_LIMIT 511u
#define PART_LIMIT 127u
#define PART_COUNT 8u
#define CAN_MKDIR 1u
#define CAN_GET 2u
#define CAN_PUT 4u

enum { RESULT_OK = 0, RESULT_USAGE = 2, RESULT_MISSING = 3, RESULT_ERROR = 4 };
enum { LOOKUP_ERROR = -1, LOOKUP_MISSING = 0, LOOKUP_FOUND = 1 };
struct path { char text[PATH_LIMIT + 1]; char *part[PART_COUNT]; size_t count; };
struct object { uint32_t id, parent; uint64_t size; time_t modified; int directory; };
struct device { LIBMTP_mtpdevice_t *mtp; uint32_t storage; };
struct bytes { unsigned char *data; size_t size, position, capacity; };
static const char *failure = "UNSPECIFIED";

static int error(const char *code) { failure = code; return RESULT_ERROR; }

static int hex_sid(const char *value) {
    if (strlen(value) != 16) return 0;
    for (size_t i = 0; i < 16; ++i)
        if (!((value[i] >= '0' && value[i] <= '9') ||
              (value[i] >= 'a' && value[i] <= 'f'))) return 0;
    return 1;
}

static int split_path(const char *value, struct path *path) {
    size_t length = strlen(value);
    memset(path, 0, sizeof(*path));
    if (!length || length > PATH_LIMIT || value[0] == '/' || value[length - 1] == '/') return 0;
    for (size_t i = 0; i < length; ++i) {
        unsigned char c = (unsigned char)value[i];
        if (!((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
              (c >= '0' && c <= '9') || c == '/' || c == '.' || c == '_' || c == '-')) return 0;
    }
    memcpy(path->text, value, length + 1);
    char *part = path->text;
    for (;;) {
        if (path->count == PART_COUNT) return 0;
        char *slash = strchr(part, '/');
        if (slash) *slash = '\0';
        size_t n = strlen(part);
        if (!n || n > PART_LIMIT || !strcmp(part, ".") || !strcmp(part, "..")) return 0;
        path->part[path->count++] = part;
        if (!slash) return 1;
        part = slash + 1;
    }
}

static int sequence_file(const char *name, const char *extension) {
    if (strlen(name) != 4 + strlen(extension)) return 0;
    for (size_t i = 0; i < 4; ++i) if (name[i] < '0' || name[i] > '9') return 0;
    return !strcmp(name + 4, extension);
}

static unsigned allowed_path(const struct path *p) {
    if (!p->count || strcmp(p->part[0], "Download")) return 0;
    if (p->count == 1) return CAN_MKDIR;
    if (p->count == 2 && (!strcmp(p->part[1], "B1.sh") || !strcmp(p->part[1], "F4.sh") ||
                         !strcmp(p->part[1], "B2.sh") || !strcmp(p->part[1], "L1.sh") ||
                         !strcmp(p->part[1], "FindUAS_ARTTI_V2.so") ||
                         !strcmp(p->part[1], "B3.sh") || !strcmp(p->part[1], "L2.sh") ||
                         !strcmp(p->part[1], "FindUAS_RID_CACHE.so") ||
                         !strcmp(p->part[1], "B4.sh") || !strcmp(p->part[1], "L3.sh") ||
                         !strcmp(p->part[1], "FindUAS_CLOUD_POLICY.so")))
        return CAN_GET | CAN_PUT;
    if (strcmp(p->part[1], "FindUAS")) return 0;
    if (p->count == 2) return CAN_MKDIR;
    if (!strcmp(p->part[2], "Probe")) {
        if (p->count == 3) return CAN_MKDIR;
        if (p->count != 4) return 0;
        const char *name = p->part[3], *prefix = "FindUAS_F4_";
        if (!strcmp(name, "A048_copy.receipt") || !strcmp(name, "A048_attach.attempted")) return CAN_GET;
        if (!strcmp(name, "A051_copy.receipt") || !strcmp(name, "A051_attach.attempted")) return CAN_GET;
        if (!strcmp(name, "A054_copy.receipt") || !strcmp(name, "A054_attach.attempted")) return CAN_GET;
        size_t n = strlen(name), prefix_length = strlen(prefix);
        return n > prefix_length + 4 && !strncmp(name, prefix, prefix_length) &&
            !strcmp(name + n - 4, ".txt") ? CAN_GET : 0;
    }
    if (strcmp(p->part[2], "Bridge")) return 0;
    if (p->count == 3) return CAN_MKDIR;
    if (p->count == 4 && !strcmp(p->part[3], "active.session")) return CAN_GET | CAN_PUT;
    if (!hex_sid(p->part[3])) return 0;
    if (p->count == 4) return CAN_MKDIR;
    if (p->count == 5) {
        if (!strcmp(p->part[4], "inbox") || !strcmp(p->part[4], "outbox")) return CAN_MKDIR;
        const char *files[] = { "active.session", "worker.lock", "worker.log", "session.ready", "session.closed", "session.receiver" };
        for (size_t i = 0; i < sizeof(files) / sizeof(files[0]); ++i)
            if (!strcmp(p->part[4], files[i])) return CAN_GET;
        return 0;
    }
    if (p->count != 6) return 0;
    if (!strcmp(p->part[4], "inbox") &&
        (sequence_file(p->part[5], ".job") || sequence_file(p->part[5], ".ready")))
        return CAN_GET | CAN_PUT;
    if (!strcmp(p->part[4], "outbox") &&
        (sequence_file(p->part[5], ".accepted") || sequence_file(p->part[5], ".report") ||
         sequence_file(p->part[5], ".done"))) return CAN_GET;
    return 0;
}

static int same_parent(uint32_t actual, uint32_t expected) {
    return actual == expected || (expected == 0 && actual == LIBMTP_FILES_AND_FOLDERS_ROOT);
}

static int ascii_name_equal(const char *a, const char *b) {
    while (*a && *b) {
        unsigned char x = (unsigned char)*a++, y = (unsigned char)*b++;
        if (x >= 'A' && x <= 'Z') x = (unsigned char)(x + ('a' - 'A'));
        if (y >= 'A' && y <= 'Z') y = (unsigned char)(y + ('a' - 'A'));
        if (x != y) return 0;
    }
    return *a == *b;
}

static int select_child(LIBMTP_file_t *files, uint32_t storage, uint32_t parent,
                        const char *name, struct object *out) {
    unsigned matches = 0;
    for (LIBMTP_file_t *f = files; f; f = f->next) {
        if (f->storage_id != storage || !same_parent(f->parent_id, parent) ||
            !f->filename || !ascii_name_equal(f->filename, name)) continue;
        /* The SD filesystem may fold case. Never create through an existing alias. */
        if (strcmp(f->filename, name)) return LOOKUP_ERROR;
        if (++matches != 1 || !f->item_id || f->item_id == LIBMTP_FILES_AND_FOLDERS_ROOT)
            return LOOKUP_ERROR;
        *out = (struct object){ f->item_id, parent, f->filesize, f->modificationdate,
                              f->filetype == LIBMTP_FILETYPE_FOLDER };
    }
    return matches ? LOOKUP_FOUND : LOOKUP_MISSING;
}

static void free_files(LIBMTP_file_t *files) {
    while (files) { LIBMTP_file_t *next = files->next; LIBMTP_destroy_file_t(files); files = next; }
}

static int lookup(struct device *d, uint32_t parent, const char *name, struct object *out) {
    LIBMTP_Clear_Errorstack(d->mtp);
    LIBMTP_file_t *files = LIBMTP_Get_Files_And_Folders(d->mtp, d->storage,
        parent ? parent : LIBMTP_FILES_AND_FOLDERS_ROOT);
    int result = LIBMTP_Get_Errorstack(d->mtp) ? LOOKUP_ERROR :
        select_child(files, d->storage, parent, name, out);
    free_files(files);
    if (result == LOOKUP_ERROR) failure = "DIRECTORY_LOOKUP_FAILED_OR_DUPLICATE";
    return result;
}

static int open_device(struct device *d) {
    LIBMTP_raw_device_t *raw = NULL;
    int count = 0, matches = 0, selected = -1;
    LIBMTP_Init();
    LIBMTP_Set_Debug(0);
    LIBMTP_error_number_t detected = LIBMTP_Detect_Raw_Devices(&raw, &count);
    if (detected != LIBMTP_ERROR_NONE) { free(raw); return error("DEVICE_DETECTION_FAILED"); }
    for (int i = 0; i < count; ++i) {
        if (raw[i].device_entry.vendor_id == 0x2ca3 && raw[i].device_entry.product_id == 0x1021) {
            selected = i;
            ++matches;
        }
    }
    if (matches != 1) { free(raw); return error("RC2_NOT_UNIQUE"); }
    d->mtp = LIBMTP_Open_Raw_Device_Uncached(&raw[selected]);
    free(raw);
    if (!d->mtp) return error("RC2_OPEN_FAILED");
    if (LIBMTP_Get_Storage(d->mtp, LIBMTP_STORAGE_SORTBY_NOTSORTED) != 0)
        return error("STORAGE_QUERY_FAILED");
    matches = 0;
    for (LIBMTP_devicestorage_t *s = d->mtp->storage; s; s = s->next) {
        if (s->StorageType == 0x0004) { d->storage = s->id; ++matches; }
    }
    if (matches != 1 || !d->storage || d->storage == LIBMTP_FILES_AND_FOLDERS_ROOT)
        return error("REMOVABLE_STORAGE_NOT_UNIQUE");
    return RESULT_OK;
}

static int directory(struct device *d, const struct path *p, size_t count, int create, uint32_t *parent) {
    *parent = 0;
    for (size_t i = 0; i < count; ++i) {
        struct object found;
        int state = lookup(d, *parent, p->part[i], &found);
        if (state == LOOKUP_ERROR) return RESULT_ERROR;
        if (state == LOOKUP_MISSING) {
            if (!create) return RESULT_MISSING;
            char name[PART_LIMIT + 1];
            strcpy(name, p->part[i]);
            uint32_t id = LIBMTP_Create_Folder(d->mtp, name, *parent, d->storage);
            if (!id || strcmp(name, p->part[i])) return error("DIRECTORY_CREATE_FAILED");
            if (lookup(d, *parent, p->part[i], &found) != LOOKUP_FOUND || found.id != id)
                return error("DIRECTORY_CREATE_READBACK_FAILED");
        }
        if (!found.directory) return error("PATH_COMPONENT_IS_NOT_DIRECTORY");
        *parent = found.id;
    }
    return RESULT_OK;
}

static uint16_t receive_bytes(void *params, void *opaque, uint32_t length,
                              unsigned char *data, uint32_t *received) {
    (void)params;
    struct bytes *b = opaque;
    *received = 0;
    if (b->position > b->capacity || length > b->capacity - b->position)
        return LIBMTP_HANDLER_RETURN_CANCEL;
    if (length) memcpy(b->data + b->position, data, length);
    b->position += length;
    *received = length;
    return LIBMTP_HANDLER_RETURN_OK;
}

static uint16_t supply_bytes(void *params, void *opaque, uint32_t wanted,
                             unsigned char *data, uint32_t *supplied) {
    (void)params;
    struct bytes *b = opaque;
    *supplied = 0;
    if (b->position > b->size) return LIBMTP_HANDLER_RETURN_ERROR;
    size_t n = b->size - b->position;
    if (n > wanted) n = wanted;
    if (n) memcpy(data, b->data + b->position, n);
    b->position += n;
    *supplied = (uint32_t)n;
    return LIBMTP_HANDLER_RETURN_OK;
}

static int fetch(struct device *d, const struct object *object, const char *name,
                 size_t limit, struct bytes *out) {
    if (object->directory || object->size > limit) return error("REMOTE_FILE_TYPE_OR_SIZE");
    out->data = malloc(object->size ? (size_t)object->size : 1);
    if (!out->data) return error("ALLOCATION_FAILED");
    out->capacity = out->size = (size_t)object->size;
    out->position = 0;
    /* The handler counts payload only. Do not compare libmtp's transport progress
       (which includes PTP overhead) with the advertised file length. */
    if (LIBMTP_Get_File_To_Handler(d->mtp, object->id, receive_bytes, out, NULL, NULL) != 0 ||
        out->position != out->size) return error("REMOTE_READ_INCOMPLETE");
    struct object after;
    if (lookup(d, object->parent, name, &after) != LOOKUP_FOUND || after.directory ||
        after.id != object->id || after.size != object->size || after.modified != object->modified)
        return error("REMOTE_FILE_CHANGED_DURING_READ");
    return RESULT_OK;
}

static int same_stat(const struct stat *a, const struct stat *b) {
    if (a->st_dev != b->st_dev || a->st_ino != b->st_ino || a->st_size != b->st_size) return 0;
#ifdef __APPLE__
    return a->st_mtimespec.tv_sec == b->st_mtimespec.tv_sec &&
           a->st_mtimespec.tv_nsec == b->st_mtimespec.tv_nsec &&
           a->st_ctimespec.tv_sec == b->st_ctimespec.tv_sec &&
           a->st_ctimespec.tv_nsec == b->st_ctimespec.tv_nsec;
#else
    return a->st_mtim.tv_sec == b->st_mtim.tv_sec && a->st_mtim.tv_nsec == b->st_mtim.tv_nsec &&
           a->st_ctim.tv_sec == b->st_ctim.tv_sec && a->st_ctim.tv_nsec == b->st_ctim.tv_nsec;
#endif
}

static int read_local(const char *name, struct bytes *out) {
    int fd = open(name, O_RDONLY | O_NOFOLLOW | O_NONBLOCK);
    if (fd < 0) return error("LOCAL_SOURCE_OPEN_FAILED");
    struct stat before, after;
    int result = RESULT_ERROR;
    if (fstat(fd, &before) || !S_ISREG(before.st_mode) || before.st_size < 0 ||
        (uint64_t)before.st_size > PUT_LIMIT) { failure = "LOCAL_SOURCE_TYPE_OR_SIZE"; goto done; }
    out->size = out->capacity = (size_t)before.st_size;
    out->data = malloc(out->size ? out->size : 1);
    if (!out->data) { failure = "ALLOCATION_FAILED"; goto done; }
    while (out->position < out->size) {
        ssize_t n = read(fd, out->data + out->position, out->size - out->position);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) { failure = "LOCAL_SOURCE_READ_FAILED"; goto done; }
        out->position += (size_t)n;
    }
    unsigned char extra;
    ssize_t tail;
    do { tail = read(fd, &extra, 1); } while (tail < 0 && errno == EINTR);
    if (tail != 0) { failure = "LOCAL_SOURCE_CHANGED_OR_READ_FAILED"; goto done; }
    if (fstat(fd, &after) || !same_stat(&before, &after)) {
        failure = "LOCAL_SOURCE_CHANGED"; goto done;
    }
    out->position = 0;
    result = RESULT_OK;
done:
    if (close(fd) && result == RESULT_OK) result = error("LOCAL_SOURCE_CLOSE_FAILED");
    return result;
}

static int write_local(const char *name, const struct bytes *data) {
    int fd = open(name, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
    if (fd < 0) return error("LOCAL_OUTPUT_CREATE_FAILED");
    size_t offset = 0;
    int result = RESULT_OK;
    while (offset < data->size) {
        ssize_t n = write(fd, data->data + offset, data->size - offset);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) { result = error("LOCAL_OUTPUT_WRITE_FAILED"); break; }
        offset += (size_t)n;
    }
    if (result == RESULT_OK && fsync(fd)) result = error("LOCAL_OUTPUT_SYNC_FAILED");
    if (close(fd) && result == RESULT_OK) result = error("LOCAL_OUTPUT_CLOSE_FAILED");
    return result;
}

static int put(struct device *d, const struct path *p, struct bytes *source, int *created) {
    uint32_t parent;
    int result = directory(d, p, p->count - 1, 0, &parent);
    if (result) return result == RESULT_MISSING ? error("REMOTE_PARENT_MISSING") : result;
    const char *name = p->part[p->count - 1];
    struct object object;
    int state = lookup(d, parent, name, &object);
    if (state == LOOKUP_ERROR) return RESULT_ERROR;
    if (state == LOOKUP_MISSING) {
        LIBMTP_file_t *file = LIBMTP_new_file_t();
        if (!file) return error("ALLOCATION_FAILED");
        file->filename = strdup(name);
        if (!file->filename) { LIBMTP_destroy_file_t(file); return error("ALLOCATION_FAILED"); }
        file->filesize = source->size;
        file->storage_id = d->storage;
        file->parent_id = parent;
        file->filetype = LIBMTP_FILETYPE_UNKNOWN;
        source->position = 0;
        int sent = LIBMTP_Send_File_From_Handler(d->mtp, supply_bytes, source, file, NULL, NULL);
        uint32_t id = file->item_id;
        int unchanged_name = file->filename && !strcmp(file->filename, name);
        LIBMTP_destroy_file_t(file);
        if (sent || source->position != source->size || !id || !unchanged_name)
            return error("UPLOAD_FAILED_OR_UNCERTAIN");
        *created = 1;
        if (lookup(d, parent, name, &object) != LOOKUP_FOUND || object.id != id)
            return error("UPLOAD_NAME_READBACK_FAILED");
    }
    if (object.directory || object.size != source->size) return error("REMOTE_CONTENT_CONFLICT");
    struct bytes returned = {0};
    result = fetch(d, &object, name, PUT_LIMIT, &returned);
    if (!result && memcmp(returned.data, source->data, source->size)) result = error("REMOTE_CONTENT_CONFLICT");
    free(returned.data);
    return result;
}

static int exact_text(const struct bytes *b, const char *text) {
    return b->size == strlen(text) && !memcmp(b->data, text, b->size);
}

static int closed_session(const struct bytes *b, const char *sid) {
    const char *reasons[] = { "STOP", "TTL", "LIMIT", "ERROR" };
    char text[80];
    for (size_t i = 0; i < sizeof(reasons) / sizeof(reasons[0]); ++i) {
        snprintf(text, sizeof(text), "B1 CLOSED %s %s END\n", sid, reasons[i]);
        if (exact_text(b, text)) return 1;
    }
    return 0;
}

static int archive_active(struct device *d, const char *sid) {
    struct path bridge, session;
    char session_path[100], expected[80];
    snprintf(session_path, sizeof(session_path), "Download/FindUAS/Bridge/%s", sid);
    snprintf(expected, sizeof(expected), "B1 SESSION %s END\n", sid);
    if (!split_path("Download/FindUAS/Bridge", &bridge) || !split_path(session_path, &session))
        return error("INVALID_SESSION_PATH");
    uint32_t parent, destination;
    if (directory(d, &bridge, bridge.count, 0, &parent) ||
        directory(d, &session, session.count, 0, &destination)) return error("SESSION_DIRECTORY_UNAVAILABLE");
    struct object active, closed, collision;
    if (lookup(d, parent, "active.session", &active) != LOOKUP_FOUND ||
        lookup(d, destination, "session.closed", &closed) != LOOKUP_FOUND)
        return error("SESSION_RECORD_UNAVAILABLE");
    if (lookup(d, destination, "active.session", &collision) != LOOKUP_MISSING)
        return error("ARCHIVE_DESTINATION_NOT_EMPTY");
    struct bytes active_data = {0}, closed_data = {0}, archived_data = {0};
    int result = fetch(d, &active, "active.session", PUT_LIMIT, &active_data);
    if (!result) result = fetch(d, &closed, "session.closed", GET_LIMIT, &closed_data);
    if (!result && (!exact_text(&active_data, expected) || !closed_session(&closed_data, sid)))
        result = error("SESSION_PROTOCOL_MISMATCH");
    if (!result && !LIBMTP_Check_Capability(d->mtp, LIBMTP_DEVICECAP_MoveObject))
        result = error("MOVE_UNSUPPORTED");
    if (!result && LIBMTP_Move_Object(d->mtp, active.id, d->storage, destination))
        result = error("ARCHIVE_MOVE_FAILED_OR_UNCERTAIN");
    if (!result) {
        if (lookup(d, parent, "active.session", &collision) != LOOKUP_MISSING ||
            lookup(d, destination, "active.session", &collision) != LOOKUP_FOUND || collision.id != active.id)
            result = error("ARCHIVE_MOVE_READBACK_FAILED");
        else result = fetch(d, &collision, "active.session", PUT_LIMIT, &archived_data);
    }
    if (!result && !exact_text(&archived_data, expected)) result = error("ARCHIVE_CONTENT_MISMATCH");
    free(active_data.data); free(closed_data.data); free(archived_data.data);
    return result;
}

#define CHECK(condition) do { if (!(condition)) { fprintf(stderr, "self-test failed at line %d\n", __LINE__); return 1; } } while (0)
static int self_test(void) {
    const struct { const char *name; unsigned allowed; } paths[] = {
        {"Download", CAN_MKDIR}, {"Download/B1.sh", CAN_GET | CAN_PUT},
        {"Download/F4.sh", CAN_GET | CAN_PUT}, {"Download/F1.sh", 0},
        {"Download/B2.sh", CAN_GET | CAN_PUT}, {"Download/L1.sh", CAN_GET | CAN_PUT},
        {"Download/FindUAS_ARTTI_V2.so", CAN_GET | CAN_PUT},
        {"Download/B3.sh", CAN_GET | CAN_PUT}, {"Download/L2.sh", CAN_GET | CAN_PUT},
        {"Download/FindUAS_RID_CACHE.so", CAN_GET | CAN_PUT},
        {"Download/B4.sh", CAN_GET | CAN_PUT}, {"Download/L3.sh", CAN_GET | CAN_PUT},
        {"Download/FindUAS_CLOUD_POLICY.so", CAN_GET | CAN_PUT},
        {"Download/FindUAS_ARTTI_V1.so", 0},
        {"Download/FindUAS/Bridge/active.session", CAN_GET | CAN_PUT},
        {"Download/FindUAS/Bridge/0123456789abcdef/inbox", CAN_MKDIR},
        {"Download/FindUAS/Bridge/0123456789abcdef/inbox/0001.job", CAN_GET | CAN_PUT},
        {"Download/FindUAS/Bridge/0123456789abcdef/inbox/0001.ready", CAN_GET | CAN_PUT},
        {"Download/FindUAS/Bridge/0123456789abcdef/outbox/0001.report", CAN_GET},
        {"Download/FindUAS/Bridge/0123456789abcdef/active.session", CAN_GET},
        {"Download/FindUAS/Bridge/0123456789abcdef/session.closed", CAN_GET},
        {"Download/FindUAS/Bridge/0123456789abcdef/session.receiver", CAN_GET},
        {"Download/FindUAS/Bridge/0123456789abcdef/inbox/1.job", 0},
        {"Download/FindUAS/Bridge/0123456789abcdef/outbox/0001.sh", 0},
        {"Download/FindUAS/Bridge/0123456789abcdeg/inbox", 0},
        {"Download/FindUAS/Probe/FindUAS_F4_TEST.txt", CAN_GET},
        {"Download/FindUAS/Probe/FindUAS_F3_TEST.txt", 0},
        {"Download/FindUAS/Probe/A048_copy.receipt", CAN_GET},
        {"Download/FindUAS/Probe/A051_copy.receipt", CAN_GET},
        {"Download/FindUAS/Probe/A051_attach.attempted", CAN_GET},
        {"Download/FindUAS/Probe/A054_copy.receipt", CAN_GET},
        {"Download/FindUAS/Probe/A054_attach.attempted", CAN_GET},
        {"Download/FindUAS/Probe/A048_attach.attempted", CAN_GET},
        {"Download/FindUAS/Probe/A048_copy.receipt.extra", 0},
        {"Download/FindUAS/Samples/TEST.zip", 0}, {"Download/user.txt", 0},
        {"/Download/B1.sh", 0}, {"Download//B1.sh", 0}, {"Download/./B1.sh", 0},
        {"Download/../B1.sh", 0}, {"Download\\B1.sh", 0}, {"Download/B1.sh/", 0},
        {"Download/B1.sh\n", 0}, {"", 0}
    };
    for (size_t i = 0; i < sizeof(paths) / sizeof(paths[0]); ++i) {
        struct path p;
        unsigned permitted = split_path(paths[i].name, &p) ? allowed_path(&p) : 0;
        CHECK(permitted == paths[i].allowed);
    }
    char long_path[PATH_LIMIT + 3]; memset(long_path, 'a', sizeof(long_path));
    long_path[sizeof(long_path) - 1] = 0;
    struct path p; CHECK(!split_path(long_path, &p));
    LIBMTP_file_t a = {0}, b = {0}; struct object selected;
    a.filename = b.filename = "B1.sh"; a.item_id = 10; b.item_id = 11;
    a.storage_id = b.storage_id = 7; a.parent_id = b.parent_id = 4;
    CHECK(select_child(&a, 7, 4, "B1.sh", &selected) == LOOKUP_FOUND && selected.id == 10);
    a.next = &b; CHECK(select_child(&a, 7, 4, "B1.sh", &selected) == LOOKUP_ERROR);
    b.storage_id = 8; CHECK(select_child(&a, 7, 4, "B1.sh", &selected) == LOOKUP_FOUND);
    a.parent_id = 5; CHECK(select_child(&a, 7, 4, "B1.sh", &selected) == LOOKUP_MISSING);
    a.parent_id = 4; a.filename = "b1.sh";
    CHECK(select_child(&a, 7, 4, "B1.sh", &selected) == LOOKUP_ERROR);
    unsigned char data[4] = {0}, input[4] = {1, 2, 3, 4}; uint32_t count = 0;
    struct bytes bytes = { data, 4, 0, 4 };
    CHECK(receive_bytes(NULL, &bytes, 3, input, &count) == LIBMTP_HANDLER_RETURN_OK && count == 3);
    CHECK(receive_bytes(NULL, &bytes, 2, input, &count) == LIBMTP_HANDLER_RETURN_CANCEL && !count && bytes.position == 3);
    CHECK(receive_bytes(NULL, &bytes, UINT32_MAX, input, &count) == LIBMTP_HANDLER_RETURN_CANCEL);
    bytes.position = 0;
    CHECK(supply_bytes(NULL, &bytes, 9, input, &count) == LIBMTP_HANDLER_RETURN_OK && count == 4);
    CHECK(supply_bytes(NULL, &bytes, 1, input, &count) == LIBMTP_HANDLER_RETURN_OK && !count);
    const char *sid = "0123456789abcdef";
    const char *valid = "B1 CLOSED 0123456789abcdef STOP END\n";
    struct bytes text = { (unsigned char *)valid, strlen(valid), 0, 0 };
    CHECK(closed_session(&text, sid));
    CHECK(!closed_session(&text, "0123456789abcdee"));
    --text.size; CHECK(!closed_session(&text, sid));
    const char *reasons[] = { "STOP", "TTL", "LIMIT", "ERROR", "UNKNOWN" };
    char closed[100];
    for (size_t i = 0; i < sizeof(reasons) / sizeof(reasons[0]); ++i) {
        snprintf(closed, sizeof(closed), "B1 CLOSED %s %s END\n", sid, reasons[i]);
        text = (struct bytes){ (unsigned char *)closed, strlen(closed), 0, 0 };
        CHECK(closed_session(&text, sid) == (i < 4));
    }
    const char *trailing = "B1 CLOSED 0123456789abcdef STOP END\nEXTRA\n";
    text = (struct bytes){ (unsigned char *)trailing, strlen(trailing), 0, 0 };
    CHECK(!closed_session(&text, sid));
    puts("SELF_TEST_OK usb_initialized=false");
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 2 && !strcmp(argv[1], "--self-test")) return self_test();
    int is_mkdir = argc == 3 && !strcmp(argv[1], "mkdir");
    int is_put = argc == 4 && !strcmp(argv[1], "put");
    int is_get = argc == 4 && !strcmp(argv[1], "get");
    int is_archive = argc == 3 && !strcmp(argv[1], "archive-active");
    struct path path;
    unsigned required = is_mkdir ? CAN_MKDIR : is_put ? CAN_PUT : CAN_GET;
    if ((!is_mkdir && !is_put && !is_get && !is_archive) ||
        (is_archive ? !hex_sid(argv[2]) :
         (!split_path(argv[2], &path) || !(allowed_path(&path) & required)))) {
        fprintf(stderr, "usage: mtp_bridge mkdir DIR | put FILE SOURCE | get FILE NEW_OUTPUT | archive-active SID\n");
        return RESULT_USAGE;
    }
    struct bytes source = {0}, received = {0};
    if (is_put && read_local(argv[3], &source)) {
        fprintf(stderr, "ERROR code=%s\n", failure); free(source.data); return RESULT_ERROR;
    }
    if (is_get) {
        struct stat existing;
        if (!lstat(argv[3], &existing) || errno != ENOENT) {
            fprintf(stderr, "ERROR code=LOCAL_OUTPUT_MUST_BE_NEW\n"); return RESULT_ERROR;
        }
    }
    /* libmtp may print device diagnostics on stdout. Keep the machine result on a
       separate descriptor; the caller must retain stderr only in private logs. */
    int result_fd = dup(STDOUT_FILENO);
    if (result_fd < 0 || dup2(STDERR_FILENO, STDOUT_FILENO) < 0) {
        if (result_fd >= 0) close(result_fd);
        free(source.data); return RESULT_ERROR;
    }
    struct device device = {0};
    int created = 0, result = open_device(&device);
    if (!result && is_mkdir) {
        uint32_t unused;
        result = directory(&device, &path, path.count, 1, &unused);
    } else if (!result && is_put) result = put(&device, &path, &source, &created);
    else if (!result && is_get) {
        uint32_t parent;
        result = directory(&device, &path, path.count - 1, 0, &parent);
        if (!result) {
            struct object object;
            int found = lookup(&device, parent, path.part[path.count - 1], &object);
            if (found == LOOKUP_MISSING) result = RESULT_MISSING;
            else if (found == LOOKUP_ERROR) result = RESULT_ERROR;
            else result = fetch(&device, &object, path.part[path.count - 1], GET_LIMIT, &received);
        }
        if (!result) result = write_local(argv[3], &received);
    } else if (!result && is_archive) result = archive_active(&device, argv[2]);
    if (device.mtp) {
        if (result != RESULT_OK && result != RESULT_MISSING) LIBMTP_Dump_Errorstack(device.mtp);
        LIBMTP_Release_Device(device.mtp);
    }
    if (result == RESULT_MISSING && !is_get) result = error("REMOTE_PARENT_MISSING");
    if (!result) dprintf(result_fd, "OK operation=%s bytes=%zu created=%d\n", argv[1],
                        is_put ? source.size : is_get ? received.size : 0, created);
    else if (result == RESULT_MISSING) dprintf(result_fd, "MISSING\n");
    else dprintf(result_fd, "ERROR code=%s\n", failure);
    close(result_fd);
    free(source.data); free(received.data);
    return result;
}
