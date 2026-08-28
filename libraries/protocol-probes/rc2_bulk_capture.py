"""Passively capture DJI RC 2 vendor-BULK traffic.

The program never writes to the USB device.  It claims interface 0 and reads
endpoint 0x81 for a bounded interval, then prints compact DUML frame metadata.
"""

from __future__ import annotations

import argparse
import json
import time

import usb1


VID = 0x2CA3
PID = 0x1021
INTERFACE = 0
EP_IN = 0x81


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


def describe(frame: bytes):
    return {
        "length": len(frame),
        "sender": frame[4],
        "receiver": frame[5],
        "sequence": int.from_bytes(frame[6:8], "little"),
        "command_type": frame[8],
        "command_set": frame[9],
        "command_id": frame[10],
        "payload_hex": frame[11:-2].hex(),
        "frame_hex": frame.hex(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=15.0)
    args = parser.parse_args()

    context = usb1.USBContext()
    device = context.getByVendorIDAndProductID(VID, PID)
    if device is None:
        raise SystemExit("DJI RC 2 USB device not found")

    handle = device.open()
    handle.claimInterface(INTERFACE)
    deadline = time.monotonic() + args.seconds
    pending = bytearray()
    frames = 0
    reads = 0
    timeouts = 0
    try:
        while time.monotonic() < deadline:
            try:
                chunk = bytes(handle.bulkRead(EP_IN, 16 * 1024, timeout=500))
            except usb1.USBErrorTimeout:
                timeouts += 1
                continue
            reads += 1
            pending.extend(chunk)
            for frame in extract_frames(pending):
                frames += 1
                print(json.dumps(describe(frame), separators=(",", ":")))
    finally:
        handle.releaseInterface(INTERFACE)
        handle.close()
        context.close()

    print(json.dumps({"summary": {"reads": reads, "frames": frames, "timeouts": timeouts}}))


if __name__ == "__main__":
    main()
