#include "cloud_policy_parser.h"

#include <stdlib.h>
#include <string.h>

/* This parser accepts only the fixed namespace/policy schema. Unknown row
 * fields are skipped as bounded JSON; no payload is logged or returned. */
struct span { const char *data; size_t size; };
struct row { struct span country, data; int blocked, duplicate; };
struct parser {
    const char *text;
    size_t size, at, used, nodes, block_entries;
    char *arena;
    enum cloud_policy_result error;
};

static int fail(struct parser *p, enum cloud_policy_result error) {
    if (p->error == CLOUD_POLICY_OK) p->error = error;
    return 0;
}

static int equal(struct span a, struct span b) {
    return a.size == b.size && (a.size == 0 || memcmp(a.data, b.data, a.size) == 0);
}

static int literal(struct span value, const char *text) {
    struct span expected = {text, strlen(text)};
    return equal(value, expected);
}

static void space(struct parser *p) {
    while (p->at < p->size && (p->text[p->at] == ' ' || p->text[p->at] == '\t' ||
           p->text[p->at] == '\n' || p->text[p->at] == '\r')) ++p->at;
}

static int take(struct parser *p, char value) {
    space(p);
    if (p->at >= p->size || p->text[p->at] != value) return 0;
    ++p->at;
    return 1;
}

static int require(struct parser *p, char value) {
    return take(p, value) || fail(p, CLOUD_POLICY_MALFORMED);
}

static int word(struct parser *p, const char *text) {
    space(p);
    size_t size = strlen(text);
    if (size > p->size - p->at || memcmp(p->text + p->at, text, size) != 0) return 0;
    p->at += size;
    return 1;
}

static int node(struct parser *p, unsigned depth) {
    if (depth > CLOUD_POLICY_MAX_DEPTH || ++p->nodes > 32768u)
        return fail(p, CLOUD_POLICY_LIMIT);
    return 1;
}

