"""Encode only the EASA OPID action payload (RID-005 / C-124).

Command 0x03/0x78: GET [02], DELETE [01], SET [00,10]+16 wire bytes.
SET input is the already validated 16-byte wire field, not the SDK's full
20-character registration input. This codec does not validate its country or
checksum, generate a transport header, select a receiver or access a device.
Operator ID is separate from Basic/UAS ID and operator position.
"""
import argparse
from pathlib import Path

CMD = 0x78
SUB = 0x03
MAX_LEN = 16


def build(payload: bytes) -> bytes:
    if not payload:
        return b"\x01"
    if len(payload) != MAX_LEN:
        raise ValueError("OPID wire field must be exactly 16 bytes, or empty for DELETE")
    return b"\x00\x10" + payload


def build_get() -> bytes:
    return b"\x02"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--payload-file", type=Path, help="validated 16-byte wire field")
    action.add_argument("--delete", action="store_true")
    action.add_argument("--get", action="store_true")
    args = parser.parse_args()
    if args.get:
        payload = build_get()
    elif args.delete:
        payload = build(b"")
    else:
        data = args.payload_file.read_bytes()
        if len(data) != MAX_LEN:
            raise ValueError("SET payload file must contain exactly 16 bytes")
        payload = build(data)
    print(payload.hex())


if __name__ == "__main__":
    main()
