"""Read the narrow French EID switch with the fixed DJI GET only.

The only outbound request is FLYC 0x03/0x77 with the one-byte GET payload
0x02 recovered from DJI MSDK 5.18 native code. For runtime product 139, the
merged characteristics table resolves the official default receiver to packed
DUML address 0x92 (type 18, index 4). It has no SET path, does not retry, and
emits no raw frame or device identifier.

The source bytes below are the already verified direct-USB bridge addresses;
they are not claims about DJI Fly's runtime GlobalPacketStatus sender index.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import pathlib
import time

from rid_param_protocol import simple_filter


VID = 0x2CA3
EID_RECEIVER_PRODUCT_139 = 0x92
EID_RECEIVER_DIRECT_FLYC = 0x03
CMD_TYPE_REQUEST_ACK = 0x40
CMD_TYPE_RESPONSE = 0x80
CMD_TYPE_ACK_RESPONSE = 0xC0
CMD_SET_FLYC = 0x03
CMD_EID_SWITCH = 0x77
GET_EID_SWITCH = b"\x02"
MAX_FRAME_BYTES = 1023

TRANSPORTS = {
    "aircraft": {
        "pid": 0x0020,
        "interface": 4,
        "endpoint_out": 0x04,
        "endpoint_in": 0x85,
        "source": 0x0A,
    },
    "rc2": {
        "pid": 0x1021,
        "interface": 0,
        "endpoint_out": 0x01,
        "endpoint_in": 0x81,
        "source": 0xAA,
    },
}


def load_duml_module():
    path = pathlib.Path(__file__).parent / "third-party" / "duml.py"
    spec = importlib.util.spec_from_file_location("eid_readonly_duml", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load DUML implementation from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module.__name__] = module
    spec.loader.exec_module(module)
    return module


def _later_complete_valid_frame(buffer: bytearray, duml) -> int | None:
    """Find a later complete valid frame when a plausible false header blocks parsing."""

    search_from = 1
    while search_from < len(buffer):
        try:
            start = buffer.index(0x55, search_from)
        except ValueError:
            return None
        if len(buffer) - start < 3:
            return None
        declared = int.from_bytes(buffer[start + 1 : start + 3], "little")
        length = declared & 0x03FF
        if (
            declared >> 10 == 1
            and 13 <= length <= MAX_FRAME_BYTES
            and len(buffer) - start >= length
            and valid_crc(bytes(buffer[start : start + length]), duml)
        ):
            return start
        search_from = start + 1
    return None


def extract_frames(buffer: bytearray, duml):
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
        declared = int.from_bytes(buffer[1:3], "little")
        length = declared & 0x03FF
        if declared >> 10 != 1 or length < 13 or length > MAX_FRAME_BYTES:
            del buffer[0]
            continue
        if len(buffer) < length:
            later = _later_complete_valid_frame(buffer, duml)
            if later is not None:
                del buffer[:later]
                continue
            return
        frame = bytes(buffer[:length])
        del buffer[:length]
        yield frame


def valid_crc(frame: bytes, duml) -> bool:
    if len(frame) < 13 or len(frame) > 1023:
        return False
    declared = int.from_bytes(frame[1:3], "little")
    if declared & 0x03FF != len(frame) or declared >> 10 != 1:
        return False
    if duml.calc_crc8(frame, 3) != frame[3]:
        return False
    return duml.calc_crc16(frame, len(frame) - 2) == int.from_bytes(frame[-2:], "little")


def parse_eid_payload(payload: bytes) -> str:
    """Parse the exact official GET ACK body without guessing extensions."""

    if len(payload) != 2:
        return "malformed"
    if payload[0] != 0:
        return "unsupported_or_error"
    if payload[1] & 0xFE:
        return "unknown_state_bits"
    return "enabled" if payload[1] == 1 else "disabled"


def build_fixed_get(
    duml,
    *,
    source: int,
    sequence: int,
    receiver: int = EID_RECEIVER_PRODUCT_139,
    wire_mode: str = "plaintext",
) -> bytes:
    """Build the sole command this probe is permitted to transmit."""

    if GET_EID_SWITCH != b"\x02":
        raise AssertionError("refusing anything except the fixed EID GET")
    request = duml.build_packet(
        source,
        receiver,
        CMD_TYPE_REQUEST_ACK,
        CMD_SET_FLYC,
        CMD_EID_SWITCH,
        GET_EID_SWITCH,
        sequence,
    )
    if wire_mode == "simple":
        encoded = bytearray(request)
        encoded[9:-2] = simple_filter(bytes(encoded[9:-2]), sequence)
        encoded[8] |= 0x03
        encoded[-2:] = duml.calc_crc16(encoded, len(encoded) - 2).to_bytes(
            2, "little"
        )
        request = bytes(encoded)
    elif wire_mode != "plaintext":
        raise ValueError(f"unsupported wire mode: {wire_mode}")
    if (
        len(request) != 14
        or not valid_crc(request, duml)
        or request[4] != source
        or request[5] != receiver
        or request[6:8] != sequence.to_bytes(2, "little")
    ):
        raise AssertionError("fixed EID GET encoder invariant failed")
    if wire_mode == "plaintext":
        interpreted = request
    else:
        interpreted = bytearray(request)
        interpreted[9:-2] = simple_filter(bytes(interpreted[9:-2]), sequence)
    if (
        interpreted[8] & ~0x03 != CMD_TYPE_REQUEST_ACK
        or bytes(interpreted[9:11]) != bytes((CMD_SET_FLYC, CMD_EID_SWITCH))
        or bytes(interpreted[11:-2]) != GET_EID_SWITCH
    ):
        raise AssertionError("fixed EID GET semantic invariant failed")
    return request


def matching_get_response(
    frame: bytes,
    *,
    duml,
    expected_source: int,
    expected_sequence: int,
    expected_receiver: int = EID_RECEIVER_PRODUCT_139,
) -> bytes | None:
    """Admit only a CRC-valid, exact reverse-route response to this GET."""

    if not (
        valid_crc(frame, duml)
        and frame[4] == expected_receiver
        and frame[5] == expected_source
        and frame[6:8] == expected_sequence.to_bytes(2, "little")
    ):
        return None
    encryption = frame[8] & 0x03
    command_type = frame[8] & ~0x03
    if encryption not in {0, 3} or command_type not in {
        CMD_TYPE_RESPONSE,
        CMD_TYPE_ACK_RESPONSE,
    }:
        return None
    interpreted = bytearray(frame)
    if encryption == 3:
        interpreted[9:-2] = simple_filter(
            bytes(interpreted[9:-2]), expected_sequence
        )
    if (
        interpreted[9] != CMD_SET_FLYC
        or interpreted[10] != CMD_EID_SWITCH
        or len(interpreted[11:-2]) != 2
    ):
        return None
    return bytes(interpreted[11:-2])


def main() -> None:
    try:
        import usb1
    except ImportError as exc:
        raise SystemExit(f"python usb1 module is required for live USB access: {exc}")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transport", choices=tuple(TRANSPORTS), required=True)
    parser.add_argument(
        "--route",
        choices=("product139", "direct-flyc"),
        default="product139",
        help="logical product-139 address 0x92 or direct FLYC address 0x03",
    )
    parser.add_argument(
        "--wire-mode",
        choices=("plaintext", "simple"),
        default="plaintext",
    )
    args = parser.parse_args()
    transport = TRANSPORTS[args.transport]
    receiver = (
        EID_RECEIVER_PRODUCT_139
        if args.route == "product139"
        else EID_RECEIVER_DIRECT_FLYC
    )
    duml = load_duml_module()
    sequence = (int(time.monotonic() * 1000) + CMD_EID_SWITCH) & 0xFFFF
    request = build_fixed_get(
        duml,
        source=transport["source"],
        sequence=sequence,
        receiver=receiver,
        wire_mode=args.wire_mode,
    )

    context = usb1.USBContext()
    devices = [
        device
        for device in context.getDeviceList(skip_on_error=True)
        if device.getVendorID() == VID and device.getProductID() == transport["pid"]
    ]
    if not devices:
        context.close()
        raise RuntimeError(f"DJI {args.transport} USB device not found")
    if len(devices) != 1:
        context.close()
        raise RuntimeError(
            f"ambiguous DJI {args.transport} USB match: found {len(devices)} devices"
        )
    handle = None
    claimed = False
    pending = bytearray()
    result: str | None = None
    try:
        handle = devices[0].open()
        handle.claimInterface(transport["interface"])
        claimed = True
        written = handle.bulkWrite(transport["endpoint_out"], request, timeout=1000)
        if written != len(request):
            raise RuntimeError("short USB write")
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline and result is None:
            try:
                pending.extend(
                    bytes(
                        handle.bulkRead(
                            transport["endpoint_in"], 16 * 1024, timeout=250
                        )
                    )
                )
            except usb1.USBErrorTimeout:
                continue
            for frame in extract_frames(pending, duml):
                response_payload = matching_get_response(
                    frame,
                    duml=duml,
                    expected_source=transport["source"],
                    expected_sequence=sequence,
                    expected_receiver=receiver,
                )
                if response_payload is not None:
                    result = parse_eid_payload(response_payload)
                    break
    finally:
        pending[:] = b"\x00" * len(pending)
        try:
            if claimed and handle is not None:
                handle.releaseInterface(transport["interface"])
        finally:
            try:
                if handle is not None:
                    handle.close()
            finally:
                context.close()

    print(f"transport={args.transport}")
    print(f"route={args.route}")
    print(f"wire_mode={args.wire_mode}")
    print("usb_route=experimental_unproven")
    print(f"canonical_get_ack={'observed' if result is not None else 'none'}")
    print(f"france_eid={result or 'unobserved'}")


if __name__ == "__main__":
    main()
