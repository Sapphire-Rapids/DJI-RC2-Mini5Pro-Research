"""Encode the one-byte AirSense/ADS-B agent switch payload (C-135/C-435).

Command 0x11/0x37 is an ADS-B receive/configuration surface, not a Remote ID
broadcast switch. No SDK object header, routing or transport is included.
"""
import argparse

CMD = 0x37
SUB = 0x11


def build(value: int = 0) -> bytes:
    return bytes([1 if value else 0])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--value", type=int, required=True, help="AirSense: 0 off, nonzero on")
    args = parser.parse_args()
    print(build(args.value).hex())


if __name__ == "__main__":
    main()
