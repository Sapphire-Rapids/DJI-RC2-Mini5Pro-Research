"""Read only the aircraft flight-controller area code.

The only outbound command is FLYC 0x03/0xAF with the documented
DataFlycGetSetProductConfig GET_AREA_CODE payload: subcommand 4 followed by
eight zero bytes.  It never sends SET_AREA_CODE (subcommand 3) and prints no
raw frames or device identifiers.
"""

from __future__ import annotations

import importlib.util
import sys
import pathlib
import time

import usb1


VID = 0x2CA3
PID = 0x0020
INTERFACE = 4
EP_OUT = 0x04
EP_IN = 0x85
SOURCE = 0x0A
TARGET = 0x03
CMD_TYPE_REQUEST_ACK = 0x40
CMD_SET_FLYC = 0x03
CMD_GET_SET_PRODUCT_CONFIG = 0xAF
GET_AREA_CODE = 4

ISO_NUMERIC_TO_ALPHA2 = {
    36: "AU",
    156: "CN",
    250: "FR",
    392: "JP",
    702: "SG",
    826: "GB",
    840: "US",
}


def load_duml_module():
    path = pathlib.Path(__file__).parent / "third-party" / "duml.py"
    spec = importlib.util.spec_from_file_location("area_readonly_duml", path)
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


def parse_area(payload: bytes) -> int | None:
    if len(payload) < 9 or payload[0] != GET_AREA_CODE:
        return None
    return int.from_bytes(payload[1:9], "little", signed=False)


def main() -> None:
    payload = bytes((GET_AREA_CODE,)) + bytes(8)
    if payload != b"\x04" + bytes(8):
        raise AssertionError("refusing anything except GET_AREA_CODE")

    duml = load_duml_module()
    sequence = int(time.monotonic() * 1000) & 0xFFFF
    packet = duml.build_packet(
        SOURCE,
        TARGET,
        CMD_TYPE_REQUEST_ACK,
        CMD_SET_FLYC,
        CMD_GET_SET_PRODUCT_CONFIG,
        payload,
        sequence,
    )

    context = usb1.USBContext()
    device = context.getByVendorIDAndProductID(VID, PID)
    if device is None:
        context.close()
        raise RuntimeError("DJI aircraft USB device not found")
    handle = device.open()
    handle.claimInterface(INTERFACE)
    pending = bytearray()
    areas: list[int] = []
    response_types: list[int] = []
    try:
        handle.bulkWrite(EP_OUT, packet, timeout=1000)
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            try:
                pending.extend(bytes(handle.bulkRead(EP_IN, 16 * 1024, timeout=250)))
            except usb1.USBErrorTimeout:
                continue
            for frame in extract_frames(pending):
                if (
                    frame[6:8] == sequence.to_bytes(2, "little")
                    and frame[9] == CMD_SET_FLYC
                    and frame[10] == CMD_GET_SET_PRODUCT_CONFIG
                ):
                    area = parse_area(frame[11:-2])
                    if area is not None:
                        areas.append(area)
                        response_types.append(frame[8])
    finally:
        handle.releaseInterface(INTERFACE)
        handle.close()
        context.close()

    if not areas:
        print("aircraft_area=unavailable")
        return
    area = areas[-1]
    alpha2 = ISO_NUMERIC_TO_ALPHA2.get(area, "unknown")
    print(f"aircraft_area={alpha2} iso_numeric={area}")
    print(f"response_cmd_type=0x{response_types[-1]:02x}")


if __name__ == "__main__":
    main()
