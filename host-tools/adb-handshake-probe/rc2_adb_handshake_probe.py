#!/usr/bin/env python3
"""Read-only DJI RC2 ADB transport/authentication handshake probe.

This deliberately stops before A_OPEN.  It reproduces Dr-Muh/dji-adb's
first profile: ADB 1.0.0, MAXDATA=256 KiB, host::pydevice\0, and direct
AUTH_RSAPUBLICKEY after AUTH_TOKEN (no AUTH_SIGNATURE).
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
import time
from datetime import datetime

import usb1
from adb_shell.auth.sign_pythonrsa import PythonRSASigner


# RC331's normal DJI composite, Android's generic MTP+ADB composite, and the
# Qualcomm DIAG+ADB composite exposed by DJI's own Type-C page.  The interface
# and endpoint numbers are always discovered from descriptors.
USB_TARGETS = {
    (0x2CA3, 0x1021),
    (0x18D1, 0x4EE2),
    (0x05C6, 0x901D),
}
ADB_CLASS = 0xFF
ADB_SUBCLASS = 0x42
ADB_PROTOCOL = 0x01
TIMEOUT_MS = 15_000
VERSION = 0x01000000
MAXDATA = 256 * 1024
BANNER = b"host::pydevice\x00"
KEY_PATH = os.path.expanduser("~/.android/adbkey")


def command(value: bytes) -> int:
    return struct.unpack("<I", value)[0]


A_CNXN = command(b"CNXN")
A_AUTH = command(b"AUTH")
A_OPEN = command(b"OPEN")
A_OKAY = command(b"OKAY")
A_WRTE = command(b"WRTE")
A_CLSE = command(b"CLSE")
AUTH_TOKEN = 1
AUTH_SIGNATURE = 2
AUTH_RSAPUBLICKEY = 3

COMMAND_NAMES = {
    A_CNXN: "CNXN",
    A_AUTH: "AUTH",
    A_OPEN: "OPEN",
    A_OKAY: "OKAY",
    A_WRTE: "WRTE",
    A_CLSE: "CLSE",
}


def stamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def event(message: str) -> None:
    print(f"{stamp()} {message}", flush=True)


def escaped(data: bytes) -> str:
    return "".join(chr(value) if 0x20 <= value <= 0x7E else f"\\x{value:02x}" for value in data)


def checksum(data: bytes) -> int:
    return sum(data) & 0xFFFFFFFF


def packet_header(
    cmd: int,
    arg0: int,
    arg1: int,
    payload: bytes,
    checksum_mode: str = "sum",
) -> bytes:
    data_checksum = checksum(payload) if checksum_mode == "sum" else 0
    return struct.pack(
        "<6I",
        cmd,
        arg0,
        arg1,
        len(payload),
        data_checksum,
        cmd ^ 0xFFFFFFFF,
    )


def log_packet(direction: str, header: bytes, payload: bytes) -> tuple[int, int, int, int, int, int]:
    cmd, arg0, arg1, payload_length, data_checksum, magic = struct.unpack("<6I", header)
    name = COMMAND_NAMES.get(cmd, f"UNKNOWN(0x{cmd:08x})")
    event(
        f"ADB {direction} command={name} command_raw=0x{cmd:08x} "
        f"arg0=0x{arg0:08x} arg1=0x{arg1:08x} "
        f"payload_length={payload_length} checksum=0x{data_checksum:08x} magic=0x{magic:08x}"
    )
    event(f"ADB {direction} payload_hex={payload.hex()}")
    event(f"ADB {direction} payload_ascii={escaped(payload)}")
    return cmd, arg0, arg1, payload_length, data_checksum, magic


def usb_error_kind(exc: BaseException) -> str:
    if isinstance(exc, usb1.USBErrorTimeout):
        return "timeout"
    if isinstance(exc, usb1.USBErrorPipe):
        return "stall"
    if isinstance(exc, usb1.USBErrorNoDevice):
        return "device-removed-or-reset"
    if isinstance(exc, usb1.USBErrorIO):
        return "io-error-possibly-reset"
    return "other-usb-error"


def bulk_write(handle: usb1.USBDeviceHandle, endpoint: int, data: bytes, label: str) -> None:
    started = time.monotonic()
    event(f"USB WRITE begin label={label} endpoint=0x{endpoint:02x} requested={len(data)} timeout_ms={TIMEOUT_MS}")
    try:
        written = handle.bulkWrite(endpoint, data, timeout=TIMEOUT_MS)
    except usb1.USBError as exc:
        elapsed = (time.monotonic() - started) * 1000
        event(
            f"USB WRITE error label={label} kind={usb_error_kind(exc)} "
            f"exception={type(exc).__name__} value={getattr(exc, 'value', None)!r} "
            f"elapsed_ms={elapsed:.1f} detail={exc!r}"
        )
        raise
    elapsed = (time.monotonic() - started) * 1000
    event(f"USB WRITE end label={label} transferred={written} elapsed_ms={elapsed:.1f}")
    if written != len(data):
        raise RuntimeError(f"short USB write for {label}: {written}/{len(data)}")


def bulk_read(handle: usb1.USBDeviceHandle, endpoint: int, length: int, label: str) -> bytes:
    started = time.monotonic()
    event(f"USB READ begin label={label} endpoint=0x{endpoint:02x} requested={length} timeout_ms={TIMEOUT_MS}")
    try:
        data = bytes(handle.bulkRead(endpoint, length, timeout=TIMEOUT_MS))
    except usb1.USBError as exc:
        elapsed = (time.monotonic() - started) * 1000
        event(
            f"USB READ error label={label} kind={usb_error_kind(exc)} "
            f"exception={type(exc).__name__} value={getattr(exc, 'value', None)!r} "
            f"elapsed_ms={elapsed:.1f} detail={exc!r}"
        )
        raise
    elapsed = (time.monotonic() - started) * 1000
    event(f"USB READ end label={label} transferred={len(data)} elapsed_ms={elapsed:.1f}")
    if len(data) != length:
        event(f"USB READ short label={label} expected={length} actual={len(data)} bytes_hex={data.hex()}")
        raise RuntimeError(f"short USB read for {label}: {len(data)}/{length}")
    return data


def send_packet(
    handle: usb1.USBDeviceHandle,
    endpoint: int,
    cmd: int,
    arg0: int,
    arg1: int,
    payload: bytes,
    framing: str = "split",
    checksum_mode: str = "sum",
) -> None:
    # This probe is fail-closed: it can only transmit CNXN or direct public-key AUTH.
    allowed = cmd == A_CNXN or (cmd == A_AUTH and arg0 == AUTH_RSAPUBLICKEY and arg1 == 0)
    if not allowed:
        raise RuntimeError(f"transmit guard rejected command=0x{cmd:08x} arg0={arg0} arg1={arg1}")
    header = packet_header(cmd, arg0, arg1, payload, checksum_mode=checksum_mode)
    log_packet("TX", header, payload)
    if framing == "split":
        # Preserve Dr-Muh/dji-adb's two-transfer packet framing exactly.
        bulk_write(handle, endpoint, header, "adb-header")
        if payload:
            bulk_write(handle, endpoint, payload, "adb-payload")
    elif framing == "combined":
        bulk_write(handle, endpoint, header + payload, "adb-header-plus-payload")
    else:
        raise RuntimeError(f"unsupported USB framing: {framing}")


def receive_packet(
    handle: usb1.USBDeviceHandle,
    endpoint: int,
    maxdata: int = MAXDATA,
) -> tuple[int, int, int, bytes]:
    # Preserve the upstream single-read header and single-read payload behavior.
    header = bulk_read(handle, endpoint, 24, "adb-header")
    cmd, arg0, arg1, payload_length, data_checksum, magic = struct.unpack("<6I", header)
    if payload_length > maxdata:
        event(f"ADB RX validation_error=payload-too-large payload_length={payload_length} max={maxdata}")
        raise RuntimeError("incoming ADB payload exceeds negotiated MAXDATA")
    payload = bulk_read(handle, endpoint, payload_length, "adb-payload") if payload_length else b""
    log_packet("RX", header, payload)
    if magic != (cmd ^ 0xFFFFFFFF):
        raise RuntimeError(f"bad ADB magic: 0x{magic:08x}")
    actual_checksum = checksum(payload)
    if data_checksum != actual_checksum:
        raise RuntimeError(f"bad ADB checksum: header=0x{data_checksum:08x} actual=0x{actual_checksum:08x}")
    return cmd, arg0, arg1, payload


def find_adb_interface(context: usb1.USBContext):
    matches = []
    for device in context.getDeviceList(skip_on_error=True):
        vid = device.getVendorID()
        pid = device.getProductID()
        if (vid, pid) not in USB_TARGETS:
            continue
        event(
            f"USB DEVICE vid=0x{vid:04x} pid=0x{pid:04x} "
            f"bus={device.getBusNumber()} address={device.getDeviceAddress()}"
        )
        for configuration in device.iterConfigurations():
            for interface in configuration:
                for setting in interface:
                    endpoint_rows = []
                    bulk_in = []
                    bulk_out = []
                    for endpoint in setting:
                        address = endpoint.getAddress()
                        attributes = endpoint.getAttributes()
                        max_packet = endpoint.getMaxPacketSize()
                        endpoint_rows.append((address, attributes, max_packet))
                        if attributes & 0x03 == 0x02:
                            (bulk_in if address & 0x80 else bulk_out).append(address)
                    event(
                        f"USB DESCRIPTOR configuration={configuration.getConfigurationValue()} "
                        f"interface={setting.getNumber()} alt={setting.getAlternateSetting()} "
                        f"class=0x{setting.getClass():02x} subclass=0x{setting.getSubClass():02x} "
                        f"protocol=0x{setting.getProtocol():02x} endpoints="
                        + ",".join(
                            f"0x{address:02x}/attr=0x{attributes:02x}/maxpacket={max_packet}"
                            for address, attributes, max_packet in endpoint_rows
                        )
                    )
                    if (
                        setting.getClass() == ADB_CLASS
                        and setting.getSubClass() == ADB_SUBCLASS
                        and setting.getProtocol() == ADB_PROTOCOL
                        and len(bulk_in) == 1
                        and len(bulk_out) == 1
                    ):
                        matches.append((device, setting.getNumber(), bulk_out[0], bulk_in[0]))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one supported RC2 ADB interface, found {len(matches)}")
    return matches[0]


def wait_for_adb_interface(context: usb1.USBContext, wait_seconds: float):
    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            return find_adb_interface(context)
        except RuntimeError as exc:
            if time.monotonic() >= deadline:
                raise
            event(f"USB WAIT detail={exc} remaining_seconds={max(0.0, deadline - time.monotonic()):.1f}")
            time.sleep(0.25)


def load_public_key(nul_terminated: bool = True) -> bytes:
    if not os.path.isfile(KEY_PATH):
        raise RuntimeError(f"existing ADB private key required but absent: {KEY_PATH}")
    if not os.path.isfile(KEY_PATH + ".pub"):
        raise RuntimeError(f"existing ADB public key required but absent: {KEY_PATH}.pub")
    signer = PythonRSASigner.FromRSAKeyPath(KEY_PATH)
    public_key = signer.GetPublicKey()
    if isinstance(public_key, str):
        public_key = public_key.encode()
    if nul_terminated and not public_key.endswith(b"\x00"):
        public_key += b"\x00"
    if not nul_terminated:
        public_key = public_key.rstrip(b"\x00")
    # A public-key fingerprint is unnecessary for the packet-state experiment
    # and becomes a persistent host identifier if a log is later shared.
    event(
        f"AUTH PUBLIC_KEY source=existing-adbkey length={len(public_key)} "
        f"nul_terminated={public_key.endswith(bytes([0]))}"
    )
    return public_key


def parse_int(value: str) -> int:
    return int(value, 0)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="dr-muh-exact")
    parser.add_argument("--version", type=parse_int, default=VERSION)
    parser.add_argument("--maxdata", type=parse_int, default=MAXDATA)
    parser.add_argument("--banner-hex", default=BANNER.hex())
    parser.add_argument("--framing", choices=("split", "combined"), default="split")
    parser.add_argument("--checksum", choices=("sum", "zero"), default="sum")
    parser.add_argument("--public-key-nul", choices=("yes", "no"), default="yes")
    parser.add_argument(
        "--wait-seconds",
        type=float,
        default=0.0,
        help="wait for a supported RC2 USB composition before probing",
    )
    args = parser.parse_args()
    try:
        args.banner = bytes.fromhex(args.banner_hex)
    except ValueError as exc:
        parser.error(f"invalid --banner-hex: {exc}")
    if not 1 <= args.maxdata <= 4 * 1024 * 1024:
        parser.error("--maxdata must be between 1 and 4194304")
    if not 1 <= len(args.banner) <= 4096:
        parser.error("decoded banner must be between 1 and 4096 bytes")
    if not 0 <= args.wait_seconds <= 300:
        parser.error("--wait-seconds must be between 0 and 300")
    return args


def run() -> int:
    args = parse_args()
    event(
        f"PROBE START profile={args.label}-handshake-only version=0x{args.version:08x} "
        f"maxdata={args.maxdata} banner={escaped(args.banner)} framing={args.framing} "
        f"checksum={args.checksum} public_key_nul={args.public_key_nul} timeout_ms={TIMEOUT_MS} "
        f"usb_wait_seconds={args.wait_seconds}"
    )
    event("SAFETY no_OPEN=true no_shell=true no_SIGNATURE=true no_key_generation=true")
    public_key = load_public_key(nul_terminated=args.public_key_nul == "yes")
    context = usb1.USBContext()
    handle = None
    claimed_interface = None
    try:
        device, interface_number, endpoint_out, endpoint_in = wait_for_adb_interface(
            context, args.wait_seconds
        )
        event(
            f"USB SELECT interface={interface_number} endpoint_out=0x{endpoint_out:02x} "
            f"endpoint_in=0x{endpoint_in:02x}"
        )
        handle = device.open()
        try:
            handle.setAutoDetachKernelDriver(True)
            event("USB setAutoDetachKernelDriver result=ok")
        except Exception as exc:  # macOS commonly reports unsupported here.
            event(f"USB setAutoDetachKernelDriver result=warning exception={type(exc).__name__} detail={exc!r}")
        handle.claimInterface(interface_number)
        claimed_interface = interface_number
        event(f"USB claimInterface interface={interface_number} result=ok")
        for endpoint in (endpoint_out, endpoint_in):
            try:
                handle.clearHalt(endpoint)
                event(f"USB clearHalt endpoint=0x{endpoint:02x} result=ok")
            except usb1.USBError as exc:
                event(
                    f"USB clearHalt endpoint=0x{endpoint:02x} result=warning "
                    f"kind={usb_error_kind(exc)} exception={type(exc).__name__} detail={exc!r}"
                )

        send_packet(
            handle,
            endpoint_out,
            A_CNXN,
            args.version,
            args.maxdata,
            args.banner,
            framing=args.framing,
            checksum_mode=args.checksum,
        )
        cmd, arg0, arg1, payload = receive_packet(handle, endpoint_in, maxdata=args.maxdata)
        if cmd == A_CNXN:
            event(f"HANDSHAKE RESULT=success-without-auth peer_version=0x{arg0:08x} peer_maxdata={arg1}")
            return 0
        if cmd != A_AUTH or arg0 != AUTH_TOKEN:
            event(
                f"HANDSHAKE RESULT=unexpected-first-response command={COMMAND_NAMES.get(cmd, hex(cmd))} "
                f"arg0=0x{arg0:08x} arg1=0x{arg1:08x}"
            )
            return 4

        event(f"HANDSHAKE STATE=AUTH_TOKEN_RECEIVED token_length={len(payload)}")
        send_packet(
            handle,
            endpoint_out,
            A_AUTH,
            AUTH_RSAPUBLICKEY,
            0,
            public_key,
            framing=args.framing,
            checksum_mode=args.checksum,
        )
        cmd, arg0, arg1, payload = receive_packet(handle, endpoint_in, maxdata=args.maxdata)
        if cmd == A_CNXN:
            event(f"HANDSHAKE RESULT=success-direct-public-key peer_version=0x{arg0:08x} peer_maxdata={arg1}")
            return 0
        event(
            f"HANDSHAKE RESULT=public-key-rejected-or-more-auth command={COMMAND_NAMES.get(cmd, hex(cmd))} "
            f"arg0=0x{arg0:08x} arg1=0x{arg1:08x}"
        )
        return 5
    except usb1.USBError as exc:
        event(
            f"HANDSHAKE RESULT=usb-error kind={usb_error_kind(exc)} "
            f"exception={type(exc).__name__} value={getattr(exc, 'value', None)!r} detail={exc!r}"
        )
        return 6
    except Exception as exc:
        event(f"HANDSHAKE RESULT=host-error exception={type(exc).__name__} detail={exc!r}")
        return 7
    finally:
        if handle is not None and claimed_interface is not None:
            try:
                handle.releaseInterface(claimed_interface)
                event(f"USB releaseInterface interface={claimed_interface} result=ok")
            except Exception as exc:
                event(f"USB releaseInterface result=warning exception={type(exc).__name__} detail={exc!r}")
        if handle is not None:
            try:
                handle.close()
                event("USB handle close result=ok")
            except Exception as exc:
                event(f"USB handle close result=warning exception={type(exc).__name__} detail={exc!r}")
        try:
            context.close()
            event("USB context close result=ok")
        except Exception as exc:
            event(f"USB context close result=warning exception={type(exc).__name__} detail={exc!r}")
        event("PROBE END")


if __name__ == "__main__":
    sys.exit(run())
