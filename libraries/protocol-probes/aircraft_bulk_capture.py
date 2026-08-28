"""Passively summarize the candidate DJI aircraft DUML USB interface.

The tool never writes to the device.  It claims interface 4, reads endpoint
0x85 for a bounded interval, and emits only DUML routing metadata.  Payloads,
coordinates, identifiers, and raw frames are deliberately omitted.
"""

from __future__ import annotations

import argparse
import collections
import json
import time

import usb1


VID = 0x2CA3
PID = 0x0020
INTERFACE = 4
EP_IN = 0x85


def extract_frames(buffer: bytearray):
    while True:
        try:
            start = buffer.index(0x55)
        except ValueError:
            buffer.clear()
            return
        if start:
            del buffer[:start]
        if len(buffer) < 3:
            return
        length = (buffer[1] | (buffer[2] << 8)) & 0x03FF
        if length < 13 or length > 1023:
            del buffer[0]
            continue
        if len(buffer) < length:
            return
        frame = bytes(buffer[:length])
        del buffer[:length]
        yield frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=10.0)
    args = parser.parse_args()

    context = usb1.USBContext()
    device = context.getByVendorIDAndProductID(VID, PID)
    if device is None:
        raise SystemExit("DJI aircraft USB device not found")

    handle = device.open()
    handle.claimInterface(INTERFACE)
    pending = bytearray()
    counts = collections.Counter()
    reads = 0
    byte_count = 0
    timeouts = 0
    deadline = time.monotonic() + args.seconds
    try:
        while time.monotonic() < deadline:
            try:
                chunk = bytes(handle.bulkRead(EP_IN, 64 * 1024, timeout=500))
            except usb1.USBErrorTimeout:
                timeouts += 1
                continue
            reads += 1
            byte_count += len(chunk)
            pending.extend(chunk)
            for frame in extract_frames(pending):
                counts[(frame[4], frame[5], frame[8], frame[9], frame[10], len(frame))] += 1
    finally:
        handle.releaseInterface(INTERFACE)
        handle.close()
        context.close()

    print(
        json.dumps(
            {
                "interface": INTERFACE,
                "endpoint": EP_IN,
                "reads": reads,
                "bytes": byte_count,
                "timeouts": timeouts,
                "routes": [
                    {
                        "sender": key[0],
                        "receiver": key[1],
                        "command_type": key[2],
                        "command_set": key[3],
                        "command_id": key[4],
                        "frame_length": key[5],
                        "count": value,
                    }
                    for key, value in sorted(counts.items())
                ],
                "privacy": "payloads and raw frames were not retained",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
