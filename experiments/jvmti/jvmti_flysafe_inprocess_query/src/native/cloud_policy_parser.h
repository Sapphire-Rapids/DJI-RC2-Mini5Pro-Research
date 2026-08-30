#ifndef FINDUAS_CLOUD_POLICY_PARSER_H
#define FINDUAS_CLOUD_POLICY_PARSER_H

#include <stddef.h>
#include <stdint.h>

#define CLOUD_POLICY_MAX_BYTES 65536u
#define CLOUD_POLICY_MAX_ROWS 256u
#define CLOUD_POLICY_MAX_DEPTH 12u
#define CLOUD_POLICY_MAX_MEMBERS 64u
#define CLOUD_POLICY_MAX_BLOCK_ENTRIES 4096u

enum cloud_policy_result {
    CLOUD_POLICY_OK = 0,
    CLOUD_POLICY_NAMESPACE_NULL = 1,
    CLOUD_POLICY_MISSING = 2,
    CLOUD_POLICY_NULL = 3,
    CLOUD_POLICY_JSON_NULL = 4,
    CLOUD_POLICY_EMPTY_TEXT = 5,
    CLOUD_POLICY_MALFORMED = 6,
    CLOUD_POLICY_LIMIT = 7,
    CLOUD_POLICY_UNSUPPORTED_TEXT = 8,
    CLOUD_POLICY_PRODUCT_UNOBSERVED = 9,
    CLOUD_POLICY_INVALID_ARGUMENT = 10,
    CLOUD_POLICY_NO_MEMORY = 11
};

struct cloud_policy_summary {
    int row_count;
    int effective_row_count;
    int duplicate_row_count;
    int default_row_count;
    int blocked_row_count;
    int nonempty_candidate_count;
    int matching_candidate_count;
    int default_match;
    int receiver_match;
};

/* Offline candidate-set comparison, with no actual-area selection or emission.
 * Inputs are length-delimited standard UTF-8. JSON escapes and valid surrogate
 * pairs are decoded, without normalization or case conversion. Convert JNI
 * UTF-16 to standard UTF-8; do not substitute modified UTF-8. Invalid UTF-8,
 * isolated surrogates and NUL are MALFORMED (including in unknown fields).
 * namespace_json == NULL denotes an unobserved/null namespace; cache_utf8 ==
 * NULL denotes an unobserved cache. Their lengths must be zero. product_type < 0
 * denotes an unobserved product. All summary fields stay -1 on failure; cache
 * comparison fields stay -1 when a successfully parsed policy has no cache.
 * The shared cache match is receiver18/4 + string equality, not writer identity.
 */
enum cloud_policy_result cloud_policy_audit(
    const char *namespace_json, size_t namespace_len, int64_t product_type,
    const char *cache_utf8, size_t cache_len, int receiver_type,
    int receiver_index, struct cloud_policy_summary *out);

#endif
