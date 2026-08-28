#!/usr/bin/env python3
"""Disassemble one virtual-address range from an ELF64 PT_LOAD mapping."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM64, CS_MODE_ARM, Cs


PT_LOAD = 1


def virtual_to_file(blob: bytes, address: int, size: int) -> int:
    if blob[:4] != b"\x7fELF" or blob[4] != 2 or blob[5] != 1:
        raise ValueError("expected little-endian ELF64")
    program_offset = struct.unpack_from("<Q", blob, 32)[0]
    entry_size = struct.unpack_from("<H", blob, 54)[0]
    entry_count = struct.unpack_from("<H", blob, 56)[0]
    for index in range(entry_count):
        offset = program_offset + index * entry_size
        p_type, _, p_offset, p_vaddr, _, p_filesz, _, _ = struct.unpack_from(
            "<IIQQQQQQ", blob, offset
        )
        if (
            p_type == PT_LOAD
            and p_vaddr <= address
            and address + size <= p_vaddr + p_filesz
        ):
            return p_offset + address - p_vaddr
    raise ValueError("requested virtual range is not file-backed by one PT_LOAD")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("elf", type=Path)
    parser.add_argument("start", type=lambda value: int(value, 0))
    parser.add_argument("end", type=lambda value: int(value, 0))
    arguments = parser.parse_args()
    if arguments.end <= arguments.start:
        raise ValueError("end must be greater than start")

    blob = arguments.elf.read_bytes()
    size = arguments.end - arguments.start
    file_offset = virtual_to_file(blob, arguments.start, size)
    engine = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    engine.skipdata = True
    for instruction in engine.disasm(blob[file_offset : file_offset + size], arguments.start):
        print(f"0x{instruction.address:08x}: {instruction.mnemonic:<8} {instruction.op_str}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
