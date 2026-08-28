#ifndef FINDUAS_EID_ROUTE_V22_ELF_PROFILE_H
#define FINDUAS_EID_ROUTE_V22_ELF_PROFILE_H

#include <stdint.h>

#define FINDUAS_ET_DYN 3u
#define FINDUAS_EM_AARCH64 183u
#define FINDUAS_EV_CURRENT 1u

#define FINDUAS_PT_LOAD 1u
#define FINDUAS_PT_DYNAMIC 2u
#define FINDUAS_PT_NOTE 4u
#define FINDUAS_PT_GNU_EH_FRAME UINT32_C(0x6474e550)

#define FINDUAS_PF_X 1u
#define FINDUAS_PF_W 2u
#define FINDUAS_PF_R 4u

typedef struct FinduasElf64Ehdr {
    uint8_t e_ident[16];
    uint16_t e_type;
    uint16_t e_machine;
    uint32_t e_version;
    uint64_t e_entry;
    uint64_t e_phoff;
    uint64_t e_shoff;
    uint32_t e_flags;
    uint16_t e_ehsize;
    uint16_t e_phentsize;
    uint16_t e_phnum;
    uint16_t e_shentsize;
    uint16_t e_shnum;
    uint16_t e_shstrndx;
} FinduasElf64Ehdr;

typedef struct FinduasElf64Phdr {
    uint32_t p_type;
    uint32_t p_flags;
    uint64_t p_offset;
    uint64_t p_vaddr;
    uint64_t p_paddr;
    uint64_t p_filesz;
    uint64_t p_memsz;
    uint64_t p_align;
} FinduasElf64Phdr;

_Static_assert(sizeof(FinduasElf64Ehdr) == 64u, "exact ELF64 header layout");
_Static_assert(sizeof(FinduasElf64Phdr) == 56u, "exact ELF64 program-header layout");

#endif
