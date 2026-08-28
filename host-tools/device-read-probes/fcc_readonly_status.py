"""Read two fixed DJI SDR status registers from sky and ground endpoints.

Safety boundary: this tool can only issue OSD command 0x26
(`DataOsdSetSdrAssitantRead`) for the FCC selector at 0xFFFF0048 and frequency
band at 0xFFFF0063.  It contains no write, service-mode, country-code, commit,
or keepalive command.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import time

import usb1


VID = 0x2CA3
CMD_TYPE_REQUEST_ACK = 0x40
CMD_SET_OSD = 0x09
CMD_SDR_ASSISTANT_READ = 0x26
FCC_SELECTOR_ADDRESS = 0xFFFF0048
FREQUENCY_BAND_ADDRESS = 0xFFFF0063
CMD_SET_RC = 0x06
CMD_RC_POWER_MODE_GET = 0x21


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


def query(
    *,
    name: str,
    address: int,
    pid: int,
    interface: int,
    ep_out: int,
    ep_in: int,
    source: int,
    target: int,
):
    duml = load_duml_module()
    context = usb1.USBContext()
    device = context.getByVendorIDAndProductID(VID, pid)
    if device is None:
        context.close()
        return {"endpoint": name, "available": False, "replies": []}

    handle = device.open()
    handle.claimInterface(interface)
    sequence = (int(time.monotonic() * 1000) + target) & 0xFFFF
    if address not in {FCC_SELECTOR_ADDRESS, FREQUENCY_BAND_ADDRESS}:
        raise AssertionError("refusing an SDR register outside the read-only allow-list")
    payload = bytes((0x00, 0x02)) + address.to_bytes(4, "little")
    if CMD_SET_OSD != 0x09 or CMD_SDR_ASSISTANT_READ != 0x26 or len(payload) != 6:
        raise AssertionError("refusing anything except the fixed SDR assistant read")
    packet = duml.build_packet(
        source,
        target,
        CMD_TYPE_REQUEST_ACK,
        CMD_SET_OSD,
        CMD_SDR_ASSISTANT_READ,
        payload,
        sequence,
    )
    pending = bytearray()
    replies = []
    try:
        handle.bulkWrite(ep_out, packet, timeout=1000)
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            try:
                pending.extend(bytes(handle.bulkRead(ep_in, 16 * 1024, timeout=250)))
            except usb1.USBErrorTimeout:
                continue
            for frame in extract_frames(pending):
                if (
                    frame[6:8] == sequence.to_bytes(2, "little")
                    and frame[9] == CMD_SET_OSD
                    and frame[10] == CMD_SDR_ASSISTANT_READ
                ):
                    replies.append(
                        {
                            "sender": frame[4],
                            "receiver": frame[5],
                            "command_type": frame[8],
                            "payload_hex": frame[11:-2].hex(),
                        }
                    )
    finally:
        handle.releaseInterface(interface)
        handle.close()
        context.close()
    return {"endpoint": name, "available": True, "replies": replies}


def query_ground_power_mode(*, target: int, name: str):
    """Issue the legacy RC CE/FCC power-mode GET with an empty payload."""
    duml = load_duml_module()
    context = usb1.USBContext()
    device = context.getByVendorIDAndProductID(VID, 0x1021)
    if device is None:
        context.close()
        return {"endpoint": name, "available": False, "replies": []}

    handle = device.open()
    handle.claimInterface(0)
    sequence = (int(time.monotonic() * 1000) + 0x21) & 0xFFFF
    if CMD_SET_RC != 0x06 or CMD_RC_POWER_MODE_GET != 0x21:
        raise AssertionError("refusing anything except RC power-mode GET")
    packet = duml.build_packet(
        0xAA,
        target,
        CMD_TYPE_REQUEST_ACK,
        CMD_SET_RC,
        CMD_RC_POWER_MODE_GET,
        b"",
        sequence,
    )
    pending = bytearray()
    replies = []
    try:
        handle.bulkWrite(0x01, packet, timeout=1000)
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            try:
                pending.extend(bytes(handle.bulkRead(0x81, 16 * 1024, timeout=250)))
            except usb1.USBErrorTimeout:
                continue
            for frame in extract_frames(pending):
                if (
                    frame[6:8] == sequence.to_bytes(2, "little")
                    and frame[9] == CMD_SET_RC
                    and frame[10] == CMD_RC_POWER_MODE_GET
                ):
                    replies.append(
                        {
                            "sender": frame[4],
                            "receiver": frame[5],
                            "command_type": frame[8],
                            "payload_hex": frame[11:-2].hex(),
                        }
                    )
    finally:
        handle.releaseInterface(0)
        handle.close()
        context.close()
    return {"endpoint": name, "available": True, "replies": replies}


def main():
    results = [
        query(
            name="aircraft_sky_fcc_selector",
            address=FCC_SELECTOR_ADDRESS,
            pid=0x0020,
            interface=4,
            ep_out=0x04,
            ep_in=0x85,
            source=0x0A,
            target=0x09,
        ),
        query(
            name="rc2_ground_fcc_selector",
            address=FCC_SELECTOR_ADDRESS,
            pid=0x1021,
            interface=0,
            ep_out=0x01,
            ep_in=0x81,
            source=0xAA,
            target=0x0E,
        ),
        query(
            name="aircraft_sky_frequency_band",
            address=FREQUENCY_BAND_ADDRESS,
            pid=0x0020,
            interface=4,
            ep_out=0x04,
            ep_in=0x85,
            source=0x0A,
            target=0x09,
        ),
        query(
            name="rc2_ground_frequency_band",
            address=FREQUENCY_BAND_ADDRESS,
            pid=0x1021,
            interface=0,
            ep_out=0x01,
            ep_in=0x81,
            source=0xAA,
            target=0x0E,
        ),
        query_ground_power_mode(target=0x0E, name="rc2_ground_power_mode_osd_route"),
        query_ground_power_mode(target=0x06, name="rc2_ground_power_mode_rc_route"),
    ]
    print(json.dumps({"fixed_read_only_queries": results}, indent=2))


if __name__ == "__main__":
    main()
