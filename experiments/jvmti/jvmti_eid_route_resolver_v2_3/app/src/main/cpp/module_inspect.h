#ifndef FINDUAS_EID_ROUTE_V23_MODULE_INSPECT_H
#define FINDUAS_EID_ROUTE_V23_MODULE_INSPECT_H

#include <stddef.h>
#include <stdint.h>

#include "target_profile.h"

#define FINDUAS_MODULE_PATH_CAPACITY 4096u
#define FINDUAS_MODULE_SEGMENT_CAPACITY 8u

typedef struct FinduasLoadSegment {
    uintptr_t start;
    uintptr_t end;
    uint32_t flags;
} FinduasLoadSegment;

typedef struct FinduasLoadedModule {
    unsigned int match_count;
    uintptr_t base;
    char path[FINDUAS_MODULE_PATH_CAPACITY];
    size_t path_length;
    const void *runtime_phdr;
    uint16_t runtime_phnum;
    uint64_t linker_adds;
    uint64_t linker_subs;
    FinduasLoadSegment segments[FINDUAS_MODULE_SEGMENT_CAPACITY];
    size_t segment_count;
    uint8_t build_id[FINDUAS_GNU_BUILD_ID_SIZE];
    unsigned int build_id_count;
    void *handle;
} FinduasLoadedModule;

typedef struct FinduasModuleSet {
    FinduasLoadedModule modules[FINDUAS_MODULE_COUNT];
    unsigned int validated_module_count;
    unsigned int opened_handle_count;
    uint64_t linker_adds;
    uint64_t linker_subs;
    uint32_t identity_admission;
} FinduasModuleSet;

enum FinduasModuleError {
    FINDUAS_MODULE_ERROR_NONE = 0,
    FINDUAS_MODULE_ERROR_ITERATION = 1,
    FINDUAS_MODULE_ERROR_CARDINALITY = 2,
    FINDUAS_MODULE_ERROR_PATH = 3,
    FINDUAS_MODULE_ERROR_SEGMENTS = 4,
    FINDUAS_MODULE_ERROR_BUILD_ID = 5,
    FINDUAS_MODULE_ERROR_NOLOAD = 6,
    FINDUAS_MODULE_ERROR_DLSYM = 7,
    FINDUAS_MODULE_ERROR_DLADDR = 8,
    FINDUAS_MODULE_ERROR_RVA = 9,
    FINDUAS_MODULE_ERROR_RANGE = 10,
    FINDUAS_MODULE_ERROR_SIGNATURE = 11,
    FINDUAS_MODULE_ERROR_LINKER_EPOCH = 12,
};

enum FinduasModuleError finduas_modules_discover(FinduasModuleSet *set);
enum FinduasModuleError finduas_modules_open_noload(FinduasModuleSet *set);
enum FinduasModuleError finduas_modules_recheck(const FinduasModuleSet *set);
enum FinduasModuleError finduas_modules_admit_after_identity_recheck(
    FinduasModuleSet *set);
enum FinduasModuleError finduas_modules_finalize_verified(FinduasModuleSet *set);
void finduas_modules_close(FinduasModuleSet *set);

enum FinduasModuleError finduas_resolve_exact_symbol(
    const FinduasModuleSet *set,
    const FinduasSymbolProfile *profile,
    void **output);

int finduas_module_range_contains(
    const FinduasLoadedModule *module,
    uintptr_t address,
    size_t length,
    uint32_t required_flags);

#endif
