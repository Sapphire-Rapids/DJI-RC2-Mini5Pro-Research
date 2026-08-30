#include "cloud_policy_parser.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int checks;
#define CHECK(x) do { ++checks; if (!(x)) { fprintf(stderr, "check failed at line %d\n", __LINE__); exit(1); } } while (0)

static char *wrap(const char *policy) {
    size_t size = strlen(policy);
    char *out = malloc(size * 6 + 64);
    CHECK(out != NULL);
    const char *prefix = "{\"country_and_device_type\":\"";
    size_t used = strlen(prefix);
    memcpy(out, prefix, used);
    for (size_t i = 0; i < size; ++i) {
        unsigned char c = (unsigned char)policy[i];
        if (c == '"' || c == '\\') out[used++] = '\\';
        if (c < 0x20) {
            static const char hex[] = "0123456789abcdef";
            memcpy(out + used, "\\u00", 4); used += 4;
            out[used++] = hex[c >> 4]; out[used++] = hex[c & 15];
        } else out[used++] = (char)c;
    }
    out[used++] = '"'; out[used++] = '}'; out[used] = 0;
    return out;
}

static enum cloud_policy_result run(const char *policy, const char *cache,
                                    struct cloud_policy_summary *out) {
    char *json = wrap(policy);
    enum cloud_policy_result rc = cloud_policy_audit(json, strlen(json), 139,
        cache, cache ? strlen(cache) : 0, 18, 4, out);
    free(json);
    return rc;
}

static void error(const char *policy, enum cloud_policy_result expected) {
    struct cloud_policy_summary out;
    CHECK(run(policy, "TEST-PRIVATE", &out) == expected);
    CHECK(out.row_count == -1 && out.matching_candidate_count == -1 && out.default_match == -1);
}

