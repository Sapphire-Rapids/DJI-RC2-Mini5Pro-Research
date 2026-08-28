#include "route_resolver.h"

#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "abi_shims.h"
#include "module_inspect.h"
#include "route_policy.h"
#include "runtime_identity.h"
#include "target_profile.h"

#define FINDUAS_TARGET_STRING_SIZE 24u
#define FINDUAS_CACHE_KEY_SIZE 0x50u
#define FINDUAS_CORE_HARDWARE_OFFSET 0x28u
#define FINDUAS_HARDWARE_PRIMARY_VPTR_OFFSET 0x00u
#define FINDUAS_HARDWARE_SECONDARY_VPTR_OFFSET 0x08u
#define FINDUAS_HARDWARE_PRIMARY_ADDRESS_POINT_OFFSET 0x10u
#define FINDUAS_HARDWARE_SECONDARY_ADDRESS_POINT_OFFSET 0x68u
#define FINDUAS_MIX139_ADDRESS_POINT_OFFSET 0x10u
#define FINDUAS_BASE_COMPONENT_TYPE_OFFSET 0x9cu
#define FINDUAS_BASE_READY_STATE_OFFSET 0xe9u

typedef struct FinduasPointerPair {
    void *object;
    void *control;
} FinduasPointerPair;

typedef struct FinduasOpaqueVector {
    const uint32_t *begin;
    const uint32_t *end;
    const uint32_t *capacity;
} FinduasOpaqueVector;

typedef void *(*FinduasWeakLock)(void *control);
typedef void (*FinduasReleaseOwner)(void *control);
typedef void (*FinduasStringInit)(void *storage, const char *text, size_t length);
typedef void (*FinduasDestructor)(void *storage);
typedef const void *(*FinduasGetPrefixes)(const void *cache_key);
typedef void *(*FinduasGetCharacteristics)(void *abstraction, const void *cache_key);
typedef uint32_t (*FinduasScalarGetter)(const void *abstraction);

typedef struct FinduasTargetApi {
    void *symbols[FINDUAS_TARGET_SYMBOL_COUNT];
} FinduasTargetApi;

/*
 * This exact artifact deliberately cannot cross the target-libc++ exception boundary.  The
 * target-owned string and CacheKey construction path is present below for source/ABI review, but
 * the only live carrier has this private, non-exported, write-free gate fixed to zero.  There is no
 * option, environment variable, JNI method, component, DEX, or exported setter that can change it.
 */
static const volatile uint32_t g_exception_boundary_admitted = 0u;

__attribute__((noinline)) static int route_exception_boundary_admitted(void) {
    return g_exception_boundary_admitted == 1u;
}

static void *add_pointer(void *base, uintptr_t offset) {
    const uintptr_t value = (uintptr_t)base;
    if (value > UINTPTR_MAX - offset) {
        return NULL;
    }
    return (void *)(value + offset);
}

static enum FinduasRouteStatus resolve_target_api(
    const FinduasModuleSet *modules,
    FinduasTargetApi *api,
    FinduasRouteDiagnostic *diagnostic) {
    memset(api, 0, sizeof(*api));
    for (int index = 0; index < FINDUAS_TARGET_SYMBOL_COUNT; ++index) {
        const enum FinduasModuleError error = finduas_resolve_exact_symbol(
            modules,
            &kFinduasSymbolProfiles[index],
            &api->symbols[index]);
        if (error != FINDUAS_MODULE_ERROR_NONE) {
            diagnostic->module_error = (uint32_t)error;
            return FINDUAS_ROUTE_STATUS_SYMBOL_VALIDATION_FAILED;
        }
        ++diagnostic->validated_symbol_count;
    }
    return FINDUAS_ROUTE_STATUS_NONE;
}

static int pointer_pair_is_full(const FinduasPointerPair *pair) {
    return pair != NULL && pair->object != NULL && pair->control != NULL;
}

static int decode_exact_prefix_vector(
    const void *opaque_vector,
    const FinduasSemanticTuple *semantic,
    const uint32_t **prefixes,
    size_t *prefix_count) {
    if (opaque_vector == NULL || semantic == NULL || prefixes == NULL || prefix_count == NULL) {
        return 0;
    }
    const FinduasOpaqueVector *vector = (const FinduasOpaqueVector *)opaque_vector;
    const uintptr_t begin = (uintptr_t)vector->begin;
    const uintptr_t end = (uintptr_t)vector->end;
    const uintptr_t capacity = (uintptr_t)vector->capacity;
    if (begin == 0u || end < begin || capacity < end ||
        ((end - begin) % sizeof(uint32_t)) != 0u ||
        ((capacity - begin) % sizeof(uint32_t)) != 0u) {
        return 0;
    }
    const size_t count = (size_t)((end - begin) / sizeof(uint32_t));
    const size_t capacity_count = (size_t)((capacity - begin) / sizeof(uint32_t));
    if (count != 3u || capacity_count < count || capacity_count > 16u ||
        !finduas_prefixes_are_exact(vector->begin, count, semantic)) {
        return 0;
    }
    *prefixes = vector->begin;
    *prefix_count = count;
    return 1;
}

