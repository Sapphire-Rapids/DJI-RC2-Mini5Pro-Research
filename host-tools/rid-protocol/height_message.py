"""Represent the empty dynamic maximum-height GET payload (0x11/0x50, C-436).

This is a query payload, not a RID altitude setter or a transport frame.
The CLI prints an empty hex line because the payload contains zero bytes.
"""
import argparse

CMD = 0x50
SUB = 0x11


def build() -> bytes:
    return b""


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(build().hex())


if __name__ == "__main__":
    main()
