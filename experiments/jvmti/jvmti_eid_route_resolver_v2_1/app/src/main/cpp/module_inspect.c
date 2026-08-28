#include "module_inspect.h"

#include <dlfcn.h>
#include <elf.h>
#include <link.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "note_parser.h"

#if !defined(RTLD_NOLOAD)
#error "RTLD_NOLOAD is required for the route resolver"
#endif

typedef struct FinduasScanContext {
    FinduasModuleSet *set;
    enum FinduasModuleError error;
} FinduasScanContext;

static int add_uintptr(uintptr_t left, uintptr_t right, uintptr_t *output) {
    if (left > UINTPTR_MAX - right) {
        return 0;
    }
    *output = left + right;
    return 1;
}

static const char *find_basename(const char *path) {
    if (path == NULL) {
        return NULL;
    }
    const char *basename = path;
    for (const char *cursor = path; *cursor != '\0'; ++cursor) {
        if (*cursor == '/') {
            basename = cursor + 1;
        }
    }
    return basename;
}

static int exact_text_equal(const char *left, const char *right) {
    if (left == NULL || right == NULL) {
        return 0;
    }
    while (*left != '\0' && *right != '\0') {
        if (*left != *right) {
            return 0;
        }
        ++left;
        ++right;
    }
    return *left == '\0' && *right == '\0';
}

static int copy_path_exact(const char *path, char *output, size_t capacity, size_t *length) {
    if (path == NULL || output == NULL || capacity == 0u || length == NULL) {
        return 0;
    }
    size_t index = 0;
    while (path[index] != '\0') {
        if (index + 1u >= capacity) {
            return 0;
        }
        output[index] = path[index];
        ++index;
    }
    if (index == 0u) {
        return 0;
    }
    output[index] = '\0';
    *length = index;
    return 1;
}

int finduas_module_range_contains(
    const FinduasLoadedModule *module,
    uintptr_t address,
    size_t length,
    uint32_t required_flags) {
    if (module == NULL || length == 0u || address > UINTPTR_MAX - length) {
        return 0;
    }
    const uintptr_t end = address + length;
    for (size_t index = 0; index < module->segment_count; ++index) {
        const FinduasLoadSegment *segment = &module->segments[index];
        if ((segment->flags & required_flags) == required_flags &&
            address >= segment->start && end <= segment->end) {
            return 1;
        }
    }
    return 0;
}

static int profile_id_for_basename(const char *basename) {
    for (int index = 0; index < FINDUAS_MODULE_COUNT; ++index) {
        if (exact_text_equal(basename, kFinduasModuleProfiles[index].basename)) {
            return index;
        }
    }
    return -1;
}

static int inspect_matching_module(
    const struct dl_phdr_info *info,
    FinduasLoadedModule *module,
    enum FinduasModuleError *error) {
    if (!copy_path_exact(
            info->dlpi_name,
            module->path,
            sizeof(module->path),
            &module->path_length)) {
        *error = FINDUAS_MODULE_ERROR_PATH;
        return 0;
    }

    module->base = (uintptr_t)info->dlpi_addr;
    if (module->base == 0u || info->dlpi_phdr == NULL || info->dlpi_phnum == 0u) {
        *error = FINDUAS_MODULE_ERROR_SEGMENTS;
        return 0;
    }

    for (ElfW(Half) index = 0; index < info->dlpi_phnum; ++index) {
        const ElfW(Phdr) *header = &info->dlpi_phdr[index];
        if (header->p_type != PT_LOAD || header->p_memsz == 0u) {
            continue;
        }
        if (module->segment_count >= FINDUAS_MODULE_SEGMENT_CAPACITY) {
            *error = FINDUAS_MODULE_ERROR_SEGMENTS;
            return 0;
        }
        uintptr_t start = 0;
        uintptr_t end = 0;
        if (!add_uintptr(module->base, (uintptr_t)header->p_vaddr, &start) ||
            !add_uintptr(start, (uintptr_t)header->p_memsz, &end) || end <= start) {
            *error = FINDUAS_MODULE_ERROR_SEGMENTS;
            return 0;
        }
        module->segments[module->segment_count++] =
            (FinduasLoadSegment){start, end, (uint32_t)header->p_flags};
    }
    if (module->segment_count == 0u) {
        *error = FINDUAS_MODULE_ERROR_SEGMENTS;
        return 0;
    }

    for (ElfW(Half) index = 0; index < info->dlpi_phnum; ++index) {
        const ElfW(Phdr) *header = &info->dlpi_phdr[index];
        if (header->p_type != PT_NOTE || header->p_memsz == 0u) {
            continue;
        }
        uintptr_t note_address = 0;
        if (!add_uintptr(module->base, (uintptr_t)header->p_vaddr, &note_address) ||
            header->p_memsz > SIZE_MAX ||
            !finduas_module_range_contains(
                module,
                note_address,
                (size_t)header->p_memsz,
                PF_R)) {
            *error = FINDUAS_MODULE_ERROR_BUILD_ID;
            return 0;
        }

        uint8_t build_id[FINDUAS_GNU_BUILD_ID_SIZE] = {0};
        if (!finduas_parse_unique_gnu_build_id(
                (const uint8_t *)note_address,
                (size_t)header->p_memsz,
                build_id) ||
            module->build_id_count != 0u) {
            *error = FINDUAS_MODULE_ERROR_BUILD_ID;
            return 0;
        }
        memcpy(module->build_id, build_id, sizeof(module->build_id));
        ++module->build_id_count;
    }

    if (module->build_id_count != 1u) {
        *error = FINDUAS_MODULE_ERROR_BUILD_ID;
        return 0;
    }
    return 1;
}