static enum FinduasRouteStatus run_admitted_route_calls(
    const FinduasTargetApi *api,
    FinduasRouteDiagnostic *diagnostic) {
    const FinduasSemanticTuple semantic = {
        FINDUAS_EID_PRODUCT_ID,
        FINDUAS_EID_COMPONENT_TYPE,
        FINDUAS_EID_COMPONENT_INDEX,
        FINDUAS_EID_IGNORE_SENTINEL,
        FINDUAS_EID_IGNORE_SENTINEL,
    };
    _Alignas(8) uint8_t target_string[FINDUAS_TARGET_STRING_SIZE] = {0};
    _Alignas(8) uint8_t cache_key[FINDUAS_CACHE_KEY_SIZE] = {0};
    FinduasPointerPair framework_weak = {NULL, NULL};
    FinduasPointerPair framework_strong = {NULL, NULL};
    FinduasPointerPair abstraction_before = {NULL, NULL};
    FinduasPointerPair abstraction_after = {NULL, NULL};
    const uint32_t *prefixes = NULL;
    size_t prefix_count = 0u;
    enum FinduasRouteStatus status = FINDUAS_ROUTE_STATUS_NONE;
    int framework_weak_pending = 0;
    int framework_strong_pending = 0;
    int string_pending = 0;
    int cache_key_pending = 0;
    int abstraction_before_pending = 0;
    int abstraction_after_pending = 0;

    FinduasWeakLock weak_lock = (FinduasWeakLock)api->symbols[FINDUAS_SYMBOL_WEAK_LOCK];
    FinduasReleaseOwner release_shared =
        (FinduasReleaseOwner)api->symbols[FINDUAS_SYMBOL_RELEASE_SHARED];
    FinduasReleaseOwner release_weak =
        (FinduasReleaseOwner)api->symbols[FINDUAS_SYMBOL_RELEASE_WEAK];
    FinduasStringInit string_init =
        (FinduasStringInit)api->symbols[FINDUAS_SYMBOL_STRING_INIT];
    FinduasDestructor string_dtor =
        (FinduasDestructor)api->symbols[FINDUAS_SYMBOL_STRING_DTOR];
    FinduasDestructor cache_key_dtor =
        (FinduasDestructor)api->symbols[FINDUAS_SYMBOL_CACHE_KEY_DTOR];
    FinduasGetPrefixes get_prefixes =
        (FinduasGetPrefixes)api->symbols[FINDUAS_SYMBOL_CACHE_KEY_GET_PREFIXES];
    FinduasGetCharacteristics get_characteristics =
        (FinduasGetCharacteristics)api->symbols[FINDUAS_SYMBOL_GET_CHARACTERISTICS];
    FinduasScalarGetter get_device_id =
        (FinduasScalarGetter)api->symbols[FINDUAS_SYMBOL_GET_DEVICE_ID];
    FinduasScalarGetter get_product_id =
        (FinduasScalarGetter)api->symbols[FINDUAS_SYMBOL_GET_PRODUCT_ID];
    FinduasScalarGetter get_abstraction_id =
        (FinduasScalarGetter)api->symbols[FINDUAS_SYMBOL_GET_ABSTRACTION_ID];
    FinduasScalarGetter get_component_index =
        (FinduasScalarGetter)api->symbols[FINDUAS_SYMBOL_GET_COMPONENT_INDEX];

    diagnostic->semantic_tuple_validated =
        (uint32_t)finduas_semantic_tuple_is_exact(&semantic);
    if (diagnostic->semantic_tuple_validated == 0u) {
        status = FINDUAS_ROUTE_STATUS_PREFIX_INVALID;
        goto cleanup;
    }

    void *mediator = NULL;
    memcpy(
        &mediator,
        api->symbols[FINDUAS_SYMBOL_GLOBAL_MEDIATOR],
        sizeof(mediator));
    diagnostic->mediator_present = mediator != NULL ? 1u : 0u;
    if (mediator == NULL) {
        status = FINDUAS_ROUTE_STATUS_MEDIATOR_ABSENT;
        goto cleanup;
    }

    finduas_call_sret_member0(
        api->symbols[FINDUAS_SYMBOL_GET_FRAMEWORK_CORE],
        &framework_weak,
        mediator);
    if (framework_weak.control != NULL) {
        framework_weak_pending = 1;
        ++diagnostic->acquired_weak_count;
    }
    if (!pointer_pair_is_full(&framework_weak)) {
        status = FINDUAS_ROUTE_STATUS_FRAMEWORK_WEAK_INVALID;
        goto cleanup;
    }

    framework_strong.control = weak_lock(framework_weak.control);
    if (framework_strong.control == NULL ||
        framework_strong.control != framework_weak.control) {
        /*
         * The target lock contract can return only this control block or NULL.  Do not call a
         * virtual refcount release on an unexpected pointer: a corrupted return must fail closed,
         * not turn an impossible ownership state into an arbitrary indirect call.
         */
        framework_strong.control = NULL;
        status = FINDUAS_ROUTE_STATUS_FRAMEWORK_LOCK_FAILED;
        goto cleanup;
    }
    framework_strong.object = framework_weak.object;
    framework_strong_pending = 1;
    ++diagnostic->acquired_shared_count;
    release_weak(framework_weak.control);
    framework_weak_pending = 0;
    ++diagnostic->released_weak_count;
    diagnostic->framework_pinned = 1u;

    void *hardware_slot = add_pointer(framework_strong.object, FINDUAS_CORE_HARDWARE_OFFSET);
    void *hardware = NULL;
    if (hardware_slot != NULL) {
        memcpy(&hardware, hardware_slot, sizeof(hardware));
    }
    if (hardware == NULL || ((uintptr_t)hardware & (sizeof(void *) - 1u)) != 0u) {
        status = FINDUAS_ROUTE_STATUS_HARDWARE_INVALID;
        goto cleanup;
    }

    void *hardware_primary_vptr = NULL;
    void *hardware_secondary_vptr = NULL;
    memcpy(
        &hardware_primary_vptr,
        add_pointer(hardware, FINDUAS_HARDWARE_PRIMARY_VPTR_OFFSET),
        sizeof(hardware_primary_vptr));
    memcpy(
        &hardware_secondary_vptr,
        add_pointer(hardware, FINDUAS_HARDWARE_SECONDARY_VPTR_OFFSET),
        sizeof(hardware_secondary_vptr));
    void *expected_primary_vptr = add_pointer(
        api->symbols[FINDUAS_SYMBOL_HARDWARE_VTABLE],
        FINDUAS_HARDWARE_PRIMARY_ADDRESS_POINT_OFFSET);
    void *expected_secondary_vptr = add_pointer(
        api->symbols[FINDUAS_SYMBOL_HARDWARE_VTABLE],
        FINDUAS_HARDWARE_SECONDARY_ADDRESS_POINT_OFFSET);
    if (hardware_primary_vptr != expected_primary_vptr ||
        hardware_secondary_vptr != expected_secondary_vptr) {
        status = FINDUAS_ROUTE_STATUS_HARDWARE_INVALID;
        goto cleanup;
    }
    diagnostic->hardware_validated = 1u;

    string_init(
        target_string,
        FINDUAS_EID_IDENTIFIER,
        FINDUAS_EID_IDENTIFIER_LENGTH);
    string_pending = 1;
    ++diagnostic->initialized_string_count;

    finduas_call_sret_core_get_key(
        api->symbols[FINDUAS_SYMBOL_CORE_GET_KEY],
        cache_key,
        framework_strong.object,
        semantic.product_id,
        semantic.component_type,
        semantic.component_index,
        semantic.subcomponent_type,
        semantic.subcomponent_index,
        target_string);
    cache_key_pending = 1;
    ++diagnostic->initialized_cache_key_count;

    const void *prefix_vector = get_prefixes(cache_key);
    if (!decode_exact_prefix_vector(
            prefix_vector,
            &semantic,
            &prefixes,
            &prefix_count)) {
        status = FINDUAS_ROUTE_STATUS_PREFIX_INVALID;
        goto cleanup;
    }
    diagnostic->prefixes_validated = 1u;

    finduas_call_sret_get_abstraction(
        api->symbols[FINDUAS_SYMBOL_HARDWARE_GET_ABSTRACTION],
        &abstraction_before,
        hardware,
        prefix_vector);
    if (abstraction_before.control != NULL) {
        abstraction_before_pending = 1;
        ++diagnostic->acquired_shared_count;
    }
    if (!pointer_pair_is_full(&abstraction_before)) {
        status = FINDUAS_ROUTE_STATUS_ABSTRACTION_INVALID;
        goto cleanup;
    }

    void *abstraction_vptr = NULL;
    memcpy(&abstraction_vptr, abstraction_before.object, sizeof(abstraction_vptr));
    void *expected_mix_vptr = add_pointer(
        api->symbols[FINDUAS_SYMBOL_MIX139_VTABLE],
        FINDUAS_MIX139_ADDRESS_POINT_OFFSET);
    if (abstraction_vptr != expected_mix_vptr) {
        status = FINDUAS_ROUTE_STATUS_ABSTRACTION_INVALID;
        goto cleanup;
    }
    diagnostic->abstraction_type_validated = 1u;

    FinduasLiveRouteScalars scalars;
    memset(&scalars, 0, sizeof(scalars));
    scalars.product_id = get_product_id(abstraction_before.object);
    scalars.device_id = get_device_id(abstraction_before.object);
    scalars.abstraction_id = get_abstraction_id(abstraction_before.object);
    scalars.component_index = get_component_index(abstraction_before.object);
    memcpy(
        &scalars.component_type,
        add_pointer(abstraction_before.object, FINDUAS_BASE_COMPONENT_TYPE_OFFSET),
        sizeof(scalars.component_type));
    memcpy(
        &scalars.ready_state,
        add_pointer(abstraction_before.object, FINDUAS_BASE_READY_STATE_OFFSET),
        sizeof(scalars.ready_state));
    diagnostic->product_id = scalars.product_id;
    diagnostic->component_type = scalars.component_type;
    diagnostic->component_index = scalars.component_index;
    diagnostic->abstraction_id = scalars.abstraction_id;
    diagnostic->device_id = scalars.device_id;
    if (!finduas_live_route_scalars_match(
            &scalars,
            prefixes,
            prefix_count,
            &semantic)) {
        status = FINDUAS_ROUTE_STATUS_ROUTE_SCALAR_MISMATCH;
        goto cleanup;
    }

    void *characteristics_before =
        get_characteristics(abstraction_before.object, cache_key);
    const void *invalid_characteristics =
        api->symbols[FINDUAS_SYMBOL_CHARACTERISTICS_INVALID];
    if (characteristics_before == NULL ||
        characteristics_before == invalid_characteristics) {
        status = FINDUAS_ROUTE_STATUS_CHARACTERISTICS_INVALID;
        goto cleanup;
    }
    diagnostic->characteristics_present = 1u;

    finduas_call_sret_get_abstraction(
        api->symbols[FINDUAS_SYMBOL_HARDWARE_GET_ABSTRACTION],
        &abstraction_after,
        hardware,
        prefix_vector);
    if (abstraction_after.control != NULL) {
        abstraction_after_pending = 1;
        ++diagnostic->acquired_shared_count;
    }
    if (!pointer_pair_is_full(&abstraction_after) ||
        abstraction_after.object != abstraction_before.object ||
        abstraction_after.control != abstraction_before.control) {
        status = FINDUAS_ROUTE_STATUS_OWNER_CHANGED;
        goto cleanup;
    }
    void *characteristics_after =
        get_characteristics(abstraction_after.object, cache_key);
    if (characteristics_after == NULL ||
        characteristics_after == invalid_characteristics ||
        characteristics_after != characteristics_before) {
        status = FINDUAS_ROUTE_STATUS_OWNER_CHANGED;
        goto cleanup;
    }
    diagnostic->same_owner_before_after = 1u;
    status = FINDUAS_ROUTE_STATUS_RESOLVED;

cleanup:
    if (abstraction_after_pending) {
        release_shared(abstraction_after.control);
        ++diagnostic->released_shared_count;
    }
    if (abstraction_before_pending) {
        release_shared(abstraction_before.control);
        ++diagnostic->released_shared_count;
    }
    if (cache_key_pending) {
        cache_key_dtor(cache_key);
        ++diagnostic->destroyed_cache_key_count;
    }
    if (string_pending) {
        string_dtor(target_string);
        ++diagnostic->destroyed_string_count;
    }
    if (framework_strong_pending) {
        release_shared(framework_strong.control);
        ++diagnostic->released_shared_count;
    }
    if (framework_weak_pending) {
        release_weak(framework_weak.control);
        ++diagnostic->released_weak_count;
    }

    if (diagnostic->acquired_weak_count != diagnostic->released_weak_count ||
        diagnostic->acquired_shared_count != diagnostic->released_shared_count ||
        diagnostic->initialized_string_count != diagnostic->destroyed_string_count ||
        diagnostic->initialized_cache_key_count != diagnostic->destroyed_cache_key_count) {
        return FINDUAS_ROUTE_STATUS_LIFECYCLE_MISMATCH;
    }
    return status;
}

