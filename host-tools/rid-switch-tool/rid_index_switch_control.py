"""Bounded USB DUML by-index A-B-A for one EU C0 RID candidate parameter.

This tool addresses only the wa150 table parameter ``EU_CE_enable_c0_rid``
(index 1306, U8 0..1) over verified USB DUML paths. It never sends a write
unless the table identity (0xE0), the on-board name (0xE1), and the current
value (0xE2) all pass in the same session, and it always restores the captured
baseline immediately after the forward write. It has no generic payload, route,
command, or parameter interface.

Commands reachable: FLYC 0x03/0xE0 (table), 0x03/0xE1 (get_info), 0x03/0xE2
(read), 0x03/0xE3 (write). No motor is started and no radio state is measured.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import time

import usb1



VID = 0x2CA3
LEGACY_TARGET_FC = 0x03
CMD_TYPE_REQUEST_ACK = 0x40

# The single subject of this tool.
RID_INDEX = 1306
RID_NAME = "EU_CE_enable_c0_rid"

# wa150 (Mini 5 Pro) table identity published by lmdegreeds/djiparam. The probe
# re-verifies the live CRC/count through 0xE0 before any write.
WA150_TABLE_CRC = 0x5F8B2AE1
WA150_TABLE_COUNT = 1557


def load_protocol_module():
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "libraries"
        / "protocol-probes"
        / "rid_param_index_protocol.py"
    )
    spec = importlib.util.spec_from_file_location("rid_index_switch_protocol", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load index protocol from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_duml_module():
    path = (
        Path(__file__).resolve().parent.parent
        / "device-read-probes"
        / "third-party"
        / "duml.py"
    )
    spec = importlib.util.spec_from_file_location("rid_index_switch_duml", path)
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


class IndexSession:
    """One USB DUML session with fixed by-index routing and strict validation."""

    def __init__(
        self,
        *,
        handle,
        duml,
        protocol_module,
        source: int,
        target: int,
        endpoint_out: int,
        endpoint_in: int,
        reply_seconds: float,
    ):
        self.handle = handle
        self.duml = duml
        self.protocol = protocol_module
        self.source = source
        self.target = target
        self.endpoint_out = endpoint_out
        self.endpoint_in = endpoint_in
        self.reply_seconds = reply_seconds
        self.pending = bytearray()
        self.sequence = int(time.monotonic() * 1000) & 0xFFFF

    def exchange(self, command_id: int, payload: bytes) -> bytes:
        if command_id not in (
            self.protocol.READ_ONLY_INDEX_COMMANDS | {self.protocol.CMD_WRITE_VALUE}
        ):
            raise AssertionError("refusing an unlisted by-index command")
        self.sequence = (self.sequence + 1) & 0xFFFF
        packet = self.duml.build_packet(
            self.source,
            self.target,
            CMD_TYPE_REQUEST_ACK,
            self.protocol.CMD_SET_FLYC,
            command_id,
            payload,
            self.sequence,
        )
        written = self.handle.bulkWrite(self.endpoint_out, packet, timeout=1000)
        if written != len(packet):
            raise RuntimeError("short USB write")
        deadline = time.monotonic() + self.reply_seconds
        rejected = 0
        while time.monotonic() < deadline:
            try:
                self.pending.extend(
                    bytes(self.handle.bulkRead(self.endpoint_in, 16 * 1024, timeout=250))
                )
            except usb1.USBErrorTimeout:
                continue
            for frame in extract_frames(self.pending):
                if len(frame) < 11:
                    continue
                if int.from_bytes(frame[6:8], "little") != self.sequence:
                    continue
                if frame[4] != self.target or frame[5] != self.source:
                    continue
                if frame[9] != self.protocol.CMD_SET_FLYC or frame[10] != command_id:
                    continue
                return frame[11:-2]
        if rejected:
            raise RuntimeError(f"no valid response; rejected {rejected} matching frame(s)")
        raise TimeoutError("no matching response")


def probe_value(session: IndexSession):
    """Return the verified info and current Boolean value for the RID index."""

    protocol = session.protocol
    attr_payload = session.exchange(
        protocol.CMD_GET_TABLE_ATTRIBUTES,
        protocol.build_table_attributes_request(0),
    )
    attrs = protocol.parse_table_attributes(attr_payload)

    info_payload = session.exchange(
        protocol.CMD_GET_INFO, protocol.build_get_info_request(0, RID_INDEX)
    )
    info = protocol.parse_get_info(
        info_payload, expected_name=RID_NAME, expected_index=RID_INDEX
    )

    value_payload = session.exchange(
        protocol.CMD_READ_VALUE, protocol.build_read_value_request(0, RID_INDEX)
    )
    value = protocol.parse_read_value(value_payload, index=RID_INDEX, info=info)
    return attrs, info, value


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bounded USB DUML by-index A-B-A for EU_CE_enable_c0_rid."
    )
    parser.add_argument(
        "--transport",
        choices=("aircraft", "rc2"),
        default="rc2",
        help="USB transport to use (default: rc2)",
    )
    parser.add_argument(
        "--target",
        choices=("on", "off"),
        help="Forward write target; without it the tool only probes and reports",
    )
    parser.add_argument(
        "--reply-seconds",
        type=float,
        default=2.0,
        help="per-reply receive window in seconds (default: 2.0)",
    )
    args = parser.parse_args()
    if not 0.25 <= args.reply_seconds <= 5.0:
        raise SystemExit("--reply-seconds must be between 0.25 and 5.0")

    protocol = load_protocol_module()
    duml = load_duml_module()
    config = transport_config(args.transport)

    context = usb1.USBContext()
    device = context.getByVendorIDAndProductID(VID, config["pid"])
    if device is None:
        context.close()
        raise SystemExit(f"DJI {args.transport} USB device not found")

    handle = device.open()
    handle.claimInterface(config["interface"])
    session = IndexSession(
        handle=handle,
        duml=duml,
        protocol_module=protocol,
        source=config["source"],
        target=LEGACY_TARGET_FC,
        endpoint_out=config["endpoint_out"],
        endpoint_in=config["endpoint_in"],
        reply_seconds=args.reply_seconds,
    )

    report: dict[str, object] = {
        "transport": args.transport,
        "parameter": RID_NAME,
        "index": RID_INDEX,
        "target": args.target,
        "state": "unavailable",
        "steps": [],
    }

    def record(step: str, outcome: str, detail: dict[str, object]) -> None:
        report["steps"].append({"step": step, "outcome": outcome, **detail})

    baseline: bool | None = None
    info = None

    try:
        try:
            attrs, info, value = probe_value(session)
            record("table_identity", "verified", {
                "crc": f"0x{attrs.crc:08X}",
                "count": attrs.count,
                "expected_crc": f"0x{WA150_TABLE_CRC:08X}",
                "expected_count": WA150_TABLE_COUNT,
            })
            record("get_info", "verified", {"info": protocol.info_summary(info)})
            baseline = bool(value.decoded)
            record("baseline", "read", {
                "value": value.decoded,
                "raw_hex": value.raw.hex(),
            })
        except (
            TimeoutError,
            RuntimeError,
            protocol.ParamIndexError,
            usb1.USBError,
        ) as exc:
            record("baseline", "fail", {"reason": f"{type(exc).__name__}: {exc}"})
            report["state"] = "baseline_unavailable"
            raise RuntimeError("no same-session by-index baseline; no write attempted") from exc

        report["state"] = "baseline"
        if args.target is None:
            report["state"] = "probe_only"
            return

        target_value = args.target == "on"
        if baseline == target_value:
            record("forward_write", "no_op", {"reason": "baseline already equals target"})
            report["state"] = "already_target"
            return

        write_payload = protocol.build_write_value_request(
            0,
            RID_INDEX,
            protocol.encode_boolean_value(target_value, info=info),
            info=info,
        )
        try:
            ack = session.exchange(protocol.CMD_WRITE_VALUE, write_payload)
            status = protocol.parse_write_status(ack)
            record("forward_write", "ack", {"status": status})
        except (
            TimeoutError,
            RuntimeError,
            protocol.ParamIndexError,
            usb1.USBError,
        ) as exc:
            record("forward_write", "fail", {"reason": f"{type(exc).__name__}: {exc}"})
            report["state"] = "write_failed_restoring"
            raise

        forward_ok = False
        try:
            _, _, fwd_value = probe_value(session)
            forward_ok = bool(fwd_value.decoded) == target_value
            record("forward_readback", "match" if forward_ok else "mismatch", {
                "value": fwd_value.decoded,
                "raw_hex": fwd_value.raw.hex(),
            })
        except (
            TimeoutError,
            RuntimeError,
            protocol.ParamIndexError,
            usb1.USBError,
        ) as exc:
            record("forward_readback", "fail", {"reason": f"{type(exc).__name__}: {exc}"})

        # Always restore the baseline.
        restore_payload = protocol.build_write_value_request(
            0,
            RID_INDEX,
            protocol.encode_boolean_value(baseline, info=info),
            info=info,
        )
        restore_ok = False
        try:
            restore_ack = session.exchange(protocol.CMD_WRITE_VALUE, restore_payload)
            protocol.parse_write_status(restore_ack)
            _, _, restore_value = probe_value(session)
            restore_ok = bool(restore_value.decoded) == baseline
            record("restore", "ack" if restore_ok else "readback_mismatch", {
                "value": restore_value.decoded,
                "raw_hex": restore_value.raw.hex(),
            })
        except (
            TimeoutError,
            RuntimeError,
            protocol.ParamIndexError,
            usb1.USBError,
        ) as exc:
            record("restore", "fail", {"reason": f"{type(exc).__name__}: {exc}"})

        if restore_ok and forward_ok:
            report["state"] = "A_B_A_complete"
        elif restore_ok:
            report["state"] = "restored_forward_unverified"
        else:
            report["state"] = "restore_unverified"
    finally:
        handle.releaseInterface(config["interface"])
        handle.close()
        context.close()

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
