"""Encode only the France EID payload from RID-003 / C-010.

Command 0x03/0x77: GET [02], SET off/on [00]/[01]. This is not a global
Remote ID switch. Routing, transport, device acceptance and RF are unverified.
An SDK request object is not a wire header and is not included in this output.
"""
import argparse

CMD = 0x77
SUB = 0x03


def build(value: int = 0) -> bytes:
    if value not in (0, 1):
        raise ValueError("France EID value must be 0 or 1")
    return bytes([value])


def build_get() -> bytes:
    return b"\x02"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--value", type=int, choices=(0, 1), help="France EID: 0 off, 1 on")
    action.add_argument("--get", action="store_true")
    args = parser.parse_args()
    print((build_get() if args.get else build(args.value)).hex())


if __name__ == "__main__":
    main()
