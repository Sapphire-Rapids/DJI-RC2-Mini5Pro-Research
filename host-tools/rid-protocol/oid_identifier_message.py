"""Encode only the product-139 China UOM tag payload (RID-005B / C-123).

Command 0x11/0xD6 uses 18 bytes: [01][03 if empty else 01][16-byte field].
At most eight input bytes are copied. GET [01,02] gets a deterministically
zeroed tail here; the vendor's uninitialized GET tail is not reproduced.
No SDK object header, routing, transport or device control is provided.
"""
import argparse

CMD = 0xD6
SUB = 0x11
PACK_LEN = 18
MAX_INPUT = 8


def build(text: bytes) -> bytes:
    return bytes([1, 3 if not text else 1]) + text[:MAX_INPUT].ljust(16, b"\0")


def build_get() -> bytes:
    return b"\x01\x02" + bytes(16)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--text", help="tag bytes encoded as UTF-8; first eight bytes copied")
    action.add_argument("--get", action="store_true")
    args = parser.parse_args()
    print((build_get() if args.get else build(args.text.encode())).hex())


if __name__ == "__main__":
    main()
