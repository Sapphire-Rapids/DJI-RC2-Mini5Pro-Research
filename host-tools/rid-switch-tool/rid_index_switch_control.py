"""Bounded USB DUML by-index A-B-A for one EU C0 RID candidate parameter.

This tool addresses only the wa150 table parameter ``EU_CE_enable_c0_rid``
(index 1306, U8 0..1) over verified USB DUML paths. It never sends a write
unless the table identity (0xE0), the on-board name (0xE1), and the current
value (0xE2) all pass in the same session, and it attempts to restore the captured
baseline immediately after any possible forward write. It has no generic payload, route,
command, or parameter interface.

Commands reachable: FLYC 0x03/0xE0 (table), 0x03/0xE1 (get_info), 0x03/0xE2
(read), 0x03/0xE3 (write). No motor is started and no radio state is measured.

An optional ``--hash-bridge`` read-only step maps the same parameter to its
by-hash name ``EU_CE_enable_c0_rid_0`` (hash ``0xF80992FE``) with an F7/F8
probe, anchoring the by-index row and the by-hash identifier to each other
without writing.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import json
from pathlib import Path
import time

import usb1

from index_protocol_guard import (
    WA150_TABLE_CRC, WA150_TABLE_COUNT, validate_response, verify_table_identity,
)
from switch_safety import close_usb, run_transition, validate_boolean_write_range


VID = 0x2CA3
LEGACY_TARGET_FC = 0x03
CMD_TYPE_REQUEST_ACK = 0x40

# The single subject of this tool.
RID_INDEX = 1306
RID_NAME = "EU_CE_enable_c0_rid"

# wa150 (Mini 5 Pro) table identity published by lmdegreeds/djiparam. The probe
# re-verifies the live CRC/count through 0xE0 before any write.

# The by-hash name for the same wa150 row. Its hash is pinned by the independent
# helper libraries/protocol-probes/dji_flyc_parameter_hash.py.
HASH_BRIDGE_NAME = "EU_CE_enable_c0_rid_0"
HASH_BRIDGE_HASH = 0xF80992FE
HASH_BRIDGE_KIND = "bool"


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
    spec = importlib.util.spec_from_file_location("rid_index_switch_duml", path)
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
    spec = importlib.util.spec_from_file_location("rid_index_switch_hash", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load hash module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module.__name__] = module
    spec.loader.exec_module(module)
    return module


def load_hash_protocol_module():
    path = (
        Path(__file__).resolve().parent.parent
        / "device-read-probes"
        / "rid_param_protocol.py"
    )
    spec = importlib.util.spec_from_file_location("rid_index_switch_hash_protocol", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load by-hash protocol from {path}")
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
        hash_protocol=None,
    ):
        self.handle = handle
        self.duml = duml
        self.protocol = protocol_module
        self.source = source
        self.target = target
        self.endpoint_out = endpoint_out
        self.endpoint_in = endpoint_in
        self.reply_seconds = reply_seconds
        self.hash_protocol = hash_protocol
        self.pending = bytearray()
        self.sequence = int(time.monotonic() * 1000) & 0xFFFF

    def exchange(self, command_id: int, payload: bytes) -> bytes:
        hash_read = command_id in (0xF7, 0xF8)
        if hash_read:
            if payload != HASH_BRIDGE_HASH.to_bytes(4, "little"):
                raise AssertionError("refusing an unlisted hash bridge parameter")
            if self.hash_protocol is None:
                raise AssertionError("hash bridge codec is unavailable")
        elif command_id not in (
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
        if hash_read:
            packet = self.hash_protocol.encrypt_read_request_frame(packet, duml=self.duml)
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
                try:
                    if hash_read:
                        return self.hash_protocol.validate_response_frame(
                            frame, duml=self.duml, expected_sender=self.target,
                            expected_receiver=self.source, expected_sequence=self.sequence,
                            expected_command_id=command_id,
                        )
                    return validate_response(
                        frame, duml=self.duml, sender=self.target, receiver=self.source,
                        sequence=self.sequence, command=command_id,
                    )
                except (ValueError, RuntimeError):
                    rejected += 1
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
    verify_table_identity(attrs)

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
    if info.size != 1 or info.type_id not in (0, 4, 11) or value.raw not in (b"\x00", b"\x01"):
        raise protocol.ParamIndexError("RID baseline is not a one-byte Boolean")
    return attrs, info, value


def probe_hash_bridge(session: IndexSession, hash_protocol):
    """Read-only F7/F8 of the by-hash name for the same wa150 row."""

    payload = HASH_BRIDGE_HASH.to_bytes(4, "little")
    f7_payload = session.exchange(hash_protocol.CMD_GET_PARAM_INFO_BY_HASH, payload)
    metadata = hash_protocol.parse_f7_metadata(
        f7_payload,
        expected_name=HASH_BRIDGE_NAME,
        semantic_kind=HASH_BRIDGE_KIND,
    )
    f8_payload = session.exchange(
        hash_protocol.CMD_GET_PARAM_VALUE_BY_HASH, payload
    )
    value = hash_protocol.parse_f8_value(
        f8_payload,
        expected_hash=HASH_BRIDGE_HASH,
        metadata=metadata,
        semantic_kind=HASH_BRIDGE_KIND,
    )
    return metadata, value, f7_payload, f8_payload


def main(argv=None) -> int:
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
    parser.add_argument(
        "--hash-bridge",
        action="store_true",
        help="after the by-index baseline, read-only F7/F8 probe the same row via "
        "its _0 by-hash name EU_CE_enable_c0_rid_0 (default: off)",
    )
    args = parser.parse_args(argv)
    if not 0.25 <= args.reply_seconds <= 5.0:
        raise SystemExit("--reply-seconds must be between 0.25 and 5.0")

    protocol = load_protocol_module()
    duml = load_duml_module()
    hash_module = load_hash_module()
    hash_protocol = load_hash_protocol_module()
    if hash_module.dji_flyc_parameter_hash(HASH_BRIDGE_NAME) != HASH_BRIDGE_HASH:
        raise SystemExit("hash bridge name/hash mismatch; refusing to run")
    config = transport_config(args.transport)

    context = None
    handle = None
    claimed = False

    report: dict[str, object] = {
        "transport": args.transport,
        "parameter": RID_NAME,
        "index": RID_INDEX,
        "requested_target": args.target,
        "state": "unavailable",
        "steps": [],
    }

    def record(step: str, outcome: str, detail: dict[str, object]) -> None:
        report["steps"].append({"step": step, "outcome": outcome, **detail})

    baseline: bool | None = None
    info = None

    def run():
        nonlocal context, handle, claimed
        context = usb1.USBContext()
        device = context.getByVendorIDAndProductID(VID, config["pid"])
        if device is None:
            raise RuntimeError("USB device not found")

        handle = device.open()
        handle.claimInterface(config["interface"])
        claimed = True
        session = IndexSession(
            handle=handle,
            duml=duml,
            protocol_module=protocol,
            source=config["source"],
            target=LEGACY_TARGET_FC,
            endpoint_out=config["endpoint_out"],
            endpoint_in=config["endpoint_in"],
            reply_seconds=args.reply_seconds,
            hash_protocol=hash_protocol,
        )

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
            baseline_raw = bytes(value.raw)
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

        bridge_verified = True
        if args.hash_bridge:
            try:
                bridge_metadata, bridge_value, bridge_f7, bridge_f8 = probe_hash_bridge(
                    session, hash_protocol
                )
                if bridge_value.decoded != baseline:
                    raise RuntimeError("hash bridge disagrees with the by-index baseline")
                record("hash_bridge", "pass", {
                    "parameter": HASH_BRIDGE_NAME,
                    "hash": f"0x{HASH_BRIDGE_HASH:08X}",
                    "value": bridge_value.decoded,
                    "raw_hex": bridge_value.raw.hex(),
                    "metadata": hash_protocol.metadata_summary(bridge_metadata),
                    "f7_length": len(bridge_f7),
                    "f8_length": len(bridge_f8),
                })
            except (
                TimeoutError,
                RuntimeError,
                hash_protocol.ParamProtocolError,
                usb1.USBError,
            ) as exc:
                record("hash_bridge", "fail", {"reason": f"{type(exc).__name__}: {exc}"})
                bridge_verified = False

        if not bridge_verified:
            report["state"] = "partial_bridge_unverified"
            return 1
        report["state"] = "baseline"
        if args.target is None:
            report["state"] = "probe_only"
            return 0

        report["state"] = "write_encoding_not_admitted"
        validate_boolean_write_range(
            type_id=info.type_id, size=info.size,
            minimum_raw=info.minimum_raw, maximum_raw=info.maximum_raw,
        )
        target_value = args.target == "on"
        if baseline == target_value:
            record("forward_write", "no_op", {"reason": "baseline already equals target"})
            report["state"] = "already_target"
            return 0

        target_raw = bytes((int(target_value),))
        # Both encodings are validated before any possible mutation.
        protocol.build_write_value_request(0, RID_INDEX, target_raw, info=info)
        protocol.build_write_value_request(0, RID_INDEX, baseline_raw, info=info)

        def write(raw):
            payload = protocol.build_write_value_request(0, RID_INDEX, raw, info=info)
            ack = session.exchange(protocol.CMD_WRITE_VALUE, payload)
            protocol.parse_write_status(ack)

        def read():
            _, observed_info, observed = probe_value(session)
            if observed_info != info:
                raise RuntimeError("parameter metadata changed during transition")
            return bytes(observed.raw)

        return 0 if run_transition(
            report=report, record=record, write=write, read=read,
            target_raw=target_raw, baseline_raw=baseline_raw,
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