enum FinduasRouteStatus finduas_route_resolver_run(FinduasRouteDiagnostic *diagnostic) {
    if (diagnostic == NULL) {
        return FINDUAS_ROUTE_STATUS_MODULE_DISCOVERY_FAILED;
    }
    memset(diagnostic, 0, sizeof(*diagnostic));
    FinduasModuleSet modules;
    FinduasTargetApi api;
    memset(&modules, 0, sizeof(modules));
    memset(&api, 0, sizeof(api));

    enum FinduasModuleError module_error = finduas_modules_discover(&modules);
    diagnostic->module_error = (uint32_t)module_error;
    diagnostic->validated_module_count = modules.validated_module_count;
    if (module_error != FINDUAS_MODULE_ERROR_NONE) {
        diagnostic->status = FINDUAS_ROUTE_STATUS_MODULE_DISCOVERY_FAILED;
        return diagnostic->status;
    }

    module_error = finduas_modules_open_noload(&modules);
    diagnostic->module_error = (uint32_t)module_error;
    diagnostic->opened_handle_count = modules.opened_handle_count;
    if (module_error != FINDUAS_MODULE_ERROR_NONE) {
        diagnostic->status = FINDUAS_ROUTE_STATUS_MODULE_NOLOAD_FAILED;
        return diagnostic->status;
    }

