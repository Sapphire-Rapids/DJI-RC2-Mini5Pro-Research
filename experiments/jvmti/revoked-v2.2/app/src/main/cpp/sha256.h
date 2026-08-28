#ifndef FINDUAS_EID_ROUTE_V22_SHA256_H
#define FINDUAS_EID_ROUTE_V22_SHA256_H

#include <stddef.h>
#include <stdint.h>

#define FINDUAS_SHA256_DIGEST_SIZE 32u

typedef struct FinduasSha256Context {
    uint32_t state[8];
    uint64_t total_bytes;
    uint8_t block[64];
    size_t block_size;
} FinduasSha256Context;

void finduas_sha256_init(FinduasSha256Context *context);
int finduas_sha256_update(
    FinduasSha256Context *context,
    const uint8_t *data,
    size_t size);
int finduas_sha256_finish(
    FinduasSha256Context *context,
    uint8_t digest[FINDUAS_SHA256_DIGEST_SIZE]);
int finduas_constant_time_equal(const uint8_t *left, const uint8_t *right, size_t size);

#endif