int main(void) {
    struct cloud_policy_summary out;
    const char *simple = "[{\"country_code\":\"TEST-AREA\",\"data\":\"TEST-PAYLOAD\",\"block_device\":[]}]";
    CHECK(run(simple, "TEST-PAYLOAD", &out) == CLOUD_POLICY_OK);
    CHECK(out.row_count == 1 && out.effective_row_count == 1 && out.nonempty_candidate_count == 1);
    CHECK(out.matching_candidate_count == 1 && out.receiver_match == 1 && out.default_match == 0);
    CHECK(run(simple, NULL, &out) == CLOUD_POLICY_OK);
    CHECK(out.matching_candidate_count == -1 && out.receiver_match == -1 && out.default_match == -1);
    CHECK(run(simple, "TEST-OTHER", &out) == CLOUD_POLICY_OK && out.matching_candidate_count == 0);
    char *json = wrap(simple);
    CHECK(cloud_policy_audit(json, strlen(json), 139, "TEST-PAYLOAD", 12, 4, 4, &out) == CLOUD_POLICY_OK);
    CHECK(out.matching_candidate_count == 0 && out.receiver_match == 0);
    CHECK(cloud_policy_audit(json, strlen(json), -1, NULL, 0, 18, 4, &out) == CLOUD_POLICY_PRODUCT_UNOBSERVED);
    free(json);

    const char *duplicates = "["
        "{\"country_code\":\"TEST-AREA\",\"data\":\"TEST-BLOCKED\",\"block_device\":[139]},"
        "{\"country_code\":\"TEST-AREA\",\"data\":\"TEST-LATER\",\"block_device\":[]},"
        "{\"country_code\":\"DEFAULT\",\"data\":\"TEST-DEFAULT\",\"block_device\":[139]},"
        "{\"country_code\":\"DEFAULT\",\"data\":\"TEST-LATER-DEFAULT\",\"block_device\":[]},"
        "{\"country_code\":\"test-area\",\"data\":\"TEST-LOWER\",\"block_device\":[]}]";
    CHECK(run(duplicates, "TEST-DEFAULT", &out) == CLOUD_POLICY_OK);
    CHECK(out.row_count == 5 && out.effective_row_count == 3 && out.duplicate_row_count == 2);
    CHECK(out.default_row_count == 2 && out.blocked_row_count == 2 && out.nonempty_candidate_count == 2);
    CHECK(out.default_match == 1 && out.matching_candidate_count == 1);
    CHECK(run(duplicates, "TEST-LATER", &out) == CLOUD_POLICY_OK && out.matching_candidate_count == 0);
    CHECK(run("[]", "", &out) == CLOUD_POLICY_OK && out.nonempty_candidate_count == 0 && out.matching_candidate_count == 0);
    CHECK(run("[{\"country_code\":\"TEST\",\"data\":\"\",\"block_device\":[]}]", "", &out) == CLOUD_POLICY_OK && out.matching_candidate_count == 0);
    CHECK(run("[{\"country_code\":\"TEST\",\"data\":\" \",\"block_device\":[]}]", " ", &out) == CLOUD_POLICY_OK && out.matching_candidate_count == 1);

    const char *unicode = "[{\"country_code\":\"TEST-\\u4e2d\",\"data\":\"TEST-\\uD83D\\uDE80\\n\\u0041\",\"block_device\":[],"
                          "\"unknown\":{\"text\":\"说明\",\"nested\":[true,false,null,1.25e+2]}}]";
    CHECK(run(unicode, "TEST-\xf0\x9f\x9a\x80\nA", &out) == CLOUD_POLICY_OK && out.matching_candidate_count == 1);
    CHECK(run("[{\"country_code\":\"TEST\",\"data\":\"TEST-\\\"\\\\\\/\\b\\f\\r\\t\",\"block_device\":[]}]",
              "TEST-\"\\/\b\f\r\t", &out) == CLOUD_POLICY_OK && out.matching_candidate_count == 1);
    error("[{\"country_code\":\"TEST\",\"data\":\"\\ud800\",\"block_device\":[]}]", CLOUD_POLICY_MALFORMED);
    error("[{\"country_code\":\"TEST\",\"data\":\"\\udc00\",\"block_device\":[]}]", CLOUD_POLICY_MALFORMED);
    error("[{\"country_code\":\"TEST\",\"data\":\"\\u0000\",\"block_device\":[]}]", CLOUD_POLICY_MALFORMED);
    error("[{\"country_code\":\"TEST\",\"data\":\"\\uZZZZ\",\"block_device\":[]}]", CLOUD_POLICY_MALFORMED);
    error("[{\"country_code\":\"TEST\",\"data\":\"\\v\",\"block_device\":[]}]", CLOUD_POLICY_MALFORMED);
    error("[{\"country_code\":\"TEST\",\"data\":\"TEST-A\",\"data\":\"TEST-B\",\"block_device\":[]}]", CLOUD_POLICY_MALFORMED);
    error("[{\"country_code\":\"TEST\",\"data\":\"TEST\",\"block_device\":[],\"extra\":{\"a\":1,\"a\":2}}]", CLOUD_POLICY_MALFORMED);
    error("[{\"country_code\":null,\"data\":\"TEST\",\"block_device\":[]}]", CLOUD_POLICY_MALFORMED);
    error("[{\"country_code\":\"TEST\",\"data\":\"TEST\"}]", CLOUD_POLICY_MALFORMED);
    error("[{\"country_code\":\"TEST\",\"data\":\"TEST\",\"block_device\":[true]}]", CLOUD_POLICY_MALFORMED);
    error("[{\"country_code\":\"TEST\",\"data\":\"TEST\",\"block_device\":[139.0]}]", CLOUD_POLICY_MALFORMED);
    error("[{\"country_code\":\"TEST\",\"data\":\"TEST\",\"block_device\":[9223372036854775808]}]", CLOUD_POLICY_MALFORMED);
    CHECK(run("[{\"country_code\":\"TEST\",\"data\":\"TEST\",\"block_device\":[-9223372036854775808,9223372036854775807,-0]}]", "TEST", &out) == CLOUD_POLICY_OK);
    error("[] trailing", CLOUD_POLICY_MALFORMED);
    error("[null]", CLOUD_POLICY_MALFORMED);
    error("[{]", CLOUD_POLICY_MALFORMED);
    error("", CLOUD_POLICY_EMPTY_TEXT);
    error("null", CLOUD_POLICY_JSON_NULL);
    CHECK(cloud_policy_audit(NULL, 0, 139, NULL, 0, 18, 4, &out) == CLOUD_POLICY_NAMESPACE_NULL);
    CHECK(cloud_policy_audit(NULL, 1, 139, NULL, 0, 18, 4, &out) == CLOUD_POLICY_INVALID_ARGUMENT);
    CHECK(cloud_policy_audit("{}", 2, 139, NULL, 0, 18, 4, &out) == CLOUD_POLICY_MISSING);
    const char *null = "{\"country_and_device_type\":null}";
    CHECK(cloud_policy_audit(null, strlen(null), 139, NULL, 0, 18, 4, &out) == CLOUD_POLICY_NULL);
    const char *bad_utf8[] = {"\xc0\x80", "\xed\xa0\x80", "\xf4\x90\x80\x80", "\xe2\x82"};
    for (size_t i = 0; i < sizeof(bad_utf8) / sizeof(*bad_utf8); ++i)
        CHECK(cloud_policy_audit(bad_utf8[i], strlen(bad_utf8[i]), 139, NULL, 0, 18, 4, &out) == CLOUD_POLICY_MALFORMED);

    char *large = malloc(CLOUD_POLICY_MAX_BYTES + 2);
    CHECK(large != NULL);
    memset(large, ' ', CLOUD_POLICY_MAX_BYTES + 1);
    CHECK(cloud_policy_audit(large, CLOUD_POLICY_MAX_BYTES + 1, 139, NULL, 0, 18, 4, &out) == CLOUD_POLICY_LIMIT);
    large[0] = '['; size_t used = 1;
    const char *entry = "{\"country_code\":\"TEST\",\"data\":\"TEST\",\"block_device\":[]}";
    for (size_t i = 0; i < CLOUD_POLICY_MAX_ROWS; ++i) {
        if (i) large[used++] = ',';
        memcpy(large + used, entry, strlen(entry)); used += strlen(entry);
    }
    large[used] = ']'; large[used + 1] = 0;
    CHECK(run(large, "TEST", &out) == CLOUD_POLICY_OK && out.row_count == 256 && out.duplicate_row_count == 255);
    large[used++] = ','; memcpy(large + used, entry, strlen(entry)); used += strlen(entry);
    large[used++] = ']'; large[used] = 0;
    error(large, CLOUD_POLICY_LIMIT);
    strcpy(large, "[{\"country_code\":\"TEST\",\"data\":\"TEST\",\"block_device\":[],\"extra\":");
    used = strlen(large);
    for (unsigned i = 0; i < CLOUD_POLICY_MAX_DEPTH + 1; ++i) large[used++] = '[';
    large[used++] = '0';
    for (unsigned i = 0; i < CLOUD_POLICY_MAX_DEPTH + 1; ++i) large[used++] = ']';
    memcpy(large + used, "}]", 3);
    error(large, CLOUD_POLICY_LIMIT);
    free(large);
    printf("cloud_policy_parser: %d checks passed\n", checks);
    return 0;
}
