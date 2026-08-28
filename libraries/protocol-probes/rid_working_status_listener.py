#!/usr/bin/env python3
"""Passively listen for validated DJI RID working-status pushes over USB.

Only vendor IN endpoints are read.  The listener neither builds nor transmits
DUML commands, and its JSON Lines output never contains a raw frame or payload.
Raw bytes exist only in the transient parser buffer and are never persisted.
Identical status repeats are suppressed; the first accepted status and later
changes are emitted.
"""

from __future__ import annotations

import argparse
import collections
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import threading
import time
from typing import Callable

from rid_working_status_protocol import (
    CMD_ID_RID_WORKING_STATUS,
    CMD_SET_ADSB,
    RidProtocolError,
    RidWorkingStatus,
    deidentified_summary,
    extract_valid_duml_frames,
    parse_rid_working_status_frame,
)


DJI_VENDOR_ID = 0x2CA3


@dataclass(frozen=True)
class SourceSpec:
    name: str
    product_id: int
    interface: int
    endpoint_in: int


SOURCES = {
    "aircraft": SourceSpec(
        name="aircraft", product_id=0x0020, interface=4, endpoint_in=0x85
    ),
    "rc2": SourceSpec(
        name="rc2", product_id=0x1021, interface=0, endpoint_in=0x81
    ),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deduplication_key(status: RidWorkingStatus) -> tuple[object, ...]:
    return (
        status.sender,
        status.receiver,
        status.flags_word,
        status.area_code_value,
        status.failure_code,
    )


def _scan_source(
    spec: SourceSpec,
    *,
    seconds: float,
    emit: Callable[[dict[str, object]], None],
) -> dict[str, object]:
    summary: dict[str, object] = {
        "source": spec.name,
        "vendor_id": DJI_VENDOR_ID,
        "product_id": spec.product_id,
        "interface": spec.interface,
        "endpoint_in": spec.endpoint_in,
        "duration_requested_seconds": seconds,
        "reads": 0,
        "bytes": 0,
        "timeouts": 0,
        "valid_duml_frames": 0,
        "rid_route_candidates": 0,
        "rid_status_events_emitted": 0,
        "identical_status_repeats_suppressed": 0,
        "rejected_rid_candidates": {},
        "privacy": "raw frames and payloads were not emitted or persisted",
    }

    try:
        import usb1
    except ImportError as exc:
        summary["result"] = "dependency_missing"
        summary["error"] = f"python usb1 module unavailable: {exc}"
        return summary

    context = usb1.USBContext()
    handle = None
    claimed = False
    rejection_counts: collections.Counter[str] = collections.Counter()
    last_status_key: tuple[object, ...] | None = None
    pending = bytearray()
    started = time.monotonic()

    try:
        device = context.getByVendorIDAndProductID(
            DJI_VENDOR_ID, spec.product_id
        )
        if device is None:
            summary["result"] = "device_not_found"
            return summary

        handle = device.open()
        handle.claimInterface(spec.interface)
        claimed = True
        deadline = started + seconds

        while time.monotonic() < deadline:
            try:
                chunk = bytes(
                    handle.bulkRead(spec.endpoint_in, 64 * 1024, timeout=500)
                )
            except usb1.USBErrorTimeout:
                summary["timeouts"] = int(summary["timeouts"]) + 1
                continue

            summary["reads"] = int(summary["reads"]) + 1
            summary["bytes"] = int(summary["bytes"]) + len(chunk)
            pending.extend(chunk)

            for frame in extract_valid_duml_frames(pending):
                summary["valid_duml_frames"] = (
                    int(summary["valid_duml_frames"]) + 1
                )
                if frame[9] != CMD_SET_ADSB or frame[10] != CMD_ID_RID_WORKING_STATUS:
                    continue

                summary["rid_route_candidates"] = (
                    int(summary["rid_route_candidates"]) + 1
                )
                try:
                    status = parse_rid_working_status_frame(frame)
                except RidProtocolError as exc:
                    rejection_counts[str(exc)] += 1
                    continue

                status_key = _deduplication_key(status)
                if status_key == last_status_key:
                    summary["identical_status_repeats_suppressed"] = (
                        int(summary["identical_status_repeats_suppressed"]) + 1
                    )
                    continue
                last_status_key = status_key

                event = {
                    "event": "rid_working_status",
                    "timestamp_utc": _utc_now(),
                    "source": spec.name,
                    **deidentified_summary(status),
                }
                emit(event)
                summary["rid_status_events_emitted"] = (
                    int(summary["rid_status_events_emitted"]) + 1
                )

        summary["result"] = "completed"
    except Exception as exc:  # USB backend errors differ by platform/version.
        summary["result"] = "error"
        summary["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        summary["duration_actual_seconds"] = round(
            time.monotonic() - started, 3
        )
        summary["rejected_rid_candidates"] = dict(
            sorted(rejection_counts.items())
        )
        if claimed and handle is not None:
            try:
                handle.releaseInterface(spec.interface)
            except Exception:
                pass
        if handle is not None:
            try:
                handle.close()
            except Exception:
                pass
        context.close()

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only listener for strictly validated DJI ADS-B/RID "
            "0x11/0x1C status pushes"
        )
    )
    parser.add_argument(
        "--source",
        choices=("aircraft", "rc2", "both"),
        default="both",
        help="USB source to observe (default: both concurrently)",
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=20.0,
        help="bounded observation time per source (default: 20)",
    )
    args = parser.parse_args()
    if not 0 < args.seconds <= 3600:
        parser.error("--seconds must be greater than 0 and at most 3600")

    selected = (
        list(SOURCES.values())
        if args.source == "both"
        else [SOURCES[args.source]]
    )
    output_lock = threading.Lock()

    def emit(value: dict[str, object]) -> None:
        with output_lock:
            print(json.dumps(value, separators=(",", ":"), sort_keys=True), flush=True)

    with ThreadPoolExecutor(max_workers=len(selected)) as executor:
        futures = [
            executor.submit(_scan_source, spec, seconds=args.seconds, emit=emit)
            for spec in selected
        ]
        summaries = [future.result() for future in futures]

    emit(
        {
            "event": "summary",
            "timestamp_utc": _utc_now(),
            "sources": sorted(summaries, key=lambda item: str(item["source"])),
        }
    )


if __name__ == "__main__":
    main()
