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

import dji_target_locked_module_download as subject


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


class TargetLockedDownloadTests(unittest.TestCase):
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

    def test_all_compiled_targets_validate_against_report(self):
        configs = []
        for version in sorted({key[0] for key in subject.LOCKED_TARGETS}):
            modules = []
            for (target_version, _), target in subject.LOCKED_TARGETS.items():
                if target_version == version:
                    modules.append(
                        {
                            "module_id": target.module_id,
                            "module_version": target.module_version,
                            "filename": target.filename,
                            "size": target.size,
                            "md5": target.md5,
                        }
                    )
            configs.append({"product_version": version, "modules": modules})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "summary.json"
            path.write_text(
                json.dumps({"product_id": "wa150", "configs": configs}),
                encoding="utf-8",
            )
            for key, expected in subject.LOCKED_TARGETS.items():
                with self.subTest(target=key):
                    self.assertEqual(
                        subject._load_and_validate_target(*key, summary_path=path),
                        expected,
                    )

    def test_report_tampering_is_refused(self):
        target = subject.LOCKED_TARGETS[("01.00.0600", "2603")]
        report = {
            "product_id": "wa150",
            "configs": [
                {
                    "product_version": target.product_version,
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
            with self.assertRaises(subject.DownloadSafetyError):
                subject._load_and_validate_target(
                    target.product_version, target.module_id, path
                )

    def test_firmware_redirect_allowlist(self):
        filename = subject.LOCKED_TARGETS[("01.00.0600", "2603")].filename
        host, private_target, public_path = subject._validated_firmware_redirect(
            f"https://terra-2-g-a.djicdn.com/release/{filename}?opaque=1", filename
        )
        self.assertEqual(host, "terra-2-g-a.djicdn.com")
        self.assertEqual(private_target, f"/release/{filename}?opaque=1")
        self.assertEqual(public_path, f"/release/{filename}")

        refused = (
            f"http://a.djicdn.com/release/{filename}",
            f"https://djicdn.com/release/{filename}",
            f"https://a.djicdn.com.evil.example/release/{filename}",
            f"https://user@a.djicdn.com/release/{filename}",
            f"https://a.djicdn.com:444/release/{filename}",
            f"https://a.djicdn.com:invalid/release/{filename}",
            f"https://a.djicdn.com/release/%2e%2e/{filename}",
            f"https://a.djicdn.com//release/{filename}",
            f"https://a.djicdn.com/release/not-{filename}",
            f"https://a.djicdn.com/release/{filename}?bad query",
            f"https://a.djicdn.com/release/{filename}?bad=%zz",
            f"https://a.djicdn.com/release/{filename}#fragment",
        )
        for location in refused:
            with self.subTest(location=location):
                with self.assertRaises(subject.DownloadSafetyError):
                    subject._validated_firmware_redirect(location, filename)

    def test_operation_boundary_rejects_constructed_target(self):
        allowed = subject.LOCKED_TARGETS[("01.00.0600", "2603")]
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

    def test_initial_api_is_one_get_and_private_errors_are_sanitized(self):
        target = subject.LOCKED_TARGETS[("01.00.0600", "2603")]
        location = f"https://a.djicdn.com/release/{target.filename}?opaque=1"
        connection = FakeConnection(
            FakeResponse(302, headers={"Location": location})
        )
        with mock.patch.object(
            subject.http.client, "HTTPSConnection", return_value=connection
        ):
            self.assertEqual(
                subject._request_redirect(target, b"synthetic", 1.0, None),
                (
                    "a.djicdn.com",
                    f"/release/{target.filename}?opaque=1",
                    f"/release/{target.filename}",
                ),
            )
        self.assertEqual(len(connection.requests), 1)
        self.assertEqual(connection.requests[0][0], "GET")
        self.assertTrue(connection.requests[0][1].startswith(subject.API_PATH + "?"))

        marker = "private-query-must-not-escape"
        connection = FakeConnection(request_error=http.client.InvalidURL(marker))
        with mock.patch.object(
            subject.http.client, "HTTPSConnection", return_value=connection
        ):
            with self.assertRaises(subject.DownloadFormatError) as caught:
                subject._request_redirect(target, b"synthetic", 1.0, None)
        self.assertNotIn(marker, str(caught.exception))

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
                mock.patch.object(
                    subject,
                    "LOCKED_TARGETS",
                    {(target.product_version, target.module_id): target},
                ),
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
                mock.patch.object(
                    subject,
                    "LOCKED_TARGETS",
                    {(target.product_version, target.module_id): target},
                ),
            ):
                directory_fd, destination = subject._open_secure_output_dir(target)
                connection = FakeConnection(response)
                try:
                    with mock.patch.object(
                        subject.http.client,
                        "HTTPSConnection",
                        return_value=connection,
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
                return connection

    def test_stream_accepts_exact_body_and_refuses_second_redirect(self):
        connection = self._run_stream_case(
            FakeResponse(
                200,
                headers={
                    "Content-Type": "application/pgp-signature",
                    "Content-Length": "3",
                },
                body=b"abc",
            )
        )
        self.assertEqual(len(connection.requests), 1)
        self.assertEqual(connection.requests[0][0], "GET")

        self._run_stream_case(
            FakeResponse(302, headers={"Location": "https://b.djicdn.com/x"}),
            expect_error=subject.DownloadSafetyError,
        )

    def test_stream_rejects_length_and_md5_failures_without_publish(self):
        cases = (
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
        for response in cases:
            with self.subTest(body=response.stream.getvalue(), headers=response.headers):
                self._run_stream_case(response, expect_error=subject.DownloadSafetyError)

    def test_stream_http_error_does_not_expose_private_query(self):
        marker = "private-query-must-not-escape"
        target = self._synthetic_target()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            with (
                mock.patch.object(subject, "BASE_DIR", base),
                mock.patch.object(subject, "FIRMWARE_ROOT", base / "firmware"),
                mock.patch.object(
                    subject,
                    "LOCKED_TARGETS",
                    {(target.product_version, target.module_id): target},
                ),
            ):
                directory_fd, destination = subject._open_secure_output_dir(target)
                connection = FakeConnection(request_error=http.client.InvalidURL(marker))
                try:
                    with mock.patch.object(
                        subject.http.client,
                        "HTTPSConnection",
                        return_value=connection,
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
