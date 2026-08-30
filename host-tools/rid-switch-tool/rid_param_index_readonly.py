"""Read Mini 5 Pro (wa150) RID parameters by index over USB DUML.

This probe uses the by-index FLYC command family (0xE0 table attributes,
0xE1 get_info, 0xE2 read value) recovered from the public wa150 firmware
parameter table. It is strictly read-only: the 0xE3 write command is not
reachable from this file, no value is changed, and no motor or RF state is
observed.

The probe first verifies the parameter table identity (0xE0 CRC/count), then
for each candidate RID index performs get_info (0xE1) and read value (0xE2).
A name mismatch or a status error is reported as unavailable, never guessed.

For each candidate it also reports the by-hash bridge value computed from the
candidate's ``_0`` name form through the independent FLYC parameter-name hash.
This read-only metadata lets an operator map an on-board by-index name to the
by-hash F7/F8/F9 identifier without writing anything.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import json
from pathlib import Path
import time

import usb1

from index_protocol_guard import validate_response, verify_table_identity
from switch_safety import close_usb

VID = 0x2CA3
LEGACY_TARGET_FC = 0x03
MODERN_SOURCE_APP4 = 0x82
MODERN_TARGET_FC4 = 0x92
CMD_TYPE_REQUEST_ACK = 0x40

# Mini 5 Pro (wa150) parameter-table candidate RID indices. The on-board name is
# always re-verified through get_info before a value is interpreted.
CANDIDATES = (
    {"table": 0, "index": 1306, "name": "EU_CE_enable_c0_rid"},
    {"table": 0, "index": 1308, "name": "EU_CE_Reg_RID_Enable"},
    {"table": 0, "index": 1315, "name": "eu_ce_support_remote_set_level"},
)


def load_index_protocol_module():
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "libraries"
        / "protocol-probes"
        / "rid_param_index_protocol.py"
    )
    spec = importlib.util.spec_from_file_location("rid_param_index_protocol", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load index protocol from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module.__name__] = module
    spec.loader.exec_module(module)
    return module


def load_duml_module():
    path = (
        Path(__file__).resolve().parent.parent
        / "device-read-probes"
        / "third-party"
        / "duml.py"
    )
    spec = importlib.util.spec_from_file_location("rid_index_duml", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load DUML implementation from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module.__name__] = module
    spec.loader.exec_module(module)
    return module


def load_hash_module():
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "libraries"
        / "protocol-probes"
        / "dji_flyc_parameter_hash.py"
    )
    spec = importlib.util.spec_from_file_location("rid_index_hash", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load hash module from {path}")
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only by-index RID parameter probe."
    )
    parser.add_argument(
        "--transport",
        choices=("aircraft", "rc2"),
        default="rc2",
        help="USB transport to use (default: rc2)",
    )
    parser.add_argument(
        "--route",
        choices=("legacy", "modern"),
        default="legacy",
        help="FC routing; modern is 0x82->0x92 (aircraft only, default: legacy)",
    )
    parser.add_argument(
        "--reply-seconds",
        type=float,
        default=2.0,
        help="per-reply receive window in seconds (default: 2.0)",
    )
    args = parser.parse_args(argv)
    if not 0.25 <= args.reply_seconds <= 5.0:
        raise SystemExit("--reply-seconds must be between 0.25 and 5.0")

    protocol = load_index_protocol_module()
    duml = load_duml_module()
    hash_module = load_hash_module()
    config = transport_config(args.transport)
    if args.route == "modern":
        if args.transport != "aircraft":
            raise SystemExit("--route modern is only defined for the aircraft transport")
        route_source = MODERN_SOURCE_APP4
        route_target = MODERN_TARGET_FC4
    else:
        route_source = config["source"]
        route_target = LEGACY_TARGET_FC

    context = None
    handle = None
    claimed = False
    pending = bytearray()
    sequence = int(time.monotonic() * 1000) & 0xFFFF

    def exchange(command_id: int, payload: bytes) -> bytes:
        nonlocal sequence
        if command_id not in protocol.READ_ONLY_INDEX_COMMANDS:
            raise AssertionError("refusing a non-read-only index command")
        sequence = (sequence + 1) & 0xFFFF
        packet = duml.build_packet(
            route_source,
            route_target,
            CMD_TYPE_REQUEST_ACK,
            protocol.CMD_SET_FLYC,
            command_id,
            payload,
            sequence,
        )
        written = handle.bulkWrite(config["endpoint_out"], packet, timeout=1000)
        if written != len(packet):
            raise RuntimeError("short USB write")
        deadline = time.monotonic() + args.reply_seconds
        rejected = 0
        while time.monotonic() < deadline:
            try:
                pending.extend(
                    bytes(handle.bulkRead(config["endpoint_in"], 16 * 1024, timeout=250))
                )
            except usb1.USBErrorTimeout:
                continue
            for frame in extract_frames(pending):
                if len(frame) < 11:
                    continue
                if int.from_bytes(frame[6:8], "little") != sequence:
                    continue
                try:
                    return validate_response(
                        frame, duml=duml, sender=route_target, receiver=route_source,
                        sequence=sequence, command=command_id,
                    )
                except RuntimeError:
                    rejected += 1
        if rejected:
            raise RuntimeError("no valid by-index response")
        raise TimeoutError("no matching response")

    report: dict[str, object] = {
        "transport": args.transport,
        "route": args.route,
        "source": f"0x{route_source:02X}",
        "route_target": f"0x{route_target:02X}",
        "mode": "by-index read-only",
        "table": 0,
        "table_attributes": None,
        "results": [],
    }

    def run():
        nonlocal context, handle, claimed
        context = usb1.USBContext()
        device = context.getByVendorIDAndProductID(VID, config["pid"])
        if device is None:
            raise RuntimeError("USB device not found")

        handle = device.open()
        handle.claimInterface(config["interface"])
        claimed = True
        # Table identity positive control.
        try:
            attr_payload = exchange(
                protocol.CMD_GET_TABLE_ATTRIBUTES,
                protocol.build_table_attributes_request(0),
            )
            attrs = protocol.parse_table_attributes(attr_payload)
            verify_table_identity(attrs)
            report["table_attributes"] = {
                "crc": f"0x{attrs.crc:08X}",
                "count": attrs.count,
            }
        except (
            TimeoutError,
            RuntimeError,
            protocol.ParamIndexError,
            usb1.USBError,
        ) as exc:
            report["table_attributes"] = {"error": f"{type(exc).__name__}: {exc}"}
            return 1

        for candidate in CANDIDATES:
            record: dict[str, object] = {
                "index": candidate["index"],
                "expected_name": candidate["name"],
                "state": "unavailable",
            }
            try:
                info_payload = exchange(
                    protocol.CMD_GET_INFO,
                    protocol.build_get_info_request(0, candidate["index"]),
                )
                info = protocol.parse_get_info(
                    info_payload,
                    expected_name=candidate["name"],
                    expected_index=candidate["index"],
                )
                record["info"] = protocol.info_summary(info)
                record["by_hash_bridge"] = {
                    "name": f"{candidate['name']}_0",
                    "hash": f"0x{hash_module.dji_flyc_parameter_hash(candidate['name'] + '_0'):08X}",
                }

                value_payload = exchange(
                    protocol.CMD_READ_VALUE,
                    protocol.build_read_value_request(0, candidate["index"]),
                )
                value = protocol.parse_read_value(
                    value_payload, index=candidate["index"], info=info
                )
                record.update(
                    {
                        "state": "read",
                        "value": value.decoded,
                        "value_raw_hex": value.raw.hex(),
                    }
                )
            except (
                TimeoutError,
                RuntimeError,
                protocol.ParamIndexError,
                usb1.USBError,
            ) as exc:
                record["reason"] = f"{type(exc).__name__}: {exc}"
            report["results"].append(record)
        return 0 if all(item["state"] == "read" for item in report["results"]) else 1
    try:
        exit_code = run()
    except (Exception, KeyboardInterrupt) as exc:
        report["error_type"] = type(exc).__name__
        exit_code = 1
    finally:
        close_usb(context=context, handle=handle, claimed=claimed,
                  interface=config["interface"], report=report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report.get("cleanup_errors") else exit_code


if __name__ == "__main__":
    raise SystemExit(main())
