"""Issue a fixed, read-only set of DJI flight-controller parameter queries.

Safety boundary: this tool only permits DUML FLYC commands 0xF7 (parameter
metadata by hash) and 0xF8 (parameter value by hash), for the three parameter
names and hashes hard-coded below.  It cannot send parameter-write/reset
commands.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import json
import pathlib
import time

import usb1


VID = 0x2CA3
PID = 0x1021
INTERFACE = 0
EP_OUT = 0x01
EP_IN = 0x81

# RC 2 currently routes FC pushes to PC instance 5 (0xAA).  Using the same
# observed return address is required for FC replies on this USB bridge.
SOURCE_APP = 0xAA
TARGET_FC = 0x03
CMD_TYPE_REQUEST_ACK = 0x40
CMD_SET_FLYC = 0x03
CMD_GET_PARAM_INFO_BY_HASH = 0xF7
CMD_GET_PARAM_VALUE_BY_HASH = 0xF8

PARAMETERS = {
    "g_config.flying_limit.max_height_0": 0x0371238A,
    "g_config.flying_limit.max_radius_0": 0x425C0A94,
    "g_config.advanced_function.radius_limit_enabled_0": 0x7ECE6D19,
}


def load_duml_module():
    path = pathlib.Path(__file__).parent / "third-party" / "duml.py"
    spec = importlib.util.spec_from_file_location("readonly_duml", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load DUML implementation from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module.__name__] = module
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
    parser.add_argument("--reply-seconds", type=float, default=1.5)
    args = parser.parse_args()

    duml = load_duml_module()
    context = usb1.USBContext()
    device = context.getByVendorIDAndProductID(VID, PID)
    if device is None:
        raise SystemExit("DJI RC 2 USB device not found")

    handle = device.open()
    handle.claimInterface(INTERFACE)
    pending = bytearray()
    sequence = int(time.monotonic() * 1000) & 0xFFFF
    results = []
    try:
        for parameter_name, parameter_hash in PARAMETERS.items():
            for command_id, query_kind in (
                (CMD_GET_PARAM_INFO_BY_HASH, "metadata"),
                (CMD_GET_PARAM_VALUE_BY_HASH, "value"),
            ):
                if command_id not in {CMD_GET_PARAM_INFO_BY_HASH, CMD_GET_PARAM_VALUE_BY_HASH}:
                    raise AssertionError("refusing non-read-only DUML command")
                sequence = (sequence + 1) & 0xFFFF
                payload = parameter_hash.to_bytes(4, "little")
                packet = duml.build_packet(
                    SOURCE_APP,
                    TARGET_FC,
                    CMD_TYPE_REQUEST_ACK,
                    CMD_SET_FLYC,
                    command_id,
                    payload,
                    sequence,
                )
                written = handle.bulkWrite(EP_OUT, packet, timeout=1000)
                query = {
                    "parameter": parameter_name,
                    "hash": f"0x{parameter_hash:08X}",
                    "kind": query_kind,
                    "command_id": f"0x{command_id:02X}",
                    "sequence": sequence,
                    "bytes_written": written,
                    "request_hex": packet.hex(),
                    "matching_replies": [],
                }

                deadline = time.monotonic() + args.reply_seconds
                while time.monotonic() < deadline:
                    try:
                        chunk = bytes(handle.bulkRead(EP_IN, 16 * 1024, timeout=250))
                    except usb1.USBErrorTimeout:
                        continue
                    pending.extend(chunk)
                    for frame in extract_frames(pending):
                        item = describe(frame)
                        if (
                            item["sequence"] == sequence
                            and item["command_set"] == CMD_SET_FLYC
                            and item["command_id"] == command_id
                        ):
                            query["matching_replies"].append(item)
                results.append(query)
                time.sleep(0.1)
    finally:
        handle.releaseInterface(INTERFACE)
        handle.close()
        context.close()

    print(json.dumps({"queries": results}, indent=2))


if __name__ == "__main__":
    main()
