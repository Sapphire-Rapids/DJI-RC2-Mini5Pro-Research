#ifndef FINDUAS_EID_ROUTE_V22_TARGET_PROFILE_H
#define FINDUAS_EID_ROUTE_V22_TARGET_PROFILE_H

#include <stddef.h>
#include <stdint.h>

#include "elf_profile.h"
#include "note_parser.h"

#define FINDUAS_INSTRUCTION_SIGNATURE_SIZE 16u
#define FINDUAS_SHA256_SIZE 32u
#define FINDUAS_ELF_HEADER_SIZE 64u
#define FINDUAS_PROFILE_PHDR_COUNT 7u

enum FinduasModuleSourceKind {
    FINDUAS_SOURCE_EXTRACTED_ELF_V1 = 1,
};

enum FinduasTargetModuleId {
    FINDUAS_MODULE_SDK_JNI = 0,
    FINDUAS_MODULE_SDK_KEY_VALUE = 1,
    FINDUAS_MODULE_SDK_BASE = 2,
    FINDUAS_MODULE_COUNT = 3,
};

enum FinduasSymbolKind {
    FINDUAS_SYMBOL_FUNCTION = 0,
    FINDUAS_SYMBOL_OBJECT = 1,
};

enum FinduasTargetSymbolId {
    FINDUAS_SYMBOL_GLOBAL_MEDIATOR = 0,
    FINDUAS_SYMBOL_GET_FRAMEWORK_CORE,
    FINDUAS_SYMBOL_CORE_GET_KEY,
    FINDUAS_SYMBOL_HARDWARE_GET_ABSTRACTION,
    FINDUAS_SYMBOL_GET_CHARACTERISTICS,
    FINDUAS_SYMBOL_GET_DEVICE_ID,
    FINDUAS_SYMBOL_GET_PRODUCT_ID,
    FINDUAS_SYMBOL_GET_ABSTRACTION_ID,
    FINDUAS_SYMBOL_GET_COMPONENT_INDEX,
    FINDUAS_SYMBOL_WEAK_LOCK,
    FINDUAS_SYMBOL_RELEASE_SHARED,
    FINDUAS_SYMBOL_RELEASE_WEAK,
    FINDUAS_SYMBOL_STRING_INIT,
    FINDUAS_SYMBOL_STRING_DTOR,
    FINDUAS_SYMBOL_CACHE_KEY_DTOR,
    FINDUAS_SYMBOL_HARDWARE_VTABLE,
    FINDUAS_SYMBOL_MIX139_VTABLE,
    FINDUAS_SYMBOL_CACHE_KEY_GET_PREFIXES,
    FINDUAS_SYMBOL_CHARACTERISTICS_INVALID,
    FINDUAS_SYMBOL_GLOBAL_PACKET_STATUS_INSTANCE,
    FINDUAS_SYMBOL_GLOBAL_PACKET_STATUS_GET_SENDER_INDEX,
    FINDUAS_TARGET_SYMBOL_COUNT,
};

typedef struct FinduasModuleProfile {
    const char *basename;
    uint8_t build_id[FINDUAS_GNU_BUILD_ID_SIZE];
    uint32_t source_kind;
    uint64_t exact_file_size;
    uint8_t whole_file_sha256[FINDUAS_SHA256_SIZE];
    uint8_t elf_header[FINDUAS_ELF_HEADER_SIZE];
    uint16_t exact_phnum;
    uint8_t reserved[6];
    FinduasElf64Phdr phdrs[FINDUAS_PROFILE_PHDR_COUNT];
} FinduasModuleProfile;

typedef struct FinduasSymbolProfile {
    enum FinduasTargetModuleId module_id;
    enum FinduasSymbolKind kind;
    const char *name;
    uintptr_t expected_rva;
    size_t symbol_size;
    size_t signature_size;
    uint8_t instruction_signature[FINDUAS_INSTRUCTION_SIGNATURE_SIZE];
} FinduasSymbolProfile;

extern const FinduasModuleProfile kFinduasModuleProfiles[FINDUAS_MODULE_COUNT];
extern const FinduasSymbolProfile kFinduasSymbolProfiles[FINDUAS_TARGET_SYMBOL_COUNT];

#endif
