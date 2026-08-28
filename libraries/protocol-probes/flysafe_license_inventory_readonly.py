#!/usr/bin/env python3
"""Read a bounded DJI FlySafe license inventory using only 0x11/0x11.

The direct-aircraft and RC 2 transports both target the flight controller.
There is no generic command option: every USB OUT transfer is built by the
fixed one-byte inventory request constructor.  Output is limited to counts,
type, level, enabled, and validity summaries.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import time

import flysafe_license_protocol as protocol


DJI_VENDOR_ID = 0x2CA3


@dataclass(frozen=True)
class Transport:
    name: str
    product_id: int
    interface: int
    endpoint_out: int
    endpoint_in: int
    source: int


TRANSPORTS = {
    "aircraft": Transport(
        name="aircraft",
        product_id=0x0020,
        interface=4,
        endpoint_out=0x04,
        endpoint_in=0x85,
        source=protocol.SOURCE_DIRECT_AIRCRAFT,
    ),
    "rc2": Transport(
        name="rc2",
        product_id=0x1021,
        interface=0,
        endpoint_out=0x01,
        endpoint_in=0x81,
        source=protocol.SOURCE_RC2_PROXY,
    ),
}


def _exchange_license_record(
    *,
    handle,
    usb1_module,
    transport: Transport,
    pending: bytearray,
    request_id: int,
    sequence: int,
    reply_seconds: float,
) -> protocol.LicenseResponse:
    request = protocol.build_license_request_frame(
        source=transport.source,
        request_id=request_id,
        sequence=sequence,
    )
    written = handle.bulkWrite(transport.endpoint_out, request, timeout=1000)
    if written != len(request):
        raise RuntimeError("short USB write for the fixed inventory request")

    deadline = time.monotonic() + reply_seconds
    rejected_matching_sequence = 0
    while time.monotonic() < deadline:
        try:
            chunk = bytes(
                handle.bulkRead(transport.endpoint_in, 16 * 1024, timeout=250)
            )
        except usb1_module.USBErrorTimeout:
            continue
        pending.extend(chunk)
        for frame in protocol.extract_valid_duml_frames(pending):
            if int.from_bytes(frame[6:8], "little") != sequence:
                continue
            try:
                return protocol.parse_license_response_frame(
                    frame,
                    expected_source=transport.source,
                    expected_sequence=sequence,
                )
            except protocol.LicenseProtocolError:
                rejected_matching_sequence += 1

    if rejected_matching_sequence:
        raise RuntimeError(
            "no valid fixed-command response; rejected "
            f"{rejected_matching_sequence} matching-sequence frame(s)"
        )
    raise TimeoutError("no fixed-command inventory response")


def run_inventory(
    *, transport: Transport, reply_seconds: float
) -> protocol.LicenseInventory:
    try:
        import usb1
    except ImportError as exc:
        raise RuntimeError(f"python usb1 module unavailable: {exc}") from exc

    context = usb1.USBContext()
    handle = None
    claimed = False
    try:
        device = context.getByVendorIDAndProductID(
            DJI_VENDOR_ID, transport.product_id
        )
        if device is None:
            raise RuntimeError(f"DJI {transport.name} USB device not found")
        handle = device.open()
        handle.claimInterface(transport.interface)
        claimed = True
        pending = bytearray()
        sequence = int(time.monotonic() * 1000) & 0xFFFF

        def fetch(request_id: int) -> protocol.LicenseResponse:
            nonlocal sequence
            sequence = (sequence + 1) & 0xFFFF
            return _exchange_license_record(
                handle=handle,
                usb1_module=usb1,
                transport=transport,
                pending=pending,
                request_id=request_id,
                sequence=sequence,
                reply_seconds=reply_seconds,
            )

        return protocol.collect_inventory(fetch)
    finally:
        if claimed and handle is not None:
            try:
                handle.releaseInterface(transport.interface)
            except Exception:
                pass
        if handle is not None:
            try:
                handle.close()
            except Exception:
                pass
        context.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Strict, bounded read of DJI FlySafe license summary state using "
            "only ADS-B/whitelist 0x11/0x11"
        )
    )
    parser.add_argument(
        "--transport", choices=tuple(TRANSPORTS), required=True
    )
    parser.add_argument(
        "--reply-seconds",
        type=float,
        default=1.5,
        help="per-record response timeout between 0.25 and 5 seconds",
    )
    args = parser.parse_args()
    if not 0.25 <= args.reply_seconds <= 5.0:
        parser.error("--reply-seconds must be between 0.25 and 5.0")

    try:
        inventory = run_inventory(
            transport=TRANSPORTS[args.transport],
            reply_seconds=args.reply_seconds,
        )
    except Exception as exc:
        raise SystemExit(f"inventory unavailable: {type(exc).__name__}: {exc}")
    print(
        json.dumps(
            protocol.deidentified_inventory_summary(inventory),
            separators=(",", ":"),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
