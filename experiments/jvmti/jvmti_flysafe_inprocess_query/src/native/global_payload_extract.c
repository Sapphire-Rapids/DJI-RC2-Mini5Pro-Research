#include "global_payload_extract.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Reuse the frozen parser's owned spans and per-row block-list membership. */
#include "cloud_policy_parser.c"

static enum global_payload_result global_policy_error(enum cloud_policy_result code) {
    switch (code) {
        case CLOUD_POLICY_LIMIT: return GLOBAL_PAYLOAD_POLICY_LIMIT;
        case CLOUD_POLICY_PRODUCT_UNOBSERVED: return GLOBAL_PAYLOAD_PRODUCT_UNOBSERVED;
        case CLOUD_POLICY_NO_MEMORY: return GLOBAL_PAYLOAD_ALLOCATION;
        case CLOUD_POLICY_INVALID_ARGUMENT: return GLOBAL_PAYLOAD_ARGUMENT;
        case CLOUD_POLICY_NAMESPACE_NULL: case CLOUD_POLICY_MISSING: case CLOUD_POLICY_NULL:
        case CLOUD_POLICY_JSON_NULL: case CLOUD_POLICY_EMPTY_TEXT: return GLOBAL_PAYLOAD_POLICY_UNAVAILABLE;
        default: return GLOBAL_PAYLOAD_POLICY_MALFORMED;
    }
}

struct global_writer { char *data; size_t used; int error; };

static void global_append(struct global_writer *writer, const char *data, size_t size) {
    if (writer->error) return;
    if (size > GLOBAL_PAYLOAD_JSON_LIMIT - writer->used) { writer->error = 1; return; }
    if (writer->data && size) memcpy(writer->data + writer->used, data, size);
    writer->used += size;
}

static void global_literal(struct global_writer *writer, const char *text) {
    global_append(writer, text, strlen(text));
}

static void global_quote(struct global_writer *writer, struct span value) {
    static const char hex[] = "0123456789abcdef";
    global_literal(writer, "\"");
    for (size_t i = 0; i < value.size && !writer->error; ++i) {
        unsigned char c = (unsigned char)value.data[i];
        if (c == '"' || c == '\\') {
            char escaped[2] = {'\\', (char)c};
            global_append(writer, escaped, sizeof(escaped));
        } else if (c < 0x20) {
            char escaped[6] = {'\\', 'u', '0', '0', hex[c >> 4], hex[c & 15]};
            global_append(writer, escaped, sizeof(escaped));
        } else global_append(writer, value.data + i, 1);
    }
    global_literal(writer, "\"");
}

static void global_serialize(struct global_writer *writer, const struct row *rows,
                             size_t count, int64_t product_type,
                             const struct global_payload_summary *summary) {
    char prefix[768];
    int n = snprintf(prefix, sizeof(prefix),
        "{\"schema\":\"finduas-rid-policy-set/v1\",\"product_type\":%lld,"
        "\"row_count\":%d,\"distinct_nonempty_count\":%d,\"nonempty_row_count\":%d,"
        "\"duplicate_country_row_count\":%d,\"default_row_count\":%d,"
        "\"first_default_present\":%s,\"first_default_nonempty\":%s,"
        "\"first_default_row_index\":%d,\"blocked_row_count\":%d,\"rows\":[",
        (long long)product_type, summary->row_count, summary->distinct_nonempty_count,
        summary->nonempty_row_count, summary->duplicate_country_row_count,
        summary->default_row_count, summary->first_default_present ? "true" : "false",
        summary->first_default_nonempty ? "true" : "false", summary->first_default_row_index,
        summary->blocked_row_count);
    if (n < 0 || (size_t)n >= sizeof(prefix)) { writer->error = 1; return; }
    global_append(writer, prefix, (size_t)n);
    for (size_t i = 0; i < count && !writer->error; ++i) {
        if (i) global_literal(writer, ",");
        global_literal(writer, "{\"country_code\":");
        global_quote(writer, rows[i].country);
        global_literal(writer, ",\"data_hex\":");
        global_quote(writer, rows[i].data);
        global_literal(writer, rows[i].blocked ? ",\"blocked_for_product\":true}" : ",\"blocked_for_product\":false}");
    }
    global_literal(writer, "]}");
}

