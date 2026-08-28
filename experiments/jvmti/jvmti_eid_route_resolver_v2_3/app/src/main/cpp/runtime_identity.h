#ifndef FINDUAS_EID_ROUTE_V23_RUNTIME_IDENTITY_H
#define FINDUAS_EID_ROUTE_V23_RUNTIME_IDENTITY_H

#include <stddef.h>
#include <stdint.h>

#include "identity_core.h"

/*
 * Deliberately narrower than FinduasModuleSet: the pre-epoch identity verifier
 * cannot name, load, or dereference dlpi_phdr/runtime ELF metadata.
 */
typedef struct FinduasIdentityModule {
    uintptr_t base;
    const char *path;
    size_t path_length;
} FinduasIdentityModule;

typedef struct FinduasIdentityModuleSet {
    FinduasIdentityModule modules[FINDUAS_MODULE_COUNT];
    uint32_t module_count;
    uint32_t noload_handle_count;
} FinduasIdentityModuleSet;

typedef struct FinduasIdentityDiagnostic {
    enum FinduasIdentityError error;
    uint32_t module_id;
    uint32_t stage;
    int32_t errno_value;
    uint64_t hashed_bytes;
    uint32_t relevant_vma_count;
    uint32_t opened_fd_count;
    uint32_t closed_fd_count;
    uint32_t verified_module_count;
} FinduasIdentityDiagnostic;

enum FinduasIdentityError finduas_runtime_identity_verify(
    const FinduasIdentityModuleSet *modules,
    FinduasIdentityDiagnostic *diagnostic);

#endif
