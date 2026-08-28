#!/usr/bin/env python3
"""Read bytes from an ELF64 load virtual address using only stdlib.

The script is deliberately small and offline-friendly.  It translates a
virtual address through PT_LOAD program headers instead of assuming that a
virtual address is also a file offset.

Examples:
  python3 elf64_va_read.py lib.so 0x12379c8 4
  python3 elf64_va_read.py lib.so 0x12379c8 4 --tuple-hhhb
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


def parse_int(value: str) -> int:
    return int(value, 0)


def va_to_offset(blob: bytes, va: int, size: int) -> tuple[int, int]:
    if blob[:4] != b"\x7fELF" or blob[4] != 2:
        raise ValueError("expected an ELF64 file")
    prefix = "<" if blob[5] == 1 else ">"
    header = struct.unpack_from(prefix + "16sHHIQQQIHHHHHH", blob)
    phoff, phentsize, phnum = header[5], header[9], header[10]
    ph_fmt = prefix + "IIQQQQQQ"
    for index in range(phnum):
        p_type, _flags, p_offset, p_vaddr, _paddr, p_filesz, _memsz, _align = (
            struct.unpack_from(ph_fmt, blob, phoff + index * phentsize)
        )
        if p_type == 1 and p_vaddr <= va and va + size <= p_vaddr + p_filesz:
            return p_offset + (va - p_vaddr), index
    raise ValueError(f"VA range 0x{va:x}..0x{va + size:x} is not file-backed by PT_LOAD")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("elf", type=Path)
    parser.add_argument("address", type=parse_int)
    parser.add_argument("size", type=parse_int)
    parser.add_argument(
        "--tuple-hhhb",
        action="store_true",
        help="also decode the first four bytes as tuple<unsigned char,unsigned char,unsigned char,bool>",
    )
    args = parser.parse_args()

    blob = args.elf.read_bytes()
    offset, segment = va_to_offset(blob, args.address, args.size)
    value = blob[offset : offset + args.size]
    print(f"elf={args.elf}")
    print(f"va=0x{args.address:x} file_offset=0x{offset:x} pt_load_index={segment}")
    print("bytes=" + value.hex(" "))
    if args.tuple_hhhb:
        if len(value) < 4:
            raise ValueError("--tuple-hhhb requires size >= 4")
        print(
            "tuple<unsigned char,unsigned char,unsigned char,bool>="
            f"({value[0]}, {value[1]}, {value[2]}, {bool(value[3])})"
        )


if __name__ == "__main__":
    main()
