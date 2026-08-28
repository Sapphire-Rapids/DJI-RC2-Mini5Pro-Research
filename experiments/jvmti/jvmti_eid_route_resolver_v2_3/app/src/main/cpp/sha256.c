#include "sha256.h"

#include <limits.h>
#include <string.h>

static const uint32_t kRoundConstants[64] = {
    0x428a2f98u, 0x71374491u, 0xb5c0fbcfu, 0xe9b5dba5u,
    0x3956c25bu, 0x59f111f1u, 0x923f82a4u, 0xab1c5ed5u,
    0xd807aa98u, 0x12835b01u, 0x243185beu, 0x550c7dc3u,
    0x72be5d74u, 0x80deb1feu, 0x9bdc06a7u, 0xc19bf174u,
    0xe49b69c1u, 0xefbe4786u, 0x0fc19dc6u, 0x240ca1ccu,
    0x2de92c6fu, 0x4a7484aau, 0x5cb0a9dcu, 0x76f988dau,
    0x983e5152u, 0xa831c66du, 0xb00327c8u, 0xbf597fc7u,
    0xc6e00bf3u, 0xd5a79147u, 0x06ca6351u, 0x14292967u,
    0x27b70a85u, 0x2e1b2138u, 0x4d2c6dfcu, 0x53380d13u,
    0x650a7354u, 0x766a0abbu, 0x81c2c92eu, 0x92722c85u,
    0xa2bfe8a1u, 0xa81a664bu, 0xc24b8b70u, 0xc76c51a3u,
    0xd192e819u, 0xd6990624u, 0xf40e3585u, 0x106aa070u,
    0x19a4c116u, 0x1e376c08u, 0x2748774cu, 0x34b0bcb5u,
    0x391c0cb3u, 0x4ed8aa4au, 0x5b9cca4fu, 0x682e6ff3u,
    0x748f82eeu, 0x78a5636fu, 0x84c87814u, 0x8cc70208u,
    0x90befffau, 0xa4506cebu, 0xbef9a3f7u, 0xc67178f2u,
};

static uint32_t rotate_right(uint32_t value, unsigned int shift) {
    return (value >> shift) | (value << (32u - shift));
}

static uint32_t load_big_endian_u32(const uint8_t *input) {
    return ((uint32_t)input[0] << 24u) |
           ((uint32_t)input[1] << 16u) |
           ((uint32_t)input[2] << 8u) |
           (uint32_t)input[3];
}

static void store_big_endian_u32(uint8_t *output, uint32_t value) {
    output[0] = (uint8_t)(value >> 24u);
    output[1] = (uint8_t)(value >> 16u);
    output[2] = (uint8_t)(value >> 8u);
    output[3] = (uint8_t)value;
}

static void compress_block(FinduasSha256Context *context, const uint8_t block[64]) {
    uint32_t schedule[64];
    for (size_t index = 0; index < 16u; ++index) {
        schedule[index] = load_big_endian_u32(block + (index * 4u));
    }
    for (size_t index = 16u; index < 64u; ++index) {
        const uint32_t left = schedule[index - 15u];
        const uint32_t right = schedule[index - 2u];
        const uint32_t sigma0 =
            rotate_right(left, 7u) ^ rotate_right(left, 18u) ^ (left >> 3u);
        const uint32_t sigma1 =
            rotate_right(right, 17u) ^ rotate_right(right, 19u) ^ (right >> 10u);
        schedule[index] =
            schedule[index - 16u] + sigma0 + schedule[index - 7u] + sigma1;
    }

    uint32_t a = context->state[0];
    uint32_t b = context->state[1];
    uint32_t c = context->state[2];
    uint32_t d = context->state[3];
    uint32_t e = context->state[4];
    uint32_t f = context->state[5];
    uint32_t g = context->state[6];
    uint32_t h = context->state[7];
    for (size_t index = 0; index < 64u; ++index) {
        const uint32_t sum1 =
            rotate_right(e, 6u) ^ rotate_right(e, 11u) ^ rotate_right(e, 25u);
        const uint32_t choose = (e & f) ^ ((~e) & g);
        const uint32_t temporary1 =
            h + sum1 + choose + kRoundConstants[index] + schedule[index];
        const uint32_t sum0 =
            rotate_right(a, 2u) ^ rotate_right(a, 13u) ^ rotate_right(a, 22u);
        const uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
        const uint32_t temporary2 = sum0 + majority;
        h = g;
        g = f;
        f = e;
        e = d + temporary1;
        d = c;
        c = b;
        b = a;
        a = temporary1 + temporary2;
    }
    context->state[0] += a;
    context->state[1] += b;
    context->state[2] += c;
    context->state[3] += d;
    context->state[4] += e;
    context->state[5] += f;
    context->state[6] += g;
    context->state[7] += h;
    memset(schedule, 0, sizeof(schedule));
}

void finduas_sha256_init(FinduasSha256Context *context) {
    if (context == NULL) {
        return;
    }
    memset(context, 0, sizeof(*context));
    context->state[0] = 0x6a09e667u;
    context->state[1] = 0xbb67ae85u;
    context->state[2] = 0x3c6ef372u;
    context->state[3] = 0xa54ff53au;
    context->state[4] = 0x510e527fu;
    context->state[5] = 0x9b05688cu;
    context->state[6] = 0x1f83d9abu;
    context->state[7] = 0x5be0cd19u;
}

int finduas_sha256_update(
    FinduasSha256Context *context,
    const uint8_t *data,
    size_t size) {
    if (context == NULL || (size != 0u && data == NULL) ||
        (uint64_t)size > UINT64_MAX - context->total_bytes) {
        return 0;
    }
    context->total_bytes += (uint64_t)size;
    while (size != 0u) {
        const size_t remaining = sizeof(context->block) - context->block_size;
        const size_t copied = size < remaining ? size : remaining;
        memcpy(context->block + context->block_size, data, copied);
        context->block_size += copied;
        data += copied;
        size -= copied;
        if (context->block_size == sizeof(context->block)) {
            compress_block(context, context->block);
            context->block_size = 0u;
        }
    }
    return 1;
}

int finduas_sha256_finish(
    FinduasSha256Context *context,
    uint8_t digest[FINDUAS_SHA256_DIGEST_SIZE]) {
    if (context == NULL || digest == NULL ||
        context->total_bytes > UINT64_MAX / 8u || context->block_size >= 64u) {
        return 0;
    }
    const uint64_t total_bits = context->total_bytes * 8u;
    context->block[context->block_size++] = 0x80u;
    if (context->block_size > 56u) {
        memset(context->block + context->block_size, 0, 64u - context->block_size);
        compress_block(context, context->block);
        context->block_size = 0u;
    }
    memset(context->block + context->block_size, 0, 56u - context->block_size);
    for (size_t index = 0; index < 8u; ++index) {
        context->block[63u - index] = (uint8_t)(total_bits >> (index * 8u));
    }
    compress_block(context, context->block);
    for (size_t index = 0; index < 8u; ++index) {
        store_big_endian_u32(digest + index * 4u, context->state[index]);
    }
    memset(context, 0, sizeof(*context));
    return 1;
}

int finduas_constant_time_equal(const uint8_t *left, const uint8_t *right, size_t size) {
    if ((size != 0u && (left == NULL || right == NULL))) {
        return 0;
    }
    uint8_t difference = 0u;
    for (size_t index = 0; index < size; ++index) {
        difference |= (uint8_t)(left[index] ^ right[index]);
    }
    return difference == 0u;
}
