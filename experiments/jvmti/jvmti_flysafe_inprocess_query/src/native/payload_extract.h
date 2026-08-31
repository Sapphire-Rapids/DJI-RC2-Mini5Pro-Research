#ifndef FINDUAS_PAYLOAD_EXTRACT_H
#define FINDUAS_PAYLOAD_EXTRACT_H
#include <stddef.h>
#include <stdint.h>

#define CLOUD_PAYLOAD_JSON_LIMIT 32768u

enum cloud_payload_result {
    CLOUD_PAYLOAD_OK = 0,
    CLOUD_PAYLOAD_ARGUMENT = 1,
    CLOUD_PAYLOAD_POLICY_UNAVAILABLE = 2,
    CLOUD_PAYLOAD_POLICY_MALFORMED = 3,
    CLOUD_PAYLOAD_POLICY_LIMIT = 4,
    CLOUD_PAYLOAD_PRODUCT_UNOBSERVED = 5,
    CLOUD_PAYLOAD_CACHE_MISSING = 6,
    CLOUD_PAYLOAD_RECEIVER_MISMATCH = 7,
    CLOUD_PAYLOAD_NO_ELIGIBLE_MATCH = 8,
    CLOUD_PAYLOAD_MATCHED_HEX_INVALID = 9,
    CLOUD_PAYLOAD_DEFAULT_HEX_INVALID = 10,
    CLOUD_PAYLOAD_OUTPUT_LIMIT = 11,
    CLOUD_PAYLOAD_ALLOCATION = 12
};

struct cloud_payload_summary {
    int policy_rc;
    int matching_row_count;
    int default_present;
    int default_nonempty;
    int matched_hex_valid;
    int default_hex_valid;
    int matched_hex_length;
    int matched_decoded_length;
    int default_hex_length;
    int default_decoded_length;
    int json_length;
    int row_count;
    int effective_row_count;
    int duplicate_row_count;
    int default_row_count;
    int blocked_row_count;
    int candidate_count;
};

/* Pure in-memory extraction. No device, file, network, log or application calls.
 * Receivers other than18/4 or a cache string outside the eligible candidate set
 * produce no JSON. Only two validated even-length hex strings can be exported.
 * The first DEFAULT is preserved: missing=>null, present-empty=>"".
 * On success *out_json is malloc-owned, length excludes terminating NUL.
 * On failure *out_json=NULL and *out_len=0; numeric summary remains available.
 * This unit includes the frozen cloud_policy_parser.c: do not separately link it.
 */
enum cloud_payload_result cloud_payload_extract(
    const char *namespace_json, size_t namespace_len, int64_t product_type,
    const char *cache_utf8, size_t cache_len, int receiver_type, int receiver_index,
    char **out_json, size_t *out_len, struct cloud_payload_summary *summary);
#endif