    FinduasIdentityDiagnostic identity;
    memset(&identity, 0, sizeof(identity));
    const enum FinduasIdentityError identity_error =
        finduas_runtime_identity_verify(&modules, &identity);
    diagnostic->identity_error = (uint32_t)identity.error;
    diagnostic->identity_module_id = identity.module_id;
    diagnostic->identity_stage = identity.stage;
    diagnostic->identity_errno = identity.errno_value;
    diagnostic->identity_hashed_bytes = identity.hashed_bytes;
    diagnostic->identity_relevant_vma_count = identity.relevant_vma_count;
    diagnostic->identity_opened_fd_count = identity.opened_fd_count;
    diagnostic->identity_closed_fd_count = identity.closed_fd_count;
    diagnostic->identity_verified_module_count = identity.verified_module_count;
    if (identity_error != FINDUAS_IDENTITY_OK) {
        diagnostic->status = FINDUAS_ROUTE_STATUS_RUNTIME_IDENTITY_FAILED;
        finduas_modules_close(&modules);
        return diagnostic->status;
    }

    module_error = finduas_modules_finalize_verified(&modules);
    diagnostic->module_error = (uint32_t)module_error;
    if (module_error != FINDUAS_MODULE_ERROR_NONE) {
        diagnostic->status = FINDUAS_ROUTE_STATUS_MODULE_DISCOVERY_FAILED;
        finduas_modules_close(&modules);
        return diagnostic->status;
    }

    enum FinduasRouteStatus status = resolve_target_api(&modules, &api, diagnostic);
    if (status != FINDUAS_ROUTE_STATUS_NONE) {
        diagnostic->status = status;
        finduas_modules_close(&modules);
        return diagnostic->status;
    }

    void *mediator = NULL;
    memcpy(
        &mediator,
        api.symbols[FINDUAS_SYMBOL_GLOBAL_MEDIATOR],
        sizeof(mediator));
    diagnostic->mediator_present = mediator != NULL ? 1u : 0u;
    if (mediator == NULL) {
        diagnostic->status = FINDUAS_ROUTE_STATUS_MEDIATOR_ABSENT;
        finduas_modules_close(&modules);
        return diagnostic->status;
    }

    diagnostic->exception_boundary_admitted =
        route_exception_boundary_admitted() ? 1u : 0u;
    if (diagnostic->exception_boundary_admitted == 0u) {
        diagnostic->status = FINDUAS_ROUTE_STATUS_EXCEPTION_BOUNDARY_UNPROVEN;
        finduas_modules_close(&modules);
        return diagnostic->status;
    }

    status = run_admitted_route_calls(&api, diagnostic);
    diagnostic->status = status;
    finduas_modules_close(&modules);
    return diagnostic->status;
}
