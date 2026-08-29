"""Bounded USB DUML control for the single RID candidate parameter.

This tool addresses only the fixed flight-controller parameter
``rid_ctrl_enable_0`` (hash ``0x3CBD864F``) over verified USB DUML paths. It
never sends a write unless a same-session F7/F8 baseline exists, and it always
restores that baseline immediately after a forward write. It has no generic
payload, route, command, or parameter interface.

Commands reachable here are FLYC 0x03/0xF7 (metadata), 0x03/0xF8 (value), and
0x03/0xF9 (write). F7/F8/F9 payloads and replies are SIMPLE-keystream protected;
plaintext wire mode is also supported for the read probes. The tool starts
motors for nothing and measures no radio state.
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
MODERN_SOURCE_APP4 = 0x82
MODERN_TARGET_FC4 = 0x92
CMD_TYPE_REQUEST_ACK = 0x40

# The single subject of this tool. A positive control is required first.
RID_PARAM_NAME = "rid_ctrl_enable_0"
RID_PARAM_HASH = 0x3CBD864F
RID_SEMANTIC_KIND = "bool"

POSITIVE_CONTROL_NAME = "g_config.flying_limit.max_height"
POSITIVE_CONTROL_HASH = 0x0371238A
POSITIVE_CONTROL_KIND = "int"


def build_target_raw(baseline_raw: bytes, target: bool) -> bytes:
    """Return the F9 value bytes for ``target`` with the baseline width.

    The strict Boolean decoder accepts a raw value of exactly the F7 width
    filled with all-zero or all-one bytes. This helper keeps that width and
    never changes it.
    """

    if not baseline_raw:
        raise ValueError("baseline raw value is empty")
    return bytes([1 if target else 0]) * len(baseline_raw)


def load_protocol_module():
    path = Path(__file__).resolve().parent.parent / "device-read-probes" / "rid_param_protocol.py"
    spec = importlib.util.spec_from_file_location("rid_switch_protocol", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load rid_param_protocol from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_duml_module():
    path = Path(__file__).resolve().parent.parent / "device-read-probes" / "third-party" / "duml.py"
    spec = importlib.util.spec_from_file_location("rid_switch_duml", path)
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


class FCSession:
    """One USB DUML session with fixed routing and strict reply validation."""

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
        wire_mode: str,
        reply_seconds: float,
    ):
        self.handle = handle
        self.duml = duml
        self.protocol = protocol_module
        self.source = source
        self.target = target
        self.endpoint_out = endpoint_out
        self.endpoint_in = endpoint_in
        self.wire_mode = wire_mode
        self.reply_seconds = reply_seconds
        self.pending = bytearray()
        self.sequence = int(time.monotonic() * 1000) & 0xFFFF
        self.rejected_frames = 0

    def exchange(self, command_id: int, payload: bytes) -> bytes:
        if command_id not in (self.protocol.READ_ONLY_COMMANDS | self.protocol.WRITE_COMMANDS):
            raise AssertionError("refusing an unlisted FLYC command")
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
        if self.wire_mode == "simple":
            packet = self.protocol.encrypt_request_frame(
                packet,
                duml=self.duml,
                allowed_commands=(
                    self.protocol.READ_ONLY_COMMANDS
                    if command_id in self.protocol.READ_ONLY_COMMANDS
                    else self.protocol.WRITE_COMMANDS
                ),
            )
        elif self.wire_mode != "plaintext":
            raise AssertionError("unsupported wire mode")

        written = self.handle.bulkWrite(self.endpoint_out, packet, timeout=1000)
        if written != len(packet):
            raise RuntimeError("short USB write")

        deadline = time.monotonic() + self.reply_seconds
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
                try:
                    return self.protocol.validate_response_frame(
                        frame,
                        duml=self.duml,
                        expected_sender=self.target,
                        expected_receiver=self.source,
                        expected_sequence=self.sequence,
                        expected_command_id=command_id,
                    )
                except self.protocol.ParamProtocolError:
                    self.rejected_frames += 1
        if self.rejected_frames:
            raise RuntimeError(
                f"no valid response; rejected {self.rejected_frames} matching frame(s)"
            )
        raise TimeoutError("no matching response")


def probe_parameter(session: FCSession, *, name: str, hash_value: int, kind: str):
    """Return (metadata, value, f7_payload, f8_payload) for one parameter."""
    protocol_module = session.protocol
    f7_payload = session.exchange(
        protocol_module.CMD_GET_PARAM_INFO_BY_HASH, hash_value.to_bytes(4, "little")
    )
    metadata = protocol_module.parse_f7_metadata(
        f7_payload, expected_name=name, semantic_kind=kind
    )
    f8_payload = session.exchange(
        protocol_module.CMD_GET_PARAM_VALUE_BY_HASH, hash_value.to_bytes(4, "little")
    )
    value = protocol_module.parse_f8_value(
        f8_payload, expected_hash=hash_value, metadata=metadata, semantic_kind=kind
    )
    return metadata, value, f7_payload, f8_payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bounded USB DUML switch for rid_ctrl_enable_0."
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
        "--wire-mode",
        choices=("plaintext", "simple"),
        default="simple",
        help="DUML payload protection for the fixed F7/F8/F9 (default: simple)",
    )
    parser.add_argument(
        "--target",
        choices=("on", "off"),
        help="Forward write target; without it the tool only probes and reports the baseline",
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

    protocol_module = load_protocol_module()
    duml = load_duml_module()
    config = transport_config(args.transport)
    if args.route == "modern":
        if args.transport != "aircraft":
            raise SystemExit("--route modern is only defined for the aircraft transport")
        route_source = MODERN_SOURCE_APP4
        route_target = MODERN_TARGET_FC4
    else:
        route_source = config["source"]
        route_target = LEGACY_TARGET_FC

    context = usb1.USBContext()
    device = context.getByVendorIDAndProductID(VID, config["pid"])
    if device is None:
        context.close()
        raise SystemExit(f"DJI {args.transport} USB device not found")

    handle = device.open()
    handle.claimInterface(config["interface"])
    session = FCSession(
        handle=handle,
        duml=duml,
        protocol_module=protocol_module,
        source=route_source,
        target=route_target,
        endpoint_out=config["endpoint_out"],
        endpoint_in=config["endpoint_in"],
        wire_mode=args.wire_mode,
        reply_seconds=args.reply_seconds,
    )

    report = {
        "transport": args.transport,
        "route": args.route,
        "source": f"0x{route_source:02X}",
        "target": f"0x{route_target:02X}",
        "wire_mode": args.wire_mode,
        "target": args.target,
        "parameter": RID_PARAM_NAME,
        "hash": f"0x{RID_PARAM_HASH:08X}",
        "state": "unavailable",
        "steps": [],
    }

    baseline: bool | None = None
    original_raw: bytes | None = None
    metadata = None

    def record(step: str, outcome: str, detail: dict[str, object]) -> None:
        report["steps"].append({"step": step, "outcome": outcome, **detail})

    try:
        # Positive control: a known-good parameter must round-trip first.
        try:
            _, _, pc_f7, pc_f8 = probe_parameter(
                session,
                name=POSITIVE_CONTROL_NAME,
                hash_value=POSITIVE_CONTROL_HASH,
                kind=POSITIVE_CONTROL_KIND,
            )
            record("positive_control", "pass", {
                "parameter": POSITIVE_CONTROL_NAME,
                "f7_length": len(pc_f7),
                "f8_length": len(pc_f8),
            })
        except (TimeoutError, RuntimeError, protocol_module.ParamProtocolError, usb1.USBError) as exc:
            record("positive_control", "fail", {"reason": f"{type(exc).__name__}: {exc}"})
            report["state"] = "route_not_verified"
            raise RuntimeError("positive control failed; refusing to touch the RID parameter") from exc

        # Baseline: F7 metadata then F8 value for the RID parameter.
        try:
            metadata, value, f7_payload, f8_payload = probe_parameter(
                session,
                name=RID_PARAM_NAME,
                hash_value=RID_PARAM_HASH,
                kind=RID_SEMANTIC_KIND,
            )
            baseline = bool(value.decoded)
            original_raw = bytes(value.raw)
            record("baseline", "read", {
                "value": value.decoded,
                "layout": value.layout,
                "raw_hex": value.raw.hex(),
                "metadata": protocol_module.metadata_summary(metadata),
            })
        except (TimeoutError, RuntimeError, protocol_module.ParamProtocolError, usb1.USBError) as exc:
            record("baseline", "fail", {"reason": f"{type(exc).__name__}: {exc}"})
            report["state"] = "baseline_unavailable"
            raise RuntimeError("no same-session baseline; no write was attempted") from exc

        report["state"] = "baseline"
        if args.target is None:
            report["state"] = "probe_only"
            return

        target_value = args.target == "on"
        if baseline == target_value:
            record("forward_write", "no_op", {"reason": "baseline already equals target"})
            report["state"] = "already_target"
            return

        # Forward write with the same wire protection as reads. The encoded
        # Boolean target keeps the baseline value width and fills the whole raw
        # value with 0 or 1, matching the strict Boolean decoder.
        target_raw = build_target_raw(original_raw, target_value)
        write_payload = protocol_module.build_write_request_body(
            target_raw, parameter_hash=RID_PARAM_HASH
        )
        try:
            ack_payload = session.exchange(protocol_module.CMD_WRITE_PARAM_BY_HASH, write_payload)
            status = protocol_module.parse_f9_write_ack(ack_payload)
            record("forward_write", "ack", {"status": status, "payload_length": len(ack_payload)})
        except (TimeoutError, RuntimeError, protocol_module.ParamProtocolError, usb1.USBError) as exc:
            record("forward_write", "fail", {"reason": f"{type(exc).__name__}: {exc}"})
            report["state"] = "write_failed_restoring"
            raise

        # Readback of the forward value.
        forward_ok = False
        try:
            _, fwd_value, _, _ = probe_parameter(
                session,
                name=RID_PARAM_NAME,
                hash_value=RID_PARAM_HASH,
                kind=RID_SEMANTIC_KIND,
            )
            forward_ok = bool(fwd_value.decoded) == target_value
            record("forward_readback", "match" if forward_ok else "mismatch", {
                "value": fwd_value.decoded,
                "raw_hex": fwd_value.raw.hex(),
            })
        except (TimeoutError, RuntimeError, protocol_module.ParamProtocolError, usb1.USBError) as exc:
            record("forward_readback", "fail", {"reason": f"{type(exc).__name__}: {exc}"})

        # Always restore the baseline.
        restore_payload = protocol_module.build_write_request_body(
            original_raw, parameter_hash=RID_PARAM_HASH
        )
        restore_ok = False
        try:
            restore_ack = session.exchange(protocol_module.CMD_WRITE_PARAM_BY_HASH, restore_payload)
            protocol_module.parse_f9_write_ack(restore_ack)
            record("restore_write", "ack", {"payload_length": len(restore_ack)})
            _, restore_value, _, _ = probe_parameter(
                session,
                name=RID_PARAM_NAME,
                hash_value=RID_PARAM_HASH,
                kind=RID_SEMANTIC_KIND,
            )
            restore_ok = bool(restore_value.decoded) == baseline
            record("restore_readback", "match" if restore_ok else "mismatch", {
                "value": restore_value.decoded,
                "raw_hex": restore_value.raw.hex(),
            })
        except (TimeoutError, RuntimeError, protocol_module.ParamProtocolError, usb1.USBError) as exc:
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
