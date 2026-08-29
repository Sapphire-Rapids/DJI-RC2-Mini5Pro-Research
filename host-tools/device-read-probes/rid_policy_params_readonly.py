"""Strictly read two fixed RID-policy FC parameters over verified USB paths.

Only FLYC F7 metadata reads and F8 value reads are reachable. Every response
must pass DUML framing/CRC/reverse-route/sequence/response-type checks. F8 is
accepted only when the echoed requested hash, F7 wire type/size, and exact
payload length close one published layout without ambiguity.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import json
from pathlib import Path
import time

import usb1

import rid_param_protocol as protocol


VID = 0x2CA3
LEGACY_TARGET_FC = 0x03
MODERN_SOURCE_APP4 = 0x82
MODERN_TARGET_FC4 = 0x92
CMD_TYPE_REQUEST_ACK = 0x40

RID_POLICY_PARAMETERS = (
    {
        "name": "g_config.flying_limit.max_height_0",
        "hash": 0x0371238A,
        "semantic_kind": "int",
    },
    {
        "name": "rid_ctrl_enable_0",
        "hash": 0x3CBD864F,
        "semantic_kind": "bool",
    },
    {
        "name": "ccc_broadcast_signal_quality_0",
        "hash": 0xD7757AD2,
        "semantic_kind": "int",
    },
    {
        "name": "EU_CE_enable_c0_rid_0",
        "hash": 0xF80992FE,
        "semantic_kind": "bool",
    },
)


def load_duml_module():
    path = Path(__file__).parent / "third-party" / "duml.py"
    spec = importlib.util.spec_from_file_location("rid_readonly_duml", path)
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
        length = int.from_bytes(buffer[1:3], "little") & 0x03FF
        if length < 13 or length > 1023:
            del buffer[0]
            continue
        if len(buffer) < length:
            return
        frame = bytes(buffer[:length])
        del buffer[:length]
        yield frame


def exchange_read(
    *,
    handle,
    duml,
    pending: bytearray,
    endpoint_out: int,
    endpoint_in: int,
    source: int,
    target: int,
    command_id: int,
    parameter_hash: int,
    sequence: int,
    reply_seconds: float,
    wire_mode: str,
) -> bytes:
    if command_id not in protocol.READ_ONLY_COMMANDS:
        raise AssertionError("refusing a non-read-only command")
    packet = duml.build_packet(
        source,
        target,
        CMD_TYPE_REQUEST_ACK,
        protocol.CMD_SET_FLYC,
        command_id,
        parameter_hash.to_bytes(4, "little"),
        sequence,
    )
    if wire_mode == "simple":
        packet = protocol.encrypt_read_request_frame(packet, duml=duml)
    elif wire_mode != "plaintext":
        raise AssertionError("unsupported wire mode")
    written = handle.bulkWrite(endpoint_out, packet, timeout=1000)
    if written != len(packet):
        raise RuntimeError("short USB write")

    deadline = time.monotonic() + reply_seconds
    rejected_matching_frames = 0
    while time.monotonic() < deadline:
        try:
            pending.extend(bytes(handle.bulkRead(endpoint_in, 16 * 1024, timeout=250)))
        except usb1.USBErrorTimeout:
            continue
        for frame in extract_frames(pending):
            # The command tuple itself is encrypted in a SIMPLE reply.  Use the
            # cleartext sequence as the first filter, then let the strict frame
            # validator decrypt and check the fixed command tuple.
            if len(frame) < 11:
                continue
            if int.from_bytes(frame[6:8], "little") != sequence:
                continue
            try:
                return protocol.validate_response_frame(
                    frame,
                    duml=duml,
                    expected_sender=target,
                    expected_receiver=source,
                    expected_sequence=sequence,
                    expected_command_id=command_id,
                )
            except protocol.ParamProtocolError:
                rejected_matching_frames += 1
    if rejected_matching_frames:
        raise RuntimeError(
            f"no valid response; rejected {rejected_matching_frames} matching frame(s)"
        )
    raise TimeoutError("no matching response")


def transport_config(name: str) -> dict[str, int]:
    if name == "aircraft":
        return {
            "pid": 0x0020,
            "interface": 4,
            "endpoint_out": 0x04,
            "endpoint_in": 0x85,
            "source": 0x0A,
        }
    if name == "rc2":
        return {
            "pid": 0x1021,
            "interface": 0,
            "endpoint_out": 0x01,
            "endpoint_in": 0x81,
            "source": 0xAA,
        }
    raise ValueError("unsupported transport")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=("aircraft", "rc2"), required=True)
    parser.add_argument(
        "--route",
        choices=("legacy", "modern"),
        default="legacy",
        help="legacy uses the previously validated direct route; modern uses app4 0x82 -> FC4 0x92",
    )
    parser.add_argument(
        "--parameter",
        choices=tuple(item["name"] for item in RID_POLICY_PARAMETERS),
        help="run only one fixed parameter instead of the full allow-list",
    )
    parser.add_argument("--reply-seconds", type=float, default=1.5)
    parser.add_argument(
        "--wire-mode",
        choices=("plaintext", "simple"),
        default="plaintext",
        help="DUML framing for the fixed F7/F8 reads; SIMPLE uses no handshake",
    )
    args = parser.parse_args()
    if not 0.25 <= args.reply_seconds <= 5.0:
        raise SystemExit("--reply-seconds must be between 0.25 and 5.0")

    config = transport_config(args.transport)
    if args.route == "modern":
        route_source = MODERN_SOURCE_APP4
        route_target = MODERN_TARGET_FC4
    else:
        route_source = config["source"]
        route_target = LEGACY_TARGET_FC
    selected_parameters = tuple(
        item for item in RID_POLICY_PARAMETERS
        if args.parameter is None or item["name"] == args.parameter
    )
    duml = load_duml_module()
    context = usb1.USBContext()
    device = context.getByVendorIDAndProductID(VID, config["pid"])
    if device is None:
        context.close()
        raise SystemExit(f"DJI {args.transport} USB device not found")

    handle = device.open()
    handle.claimInterface(config["interface"])
    pending = bytearray()
    sequence = int(time.monotonic() * 1000) & 0xFFFF
    results: list[dict[str, object]] = []
    try:
        for item in selected_parameters:
            record: dict[str, object] = {
                "parameter": item["name"],
                "hash": f"0x{item['hash']:08X}",
                "state": "unavailable",
            }
            try:
                last_reply_kind = "F7"
                last_reply_payload: bytes | None = None
                sequence = (sequence + 1) & 0xFFFF
                f7_payload = exchange_read(
                    handle=handle,
                    duml=duml,
                    pending=pending,
                    endpoint_out=config["endpoint_out"],
                    endpoint_in=config["endpoint_in"],
                    source=route_source,
                    target=route_target,
                    command_id=protocol.CMD_GET_PARAM_INFO_BY_HASH,
                    parameter_hash=item["hash"],
                    sequence=sequence,
                    reply_seconds=args.reply_seconds,
                    wire_mode=args.wire_mode,
                )
                last_reply_payload = f7_payload
                metadata = protocol.parse_f7_metadata(
                    f7_payload,
                    expected_name=item["name"],
                    semantic_kind=item["semantic_kind"],
                )
                record["metadata"] = protocol.metadata_summary(metadata)

                sequence = (sequence + 1) & 0xFFFF
                last_reply_kind = "F8"
                last_reply_payload = None
                f8_payload = exchange_read(
                    handle=handle,
                    duml=duml,
                    pending=pending,
                    endpoint_out=config["endpoint_out"],
                    endpoint_in=config["endpoint_in"],
                    source=route_source,
                    target=route_target,
                    command_id=protocol.CMD_GET_PARAM_VALUE_BY_HASH,
                    parameter_hash=item["hash"],
                    sequence=sequence,
                    reply_seconds=args.reply_seconds,
                    wire_mode=args.wire_mode,
                )
                last_reply_payload = f8_payload
                value = protocol.parse_f8_value(
                    f8_payload,
                    expected_hash=item["hash"],
                    metadata=metadata,
                    semantic_kind=item["semantic_kind"],
                )
                record.update(
                    {
                        "state": "read",
                        "layout": value.layout,
                        "value": value.decoded,
                        "value_raw_hex": value.raw.hex(),
                    }
                )
            except (
                TimeoutError,
                RuntimeError,
                protocol.ParamProtocolError,
                usb1.USBError,
            ) as exc:
                record["reason"] = f"{type(exc).__name__}: {exc}"
                if last_reply_payload is not None:
                    record["diagnostic_reply"] = {
                        "command": last_reply_kind,
                        "payload_length": len(last_reply_payload),
                        "payload_hex": last_reply_payload.hex(),
                    }
            results.append(record)
            time.sleep(0.1)
    finally:
        handle.releaseInterface(config["interface"])
        handle.close()
        context.close()

    print(
        json.dumps(
            {
                "transport": args.transport,
                "mode": "F7/F8 read-only",
                "route": args.route,
                "source": f"0x{route_source:02X}",
                "target": f"0x{route_target:02X}",
                "wire_mode": args.wire_mode,
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
