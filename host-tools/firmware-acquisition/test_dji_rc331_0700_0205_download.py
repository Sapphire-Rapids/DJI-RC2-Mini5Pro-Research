import hashlib
import http.client
import io
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import dji_rc331_0700_0205_download as subject


class FakeResponse:
    def __init__(self, status, *, headers=None, body=b""):
        self.status = status
        self.headers = headers or {}
        self.stream = io.BytesIO(body)

    def getheader(self, name):
        return self.headers.get(name)

    def read(self, amount=-1):
        return self.stream.read(amount)


class FakeConnection:
    def __init__(self, response=None, request_error=None):
        self.response = response
        self.request_error = request_error
        self.requests = []
        self.closed = False

    def request(self, method, target, **kwargs):
        self.requests.append((method, target, kwargs))
        if self.request_error:
            raise self.request_error

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


class Rc331SingleTargetDownloadTests(unittest.TestCase):
    @staticmethod
    def _synthetic_target():
        return subject.LockedTarget(
            "test-version",
            "test-module",
            "test-module-version",
            "artifact.pro.fw.sig",
            3,
            hashlib.md5(b"abc").hexdigest(),
        )

    @staticmethod
    def _compiled_report(target):
        return {
            "product_id": "rc331",
            "target_versions": ["10.00.0700", "10.00.0800"],
            "configs": [
                {
                    "product_version": target.product_version,
                    "xml_retrieved": True,
                    "modules": [
                        {
                            "module_id": target.module_id,
                            "module_version": target.module_version,
                            "filename": target.filename,
                            "size": target.size,
                            "md5": target.md5,
                        }
                    ],
                }
            ],
        }

    def test_compiled_target_matches_deidentified_report(self):
        target = subject.LOCKED_TARGET
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "summary.json"
            path.write_text(json.dumps(self._compiled_report(target)), encoding="utf-8")
            with mock.patch.object(subject, "SUMMARY_PATH", path):
                self.assertEqual(subject._load_and_validate_target(path), target)
        self.assertEqual(
            (
                subject.PRODUCT_ID,
                target.product_version,
                target.module_id,
                target.module_version,
                target.size,
                target.md5,
            ),
            (
                "rc331",
                "10.00.0700",
                "0205",
                "00.01.14.99",
                985_959_104,
                "5c874f6e39819067caa31b67e0ad341b",
            ),
        )

    def test_arbitrary_report_path_and_constructed_target_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(subject.DownloadSafetyError):
                subject._load_and_validate_target(Path(directory) / "other.json")
        allowed = subject.LOCKED_TARGET
        constructed = subject.LockedTarget(
            allowed.product_version,
            allowed.module_id,
            allowed.module_version,
            "../outside.pro.fw.sig",
            allowed.size,
            allowed.md5,
        )
        with self.assertRaises(subject.DownloadSafetyError):
            subject._request_redirect(constructed, b"test", 1.0, None)

    def test_report_tampering_is_refused_even_at_compiled_path(self):
        target = subject.LOCKED_TARGET
        report = {
            "product_id": "rc331",
            "target_versions": ["10.00.0700", "10.00.0800"],
            "configs": [
                {
                    "product_version": target.product_version,
                    "xml_retrieved": True,
                    "modules": [
                        {
                            "module_id": target.module_id,
                            "module_version": target.module_version,
                            "filename": target.filename,
                            "size": target.size + 1,
                            "md5": target.md5,
                        }
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "summary.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            with mock.patch.object(subject, "SUMMARY_PATH", path):
                with self.assertRaises(subject.DownloadSafetyError):
                    subject._load_and_validate_target(path)

    def test_dry_run_uses_only_rc2_library_and_no_network(self):
        marker_secret = b"synthetic-secret"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "summary.json"
            path.write_text(
                json.dumps(self._compiled_report(subject.LOCKED_TARGET)),
                encoding="utf-8",
            )
            with (
                mock.patch.object(subject, "SUMMARY_PATH", path),
                mock.patch.object(
                    subject.metadata,
                    "extract_assistant_material",
                    return_value=(
                        "https://mydjiflight.dji.com",
                        marker_secret,
                        "ab" * 32,
                    ),
                ) as extract,
                mock.patch.object(subject.http.client, "HTTPSConnection") as connection,
            ):
                report = subject.dry_run()
        extract.assert_called_once_with(subject.RC2_DYLIB)
        connection.assert_not_called()
        self.assertEqual(report["network_used"], False)
        self.assertEqual(report["module_id"], "0205")
        self.assertNotIn(marker_secret.decode(), json.dumps(report))

    def test_initial_api_is_one_get_and_private_errors_are_sanitized(self):
        target = subject.LOCKED_TARGET
        location = f"https://a.djicdn.com/release/{target.filename}?opaque=1"
        connection = FakeConnection(FakeResponse(302, headers={"Location": location}))
        with mock.patch.object(
            subject.http.client, "HTTPSConnection", return_value=connection
        ):
            result = subject._request_redirect(target, b"synthetic", 1.0, None)
        self.assertEqual(
            result,
            (
                "a.djicdn.com",
                f"/release/{target.filename}?opaque=1",
                f"/release/{target.filename}",
            ),
        )
        self.assertEqual(len(connection.requests), 1)
        self.assertEqual(connection.requests[0][0], "GET")

        marker = "private-query-must-not-escape"
        connection = FakeConnection(request_error=http.client.InvalidURL(marker))
        with mock.patch.object(
            subject.http.client, "HTTPSConnection", return_value=connection
        ):
            with self.assertRaises(subject.DownloadFormatError) as caught:
                subject._request_redirect(target, b"synthetic", 1.0, None)
        self.assertNotIn(marker, str(caught.exception))

    def test_firmware_redirect_is_filename_and_cdn_locked(self):
        filename = subject.LOCKED_TARGET.filename
        valid = f"https://a.djicdn.com/release/{filename}?opaque=1"
        self.assertEqual(
            subject._validated_firmware_redirect(valid, filename),
            (
                "a.djicdn.com",
                f"/release/{filename}?opaque=1",
                f"/release/{filename}",
            ),
        )
        refused = (
            f"http://a.djicdn.com/release/{filename}",
            f"https://djicdn.com/release/{filename}",
            f"https://a.djicdn.com.evil.example/release/{filename}",
            f"https://a.djicdn.com/release/not-{filename}",
            f"https://a.djicdn.com/release/%2e%2e/{filename}",
            f"https://a.djicdn.com/release/{filename}?bad=%zz",
            f"https://user@a.djicdn.com/release/{filename}",
            f"https://a.djicdn.com:444/release/{filename}",
            f"https://a.djicdn.com/release/{filename}#fragment",
        )
        for location in refused:
            with self.subTest(location=location):
                with self.assertRaises(subject.DownloadSafetyError):
                    subject._validated_firmware_redirect(location, filename)

    def test_symlinked_output_parent_is_refused(self):
        target = self._synthetic_target()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / "base"
            outside = Path(directory) / "outside"
            base.mkdir()
            outside.mkdir()
            (base / "firmware").symlink_to(outside, target_is_directory=True)
            with (
                mock.patch.object(subject, "BASE_DIR", base),
                mock.patch.object(subject, "FIRMWARE_ROOT", base / "firmware"),
                mock.patch.object(subject, "LOCKED_TARGET", target),
            ):
                with self.assertRaises(subject.DownloadSafetyError):
                    subject._open_secure_output_dir(target)
            self.assertEqual(list(outside.iterdir()), [])

    def _run_stream_case(self, response, *, expect_error=None):
        target = self._synthetic_target()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            with (
                mock.patch.object(subject, "BASE_DIR", base),
                mock.patch.object(subject, "FIRMWARE_ROOT", base / "firmware"),
                mock.patch.object(subject, "LOCKED_TARGET", target),
            ):
                directory_fd, destination = subject._open_secure_output_dir(target)
                connection = FakeConnection(response)
                try:
                    with mock.patch.object(
                        subject.http.client, "HTTPSConnection", return_value=connection
                    ):
                        if expect_error:
                            with self.assertRaises(expect_error):
                                subject._stream_cdn(
                                    "a.djicdn.com",
                                    f"/release/{target.filename}?opaque=1",
                                    f"/release/{target.filename}",
                                    target,
                                    destination,
                                    directory_fd,
                                    1.0,
                                    None,
                                )
                        else:
                            result = subject._stream_cdn(
                                "a.djicdn.com",
                                f"/release/{target.filename}?opaque=1",
                                f"/release/{target.filename}",
                                target,
                                destination,
                                directory_fd,
                                1.0,
                                None,
                            )
                            self.assertEqual(result["status"], "downloaded-and-verified")
                finally:
                    os.close(directory_fd)
                if expect_error:
                    self.assertFalse(destination.exists())
                    self.assertEqual(list(destination.parent.glob("*.part")), [])
                else:
                    self.assertEqual(destination.read_bytes(), b"abc")
                    self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o444)

    def test_simulated_stream_accepts_exact_body_only(self):
        self._run_stream_case(
            FakeResponse(
                200,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": "3",
                },
                body=b"abc",
            )
        )
        failures = (
            FakeResponse(302, headers={"Location": "https://b.djicdn.com/x"}),
            FakeResponse(
                200,
                headers={"Content-Type": "application/octet-stream", "Content-Length": "4"},
                body=b"abc",
            ),
            FakeResponse(
                200,
                headers={"Content-Type": "application/octet-stream", "Content-Length": "3"},
                body=b"ab",
            ),
            FakeResponse(
                200,
                headers={"Content-Type": "application/octet-stream", "Content-Length": "3"},
                body=b"abd",
            ),
            FakeResponse(
                200,
                headers={"Content-Type": "application/octet-stream", "Content-Length": "3"},
                body=b"abcd",
            ),
        )
        for response in failures:
            with self.subTest(status=response.status, body=response.stream.getvalue()):
                self._run_stream_case(response, expect_error=subject.DownloadSafetyError)

    def test_stream_error_does_not_expose_private_query(self):
        target = self._synthetic_target()
        marker = "private-query-must-not-escape"
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            with (
                mock.patch.object(subject, "BASE_DIR", base),
                mock.patch.object(subject, "FIRMWARE_ROOT", base / "firmware"),
                mock.patch.object(subject, "LOCKED_TARGET", target),
            ):
                directory_fd, destination = subject._open_secure_output_dir(target)
                connection = FakeConnection(request_error=http.client.InvalidURL(marker))
                try:
                    with mock.patch.object(
                        subject.http.client, "HTTPSConnection", return_value=connection
                    ):
                        with self.assertRaises(subject.DownloadFormatError) as caught:
                            subject._stream_cdn(
                                "a.djicdn.com",
                                f"/release/{target.filename}?opaque=1",
                                f"/release/{target.filename}",
                                target,
                                destination,
                                directory_fd,
                                1.0,
                                None,
                            )
                finally:
                    os.close(directory_fd)
                self.assertNotIn(marker, str(caught.exception))
                self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
