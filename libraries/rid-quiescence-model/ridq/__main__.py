"""Command-line entry point for JSON-only offline verification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .constants import PREFIX_CLASSES, SCHEMA
from .fixtures import (
    REJECT_DESCRIPTIONS,
    minimal_accept_trace,
    rejected_traces,
    trace_to_json_value,
)
from .model import QuiescenceVerifier, TraceEvent, verify_trace


def _read_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _events(value: Any) -> list[TraceEvent]:
    if type(value) is not dict or set(value) != {"schema", "events"} or value.get("schema") != SCHEMA:
        raise ValueError(f"input must be an object with schema={SCHEMA}")
    raw_events = value.get("events")
    if type(raw_events) is not list:
        raise ValueError("events must be an array")
    return [TraceEvent.from_dict(item) for item in raw_events]


def _prefix_reports(events: list[TraceEvent]) -> list[dict[str, Any]]:
    verifier = QuiescenceVerifier()
    reports: list[dict[str, Any]] = []
    for event in events:
        report = verifier.consume(event)
        if report.classification not in PREFIX_CLASSES:
            raise AssertionError("closed prefix classification violated")
        reports.append(report.to_dict())
    return reports


def _self_check() -> dict[str, Any]:
    accepted = minimal_accept_trace()
    accepted_report = verify_trace(accepted)
    rejects = rejected_traces()
    rejected_reports = [verify_trace(trace) for trace in rejects]
    prefix_count = 0
    for trace in [accepted, *rejects]:
        reports = _prefix_reports(trace)
        prefix_count += len(reports)
        if any(report["classification"] not in PREFIX_CLASSES for report in reports):
            raise AssertionError("unexpected prefix classification")
    if not accepted_report.accepted:
        raise AssertionError("minimal witness trace was not accepted")
    if any(report.accepted for report in rejected_reports):
        raise AssertionError("a required rejection trace was accepted")
    return {
        "schema": SCHEMA,
        "minimal_accept": accepted_report.to_dict(),
        "rejected_trace_count": len(rejected_reports),
        "rejected_descriptions": list(REJECT_DESCRIPTIONS),
        "prefixes_checked": prefix_count,
        "status": "PASS",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify synthetic RID quiescence traces")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", metavar="JSON", help="synthetic trace JSON path, or - for stdin")
    source.add_argument("--fixture", choices=("minimal", *(f"reject-{i:02d}" for i in range(1, 25))))
    source.add_argument("--self-check", action="store_true")
    parser.add_argument("--all-prefixes", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.self_check:
            value = _self_check()
        else:
            if args.input:
                events = _events(_read_json(args.input))
            elif args.fixture == "minimal":
                events = minimal_accept_trace()
            else:
                index = int(args.fixture.rsplit("-", 1)[1]) - 1
                events = rejected_traces()[index]
            value = {
                "schema": SCHEMA,
                "report": verify_trace(events).to_dict(),
            }
            if args.all_prefixes:
                value["prefix_reports"] = _prefix_reports(events)
        json.dump(value, sys.stdout, ensure_ascii=False, sort_keys=True, indent=2)
        sys.stdout.write("\n")
        return 0
    except (OSError, TypeError, ValueError, AssertionError, KeyError) as error:
        json.dump(
            {"schema": SCHEMA, "status": "INPUT_OR_MODEL_ERROR", "message": str(error)},
            sys.stderr,
            ensure_ascii=False,
            sort_keys=True,
        )
        sys.stderr.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
