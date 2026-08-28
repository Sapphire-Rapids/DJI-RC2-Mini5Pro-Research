#include "route_policy.h"

#include <limits.h>

int finduas_semantic_tuple_is_exact(const FinduasSemanticTuple *tuple) {
    return tuple != NULL &&
           tuple->product_id == FINDUAS_EID_PRODUCT_ID &&
           tuple->component_type == FINDUAS_EID_COMPONENT_TYPE &&
           tuple->component_index == FINDUAS_EID_COMPONENT_INDEX &&
           tuple->subcomponent_type == FINDUAS_EID_IGNORE_SENTINEL &&
           tuple->subcomponent_index == FINDUAS_EID_IGNORE_SENTINEL;
}

int finduas_prefixes_are_exact(
    const uint32_t *prefixes,
    size_t prefix_count,
    const FinduasSemanticTuple *tuple) {
    return finduas_semantic_tuple_is_exact(tuple) &&
           prefixes != NULL &&
           prefix_count == 3u &&
           prefixes[0] == tuple->product_id &&
           prefixes[1] == tuple->component_type &&
           prefixes[2] == tuple->component_index;
}

int finduas_live_route_scalars_match(
    const FinduasLiveRouteScalars *route,
    const uint32_t *prefixes,
    size_t prefix_count,
    const FinduasSemanticTuple *tuple) {
    if (route == NULL ||
        !finduas_prefixes_are_exact(prefixes, prefix_count, tuple) ||
        route->product_id != tuple->product_id ||
        route->component_type != tuple->component_type ||
        route->component_index != tuple->component_index ||
        route->ready_state != 0u ||
        route->device_id > UINT16_MAX) {
        return 0;
    }

    if (route->device_id > (UINT32_MAX - route->abstraction_id) / 16u) {
        return 0;
    }
    return route->abstraction_id + (16u * route->device_id) == prefixes[2];
}
