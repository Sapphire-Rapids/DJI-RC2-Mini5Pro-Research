"""Bounded Sky/Ground country write-readback-rollback experiments.

Each surface is tested separately. Two fixed 0x07/0x19 GETs must both report
CN before the fixed 0x07/0x30 setter may send US. Every write is followed by a
fresh GET, and at most one CN restore write is permitted. No raw frames,
identifiers, power registers, or other commands are exposed.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import pathlib
import time

import usb1


VID = 0x2CA3
CMD_TYPE_REQUEST_ACK = 0x40
CMD_TYPE_RESPONSE = 0x80
CMD_SET_GENERAL = 0x07
CMD_GET_COUNTRY = 0x19
CMD_SET_COUNTRY = 0x30
LAB_ORIGINAL = "CN"
LAB_TARGET = "US"
ONE_SHOT_AUTHORIZATION_CONSUMED = True
ALLOWED = {"CN", "US", "FR", "DE", "JP", "SG", "GB", "AE", "AU"}


@dataclass(frozen=True)
class Route:
    name: str
    pid: int
    interface: int
    ep_out: int
    ep_in: int
    source: int
    target: int


ROUTES = (
    Route("sky", 0x0020, 4, 0x04, 0x85, 0x0A, 0x09),
    Route("ground", 0x1021, 0, 0x01, 0x81, 0xAA, 0x0E),
)


def load_duml_module():
    path = pathlib.Path(__file__).parent / "third-party" / "duml.py"
    spec = importlib.util.spec_from_file_location("country_roundtrip_duml", path)
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
    return duml.calc_crc16(frame, len(frame) - 2) == int.from_bytes(frame[-2:], "little")


def country_payload(country: str) -> bytes:
    if country not in ALLOWED:
        raise ValueError("country is outside the fixed lab allow-list")
    code = country.encode("ascii")
    return code + bytes(2) + code + bytes(2) + b"\x01\x00"


def parse_country(payload: bytes) -> str | None:
    if len(payload) < 4 or payload[0] != 0:
        return None
    value = payload[1:3]
    if not all(ord("A") <= byte <= ord("Z") for byte in value):
        return None
    if any(payload[3:]):
        return None
    return value.decode("ascii")


class CountrySession:
    def __init__(self, handle, route: Route, duml):
        self.handle = handle
        self.route = route
        self.duml = duml
        self.pending = bytearray()
        self.sequence = int(time.monotonic() * 1000) & 0xFFFF

    def exchange(self, command: int, payload: bytes, timeout: float = 2.0) -> bytes:
        if command not in (CMD_GET_COUNTRY, CMD_SET_COUNTRY):
            raise AssertionError("refusing a non-country command")
        self.sequence = (self.sequence + 1) & 0xFFFF
        packet = self.duml.build_packet(
            self.route.source,
            self.route.target,
            CMD_TYPE_REQUEST_ACK,
            CMD_SET_GENERAL,
            command,
            payload,
            self.sequence,
        )
        written = self.handle.bulkWrite(self.route.ep_out, packet, timeout=1000)
        if written != len(packet):
            raise RuntimeError(f"short {self.route.name} USB write")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                self.pending.extend(
                    bytes(self.handle.bulkRead(self.route.ep_in, 16 * 1024, timeout=250))
                )
            except usb1.USBErrorTimeout:
                continue
            for frame in extract_frames(self.pending):
                if not valid_crc(frame, self.duml):
                    continue
                if (
                    frame[4] == self.route.target
                    and frame[5] == self.route.source
                    and frame[6:8] == self.sequence.to_bytes(2, "little")
                    and frame[8] == CMD_TYPE_RESPONSE
                    and frame[9] == CMD_SET_GENERAL
                    and frame[10] == command
                ):
                    return frame[11:-2]
        raise TimeoutError(f"no matching validated {self.route.name} response")

    def get_country(self) -> str:
        country = parse_country(self.exchange(CMD_GET_COUNTRY, b""))
        if country not in ALLOWED:
            raise RuntimeError(f"{self.route.name} returned an unsupported country")
        return country

    def set_country_once(self, country: str) -> None:
        response = self.exchange(CMD_SET_COUNTRY, country_payload(country))
        if response and response[0] != 0:
            raise RuntimeError(f"{self.route.name} setter returned a failure status")


def test_route(route: Route, duml) -> None:
    context = usb1.USBContext()
    handle = None
    interface_claimed = False
    session: CountrySession | None = None
    original: str | None = None
    forward_write_attempted = False
    forward_observed: str | None = None
    restore_write_attempted = False
    rollback_verified = False
    last_observed: str | None = None
    primary_error: BaseException | None = None
    rollback_error: BaseException | None = None
    cleanup_error: BaseException | None = None
    try:
        devices = [
            device
            for device in context.getDeviceList(skip_on_error=True)
            if device.getVendorID() == VID and device.getProductID() == route.pid
        ]
        if len(devices) != 1:
            raise RuntimeError(
                f"{route.name} expected exactly one USB device; found {len(devices)}"
            )
        handle = devices[0].open()
        handle.claimInterface(route.interface)
        interface_claimed = True
        session = CountrySession(handle, route, duml)

        snapshot = session.get_country()
        confirmation = session.get_country()
        print(f"{route.name}_snapshot={snapshot}")
        print(f"{route.name}_preflight_confirmation={confirmation}")
        if snapshot != LAB_ORIGINAL or confirmation != LAB_ORIGINAL:
            raise RuntimeError(
                f"{route.name} authorized start must be two consecutive CN reads"
            )
        original = LAB_ORIGINAL

        forward_write_attempted = True
        session.set_country_once(LAB_TARGET)
        forward_observed = session.get_country()
        print(f"{route.name}_forward_readback={forward_observed}")
        if forward_observed != LAB_TARGET:
            raise RuntimeError(f"{route.name} forward readback mismatch")
        print(f"{route.name}_forward_verified=true")
    except BaseException as error:
        primary_error = error
    finally:
        try:
            if session is not None and original == LAB_ORIGINAL and forward_write_attempted:
                current = forward_observed
                if current not in (LAB_ORIGINAL, LAB_TARGET):
                    try:
                        current = session.get_country()
                    except BaseException as error:
                        rollback_error = error

                if current == LAB_ORIGINAL:
                    last_observed = current
                    rollback_verified = True
                elif current == LAB_TARGET:
                    restore_write_attempted = True
                    try:
                        session.set_country_once(LAB_ORIGINAL)
                    except BaseException as error:
                        rollback_error = error
                    try:
                        last_observed = session.get_country()
                        if last_observed == LAB_ORIGINAL:
                            rollback_verified = True
                        elif last_observed != LAB_TARGET:
                            rollback_error = RuntimeError(
                                f"{route.name} reached third country {last_observed}; "
                                "refusing any further write"
                            )
                        else:
                            rollback_error = RuntimeError(
                                f"{route.name} remained US after its single restore write"
                            )
                    except BaseException as error:
                        rollback_error = error
                elif current is not None:
                    last_observed = current
                    rollback_error = RuntimeError(
                        f"{route.name} reached third country {current}; "
                        "refusing any restore write"
                    )
                elif rollback_error is None:
                    rollback_error = RuntimeError(
                        f"{route.name} country unavailable; refusing a blind restore write"
                    )

                print(f"{route.name}_rollback_readback={last_observed or 'unavailable'}")
                print(
                    f"{route.name}_rollback_verified="
                    f"{'true' if rollback_verified else 'false'}"
                )
                print(
                    f"{route.name}_restore_write_attempted="
                    f"{'true' if restore_write_attempted else 'false'}"
                )
        finally:
            if handle is not None and interface_claimed:
                try:
                    handle.releaseInterface(route.interface)
                except BaseException as error:
                    cleanup_error = error
            if handle is not None:
                try:
                    handle.close()
                except BaseException as error:
                    cleanup_error = cleanup_error or error
            try:
                context.close()
            except BaseException as error:
                cleanup_error = cleanup_error or error

    if forward_write_attempted and not rollback_verified:
        detail = rollback_error or RuntimeError("rollback was not verified")
        raise RuntimeError(
            f"{route.name} rollback could not be verified after one restore attempt"
        ) from detail
    if primary_error is not None:
        raise primary_error
    if cleanup_error is not None:
        raise RuntimeError(f"{route.name} USB cleanup failed") from cleanup_error


def main() -> None:
    if ONE_SHOT_AUTHORIZATION_CONSUMED:
        raise RuntimeError(
            "the 2026-08-27 one-shot Sky/Ground authorization has been consumed; "
            "refusing to write again"
        )
    duml = load_duml_module()
    for route in ROUTES:
        test_route(route, duml)


if __name__ == "__main__":
    main()
