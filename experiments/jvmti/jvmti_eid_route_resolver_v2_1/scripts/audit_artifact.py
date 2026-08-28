#!/usr/bin/env python3
"""Fail-closed artifact/source audit for the offline EID route resolver V2.1."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import struct
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path


EXPECTED_SIGNER_CERT_SHA256 = (
    "37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224"
)
DJI_PLATFORM_CERT_SHA256 = (
    "a4aa1cdd2ea580cbbe67486b5f6f3cfea83f488889995afa70793daa516687da"
)
EXPECTED_PACKAGE = "com.finduas.jvmti.eidroute.v21"
EXPECTED_NATIVE_ENTRY = "lib/arm64-v8a/libfinduas_eid_route_resolver_v2_1.so"
EXPECTED_ZIP_ENTRIES = {
    "META-INF/com/android/build/gradle/app-metadata.properties",
    "AndroidManifest.xml",
    "resources.arsc",
    EXPECTED_NATIVE_ENTRY,
}
EXPECTED_NEEDED = {"liblog.so", "libdl.so", "libc.so"}
EXPECTED_UNDEFINED = {
    "__android_log_print",
    "__memcpy_chk",
    "__memset_chk",
    "__stack_chk_fail",
    "dl_iterate_phdr",
    "dladdr",
    "dlclose",
    "dlerror",
    "dlopen",
    "dlsym",
    "memcmp",
}

PT_LOAD = 1
PT_DYNAMIC = 2
PT_NOTE = 4
PF_X = 1
PF_W = 2
PF_R = 4
DT_NULL = 0
DT_HASH = 4
DT_STRTAB = 5
DT_SYMTAB = 6
DT_RELA = 7
DT_RELASZ = 8
DT_RELAENT = 9
DT_STRSZ = 10
DT_SYMENT = 11
DT_GNU_HASH = 0x6FFFFEF5
R_AARCH64_RELATIVE = 1027
SHN_UNDEF = 0
STB_GLOBAL = 1
STB_WEAK = 2
STT_OBJECT = 1
STT_FUNC = 2
STV_DEFAULT = 0


class AuditFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditFailure(message)


def research_fixture_root() -> Path:
    setting = os.environ.get("FINDUAS_RESEARCH_FIXTURE_ROOT")
    require(bool(setting), "set FINDUAS_RESEARCH_FIXTURE_ROOT to the external fixture tree")
    return Path(str(setting)).expanduser().resolve()


def run_checked(command: list[str]) -> str:
    completed = subprocess.run(command, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        raise AuditFailure(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stdout}{completed.stderr}"
        )
    return completed.stdout + completed.stderr


def configure_java_runtime() -> None:
    for candidate in (
        os.environ.get("FINDUAS_ROUTE_V21_JAVA_HOME"),
        os.environ.get("JAVA_HOME"),
    ):
        if not candidate:
            continue
        java_home = Path(candidate).expanduser().resolve()
        if (java_home / "bin/java").is_file():
            os.environ["JAVA_HOME"] = str(java_home)
            os.environ["PATH"] = f"{java_home / 'bin'}:{os.environ.get('PATH', '')}"
            return
    raise AuditFailure("no usable Java runtime")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dynamic_symbol_names(output: str) -> set[str]:
    names: set[str] = set()
    for line in output.splitlines():
        fields = line.split()
        if fields:
            names.add(fields[-1].split("@", 1)[0])
    return names


@dataclass(frozen=True)
class ProgramHeader:
    kind: int
    flags: int
    offset: int
    vaddr: int
    file_size: int
    memory_size: int


class ExactElf:
    def __init__(self, path: Path):
        self.path = path
        self.data = path.read_bytes()
        require(self.data[:6] == b"\x7fELF\x02\x01", f"not ELF64 LE: {path}")
        require(len(self.data) >= 64, f"truncated ELF header: {path}")
        phoff = struct.unpack_from("<Q", self.data, 32)[0]
        phentsize = struct.unpack_from("<H", self.data, 54)[0]
        phnum = struct.unpack_from("<H", self.data, 56)[0]
        require(phentsize >= 56 and phnum > 0, f"invalid program headers: {path}")
        self.program_headers: list[ProgramHeader] = []
        for index in range(phnum):
            offset = phoff + index * phentsize
            require(offset + 56 <= len(self.data), f"truncated program header: {path}")
            values = struct.unpack_from("<IIQQQQQQ", self.data, offset)
            self.program_headers.append(
                ProgramHeader(values[0], values[1], values[2], values[3], values[5], values[6])
            )

    def vaddr_to_offset(self, vaddr: int, size: int) -> int:
        require(vaddr >= 0 and size >= 0, "negative ELF range")
        for header in self.program_headers:
            if header.kind != PT_LOAD:
                continue
            if vaddr >= header.vaddr and vaddr + size <= header.vaddr + header.file_size:
                result = header.offset + (vaddr - header.vaddr)
                require(result + size <= len(self.data), "mapped ELF range exceeds file")
                return result
        raise AuditFailure(f"RVA 0x{vaddr:x}+0x{size:x} is not file-backed in {self.path}")

    def offset_to_vaddr(self, offset: int, size: int) -> int:
        require(offset >= 0 and size >= 0, "negative ELF file range")
        for header in self.program_headers:
            if header.kind != PT_LOAD:
                continue
            if offset >= header.offset and offset + size <= header.offset + header.file_size:
                return header.vaddr + (offset - header.offset)
        raise AuditFailure(f"file range 0x{offset:x}+0x{size:x} is not in PT_LOAD: {self.path}")

    def bytes_at(self, vaddr: int, size: int) -> bytes:
        offset = self.vaddr_to_offset(vaddr, size)
        return self.data[offset : offset + size]

    def load_for_range(self, vaddr: int, size: int) -> ProgramHeader:
        matches = [
            header
            for header in self.program_headers
            if header.kind == PT_LOAD
            and vaddr >= header.vaddr
            and vaddr + size <= header.vaddr + header.file_size
        ]
        require(len(matches) == 1, f"PT_LOAD range cardinality for 0x{vaddr:x}+0x{size:x}")
        return matches[0]

    def cstring_at(self, vaddr: int, maximum: int = 4096) -> str:
        offset = self.vaddr_to_offset(vaddr, 1)
        limit = min(len(self.data), offset + maximum)
        end = self.data.find(b"\0", offset, limit)
        require(end >= 0, f"unterminated ELF string at RVA 0x{vaddr:x}")
        return self.data[offset:end].decode("utf-8", errors="strict")

    def unique_cstring_rva(self, value: str) -> int:
        needle = value.encode("utf-8") + b"\0"
        require(self.data.count(needle) == 1, f"ELF string cardinality for {value!r}")
        return self.offset_to_vaddr(self.data.index(needle), len(needle))

    def build_id(self) -> bytes:
        matches: list[bytes] = []
        for header in self.program_headers:
            if header.kind != PT_NOTE or header.file_size == 0:
                continue
            note_data = self.bytes_at(header.vaddr, header.file_size)
            cursor = 0
            while cursor < len(note_data):
                require(cursor + 12 <= len(note_data), "truncated ELF note header")
                name_size, desc_size, note_type = struct.unpack_from("<III", note_data, cursor)
                cursor += 12
                name_end = cursor + name_size
                desc_start = (name_end + 3) & ~3
                desc_end = desc_start + desc_size
                next_note = (desc_end + 3) & ~3
                require(next_note <= len(note_data) and next_note > cursor, "invalid ELF note")
                name = note_data[cursor:name_end]
                description = note_data[desc_start:desc_end]
                if name == b"GNU\0" and note_type == 3:
                    matches.append(description)
                cursor = next_note
        require(len(matches) == 1 and len(matches[0]) == 20, "GNU build-id cardinality/size")
        return matches[0]

    def dynamic_tags(self) -> dict[int, int]:
        dynamic_headers = [h for h in self.program_headers if h.kind == PT_DYNAMIC]
        require(len(dynamic_headers) == 1, "PT_DYNAMIC cardinality")
        header = dynamic_headers[0]
        dynamic = self.bytes_at(header.vaddr, header.file_size)
        tags: dict[int, int] = {}
        for offset in range(0, len(dynamic), 16):
            require(offset + 16 <= len(dynamic), "truncated dynamic table")
            tag, value = struct.unpack_from("<QQ", dynamic, offset)
            if tag == DT_NULL:
                break
            tags[tag] = value
        require(DT_SYMTAB in tags and DT_STRTAB in tags and DT_STRSZ in tags, "dynsym tags absent")
        return tags

    def rela_entries(self) -> list[tuple[int, int, int, int]]:
        tags = self.dynamic_tags()
        require(DT_RELA in tags and DT_RELASZ in tags, "DT_RELA metadata absent")
        entry_size = tags.get(DT_RELAENT, 24)
        require(entry_size == 24 and tags[DT_RELASZ] % entry_size == 0, "invalid ELF64 RELA table")
        raw = self.bytes_at(tags[DT_RELA], tags[DT_RELASZ])
        result: list[tuple[int, int, int, int]] = []
        for offset in range(0, len(raw), entry_size):
            relocation_offset, info, addend = struct.unpack_from("<QQq", raw, offset)
            result.append((relocation_offset, info & 0xFFFFFFFF, info >> 32, addend))
        return result

    def dynsym_count(self, tags: dict[int, int]) -> int:
        if DT_HASH in tags:
            raw = self.bytes_at(tags[DT_HASH], 8)
            _bucket_count, chain_count = struct.unpack("<II", raw)
            return chain_count
        require(DT_GNU_HASH in tags, "neither SYSV nor GNU hash is present")
        header = self.bytes_at(tags[DT_GNU_HASH], 16)
        bucket_count, symbol_offset, bloom_size, _bloom_shift = struct.unpack("<IIII", header)
        buckets_rva = tags[DT_GNU_HASH] + 16 + bloom_size * 8
        buckets_raw = self.bytes_at(buckets_rva, bucket_count * 4)
        buckets = struct.unpack(f"<{bucket_count}I", buckets_raw) if bucket_count else ()
        nonzero = [value for value in buckets if value != 0]
        if not nonzero:
            return symbol_offset
        symbol_index = max(nonzero)
        require(symbol_index >= symbol_offset, "invalid GNU hash bucket")
        chains_rva = buckets_rva + bucket_count * 4
        while True:
            chain_rva = chains_rva + (symbol_index - symbol_offset) * 4
            value = struct.unpack("<I", self.bytes_at(chain_rva, 4))[0]
            symbol_index += 1
            if value & 1:
                return symbol_index
            require(symbol_index < 1_000_000, "unbounded GNU hash chain")

    def true_dynsym(self) -> dict[str, list[tuple[int, int, int, int, int]]]:
        tags = self.dynamic_tags()
        symbol_count = self.dynsym_count(tags)
        symbol_size = tags.get(DT_SYMENT, 24)
        require(symbol_size == 24, "unexpected ELF64 symbol size")
        string_table = self.bytes_at(tags[DT_STRTAB], tags[DT_STRSZ])
        symbols: dict[str, list[tuple[int, int, int, int, int]]] = {}
        for index in range(symbol_count):
            raw = self.bytes_at(tags[DT_SYMTAB] + index * symbol_size, symbol_size)
            name_offset, info, other, section, value, size = struct.unpack("<IBBHQQ", raw)
            require(name_offset < len(string_table), "dynsym name offset outside string table")
            end = string_table.find(b"\0", name_offset)
            require(end >= 0, "unterminated dynsym name")
            name = string_table[name_offset:end].decode("utf-8", errors="strict")
            symbols.setdefault(name, []).append((info, other, section, value, size))
        return symbols


MODULE_PROFILES = {
    "libsdk_jni.so": {
        "relative": "official_dji_fly_20260827/working/extracted/libsdk_jni.so",
        "sha256": "5abd990c86bcd00c9a652a21e329ad4580a20ec9f80188075ada61f5a7b46286",
        "build_id": "c892b3c06664df91d643f84ae9e59a906387068b",
    },
    "libsdk_key_value.so": {
        "relative": "official_dji_fly_20260827/working/sdk_native/libsdk_key_value.so",
        "sha256": "09f4aa8aef65f720da09a1dad79c8851e05d619affaf73708bf6747341208336",
        "build_id": "877a01a5b4b17e0a0f1b9153ccfe24891fb3c230",
    },
    "libsdk_base.so": {
        "relative": "official_dji_fly_20260827/working/sdk_native/libsdk_base.so",
        "sha256": "e5b290ebc6aa6e409e116cc0d3b84fb4e49c70f6c552feffacd5b15c7c83e873",
        "build_id": "de104ddaca91438807b21688baf08455d5ade20c",
    },
}


@dataclass(frozen=True)
class TargetSymbol:
    module: str
    name: str
    rva: int
    symbol_type: int
    binding: int
    profile_size: int
    signature: str = ""


TARGET_SYMBOLS = [
    TargetSymbol("libsdk_jni.so", "_ZN3uav3sdk17g_pModuleMediatorE", 0x05344600, STT_OBJECT, STB_GLOBAL, 8),
    TargetSymbol("libsdk_jni.so", "_ZN3uav3sdk14ModuleMediator16GetFrameworkCoreEv", 0x01D54FF8, STT_FUNC, STB_GLOBAL, 56, "091842f9690100b4090100f9091c42f9"),
    TargetSymbol("libsdk_jni.so", "_ZN3uav3sdk16SDKFrameworkCore6GetKeyEjjjjjRKNSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEE", 0x025006BC, STT_FUNC, STB_GLOBAL, 52, "29690190290940f9e00308aa29014079"),
    TargetSymbol("libsdk_jni.so", "_ZN3uav3sdk13HardwareLayer14GetAbstractionERKNSt6__ndk16vectorIjNS2_9allocatorIjEEEE", 0x0250D6C0, STT_FUNC, STB_GLOBAL, 8, "00800091af8aad14"),
    TargetSymbol("libsdk_jni.so", "_ZN3uav3sdk15BaseAbstraction18GetCharacteristicsERKNS0_8CacheKeyE", 0x02515D94, STT_FUNC, STB_GLOBAL, 52, "fd7bbea9f30b00f9fd030091f30300aa"),
    TargetSymbol("libsdk_jni.so", "_ZNK3uav3sdk15BaseAbstraction11GetDeviceIDEv", 0x025194C8, STT_FUNC, STB_GLOBAL, 8, "00e040b9c0035fd6"),
    TargetSymbol("libsdk_jni.so", "_ZNK3uav3sdk15BaseAbstraction12GetProductIDEv", 0x025194D0, STT_FUNC, STB_GLOBAL, 8, "009840b9c0035fd6"),
    TargetSymbol("libsdk_jni.so", "_ZNK3uav3sdk15BaseAbstraction16GetAbstractionIDEv", 0x025194D8, STT_FUNC, STB_GLOBAL, 8, "00a040b9c0035fd6"),
    TargetSymbol("libsdk_jni.so", "_ZNK3uav3sdk15BaseAbstraction17GetComponentIndexEv", 0x02519B10, STT_FUNC, STB_GLOBAL, 8, "00e440b9c0035fd6"),
    TargetSymbol("libsdk_jni.so", "_ZNSt6__ndk119__shared_weak_count4lockEv", 0x01D2F300, STT_FUNC, STB_GLOBAL, 84, "5f2403d5082000910afddfc85f0500b1"),
    TargetSymbol("libsdk_jni.so", "_ZNSt6__ndk119__shared_weak_count16__release_sharedEv", 0x01D2F244, STT_FUNC, STB_GLOBAL, 136, "3f2303d5fd7bbea9f44f01a9fd030091"),
    TargetSymbol("libsdk_jni.so", "_ZNSt6__ndk119__shared_weak_count14__release_weakEv", 0x01D2F2CC, STT_FUNC, STB_GLOBAL, 52, "5f2403d50840009109fddfc8e90000b4"),
    TargetSymbol("libsdk_jni.so", "_ZNSt6__ndk112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEE6__initEPKcm", 0x01D30EE8, STT_FUNC, STB_WEAK, 144, "3f2303d5fd7bbda9f65701a9f44f02a9"),
    TargetSymbol("libsdk_jni.so", "_ZNSt6__ndk112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEED2Ev", 0x01D30BCC, STT_FUNC, STB_WEAK, 24, "5f2403d50800403948000037c0035fd6"),
    TargetSymbol("libsdk_jni.so", "_ZN3uav3sdk8CacheKeyD2Ev", 0x04A32A48, STT_FUNC, STB_WEAK, 68, "fd7bbea9f30b00f9fd030091f30300aa"),
    TargetSymbol("libsdk_jni.so", "_ZTVN3uav3sdk13HardwareLayerE", 0x050F1250, STT_OBJECT, STB_GLOBAL, 0x70),
    TargetSymbol("libsdk_jni.so", "_ZTVN3uav3sdk3key6MixAbsINS0_32UAV77FlightControllerAbstractionENS1_11UAV139FCAbsEEE", 0x05100F88, STT_OBJECT, STB_WEAK, 0x20),
    TargetSymbol("libsdk_key_value.so", "_ZNK3uav3sdk8CacheKey11GetPrefixesEv", 0x007EAB64, STT_FUNC, STB_GLOBAL, 8, "00c00091c0035fd6"),
    TargetSymbol("libsdk_key_value.so", "_ZN3uav3sdk15Characteristics7InvalidE", 0x00C19D78, STT_OBJECT, STB_GLOBAL, 56),
    TargetSymbol("libsdk_base.so", "_ZN3uav4core18GlobalPacketStatus8instanceEv", 0x002EC280, STT_FUNC, STB_GLOBAL, 168, "fd7bbea9f44f01a9fd03009188230090"),
    TargetSymbol("libsdk_base.so", "_ZN3uav4core18GlobalPacketStatus20GetGlobalSenderIndexEv", 0x002EC328, STT_FUNC, STB_GLOBAL, 24, "080040f9680000b400fddf08c0035fd6"),
]


def audit_target_samples(project_dir: Path) -> None:
    del project_dir
    research_dir = research_fixture_root()
    parsed: dict[str, ExactElf] = {}
    dynsyms: dict[str, dict[str, list[tuple[int, int, int, int, int]]]] = {}
    for module_name, profile in MODULE_PROFILES.items():
        path = research_dir / str(profile["relative"])
        require(path.is_file(), f"missing exact target sample: {path}")
        require(sha256_file(path) == profile["sha256"], f"target SHA mismatch: {module_name}")
        elf = ExactElf(path)
        require(elf.build_id().hex() == profile["build_id"], f"build-id mismatch: {module_name}")
        parsed[module_name] = elf
        dynsyms[module_name] = elf.true_dynsym()

    require(len(TARGET_SYMBOLS) == 21, "target symbol manifest cardinality")
    for target in TARGET_SYMBOLS:
        matches = dynsyms[target.module].get(target.name, [])
        require(len(matches) == 1, f"true dynsym cardinality: {target.name}")
        info, other, section, value, symbol_size = matches[0]
        require(info >> 4 == target.binding, f"dynsym binding mismatch: {target.name}")
        require(info & 0xF == target.symbol_type, f"dynsym type mismatch: {target.name}")
        require(other & 0x3 == STV_DEFAULT, f"dynsym visibility mismatch: {target.name}")
        require(section != SHN_UNDEF, f"undefined target dynsym: {target.name}")
        require(value == target.rva, f"dynsym RVA mismatch: {target.name}")
        if target.symbol_type == STT_FUNC:
            require(symbol_size == target.profile_size, f"function st_size mismatch: {target.name}")
        else:
            require(
                0 < target.profile_size <= symbol_size,
                f"object profile range exceeds dynsym size: {target.name}",
            )
        if target.signature:
            signature_size = len(bytes.fromhex(target.signature))
            require(
                0 < signature_size <= target.profile_size <= symbol_size,
                f"instruction signature exceeds dynsym size: {target.name}",
            )
            require(
                parsed[target.module].bytes_at(target.rva, signature_size).hex() == target.signature,
                f"instruction signature mismatch: {target.name}",
            )


def unique_relative_relocation(
    elf: ExactElf,
    relocations: list[tuple[int, int, int, int]],
    string_value: str,
) -> tuple[int, int, int, int]:
    string_rva = elf.unique_cstring_rva(string_value)
    matches = [
        relocation
        for relocation in relocations
        if relocation[1] == R_AARCH64_RELATIVE
        and relocation[2] == 0
        and relocation[3] == string_rva
    ]
    require(len(matches) == 1, f"compiled string relocation cardinality: {string_value}")
    return matches[0]


def audit_compiled_target_profile(elf: ExactElf) -> None:
    """Prove that the packaged runtime tables equal the independently checked manifest."""
    relocations = elf.rela_entries()
    module_names = list(MODULE_PROFILES)

    module_entry_rvas: list[int] = []
    for module_index, module_name in enumerate(module_names):
        relocation = unique_relative_relocation(elf, relocations, module_name)
        entry_rva = relocation[0]
        module_entry_rvas.append(entry_rva)
        raw = elf.bytes_at(entry_rva, 32)
        require(raw[:8] == b"\0" * 8, f"compiled module pointer storage: {module_name}")
        require(
            raw[8:28] == bytes.fromhex(str(MODULE_PROFILES[module_name]["build_id"])),
            f"compiled module build-id mismatch: {module_name}",
        )
        require(raw[28:32] == b"\0" * 4, f"compiled module padding mismatch: {module_name}")
        if module_index:
            require(
                entry_rva == module_entry_rvas[0] + module_index * 32,
                "compiled module profile is not one exact contiguous table",
            )

    symbol_entry_rvas: list[int] = []
    for symbol_index, target in enumerate(TARGET_SYMBOLS):
        relocation = unique_relative_relocation(elf, relocations, target.name)
        entry_rva = relocation[0] - 8
        symbol_entry_rvas.append(entry_rva)
        raw = elf.bytes_at(entry_rva, 56)
        module_id, kind, pointer_storage, rva, profile_size, signature_size = struct.unpack_from(
            "<IIQQQQ", raw, 0
        )
        expected_module_id = module_names.index(target.module)
        expected_kind = 0 if target.symbol_type == STT_FUNC else 1
        expected_signature = bytes.fromhex(target.signature)
        require(module_id == expected_module_id, f"compiled module id mismatch: {target.name}")
        require(kind == expected_kind, f"compiled symbol kind mismatch: {target.name}")
        require(pointer_storage == 0, f"compiled symbol pointer storage: {target.name}")
        require(rva == target.rva, f"compiled profile RVA mismatch: {target.name}")
        require(profile_size == target.profile_size, f"compiled profile size mismatch: {target.name}")
        require(
            signature_size == len(expected_signature),
            f"compiled signature size mismatch: {target.name}",
        )
        require(
            raw[40:56] == expected_signature.ljust(16, b"\0"),
            f"compiled signature bytes mismatch: {target.name}",
        )
        if symbol_index:
            require(
                entry_rva == symbol_entry_rvas[0] + symbol_index * 56,
                "compiled symbol profile is not one exact contiguous table",
            )

    require(
        module_entry_rvas[-1] + 32 == symbol_entry_rvas[0],
        "compiled module/symbol profile table boundary mismatch",
    )


def decode_aarch64_bl_target(address: int, instruction: int) -> int:
    require(instruction & 0xFC000000 == 0x94000000, f"not AArch64 BL at 0x{address:x}")
    immediate = instruction & 0x03FFFFFF
    if immediate & 0x02000000:
        immediate -= 0x04000000
    return address + immediate * 4


def audit_compiled_exception_gate(elf: ExactElf) -> None:
    """Bind the source-level gate claim to the exact packaged machine-code control flow."""
    gate_rva = 0x0FE4
    gate_check_rva = 0x4E38
    dormant_helper_rva = 0x4E4C
    gate_call_rva = 0x4C94
    gate_true_branch_rva = 0x4CB0
    false_exit_branch_rva = 0x4CD8
    dormant_call_rva = 0x4CE4

    require(elf.bytes_at(gate_rva, 4) == b"\0" * 4, "compiled exception gate is not zero")
    gate_load = elf.load_for_range(gate_rva, 4)
    require(gate_load.flags & PF_R != 0, "compiled exception gate is not readable")
    require(gate_load.flags & (PF_W | PF_X) == 0, "compiled exception gate is writable/executable")
    for relocation_offset, _kind, _symbol, _addend in elf.rela_entries():
        require(
            not (gate_rva <= relocation_offset < gate_rva + 4),
            "compiled exception gate has a relocation",
        )

    gate_check = bytes.fromhex(
        "e8ffff90"  # adrp x8, gate page
        "08e54fb9"  # ldr w8, [x8, #0xfe4]
        "08050071"  # subs w8, w8, #1
        "e0179f1a"  # cset w0, eq
        "c0035fd6"  # ret
    )
    require(elf.bytes_at(gate_check_rva, len(gate_check)) == gate_check, "gate check code mismatch")
    require(elf.data.count(gate_check) == 1, "gate check code cardinality")

    # Lock the full data-flow block, not only its branch endpoints.  This proves that the value
    # returned by the fixed-zero check is normalized, stored, reloaded and used by the CBNZ;
    # replacing the reload with (for example) ``mov w8, #1`` must be rejected.
    gate_control_block = bytes.fromhex(
        "69000094"  # bl gate_check
        "08000071"  # subs w8, w0, #0
        "e8079f1a"  # cset w8, ne
        "e91340f9"  # ldr x9, [sp, #0x20]
        "281900b9"  # str w8, [x9, #0x18]
        "e81340f9"  # ldr x8, [sp, #0x20]
        "081940b9"  # ldr w8, [x8, #0x18]
        "68010035"  # cbnz w8, admitted block
        "01000014"  # b false block
        "e91340f9"  # false: ldr x9, [sp, #0x20]
        "a8008052"  # mov w8, #5 (EXCEPTION_BOUNDARY_UNPROVEN)
        "280100b9"  # str w8, [x9]
        "e0830591"  # add x0, sp, #0x160
        "b2faff97"  # bl close module handles
        "e81340f9"  # ldr x8, [sp, #0x20]
        "080140b9"  # ldr w8, [x8]
        "e82f00b9"  # str w8, [sp, #0x2c]
        "0e000014"  # b after dormant helper block
    )
    require(
        elf.bytes_at(gate_call_rva, len(gate_control_block)) == gate_control_block,
        "gate result data-flow/control block mismatch",
    )
    require(elf.data.count(gate_control_block) == 1, "gate control block cardinality")

    gate_call = struct.unpack("<I", elf.bytes_at(gate_call_rva, 4))[0]
    dormant_call = struct.unpack("<I", elf.bytes_at(dormant_call_rva, 4))[0]
    require(
        decode_aarch64_bl_target(gate_call_rva, gate_call) == gate_check_rva,
        "gate call target mismatch",
    )
    require(
        decode_aarch64_bl_target(dormant_call_rva, dormant_call) == dormant_helper_rva,
        "dormant helper call target mismatch",
    )
    require(
        struct.unpack("<I", elf.bytes_at(gate_true_branch_rva, 4))[0] == 0x35000168,
        "gate true CBNZ edge mismatch",
    )
    require(
        struct.unpack("<I", elf.bytes_at(false_exit_branch_rva, 4))[0] == 0x1400000E,
        "gate false exit edge mismatch",
    )

    executable_calls_to_gate: list[int] = []
    executable_calls_to_helper: list[int] = []
    for header in elf.program_headers:
        if header.kind != PT_LOAD or header.flags & PF_X == 0:
            continue
        for address in range(header.vaddr, header.vaddr + header.file_size - 3, 4):
            instruction = struct.unpack("<I", elf.bytes_at(address, 4))[0]
            if instruction & 0xFC000000 != 0x94000000:
                continue
            target = decode_aarch64_bl_target(address, instruction)
            if target == gate_check_rva:
                executable_calls_to_gate.append(address)
            if target == dormant_helper_rva:
                executable_calls_to_helper.append(address)
    require(executable_calls_to_gate == [gate_call_rva], "gate check call-site cardinality")
    require(executable_calls_to_helper == [dormant_call_rva], "dormant helper call-site cardinality")

    # The only helper call is in the CBNZ-taken block.  The not-taken block exits over it.
    require(gate_true_branch_rva < false_exit_branch_rva < dormant_call_rva, "gate block order")


def audit_source(project_dir: Path) -> None:
    cpp_dir = project_dir / "app/src/main/cpp"
    source_names = sorted(
        path.name
        for path in cpp_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".c", ".h", ".s", ".asm"}
    )
    require(
        source_names == [
            "abi_shims.S", "abi_shims.h", "agent.c", "module_inspect.c", "module_inspect.h",
            "note_parser.c", "note_parser.h", "route_policy.c", "route_policy.h",
            "route_resolver.c", "route_resolver.h", "target_profile.c", "target_profile.h",
        ],
        f"unexpected native source inventory: {source_names}",
    )

    cmake = (cpp_dir / "CMakeLists.txt").read_text(encoding="utf-8")
    require("LANGUAGES C ASM" in cmake, "CMake does not enable explicit ASM shims")
    require(cmake.count("-nostartfiles") == 1, "no-constructor link boundary mismatch")
    require(cmake.count("-mno-outline-atomics") == 1, "outline atomics boundary mismatch")
    require("ANDROID_STL=none" in (project_dir / "app/build.gradle.kts").read_text(encoding="utf-8"), "carrier links an STL")

    assembly = (cpp_dir / "abi_shims.S").read_text(encoding="utf-8")
    require(assembly.count("mov x8, x1") == 3, "x8 hidden-sret move count mismatch")
    require(assembly.count("br x9") == 3 and "blr" not in assembly, "sret shims are not tail bridges")
    require("ldr x10, [sp]" in assembly and "mov x6, x10" in assembly, "GetKey stack argument bridge absent")

    agent = (cpp_dir / "agent.c").read_text(encoding="utf-8")
    route = (cpp_dir / "route_resolver.c").read_text(encoding="utf-8")
    module = (cpp_dir / "module_inspect.c").read_text(encoding="utf-8")
    profile_source = (cpp_dir / "target_profile.c").read_text(encoding="utf-8")
    combined = "\n".join(path.read_text(encoding="utf-8") for path in cpp_dir.iterdir() if path.suffix.lower() in {".c", ".h", ".s"})

    require(agent.count("RemoteIDModelImpl$electronicIDBroadcastOn$2$1;") == 1, "on anchor mismatch")
    require(agent.count("RemoteIDModelImpl$electronicIDBroadcastExisted$2$1;") == 1, "gate anchor mismatch")
    require(agent.count("GetLoadedClasses") == 1 and agent.count("GetClassSignature") == 1, "anchor enumeration surface mismatch")
    require(agent.count("GetClassLoader") == 1 and agent.count("IsSameObject") == 1, "same-loader gate mismatch")
    require(len(re.findall(r'"Lcom/', agent)) == 2, "agent enumerates non-EID class anchors")

    require(route.count("static const volatile uint32_t g_exception_boundary_admitted = 0u;") == 1, "exception gate is not fixed zero")
    require(route.count("g_exception_boundary_admitted") == 2, "exception gate has a hidden mutation/reference")
    run_marker = route.index("enum FinduasRouteStatus finduas_route_resolver_run")
    gate_index = route.index("if (diagnostic->exception_boundary_admitted == 0u)", run_marker)
    admitted_call_index = route.index("status = run_admitted_route_calls(&api, diagnostic);", run_marker)
    require(gate_index < admitted_call_index, "target call path is not downstream of hard exception gate")
    require("FINDUAS_ROUTE_STATUS_EXCEPTION_BOUNDARY_UNPROVEN" in route, "exception failure status absent")

    require(module.count("dlopen(module->path, RTLD_NOW | RTLD_NOLOAD)") == 1, "not exact RTLD_NOLOAD-only open")
    require(module.count("dlopen(") == 1 and "RTLD_DEFAULT" not in combined, "plain/default dynamic lookup exists")
    require(module.count("dlsym(") == 1 and module.count("dladdr(") == 1, "true dynsym/dladdr validation surface mismatch")
    require("(uintptr_t)symbol != expected_address" in module, "base+RVA equality gate absent")
    require("memcmp(\n            symbol,\n            profile->instruction_signature,\n            profile->signature_size)" in module, "instruction signature gate absent")
    require("profile->signature_size > profile->symbol_size" in module, "signature-size bound absent")
    require("profile->signature_size > FINDUAS_INSTRUCTION_SIGNATURE_SIZE" in module, "signature-cap bound absent")
    require("finduas_parse_unique_gnu_build_id" in module, "in-memory GNU build-id gate absent")

    require(profile_source.count("FUNCTION_PROFILE(") == 18, "function profile macro/use count mismatch")
    require(profile_source.count("OBJECT_PROFILE(") == 5, "object profile macro/use count mismatch")
    for target in TARGET_SYMBOLS:
        require(profile_source.count(f'"{target.name}"') == 1, f"target source symbol cardinality: {target.name}")

    require("characteristics_before == invalid_characteristics" in route, "Invalid singleton first gate absent")
    require("characteristics_after == invalid_characteristics" in route, "Invalid singleton second gate absent")
    require("characteristics_after != characteristics_before" in route, "Characteristics identity epoch gate absent")
    require("abstraction_after.control != abstraction_before.control" in route, "control-block epoch gate absent")
    require("release_weak(framework_weak.control)" in route, "weak release absent")
    for owner in (
        "abstraction_after.control",
        "abstraction_before.control",
        "framework_strong.control",
    ):
        require(route.count(f"release_shared({owner})") == 1, f"shared owner cleanup mismatch: {owner}")
    require("release_shared(framework_weak.control)" not in route, "weak owner released as shared")
    require("cache_key_dtor(cache_key)" in route and "string_dtor(target_string)" in route, "target destructor pair absent")

    for forbidden in (
        "GetInstance",
        "JNIRawData",
        "native_SendData",
        "native_SendDataWithTcpPort",
        "JNIKeyValue",
        "native_get",
        "native_set",
        "RegisterObserver",
        "AddProductConnectionObserver",
        "AddDatalinkObserver",
        "127.0.0.1",
        "40007",
        "40009",
        "android/os/Binder",
    ):
        require(forbidden not in combined, f"forbidden control/observer route: {forbidden}")
    for pattern, label in (
        (r"\b(?:socket|connect|bind|listen|accept|send|sendto|recv|recvfrom)\s*\(", "network API"),
        (r"\b(?:open|openat|creat|fopen|write|pwrite|rename|unlink)\s*\(", "filesystem API"),
        (r"\b(?:fork|vfork|execve|system|popen|ptrace|process_vm_readv)\s*\(", "process API"),
    ):
        require(re.search(pattern, combined) is None, f"source contains forbidden {label}")

    audit_target_samples(project_dir)


def audit_manifest(aapt: Path, apk: Path) -> None:
    manifest = run_checked([str(aapt), "dump", "xmltree", str(apk), "AndroidManifest.xml"])
    elements = re.findall(r"^\s*E:\s+([^\s(]+)", manifest, flags=re.MULTILINE)
    require(elements == ["manifest", "uses-sdk", "application"], f"unexpected elements: {elements}")
    require(f'package="{EXPECTED_PACKAGE}"' in manifest, "unexpected package")
    for label, pattern in {
        "versionCode 1": r"android:versionCode[^\n]*\(type 0x10\)0x1(?:\s|$)",
        "versionName": r'android:versionName[^\n]*="0\.1\.0-offline-unadmitted"',
        "minSdk 30": r"android:minSdkVersion[^\n]*\(type 0x10\)0x1e(?:\s|$)",
        "targetSdk 30": r"android:targetSdkVersion[^\n]*\(type 0x10\)0x1e(?:\s|$)",
        "fixed label": r'android:label[^\n]*="FindUAS EID route resolver V2\.1 offline carrier"',
        "hasCode false": r"android:hasCode[^\n]*\(type 0x12\)0x0(?:\s|$)",
        "debuggable true": r"android:debuggable[^\n]*\(type 0x12\)0xffffffff(?:\s|$)",
        "allowBackup false": r"android:allowBackup[^\n]*\(type 0x12\)0x0(?:\s|$)",
        "extractNativeLibs true": r"android:extractNativeLibs[^\n]*\(type 0x12\)0xffffffff(?:\s|$)",
        "cleartext false": r"android:usesCleartextTraffic[^\n]*\(type 0x12\)0x0(?:\s|$)",
    }.items():
        require(re.search(pattern, manifest) is not None, f"manifest missing {label}")
    require("E: uses-permission" not in manifest, "manifest declares a permission")
    require("android:sharedUserId" not in manifest, "manifest requests a shared UID")
    for component in ("activity", "service", "receiver", "provider", "instrumentation"):
        require(f"E: {component}" not in manifest, f"manifest declares {component}")


def audit_elf(ndk_bin: Path, library_path: Path) -> None:
    readelf = ndk_bin / "llvm-readelf"
    nm = ndk_bin / "llvm-nm"
    strings = ndk_bin / "llvm-strings"

    header = run_checked([str(readelf), "-h", str(library_path)])
    require("Class:                             ELF64" in header, "carrier is not ELF64")
    require("Machine:                           AArch64" in header, "carrier is not AArch64")

    carrier_elf = ExactElf(library_path)
    audit_compiled_target_profile(carrier_elf)
    audit_compiled_exception_gate(carrier_elf)

    dynamic = run_checked([str(readelf), "-d", str(library_path)])
    needed = set(re.findall(r"Shared library: \[([^]]+)\]", dynamic))
    require(needed == EXPECTED_NEEDED, f"unexpected dependencies: {sorted(needed)}")
    require("Library soname: [libfinduas_eid_route_resolver_v2_1.so]" in dynamic, "unexpected SONAME")
    require(all(tag not in dynamic for tag in ("(INIT)", "(INIT_ARRAY)", "(PREINIT_ARRAY)", "(FINI)", "(FINI_ARRAY)")), "constructor/destructor table present")
    require(all(tag not in dynamic for tag in ("(TEXTREL)", "(RPATH)", "(RUNPATH)")), "unsafe ELF dynamic path/text relocation")

    defined = dynamic_symbol_names(run_checked([str(nm), "-D", "--defined-only", "--extern-only", str(library_path)]))
    require(defined == {"Agent_OnAttach"}, f"unexpected exports: {sorted(defined)}")
    undefined = dynamic_symbol_names(run_checked([str(nm), "-D", "--undefined-only", str(library_path)]))
    require(undefined == EXPECTED_UNDEFINED, f"unexpected imports: {sorted(undefined)}")
    for forbidden in ("socket", "connect", "open", "openat", "write", "ptrace", "fork", "execve", "getenv", "__system_property_get"):
        require(forbidden not in undefined, f"forbidden import: {forbidden}")

    printable = run_checked([str(strings), "-a", str(library_path)])
    for required in (
        "FindUAS-EID-Route-V21",
        "FINDUAS_EID_ROUTE_V21 error=",
        "libsdk_jni.so",
        "libsdk_key_value.so",
        "libsdk_base.so",
        "EIDSwitch",
        "Characteristics7InvalidE",
    ):
        require(required in printable, f"required binary evidence absent: {required}")
    for forbidden in ("GetInstance", "JNIRawData", "native_SendData", "127.0.0.1", "40007", "40009", "/data/", "/sdcard/"):
        require(forbidden not in printable, f"forbidden binary string: {forbidden}")

    library_bytes = library_path.read_bytes()
    # Hidden names are stripped from the packaged SO, so validate each exact bridge byte sequence
    # directly.  llvm-objdump renders AArch64 raw words in host textual order, which is not the
    # byte order used by an in-file signature.
    for signature in (
        "e9 03 00 aa e8 03 01 aa e0 03 02 aa 20 01 1f d6",
        "ea 03 40 f9 e9 03 00 aa e8 03 01 aa e0 03 02 aa",
        "e9 03 00 aa e8 03 01 aa e0 03 02 aa e1 03 03 aa",
    ):
        require(
            library_bytes.count(bytes.fromhex(signature)) == 1,
            "AArch64 x8 sret shim signature cardinality",
        )

    require(library_bytes.count(b"\x7fELF") == 1, "embedded ELF payload present")
    require(b"dex\n" not in library_bytes, "embedded DEX payload present")
    require(b"PK\x03\x04" not in library_bytes, "embedded ZIP payload present")


def audit_readme(project_dir: Path, apk_digest: str, apk_size: int, so_digest: str, so_size: int) -> None:
    readme = (project_dir / "README.md").read_text(encoding="utf-8")
    require(f"APK SHA-256: `{apk_digest}`" in readme, "README APK digest mismatch")
    require(f"APK bytes: `{apk_size}`" in readme, "README APK size mismatch")
    require(f"packaged SO SHA-256: `{so_digest}`" in readme, "README SO digest mismatch")
    require(f"packaged SO bytes: `{so_size}`" in readme, "README SO size mismatch")
    require("DO NOT INSTALL OR ATTACH" in readme, "README warning absent")
    require("EXCEPTION_BOUNDARY_UNPROVEN" in readme, "README does not disclose hard gate")
    for document in ("LIVE_ADMISSION.md", "ZERO_SEND_CONTRACT.md"):
        require((project_dir / document).is_file(), f"missing project document: {document}")


def audit_apk(apk: Path, project_dir: Path, sdk_root: Path, ndk_root: Path) -> None:
    require(apk.is_file(), f"missing APK: {apk}")
    build_tools = sdk_root / "build-tools/35.0.0"
    aapt = build_tools / "aapt"
    apksigner = build_tools / "apksigner"
    zipalign = build_tools / "zipalign"
    ndk_bin = ndk_root / "toolchains/llvm/prebuilt/darwin-x86_64/bin"

    with zipfile.ZipFile(apk) as archive:
        entries = archive.namelist()
        require(len(entries) == len(set(entries)), "duplicate ZIP entry")
        require(set(entries) == EXPECTED_ZIP_ENTRIES, f"unexpected ZIP inventory: {entries}")
        require(not any(re.fullmatch(r"classes\d*\.dex", entry) for entry in entries), "packaged DEX present")
        native_info = archive.getinfo(EXPECTED_NATIVE_ENTRY)
        require(native_info.compress_type == zipfile.ZIP_DEFLATED, "native library is not compressed")
        library_bytes = archive.read(EXPECTED_NATIVE_ENTRY)

    inspection_mirror = project_dir / "build/inspect.so"
    require(inspection_mirror.is_file() and not inspection_mirror.is_symlink(), "missing regular inspection mirror")
    require(inspection_mirror.read_bytes() == library_bytes, "inspection mirror differs from packaged SO")

    audit_manifest(aapt, apk)
    run_checked([str(zipalign), "-c", "4", str(apk)])
    signer_output = run_checked([str(apksigner), "verify", "--verbose", "--print-certs", str(apk)])
    for line in (
        "Verifies",
        "Verified using v1 scheme (JAR signing): false",
        "Verified using v2 scheme (APK Signature Scheme v2): true",
        "Verified using v3 scheme (APK Signature Scheme v3): false",
        "Verified using v3.1 scheme (APK Signature Scheme v3.1): false",
        "Verified using v4 scheme (APK Signature Scheme v4): false",
        "Verified for SourceStamp: false",
        "Number of signers: 1",
    ):
        require(line in signer_output, f"unexpected signing profile: {line}")
    match = re.search(r"certificate SHA-256 digest:\s*([0-9a-fA-F]+)", signer_output)
    require(match is not None, "signer digest absent")
    signer_digest = match.group(1).lower()
    require(signer_digest == EXPECTED_SIGNER_CERT_SHA256, "unexpected signer")
    require(signer_digest != DJI_PLATFORM_CERT_SHA256, "DJI platform signer unexpectedly used")

    with tempfile.TemporaryDirectory(prefix="finduas-route-v21-audit-") as temporary:
        library_path = Path(temporary) / "libfinduas_eid_route_resolver_v2_1.so"
        library_path.write_bytes(library_bytes)
        audit_elf(ndk_bin, library_path)

    apk_digest = sha256_file(apk)
    so_digest = sha256_bytes(library_bytes)
    audit_readme(project_dir, apk_digest, apk.stat().st_size, so_digest, len(library_bytes))

    print(f"APK SHA-256: {apk_digest}")
    print(f"Packaged SO SHA-256: {so_digest}")
    print(f"Signer certificate SHA-256: {signer_digest}")
    print(f"Native entry: {EXPECTED_NATIVE_ENTRY} ({len(library_bytes)} bytes, compressed)")
    print("Manifest: no permissions, no components, no shared UID, hasCode=false")
    print("Packaged/embedded DEX: absent")
    print("Target profile: packaged tables equal 3 build-ids and 21 true dynsym/RVA/size/signature targets")
    print("Runtime: RTLD_NOLOAD only; packaged zero/RO/no-reloc gate uniquely dominates dormant route")
    print("Control surface: no GET/listen/SET/send/observer/socket/Binder/file/process route")
    print("AUDIT PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("apk", type=Path)
    arguments = parser.parse_args()
    configure_java_runtime()

    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    sdk_setting = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    require(bool(sdk_setting), "set ANDROID_SDK_ROOT or ANDROID_HOME")
    sdk_root = Path(str(sdk_setting)).expanduser().resolve()
    ndk_root = Path(os.environ.get("FINDUAS_ROUTE_V21_NDK_ROOT", str(sdk_root / "ndk/27.2.12479018"))).resolve()

    audit_source(project_dir)
    audit_apk(arguments.apk.resolve(), project_dir, sdk_root, ndk_root)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditFailure as error:
        print(f"AUDIT FAILED: {error}")
        raise SystemExit(1)
