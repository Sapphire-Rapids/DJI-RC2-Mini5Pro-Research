import importlib.util
import struct
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("extract_runtime_dex.py")
SPEC = importlib.util.spec_from_file_location("extract_runtime_dex", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def synthetic_dex(size: int = 0x80) -> bytes:
    data = bytearray(size)
    data[:8] = b"dex\n037\0"
    struct.pack_into("<I", data, 0x20, size)
    struct.pack_into("<I", data, 0x24, MODULE.DEX_HEADER_SIZE)
    struct.pack_into("<I", data, 0x28, MODULE.ENDIAN_CONSTANT)
    return bytes(data)


class RuntimeDexScanTest(unittest.TestCase):
    def test_extracts_multiple_images_in_offset_order(self) -> None:
        first = synthetic_dex()
        second = synthetic_dex(0x90)
        memory = b"prefix" + first + b"gap" + second + b"suffix"

        images = MODULE.find_dex_images(memory)

        self.assertEqual([6, 6 + len(first) + 3], [item[0] for item in images])
        self.assertEqual([first, second], [item[1] for item in images])

    def test_rejects_truncated_or_invalid_headers(self) -> None:
        truncated = synthetic_dex()[:-1]
        invalid = bytearray(synthetic_dex())
        struct.pack_into("<I", invalid, 0x24, 0x71)

        self.assertEqual([], MODULE.find_dex_images(truncated))
        self.assertEqual([], MODULE.find_dex_images(bytes(invalid)))


if __name__ == "__main__":
    unittest.main()
