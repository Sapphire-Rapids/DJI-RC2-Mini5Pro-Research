#!/usr/bin/env python3
"""Build and verify the exact DJI Fly 1.21.10 runtime-route ELF manifest.

This parser intentionally uses only the Python standard library.  In particular,
it does not consult ELF section headers.  The protected DJI objects carry a
misleading PT_DYNAMIC.p_offset, so the dynamic table is located by mapping the
PT_DYNAMIC virtual address through the file-backed PT_LOAD segments, exactly as
the runtime loader does.

The committed manifest is an admission list, not a symbol discovery mechanism:
every required symbol, RVA, ELF identity, code prefix and data address point is
version-pinned.  Verification fails closed on any mismatch.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA = "finduas.dji-fly-runtime-route-elf-manifest"
SCHEMA_VERSION = 1
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_JSON = SCRIPT_DIR / "runtime_route_manifest_20260828.json"
DEFAULT_MD = SCRIPT_DIR / "runtime_route_manifest_20260828.md"

ELF_MAGIC = b"\x7fELF"
ELFCLASS64 = 2
ELFDATA2LSB = 1
ET_DYN = 3
EM_AARCH64 = 183

PT_LOAD = 1
PT_DYNAMIC = 2
PT_NOTE = 4
PF_X = 1
PF_W = 2
PF_R = 4

SHN_UNDEF = 0
SHN_ABS = 0xFFF1

DT_NULL = 0
DT_NEEDED = 1
DT_HASH = 4
DT_STRTAB = 5
DT_SYMTAB = 6
DT_STRSZ = 10
DT_SYMENT = 11
DT_SONAME = 14
DT_GNU_HASH = 0x6FFFFEF5
DT_VERSYM = 0x6FFFFFF0

NT_GNU_BUILD_ID = 3

BIND_NAMES = {
    0: "LOCAL",
    1: "GLOBAL",
    2: "WEAK",
    10: "GNU_UNIQUE",
}
TYPE_NAMES = {
    0: "NOTYPE",
    1: "OBJECT",
    2: "FUNC",
    3: "SECTION",
    4: "FILE",
    5: "COMMON",
    6: "TLS",
    10: "GNU_IFUNC",
}
VIS_NAMES = {0: "DEFAULT", 1: "INTERNAL", 2: "HIDDEN", 3: "PROTECTED"}


class ManifestError(RuntimeError):
    """A fail-closed ELF or manifest validation failure."""


def hx(value: int) -> str:
    return f"0x{value:x}"


def sha256_bytes(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def flags_text(flags: int) -> str:
    return "".join(
        letter if flags & bit else "-"
        for bit, letter in ((PF_R, "R"), (PF_W, "W"), (PF_X, "X"))
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


def align4(value: int) -> int:
    return (value + 3) & ~3


@dataclass(frozen=True)
class ProgramHeader:
    index: int
    p_type: int
    p_flags: int
    p_offset: int
    p_vaddr: int
    p_paddr: int
    p_filesz: int
    p_memsz: int
    p_align: int

    def contains_file_vaddr(self, vaddr: int, size: int) -> bool:
        return (
            size >= 0
            and self.p_type == PT_LOAD
            and self.p_vaddr <= vaddr
            and vaddr + size <= self.p_vaddr + self.p_filesz
        )

    def contains_memory_vaddr(self, vaddr: int, size: int) -> bool:
        return (
            size >= 0
            and self.p_type == PT_LOAD
            and self.p_vaddr <= vaddr
            and vaddr + size <= self.p_vaddr + self.p_memsz
        )

    def file_offset_for(self, vaddr: int) -> int:
        return self.p_offset + (vaddr - self.p_vaddr)


@dataclass(frozen=True)
class DynamicEntry:
    index: int
    tag: int
    value: int


@dataclass(frozen=True)
class DynamicSymbol:
    index: int
    name: str
    st_name: int
    st_info: int
    st_other: int
    st_shndx: int
    st_value: int
    st_size: int
    versym_raw: int | None

    @property
    def bind(self) -> int:
        return self.st_info >> 4

    @property
    def symbol_type(self) -> int:
        return self.st_info & 0x0F

    @property
    def visibility(self) -> int:
        return self.st_other & 0x03


class ELF64LE:
    ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
    PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")
    DYNAMIC_ENTRY = struct.Struct("<qQ")
    DYNAMIC_SYMBOL = struct.Struct("<IBBHQQ")
    NOTE_HEADER = struct.Struct("<III")

    def __init__(self, data: bytes | bytearray, label: str):
        self.data = bytes(data)
        self.label = label
        require(len(self.data) >= self.ELF_HEADER.size, f"{label}: truncated ELF header")
        values = self.ELF_HEADER.unpack_from(self.data, 0)
        (
            ident,
            self.e_type,
            self.e_machine,
            self.e_version,
            self.e_entry,
            self.e_phoff,
            self.e_shoff,
            self.e_flags,
            self.e_ehsize,
            self.e_phentsize,
            self.e_phnum,
            self.e_shentsize,
            self.e_shnum,
            self.e_shstrndx,
        ) = values
        self.ident = ident
        require(ident[:4] == ELF_MAGIC, f"{label}: bad ELF magic")
        require(ident[4] == ELFCLASS64, f"{label}: not ELF64")
        require(ident[5] == ELFDATA2LSB, f"{label}: not little-endian")
        require(ident[6] == 1, f"{label}: unsupported ELF ident version")
        require(self.e_version == 1, f"{label}: unsupported ELF version")
        require(self.e_type == ET_DYN, f"{label}: expected ET_DYN, got {self.e_type}")
        require(
            self.e_machine == EM_AARCH64,
            f"{label}: expected AArch64 machine {EM_AARCH64}, got {self.e_machine}",
        )
        require(self.e_ehsize == self.ELF_HEADER.size, f"{label}: bad e_ehsize")
        require(
            self.e_phentsize == self.PROGRAM_HEADER.size,
            f"{label}: bad e_phentsize {self.e_phentsize}",
        )
        require(0 < self.e_phnum < 4096, f"{label}: unreasonable e_phnum")
        ph_end = self.e_phoff + self.e_phnum * self.e_phentsize
        require(ph_end <= len(self.data), f"{label}: program headers outside file")
        self.program_headers: list[ProgramHeader] = []
        for index in range(self.e_phnum):
            off = self.e_phoff + index * self.e_phentsize
            self.program_headers.append(ProgramHeader(index, *self.PROGRAM_HEADER.unpack_from(self.data, off)))
        self.loads = [p for p in self.program_headers if p.p_type == PT_LOAD]
        require(self.loads, f"{label}: no PT_LOAD")
        for segment in self.loads:
            require(
                segment.p_filesz <= segment.p_memsz,
                f"{label}: PT_LOAD[{segment.index}] filesz exceeds memsz",
            )
            require(
                segment.p_offset + segment.p_filesz <= len(self.data),
                f"{label}: PT_LOAD[{segment.index}] exceeds file",
            )
        require(
            min(p.p_vaddr for p in self.loads) == 0,
            f"{label}: expected zero-based ET_DYN image",
        )

        dynamics = [p for p in self.program_headers if p.p_type == PT_DYNAMIC]
        require(len(dynamics) == 1, f"{label}: expected exactly one PT_DYNAMIC")
        self.dynamic_ph = dynamics[0]
        require(self.dynamic_ph.p_filesz >= self.DYNAMIC_ENTRY.size, f"{label}: tiny PT_DYNAMIC")
        self.dynamic_file_offset, self.dynamic_load = self.vaddr_to_file(
            self.dynamic_ph.p_vaddr,
            self.dynamic_ph.p_filesz,
            "PT_DYNAMIC",
        )
        self.dynamic_entries = self._parse_dynamic()
        self.dynamic_by_tag: dict[int, list[DynamicEntry]] = {}
        for entry in self.dynamic_entries:
            self.dynamic_by_tag.setdefault(entry.tag, []).append(entry)

        self.symtab_vaddr = self.one_dynamic_value(DT_SYMTAB)
        self.strtab_vaddr = self.one_dynamic_value(DT_STRTAB)
        self.strsz = self.one_dynamic_value(DT_STRSZ)
        self.syment = self.one_dynamic_value(DT_SYMENT)
        require(self.syment == self.DYNAMIC_SYMBOL.size, f"{label}: DT_SYMENT != 24")
        require(0 < self.strsz <= len(self.data) * 2, f"{label}: unreasonable DT_STRSZ")
        self.strtab_file_offset, self.strtab_load = self.vaddr_to_file(
            self.strtab_vaddr, self.strsz, "DT_STRTAB"
        )
        self.strtab = self.data[self.strtab_file_offset : self.strtab_file_offset + self.strsz]

        self.gnu_hash_vaddr = self.one_dynamic_value(DT_GNU_HASH)
        self.gnu_hash = self._parse_gnu_hash()
        self.dynsym_count = self.gnu_hash["dynsym_count"]
        dynsym_size = self.dynsym_count * self.syment
        self.symtab_file_offset, self.symtab_load = self.vaddr_to_file(
            self.symtab_vaddr, dynsym_size, "DT_SYMTAB"
        )

        versym_entries = self.dynamic_by_tag.get(DT_VERSYM, [])
        require(len(versym_entries) <= 1, f"{label}: duplicate DT_VERSYM")
        self.versym_vaddr = versym_entries[0].value if versym_entries else None
        self.versym_file_offset: int | None = None
        if self.versym_vaddr is not None:
            self.versym_file_offset, _ = self.vaddr_to_file(
                self.versym_vaddr, self.dynsym_count * 2, "DT_VERSYM"
            )
        self.symbols = self._parse_symbols()
        self.symbols_by_name: dict[str, list[DynamicSymbol]] = {}
        for symbol in self.symbols:
            self.symbols_by_name.setdefault(symbol.name, []).append(symbol)
        self.build_id = self._parse_build_id()

    def vaddr_to_file(self, vaddr: int, size: int, what: str) -> tuple[int, ProgramHeader]:
        matches = [segment for segment in self.loads if segment.contains_file_vaddr(vaddr, size)]
        require(
            len(matches) == 1,
            f"{self.label}: {what} vaddr {hx(vaddr)} size {hx(size)} maps to {len(matches)} PT_LOADs",
        )
        segment = matches[0]
        offset = segment.file_offset_for(vaddr)
        require(offset + size <= len(self.data), f"{self.label}: {what} outside file")
        return offset, segment

    def segment_for_memory(self, vaddr: int, size: int, what: str) -> ProgramHeader:
        matches = [segment for segment in self.loads if segment.contains_memory_vaddr(vaddr, size)]
        require(
            len(matches) == 1,
            f"{self.label}: {what} vaddr {hx(vaddr)} maps to {len(matches)} memory PT_LOADs",
        )
        return matches[0]

    def _parse_dynamic(self) -> list[DynamicEntry]:
        limit = self.dynamic_ph.p_filesz // self.DYNAMIC_ENTRY.size
        entries: list[DynamicEntry] = []
        found_null = False
        for index in range(limit):
            off = self.dynamic_file_offset + index * self.DYNAMIC_ENTRY.size
            tag, value = self.DYNAMIC_ENTRY.unpack_from(self.data, off)
            entries.append(DynamicEntry(index, tag, value))
            if tag == DT_NULL:
                found_null = True
                break
        require(found_null, f"{self.label}: PT_DYNAMIC has no DT_NULL")
        return entries

    def one_dynamic_value(self, tag: int) -> int:
        values = self.dynamic_by_tag.get(tag, [])
        require(len(values) == 1, f"{self.label}: dynamic tag {hx(tag)} count is {len(values)}")
        return values[0].value

    def _parse_gnu_hash(self) -> dict[str, int]:
        header_off, segment = self.vaddr_to_file(self.gnu_hash_vaddr, 16, "DT_GNU_HASH header")
        nbuckets, symoffset, bloom_size, bloom_shift = struct.unpack_from("<IIII", self.data, header_off)
        require(0 < nbuckets < 10_000_000, f"{self.label}: unreasonable GNU hash nbuckets")
        require(0 < bloom_size < 10_000_000, f"{self.label}: unreasonable GNU hash bloom size")
        bloom_bytes = bloom_size * 8
        buckets_off = header_off + 16 + bloom_bytes
        buckets_bytes = nbuckets * 4
        segment_end = segment.p_offset + segment.p_filesz
        require(buckets_off + buckets_bytes <= segment_end, f"{self.label}: GNU hash buckets truncated")
        buckets = struct.unpack_from(f"<{nbuckets}I", self.data, buckets_off)
        chain_off = buckets_off + buckets_bytes
        max_chain_words = (segment_end - chain_off) // 4
        require(max_chain_words > 0, f"{self.label}: GNU hash has no chain room")
        highest = symoffset - 1
        chain_words_read = 0
        nonzero_buckets = 0
        for bucket in buckets:
            if bucket == 0:
                continue
            nonzero_buckets += 1
            require(bucket >= symoffset, f"{self.label}: GNU hash bucket below symoffset")
            chain_index = bucket - symoffset
            require(chain_index < max_chain_words, f"{self.label}: GNU hash bucket outside chains")
            symbol_index = bucket
            while True:
                require(chain_index < max_chain_words, f"{self.label}: unterminated GNU hash chain")
                chain_word = struct.unpack_from("<I", self.data, chain_off + chain_index * 4)[0]
                chain_words_read += 1
                highest = max(highest, symbol_index)
                if chain_word & 1:
                    break
                chain_index += 1
                symbol_index += 1
        dynsym_count = max(symoffset, highest + 1)
        require(0 < dynsym_count < 10_000_000, f"{self.label}: unreasonable dynsym count")
        return {
            "vaddr": self.gnu_hash_vaddr,
            "file_offset": header_off,
            "nbuckets": nbuckets,
            "symoffset": symoffset,
            "bloom_size": bloom_size,
            "bloom_shift": bloom_shift,
            "nonzero_buckets": nonzero_buckets,
            "max_bucket": max(buckets),
            "chain_words_read": chain_words_read,
            "dynsym_count": dynsym_count,
        }

    def _read_dynstr(self, offset: int) -> str:
        require(offset < self.strsz, f"{self.label}: st_name outside DT_STRTAB")
        end = self.strtab.find(b"\0", offset)
        require(end >= 0, f"{self.label}: unterminated dynamic symbol name")
        raw = self.strtab[offset:end]
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ManifestError(f"{self.label}: non-UTF-8 dynamic symbol name") from exc

    def _parse_symbols(self) -> list[DynamicSymbol]:
        symbols: list[DynamicSymbol] = []
        for index in range(self.dynsym_count):
            off = self.symtab_file_offset + index * self.syment
            st_name, st_info, st_other, st_shndx, st_value, st_size = self.DYNAMIC_SYMBOL.unpack_from(
                self.data, off
            )
            versym_raw = None
            if self.versym_file_offset is not None:
                versym_raw = struct.unpack_from("<H", self.data, self.versym_file_offset + index * 2)[0]
            symbols.append(
                DynamicSymbol(
                    index,
                    self._read_dynstr(st_name),
                    st_name,
                    st_info,
                    st_other,
                    st_shndx,
                    st_value,
                    st_size,
                    versym_raw,
                )
            )
        return symbols

    def _parse_build_id(self) -> str:
        found: list[bytes] = []
        for note in (p for p in self.program_headers if p.p_type == PT_NOTE):
            if note.p_filesz == 0:
                continue
            try:
                off, _ = self.vaddr_to_file(note.p_vaddr, note.p_filesz, f"PT_NOTE[{note.index}]")
            except ManifestError:
                require(
                    note.p_offset + note.p_filesz <= len(self.data),
                    f"{self.label}: PT_NOTE[{note.index}] outside file",
                )
                off = note.p_offset
            end = off + note.p_filesz
            while off + self.NOTE_HEADER.size <= end:
                namesz, descsz, note_type = self.NOTE_HEADER.unpack_from(self.data, off)
                off += self.NOTE_HEADER.size
                name_end = off + namesz
                desc_off = off + align4(namesz)
                desc_end = desc_off + descsz
                next_off = desc_off + align4(descsz)
                require(next_off <= end, f"{self.label}: truncated PT_NOTE entry")
                name = self.data[off:name_end]
                desc = self.data[desc_off:desc_end]
                if note_type == NT_GNU_BUILD_ID and name.rstrip(b"\0") == b"GNU":
                    found.append(desc)
                off = next_off
        require(len(found) == 1, f"{self.label}: expected one GNU build-id, found {len(found)}")
        require(8 <= len(found[0]) <= 64, f"{self.label}: unreasonable GNU build-id length")
        return found[0].hex()

    def exact_symbol(self, name: str) -> DynamicSymbol:
        matches = self.symbols_by_name.get(name, [])
        require(len(matches) == 1, f"{self.label}: exact dynsym {name!r} count is {len(matches)}")
        return matches[0]


def text_target(role: str, name: str, rva: int, *, bind: str = "GLOBAL") -> dict[str, Any]:
    return {
        "role": role,
        "name": name,
        "expected_rva": rva,
        "expected_bind": bind,
        "expected_type": "FUNC",
        "kind": "text",
        "signature_bytes": 16,
    }


def object_target(
    role: str,
    name: str,
    rva: int,
    *,
    bind: str = "GLOBAL",
    address_point_offsets: Sequence[int] = (),
) -> dict[str, Any]:
    return {
        "role": role,
        "name": name,
        "expected_rva": rva,
        "expected_bind": bind,
        "expected_type": "OBJECT",
        "kind": "address_only",
        "address_point_offsets": list(address_point_offsets),
    }


JNI_SYMBOLS: list[dict[str, Any]] = [
    object_target(
        "module_mediator_singleton_slot",
        "_ZN3uav3sdk17g_pModuleMediatorE",
        0x05344600,
    ),
    text_target("get_instance_do_not_call", "_ZN3uav3sdk11GetInstanceEv", 0x01D3AE40),
    text_target(
        "get_framework_core_weak_owner",
        "_ZN3uav3sdk14ModuleMediator16GetFrameworkCoreEv",
        0x01D54FF8,
    ),
    text_target(
        "get_product_manager_shared_owner",
        "_ZN3uav3sdk14ModuleMediator13GetProductMgrEv",
        0x01D54DA0,
    ),
    text_target("module_mediator_get_worker", "_ZN3uav3sdk14ModuleMediator9GetWorkerEv", 0x01D55030),
    text_target(
        "module_mediator_run_on_work_thread",
        "_ZN3uav3sdk14ModuleMediator15RunOnWorkThreadENSt6__ndk18functionIFvvEEEb",
        0x01D55764,
    ),
    text_target(
        "framework_core_get_worker",
        "_ZNK3uav3sdk16SDKFrameworkCore9GetWorkerEv",
        0x02501904,
        bind="WEAK",
    ),
    text_target(
        "framework_core_get_semantic_key",
        "_ZN3uav3sdk16SDKFrameworkCore6GetKeyEjjjjjRKNSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEE",
        0x025006BC,
    ),
    text_target(
        "hardware_layer_get_abstraction",
        "_ZN3uav3sdk13HardwareLayer14GetAbstractionERKNSt6__ndk16vectorIjNS2_9allocatorIjEEEE",
        0x0250D6C0,
    ),
    text_target(
        "base_abstraction_get_characteristics_by_cache_key",
        "_ZN3uav3sdk15BaseAbstraction18GetCharacteristicsERKNS0_8CacheKeyE",
        0x02515D94,
    ),
    text_target(
        "base_abstraction_get_characteristics_by_string",
        "_ZN3uav3sdk15BaseAbstraction18GetCharacteristicsERKNSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEE",
        0x025195E4,
    ),
    text_target(
        "base_abstraction_get_abstraction_key",
        "_ZN3uav3sdk15BaseAbstraction17GetAbstractionKeyEv",
        0x025194F0,
    ),
    text_target(
        "base_abstraction_get_datalink_id",
        "_ZNK3uav3sdk15BaseAbstraction13GetDataLinkIDEv",
        0x025194BC,
    ),
    text_target(
        "base_abstraction_get_device_id",
        "_ZNK3uav3sdk15BaseAbstraction11GetDeviceIDEv",
        0x025194C8,
    ),
    text_target(
        "base_abstraction_get_product_id",
        "_ZNK3uav3sdk15BaseAbstraction12GetProductIDEv",
        0x025194D0,
    ),
    text_target(
        "base_abstraction_get_abstraction_id",
        "_ZNK3uav3sdk15BaseAbstraction16GetAbstractionIDEv",
        0x025194D8,
    ),
    text_target(
        "base_abstraction_get_sender_seq_diagnostic_only",
        "_ZNK3uav3sdk15BaseAbstraction12GetSenderSeqEv",
        0x025195DC,
    ),
    text_target(
        "base_abstraction_get_component_index",
        "_ZNK3uav3sdk15BaseAbstraction17GetComponentIndexEv",
        0x02519B10,
    ),
    text_target(
        "product_manager_get_datalink_by_product_id",
        "_ZN3uav3sdk10ProductMgr22GetDatalinkByProductIdEjRNSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEERt",
        0x024FCD2C,
    ),
    text_target(
        "module_mediator_add_product_connection_observer",
        "_ZN3uav3sdk14ModuleMediator28AddProductConnectionObserverENSt6__ndk18functionIFvjRKNS0_11ProductInfoEEEENS3_IFvjEEE",
        0x01D5B508,
    ),
    text_target(
        "module_mediator_remove_product_connection_observer",
        "_ZN3uav3sdk14ModuleMediator31RemoveProductConnectionObserverEm",
        0x01D5BBC0,
    ),
    text_target(
        "module_mediator_add_datalink_observer",
        "_ZN3uav3sdk14ModuleMediator19AddDatalinkObserverENSt6__ndk18functionIFvRKNS2_12basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEEEEESD_",
        0x01D550A0,
    ),
    text_target(
        "module_mediator_remove_datalink_observer",
        "_ZN3uav3sdk14ModuleMediator22RemoveDatalinkObserverEm",
        0x01D55A34,
    ),
    text_target(
        "product_manager_add_product_connection_observer",
        "_ZN3uav3sdk10ProductMgr28AddProductConnectionObserverEmNSt6__ndk18functionIFvjRKNS0_11ProductInfoEEEENS3_IFvjEEE",
        0x024FCA3C,
    ),
    text_target(
        "product_manager_remove_product_connection_observer",
        "_ZN3uav3sdk10ProductMgr31RemoveProductConnectionObserverEm",
        0x024FCCE0,
    ),
    text_target(
        "target_shared_weak_lock",
        "_ZNSt6__ndk119__shared_weak_count4lockEv",
        0x01D2F300,
    ),
    text_target(
        "target_release_shared",
        "_ZNSt6__ndk119__shared_weak_count16__release_sharedEv",
        0x01D2F244,
    ),
    text_target(
        "target_release_weak",
        "_ZNSt6__ndk119__shared_weak_count14__release_weakEv",
        0x01D2F2CC,
    ),
    text_target(
        "target_string_init",
        "_ZNSt6__ndk112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEE6__initEPKcm",
        0x01D30EE8,
        bind="WEAK",
    ),
    text_target(
        "target_string_dtor",
        "_ZNSt6__ndk112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEED2Ev",
        0x01D30BCC,
        bind="WEAK",
    ),
    text_target("target_cache_key_dtor", "_ZN3uav3sdk8CacheKeyD2Ev", 0x04A32A48, bind="WEAK"),
    object_target(
        "vtable_hardware_layer",
        "_ZTVN3uav3sdk13HardwareLayerE",
        0x050F1250,
        address_point_offsets=(0x10, 0x68),
    ),
    object_target(
        "vtable_abstraction_manager_impl",
        "_ZTVN3uav3sdk22AbstractionManagerImplE",
        0x050F2040,
        address_point_offsets=(0x10,),
    ),
    object_target(
        "vtable_product139_fc_mixabs",
        "_ZTVN3uav3sdk3key6MixAbsINS0_32UAV77FlightControllerAbstractionENS1_11UAV139FCAbsEEE",
        0x05100F88,
        bind="WEAK",
        address_point_offsets=(0x10,),
    ),
]


KEY_VALUE_SYMBOLS: list[dict[str, Any]] = [
    text_target(
        "cache_key_get_prefixes",
        "_ZNK3uav3sdk8CacheKey11GetPrefixesEv",
        0x007EAB64,
    ),
    text_target(
        "characteristics_get_extra_param",
        "_ZNK3uav3sdk15Characteristics13GetExtraParamEv",
        0x008F9A54,
    ),
    text_target(
        "extra_param_get_single_send_pack_host_id",
        "_ZNK3uav3sdk25CharacteristicsExtraParam17GetSendPackHostIDEv",
        0x008F9BB0,
    ),
    text_target(
        "extra_param_get_send_pack_host_ids",
        "_ZNK3uav3sdk25CharacteristicsExtraParam18GetSendPackHostIDsEv",
        0x008F9BEC,
    ),
    object_target(
        "characteristics_invalid_singleton",
        "_ZN3uav3sdk15Characteristics7InvalidE",
        0x00C19D78,
    ),
]


BASE_SYMBOLS: list[dict[str, Any]] = [
    text_target(
        "global_packet_status_instance",
        "_ZN3uav4core18GlobalPacketStatus8instanceEv",
        0x002EC280,
    ),
    text_target(
        "global_packet_status_get_sender_index",
        "_ZN3uav4core18GlobalPacketStatus20GetGlobalSenderIndexEv",
        0x002EC328,
    ),
]


MODULE_SPECS: list[dict[str, Any]] = [
    {
        "id": "libsdk_jni.so",
        "relative_path": "official_dji_fly_20260827/working/extracted/libsdk_jni.so",
        "expected_size": 87313856,
        "expected_sha256": "5abd990c86bcd00c9a652a21e329ad4580a20ec9f80188075ada61f5a7b46286",
        "expected_build_id": "c892b3c06664df91d643f84ae9e59a906387068b",
        "expected_dynsym_count": 78496,
        "symbols": JNI_SYMBOLS,
    },
    {
        "id": "libsdk_key_value.so",
        "relative_path": "official_dji_fly_20260827/working/sdk_native/libsdk_key_value.so",
        "expected_size": 12684576,
        "expected_sha256": "09f4aa8aef65f720da09a1dad79c8851e05d619affaf73708bf6747341208336",
        "expected_build_id": "877a01a5b4b17e0a0f1b9153ccfe24891fb3c230",
        "expected_dynsym_count": 51801,
        "symbols": KEY_VALUE_SYMBOLS,
    },
    {
        "id": "libsdk_base.so",
        "relative_path": "official_dji_fly_20260827/working/sdk_native/libsdk_base.so",
        "expected_size": 7720240,
        "expected_sha256": "e5b290ebc6aa6e409e116cc0d3b84fb4e49c70f6c552feffacd5b15c7c83e873",
        "expected_build_id": "de104ddaca91438807b21688baf08455d5ade20c",
        "expected_dynsym_count": 14944,
        "symbols": BASE_SYMBOLS,
    },
]


def segment_record(segment: ProgramHeader, *, symbol_vaddr: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "index": segment.index,
        "flags": flags_text(segment.p_flags),
        "vaddr": hx(segment.p_vaddr),
        "file_offset": hx(segment.p_offset),
        "file_size": segment.p_filesz,
        "memory_size": segment.p_memsz,
        "alignment": hx(segment.p_align),
    }
    if symbol_vaddr is not None:
        result["storage"] = (
            "file_backed"
            if symbol_vaddr < segment.p_vaddr + segment.p_filesz
            else "zero_fill_bss"
        )
    return result


def symbol_record(elf: ELF64LE, spec: Mapping[str, Any]) -> dict[str, Any]:
    symbol = elf.exact_symbol(str(spec["name"]))
    require(symbol.st_shndx != SHN_UNDEF, f"{elf.label}: {symbol.name} is undefined")
    require(symbol.st_shndx != SHN_ABS, f"{elf.label}: {symbol.name} unexpectedly SHN_ABS")
    bind = BIND_NAMES.get(symbol.bind, f"UNKNOWN_{symbol.bind}")
    symbol_type = TYPE_NAMES.get(symbol.symbol_type, f"UNKNOWN_{symbol.symbol_type}")
    visibility = VIS_NAMES.get(symbol.visibility, f"UNKNOWN_{symbol.visibility}")
    require(symbol.st_value == spec["expected_rva"], f"{elf.label}: {symbol.name} RVA drift")
    require(bind == spec["expected_bind"], f"{elf.label}: {symbol.name} binding drift: {bind}")
    require(symbol_type == spec["expected_type"], f"{elf.label}: {symbol.name} type drift: {symbol_type}")
    require(visibility == "DEFAULT", f"{elf.label}: {symbol.name} visibility is {visibility}")
    memory_size = max(symbol.st_size, 1)
    segment = elf.segment_for_memory(symbol.st_value, memory_size, symbol.name)
    result: dict[str, Any] = {
        "role": spec["role"],
        "name": symbol.name,
        "index": symbol.index,
        "bind": bind,
        "type": symbol_type,
        "visibility": visibility,
        "shndx": symbol.st_shndx,
        "rva": hx(symbol.st_value),
        "size": symbol.st_size,
        "segment": segment_record(segment, symbol_vaddr=symbol.st_value),
    }
    if symbol.versym_raw is not None:
        result["version"] = {
            "raw": hx(symbol.versym_raw),
            "index": symbol.versym_raw & 0x7FFF,
            "hidden": bool(symbol.versym_raw & 0x8000),
        }
    if spec["kind"] == "text":
        require(segment.p_flags & PF_X, f"{elf.label}: {symbol.name} is not executable")
        requested_signature_len = int(spec["signature_bytes"])
        signature_len = min(requested_signature_len, symbol.st_size) if symbol.st_size else requested_signature_len
        require(signature_len >= 4 and signature_len % 4 == 0, "bad configured signature length")
        require(symbol.st_value % 4 == 0, f"{elf.label}: {symbol.name} is not instruction aligned")
        signature_off, signature_segment = elf.vaddr_to_file(
            symbol.st_value, signature_len, f"code signature for {symbol.name}"
        )
        require(signature_segment.index == segment.index, f"{elf.label}: signature segment mismatch")
        signature = elf.data[signature_off : signature_off + signature_len]
        result["code_signature"] = {
            "length": signature_len,
            "requested_max_length": requested_signature_len,
            "file_offset": hx(signature_off),
            "bytes_hex": signature.hex(),
            "sha256": sha256_bytes(signature),
        }
    else:
        require(not (segment.p_flags & PF_X), f"{elf.label}: address-only symbol in executable segment")
        points = []
        for offset in spec.get("address_point_offsets", []):
            point = symbol.st_value + int(offset)
            require(
                symbol.st_size == 0 or int(offset) < symbol.st_size,
                f"{elf.label}: {symbol.name} address point outside symbol",
            )
            point_segment = elf.segment_for_memory(point, 1, f"address point for {symbol.name}")
            points.append(
                {
                    "offset": hx(int(offset)),
                    "rva": hx(point),
                    "segment_index": point_segment.index,
                }
            )
        result["address_only"] = {
            "reason": "runtime relocations or zero-fill make file-byte hashing invalid",
            "address_points": points,
        }
    return result


def needed_names(elf: ELF64LE) -> list[str]:
    names: list[str] = []
    for entry in elf.dynamic_by_tag.get(DT_NEEDED, []):
        names.append(elf._read_dynstr(entry.value))
    return names


def build_module_record(spec: Mapping[str, Any], data: bytes, *, enforce_identity: bool) -> dict[str, Any]:
    label = str(spec["id"])
    if enforce_identity:
        require(len(data) == spec["expected_size"], f"{label}: file size mismatch")
        require(sha256_bytes(data) == spec["expected_sha256"], f"{label}: whole-file SHA-256 mismatch")
    elf = ELF64LE(data, label)
    if spec.get("expected_build_id") is not None:
        require(elf.build_id == spec["expected_build_id"], f"{label}: GNU build-id mismatch")
    if spec.get("expected_dynsym_count") is not None:
        require(
            elf.dynsym_count == spec["expected_dynsym_count"],
            f"{label}: GNU-hash dynsym count mismatch",
        )
    loads = [segment_record(segment) for segment in elf.loads]
    dynamic = elf.dynamic_ph
    result = {
        "id": spec["id"],
        "relative_path": spec["relative_path"],
        "file_size": len(data),
        "sha256": sha256_bytes(data),
        "gnu_build_id": elf.build_id,
        "elf": {
            "class": "ELF64",
            "endianness": "little",
            "type": "ET_DYN",
            "machine": "AArch64",
            "machine_number": elf.e_machine,
            "program_header_count": elf.e_phnum,
            "section_headers_used": False,
        },
        "load_segments": loads,
        "dynamic_table": {
            "program_header_index": dynamic.index,
            "vaddr": hx(dynamic.p_vaddr),
            "size": dynamic.p_filesz,
            "claimed_file_offset": hx(dynamic.p_offset),
            "mapped_file_offset": hx(elf.dynamic_file_offset),
            "claimed_offset_matches_mapping": dynamic.p_offset == elf.dynamic_file_offset,
            "mapped_through_load_segment": elf.dynamic_load.index,
            "entry_count_through_dt_null": len(elf.dynamic_entries),
            "dt_symtab": hx(elf.symtab_vaddr),
            "dt_strtab": hx(elf.strtab_vaddr),
            "dt_strsz": elf.strsz,
            "dt_syment": elf.syment,
            "dt_gnu_hash": hx(elf.gnu_hash_vaddr),
            "dt_versym": hx(elf.versym_vaddr) if elf.versym_vaddr is not None else None,
            "needed": needed_names(elf),
        },
        "gnu_hash": {
            key: hx(value) if key in {"vaddr", "file_offset"} else value
            for key, value in elf.gnu_hash.items()
        },
        "symbols": [symbol_record(elf, symbol_spec) for symbol_spec in spec["symbols"]],
    }
    return result


def module_path(spec: Mapping[str, Any]) -> Path:
    return SCRIPT_DIR / str(spec["relative_path"])


def build_manifest(*, enforce_identity: bool = True) -> dict[str, Any]:
    modules = []
    for spec in MODULE_SPECS:
        path = module_path(spec)
        require(path.is_file(), f"missing module: {path}")
        modules.append(build_module_record(spec, path.read_bytes(), enforce_identity=enforce_identity))
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "target": "DJI Fly 1.21.10 arm64-v8a on DJI RC 2 firmware 07.00.0100",
        "purpose": "fail-closed zero-send EID/RID runtime-route resolver admission",
        "source_root": "host-tools/elf-analysis",
        "parser_contract": {
            "standard_library_only": True,
            "dynamic_table_source": "PT_DYNAMIC.p_vaddr mapped through exactly one file-backed PT_LOAD",
            "section_headers_used": False,
            "dynsym_count_source": "DT_GNU_HASH buckets/chains",
            "text_policy": "exact first min(16, symbol size) AArch64 bytes (one to four instructions)",
            "data_policy": "record segment and address points; never hash relocation-sensitive or BSS bytes",
        },
        "runtime_consumer_contract": {
            "handle": "RTLD_NOLOAD on the already-loaded exact SO only; no plain dlopen and no RTLD_DEFAULT",
            "mapping": "require one coherent exact-file mapping and derive load bias from its PT_LOAD layout",
            "symbol": "dlsym(exact handle), then dladdr must name that same mapping and equal load_bias + exact RVA",
            "weak_interposition": "reject every WEAK target whose resolved address is outside the exact defining SO",
            "work_thread": "RunOnWorkThread/GetWorker are audit coverage, not synchronization barriers or v2.1 direct-call requirements",
        },
        "modules": modules,
    }


def first_difference(expected: Any, actual: Any, path: str = "$") -> str | None:
    if type(expected) is not type(actual):
        return f"{path}: type {type(expected).__name__} != {type(actual).__name__}"
    if isinstance(expected, dict):
        expected_keys = list(expected.keys())
        actual_keys = list(actual.keys())
        if expected_keys != actual_keys:
            return f"{path}: keys/order differ: {expected_keys!r} != {actual_keys!r}"
        for key in expected_keys:
            difference = first_difference(expected[key], actual[key], f"{path}.{key}")
            if difference:
                return difference
        return None
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return f"{path}: list length {len(expected)} != {len(actual)}"
        for index, (left, right) in enumerate(zip(expected, actual)):
            difference = first_difference(left, right, f"{path}[{index}]")
            if difference:
                return difference
        return None
    if expected != actual:
        return f"{path}: {expected!r} != {actual!r}"
    return None


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read committed manifest {path}: {exc}") from exc
    require(isinstance(payload, dict), "committed manifest root is not an object")
    require(payload.get("schema") == SCHEMA, "committed manifest schema mismatch")
    require(payload.get("schema_version") == SCHEMA_VERSION, "committed manifest version mismatch")
    return payload


def verify_manifest(path: Path = DEFAULT_JSON) -> dict[str, Any]:
    committed = load_json(path)
    current = build_manifest(enforce_identity=True)
    difference = first_difference(committed, current)
    require(difference is None, f"manifest verification failed: {difference}")
    return current


def markdown_for(manifest: Mapping[str, Any]) -> str:
    lines = [
        "# DJI Fly 1.21.10 runtime route exact ELF manifest",
        "",
        "日期：2026-08-28",
        "状态：**离线、只读、exact-build；没有连接或操作设备**",
        "",
        "## 作用",
        "",
        "`runtime_route_manifest_20260828.json` 是 EID/RID route resolver 的失败关闭准入清单。",
        "生成器只使用 Python 标准库，不读取 ELF section header。它按 `PT_DYNAMIC.p_vaddr`",
        "经唯一、file-backed `PT_LOAD` 映射到真实 dynamic table，再从 `DT_GNU_HASH` 的",
        "bucket/chain 推导 dynsym 数量。这样不会被 DJI 样本中误导性的",
        "`PT_DYNAMIC.p_offset` 或损坏的 section table 带偏。",
        "",
        "## 精确模块",
        "",
        "| 模块 | bytes | SHA-256 | GNU build-id | dynsym | dynamic claimed → mapped |",
        "| --- | ---: | --- | --- | ---: | --- |",
    ]
    for module in manifest["modules"]:
        dynamic = module["dynamic_table"]
        lines.append(
            f"| `{module['id']}` | {module['file_size']} | `{module['sha256']}` | "
            f"`{module['gnu_build_id']}` | {module['gnu_hash']['dynsym_count']} | "
            f"`{dynamic['claimed_file_offset']}` → `{dynamic['mapped_file_offset']}` |"
        )
    lines += [
        "",
        "## 固定目标",
        "",
        "函数记录 dynsym index/bind/type/visibility/shndx/RVA/size、所在 segment，以及入口",
        "最多 16 bytes（短函数取完整 4/8/12 bytes）的精确 AArch64 签名。全局对象与 vtable",
        "只记录 segment、RVA 和合法",
        "address point；它们可能位于 BSS 或含运行时 relocation，故**不对 file bytes 做错误哈希**。",
        "",
    ]
    for module in manifest["modules"]:
        lines += [
            f"### `{module['id']}`",
            "",
            "| role | dynsym | attr | RVA | size | segment | admission evidence |",
            "| --- | --- | --- | ---: | ---: | --- | --- |",
        ]
        for symbol in module["symbols"]:
            attr = f"{symbol['bind']}/{symbol['type']}/{symbol['visibility']}/shndx={symbol['shndx']}"
            segment = symbol["segment"]
            segment_text = f"#{segment['index']} {segment['flags']} {segment['storage']}"
            if "code_signature" in symbol:
                length = symbol["code_signature"]["length"]
                evidence = f"entry{length} `{symbol['code_signature']['bytes_hex']}`"
            else:
                points = symbol["address_only"]["address_points"]
                evidence = (
                    "address-only"
                    if not points
                    else "address-points " + ", ".join(f"`{point['rva']}`" for point in points)
                )
            lines.append(
                f"| `{symbol['role']}` | `{symbol['name']}` (#{symbol['index']}) | "
                f"{attr} | `{symbol['rva']}` | {symbol['size']} | {segment_text} | {evidence} |"
            )
        lines.append("")
    lines += [
        "## 校验",
        "",
        "```sh",
        "python3 runtime_route_manifest_20260828.py --verify",
        "python3 runtime_route_manifest_20260828.py --self-test",
        "```",
        "",
        "`--verify` 会重新读取三个 whole file，并精确比较 committed JSON 的全部字段；任何",
        "文件 hash、build-id、dynamic pointer、GNU-hash 派生计数、符号属性/RVA、segment、",
        "代码签名或 address point 漂移都会非零退出。`--self-test` 会逐个篡改真实函数入口样本，",
        "分别确认 whole-file SHA 与独立代码签名都会拒绝；同时确认至少一个样本的",
        "declared dynamic offset 确实与 loader-style 映射不同。",
        "",
        "## 运行时消费门禁",
        "",
        "本清单不能替代进程内加载状态检查。resolver 必须只对已经加载的精确 SO 使用",
        "`RTLD_NOLOAD` handle；禁止 plain `dlopen` 加载第二份，禁止 `RTLD_DEFAULT`。每个",
        "`dlsym(handle, mangled)` 结果随后都要通过 `dladdr` 证明属于唯一的预期 mapping，",
        "且地址严格等于 `load_bias + manifest RVA`。这条规则同样适用于 WEAK string/dtor/",
        "vtable 符号；发生 interposition 时必须中止。",
        "",
        "`RunOnWorkThread` / `GetWorker` 保留在 manifest 中用于路线审计和未来准入，并不",
        "表示 v2.1 route-only resolver 要直接调用它们。worker 队列不是同步或 epoch barrier；",
        "相关结论以仓库的 [evidence register](../../docs/02_EVIDENCE_REGISTER.md) 为准；",
        "本源码目录不复制工作区审计文档。",
        "",
        "该清单只证明当前 DJI Fly 1.21.10 的 ELF/runtime admission 条件，不证明任意其他",
        "Fly 版本 ABI 兼容，也不调用 GET、SET、listener、transport 或设备接口。",
        "",
    ]
    return "\n".join(lines)


def write_outputs() -> dict[str, Any]:
    manifest = build_manifest(enforce_identity=True)
    DEFAULT_JSON.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    DEFAULT_MD.write_text(markdown_for(manifest), encoding="utf-8")
    return manifest


def verify_module_bytes_against_record(
    spec: Mapping[str, Any], data: bytes | bytearray, expected_record: Mapping[str, Any]
) -> None:
    actual = build_module_record(spec, bytes(data), enforce_identity=False)
    difference = first_difference(expected_record, actual)
    require(difference is None, f"module/manifest mismatch: {difference}")


def self_test(path: Path = DEFAULT_JSON) -> list[str]:
    committed = verify_manifest(path)
    results: list[str] = []
    by_id = {module["id"]: module for module in committed["modules"]}
    saw_dynamic_offset_trap = False

    first_spec = MODULE_SPECS[0]
    bad_machine = bytearray(module_path(first_spec).read_bytes())
    struct.pack_into("<H", bad_machine, 18, 62)  # EM_X86_64, not EM_AARCH64.
    try:
        build_module_record(first_spec, bytes(bad_machine), enforce_identity=False)
    except ManifestError as exc:
        require("AArch64" in str(exc), "self-test: wrong-machine ELF hit the wrong guard")
        results.append("PASS wrong-machine ELF rejected before symbol admission")
    else:
        raise ManifestError("self-test failure: wrong-machine ELF was accepted")

    for spec in MODULE_SPECS:
        expected = by_id[str(spec["id"])]
        original = module_path(spec).read_bytes()
        code_target = next(symbol for symbol in expected["symbols"] if "code_signature" in symbol)
        signature_offset = int(code_target["code_signature"]["file_offset"], 16)
        corrupted = bytearray(original)
        corrupted[signature_offset] ^= 0x01
        try:
            verify_module_bytes_against_record(spec, corrupted, expected)
        except ManifestError as exc:
            require("$.sha256" in str(exc), f"self-test: {spec['id']} was not rejected by whole-file SHA")
            results.append(f"PASS corrupted sample rejected by whole-file SHA: {spec['id']}")
        else:
            raise ManifestError(f"self-test failure: corrupted {spec['id']} was accepted")

        # Prove the entry signature is independently effective: model an attacker
        # updating only the committed whole-file digest while leaving the exact
        # symbol admission records untouched.
        forged_expected = copy.deepcopy(expected)
        forged_expected["sha256"] = sha256_bytes(corrupted)
        try:
            verify_module_bytes_against_record(spec, corrupted, forged_expected)
        except ManifestError as exc:
            require(
                ".code_signature." in str(exc),
                f"self-test: {spec['id']} did not reach its code-signature guard",
            )
            results.append(f"PASS corrupted sample rejected by code signature: {spec['id']}")
        else:
            raise ManifestError(
                f"self-test failure: corrupted {spec['id']} passed after forged SHA"
            )

        dynamic = expected["dynamic_table"]
        claimed = int(dynamic["claimed_file_offset"], 16)
        mapped = int(dynamic["mapped_file_offset"], 16)
        if claimed != mapped:
            saw_dynamic_offset_trap = True
            require(
                mapped + int(dynamic["size"]) <= len(original),
                f"self-test: mapped dynamic table outside {spec['id']}",
            )
            results.append(
                f"PASS loader-style dynamic mapping used: {spec['id']} {hx(claimed)} != {hx(mapped)}"
            )
    require(saw_dynamic_offset_trap, "self-test did not encounter misleading PT_DYNAMIC.p_offset")

    tampered = copy.deepcopy(committed)
    tampered["modules"][0]["sha256"] = "0" * 64
    difference = first_difference(tampered, build_manifest(enforce_identity=True))
    require(difference is not None, "self-test failure: tampered committed manifest was accepted")
    results.append("PASS tampered committed JSON rejected")
    return results


def inventory(needles: Sequence[str]) -> None:
    for spec in MODULE_SPECS:
        path = module_path(spec)
        elf = ELF64LE(path.read_bytes(), str(spec["id"]))
        print(
            f"{spec['id']}: build-id={elf.build_id} dynsym={elf.dynsym_count} "
            f"dynamic={hx(elf.dynamic_ph.p_offset)}->{hx(elf.dynamic_file_offset)}"
        )
        for symbol in elf.symbols:
            if any(needle in symbol.name for needle in needles):
                print(
                    f"  {symbol.index:6d} {BIND_NAMES.get(symbol.bind, symbol.bind)}/"
                    f"{TYPE_NAMES.get(symbol.symbol_type, symbol.symbol_type)}/"
                    f"{VIS_NAMES.get(symbol.visibility, symbol.visibility)} "
                    f"rva={hx(symbol.st_value)} size={symbol.st_size} shndx={symbol.st_shndx} "
                    f"{symbol.name}"
                )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--write", action="store_true", help="regenerate JSON and Markdown")
    actions.add_argument("--verify", action="store_true", help="verify the committed JSON fail closed")
    actions.add_argument("--self-test", action="store_true", help="verify and reject corrupted samples")
    actions.add_argument(
        "--inventory",
        nargs="+",
        metavar="SUBSTRING",
        help="developer aid: list dynsym names containing a substring",
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_JSON)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.inventory:
            inventory(args.inventory)
        elif args.write:
            manifest = write_outputs()
            print(
                f"WROTE {DEFAULT_JSON} and {DEFAULT_MD}: "
                f"{sum(len(module['symbols']) for module in manifest['modules'])} exact symbols"
            )
        elif args.verify:
            manifest = verify_manifest(args.manifest)
            print(
                f"PASS exact runtime manifest: {len(manifest['modules'])} modules, "
                f"{sum(len(module['symbols']) for module in manifest['modules'])} symbols"
            )
        else:
            for line in self_test(args.manifest):
                print(line)
            print("PASS corrupted-sample self-test")
        return 0
    except ManifestError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
