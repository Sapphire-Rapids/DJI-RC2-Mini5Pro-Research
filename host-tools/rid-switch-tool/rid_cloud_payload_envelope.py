"""Offline structure analysis for the observed 20-byte cloud-policy envelope.

Recognition uses only the fixed magic, LE16 length at offset18, and a64-byte
opaque trailer. Other header values have no assigned meaning. The optional
13-byte body layout is a width/alignment candidate, not a named RID schema.
Inputs stay local; no packet generation, device access or trailer values exist
in the output.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re


MAGIC_LE32 = 0x83677667
HEADER_BYTES = 20
TRAILER_BYTES = 64
MAX_BYTES = 65536
MAX_CAPTURE_BYTES = 300000
HEADER_LAYOUT = ((0, 4), (4, 2), (6, 2), (8, 4), (12, 4), (16, 2), (18, 2))
BODY_CANDIDATE_LAYOUT = ((0, 1), (1, 2), (3, 2), (5, 4), (9, 4))


class Invalid(ValueError):
    """Fixed error codes only: never include data or a local input path."""


def strict_hex(value: str) -> bytes:
    if type(value) is not str:
        raise Invalid("HEX_NOT_STRING")
    if len(value) > MAX_BYTES * 2:
        raise Invalid("LIMIT_EXCEEDED")
    if len(value) % 2:
        raise Invalid("ODD_HEX_LENGTH")
    if re.fullmatch(r"[0-9a-fA-F]*", value) is None:
        raise Invalid("NON_CANONICAL_HEX")
    return bytes.fromhex(value)


def _validate(data: bytes) -> int:
    if type(data) is not bytes:
        raise Invalid("BYTES_REQUIRED")
    if len(data) > MAX_BYTES:
        raise Invalid("LIMIT_EXCEEDED")
    if len(data) < HEADER_BYTES + TRAILER_BYTES:
        raise Invalid("TRUNCATED_ENVELOPE")
    if int.from_bytes(data[:4], "little") != MAGIC_LE32:
        raise Invalid("MAGIC_MISMATCH")
    body_bytes = int.from_bytes(data[18:20], "little")
    if len(data) != HEADER_BYTES + body_bytes + TRAILER_BYTES:
        raise Invalid("LENGTH_MISMATCH")
    return body_bytes


def _fields(data: bytes, layout: tuple[tuple[int, int], ...], base: int = 0) -> list[dict]:
    return [{"offset": base + offset, "width_bytes": width, "byte_order": "little",
             "unsigned_value": int.from_bytes(data[offset:offset + width], "little")}
            for offset, width in layout]


def analyze_bytes(data: bytes) -> dict:
    """Return lengths and unnamed scalars; never return body/trailer byte strings."""
    body_bytes = _validate(data)
    body = data[HEADER_BYTES:HEADER_BYTES + body_bytes]
    candidate = None
    if body_bytes == 13:
        candidate = {
            "evidence": "HYPOTHESIS",
            "basis": "UNNAMED_WIDTH_ALIGNMENT_ONLY",
            "body_relative_offsets": [offset for offset, _ in BODY_CANDIDATE_LAYOUT],
            "fields": _fields(body, BODY_CANDIDATE_LAYOUT, HEADER_BYTES),
        }
    return {
        "schema": "finduas-cloud-policy-envelope/v1",
        "envelope_structure_valid": True,
        "total_bytes": len(data),
        "magic_le32": MAGIC_LE32,
        "header": {"offset": 0, "bytes": HEADER_BYTES,
                   "unnamed_fields": _fields(data[:HEADER_BYTES], HEADER_LAYOUT)},
        "body": {"offset": HEADER_BYTES, "bytes": body_bytes,
                 "length_field_offset": 18, "length_field_width_bytes": 2,
                 "layout_candidate": candidate},
        "trailer": {"offset": HEADER_BYTES + body_bytes, "bytes": TRAILER_BYTES,
                    "interpretation": "OPAQUE"},
        "named_rid_switch_field": None,
    }


def _changed(left: bytes, right: bytes, base: int = 0) -> list[int]:
    overlap = min(len(left), len(right))
    return [base + offset for offset in range(max(len(left), len(right)))
            if offset >= overlap or left[offset] != right[offset]]


def compare_bytes(matched: bytes, default: bytes) -> dict:
    """Compare fixed regions, locating each trailer using its own body length."""
    left, right = analyze_bytes(matched), analyze_bytes(default)
    left_body = matched[HEADER_BYTES:-TRAILER_BYTES]
    right_body = default[HEADER_BYTES:-TRAILER_BYTES]
    header_fields = []
    for offset, width in HEADER_LAYOUT:
        a = int.from_bytes(matched[offset:offset + width], "little")
        b = int.from_bytes(default[offset:offset + width], "little")
        if a != b:
            header_fields.append({"offset": offset, "width_bytes": width,
                                  "matched_unsigned": a, "default_unsigned": b})
    body_fields = None
    if len(left_body) == len(right_body) == 13:
        body_fields = []
        for offset, width in BODY_CANDIDATE_LAYOUT:
            a = int.from_bytes(left_body[offset:offset + width], "little")
            b = int.from_bytes(right_body[offset:offset + width], "little")
            if a != b:
                body_fields.append({"offset": HEADER_BYTES + offset,
                                    "body_relative_offset": offset, "width_bytes": width,
                                    "matched_unsigned": a, "default_unsigned": b})
    return {
        "schema": "finduas-cloud-policy-envelope-pair/v1",
        "matched": left, "default": right,
        "comparison": {
            "identical": matched == default,
            "header_changed_offsets": _changed(matched[:HEADER_BYTES], default[:HEADER_BYTES]),
            "header_changed_unnamed_fields": header_fields,
            "body_changed_offsets": _changed(left_body, right_body, HEADER_BYTES),
            "body_changed_candidate_fields": body_fields,
            "trailer_equal": matched[-TRAILER_BYTES:] == default[-TRAILER_BYTES:],
            "trailer_changed_byte_count": len(_changed(matched[-TRAILER_BYTES:], default[-TRAILER_BYTES:])),
        },
        "named_rid_switch_field": None,
    }


def analyze_capture(capture: dict) -> dict:
    if type(capture) is not dict:
        raise Invalid("CAPTURE_NOT_OBJECT")
    if "matched_hex" not in capture:
        raise Invalid("MATCHED_MISSING")
    matched = strict_hex(capture["matched_hex"])
    present = capture.get("default_present")
    if present is not None and type(present) is not bool:
        raise Invalid("INVALID_DEFAULT_STATE")
    default_hex = capture.get("default_hex")
    if default_hex is not None and present is False:
        raise Invalid("CONFLICTING_DEFAULT_STATE")
    rows = capture.get("matching_row_count")
    if rows is not None and (type(rows) is not int or rows < 1 or rows > 256):
        raise Invalid("INVALID_MATCHING_ROW_COUNT")
    if default_hex is not None:
        default = strict_hex(default_hex)
        result = compare_bytes(matched, default) if default else {"matched": analyze_bytes(matched)}
        default_state = "NONEMPTY" if default else "EMPTY"
    else:
        result = {"matched": analyze_bytes(matched)}
        default_state = "MISSING" if present is False else "UNCAPTURED" if present else "UNOBSERVED"
    nonempty = capture.get("default_nonempty")
    if nonempty is not None:
        if type(nonempty) is not bool:
            raise Invalid("INVALID_DEFAULT_NONEMPTY")
        if default_state in ("MISSING", "EMPTY") and nonempty or default_state == "NONEMPTY" and not nonempty:
            raise Invalid("CONFLICTING_DEFAULT_NONEMPTY")
    result.update(schema="finduas-cloud-policy-envelope-capture/v1", default_state=default_state,
                  matching_row_count=rows, named_rid_switch_field=None)
    return result


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid("DUPLICATE_CAPTURE_KEY")
        result[key] = value
    return result


def _reject_constant(_):
    raise Invalid("INVALID_JSON_CONSTANT")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", type=Path, help="private matched/DEFAULT capture JSON")
    parser.add_argument("--output", type=Path, required=True, help="new private analysis JSON")
    args = parser.parse_args(argv)
    try:
        with args.input.open("rb") as stream:
            raw = stream.read(MAX_CAPTURE_BYTES + 1)
        if len(raw) > MAX_CAPTURE_BYTES:
            raise Invalid("CAPTURE_LIMIT")
        capture = json.loads(raw, object_pairs_hook=_strict_object, parse_constant=_reject_constant)
        result = analyze_capture(capture)
        # Exclusive creation preserves the capture and all earlier analysis files.
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
    except (Invalid, ValueError, KeyError, TypeError, OSError, RecursionError):
        print("envelope analysis failed: invalid input or unavailable output")
        return 2
    print("private envelope analysis saved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
