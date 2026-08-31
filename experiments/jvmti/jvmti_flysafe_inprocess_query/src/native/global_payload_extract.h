#ifndef FINDUAS_GLOBAL_PAYLOAD_EXTRACT_H
#define FINDUAS_GLOBAL_PAYLOAD_EXTRACT_H
#include <stddef.h>
#include <stdint.h>

#define GLOBAL_PAYLOAD_JSON_LIMIT 32768u
#define GLOBAL_PAYLOAD_HEX_LIMIT 4096u

enum global_payload_result {
    GLOBAL_PAYLOAD_OK = 0,
    GLOBAL_PAYLOAD_ARGUMENT = 1,
    GLOBAL_PAYLOAD_POLICY_UNAVAILABLE = 2,
    GLOBAL_PAYLOAD_POLICY_MALFORMED = 3,
    GLOBAL_PAYLOAD_POLICY_LIMIT = 4,
    GLOBAL_PAYLOAD_PRODUCT_UNOBSERVED = 5,
    GLOBAL_PAYLOAD_HEX_INVALID = 6,
    GLOBAL_PAYLOAD_HEX_TOO_LONG = 7,
    GLOBAL_PAYLOAD_OUTPUT_LIMIT = 8,
    GLOBAL_PAYLOAD_ALLOCATION = 9
};

struct global_payload_summary {
    int policy_rc;
    int row_count;
    int distinct_nonempty_count;
    int nonempty_row_count;
    int duplicate_country_row_count;
    int default_row_count;
    int first_default_present;
    int first_default_nonempty;
    int first_default_row_index;
    int blocked_row_count;
    int invalid_hex_row_index;
    int json_length;
};

/* Pure memory: only the known rows in the fixed RID namespace are exported.
 * Input is length-delimited standard UTF-8, max65536 bytes; product0..65535.
 * Row order, repeated country labels and original hex case are preserved.
 * distinct_nonempty_count counts distinct nonempty strings across ALL rows;
 * blocked_for_product is raw block-list membership, including DEFAULT rows.
 * This is not actual-area selection. No current area, match, unknown fields,
 * namespace literal or block-list contents are emitted. Maximum256 rows,
 * maximum4096 characters per hex string, maximum32768 output bytes.
 * Success: malloc-owned *out_json, *out_len excludes NUL; caller frees it.
 * Failure: *out_json=NULL, *out_len=0. Summary contains only numeric metadata.
 * This unit includes frozen cloud_policy_parser.c; do not link it separately.
 */
enum global_payload_result global_payload_extract(
    const char *namespace_json, size_t namespace_len, int64_t product_type,
    char **out_json, size_t *out_len, struct global_payload_summary *summary);
#endif
