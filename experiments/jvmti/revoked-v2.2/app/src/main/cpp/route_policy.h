#ifndef FINDUAS_EID_ROUTE_V22_ROUTE_POLICY_H
#define FINDUAS_EID_ROUTE_V22_ROUTE_POLICY_H

#include <stddef.h>
#include <stdint.h>

#define FINDUAS_EID_IDENTIFIER "EIDSwitch"
#define FINDUAS_EID_IDENTIFIER_LENGTH 9u
#define FINDUAS_EID_PRODUCT_ID 0u
#define FINDUAS_EID_COMPONENT_TYPE 4u
#define FINDUAS_EID_COMPONENT_INDEX 0u
#define FINDUAS_EID_IGNORE_SENTINEL 65534u

typedef struct FinduasSemanticTuple {
    uint32_t product_id;
    uint32_t component_type;
    uint32_t component_index;
    uint32_t subcomponent_type;
    uint32_t subcomponent_index;
} FinduasSemanticTuple;

typedef struct FinduasLiveRouteScalars {
    uint32_t product_id;
    uint32_t component_type;
    uint32_t component_index;
    uint32_t abstraction_id;
    uint32_t device_id;
    uint8_t ready_state;
} FinduasLiveRouteScalars;

int finduas_semantic_tuple_is_exact(const FinduasSemanticTuple *tuple);

int finduas_prefixes_are_exact(
    const uint32_t *prefixes,
    size_t prefix_count,
    const FinduasSemanticTuple *tuple);

int finduas_live_route_scalars_match(
    const FinduasLiveRouteScalars *route,
    const uint32_t *prefixes,
    size_t prefix_count,
    const FinduasSemanticTuple *tuple);

#endif
