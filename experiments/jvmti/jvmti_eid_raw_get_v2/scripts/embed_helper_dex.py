#!/usr/bin/env python3
"""Convert one audited helper DEX into a deterministic C include."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def render(data: bytes) -> str:
    rows: list[str] = []
    for offset in range(0, len(data), 12):
        chunk = data[offset : offset + 12]
        rows.append("    " + ", ".join(f"0x{value:02x}" for value in chunk) + ",")
    digest = hashlib.sha256(data).hexdigest()
    return "\n".join(
        [
            "#ifndef FINDUAS_EID_RAW_GET_V2_HELPER_DEX_INC",
            "#define FINDUAS_EID_RAW_GET_V2_HELPER_DEX_INC",
            "",
            "static const unsigned char kFinduasRawCallbackDex[] = {",
            *rows,
            "};",
            "static const unsigned int kFinduasRawCallbackDexLength =",
            "    (unsigned int)sizeof(kFinduasRawCallbackDex);",
            f'static const char kFinduasRawCallbackDexSha256[] = "{digest}";',
            "",
            "#endif",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dex", type=Path)
    parser.add_argument("output_include", type=Path)
    arguments = parser.parse_args()

    data = arguments.input_dex.read_bytes()
    if not data.startswith(b"dex\n"):
        raise SystemExit("input is not a DEX file")
    arguments.output_include.parent.mkdir(parents=True, exist_ok=True)
    arguments.output_include.write_text(render(data), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
