#!/usr/bin/env python3
"""Create a reproducible source-only Python zip application."""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ridq.constants import (  # noqa: E402
    DETAIL_FIELD_TYPES,
    EVENT_TYPES,
    EVENT_INTEGER_FIELDS,
    EVENT_STRING_FIELDS,
    FAILURE_CODES,
    FIXED_PROFILE,
    FIXED_TRANSPORT_RETRY,
    INVARIANTS,
    MODEL_VERSION,
    PREFIX_CLASSES,
    SCHEMA,
    STATES,
    TRANSITIONS,
)


SOURCE_PATHS = tuple(
    ROOT / relative
    for relative in (
        "ridq/__init__.py",
        "ridq/__main__.py",
        "ridq/constants.py",
        "ridq/fixtures.py",
        "ridq/model.py",
    )
)
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
TOP_MAIN = b"from ridq.__main__ import main\nraise SystemExit(main())\n"


def source_digest() -> str:
    digest = hashlib.sha256()
    for path in SOURCE_PATHS:
        relative = path.relative_to(ROOT).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def manifest() -> dict:
    return {
        "artifact_schema": "finduas-ridq-model-artifact/v1",
        "model_version": MODEL_VERSION,
        "trace_schema": SCHEMA,
        "fixed_profile": FIXED_PROFILE,
        "fixed_transport_retry": FIXED_TRANSPORT_RETRY,
        "states": list(STATES),
        "transitions": [list(item) for item in TRANSITIONS],
        "prefix_classes": list(PREFIX_CLASSES),
        "invariants": list(INVARIANTS),
        "failure_codes": [[name, number] for name, number in FAILURE_CODES],
        "event_types": list(EVENT_TYPES),
        "event_integer_fields": list(EVENT_INTEGER_FIELDS),
        "event_string_fields": list(EVENT_STRING_FIELDS),
        "detail_field_types": [list(item) for item in DETAIL_FIELD_TYPES],
        "source_set_sha256": source_digest(),
    }


def _write_entry(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, ZIP_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def build(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    entries: dict[str, bytes] = {"__main__.py": TOP_MAIN}
    for path in SOURCE_PATHS:
        entries[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    entries["model_manifest.json"] = (
        json.dumps(manifest(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    with zipfile.ZipFile(target, "w", allowZip64=False) as archive:
        for name in sorted(entries):
            _write_entry(archive, name, entries[name])


def main(argv: list[str]) -> int:
    target = Path(argv[1]).resolve() if len(argv) > 1 else ROOT / "dist/rid-quiescence-verifier.pyz"
    build(target)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
