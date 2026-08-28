#ifndef FINDUAS_EID_ROUTE_V22_RUNTIME_IDENTITY_H
#define FINDUAS_EID_ROUTE_V22_RUNTIME_IDENTITY_H

#include <stdint.h>

#include "identity_core.h"
#include "module_inspect.h"

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
    const FinduasModuleSet *modules,
    FinduasIdentityDiagnostic *diagnostic);

#endif
