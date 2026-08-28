"""Bounded FC-area write/readback/rollback experiment for the lab aircraft.

This program changes only DataFlycGetSetProductConfig's validated area field.
It snapshots the original value, attempts one US write, immediately reads it
back, and restores the exact original value in ``finally``.  It has no generic
payload or command-line write interface and emits no identifiers or raw frames.
"""

from __future__ import annotations

import importlib.util
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
SET_AREA_CODE = 3
GET_AREA_CODE = 4
LAB_TARGET_AREA = 840  # ISO 3166-1 numeric US

ISO_NUMERIC_TO_ALPHA2 = {
    36: "AU",
    156: "CN",
    250: "FR",
    276: "DE",
    392: "JP",
    702: "SG",
    826: "GB",
    840: "US",
}


def load_duml_module():
    path = pathlib.Path(__file__).parent / "third-party" / "duml.py"
    spec = importlib.util.spec_from_file_location("area_roundtrip_duml", path)
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


def valid_crc(frame: bytes, duml) -> bool:
    if len(frame) < 13 or duml.calc_crc8(frame, 3) != frame[3]:
        return False
    expected = int.from_bytes(frame[-2:], "little")
    return duml.calc_crc16(frame, len(frame) - 2) == expected


class FCSession:
    def __init__(self, handle, duml):
        self.handle = handle
        self.duml = duml
        self.pending = bytearray()
        self.sequence = int(time.monotonic() * 1000) & 0xFFFF

    def exchange(self, payload: bytes, timeout: float = 2.0) -> bytes:
        self.sequence = (self.sequence + 1) & 0xFFFF
        packet = self.duml.build_packet(
            SOURCE,
            TARGET,
            CMD_TYPE_REQUEST_ACK,
            CMD_SET_FLYC,
            CMD_GET_SET_PRODUCT_CONFIG,
            payload,
            self.sequence,
        )
        self.handle.bulkWrite(EP_OUT, packet, timeout=1000)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                self.pending.extend(bytes(self.handle.bulkRead(EP_IN, 16 * 1024, timeout=250)))
            except usb1.USBErrorTimeout:
                continue
            for frame in extract_frames(self.pending):
                if not valid_crc(frame, self.duml):
                    continue
                if (
                    frame[4] == TARGET
                    and frame[5] == SOURCE
                    and frame[6:8] == self.sequence.to_bytes(2, "little")
                    and frame[9] == CMD_SET_FLYC
                    and frame[10] == CMD_GET_SET_PRODUCT_CONFIG
                ):
                    return frame[11:-2]
        raise TimeoutError("no matching validated FC response")

    def get_area(self) -> int:
        response = self.exchange(bytes((GET_AREA_CODE,)) + bytes(8))
        if len(response) < 9 or response[0] != GET_AREA_CODE:
            raise RuntimeError("malformed GET_AREA_CODE response")
        return int.from_bytes(response[1:9], "little", signed=False)

    def set_area_once(self, area: int) -> None:
        if area not in ISO_NUMERIC_TO_ALPHA2:
            raise ValueError("area is outside the fixed lab allow-list")
        payload = bytes((SET_AREA_CODE,)) + area.to_bytes(8, "little", signed=False)
        response = self.exchange(payload)
        if response and response[0] not in (0, SET_AREA_CODE):
            raise RuntimeError("SET_AREA_CODE returned an unexpected status")


def label(area: int) -> str:
    return f"{ISO_NUMERIC_TO_ALPHA2.get(area, 'unknown')}({area})"


def main() -> None:
    duml = load_duml_module()
    context = usb1.USBContext()
    device = context.getByVendorIDAndProductID(VID, PID)
    if device is None:
        context.close()
        raise RuntimeError("DJI aircraft USB device not found")
    handle = device.open()
    handle.claimInterface(INTERFACE)
    session = FCSession(handle, duml)
    original: int | None = None
    try:
        original = session.get_area()
        if original not in ISO_NUMERIC_TO_ALPHA2:
            raise RuntimeError("original area is not in the fixed rollback allow-list")
        print(f"snapshot={label(original)}")

        session.set_area_once(LAB_TARGET_AREA)
        observed = session.get_area()
        print(f"forward_readback={label(observed)}")
        if observed != LAB_TARGET_AREA:
            raise RuntimeError("forward write did not produce the requested readback")
        print("forward_verified=true")
    finally:
        if original is not None:
            restored = False
            last_observed: int | None = None
            for _ in range(3):
                try:
                    last_observed = session.get_area()
                    if last_observed == original:
                        restored = True
                        break
                    session.set_area_once(original)
                    last_observed = session.get_area()
                    if last_observed == original:
                        restored = True
                        break
                except (TimeoutError, usb1.USBError):
                    continue
            print(f"rollback_readback={label(last_observed) if last_observed is not None else 'unavailable'}")
            print(f"rollback_verified={'true' if restored else 'false'}")
            if not restored:
                raise RuntimeError("rollback could not be verified")
        handle.releaseInterface(INTERFACE)
        handle.close()
        context.close()


if __name__ == "__main__":
    main()
