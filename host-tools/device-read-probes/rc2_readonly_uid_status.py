"""Read only the flight controller's account-sync status via DJI RC 2.

Safety boundary: the only transmitted payloads are Detection/GetIsSetUUID
(subcommand 0x09) and Detection/GetUAVAppFlag (subcommand 0x0C).  Responses
are reduced to booleans; this tool never requests, prints, or stores a UUID.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import time

import usb1


VID = 0x2CA3
PID = 0x1021
INTERFACE = 0
EP_OUT = 0x01
EP_IN = 0x81

# The RC 2 USB bridge currently forwards flight-controller pushes to PC
# instance 5: DeviceType.PC (0x0A) | (5 << 5) = 0xAA.  Use that observed
# return address for a USB-originated request.  Direct PC instance 0 (0x0A)
# and the on-controller APP address (0x02) received no Detection reply.
SOURCE_APP = 0xAA
TARGET_FC = 0x03
CMD_TYPE_REQUEST_ACK = 0x40
CMD_SET_FLYC = 0x03
CMD_DETECTION = 0xDA
SUBCMD_GET_IS_SET_UUID = 0x09
SUBCMD_GET_UAV_APP_FLAG = 0x0C

QUERIES = (
    ("has_uuid", SUBCMD_GET_IS_SET_UUID),
    ("uav_app_flag", SUBCMD_GET_UAV_APP_FLAG),
)


def load_duml_module():
    path = pathlib.Path(__file__).parent / "third-party" / "duml.py"
    spec = importlib.util.spec_from_file_location("readonly_duml", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load DUML implementation from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    duml = load_duml_module()
    sequence = int(time.monotonic() * 1000) & 0xFFFF

    context = usb1.USBContext()
    device = context.getByVendorIDAndProductID(VID, PID)
    if device is None:
        raise SystemExit("DJI RC 2 USB device not found")

    handle = device.open()
    handle.claimInterface(INTERFACE)
    pending = bytearray()
    results = []
    try:
        for label, subcommand in QUERIES:
            sequence = (sequence + 1) & 0xFFFF
            request = duml.build_packet(
                SOURCE_APP,
                TARGET_FC,
                CMD_TYPE_REQUEST_ACK,
                CMD_SET_FLYC,
                CMD_DETECTION,
                bytes([subcommand]),
                sequence,
            )
            written = handle.bulkWrite(EP_OUT, request, timeout=1000)
            matching = []
            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline:
                try:
                    pending.extend(handle.bulkRead(EP_IN, 16 * 1024, timeout=250))
                except usb1.USBErrorTimeout:
                    continue
                for frame in extract_frames(pending):
                    if (
                        len(frame) >= 16
                        and frame[4] == TARGET_FC
                        and frame[5] == SOURCE_APP
                        and int.from_bytes(frame[6:8], "little") == sequence
                        and frame[9] == CMD_SET_FLYC
                        and frame[10] == CMD_DETECTION
                    ):
                        payload = frame[11:-2]
                        matching.append(
                            {
                                "payload_length": len(payload),
                                "subcommand": payload[0] if len(payload) >= 1 else None,
                                "result_code": payload[1] if len(payload) >= 2 else None,
                                label: payload[2] == 1 if len(payload) >= 3 else None,
                            }
                        )
            results.append(
                {
                    "query": label,
                    "bytes_written": written,
                    "matching_replies": matching,
                }
            )
    finally:
        handle.releaseInterface(INTERFACE)
        handle.close()
        context.close()

    print(
        json.dumps(
            {
                "queries": results,
                "privacy": "UUID values were not requested or retained",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
