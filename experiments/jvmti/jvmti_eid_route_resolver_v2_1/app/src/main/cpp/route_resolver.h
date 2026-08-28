#ifndef FINDUAS_EID_ROUTE_V21_ROUTE_RESOLVER_H
#define FINDUAS_EID_ROUTE_V21_ROUTE_RESOLVER_H

#include <stdint.h>

enum FinduasRouteStatus {
    FINDUAS_ROUTE_STATUS_NONE = 0,
    FINDUAS_ROUTE_STATUS_MODULE_DISCOVERY_FAILED = 1,
    FINDUAS_ROUTE_STATUS_MODULE_NOLOAD_FAILED = 2,
    FINDUAS_ROUTE_STATUS_SYMBOL_VALIDATION_FAILED = 3,
    FINDUAS_ROUTE_STATUS_MEDIATOR_ABSENT = 4,
    FINDUAS_ROUTE_STATUS_EXCEPTION_BOUNDARY_UNPROVEN = 5,
    FINDUAS_ROUTE_STATUS_FRAMEWORK_WEAK_INVALID = 6,
    FINDUAS_ROUTE_STATUS_FRAMEWORK_LOCK_FAILED = 7,
    FINDUAS_ROUTE_STATUS_HARDWARE_INVALID = 8,
    FINDUAS_ROUTE_STATUS_PREFIX_INVALID = 9,
    FINDUAS_ROUTE_STATUS_ABSTRACTION_INVALID = 10,
    FINDUAS_ROUTE_STATUS_ROUTE_SCALAR_MISMATCH = 11,
    FINDUAS_ROUTE_STATUS_CHARACTERISTICS_INVALID = 12,
    FINDUAS_ROUTE_STATUS_OWNER_CHANGED = 13,
    FINDUAS_ROUTE_STATUS_LIFECYCLE_MISMATCH = 14,
    FINDUAS_ROUTE_STATUS_RESOLVED = 15,
};

typedef struct FinduasRouteDiagnostic {
    enum FinduasRouteStatus status;
    uint32_t module_error;
    uint32_t validated_module_count;
    uint32_t opened_handle_count;
    uint32_t validated_symbol_count;
    uint32_t mediator_present;
    uint32_t exception_boundary_admitted;
    uint32_t framework_pinned;
    uint32_t hardware_validated;
    uint32_t semantic_tuple_validated;
    uint32_t prefixes_validated;
    uint32_t abstraction_type_validated;
    uint32_t characteristics_present;
    uint32_t same_owner_before_after;
    uint32_t acquired_weak_count;
    uint32_t released_weak_count;
    uint32_t acquired_shared_count;
    uint32_t released_shared_count;
    uint32_t initialized_string_count;
    uint32_t destroyed_string_count;
    uint32_t initialized_cache_key_count;
    uint32_t destroyed_cache_key_count;
    uint32_t product_id;
    uint32_t component_type;
    uint32_t component_index;
    uint32_t abstraction_id;
    uint32_t device_id;
} FinduasRouteDiagnostic;

enum FinduasRouteStatus finduas_route_resolver_run(FinduasRouteDiagnostic *diagnostic);

#endif
