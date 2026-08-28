#!/usr/bin/env python3
"""Passively observe DJI FlySafe support/version pushes from DJI USB.

Only vendor IN endpoints are read for a bounded interval.  The program does
not send, subscribe, connect, configure, or persist frames.  Output contains
only decoded capability state and aggregate counts; payloads and identities are
never printed.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
import time

from flysafe_runtime_state_protocol import (
    CMD_ID_AREA_INFO,
    CMD_ID_WHITE_LIST_INFO,
    CMD_SET_FLIGHT_CONTROLLER,
    CMD_TYPE_PUSH_PLAINTEXT,
    MINI_5_PRO_PRODUCT,
    FlySafeStateError,
    decode_area_unlock_version,
    decode_whitelist_support,
    select_inventory_receiver,
)
from rid_working_status_protocol import extract_valid_duml_frames


DJI_VENDOR_ID = 0x2CA3


@dataclass(frozen=True)
class SourceSpec:
    name: str
    product_id: int
    interface: int
    endpoint_in: int


SOURCES = {
    "aircraft": SourceSpec("aircraft", 0x0020, 4, 0x85),
    "rc2": SourceSpec("rc2", 0x1021, 0, 0x81),
}


def _scan_source(spec: SourceSpec, *, seconds: float) -> dict[str, object]:
    summary: dict[str, object] = {
        "source": spec.name,
        "result": "completed",
        "duration_requested_seconds": seconds,
        "reads": 0,
        "bytes": 0,
        "timeouts": 0,
        "valid_duml_frames": 0,
        "area_pushes": 0,
        "whitelist_pushes": 0,
        "rejected_command_type": 0,
        "unusable_area_pushes": 0,
        "unusable_whitelist_pushes": 0,
        "area_seen": False,
        "whitelist_seen": False,
        "unlock_version": None,
        "unlock_supported": None,
        "whitelist_encoding": None,
        "runtime_product_assumption": MINI_5_PRO_PRODUCT,
        "inventory_receiver": None,
        "privacy": "raw frames and payloads were not emitted or persisted",
        "transport": "read-only USB IN; no subscribe or request was sent",
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
                summary["valid_duml_frames"] = int(summary["valid_duml_frames"]) + 1
                if frame[9] != CMD_SET_FLIGHT_CONTROLLER:
                    continue
                command_id = frame[10]
                if command_id not in (CMD_ID_AREA_INFO, CMD_ID_WHITE_LIST_INFO):
                    continue
                if frame[8] != CMD_TYPE_PUSH_PLAINTEXT:
                    summary["rejected_command_type"] = int(
                        summary["rejected_command_type"]
                    ) + 1
                    continue
                payload = frame[11:-2]
                if command_id == CMD_ID_AREA_INFO:
                    summary["area_pushes"] = int(summary["area_pushes"]) + 1
                    try:
                        summary["unlock_version"] = decode_area_unlock_version(payload)
                        summary["area_seen"] = True
                    except FlySafeStateError:
                        summary["unusable_area_pushes"] = int(
                            summary["unusable_area_pushes"]
                        ) + 1
                else:
                    summary["whitelist_pushes"] = int(summary["whitelist_pushes"]) + 1
                    try:
                        update = decode_whitelist_support(payload)
                    except FlySafeStateError:
                        summary["unusable_whitelist_pushes"] = int(
                            summary["unusable_whitelist_pushes"]
                        ) + 1
                        continue
                    if update.usable:
                        summary["whitelist_seen"] = True
                        summary["unlock_supported"] = update.supported
                        summary["whitelist_encoding"] = update.encoding
                    else:
                        summary["unusable_whitelist_pushes"] = int(
                            summary["unusable_whitelist_pushes"]
                        ) + 1
    except Exception as exc:
        summary["result"] = "error"
        summary["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        summary["duration_actual_seconds"] = round(time.monotonic() - started, 3)
        if (
            summary["area_seen"]
            and summary["whitelist_seen"]
            and summary["unlock_supported"] is True
        ):
            try:
                summary["inventory_receiver"] = select_inventory_receiver(
                    unlock_version=int(summary["unlock_version"]),
                    product=MINI_5_PRO_PRODUCT,
                )
            except FlySafeStateError:
                summary["inventory_receiver"] = None
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
        description="read-only FlySafe runtime support/version observer"
    )
    parser.add_argument(
        "--source", choices=("aircraft", "rc2", "both"), default="both"
    )
    parser.add_argument("--seconds", type=float, default=30.0)
    args = parser.parse_args()
    if not 0 < args.seconds <= 300:
        parser.error("--seconds must be greater than 0 and at most 300")

    selected = (
        list(SOURCES.values())
        if args.source == "both"
        else [SOURCES[args.source]]
    )
    with ThreadPoolExecutor(max_workers=len(selected)) as executor:
        summaries = [
            future.result()
            for future in [
                executor.submit(_scan_source, spec, seconds=args.seconds)
                for spec in selected
            ]
        ]
    print(
        json.dumps(
            {"sources": sorted(summaries, key=lambda item: str(item["source"]))},
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
