"""Bounded USB DUML by-hash A-B-A for one EU C0 RID candidate parameter.

This tool addresses only the flight-controller parameter
``EU_CE_enable_c0_rid_0`` (hash ``0xF80992FE``) over verified USB DUML paths.
It never sends a write unless a same-session F7/F8 baseline exists, and it
attempts to restore that baseline immediately after any possible forward write. It has no
generic payload, route, command, or parameter interface.

Commands reachable here are FLYC 0x03/0xF7 (metadata), 0x03/0xF8 (value), and
0x03/0xF9 (write). F7/F8/F9 payloads and replies are SIMPLE-keystream protected;
plaintext wire mode is also supported for the read probes. The tool starts
motors for nothing and measures no radio state. An optional
``--rid-ctrl-bridge`` read-only step probes the other by-hash RID candidate
``rid_ctrl_enable_0`` in the same session to anchor the two hash identifiers,
without writing either parameter.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import json
from pathlib import Path
import time

import usb1

from switch_safety import close_usb, run_transition, validate_boolean_write_range


VID = 0x2CA3
LEGACY_TARGET_FC = 0x03
MODERN_SOURCE_APP4 = 0x82
MODERN_TARGET_FC4 = 0x92
CMD_TYPE_REQUEST_ACK = 0x40

# The single subject of this tool. A positive control is required first.
RID_PARAM_NAME = "EU_CE_enable_c0_rid_0"
RID_PARAM_HASH = 0xF80992FE
RID_SEMANTIC_KIND = "bool"

POSITIVE_CONTROL_NAME = "g_config.flying_limit.max_height_0"
POSITIVE_CONTROL_HASH = 0x0371238A
POSITIVE_CONTROL_KIND = "int"

# The other by-hash RID candidate recovered from the same wa150 context. Its
# hash is pinned by the independent helper
# ``libraries/protocol-probes/dji_flyc_parameter_hash.py``. This optional
# read-only bridge lets one session anchor the EU C0 ``_0`` name to the older
# by-hash ``rid_ctrl_enable_0`` identifier without writing either parameter.
RID_CTRL_BRIDGE_NAME = "rid_ctrl_enable_0"
RID_CTRL_BRIDGE_HASH = 0x3CBD864F
RID_CTRL_BRIDGE_KIND = "bool"


def build_target_raw(baseline_raw: bytes, target: bool) -> bytes:
    """Only one-byte 0/1 baselines have an admitted local write encoding."""
    if baseline_raw not in (b"\x00", b"\x01") or type(target) is not bool:
        raise ValueError("write encoding requires one-byte Boolean baseline and target")
    return bytes((int(target),))


def load_protocol_module():
    path = Path(__file__).resolve().parent.parent / "device-read-probes" / "rid_param_protocol.py"
    spec = importlib.util.spec_from_file_location("rid_switch_protocol", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load rid_param_protocol from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module.__name__] = module
    spec.loader.exec_module(module)
    return module


def load_duml_module():
    path = Path(__file__).resolve().parent.parent / "device-read-probes" / "third-party" / "duml.py"
    spec = importlib.util.spec_from_file_location("rid_switch_duml", path)
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
    spec = importlib.util.spec_from_file_location("rid_switch_hash", path)
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Bounded USB DUML by-hash switch for EU_CE_enable_c0_rid_0."
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
        "--rid-ctrl-bridge",
        action="store_true",
        help="before the RID baseline, read-only F7/F8 probe the by-hash "
        "rid_ctrl_enable_0 candidate in the same session (default: off)",
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
    args = parser.parse_args(argv)
    if not 0.25 <= args.reply_seconds <= 5.0:
        raise SystemExit("--reply-seconds must be between 0.25 and 5.0")

    protocol_module = load_protocol_module()
    duml = load_duml_module()
    hash_module = load_hash_module()
    if hash_module.dji_flyc_parameter_hash(POSITIVE_CONTROL_NAME) != POSITIVE_CONTROL_HASH:
        raise SystemExit("positive-control name/hash mismatch; refusing to run")
    if hash_module.dji_flyc_parameter_hash(RID_CTRL_BRIDGE_NAME) != RID_CTRL_BRIDGE_HASH:
        raise SystemExit("rid-ctrl-bridge name/hash mismatch; refusing to run")
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

    report = {
        "transport": args.transport,
        "route": args.route,
        "source": f"0x{route_source:02X}",
        "route_target": f"0x{route_target:02X}",
        "wire_mode": args.wire_mode,
        "requested_target": args.target,
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

    def run():
        nonlocal context, handle, claimed
        context = usb1.USBContext()
        device = context.getByVendorIDAndProductID(VID, config["pid"])
        if device is None:
            raise RuntimeError("USB device not found")

        handle = device.open()
        handle.claimInterface(config["interface"])
        claimed = True
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

        # Optional read-only bridge: the other by-hash RID candidate.
        bridge_verified = True
        if args.rid_ctrl_bridge:
            try:
                _, _, bridge_f7, bridge_f8 = probe_parameter(
                    session,
                    name=RID_CTRL_BRIDGE_NAME,
                    hash_value=RID_CTRL_BRIDGE_HASH,
                    kind=RID_CTRL_BRIDGE_KIND,
                )
                record("rid_ctrl_bridge", "pass", {
                    "parameter": RID_CTRL_BRIDGE_NAME,
                    "hash": f"0x{RID_CTRL_BRIDGE_HASH:08X}",
                    "f7_length": len(bridge_f7),
                    "f8_length": len(bridge_f8),
                })
            except (TimeoutError, RuntimeError, protocol_module.ParamProtocolError, usb1.USBError) as exc:
                record("rid_ctrl_bridge", "fail", {"reason": f"{type(exc).__name__}: {exc}"})
                bridge_verified = False

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

        if not bridge_verified:
            report["state"] = "partial_bridge_unverified"
            return 1
        report["state"] = "baseline"
        if args.target is None:
            report["state"] = "probe_only"
            return 0

        report["state"] = "write_encoding_not_admitted"
        validate_boolean_write_range(
            type_id=metadata.data_type, size=metadata.size,
            minimum_raw=metadata.minimum_raw, maximum_raw=metadata.maximum_raw,
        )
        target_value = args.target == "on"
        if baseline == target_value:
            record("forward_write", "no_op", {"reason": "baseline already equals target"})
            report["state"] = "already_target"
            return 0

        # Both metadata bounds and encodings pass before any possible mutation.
        target_raw = build_target_raw(original_raw, target_value)
        protocol_module.build_write_request_body(original_raw, parameter_hash=RID_PARAM_HASH)
        protocol_module.build_write_request_body(target_raw, parameter_hash=RID_PARAM_HASH)

        def write(raw):
            payload = protocol_module.build_write_request_body(raw, parameter_hash=RID_PARAM_HASH)
            ack = session.exchange(protocol_module.CMD_WRITE_PARAM_BY_HASH, payload)
            protocol_module.parse_f9_write_ack(ack)

        def read():
            observed_metadata, observed, _, _ = probe_parameter(
                session, name=RID_PARAM_NAME, hash_value=RID_PARAM_HASH, kind=RID_SEMANTIC_KIND
            )
            if observed_metadata != metadata:
                raise RuntimeError("parameter metadata changed during transition")
            return bytes(observed.raw)

        return 0 if run_transition(
            report=report, record=record, write=write, read=read,
            target_raw=target_raw, baseline_raw=original_raw,
        ) else 1
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