static int hex_digit(unsigned char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static int utf8(const char *text, size_t size) {
    size_t at = 0;
    while (at < size) {
        unsigned char first = (unsigned char)text[at++];
        if (first == 0) return 0;
        if (first < 128) continue;
        unsigned value, continuation, minimum;
        if (first >= 0xc2 && first <= 0xdf) {
            value = first & 0x1fu; continuation = 1; minimum = 0x80;
        } else if (first >= 0xe0 && first <= 0xef) {
            value = first & 0x0fu; continuation = 2; minimum = 0x800;
        } else if (first >= 0xf0 && first <= 0xf4) {
            value = first & 7u; continuation = 3; minimum = 0x10000;
        } else return 0;
        if (size - at < continuation) return 0;
        for (unsigned i = 0; i < continuation; ++i) {
            unsigned char next = (unsigned char)text[at++];
            if ((next & 0xc0u) != 0x80u) return 0;
            value = (value << 6) | (next & 0x3fu);
        }
        if (value < minimum || value > 0x10ffff || (value >= 0xd800 && value <= 0xdfff)) return 0;
    }
    return 1;
}

static int hex4(struct parser *p, unsigned *value) {
    if (p->size - p->at < 4) return fail(p, CLOUD_POLICY_MALFORMED);
    *value = 0;
    for (unsigned i = 0; i < 4; ++i) {
        int next = hex_digit((unsigned char)p->text[p->at++]);
        if (next < 0) return fail(p, CLOUD_POLICY_MALFORMED);
        *value = *value * 16u + (unsigned)next;
    }
    return 1;
}

static int unicode_escape(struct parser *p) {
    unsigned value;
    if (!hex4(p, &value)) return 0;
    if (value >= 0xd800 && value <= 0xdbff) {
        if (p->size - p->at < 6 || p->text[p->at] != '\\' || p->text[p->at + 1] != 'u')
            return fail(p, CLOUD_POLICY_MALFORMED);
        p->at += 2;
        unsigned low;
        if (!hex4(p, &low)) return 0;
        if (low < 0xdc00 || low > 0xdfff) return fail(p, CLOUD_POLICY_MALFORMED);
        value = 0x10000u + ((value - 0xd800u) << 10) + (low - 0xdc00u);
    } else if (value >= 0xdc00 && value <= 0xdfff) return fail(p, CLOUD_POLICY_MALFORMED);
    if (value == 0) return fail(p, CLOUD_POLICY_MALFORMED);
    unsigned count = value < 0x80 ? 1 : value < 0x800 ? 2 : value < 0x10000 ? 3 : 4;
    if (count > p->size - p->used) return fail(p, CLOUD_POLICY_LIMIT);
    if (count == 1) p->arena[p->used++] = (char)value;
    else {
        unsigned first = count == 2 ? 0xc0 : count == 3 ? 0xe0 : 0xf0;
        p->arena[p->used++] = (char)(first | (value >> (6u * (count - 1u))));
        for (unsigned i = count - 1; i > 0; --i)
            p->arena[p->used++] = (char)(0x80u | ((value >> (6u * (i - 1u))) & 0x3fu));
    }
    return 1;
}

static int string(struct parser *p, struct span *out) {
    if (!require(p, '"')) return 0;
    size_t begin = p->used;
    while (p->at < p->size) {
        unsigned char c = (unsigned char)p->text[p->at++];
        if (c == '"') {
            *out = (struct span){p->arena + begin, p->used - begin};
            return 1;
        }
        if (c < 0x20) return fail(p, CLOUD_POLICY_MALFORMED);
        if (c == '\\') {
            if (p->at == p->size) return fail(p, CLOUD_POLICY_MALFORMED);
            c = (unsigned char)p->text[p->at++];
            switch (c) {
                case '"': case '\\': case '/': break;
                case 'b': c = '\b'; break;
                case 'f': c = '\f'; break;
                case 'n': c = '\n'; break;
                case 'r': c = '\r'; break;
                case 't': c = '\t'; break;
                case 'u': if (!unicode_escape(p)) return 0; continue;
                default: return fail(p, CLOUD_POLICY_MALFORMED);
            }
        }
        if (p->used >= p->size) return fail(p, CLOUD_POLICY_LIMIT);
        p->arena[p->used++] = (char)c;
    }
    return fail(p, CLOUD_POLICY_MALFORMED);
}

static int digit(char c) { return c >= '0' && c <= '9'; }

static int number(struct parser *p, struct span *out) {
    space(p);
    size_t begin = p->at;
    if (p->at < p->size && p->text[p->at] == '-') ++p->at;
    if (p->at == p->size || !digit(p->text[p->at])) return fail(p, CLOUD_POLICY_MALFORMED);
    if (p->text[p->at++] != '0') {
        while (p->at < p->size && digit(p->text[p->at])) ++p->at;
    } else if (p->at < p->size && digit(p->text[p->at])) {
        return fail(p, CLOUD_POLICY_MALFORMED);
    }
    if (p->at < p->size && p->text[p->at] == '.') {
        ++p->at;
        if (p->at == p->size || !digit(p->text[p->at])) return fail(p, CLOUD_POLICY_MALFORMED);
        while (p->at < p->size && digit(p->text[p->at])) ++p->at;
    }
    if (p->at < p->size && (p->text[p->at] == 'e' || p->text[p->at] == 'E')) {
        ++p->at;
        if (p->at < p->size && (p->text[p->at] == '+' || p->text[p->at] == '-')) ++p->at;
        if (p->at == p->size || !digit(p->text[p->at])) return fail(p, CLOUD_POLICY_MALFORMED);
        while (p->at < p->size && digit(p->text[p->at])) ++p->at;
    }
    *out = (struct span){p->text + begin, p->at - begin};
    return 1;
}

static int integer(struct parser *p, int64_t *out) {
    struct span value;
    if (!number(p, &value)) return 0;
    size_t at = 0;
    int negative = value.data[0] == '-';
    if (negative) ++at;
    uint64_t maximum = negative ? (uint64_t)INT64_MAX + 1u : (uint64_t)INT64_MAX;
    uint64_t result = 0;
    for (; at < value.size; ++at) {
        if (!digit(value.data[at])) return fail(p, CLOUD_POLICY_MALFORMED);
        unsigned next = (unsigned)(value.data[at] - '0');
        if (result > (maximum - next) / 10u) return fail(p, CLOUD_POLICY_MALFORMED);
        result = result * 10u + next;
    }
    *out = negative ? -(int64_t)(result - (result != 0)) - (result != 0) : (int64_t)result;
    return 1;
}

static int key(struct parser *p, struct span *keys, size_t *count, struct span *out) {
    if (*count == CLOUD_POLICY_MAX_MEMBERS) return fail(p, CLOUD_POLICY_LIMIT);
    if (!string(p, out)) return 0;
    for (size_t i = 0; i < *count; ++i)
        if (equal(keys[i], *out)) return fail(p, CLOUD_POLICY_MALFORMED);
    keys[(*count)++] = *out;
    return require(p, ':');
}

static int skip(struct parser *p, unsigned depth) {
    if (!node(p, depth)) return 0;
    space(p);
    if (p->at == p->size) return fail(p, CLOUD_POLICY_MALFORMED);
    struct span value;
    switch (p->text[p->at]) {
        case '"': return string(p, &value);
        case '{': {
            ++p->at;
            struct span keys[CLOUD_POLICY_MAX_MEMBERS];
            size_t count = 0;
            if (take(p, '}')) return 1;
            do {
                if (!key(p, keys, &count, &value) || !skip(p, depth + 1)) return 0;
                if (take(p, '}')) return 1;
            } while (require(p, ','));
            return 0;
        }
        case '[':
            ++p->at;
            if (take(p, ']')) return 1;
            do {
                if (!skip(p, depth + 1)) return 0;
                if (take(p, ']')) return 1;
            } while (require(p, ','));
            return 0;
        case 't': if (word(p, "true")) return 1; break;
        case 'f': if (word(p, "false")) return 1; break;
        case 'n': if (word(p, "null")) return 1; break;
        default: return number(p, &value);
    }
    return fail(p, CLOUD_POLICY_MALFORMED);
}

static int end(struct parser *p) {
    space(p);
    return p->at == p->size || fail(p, CLOUD_POLICY_MALFORMED);
}

static int namespace_value(struct parser *p, struct span *policy) {
    if (!node(p, 0) || !require(p, '{')) return 0;
    struct span keys[CLOUD_POLICY_MAX_MEMBERS], name, value;
    size_t count = 0;
    int found = 0, is_null = 0;
    if (!take(p, '}')) {
        do {
            if (!key(p, keys, &count, &name) || !node(p, 1)) return 0;
            int null_value = word(p, "null");
            if (!null_value && !string(p, &value)) return 0;
            if (literal(name, "country_and_device_type")) {
                found = 1;
                is_null = null_value;
                if (!is_null) *policy = value;
            }
            if (take(p, '}')) break;
            if (!require(p, ',')) return 0;
        } while (1);
    }
    if (!end(p)) return 0;
    if (!found) return fail(p, CLOUD_POLICY_MISSING);
    if (is_null) return fail(p, CLOUD_POLICY_NULL);
    if (policy->size == 0) return fail(p, CLOUD_POLICY_EMPTY_TEXT);
    return 1;
}

static int policy_row(struct parser *p, struct row *row, int64_t product_type) {
    if (!node(p, 1) || !require(p, '{')) return 0;
    struct span keys[CLOUD_POLICY_MAX_MEMBERS], name;
    size_t count = 0;
    unsigned fields = 0;
    if (!take(p, '}')) {
        do {
            if (!key(p, keys, &count, &name)) return 0;
            if (literal(name, "country_code")) {
                fields |= 1u;
                if (!node(p, 2) || !string(p, &row->country)) return 0;
            } else if (literal(name, "data")) {
                fields |= 2u;
                if (!node(p, 2) || !string(p, &row->data)) return 0;
            } else if (literal(name, "block_device")) {
                fields |= 4u;
                if (!node(p, 2) || !require(p, '[')) return 0;
                if (!take(p, ']')) {
                    do {
                        int64_t blocked;
                        if (++p->block_entries > CLOUD_POLICY_MAX_BLOCK_ENTRIES)
                            return fail(p, CLOUD_POLICY_LIMIT);
                        if (!node(p, 3) || !integer(p, &blocked)) return 0;
                        if (blocked == product_type) row->blocked = 1;
                        if (take(p, ']')) break;
                        if (!require(p, ',')) return 0;
                    } while (1);
                }
            } else if (!skip(p, 2)) return 0;
            if (take(p, '}')) break;
            if (!require(p, ',')) return 0;
        } while (1);
    }
    return fields == 7u || fail(p, CLOUD_POLICY_MALFORMED);
}

static int policy_rows(struct parser *p, struct row *rows, size_t *count, int64_t product_type) {
    if (!node(p, 0)) return 0;
    if (word(p, "null")) {
        if (!end(p)) return 0;
        return fail(p, CLOUD_POLICY_JSON_NULL);
    }
    if (!require(p, '[')) return 0;
    if (!take(p, ']')) {
        do {
            if (*count == CLOUD_POLICY_MAX_ROWS) return fail(p, CLOUD_POLICY_LIMIT);
            if (!policy_row(p, &rows[(*count)++], product_type)) return 0;
            if (take(p, ']')) break;
            if (!require(p, ',')) return 0;
        } while (1);
    }
    return end(p);
}

static void unavailable(struct cloud_policy_summary *out) {
    *out = (struct cloud_policy_summary){-1, -1, -1, -1, -1, -1, -1, -1, -1};
}

enum cloud_policy_result cloud_policy_audit(
    const char *namespace_json, size_t namespace_len, int64_t product_type,
    const char *cache_utf8, size_t cache_len, int receiver_type,
    int receiver_index, struct cloud_policy_summary *out) {
    if (out == NULL) return CLOUD_POLICY_INVALID_ARGUMENT;
    unavailable(out);
    if ((namespace_json == NULL && namespace_len != 0) || (cache_utf8 == NULL && cache_len != 0))
        return CLOUD_POLICY_INVALID_ARGUMENT;
    if (namespace_json == NULL) return CLOUD_POLICY_NAMESPACE_NULL;
    if (namespace_len > CLOUD_POLICY_MAX_BYTES || cache_len > CLOUD_POLICY_MAX_BYTES)
        return CLOUD_POLICY_LIMIT;
    if (product_type < 0) return CLOUD_POLICY_PRODUCT_UNOBSERVED;
    if (!utf8(namespace_json, namespace_len) || !utf8(cache_utf8, cache_len))
        return CLOUD_POLICY_MALFORMED;
    char *outer_arena = malloc(namespace_len + 1);
    if (outer_arena == NULL) return CLOUD_POLICY_NO_MEMORY;
    struct parser outer = {namespace_json, namespace_len, 0, 0, 0, 0, outer_arena, CLOUD_POLICY_OK};
    struct span policy = {NULL, 0};
    if (!namespace_value(&outer, &policy)) {
        enum cloud_policy_result result = outer.error;
        free(outer_arena);
        return result;
    }
    char *inner_arena = malloc(policy.size + 1);
    struct row *rows = calloc(CLOUD_POLICY_MAX_ROWS, sizeof(*rows));
    if (inner_arena == NULL || rows == NULL) {
        free(inner_arena); free(rows); free(outer_arena);
        return CLOUD_POLICY_NO_MEMORY;
    }
    struct parser inner = {policy.data, policy.size, 0, 0, 0, 0, inner_arena, CLOUD_POLICY_OK};
    size_t count = 0;
    if (!policy_rows(&inner, rows, &count, product_type)) {
        enum cloud_policy_result result = inner.error;
        free(rows); free(inner_arena); free(outer_arena);
        return result;
    }
    struct cloud_policy_summary result = {0, 0, 0, 0, 0, 0, -1, -1, -1};
    struct span default_data = {NULL, 0};
    int found_default = 0;
    result.row_count = (int)count;
    for (size_t i = 0; i < count; ++i) {
        if (literal(rows[i].country, "DEFAULT")) {
            ++result.default_row_count;
            if (!found_default) { default_data = rows[i].data; found_default = 1; }
        }
        for (size_t j = 0; j < i; ++j)
            if (equal(rows[i].country, rows[j].country)) { rows[i].duplicate = 1; break; }
        result.duplicate_row_count += rows[i].duplicate;
        if (!rows[i].duplicate) {
            ++result.effective_row_count;
            result.blocked_row_count += rows[i].blocked;
        }
    }
    struct span candidates[CLOUD_POLICY_MAX_ROWS + 1];
    size_t candidate_count = 0;
    if (default_data.size) candidates[candidate_count++] = default_data;
    for (size_t i = 0; i < count; ++i) {
        if (rows[i].duplicate) continue;
        struct span value = rows[i].blocked ? default_data : rows[i].data;
        if (value.size == 0) continue;
        size_t j = 0;
        while (j < candidate_count && !equal(value, candidates[j])) ++j;
        if (j == candidate_count) candidates[candidate_count++] = value;
    }
    result.nonempty_candidate_count = (int)candidate_count;
    if (cache_utf8 != NULL) {
        struct span cache = {cache_utf8, cache_len};
        result.receiver_match = receiver_type == 18 && receiver_index == 4;
        result.default_match = result.receiver_match && default_data.size != 0 && equal(default_data, cache);
        result.matching_candidate_count = 0;
        if (result.receiver_match)
            for (size_t i = 0; i < candidate_count; ++i)
                if (equal(candidates[i], cache)) result.matching_candidate_count = 1;
    }
    *out = result;
    free(rows); free(inner_arena); free(outer_arena);
    return CLOUD_POLICY_OK;
}
