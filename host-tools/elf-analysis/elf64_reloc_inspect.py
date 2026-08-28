#!/usr/bin/env python3
"""Inspect ELF64 RELA targets in a virtual-address range.

This intentionally uses only Python's standard library so it works in the
offline RC 2 analysis environment.  It is aimed at Android arm64 shared
objects, but accepts either ELF endianness.

Examples:
  python3 elf64_reloc_inspect.py lib.so --range 0xa379f8:0xa37a80
  python3 elf64_reloc_inspect.py lib.so --at 0x38d9a00 --count 9
"""

from __future__ import annotations

import argparse
import dataclasses
import struct
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class Section:
    name: str
    sh_type: int
    addr: int
    offset: int
    size: int
    link: int
    entsize: int


class Elf64:
    def __init__(self, path: Path):
        self.path = path
        self.data = path.read_bytes()
        if self.data[:4] != b"\x7fELF" or self.data[4] != 2:
            raise ValueError(f"{path}: expected an ELF64 file")
        self.prefix = "<" if self.data[5] == 1 else ">"
        header = struct.unpack_from(self.prefix + "16sHHIQQQIHHHHHH", self.data)
        self.e_shoff = header[6]
        self.e_shentsize = header[11]
        self.e_shnum = header[12]
        self.e_shstrndx = header[13]
        raw_sections = []
        sh_fmt = self.prefix + "IIQQQQIIQQ"
        for index in range(self.e_shnum):
            raw_sections.append(
                struct.unpack_from(sh_fmt, self.data, self.e_shoff + index * self.e_shentsize)
            )
        shstr = raw_sections[self.e_shstrndx]
        shstr_data = self.data[shstr[4] : shstr[4] + shstr[5]]
        self.sections = []
        for raw in raw_sections:
            self.sections.append(
                Section(
                    name=self._cstring(shstr_data, raw[0]),
                    sh_type=raw[1],
                    addr=raw[3],
                    offset=raw[4],
                    size=raw[5],
                    link=raw[6],
                    entsize=raw[9],
                )
            )

    @staticmethod
    def _cstring(blob: bytes, offset: int) -> str:
        end = blob.find(b"\0", offset)
        if end < 0:
            end = len(blob)
        return blob[offset:end].decode("utf-8", errors="replace")

    def symbols(self, section_index: int) -> list[tuple[str, int]]:
        section = self.sections[section_index]
        if section.sh_type not in (2, 11):
            return []
        strings = self.sections[section.link]
        str_blob = self.data[strings.offset : strings.offset + strings.size]
        entry_size = section.entsize or 24
        result = []
        for off in range(section.offset, section.offset + section.size, entry_size):
            st_name, _info, _other, _shndx, st_value, _size = struct.unpack_from(
                self.prefix + "IBBHQQ", self.data, off
            )
            result.append((self._cstring(str_blob, st_name), st_value))
        return result

    def rela(self) -> list[tuple[int, int, int, str]]:
        rows = []
        for section in self.sections:
            if section.sh_type != 4:  # SHT_RELA
                continue
            symbols = self.symbols(section.link)
            entry_size = section.entsize or 24
            for off in range(section.offset, section.offset + section.size, entry_size):
                r_offset, r_info, r_addend = struct.unpack_from(self.prefix + "QQq", self.data, off)
                symbol_index = r_info >> 32
                relocation_type = r_info & 0xFFFFFFFF
                symbol_name = symbols[symbol_index][0] if symbol_index < len(symbols) else ""
                rows.append((r_offset, relocation_type, r_addend, symbol_name))
        return rows


def parse_int(text: str) -> int:
    return int(text, 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("elf", type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--range", dest="address_range", metavar="START:END")
    group.add_argument("--at", type=parse_int, metavar="ADDRESS")
    group.add_argument("--target", type=parse_int, metavar="ADDEND", help="find relocations resolving to ADDEND")
    parser.add_argument("--count", type=int, default=1, help="number of 8-byte slots with --at")
    args = parser.parse_args()

    if args.address_range:
        start_text, end_text = args.address_range.split(":", 1)
        start, end = parse_int(start_text), parse_int(end_text)
    elif args.at is not None:
        start, end = args.at, args.at + args.count * 8
    else:
        start = end = None

    elf = Elf64(args.elf)
    if args.target is not None:
        matches = [row for row in elf.rela() if row[2] == args.target]
    else:
        matches = [row for row in elf.rela() if start <= row[0] < end]
    for address, kind, addend, symbol in sorted(matches):
        resolved = addend
        suffix = f" {symbol}" if symbol else ""
        print(f"0x{address:016x}  type={kind:<3d}  addend=0x{resolved & ((1 << 64) - 1):016x}{suffix}")


if __name__ == "__main__":
    main()
