#!/usr/bin/env python3
"""Fail-closed static audit for the minimal RC 2 Settings launcher APK."""

from __future__ import annotations

import hashlib
import os
import pathlib
import re
import subprocess
import sys
import zipfile


EXPECTED_PACKAGE = "com.finduas.rc2settingslauncher"
EXPECTED_VERSION_NAME = "1.0.0"
EXPECTED_VERSION_CODE = "1"
EXPECTED_ACTIVITY = "com.finduas.rc2settingslauncher.MainActivity"
EXPECTED_ACTIONS = {
    "android.settings.DEVICE_INFO_SETTINGS",
    "android.settings.APPLICATION_DEVELOPMENT_SETTINGS",
}
FORBIDDEN_DEX_MARKERS = {
    "Ljava/io/File;",
    "Ljava/io/FileInputStream;",
    "Ljava/io/FileOutputStream;",
    "Ljava/lang/ProcessBuilder;",
    "Ljava/lang/Runtime;",
    "Ljava/net/Socket;",
    "Ljava/net/URL;",
    "Landroid/net/",
    "Landroid/provider/Settings$Global;",
    "Landroid/provider/Settings$Secure;",
    "Landroid/provider/Settings$System;",
    "Landroid/content/ContentResolver;",
    "Landroid/app/Service;",
    "Landroid/content/BroadcastReceiver;",
    "Landroid/content/ContentProvider;",
    "Landroid/os/IBinder;",
    "dji/",
    "uav/",
    "DUML",
    "127.0.0.1",
}


def fail(message: str) -> None:
    raise SystemExit(f"AUDIT FAIL: {message}")


def run(*args: str) -> str:
    completed = subprocess.run(
        args,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0:
        fail(f"command failed ({completed.returncode}): {' '.join(args)}\n{completed.stdout}")
    return completed.stdout


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def count_manifest_elements(xmltree: str, element: str) -> int:
    return len(re.findall(rf"^\s*E: {re.escape(element)}(?:\s|$)", xmltree, re.MULTILINE))


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: audit_artifact.py APK")
    apk = pathlib.Path(sys.argv[1]).resolve()
    if not apk.is_file():
        fail(f"missing APK: {apk}")

    sdk_value = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not sdk_value:
        fail("set ANDROID_HOME or ANDROID_SDK_ROOT to Android SDK 35")
    sdk = pathlib.Path(sdk_value)
    tools = sdk / "build-tools" / "35.0.0"
    aapt = tools / "aapt"
    dexdump = tools / "dexdump"
    apksigner = tools / "apksigner"
    zipalign = tools / "zipalign"
    for tool in (aapt, dexdump, apksigner, zipalign):
        if not tool.is_file():
            fail(f"missing required tool: {tool}")

    with zipfile.ZipFile(apk) as archive:
        entries = archive.namelist()
        dex_entries = [name for name in entries if re.fullmatch(r"classes(?:\d+)?\.dex", name)]
        # AGP 8.7 emits the generated R class and the four application classes as two tiny,
        # deterministic project-Dex shards for this dependency-free debug build.
        if dex_entries != ["classes.dex", "classes2.dex"]:
            fail(f"expected exact project DEX set, got {dex_entries}")
        if any(name.startswith("lib/") for name in entries):
            fail("native library packaged")
        dex_files = {name: archive.read(name) for name in dex_entries}
        dex_bytes = b"".join(dex_files.values())

    bad_dex_markers = sorted(
        marker for marker in FORBIDDEN_DEX_MARKERS if marker.encode("utf-8") in dex_bytes
    )
    if bad_dex_markers:
        fail(f"forbidden DEX markers: {bad_dex_markers}")
    missing_actions = sorted(
        action for action in EXPECTED_ACTIONS if action.encode("utf-8") not in dex_bytes
    )
    if missing_actions:
        fail(f"missing exact action strings from DEX: {missing_actions}")

    badging = run(str(aapt), "dump", "badging", str(apk))
    expected_badging = (
        f"package: name='{EXPECTED_PACKAGE}' versionCode='{EXPECTED_VERSION_CODE}' "
        f"versionName='{EXPECTED_VERSION_NAME}'"
    )
    if expected_badging not in badging:
        fail(f"unexpected package/version:\n{badging}")
    if f"launchable-activity: name='{EXPECTED_ACTIVITY}'" not in badging:
        fail("unexpected or missing launcher activity")

    permissions = run(str(aapt), "dump", "permissions", str(apk))
    if re.search(r"^uses-permission", permissions, re.MULTILINE):
        fail(f"Android permission declared:\n{permissions}")

    xmltree = run(str(aapt), "dump", "xmltree", str(apk), "AndroidManifest.xml")
    if count_manifest_elements(xmltree, "activity") != 1:
        fail("manifest must contain exactly one activity")
    for component in ("service", "receiver", "provider"):
        if count_manifest_elements(xmltree, component) != 0:
            fail(f"manifest contains forbidden {component}")
    if count_manifest_elements(xmltree, "uses-permission") != 0:
        fail("manifest contains uses-permission")
    for action in EXPECTED_ACTIONS:
        if action not in xmltree:
            fail(f"manifest query is missing {action}")
    if "android.intent.action.MAIN" not in xmltree or "android.intent.category.LAUNCHER" not in xmltree:
        fail("launcher intent filter is incomplete")

    dexdump_parts = []
    temporary_dex_paths = []
    try:
        for index, (name, contents) in enumerate(dex_files.items(), start=1):
            temporary_path = pathlib.Path(
                f"/tmp/rc2-settings-launcher-classes-{os.getpid()}-{index}.dex"
            )
            temporary_dex_paths.append(temporary_path)
            temporary_path.write_bytes(contents)
            dexdump_parts.append(run(str(dexdump), "-d", str(temporary_path)))
        dexdump_text = "\n".join(dexdump_parts)
    finally:
        for temporary_path in temporary_dex_paths:
            temporary_path.unlink(missing_ok=True)
    for forbidden_call in (
        "java/lang/Runtime.exec",
        "java/lang/ProcessBuilder.start",
        "android/content/ContentResolver.insert",
        "android/content/ContentResolver.update",
        "android/content/ContentResolver.delete",
        "android/content/Context.startService",
        "android/content/Context.sendBroadcast",
    ):
        if forbidden_call in dexdump_text:
            fail(f"forbidden call in bytecode: {forbidden_call}")

    align_output = run(str(zipalign), "-c", "-P", "16", "-v", "4", str(apk))
    signer_output = run(str(apksigner), "verify", "--verbose", "--print-certs", str(apk))
    cert_match = re.search(r"Signer #1 certificate SHA-256 digest: ([0-9a-f]+)", signer_output)
    if not cert_match:
        fail(f"could not parse signing certificate:\n{signer_output}")

    print("AUDIT PASS")
    print(f"artifact={apk}")
    print(f"bytes={apk.stat().st_size}")
    print(f"sha256={sha256(apk)}")
    print(f"signer_cert_sha256={cert_match.group(1)}")
    print(f"package={EXPECTED_PACKAGE}")
    print(f"version={EXPECTED_VERSION_NAME} ({EXPECTED_VERSION_CODE})")
    print("permissions=0")
    print("components=1 activity; 0 service; 0 receiver; 0 provider")
    print("native_libraries=0")
    print(f"dex_files={len(dex_entries)}")
    print("settings_actions=2 exact public Android actions")
    print(f"zipalign={align_output.strip().splitlines()[-1]}")
    print("signature=verified")


if __name__ == "__main__":
    main()
