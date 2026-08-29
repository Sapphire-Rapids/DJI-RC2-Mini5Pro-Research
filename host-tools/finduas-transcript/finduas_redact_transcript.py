#!/usr/bin/env python3
"""Create a privacy-reduced FindUAS telemetry summary.

The input is FindUASMac's local ``telemetry.jsonl`` file. That file can contain
full UAS IDs, receiver identifiers, and precise coordinates. This tool never
prints or writes those values. It emits only counts, local timestamps, a
receiver-reported Remote ID standard, and optional field-presence Booleans.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ALLOWED_OUTPUT_PREFIXES = {
    "uasID": "uas_id_digest_",
    "ridStandard": "rid_standard",
    "latitude": "location_present",
    "longitude": "location_present",
    "operatorLatitude": "operator_location_present",
    "operatorLongitude": "operator_location_present",
    "firstSeen": "first_seen",
    "lastSeen": "last_seen",
    "registrationID": "registration_id_present",
    "uavIDType": "uas_id_type_present",
    "manufacturer": "manufacturer_present",
    "model": "model_present",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize FindUAS telemetry without identifiers or coordinates"
    )
    parser.add_argument("input", type=Path, help="local telemetry.jsonl file")
    parser.add_argument(
        "--digest-prefix",
        action="store_true",
        help="include a 12-hex-character SHA-256 prefix for each distinct UAS ID",
    )
    parser.add_argument(
        "--stdout-only",
        action="store_true",
        help="do not create an output file; print the redacted summary only",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="redacted Markdown output path (default: <input>.redacted.md)",
    )
    return parser.parse_args()


def sha256_prefix(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid JSON on line {line_number}: {error.msg}"
                ) from error
            if not isinstance(value, dict):
                raise ValueError(f"line {line_number} is not a JSON object")
            if not isinstance(value.get("uasID"), str) or not value["uasID"]:
                raise ValueError(f"line {line_number} has no non-empty uasID")
            records.append(value)
    return records


def field_present(record: dict[str, Any], keys: tuple[str, ...]) -> bool:
    return any(record.get(key) is not None for key in keys)


def summarize(records: list[dict[str, Any]], digest_prefix: bool) -> str:
    by_uas_id: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_uas_id.setdefault(record["uasID"], []).append(record)

    lines = [
        "# FindUAS redacted telemetry summary",
        "",
        "This summary contains no full identifiers, receiver identifiers, coordinates, raw frames, or credentials.",
        "",
        f"Input records: {len(records)}",
        f"Distinct targets: {len(by_uas_id)}",
        "",
    ]

    for index, (uas_id, target_records) in enumerate(
        sorted(by_uas_id.items()), start=1
    ):
        first_seen = min(str(r.get("firstSeen", "")) for r in target_records)
        last_seen = max(str(r.get("lastSeen", "")) for r in target_records)
        rid_standards = sorted(
            {
                str(record["ridStandard"])
                for record in target_records
                if record.get("ridStandard") is not None
            }
        )
        lines.extend(
            [
                f"## Target {index}",
                "",
                f"- Receiver-reported RID standard: {', '.join(rid_standards) or 'UNKNOWN'}",
                f"- Record count: {len(target_records)}",
                f"- First seen: {first_seen or 'UNKNOWN'}",
                f"- Last seen: {last_seen or 'UNKNOWN'}",
                f"- UAS ID present: yes",
                f"- Registration ID present: {str(field_present(target_records[0], ('registrationID',))).lower()}",
                f"- Location fields present: {str(field_present(target_records[0], ('latitude', 'longitude'))).lower()}",
                f"- Operator-location fields present: {str(field_present(target_records[0], ('operatorLatitude', 'operatorLongitude'))).lower()}",
                f"- Manufacturer/model present: {str(field_present(target_records[0], ('manufacturer', 'model'))).lower()}",
                f"- UAS ID type present: {str(target_records[0].get('uavIDType') is not None).lower()}",
            ]
        )
        if digest_prefix:
            lines.append(f"- UAS ID digest prefix: {sha256_prefix(uas_id)}")
        lines.append("")

    lines.extend(
        [
            "## Boundaries",
            "",
            "- FindUASMac's BLE connection to its receiver does not establish the aircraft's exact BLE/Wi-Fi air bearer.",
            "- This summary is not RF A-B-A evidence by itself and must be correlated with the operator's motor-transition timestamps.",
            "- Absence from this file is not proof that the aircraft did not broadcast.",
            "",
        ]
    )
    return "\n".join(lines)


def assert_no_sensitive_values(output: str, records: list[dict[str, Any]]) -> None:
    sensitive_keys = (
        "uasID",
        "registrationID",
        "monitorID",
        "latitude",
        "longitude",
        "operatorLatitude",
        "operatorLongitude",
        "operatorRegistrationPhone",
        "manufacturer",
        "model",
    )
    for record in records:
        for key in sensitive_keys:
            value = record.get(key)
            if isinstance(value, str) and value and value in output:
                raise ValueError(f"redacted summary leaked value from {key}")
            if isinstance(value, (int, float)) and str(value) in output:
                raise ValueError(f"redacted summary leaked value from {key}")


def main() -> int:
    args = parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(f"input file not found: {args.input}")

    records = load_records(args.input)
    output = summarize(records, args.digest_prefix)
    assert_no_sensitive_values(output, records)

    if args.stdout_only:
        print(output, end="")
    else:
        output_path = args.output or args.input.with_suffix(".redacted.md")
        output_path.write_text(output, encoding="utf-8")
        print(f"redacted summary: {output_path}", file=sys.stderr)
        print("No full identifier, coordinate, receiver ID, raw frame, or credential was written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