enum global_payload_result global_payload_extract(
    const char *namespace_json, size_t namespace_len, int64_t product_type,
    char **out_json, size_t *out_len, struct global_payload_summary *summary) {
    if (out_json) *out_json = NULL;
    if (out_len) *out_len = 0;
    if (!summary || !out_json || !out_len) return GLOBAL_PAYLOAD_ARGUMENT;
    *summary = (struct global_payload_summary){-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,0};
    enum cloud_policy_result policy_rc = CLOUD_POLICY_OK;
    if ((!namespace_json && namespace_len) || product_type > 65535) policy_rc = CLOUD_POLICY_INVALID_ARGUMENT;
    else if (!namespace_json) policy_rc = CLOUD_POLICY_NAMESPACE_NULL;
    else if (namespace_len > CLOUD_POLICY_MAX_BYTES) policy_rc = CLOUD_POLICY_LIMIT;
    else if (product_type < 0) policy_rc = CLOUD_POLICY_PRODUCT_UNOBSERVED;
    else if (!utf8(namespace_json, namespace_len)) policy_rc = CLOUD_POLICY_MALFORMED;
    summary->policy_rc = (int)policy_rc;
    if (policy_rc != CLOUD_POLICY_OK) return global_policy_error(policy_rc);

    char *outer_arena = malloc(namespace_len + 1);
    if (!outer_arena) { summary->policy_rc = CLOUD_POLICY_NO_MEMORY; return GLOBAL_PAYLOAD_ALLOCATION; }
    struct parser outer = {namespace_json, namespace_len, 0, 0, 0, 0, outer_arena, CLOUD_POLICY_OK};
    struct span policy = {NULL, 0};
    if (!namespace_value(&outer, &policy)) {
        summary->policy_rc = (int)outer.error;
        free(outer_arena);
        return global_policy_error(outer.error);
    }
    char *inner_arena = malloc(policy.size + 1);
    struct row *rows = calloc(CLOUD_POLICY_MAX_ROWS, sizeof(*rows));
    if (!inner_arena || !rows) {
        free(rows); free(inner_arena); free(outer_arena);
        summary->policy_rc = CLOUD_POLICY_NO_MEMORY;
        return GLOBAL_PAYLOAD_ALLOCATION;
    }
    struct parser inner = {policy.data, policy.size, 0, 0, 0, 0, inner_arena, CLOUD_POLICY_OK};
    size_t count = 0;
    enum global_payload_result result = GLOBAL_PAYLOAD_OK;
    if (!policy_rows(&inner, rows, &count, product_type)) {
        summary->policy_rc = (int)inner.error;
        result = global_policy_error(inner.error);
        goto done;
    }

    summary->row_count = (int)count;
    for (size_t i = 0; i < count; ++i) {
        if (rows[i].data.size > GLOBAL_PAYLOAD_HEX_LIMIT) {
            summary->invalid_hex_row_index = (int)i;
            result = GLOBAL_PAYLOAD_HEX_TOO_LONG;
            goto done;
        }
        if (rows[i].data.size & 1u) {
            summary->invalid_hex_row_index = (int)i;
            result = GLOBAL_PAYLOAD_HEX_INVALID;
            goto done;
        }
        for (size_t j = 0; j < rows[i].data.size; ++j) {
            if (hex_digit((unsigned char)rows[i].data.data[j]) < 0) {
                summary->invalid_hex_row_index = (int)i;
                result = GLOBAL_PAYLOAD_HEX_INVALID;
                goto done;
            }
        }
    }
    summary->distinct_nonempty_count = summary->nonempty_row_count = 0;
    summary->duplicate_country_row_count = summary->default_row_count = 0;
    summary->first_default_present = summary->first_default_nonempty = 0;
    summary->blocked_row_count = 0;
    for (size_t i = 0; i < count; ++i) {
        summary->blocked_row_count += rows[i].blocked;
        int duplicate_country = 0, duplicate_data = 0;
        for (size_t j = 0; j < i; ++j) {
            if (equal(rows[i].country, rows[j].country)) duplicate_country = 1;
            if (equal(rows[i].data, rows[j].data)) duplicate_data = 1;
        }
        summary->duplicate_country_row_count += duplicate_country;
        if (rows[i].data.size) {
            ++summary->nonempty_row_count;
            if (!duplicate_data) ++summary->distinct_nonempty_count;
        }
        if (literal(rows[i].country, "DEFAULT")) {
            ++summary->default_row_count;
            if (!summary->first_default_present) {
                summary->first_default_present = 1;
                summary->first_default_nonempty = rows[i].data.size != 0;
                summary->first_default_row_index = (int)i;
            }
        }
    }

    struct global_writer size = {NULL, 0, 0};
    global_serialize(&size, rows, count, product_type, summary);
    if (size.error) { result = GLOBAL_PAYLOAD_OUTPUT_LIMIT; goto done; }
    char *output = malloc(size.used + 1);
    if (!output) { result = GLOBAL_PAYLOAD_ALLOCATION; goto done; }
    struct global_writer writer = {output, 0, 0};
    global_serialize(&writer, rows, count, product_type, summary);
    if (writer.error || writer.used != size.used) {
        free(output); result = GLOBAL_PAYLOAD_OUTPUT_LIMIT; goto done;
    }
    output[writer.used] = 0;
    *out_json = output; *out_len = writer.used;
    summary->json_length = (int)writer.used;
done:
    free(rows); free(inner_arena); free(outer_arena);
    return result;
}