static int scan_callback(struct dl_phdr_info *info, size_t size, void *opaque) {
    (void)size;
    FinduasScanContext *context = (FinduasScanContext *)opaque;
    if (context->error != FINDUAS_MODULE_ERROR_NONE) {
        return 1;
    }
    const char *basename = find_basename(info->dlpi_name);
    const int profile_id = profile_id_for_basename(basename);
    if (profile_id < 0) {
        return 0;
    }

    FinduasLoadedModule *module = &context->set->modules[profile_id];
    ++module->match_count;
    if (module->match_count != 1u) {
        context->error = FINDUAS_MODULE_ERROR_CARDINALITY;
        return 1;
    }
    if (!inspect_matching_module(info, module, &context->error)) {
        return 1;
    }
    return 0;
}

enum FinduasModuleError finduas_modules_discover(FinduasModuleSet *set) {
    if (set == NULL) {
        return FINDUAS_MODULE_ERROR_ITERATION;
    }
    memset(set, 0, sizeof(*set));
    FinduasScanContext context = {set, FINDUAS_MODULE_ERROR_NONE};
    const int iteration_result = dl_iterate_phdr(scan_callback, &context);
    if (context.error != FINDUAS_MODULE_ERROR_NONE) {
        return context.error;
    }
    if (iteration_result != 0) {
        return FINDUAS_MODULE_ERROR_ITERATION;
    }

    for (int index = 0; index < FINDUAS_MODULE_COUNT; ++index) {
        FinduasLoadedModule *module = &set->modules[index];
        if (module->match_count != 1u) {
            return FINDUAS_MODULE_ERROR_CARDINALITY;
        }
        if (module->build_id_count != 1u ||
            memcmp(
                module->build_id,
                kFinduasModuleProfiles[index].build_id,
                FINDUAS_GNU_BUILD_ID_SIZE) != 0) {
            return FINDUAS_MODULE_ERROR_BUILD_ID;
        }
        ++set->validated_module_count;
    }
    return FINDUAS_MODULE_ERROR_NONE;
}

enum FinduasModuleError finduas_modules_open_noload(FinduasModuleSet *set) {
    if (set == NULL || set->validated_module_count != FINDUAS_MODULE_COUNT) {
        return FINDUAS_MODULE_ERROR_NOLOAD;
    }
    for (int index = 0; index < FINDUAS_MODULE_COUNT; ++index) {
        FinduasLoadedModule *module = &set->modules[index];
        (void)dlerror();
        module->handle = dlopen(module->path, RTLD_NOW | RTLD_NOLOAD);
        const char *error = dlerror();
        if (module->handle == NULL || error != NULL) {
            finduas_modules_close(set);
            return FINDUAS_MODULE_ERROR_NOLOAD;
        }
        ++set->opened_handle_count;
    }
    return FINDUAS_MODULE_ERROR_NONE;
}

void finduas_modules_close(FinduasModuleSet *set) {
    if (set == NULL) {
        return;
    }
    for (int index = FINDUAS_MODULE_COUNT - 1; index >= 0; --index) {
        if (set->modules[index].handle != NULL) {
            (void)dlclose(set->modules[index].handle);
            set->modules[index].handle = NULL;
        }
    }
    set->opened_handle_count = 0u;
}

enum FinduasModuleError finduas_resolve_exact_symbol(
    const FinduasModuleSet *set,
    const FinduasSymbolProfile *profile,
    void **output) {
    if (set == NULL || profile == NULL || output == NULL ||
        profile->module_id < 0 || profile->module_id >= FINDUAS_MODULE_COUNT) {
        return FINDUAS_MODULE_ERROR_DLSYM;
    }
    *output = NULL;
    const FinduasLoadedModule *module = &set->modules[profile->module_id];
    if (module->handle == NULL) {
        return FINDUAS_MODULE_ERROR_DLSYM;
    }

    if (profile->symbol_size == 0u ||
        (profile->kind == FINDUAS_SYMBOL_FUNCTION &&
         (profile->signature_size == 0u ||
          profile->signature_size > profile->symbol_size ||
          profile->signature_size > FINDUAS_INSTRUCTION_SIGNATURE_SIZE)) ||
        (profile->kind == FINDUAS_SYMBOL_OBJECT && profile->signature_size != 0u)) {
        return FINDUAS_MODULE_ERROR_SIGNATURE;
    }

    (void)dlerror();
    void *symbol = dlsym(module->handle, profile->name);
    const char *symbol_error = dlerror();
    if (symbol == NULL || symbol_error != NULL) {
        return FINDUAS_MODULE_ERROR_DLSYM;
    }

    Dl_info address_info;
    memset(&address_info, 0, sizeof(address_info));
    if (dladdr(symbol, &address_info) == 0 ||
        (uintptr_t)address_info.dli_fbase != module->base) {
        return FINDUAS_MODULE_ERROR_DLADDR;
    }

    uintptr_t expected_address = 0;
    if (!add_uintptr(module->base, profile->expected_rva, &expected_address) ||
        (uintptr_t)symbol != expected_address) {
        return FINDUAS_MODULE_ERROR_RVA;
    }

    const uint32_t required_flags =
        profile->kind == FINDUAS_SYMBOL_FUNCTION ? (PF_R | PF_X) : PF_R;
    if (!finduas_module_range_contains(
            module,
            expected_address,
            profile->symbol_size,
            required_flags)) {
        return FINDUAS_MODULE_ERROR_RANGE;
    }
    if (profile->kind == FINDUAS_SYMBOL_FUNCTION &&
        memcmp(
            symbol,
            profile->instruction_signature,
            profile->signature_size) != 0) {
        return FINDUAS_MODULE_ERROR_SIGNATURE;
    }

    *output = symbol;
    return FINDUAS_MODULE_ERROR_NONE;
}
