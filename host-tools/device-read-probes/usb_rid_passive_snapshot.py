"""Bounded, input-only RID metadata snapshot from fixed DJI USB endpoints.

The probe never obtains an output endpoint and never calls bulkWrite. It retains
no raw frame, route, sequence, identifier, position, or payload. Only strict
CRC-valid command counts and the latest seven-byte RID working-status summary
are printed.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import pathlib
import time

import usb1


VID = 0x2CA3
MAX_FRAME = 1023
READ_SECONDS = 8.0


@dataclass(frozen=True)
class InputRoute:
    name: str
    pid: int
    interface: int
    ep_in: int


ROUTES = (
    InputRoute("sky", 0x0020, 4, 0x85),
    InputRoute("ground", 0x1021, 0, 0x81),
)


def load_duml_module():
    path = pathlib.Path(__file__).parent / "third-party" / "duml.py"
    spec = importlib.util.spec_from_file_location("usb_rid_passive_duml", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load local DUML checksum implementation")
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
        version = (buffer[1] | (buffer[2] << 8)) >> 10
        if length < 13 or length > MAX_FRAME or version != 1:
            del buffer[0]
            continue
        if len(buffer) < length:
            return
        frame = bytes(buffer[:length])
        del buffer[:length]
        yield frame


def valid_crc(frame: bytes, duml) -> bool:
    return (
        len(frame) >= 13
        and duml.calc_crc8(frame, 3) == frame[3]
        and duml.calc_crc16(frame, len(frame) - 2)
        == int.from_bytes(frame[-2:], "little")
    )


def rid_summary(payload: bytes) -> str | None:
    if len(payload) != 7:
        return None
    flags = int.from_bytes(payload[0:2], "little")
    return (
        f"eid_supported={str(bool(flags & (1 << 1))).lower()} "
        f"rid_supported={str(bool(flags & (1 << 0))).lower()} "
        f"eid_normal={str(bool(flags & (1 << 9))).lower()} "
        f"rid_normal={str(bool(flags & (1 << 8))).lower()} "
        f"area_code={int.from_bytes(payload[2:6], 'little', signed=True)} "
        f"failure_code={payload[6]}"
    )


def observe(route: InputRoute, duml) -> None:
    context = usb1.USBContext()
    handle = None
    claimed = False
    pending = bytearray()
    read_buffer = bytearray()
    valid_count = 0
    command_counts = {
        (0x11, 0x1C): 0,
        (0x03, 0x09): 0,
        (0x03, 0x42): 0,
        (0x03, 0x77): 0,
        (0x11, 0x11): 0,
        (0x11, 0x12): 0,
        (0x11, 0x4B): 0,
    }
    latest_rid = None
    try:
        devices = [
            device
            for device in context.getDeviceList(skip_on_error=True)
            if device.getVendorID() == VID and device.getProductID() == route.pid
        ]
        if len(devices) != 1:
            print(f"{route.name}_available=false")
            return
        handle = devices[0].open()
        handle.claimInterface(route.interface)
        claimed = True
        deadline = time.monotonic() + READ_SECONDS
        while time.monotonic() < deadline:
            try:
                chunk = bytes(handle.bulkRead(route.ep_in, 16 * 1024, timeout=250))
            except usb1.USBErrorTimeout:
                continue
            read_buffer.extend(chunk)
            pending.extend(read_buffer)
            read_buffer.clear()
            for frame in extract_frames(pending):
                if not valid_crc(frame, duml):
                    continue
                valid_count += 1
                command = (frame[9], frame[10])
                if command in command_counts:
                    command_counts[command] += 1
                if command == (0x11, 0x1C) and frame[8] == 0:
                    decoded = rid_summary(frame[11:-2])
                    if decoded is not None:
                        latest_rid = decoded
        print(f"{route.name}_available=true")
        print(f"{route.name}_crc_valid_frames={valid_count}")
        for (cmd_set, cmd_id), count in command_counts.items():
            print(f"{route.name}_cmd_{cmd_set:02x}_{cmd_id:02x}_count={count}")
        print(f"{route.name}_latest_rid={latest_rid or 'unobserved'}")
    finally:
        for index in range(len(read_buffer)):
            read_buffer[index] = 0
        for index in range(len(pending)):
            pending[index] = 0
        if handle is not None and claimed:
            handle.releaseInterface(route.interface)
        if handle is not None:
            handle.close()
        context.close()


def main() -> None:
    duml = load_duml_module()
    for route in ROUTES:
        observe(route, duml)


if __name__ == "__main__":
    main()
