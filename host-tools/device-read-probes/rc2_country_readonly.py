"""Read country-code state from fixed DJI device routes through one DUML GET.

The only outbound command is cmd set 0x07 / cmd id 0x19 with an empty
payload.  It never sends the 0x18 or 0x30 country setters and never prints raw
frames or device identifiers.
"""

from __future__ import annotations

import importlib.util
import sys
import pathlib
import time

import usb1


VID = 0x2CA3
PID = 0x1021
INTERFACE = 0
EP_OUT = 0x01
EP_IN = 0x81
SOURCE = 0xAA
CMD_TYPE_REQUEST_ACK = 0x40
CMD_SET_GENERAL = 0x07
CMD_GET_COUNTRY = 0x19


def load_duml_module():
    path = pathlib.Path(__file__).parent / "third-party" / "duml.py"
    spec = importlib.util.spec_from_file_location("country_readonly_duml", path)
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


def parse_country(payload: bytes) -> str | None:
    offset = 1 if len(payload) >= 3 and payload[0] == 0 else 0
    if len(payload) < offset + 2:
        return None
    candidate = payload[offset : offset + 2]
    if not all(ord("A") <= value <= ord("Z") for value in candidate):
        return None
    return candidate.decode("ascii")


def query_route(
    *, route_name: str, target: int
) -> tuple[str | None, int | None, int | None, bool | None]:
    if (CMD_SET_GENERAL, CMD_GET_COUNTRY) != (0x07, 0x19):
        raise AssertionError("refusing anything except the fixed country GET")

    duml = load_duml_module()
    sequence = (int(time.monotonic() * 1000) + target) & 0xFFFF
    packet = duml.build_packet(
        SOURCE,
        target,
        CMD_TYPE_REQUEST_ACK,
        CMD_SET_GENERAL,
        CMD_GET_COUNTRY,
        b"",
        sequence,
    )

    context = usb1.USBContext()
    device = context.getByVendorIDAndProductID(VID, PID)
    if device is None:
        context.close()
        raise RuntimeError("RC 2 USB device not found")
    handle = device.open()
    handle.claimInterface(INTERFACE)
    pending = bytearray()
    countries: list[str] = []
    response_types: list[int] = []
    response_lengths: list[int] = []
    trailing_zero: list[bool] = []
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
                    and frame[9] == CMD_SET_GENERAL
                    and frame[10] == CMD_GET_COUNTRY
                ):
                    country = parse_country(frame[11:-2])
                    if country is not None:
                        response_payload = frame[11:-2]
                        offset = 1 if len(response_payload) >= 3 and response_payload[0] == 0 else 0
                        countries.append(country)
                        response_types.append(frame[8])
                        response_lengths.append(len(response_payload))
                        trailing_zero.append(all(value == 0 for value in response_payload[offset + 2 :]))
    finally:
        handle.releaseInterface(INTERFACE)
        handle.close()
        context.close()

    if not countries:
        return None, None, None, None
    return countries[-1], response_types[-1], response_lengths[-1], trailing_zero[-1]


def main() -> None:
    # 0x09 is the airlink/Sky surface. 0x0E and 0x06 are probed separately so
    # a Sky reply is never mislabeled as the RC Android or Ground state.
    for route_name, target in (("sky", 0x09), ("ground", 0x0E), ("rc", 0x06)):
        country, response_type, payload_length, trailing_zero = query_route(
            route_name=route_name,
            target=target,
        )
        print(f"{route_name}_country={country or 'unavailable'}")
        if response_type is not None and payload_length is not None:
            print(
                f"{route_name}_response_cmd_type=0x{response_type:02x} "
                f"payload_length={payload_length} trailing_zero={str(trailing_zero).lower()}"
            )


if __name__ == "__main__":
    main()
