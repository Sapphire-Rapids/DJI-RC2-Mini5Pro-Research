#include "payload_extract.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Import the exact frozen, independent parser without editing or copying it. */
#include "cloud_policy_parser.c"

static enum cloud_payload_result payload_policy_error(enum cloud_policy_result rc) {
    if (rc == CLOUD_POLICY_LIMIT) return CLOUD_PAYLOAD_POLICY_LIMIT;
    if (rc == CLOUD_POLICY_PRODUCT_UNOBSERVED) return CLOUD_PAYLOAD_PRODUCT_UNOBSERVED;
    if (rc == CLOUD_POLICY_NO_MEMORY) return CLOUD_PAYLOAD_ALLOCATION;
    if (rc == CLOUD_POLICY_INVALID_ARGUMENT) return CLOUD_PAYLOAD_ARGUMENT;
    if (rc == CLOUD_POLICY_NAMESPACE_NULL || rc == CLOUD_POLICY_MISSING ||
        rc == CLOUD_POLICY_NULL || rc == CLOUD_POLICY_JSON_NULL || rc == CLOUD_POLICY_EMPTY_TEXT)
        return CLOUD_PAYLOAD_POLICY_UNAVAILABLE;
    return CLOUD_PAYLOAD_POLICY_MALFORMED;
}

static int payload_hex_valid(struct span value) {
    if (value.size & 1u) return 0;
    for (size_t i = 0; i < value.size; ++i)
        if (hex_digit((unsigned char)value.data[i]) < 0) return 0;
    return 1;
}

static enum cloud_payload_result payload_json(
    struct span matched, struct span default_value, int64_t product_type,
    struct cloud_payload_summary *summary, char **out, size_t *out_len) {
    char prefix[1024];
    int written = snprintf(prefix, sizeof(prefix),
        "{\"schema\":\"finduas-rid-policy-payload/v1\",\"product_type\":%lld,"
        "\"receiver_type\":18,\"receiver_index\":4,\"default_present\":%s,"
        "\"default_nonempty\":%s,\"matching_row_count\":%d,"
        "\"row_count\":%d,\"effective_row_count\":%d,\"duplicate_row_count\":%d,"
        "\"default_row_count\":%d,\"blocked_row_count\":%d,\"candidate_count\":%d,"
        "\"matched_hex_length\":%d,\"matched_decoded_length\":%d,"
        "\"default_hex_length\":%d,\"default_decoded_length\":%d,\"matched_hex\":\"",
        (long long)product_type,summary->default_present ? "true" : "false",summary->default_nonempty ? "true" : "false",summary->matching_row_count,
        summary->row_count,summary->effective_row_count,summary->duplicate_row_count,
        summary->default_row_count,summary->blocked_row_count,summary->candidate_count,
        summary->matched_hex_length,summary->matched_decoded_length,
        summary->default_hex_length,summary->default_decoded_length);
    if (written < 0 || (size_t)written >= sizeof(prefix)) return CLOUD_PAYLOAD_OUTPUT_LIMIT;
    const char *middle = "\",\"default_hex\":";
    size_t middle_size = strlen(middle);
    size_t default_size = summary->default_present ? default_value.size + 2 : 4;
    size_t length = (size_t)written + matched.size + middle_size + default_size + 1;
    if (length > CLOUD_PAYLOAD_JSON_LIMIT) return CLOUD_PAYLOAD_OUTPUT_LIMIT;
    char *json = malloc(length + 1);
    if (json == NULL) return CLOUD_PAYLOAD_ALLOCATION;
    size_t cursor = 0;
    memcpy(json + cursor, prefix, (size_t)written); cursor += (size_t)written;
    memcpy(json + cursor, matched.data, matched.size); cursor += matched.size;
    memcpy(json + cursor, middle, middle_size); cursor += middle_size;
    if (summary->default_present) {
        json[cursor++] = '"';
        if (default_value.size != 0) memcpy(json + cursor, default_value.data, default_value.size);
        cursor += default_value.size; json[cursor++] = '"';
    } else { memcpy(json + cursor, "null", 4); cursor += 4; }
    json[cursor++] = '}'; json[cursor] = '\0';
    if (cursor != length) { free(json); return CLOUD_PAYLOAD_ARGUMENT; }
    *out = json; *out_len = length; summary->json_length = (int)length;
    return CLOUD_PAYLOAD_OK;
}

