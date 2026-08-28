#!/usr/bin/env python3
"""Bounded input-only census of CRC-valid DJI DUML command headers.

The probe opens only the fixed vendor IN endpoints. It never discovers or opens
an OUT endpoint and contains no request/frame builder or bulk-write call. Raw
frames and payload bytes live only in transient buffers and are never emitted
or persisted. Output is limited to aggregate header counts.
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
import time

import usb1

from rid_working_status_protocol import extract_valid_duml_frames


DJI_VENDOR_ID = 0x2CA3


@dataclass(frozen=True)
class Source:
    name: str
    product_id: int
    interface: int
    endpoint_in: int


SOURCES = (
    Source("aircraft", 0x0020, 4, 0x85),
    Source("rc2", 0x1021, 0, 0x81),
)


def scan(source: Source, seconds: float) -> dict[str, object]:
    context = usb1.USBContext()
    handle = None
    claimed = False
    pending = bytearray()
    headers: Counter[tuple[int, int, int, int, int]] = Counter()
    reads = 0
    byte_count = 0
    valid_frames = 0
    started = time.monotonic()
    result = "completed"
    error = None
    try:
        device = context.getByVendorIDAndProductID(
            DJI_VENDOR_ID, source.product_id
        )
        if device is None:
            result = "device_not_found"
        else:
            handle = device.open()
            handle.claimInterface(source.interface)
            claimed = True
            deadline = started + seconds
            while time.monotonic() < deadline:
                try:
                    chunk = bytes(
                        handle.bulkRead(
                            source.endpoint_in, 64 * 1024, timeout=500
                        )
                    )
                except usb1.USBErrorTimeout:
                    continue
                reads += 1
                byte_count += len(chunk)
                pending.extend(chunk)
                for frame in extract_valid_duml_frames(pending):
                    valid_frames += 1
                    headers[(frame[4], frame[5], frame[8], frame[9], frame[10])] += 1
    except Exception as exc:
        result = "error"
        error = f"{type(exc).__name__}: {exc}"
    finally:
        for index in range(len(pending)):
            pending[index] = 0
        if claimed and handle is not None:
            try:
                handle.releaseInterface(source.interface)
            except Exception:
                pass
        if handle is not None:
            try:
                handle.close()
            except Exception:
                pass
        context.close()

    rows = [
        {
            "sender": f"0x{sender:02x}",
            "receiver": f"0x{receiver:02x}",
            "control": f"0x{control:02x}",
            "cmd_set": f"0x{cmd_set:02x}",
            "cmd_id": f"0x{cmd_id:02x}",
            "count": count,
        }
        for (sender, receiver, control, cmd_set, cmd_id), count in sorted(
            headers.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]
    summary: dict[str, object] = {
        "source": source.name,
        "result": result,
        "duration_seconds": round(time.monotonic() - started, 3),
        "reads": reads,
        "bytes": byte_count,
        "valid_frames": valid_frames,
        "header_rows": rows,
        "privacy": "aggregate headers only; no raw frame or payload retained",
    }
    if error is not None:
        summary["error"] = error
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=20.0)
    args = parser.parse_args()
    if not 0 < args.seconds <= 300:
        parser.error("--seconds must be greater than 0 and at most 300")
    with ThreadPoolExecutor(max_workers=len(SOURCES)) as executor:
        results = list(
            executor.map(lambda source: scan(source, args.seconds), SOURCES)
        )
    print(json.dumps({"sources": results}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
