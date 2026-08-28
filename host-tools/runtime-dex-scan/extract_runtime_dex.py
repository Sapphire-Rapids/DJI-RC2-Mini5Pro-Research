#!/usr/bin/env python3
"""Extract structurally valid DEX images from an authorized raw memory dump."""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path


DEX_MAGIC_PREFIX = b"dex\n0"
DEX_HEADER_SIZE = 0x70
ENDIAN_CONSTANT = 0x12345678


def find_dex_images(memory: bytes) -> list[tuple[int, bytes]]:
    """Return non-overlapping, header-bounded DEX images in offset order."""
    images: list[tuple[int, bytes]] = []
    cursor = 0
    while True:
        offset = memory.find(DEX_MAGIC_PREFIX, cursor)
        if offset < 0:
            return images
        cursor = offset + 1
        if offset + DEX_HEADER_SIZE > len(memory):
            continue

        file_size = struct.unpack_from("<I", memory, offset + 0x20)[0]
        header_size = struct.unpack_from("<I", memory, offset + 0x24)[0]
        endian = struct.unpack_from("<I", memory, offset + 0x28)[0]
        if (
            header_size != DEX_HEADER_SIZE
            or endian != ENDIAN_CONSTANT
            or file_size < DEX_HEADER_SIZE
            or offset + file_size > len(memory)
        ):
            continue

        images.append((offset, memory[offset : offset + file_size]))
        cursor = offset + file_size


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan an authorized raw memory dump for bounded DEX images."
    )
    parser.add_argument("memory", type=Path, help="input raw-memory file")
    parser.add_argument("output", type=Path, help="empty or new output directory")
    args = parser.parse_args()

    memory = args.memory.read_bytes()
    args.output.mkdir(parents=True, exist_ok=True)

    images = find_dex_images(memory)
    for index, (offset, dex) in enumerate(images, start=1):
        destination = args.output / f"classes{index:02d}.dex"
        destination.write_bytes(dex)
        print(
            f"{destination.name}\toffset=0x{offset:x}\tbytes={len(dex)}"
            f"\tsha256={hashlib.sha256(dex).hexdigest()}"
        )

    print(f"extracted={len(images)}")
    return 0 if images else 1


if __name__ == "__main__":
    raise SystemExit(main())