enum cloud_payload_result cloud_payload_extract(
    const char *namespace_json, size_t namespace_len, int64_t product_type,
    const char *cache_utf8, size_t cache_len, int receiver_type, int receiver_index,
    char **out_json, size_t *out_len, struct cloud_payload_summary *summary) {
    if (out_json != NULL) *out_json = NULL;
    if (out_len != NULL) *out_len = 0;
    if (out_json == NULL || out_len == NULL || summary == NULL) return CLOUD_PAYLOAD_ARGUMENT;
    *summary = (struct cloud_payload_summary){-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,-1,-1,-1,-1,-1,-1};
    if (product_type > 65535) return CLOUD_PAYLOAD_ARGUMENT;
    struct cloud_policy_summary audit;
    enum cloud_policy_result policy_rc = cloud_policy_audit(namespace_json,namespace_len,product_type,
        cache_utf8,cache_len,receiver_type,receiver_index,&audit);
    summary->policy_rc = (int)policy_rc;
    if (policy_rc != CLOUD_POLICY_OK) return payload_policy_error(policy_rc);
    summary->row_count = audit.row_count; summary->effective_row_count = audit.effective_row_count;
    summary->duplicate_row_count = audit.duplicate_row_count; summary->default_row_count = audit.default_row_count;
    summary->blocked_row_count = audit.blocked_row_count; summary->candidate_count = audit.nonempty_candidate_count;
    if (cache_utf8 == NULL) return CLOUD_PAYLOAD_CACHE_MISSING;
    if (!audit.receiver_match) return CLOUD_PAYLOAD_RECEIVER_MISMATCH;
    if (audit.matching_candidate_count != 1) return CLOUD_PAYLOAD_NO_ELIGIBLE_MATCH;
    struct span matched = {cache_utf8,cache_len};
    summary->matched_hex_length = (int)cache_len;
    summary->matched_hex_valid = payload_hex_valid(matched);
    if (!summary->matched_hex_valid) return CLOUD_PAYLOAD_MATCHED_HEX_INVALID;
    summary->matched_decoded_length = (int)(cache_len / 2);

    /* Decode once more into an owned arena so only the matched and first DEFAULT
     * spans can leave this unit. All country and unrelated data stay local. */
    char *outer_arena = malloc(namespace_len + 1);
    if (outer_arena == NULL) return CLOUD_PAYLOAD_ALLOCATION;
    struct parser outer = {namespace_json,namespace_len,0,0,0,0,outer_arena,CLOUD_POLICY_OK};
    struct span policy = {NULL,0};
    if (!namespace_value(&outer,&policy)) { free(outer_arena); return payload_policy_error(outer.error); }
    char *inner_arena = malloc(policy.size + 1);
    struct row *rows = calloc(CLOUD_POLICY_MAX_ROWS,sizeof(*rows));
    if (inner_arena == NULL || rows == NULL) {
        free(rows); free(inner_arena); free(outer_arena); return CLOUD_PAYLOAD_ALLOCATION;
    }
    struct parser inner = {policy.data,policy.size,0,0,0,0,inner_arena,CLOUD_POLICY_OK};
    size_t count = 0;
    enum cloud_payload_result result = CLOUD_PAYLOAD_OK;
    if (!policy_rows(&inner,rows,&count,product_type)) { result=payload_policy_error(inner.error); goto cleanup; }
    struct span default_value = {NULL,0};
    summary->matching_row_count=0; summary->default_present=0; summary->default_nonempty=0;
    for (size_t i=0;i<count;++i) {
        if (equal(rows[i].data,matched)) ++summary->matching_row_count;
        if (!summary->default_present && literal(rows[i].country,"DEFAULT")) {
            default_value=rows[i].data; summary->default_present=1;
        }
    }
    if (summary->default_present) {
        summary->default_nonempty=default_value.size!=0;
        summary->default_hex_length=(int)default_value.size;
        summary->default_hex_valid=payload_hex_valid(default_value);
        if (!summary->default_hex_valid) { result=CLOUD_PAYLOAD_DEFAULT_HEX_INVALID; goto cleanup; }
        summary->default_decoded_length=(int)(default_value.size/2);
    }
    result=payload_json(matched,default_value,product_type,summary,out_json,out_len);
cleanup:
    free(rows); free(inner_arena); free(outer_arena);
    return result;
}
