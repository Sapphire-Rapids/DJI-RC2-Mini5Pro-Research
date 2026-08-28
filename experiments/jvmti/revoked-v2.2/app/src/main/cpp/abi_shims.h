#ifndef FINDUAS_EID_ROUTE_V22_ABI_SHIMS_H
#define FINDUAS_EID_ROUTE_V22_ABI_SHIMS_H

#include <stdint.h>

#if !defined(__aarch64__)
#error "FindUAS EID route resolver V2.2 ABI shims require AArch64"
#endif

void finduas_call_sret_member0(void *function, void *output, void *self);

void finduas_call_sret_core_get_key(
    void *function,
    void *output,
    void *self,
    uint32_t product_id,
    uint32_t component_type,
    uint32_t component_index,
    uint32_t subcomponent_type,
    uint32_t subcomponent_index,
    const void *target_string);

void finduas_call_sret_get_abstraction(
    void *function,
    void *output,
    void *hardware_layer,
    const void *prefix_vector);

#endif
