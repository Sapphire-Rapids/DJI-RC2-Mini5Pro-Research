#!/usr/bin/env python3
"""Locate direct AArch64 ADR/ADRP references to selected ELF virtual addresses.

This is an offline triage helper for stripped vendor libraries whose section table is
damaged but whose executable PT_LOAD ranges remain valid.  It does not modify the ELF.
"""

from __future__ import annotations

import argparse
import struct
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from capstone import CS_ARCH_ARM64, CS_MODE_ARM, Cs
from capstone.arm64 import ARM64_OP_IMM, ARM64_OP_MEM, ARM64_OP_REG


PT_LOAD = 1
PF_X = 1


@dataclass(frozen=True)
class Segment:
    offset: int
    virtual_address: int
    file_size: int


def executable_segments(blob: bytes) -> list[Segment]:
    if blob[:4] != b"\x7fELF" or blob[4] != 2 or blob[5] != 1:
        raise ValueError("expected a little-endian ELF64 file")
    program_offset = struct.unpack_from("<Q", blob, 32)[0]
    entry_size = struct.unpack_from("<H", blob, 54)[0]
    entry_count = struct.unpack_from("<H", blob, 56)[0]
    if entry_size < 56:
        raise ValueError("invalid ELF64 program-header size")

    result: list[Segment] = []
    for index in range(entry_count):
        offset = program_offset + index * entry_size
        p_type, p_flags, p_offset, p_vaddr, _, p_filesz, _, _ = struct.unpack_from(
            "<IIQQQQQQ", blob, offset
        )
        if p_type == PT_LOAD and p_flags & PF_X and p_filesz:
            if p_offset + p_filesz > len(blob):
                raise ValueError("executable segment extends beyond the input file")
            result.append(Segment(p_offset, p_vaddr, p_filesz))
    return result


def parse_target(text: str) -> tuple[int, str]:
    address_text, separator, label = text.partition("=")
    address = int(address_text, 0)
    return address, label if separator else address_text


def format_instruction(instruction) -> str:
    return f"0x{instruction.address:08x}: {instruction.mnemonic:<8} {instruction.op_str}"


def scan_segment(blob: bytes, segment: Segment, targets: dict[int, str]) -> None:
    engine = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    engine.detail = True
    # The vendor ELF intentionally has a damaged section table and executable LOAD ranges
    # containing non-code islands.  Continue after those bytes so later functions are scanned.
    engine.skipdata = True
    recent = deque(maxlen=12)
    page_by_register: dict[int, tuple[int, int]] = {}
    contexts: list[tuple[int, str, list[str]]] = []

    for instruction in engine.disasm(
        blob[segment.offset : segment.offset + segment.file_size],
        segment.virtual_address,
    ):
        if instruction.id == 0:
            # Capstone's SKIPDATA pseudo-instruction has no operand/register detail and
            # also marks a boundary across which an ADRP pairing must not be carried.
            page_by_register.clear()
            recent.clear()
            continue
        recent.append(instruction)
        mnemonic = instruction.mnemonic
        operands = instruction.operands
        hit_address: int | None = None
        hit_kind = ""

        if mnemonic in {"adr", "adrp"} and len(operands) >= 2:
            if operands[0].type == ARM64_OP_REG and operands[1].type == ARM64_OP_IMM:
                immediate = operands[1].imm
                if mnemonic == "adr" and immediate in targets:
                    hit_address = immediate
                    hit_kind = "ADR"
                if mnemonic == "adrp":
                    page_by_register[operands[0].reg] = (immediate, instruction.address)

        if mnemonic == "add" and len(operands) >= 3:
            if (
                operands[0].type == ARM64_OP_REG
                and operands[1].type == ARM64_OP_REG
                and operands[2].type == ARM64_OP_IMM
                and operands[1].reg in page_by_register
            ):
                page, producer_address = page_by_register[operands[1].reg]
                if instruction.address - producer_address <= 64:
                    candidate = page + operands[2].imm
                    if candidate in targets:
                        hit_address = candidate
                        hit_kind = "ADRP+ADD"

        if mnemonic.startswith("ldr") and len(operands) >= 2:
            if operands[1].type == ARM64_OP_MEM and operands[1].mem.base in page_by_register:
                page, producer_address = page_by_register[operands[1].mem.base]
                if instruction.address - producer_address <= 64:
                    candidate = page + operands[1].mem.disp
                    if candidate in targets:
                        hit_address = candidate
                        hit_kind = "ADRP+LDR"

        if hit_address is not None:
            contexts.append(
                (
                    instruction.address,
                    f"{targets[hit_address]} @ 0x{hit_address:x} via {hit_kind}",
                    [format_instruction(item) for item in recent],
                )
            )

        try:
            _, written = instruction.regs_access()
        except Exception:
            written = []
        preserve = operands[0].reg if mnemonic == "adrp" and operands else None
        for register in written:
            if register != preserve:
                page_by_register.pop(register, None)

    for _, label, context in contexts:
        print(f"\n{label}")
        for line in context:
            print(f"  {line}")
    if not contexts:
        print("No direct ADR/ADRP reference found in this executable segment.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("elf", type=Path)
    parser.add_argument(
        "target",
        nargs="+",
        help="virtual address, optionally followed by =label (for example 0x1234=KeyName)",
    )
    arguments = parser.parse_args()

    blob = arguments.elf.read_bytes()
    targets = dict(parse_target(item) for item in arguments.target)
    segments = executable_segments(blob)
    if not segments:
        raise ValueError("no executable PT_LOAD segment")
    for segment in segments:
        print(
            f"Scanning executable PT_LOAD VA 0x{segment.virtual_address:x} "
            f"size 0x{segment.file_size:x}"
        )
        scan_segment(blob, segment, targets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
