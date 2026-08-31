"""Offline build rejection checks. No compiled device operation is executed."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent


class ResetGuardBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cc = shutil.which(os.environ.get("CC", "cc"))
        cls.pkg_config = shutil.which(os.environ.get("PKG_CONFIG", "pkg-config"))
        if not cls.cc or not cls.pkg_config or not shutil.which("nm"):
            raise unittest.SkipTest("C compiler, pkg-config and nm required")
        check = subprocess.run([cls.pkg_config, "--exists", "libmtp", "libusb-1.0"])
        if check.returncode:
            raise unittest.SkipTest("libmtp and libusb development files required")
        cls.libdir = Path(subprocess.check_output(
            [cls.pkg_config, "--variable=libdir", "libmtp"], text=True).strip())
        if not (cls.libdir / "libmtp.a").is_file():
            raise unittest.SkipTest("static libmtp.a required")

    def check_rejected(self, mode, expected, dynamic=""):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("build.sh", "mtp_bridge.c", "usb_reset_guard.c", "usb_reset_guard_test.c"):
                shutil.copyfile(ROOT / name, root / name)
            (root / "build").mkdir()
            product = root / "build/mtp_bridge"
            product.write_bytes(b"PREVIOUS_VERIFIED_BUILD")
            wrapper = root / "tool-wrapper"
            wrapper.write_text(f"#!{sys.executable}\n" + '''
import os
from pathlib import Path
import sys

args = sys.argv[1:]
mode = os.environ["RESET_TEST_MODE"]
if Path(sys.argv[0]).name == "pkg-config-wrapper":
    if mode == "missing_archive" and args == ["--variable=libdir", "libmtp"]:
        print(os.environ["RESET_TEST_MISSING"])
        raise SystemExit(0)
    os.execv(os.environ["RESET_TEST_PKG_CONFIG"], ["pkg-config", *args])
if any(Path(arg).name == "mtp_bridge.c" for arg in args):
    if mode == "missing_guard":
        args = [arg for arg in args if Path(arg).name != "usb_reset_guard.c"]
    elif mode == "dynamic_dependency":
        args.append(os.environ["RESET_TEST_DYNAMIC"])
os.execv(os.environ["RESET_TEST_CC"], ["cc", *args])
''')
            wrapper.chmod(0o700)
            (root / "cc-wrapper").symlink_to(wrapper.name)
            (root / "pkg-config-wrapper").symlink_to(wrapper.name)
            env = dict(os.environ, CC=str(root / "cc-wrapper"),
                       PKG_CONFIG=str(root / "pkg-config-wrapper"), RESET_TEST_MODE=mode,
                       RESET_TEST_CC=self.cc, RESET_TEST_PKG_CONFIG=self.pkg_config,
                       RESET_TEST_MISSING=str(root / "missing"), RESET_TEST_DYNAMIC=dynamic)
            result = subprocess.run(["sh", str(root / "build.sh")], env=env,
                                    capture_output=True, text=True, timeout=60)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(expected, result.stderr)
            self.assertEqual(product.read_bytes(), b"PREVIOUS_VERIFIED_BUILD")
            self.assertEqual(list((root / "build").iterdir()), [product])

    def test_missing_archive_has_no_dynamic_fallback(self):
        self.check_rejected("missing_archive", "static libmtp.a is required")

    def test_missing_guard_is_rejected_before_execution(self):
        self.check_rejected("missing_guard", "reset guard must be locally defined")

    def test_dynamic_libmtp_is_rejected_before_execution(self):
        dynamic = next((path for name in ("libmtp.dylib", "libmtp.so")
                        if (path := self.libdir / name).is_file()), None)
        if dynamic is None:
            self.skipTest("shared libmtp required for dependency rejection fixture")
        self.check_rejected("dynamic_dependency", "dynamic libmtp dependency", str(dynamic))


if __name__ == "__main__":
    unittest.main()
