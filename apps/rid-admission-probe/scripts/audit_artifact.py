#!/usr/bin/env python3
"""Fail-closed v0.12 probe audit, retaining historical v0.10/v0.11 profiles."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import zipfile


PROJECT = Path(__file__).resolve().parent.parent
CURRENT_PROFILE = "v12"
DEFAULT_APK = PROJECT / "dist" / "FindUAS-RID-Bridge-Probe-0.12.0-live32-samples.apk"
SEALED_PROFILE = os.environ.get("FINDUAS_SEALED_AUDIT") == "1"
EXPECTED_CURRENT_SIZE = 2_570_983
EXPECTED_CURRENT_SHA256 = "fdad29bfb1237bc224a805d6eb5a99358a044bd226610d9f0fc33975d94b606c"
SEALED_PRIOR_APKS = (
    (
        PROJECT / "dist" / "FindUAS-RID-Bridge-Probe-0.8.0-research.apk",
        2_477_789,
        "b67a99621440088a39d212483d2de69a47fdc26850b59ed7fecfa9e1e8c70fb1",
    ),
    (
        PROJECT / "dist" / "FindUAS-RID-Bridge-Probe-0.9.0-research.apk",
        2_538_215,
        "a59f0f6abb2d1a10aeba44efed76cc85d351086fbf6dff5c1cc377dabe12b97d",
    ),
)
EXPECTED_SIGNER = "37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224"
EXPECTED_EXTERNAL_INVOKE_COUNT = 2_361
EXPECTED_EXTERNAL_INVOKE_SHA256 = (
    "c3b4ed26b563e2be2e4806b57ba0d21b8ea15ee3e6fa276d4223e0749d32ed29"
)
# These legacy values are intentionally immutable. A new writer is not admitted
# merely by replacing the old invoke hash with whatever a build happens to emit.
PROFILES = {
    "v10": {
        "version_code": 10,
        "version_name": "0.10.0-research",
        "schema": "finduas-rid-probe/v0.10-schema-1",
        "external_count": EXPECTED_EXTERNAL_INVOKE_COUNT,
        "external_sha256": EXPECTED_EXTERNAL_INVOKE_SHA256,
        "sealed_size": EXPECTED_CURRENT_SIZE,
        "sealed_sha256": EXPECTED_CURRENT_SHA256,
    },
    "v11": {
        "version_code": 11,
        "version_name": "0.11.0-report-export",
        "schema": "finduas-rid-probe/v0.10-schema-1",  # Retained core schema.
        # Reviewed on APK aaa6f8bf...: only report storage, formatter/coordinator
        # and UI additions; the original ART/framework-read surfaces are retained.
        "external_count": 2627,
        "external_sha256": "4cc4ecb553f9c45689c29f09f8e6292e4dbceb92b438af82085b173e6f8c0f5c",
        "sealed_size": None,
        "sealed_sha256": None,
    },
    "v12": {
        "version_code": 12,
        "version_name": "0.12.0-live32-samples",
        "schema": "finduas-rid-probe/v0.10-schema-1",
        # Reviewed clean APK 46eb6ef1...: ELF32 reads, fixed PM/property reads,
        # fixed sample ZIP export and UI only; no new ART/DUML/network execution.
        "external_count": 3067,
        "external_sha256": "0e6b11a5891d2d7ac0cb84153f1c4e21ed277a24c2f1a6280418235ec421820e",
        "sealed_size": None,
        "sealed_sha256": None,
    },
}
REPORT_SOURCE = "app/src/safe/java/com/finduas/ridobserver/ProbeReportStore.kt"
REPORT_DESCRIPTOR = "Lcom/finduas/ridobserver/ProbeReportStore"
# Reviewed: unique mounted non-primary removable volume; fixed directory/name;
# non-emulated; <=256 KiB UTF-8; unique UUID attempt suffix; newly inserted URI
# ownership; pending -> UTF-8 close -> publish; own-row cleanup.
EXPECTED_REPORT_SOURCE_SHA256 = "80bec1fca211e41d86097630cae954104b617af76fbcd21106a5030f00e9265d"
EXPECTED_REPORT_DEX_SHA256 = "96fa9e54a92e65ac31d3c8f26646c049ae08ec524a3680b9384f2bfddbe6b258"
EXPECTED_REPORT_DESCRIPTORS = (
    "Lcom/finduas/ridobserver/ProbeReportStore$AndroidPendingReport;",
    "Lcom/finduas/ridobserver/ProbeReportStore$AndroidStore;",
    "Lcom/finduas/ridobserver/ProbeReportStore$PendingReport;",
    "Lcom/finduas/ridobserver/ProbeReportStore$Store;",
    "Lcom/finduas/ridobserver/ProbeReportStore$Volume;",
    "Lcom/finduas/ridobserver/ProbeReportStore;",
)
PROFILES["v11"].update({
    "report_source_sha256": EXPECTED_REPORT_SOURCE_SHA256,
    "report_dex_sha256": EXPECTED_REPORT_DEX_SHA256,
    "report_descriptors": EXPECTED_REPORT_DESCRIPTORS,
    "report_prefix": "FindUAS_Probe_v011_",
})
PROFILES["v12"].update({
    "report_source_sha256": "11fa59c20d9e8b1f4df4d0985880cf7f8729af529b78c84cad0b34eb17888a4d",
    "report_dex_sha256": "4b349108bfbf7525f3b3b7842d2f6d5c6fc3be8a71ee63f559e89d442f67273e",
    "report_descriptors": EXPECTED_REPORT_DESCRIPTORS,
    "report_prefix": "FindUAS_Probe_v012_",
    # Source-reviewed: fixed PM package/version and four enum entries only;
    # identity/path+metadata rechecks; bounded streaming; own pending SD row.
    "sample_source_sha256": "c9bda403ac697255eca7df02f38202c1a4a9c778e6f91235fa7db52ced243f90",
    "sample_dex_sha256": "5edf3cfb76d670ce6afd03b1f226f52c227eee211a39af81cfe087541bfba011",
    "sample_descriptors": (
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$$ExternalSyntheticLambda0;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$$ExternalSyntheticLambda1;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$$ExternalSyntheticLambda2;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$$ExternalSyntheticLambda3;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$$ExternalSyntheticLambda4;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$AndroidPendingZip;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$AndroidSource;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$AndroidStore;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$Copied;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$Entry;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$Failure;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$Identity;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$Metadata;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$PendingZip;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$Planned;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$Source;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$Store;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter$Volume;",
        "Lcom/finduas/ridobserver/InstalledFlySampleExporter;",
    ),
})
SAMPLE_SOURCE = "app/src/safe/java/com/finduas/ridobserver/InstalledFlySampleExporter.kt"
SAMPLE_DESCRIPTOR = "Lcom/finduas/ridobserver/InstalledFlySampleExporter"
EXPECTED_QUERIES = {
    "dji.go.v5",
    "com.dpad.fuli",
    "com.finduas.jvmti.canary.carrier",
    "com.finduas.jvmti.eidresolver.v1",
}
KNOWN_ART_VALUE = os.environ.get("FINDUAS_KNOWN_ART_PATH")
KNOWN_ART = Path(KNOWN_ART_VALUE).resolve() if KNOWN_ART_VALUE else None
KNOWN_ART_SHA256 = "3ec3d232ad7f4099c42f014b87658be47e83d7e21a7a053fb16c4d146103745d"
KNOWN_ART_BUILD_ID = "5f839ecc60b9ae39764305b5fee6ed37"
KNOWN_RANGES = (
    (0x5CCFA0, 0x100, "098c16b8613f438294017b8af2e2e45685556a9cf5c6882120f08a5ea315c668"),
    (0x56BFC4, 0xEBC, "9db764e816c6771623e660b308d2527da4e57d05530ae7a3c8dfdf9d07dec80a"),
)


class AuditFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditFailure(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tool(name: str) -> Path:
    sdk_value = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    require(sdk_value is not None, "set ANDROID_HOME or ANDROID_SDK_ROOT to Android SDK 35")
    sdk = Path(sdk_value)
    candidates = sorted((sdk / "build-tools").glob(f"*/{name}"), reverse=True)
    require(bool(candidates), f"Android build tool missing: {name}")
    return candidates[0]


def run(*args: str | Path) -> str:
    completed = subprocess.run(
        [str(value) for value in args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    require(completed.returncode == 0, f"command failed: {' '.join(map(str, args))}\n{completed.stdout}")
    return completed.stdout


def audit_prior_artifacts() -> None:
    for apk, expected_size, expected_sha256 in SEALED_PRIOR_APKS:
        require(apk.is_file(), f"sealed prior artifact is missing: {apk.name}")
        require(apk.stat().st_size == expected_size, f"sealed artifact size changed: {apk.name}")
        require(sha256(apk) == expected_sha256, f"sealed artifact hash changed: {apk.name}")


def elf_gnu_build_id(path: Path) -> str | None:
    with path.open("rb") as stream:
        header = stream.read(64)
        if len(header) != 64 or header[:6] != b"\x7fELF\x02\x01":
            return None
        program_offset = struct.unpack_from("<Q", header, 32)[0]
        program_size = struct.unpack_from("<H", header, 54)[0]
        program_count = struct.unpack_from("<H", header, 56)[0]
        if program_size < 56 or not 0 < program_count <= 1024:
            return None
        matches: list[str] = []
        for index in range(program_count):
            stream.seek(program_offset + index * program_size)
            program = stream.read(program_size)
            if len(program) != program_size or struct.unpack_from("<I", program)[0] != 4:
                continue
            note_offset = struct.unpack_from("<Q", program, 8)[0]
            note_size = struct.unpack_from("<Q", program, 32)[0]
            if not 0 < note_size <= 1024 * 1024:
                return None
            stream.seek(note_offset)
            notes = stream.read(note_size)
            if len(notes) != note_size:
                return None
            cursor = 0
            while cursor < len(notes):
                if len(notes) - cursor < 12:
                    return None
                name_size, description_size, note_type = struct.unpack_from(
                    "<III", notes, cursor
                )
                name_offset = cursor + 12
                description_offset = (name_offset + name_size + 3) & ~3
                next_offset = (description_offset + description_size + 3) & ~3
                if next_offset <= cursor or next_offset > len(notes):
                    return None
                if (
                    name_size == 4
                    and notes[name_offset:name_offset + 4] == b"GNU\x00"
                    and note_type == 3
                    and 0 < description_size <= 64
                ):
                    matches.append(
                        notes[description_offset:description_offset + description_size].hex()
                    )
                cursor = next_offset
    return matches[0] if len(matches) == 1 else None


def audit_known_profile_source() -> None:
    require(KNOWN_ART is not None, "set FINDUAS_KNOWN_ART_PATH for the sealed audit")
    require(KNOWN_ART.is_file(), f"known ART profile source missing: {KNOWN_ART}")
    require(sha256(KNOWN_ART) == KNOWN_ART_SHA256, "known ART whole-file hash changed")
    require(elf_gnu_build_id(KNOWN_ART) == KNOWN_ART_BUILD_ID, "known ART build-id changed")
    with KNOWN_ART.open("rb") as stream:
        for offset, size, expected in KNOWN_RANGES:
            stream.seek(offset)
            payload = stream.read(size)
            require(len(payload) == size, f"known ART range is short at {offset:#x}")
            require(
                hashlib.sha256(payload).hexdigest() == expected,
                f"known ART range hash changed at {offset:#x}",
            )


def audit_sources(profile: str = CURRENT_PROFILE) -> None:
    selected = PROFILES[profile]
    build = (PROJECT / "app/build.gradle.kts").read_text()
    manifest = (PROJECT / "app/src/safe/AndroidManifest.xml").read_text()
    art_source = (
        PROJECT
        / "app/src/safe/java/com/finduas/ridobserver/AndroidArtIdentityProbe.kt"
    ).read_text()
    activity = (
        PROJECT / "app/src/safe/java/com/finduas/ridobserver/MainActivity.kt"
    ).read_text()
    source_paths = sorted((PROJECT / "app/src/safe/java").rglob("*.kt"))
    safe_sources = "\n".join(path.read_text() for path in source_paths)
    non_output_sources = "\n".join(
        path.read_text() for path in source_paths
        if path not in ({PROJECT / REPORT_SOURCE, PROJECT / SAMPLE_SOURCE}
                        if profile == "v12" else {PROJECT / REPORT_SOURCE})
    )

    require(f'versionCode = {selected["version_code"]}' in build, "versionCode/profile mismatch")
    require(f'versionName = "{selected["version_name"]}"' in build, "versionName/profile mismatch")
    require('java.setSrcDirs(listOf("src/safe/java"))' in build, "safe Java source set not pinned")
    require('manifest.srcFile("src/safe/AndroidManifest.xml")' in build, "safe manifest not pinned")
    for forbidden in ("<uses-permission", "<service", "<receiver", "<provider"):
        require(forbidden not in manifest, f"safe manifest contains {forbidden}")
    query_packages = set(re.findall(r'<package android:name="([^"]+)"', manifest))
    require(query_packages == EXPECTED_QUERIES, f"unexpected package queries: {query_packages}")

    for required in (
        'SELF_MAPS_PATH = "/proc/self/maps"',
        "readMapsSnapshot(pageSize)",
        "readMapsSnapshot(firstScan.pageSizeBytes)",
        "firstScan != secondScan",
        "start <= 0L",
        "decimal.matches(fields[4])",
        "!hexadecimal.matches(parts[0])",
        "!hexadecimal.matches(parts[1])",
        "Os.lstat(identity.path)",
        "OsConstants.O_NOFOLLOW",
        "Os.fstat(descriptor)",
        "descriptorBefore.st_dev == 0L",
        "stat.st_mtim.tv_nsec",
        "stat.st_ctim.tv_nsec",
        "LinuxDeviceIdentity.matches(identity.device, descriptorBefore.st_dev)",
        "3ec3d232ad7f4099c42f014b87658be47e83d7e21a7a053fb16c4d146103745d",
        "5f839ecc60b9ae39764305b5fee6ed37",
        "098c16b8613f438294017b8af2e2e45685556a9cf5c6882120f08a5ea315c668",
        "9db764e816c6771623e660b308d2527da4e57d05530ae7a3c8dfdf9d07dec80a",
        "KNOWN_AGENT_UNLOAD_RANGE_OFFSET = 0x5ccfa0L",
        "KNOWN_AGENT_UNLOAD_RANGE_SIZE = 0x100",
        "KNOWN_RUNTIME_ATTACH_AGENT_RANGE_OFFSET = 0x56bfc4L",
        "KNOWN_RUNTIME_ATTACH_AGENT_RANGE_SIZE = 0xebc",
    ):
        require(required in art_source, f"ART source misses required guard: {required}")
    for forbidden in ("KNOWN_ATTACH_RANGE", "KNOWN_LOADER_RANGE"):
        require(forbidden not in art_source, f"ART source retains misnamed range: {forbidden}")
    if profile == "v12":
        for guard in (
            "ELF_CLASS_32 = 1", "ELF32_HEADER_SIZE = 52",
            "ELF64_HEADER_SIZE = 64", "ELF32_PROGRAM_HEADER_MIN_SIZE = 32",
            "ELF64_PROGRAM_HEADER_MIN_SIZE = 56",
            "view.getInt(28).toLong() and 0xffffffffL",
            "view.getShort(if (is32Bit) 42 else 54)",
            "view.getShort(if (is32Bit) 44 else 56)",
            "program.getInt(4).toLong() and 0xffffffffL",
            "program.getInt(16).toLong() and 0xffffffffL",
            "rangeWithinFile(programOffset, programEntrySize.toLong() * programCount, fileSize)",
            "rangeWithinFile(noteOffset, noteSize, fileSize)",
            "matches.singleOrNull()",
        ):
            require(guard in art_source, f"ELF32/64 source guard changed: {guard}")
    proc_paths = {
        value.rstrip(".,")
        for value in re.findall(r"/proc/[A-Za-z0-9_{}$./-]+", art_source)
    }
    require(proc_paths == {"/proc/self/maps"}, "ART source contains a non-self proc path")
    for forbidden in (
        "Class.forName", "getDeclaredMethod", "java.lang.reflect", ".invoke(",
        "attachJvmtiAgent", "AttachAgent(", "System.load", "loadLibrary(",
        "Runtime.getRuntime", "ProcessBuilder", "DexFile", "ClassLoader",
        "java.net", "Socket(", "dji.go.v5", "com.dji.",
    ):
        require(forbidden not in art_source, f"new ART section contains {forbidden}")

    require(selected["schema"] in activity, "profile schema missing")
    require("machine_section_end=true" in activity, "machine section terminator missing")
    require("ProbeCompletionPolicy.terminalState" in activity, "completion gate missing")
    require("nextArtIdentity.state" in activity, "completion call is not fed by ART result state")
    require("ProbeSessionCoordinator.start(applicationContext)" in activity,
            "Activity does not use retained coordinator")
    require("ProbeRunAdmissionPolicy.mayStart(state.runState)" in activity,
            "retained coordinator lacks the duplicate-run gate")
    require("readMapsSnapshot(firstScan.pageSizeBytes)" in art_source,
            "ART source lacks the second maps snapshot")
    require("artIdentity.mapEntries.forEachIndexed" in activity, "map enumeration missing")
    require("art.agent_unload_range.offset" in activity, "Agent::Unload machine field missing")
    require("art.runtime_attach_agent_range.offset" in activity,
            "Runtime::AttachAgent machine field missing")
    require("art.attach_range." not in activity, "misnamed attach_range schema survived")
    require("art.loader_range." not in activity, "misnamed loader_range schema survived")
    for forbidden in (
        "java.net", "Socket(", "127.0.0.1", "40007", "40009",
        "ObserverService", "startService", "Runtime.getRuntime",
        "ProcessBuilder", "dalvik.system", "DexFile", "loadClass(",
        "createPackageContext", "FileOutputStream", "FileWriter(",
        "OutputStreamWriter(", "BufferedWriter(", "PrintWriter(",
        "DataOutputStream(", "ObjectOutputStream(", "ZipOutputStream(",
        "System.load", ".loadLibrary(", ".writeText(", ".writeBytes(",
        ".appendText(", ".appendBytes(", ".outputStream(",
        ".bufferedWriter(", ".printWriter(", "Files.write(",
        "Files.newOutputStream(", "Files.newBufferedWriter(",
        "Files.copy(", "Files.move(", "Files.delete(",
        "Files.createFile(", "Files.createDirectory(",
        "openFileOutput(", "openOutputStream(", ".deleteRecursively(",
        ".renameTo(", ".mkdir(", ".mkdirs(", "Os.write(",
        "Os.pwrite(", "Os.writev(", "Os.socket(", "Os.connect(",
        "Os.sendto(", "Os.sendmsg(", "Os.bind(", "Os.listen(",
        "Os.accept(",
    ):
        # Exceptions are only the reviewed output classes' resolver opener and
        # v12's fixed sample ZIP constructor. File writers, syscalls and all old
        # execution/network bans still apply to those sources themselves.
        inspected = safe_sources
        if profile in ("v11", "v12") and forbidden == "openOutputStream(":
            inspected = non_output_sources
        elif profile == "v12" and forbidden == "ZipOutputStream(":
            inspected = "\n".join(path.read_text() for path in source_paths
                                    if path != PROJECT / SAMPLE_SOURCE)
        require(forbidden not in inspected, f"packaged source contains {forbidden}")
    # MessageDigest.update() is an existing read-only ART hashing operation.
    # Resolver.update overloads are checked by owning DEX class below instead of
    # banning every unrelated method with the same source-level name.
    for forbidden in (".insert(", ".delete(", ".write("):
        require(forbidden not in non_output_sources,
                f"source outside the reviewed output classes contains {forbidden}")
    if profile in ("v11", "v12"):
        report_path = PROJECT / REPORT_SOURCE
        require(report_path.is_file(), f"{profile} report store source missing")
        require(selected["report_source_sha256"] is not None,
                f"{profile} report source has not completed manual safety review")
        require(sha256(report_path) == selected["report_source_sha256"],
                "reviewed report store source changed")
        require(selected["version_name"] in activity, "report app version marker missing")
    if profile == "v12":
        sample_path = PROJECT / SAMPLE_SOURCE
        require(sample_path.is_file(), "v12 fixed sample exporter source missing")
        require(selected["sample_source_sha256"] is not None,
                "v12 fixed sample exporter has not completed manual safety review")
        require(sha256(sample_path) == selected["sample_source_sha256"],
                "reviewed fixed sample exporter source changed")
    for required in (
        "Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS",
        "Settings.ACTION_DEVICE_INFO_SETTINGS",
        "Settings.ACTION_SETTINGS",
        "ActivityNotFoundException",
        "SettingsNavigationState.ACTIVITY_NOT_FOUND",
        "SettingsNavigationState.DENIED",
        "startActivity(Intent(action))",
    ):
        require(required in activity, f"settings navigation misses {required}")
    require(safe_sources.count("startActivity(") == 1, "unexpected Activity launch surface")
    require(
        activity.index("Settings.ACTION_DEVICE_INFO_SETTINGS") <
        activity.index("Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS"),
        "Settings buttons are not declared in safe Device-info then Developer order",
    )
    for forbidden in (
        ".setPackage(", ".setComponent(", ".putExtra(", ".setData(",
        "dji.go.v5", "com.dji.",
    ):
        require(forbidden not in activity, f"settings navigation contains {forbidden}")


def dex_class_block(dex_dump: str, descriptor: str) -> str:
    marker = f"Class descriptor  : '{descriptor}'"
    start = dex_dump.find(marker)
    require(start >= 0, f"DEX class missing: {descriptor}")
    end = dex_dump.find("\nClass #", start + len(marker))
    return dex_dump[start:] if end < 0 else dex_dump[start:end]


def dex_method_block(class_block: str, method_name: str) -> str:
    marker = f"name          : '{method_name}'"
    start = class_block.find(marker)
    require(start >= 0, f"DEX method missing: {method_name}")
    candidates = [
        value for value in (
            class_block.find("\n    #", start + len(marker)),
            class_block.find("\n  source_file_idx", start + len(marker)),
        ) if value >= 0
    ]
    end = min(candidates) if candidates else len(class_block)
    return class_block[start:end]


def dex_enclosing_method_block(class_block: str, needle: str) -> str:
    """Returns the single method body containing ``needle``.

    DEX program counters restart at zero for every method.  Auditing a whole
    class would therefore let instructions or local-variable records from a
    sibling method accidentally satisfy a proof about the completion caller.
    """
    needle_offset = class_block.find(needle)
    require(needle_offset >= 0, f"DEX method needle missing: {needle}")
    method_headers = list(re.finditer(r"(?m)^    #\d+\s+: \(in ", class_block))
    containing = [
        (header.start(), method_headers[index + 1].start()
         if index + 1 < len(method_headers) else len(class_block))
        for index, header in enumerate(method_headers)
        if header.start() <= needle_offset < (
            method_headers[index + 1].start()
            if index + 1 < len(method_headers) else len(class_block)
        )
    ]
    require(len(containing) == 1, "completion caller method could not be isolated")
    start, end = containing[0]
    return class_block[start:end]


def dex_instructions(block: str) -> list[tuple[int, str]]:
    instructions: list[tuple[int, str]] = []
    for match in re.finditer(r"\|([0-9a-f]{4}):\s+([^\n]+)", block):
        operation = match.group(2).split(" //", 1)[0].strip()
        instructions.append((int(match.group(1), 16), operation))
    return instructions


def dex_catch_ranges(block: str) -> list[tuple[int, int, tuple[int, ...]]]:
    """Parses dexdump catch ranges as half-open PC intervals."""
    lines = block.splitlines()
    ranges: list[tuple[int, int, tuple[int, ...]]] = []
    for index, line in enumerate(lines):
        range_match = re.fullmatch(
            r"\s*0x([0-9a-f]{4}) - 0x([0-9a-f]{4})", line
        )
        if range_match is None:
            continue
        handlers: list[int] = []
        cursor = index + 1
        while cursor < len(lines):
            handler_match = re.fullmatch(
                r"\s*(?:<any>|L[^;]+;) -> 0x([0-9a-f]{4})", lines[cursor]
            )
            if handler_match is None:
                break
            handlers.append(int(handler_match.group(1), 16))
            cursor += 1
        require(bool(handlers), "DEX catch range has no handler")
        ranges.append(
            (
                int(range_match.group(1), 16),
                int(range_match.group(2), 16),
                tuple(handlers),
            )
        )
    return ranges


def dex_control_flow(
    block: str,
) -> tuple[
    list[tuple[int, str]],
    dict[int, set[int]],
    dict[int, set[int]],
    list[tuple[int, int, tuple[int, ...]]],
]:
    """Builds normal and exception-aware control flow for one small method."""
    instructions = dex_instructions(block)
    require(bool(instructions), "DEX caller method has no instructions")
    pcs = [pc for pc, _ in instructions]
    require(len(pcs) == len(set(pcs)), "DEX caller method repeats a program counter")
    pc_set = set(pcs)
    normal: dict[int, set[int]] = {pc: set() for pc in pcs}
    for index, (pc, operation) in enumerate(instructions):
        fallthrough = pcs[index + 1] if index + 1 < len(pcs) else None
        opcode = operation.split(" ", 1)[0]
        if opcode.startswith("goto"):
            match = re.fullmatch(r"goto(?:/\d+)? ([0-9a-f]{4})", operation)
            require(match is not None, f"unparsed DEX goto: {operation}")
            normal[pc].add(int(match.group(1), 16))
        elif opcode.startswith("if-"):
            match = re.search(r", ([0-9a-f]{4})$", operation)
            require(match is not None and fallthrough is not None,
                    f"unparsed DEX branch: {operation}")
            normal[pc].update((fallthrough, int(match.group(1), 16)))
        elif opcode in {"return", "return-void", "return-object", "return-wide", "throw"}:
            pass
        else:
            require(
                not opcode.endswith("switch") and opcode != "fill-array-data",
                f"unsupported DEX control flow in completion caller: {operation}",
            )
            if fallthrough is not None:
                normal[pc].add(fallthrough)
    require(
        all(target in pc_set for targets in normal.values() for target in targets),
        "DEX branch target is not an instruction boundary",
    )

    catches = dex_catch_ranges(block)
    graph = {pc: set(targets) for pc, targets in normal.items()}
    for start, end, handlers in catches:
        require(start < end, "DEX catch range is reversed or empty")
        require(all(handler in pc_set for handler in handlers),
                "DEX catch handler is not an instruction boundary")
        for pc in pcs:
            if start <= pc < end:
                graph[pc].update(handlers)
    return instructions, normal, graph, catches


def reachable_nodes(graph: dict[int, set[int]], start: int) -> set[int]:
    pending = [start]
    reached: set[int] = set()
    while pending:
        current = pending.pop()
        if current in reached:
            continue
        reached.add(current)
        pending.extend(graph[current] - reached)
    return reached


def dominators(graph: dict[int, set[int]], start: int) -> dict[int, set[int]]:
    reachable = reachable_nodes(graph, start)
    predecessors = {pc: set() for pc in reachable}
    for source in reachable:
        for target in graph[source] & reachable:
            predecessors[target].add(source)
    result = {
        pc: ({start} if pc == start else set(reachable))
        for pc in reachable
    }
    changed = True
    while changed:
        changed = False
        for pc in reachable - {start}:
            incoming = predecessors[pc]
            require(bool(incoming), f"reachable DEX instruction has no predecessor: {pc:#x}")
            intersection = set(reachable)
            for predecessor in incoming:
                intersection &= result[predecessor]
            updated = {pc} | intersection
            if updated != result[pc]:
                result[pc] = updated
                changed = True
    return result


def register_writes(
    instructions: list[tuple[int, str]], register: str
) -> list[tuple[int, str]]:
    """Conservatively identifies writes whose first operand is ``register``."""
    read_only_first_operand = (
        "if-", "return", "throw", "monitor-", "goto", "invoke-",
        "iput", "sput", "aput", "packed-switch", "sparse-switch",
        "fill-array-data",
    )
    writes: list[tuple[int, str]] = []
    for pc, operation in instructions:
        opcode, _, operands = operation.partition(" ")
        first_register = re.match(r"(v\d+)(?:,|$)", operands)
        if first_register is None or first_register.group(1) != register:
            continue
        if opcode.startswith(read_only_first_operand):
            continue
        writes.append((pc, operation))
    return writes


def local_register(block: str, name: str, type_descriptor: str) -> str:
    register, _, _ = local_register_lifetime(block, name, type_descriptor)
    return register


def local_register_lifetime(
    block: str, name: str, type_descriptor: str
) -> tuple[str, int, int]:
    matches = re.findall(
        rf"0x([0-9a-f]{{4}}) - 0x([0-9a-f]{{4}}) "
        rf"reg=(\d+) {re.escape(name)} {re.escape(type_descriptor)}(?:\s|$)",
        block,
    )
    require(len(set(matches)) == 1, f"DEX local register is ambiguous/missing: {name}")
    start, end, register = matches[0]
    require(int(start, 16) < int(end, 16), f"DEX local lifetime is empty: {name}")
    return f"v{register}", int(start, 16), int(end, 16)


def audit_completion_flag_provenance(
    method: str,
    completion_call_pc: int,
    register: str,
    local_start_pc: int,
    local_end_pc: int,
    probe_call_needle: str,
    label: str,
) -> None:
    """Proves a completion boolean is false until its probe returns normally."""
    instructions, normal, graph, catches = dex_control_flow(method)
    operation_by_pc = dict(instructions)
    entry = instructions[0][0]
    probe_calls = [
        pc for pc, operation in instructions if probe_call_needle in operation
    ]
    require(len(probe_calls) == 1, f"{label} probe call is ambiguous/missing")
    probe_call_pc = probe_calls[0]

    # Debug local lifetimes begin immediately *after* the initializer.  Include
    # that one preceding instruction, while excluding earlier reuse of the same
    # Dalvik register for unrelated temporaries.
    earlier = [(pc, operation) for pc, operation in instructions if pc < local_start_pc]
    require(bool(earlier), f"{label} completion local has no initializer")
    initializer_pc = earlier[-1][0]
    writes = [
        write for write in register_writes(instructions, register)
        if initializer_pc <= write[0] < local_end_pc
    ]
    require(len(writes) == 2, f"{label} completion flag has unexpected writes")
    false_write, true_write = writes
    require(
        re.fullmatch(rf"const/4 {re.escape(register)}, #int 0", false_write[1]) is not None,
        f"{label} completion flag is not initialized false",
    )
    require(
        re.fullmatch(rf"const/4 {re.escape(register)}, #int 1", true_write[1]) is not None,
        f"{label} completion flag is not set by one explicit true write",
    )
    false_pc, true_pc = false_write[0], true_write[0]
    require(false_pc == initializer_pc,
            f"{label} completion initializer is not adjacent to its local lifetime")
    require(local_start_pc <= completion_call_pc < local_end_pc,
            f"{label} completion flag is dead at the final gate")

    dom = dominators(graph, entry)
    require(completion_call_pc in dom, "completion call is unreachable in DEX CFG")
    require(false_pc in dom[probe_call_pc],
            f"{label} false initialization does not dominate its probe")
    require(false_pc in dom[true_pc],
            f"{label} false initialization does not dominate its true write")
    require(false_pc in dom[completion_call_pc],
            f"{label} false initialization does not dominate the final gate")
    require(probe_call_pc in dom[true_pc],
            f"{label} true write can bypass its probe call")

    # Dalvik requires move-result immediately after a successful invoke.  Keep
    # the entire normal-return path to the true write straight-line so no
    # branch/catch target can enter the success-only suffix.
    pcs = [pc for pc, _ in instructions]
    call_index = pcs.index(probe_call_pc)
    require(call_index + 1 < len(pcs), f"{label} probe has no move-result")
    move_result_pc = pcs[call_index + 1]
    require(operation_by_pc[move_result_pc].startswith("move-result"),
            f"{label} probe result is not consumed immediately")
    cursor = probe_call_pc
    success_path: list[int] = []
    while cursor != true_pc:
        successors = normal[cursor]
        require(len(successors) == 1,
                f"{label} success path branches before its true write")
        cursor = next(iter(successors))
        success_path.append(cursor)
        require(len(success_path) <= len(instructions),
                f"{label} success path loops before its true write")
    require(success_path[0] == move_result_pc,
            f"{label} true write is not on the probe normal-return path")

    handlers = {
        handler
        for start, end, catch_handlers in catches
        if start <= probe_call_pc < end
        for handler in catch_handlers
    }
    require(bool(handlers), f"{label} probe call is not fail-closed by a catch")
    for handler in handlers:
        reached = reachable_nodes(graph, handler)
        require(true_pc not in reached,
                f"{label} exception handler can reach its true write")
        require(completion_call_pc in reached,
                f"{label} exception handler cannot report through the final gate")


def audit_art_identity_provenance(
    method: str,
    state_get_pc: int,
    next_art_register: str,
    local_start_pc: int,
    local_end_pc: int,
) -> None:
    """Proves getState() observes either the real ART run or fail-closed fallback."""
    instructions, normal, graph, catches = dex_control_flow(method)
    operation_by_pc = dict(instructions)
    pcs = [pc for pc, _ in instructions]
    art_call_needle = (
        "Lcom/finduas/ridobserver/AndroidArtIdentityProbe;.run:()"
        "Lcom/finduas/ridobserver/AndroidArtIdentityResult;"
    )
    art_calls = [pc for pc, operation in instructions if art_call_needle in operation]
    require(len(art_calls) == 1, "ART identity probe call is ambiguous/missing")
    art_call_pc = art_calls[0]
    call_index = pcs.index(art_call_pc)
    require(call_index + 2 < len(pcs), "ART identity probe success path is truncated")
    move_result_pc = pcs[call_index + 1]
    move_result = re.fullmatch(
        r"move-result-object (v\d+)", operation_by_pc[move_result_pc]
    )
    require(move_result is not None, "ART identity result is not consumed immediately")
    success_write_pc = pcs[call_index + 2]
    require(
        operation_by_pc[success_write_pc] ==
        f"move-object {next_art_register}, {move_result.group(1)}",
        "nextArtIdentity is not assigned from AndroidArtIdentityProbe.run()",
    )

    handlers = {
        handler
        for start, end, catch_handlers in catches
        if start <= art_call_pc < end
        for handler in catch_handlers
    }
    require(len(handlers) == 1, "ART identity probe must have one fail-closed handler")
    handler = next(iter(handlers))
    art_try_starts = {
        start for start, end, catch_handlers in catches
        if start <= art_call_pc < end and handler in catch_handlers
    }
    require(len(art_try_starts) == 1, "ART identity probe try range is ambiguous")
    art_try_start = next(iter(art_try_starts))
    entry = instructions[0][0]
    full_dom = dominators(graph, entry)
    normal_dom = dominators(normal, entry)
    require(art_try_start in full_dom[state_get_pc],
            "ART state read can bypass the validated try/fallback region")
    require(art_call_pc in normal_dom[state_get_pc],
            "normal ART state-read path can bypass AndroidArtIdentityProbe.run()")
    handler_reached = reachable_nodes(graph, handler)
    require(success_write_pc not in handler_reached,
            "ART identity exception handler can enter the success assignment")
    require(state_get_pc in handler_reached,
            "ART identity exception handler cannot reach the completion observation")

    relevant_writes = [
        write for write in register_writes(instructions, next_art_register)
        if art_call_pc <= write[0] <= state_get_pc
    ]
    require(len(relevant_writes) == 2,
            "nextArtIdentity has an unexpected assignment before completion")
    require(relevant_writes[0][0] == success_write_pc,
            "nextArtIdentity success assignment order changed")
    fallback_write_pc, fallback_write = relevant_writes[1]
    fallback_match = re.fullmatch(
        rf"move-object {re.escape(next_art_register)}, (v\d+)", fallback_write
    )
    require(fallback_match is not None,
            "ART identity fallback is not an explicit result object")
    fallback_source = fallback_match.group(1)
    require(fallback_write_pc in handler_reached,
            "ART identity fallback is not reached from the probe exception")

    fallback_new = [
        pc for pc, operation in instructions
        if operation == (
            f"new-instance {fallback_source}, "
            "Lcom/finduas/ridobserver/AndroidArtIdentityResult;"
        ) and pc in handler_reached and pc <= fallback_write_pc
    ]
    require(len(fallback_new) == 1,
            "ART identity fallback object construction is ambiguous/missing")
    file_error_loads: list[tuple[int, str]] = []
    for pc, operation in instructions:
        match = re.fullmatch(
            r"sget-object (v\d+), "
            r"Lcom/finduas/ridobserver/ArtIdentityState;\.FILE_READ_ERROR:"
            r"Lcom/finduas/ridobserver/ArtIdentityState;",
            operation,
        )
        if match is not None and pc in handler_reached:
            file_error_loads.append((pc, match.group(1)))
    require(len(file_error_loads) == 1,
            "ART identity fallback does not load exactly FILE_READ_ERROR")
    file_error_pc, file_error_register = file_error_loads[0]
    fallback_constructors: list[int] = []
    for pc, operation in instructions:
        match = re.fullmatch(
            r"invoke-direct/range \{([^}]+)\}, "
            r"Lcom/finduas/ridobserver/AndroidArtIdentityResult;\.<init>:"
            r"\(Lcom/finduas/ridobserver/ArtIdentityState;.*",
            operation,
        )
        if match is None or pc not in handler_reached:
            continue
        arguments = [value.strip() for value in match.group(1).split(",")]
        if len(arguments) >= 2 and arguments[:2] == [
            next_art_register, file_error_register
        ]:
            fallback_constructors.append(pc)
    require(len(fallback_constructors) == 1,
            "ART identity fallback is not constructed with FILE_READ_ERROR")
    fallback_constructor_pc = fallback_constructors[0]
    file_error_writes = [
        write for write in register_writes(instructions, file_error_register)
        if file_error_pc <= write[0] < fallback_constructor_pc
    ]
    require(file_error_writes == [(file_error_pc, operation_by_pc[file_error_pc])],
            "FILE_READ_ERROR is overwritten before fallback construction")
    require(
        fallback_new[0] < fallback_write_pc < file_error_pc < fallback_constructor_pc < state_get_pc,
        "ART identity fallback construction order changed",
    )

    # The exception handler's normal path through fallback construction must be
    # straight-line; otherwise a branch could bypass initialization and still
    # arrive at the final state read.
    cursor = handler
    walked: list[int] = []
    while cursor != fallback_constructor_pc:
        successors = normal[cursor]
        require(len(successors) == 1,
                "ART identity fallback branches before construction")
        cursor = next(iter(successors))
        walked.append(cursor)
        require(len(walked) <= len(instructions),
                "ART identity fallback loops before construction")

    require(local_start_pc <= state_get_pc < local_end_pc,
            "nextArtIdentity is dead at its completion state read")
    # Symbolically prove every control-flow path which reaches getState has one
    # of the two validated origins, never an uninitialized/reused register.
    states_at: dict[int, set[str]] = {art_try_start: {"unset"}}
    pending = [art_try_start]
    while pending:
        pc = pending.pop()
        before = states_at[pc]
        if pc == state_get_pc:
            continue
        after = before
        if pc == success_write_pc:
            after = {"probe_run"}
        elif pc == fallback_write_pc:
            after = {"file_read_error_fallback"}
        for successor in graph[pc]:
            merged = states_at.get(successor, set()) | after
            if merged != states_at.get(successor, set()):
                states_at[successor] = merged
                pending.append(successor)
    require(
        states_at.get(state_get_pc) == {"probe_run", "file_read_error_fallback"},
        "nextArtIdentity has an unproved origin at getState()",
    )


def audit_completion_result_storage(method: str, completion_call_pc: int) -> None:
    """Proves terminalState() output becomes the persisted snapshot runState."""
    instructions, normal, graph, _ = dex_control_flow(method)
    operation_by_pc = dict(instructions)
    pcs = [pc for pc, _ in instructions]
    call_index = pcs.index(completion_call_pc)
    require(call_index + 1 < len(pcs), "completion gate result is not consumed")
    result_pc = pcs[call_index + 1]
    result_match = re.fullmatch(
        r"move-result-object (v\d+)", operation_by_pc[result_pc]
    )
    require(result_match is not None, "completion gate result is not consumed immediately")
    result_register = result_match.group(1)

    copy_prefix = (
        "Lcom/finduas/ridobserver/ProbeSessionSnapshot;.copy$default:"
        "(Lcom/finduas/ridobserver/ProbeSessionSnapshot;"
        "Lcom/finduas/ridobserver/ProtocolBinderProbeResult;"
        "Lcom/finduas/ridobserver/LocalBridgeProbeResult;"
        "Lcom/finduas/ridobserver/AndroidArtIdentityResult;ZZ"
        "Lcom/finduas/ridobserver/ProbeRunState;"
    )
    copies: list[tuple[int, list[str]]] = []
    for pc, operation in instructions:
        match = re.fullmatch(r"invoke-static/range \{([^}]+)\}, (.+)", operation)
        if match is None or not match.group(2).startswith(copy_prefix):
            continue
        copies.append((pc, [value.strip() for value in match.group(1).split(",")]))
    require(len(copies) == 1, "final ProbeSessionSnapshot copy is ambiguous/missing")
    copy_pc, copy_arguments = copies[0]
    require(len(copy_arguments) == 15,
            "final ProbeSessionSnapshot copy argument shape changed")
    require(copy_arguments[6] == result_register,
            "terminalState() result is not the snapshot runState argument")
    writes_after_result = [
        write for write in register_writes(instructions, result_register)
        if result_pc <= write[0] < copy_pc
    ]
    require(writes_after_result == [(result_pc, operation_by_pc[result_pc])],
            "terminalState() result is overwritten before snapshot storage")
    mask_register = copy_arguments[13]
    mask_writes = [
        write for write in register_writes(instructions, mask_register)
        if completion_call_pc < write[0] < copy_pc
    ]
    require(bool(mask_writes), "ProbeSessionSnapshot copy mask is not initialized")
    mask_pc, mask_operation = mask_writes[-1]
    mask_match = re.fullmatch(
        rf"const(?:/4|/16)? {re.escape(mask_register)}, #int (\d+)",
        mask_operation,
    )
    require(mask_match is not None and int(mask_match.group(1)) == 0xEC0,
            "ProbeSessionSnapshot copy mask changed from 0xec0")
    require(int(mask_match.group(1)) & 0x3F == 0,
            "ProbeSessionSnapshot copy mask defaults an observed completion field")
    require(
        [write for write in mask_writes if mask_pc <= write[0] < copy_pc] ==
        [(mask_pc, mask_operation)],
        "ProbeSessionSnapshot copy mask is overwritten before use",
    )

    dom = dominators(graph, instructions[0][0])
    require(completion_call_pc in dom[copy_pc],
            "snapshot storage can bypass terminalState()")
    cursor = completion_call_pc
    walked: list[int] = []
    while cursor != copy_pc:
        successors = normal[cursor]
        require(len(successors) == 1,
                "completion result path branches before snapshot storage")
        cursor = next(iter(successors))
        walked.append(cursor)
        require(len(walked) <= len(instructions),
                "completion result path loops before snapshot storage")

    non_nop = [(pc, operation) for pc, operation in instructions if operation != "nop"]
    copy_index = next(index for index, (pc, _) in enumerate(non_nop) if pc == copy_pc)
    require(copy_index + 2 < len(non_nop), "snapshot copy result is not persisted")
    snapshot_result = re.fullmatch(
        r"move-result-object (v\d+)", non_nop[copy_index + 1][1]
    )
    require(snapshot_result is not None, "snapshot copy result is not consumed immediately")
    state_stores = [
        (pc, operation) for pc, operation in instructions
        if re.fullmatch(
            r"sput-object v\d+, "
            r"Lcom/finduas/ridobserver/ProbeSessionCoordinator;\.state:"
            r"Lcom/finduas/ridobserver/ProbeSessionSnapshot;",
            operation,
        ) is not None
    ]
    require(len(state_stores) == 1,
            "completion caller has multiple/zero retained snapshot stores")
    require(
        non_nop[copy_index + 2][1] == (
            f"sput-object {snapshot_result.group(1)}, "
            "Lcom/finduas/ridobserver/ProbeSessionCoordinator;.state:"
            "Lcom/finduas/ridobserver/ProbeSessionSnapshot;"
        ),
        "final snapshot is not stored in ProbeSessionCoordinator.state",
    )
    require(state_stores[0][0] == non_nop[copy_index + 2][0],
            "retained snapshot store is not the completion copy result")


def application_dex_dump(dex_dump: str) -> str:
    blocks = [
        block
        for block in re.split(r"\n(?=Class #\d+\s+-)", dex_dump)
        if "Class descriptor  : 'Lcom/finduas/ridobserver/" in block
    ]
    require(bool(blocks), "could not isolate application DEX classes")
    return "\n".join(blocks)


def app_class_blocks(app_dump: str) -> list[tuple[str, str]]:
    result = []
    for block in re.split(r"\n(?=Class #\d+\s+-)", app_dump):
        descriptor = re.search(r"Class descriptor  : '(L[^']+;)'", block)
        require(descriptor is not None, "application DEX class boundary is missing")
        result.append((descriptor.group(1), block))
    require(len({descriptor for descriptor, _ in result}) == len(result),
            "application DEX repeats a class descriptor")
    return result


def owned_family_fingerprint(app_dump: str, prefix: str) -> tuple[tuple[str, ...], str]:
    """Pin the reviewed writer's fields, literals, instructions and control flow.

    This is deliberately stronger than an invoke-table hash: changing a URI,
    primary-volume fallback, branch or buffer source must require fresh review.
    The existing general semantic completion proofs remain independent.
    """
    family = sorted(
        (descriptor, block)
        for descriptor, block in app_class_blocks(app_dump)
        if descriptor == prefix + ";" or descriptor.startswith(prefix + "$")
    )
    require(bool(family), f"reviewed DEX class family missing: {prefix}")
    canonical = "\n".join(
        descriptor + "\n" + block.strip() for descriptor, block in family
    ).encode("utf-8")
    return tuple(descriptor for descriptor, _ in family), hashlib.sha256(canonical).hexdigest()


def report_dex_fingerprint(app_dump: str) -> tuple[tuple[str, ...], str]:
    return owned_family_fingerprint(app_dump, REPORT_DESCRIPTOR)


def external_invoke_fingerprint(app_dump: str) -> tuple[int, str]:
    targets = re.findall(
        r"\|[0-9a-f]{4}:\s+invoke-[^\n]+?, "
        r"(L[^ \n]+?;\.[^:\s]+:[^ \n]+)", app_dump,
    )
    targets = [target for target in targets if not target.startswith("Lcom/finduas/ridobserver/")]
    return len(targets), hashlib.sha256("\n".join(sorted(targets)).encode("utf-8")).hexdigest()


REPORT_WRITE_OWNER = REPORT_DESCRIPTOR + "$AndroidStore;"
REPORT_WRITE_CALLS = frozenset({
    "Landroid/content/ContentResolver;.insert:(Landroid/net/Uri;Landroid/content/ContentValues;)Landroid/net/Uri;",
    "Landroid/content/ContentResolver;.openOutputStream:(Landroid/net/Uri;Ljava/lang/String;)Ljava/io/OutputStream;",
    "Landroid/content/ContentResolver;.update:(Landroid/net/Uri;Landroid/content/ContentValues;Ljava/lang/String;[Ljava/lang/String;)I",
    "Landroid/content/ContentResolver;.delete:(Landroid/net/Uri;Ljava/lang/String;[Ljava/lang/String;)I",
    "Ljava/io/OutputStream;.write:([B)V",
    "Ljava/io/OutputStream;.flush:()V",
})
# Source-reviewed fixed writer. The separate final-DEX family freeze below must
# also match before any v12 artifact can pass; no general ZIP/file API is opened.
SAMPLE_WRITE_CALLS = {
    SAMPLE_DESCRIPTOR + "$AndroidStore;": frozenset(
        call for call in REPORT_WRITE_CALLS if call.startswith("Landroid/content/ContentResolver;")
    ),
    SAMPLE_DESCRIPTOR + ";": frozenset({
        "Ljava/util/zip/ZipOutputStream;.<init>:(Ljava/io/OutputStream;)V",
        "Ljava/util/zip/ZipOutputStream;.setLevel:(I)V",
        "Ljava/util/zip/ZipOutputStream;.putNextEntry:(Ljava/util/zip/ZipEntry;)V",
        "Ljava/util/zip/ZipOutputStream;.write:([BII)V",
        "Ljava/util/zip/ZipOutputStream;.write:([B)V",
        "Ljava/util/zip/ZipOutputStream;.closeEntry:()V",
    }),
}


def audit_app_dex_safety(
    app_dump: str, *, enforce_frozen_surface: bool = True, profile: str = CURRENT_PROFILE
) -> None:
    """No execution/transmission; only the version's exact reviewed output owners."""
    forbidden_exact = (
        "Ljava/io/FileOutputStream;", "Ljava/io/FileWriter;",
        "Ljava/io/OutputStreamWriter;", "Ljava/io/BufferedWriter;",
        "Ljava/io/PrintWriter;", "Ljava/io/DataOutputStream;",
        "Ljava/io/ObjectOutputStream;",
        "Ljava/net/Socket;", "Ljava/net/ServerSocket;", "Ljava/net/DatagramSocket;",
        "Landroid/os/Parcel;", "Ldalvik/system/DexFile;", "Ldalvik/system/VMDebug;",
        "attachJvmtiAgent", "Ljava/lang/System;.load:",
        "Ljava/lang/System;.loadLibrary:", "Ljava/lang/Runtime;.load:",
        "Ljava/lang/Runtime;.loadLibrary:",
    )
    for forbidden in forbidden_exact:
        require(forbidden not in app_dump,
                f"application DEX invokes forbidden surface: {forbidden}")
    for owner, block in app_class_blocks(app_dump):
        if "Ljava/util/zip/ZipOutputStream;" in block:
            require(profile == "v12" and owner == SAMPLE_DESCRIPTOR + ";",
                    "ZIP output is outside the fixed sample exporter")

    forbidden_calls = (
        r"Lkotlin/io/FilesKt[^;]*;\.(?:writeText|writeBytes|appendText|appendBytes|"
        r"outputStream|bufferedWriter|printWriter)(?:\$default)?:",
        r"Ljava/nio/file/Files;\.(?:write|newOutputStream|newBufferedWriter|copy|move|"
        r"delete|deleteIfExists|createFile|createDirectory|createDirectories):",
        r"Landroid/system/Os;\.(?:write|pwrite|writev|socket|connect|sendto|sendmsg|"
        r"bind|listen|accept):",
        r"Landroid/content/Context;\.openFileOutput:",
        r"Ljava/io/File;\.(?:delete|renameTo|mkdir|mkdirs|createNewFile):",
    )
    for pattern in forbidden_calls:
        require(re.search(pattern, app_dump) is None,
                f"application DEX invokes forbidden write/send call: {pattern}")

    scoped_writes = re.compile(
        r"(?:Landroid/content/ContentResolver;\.(?:openOutputStream|insert|update|delete)|"
        r"Ljava/io/[^;]*(?:OutputStream|Writer);\.(?:write|append|flush|close)|"
        r"Ljava/util/zip/ZipOutputStream;\.[^:]+):"
    )
    for owner, block in app_class_blocks(app_dump):
        for _, operation in dex_instructions(block):
            if not scoped_writes.search(operation):
                continue
            target = operation.split(", ", 1)[-1] if "}, " not in operation else operation.split("}, ", 1)[1]
            report_allowed = (profile in ("v11", "v12") and owner == REPORT_WRITE_OWNER
                              and target in REPORT_WRITE_CALLS)
            sample_allowed = (profile == "v12" and target in SAMPLE_WRITE_CALLS.get(owner, ()))
            require(report_allowed or sample_allowed,
                    f"write call is outside the exact output exceptions: {owner}: {target}")
    selected = PROFILES[profile]
    if profile in ("v11", "v12"):
        descriptors, digest = report_dex_fingerprint(app_dump)
        require(selected["report_descriptors"] is not None and selected["report_dex_sha256"] is not None,
                f"{profile} report DEX has not completed manual safety review")
        require(descriptors == selected["report_descriptors"],
                "report writer class family changed")
        require(digest == selected["report_dex_sha256"],
                "reviewed report writer DEX/literals/control flow changed")
    if profile == "v12":
        descriptors, digest = owned_family_fingerprint(app_dump, SAMPLE_DESCRIPTOR)
        require(selected["sample_descriptors"] is not None and selected["sample_dex_sha256"] is not None,
                "v12 sample DEX has not completed manual safety review")
        require(descriptors == selected["sample_descriptors"], "sample exporter class family changed")
        require(digest == selected["sample_dex_sha256"],
                "reviewed fixed sample exporter DEX/literals/control flow changed")
    if enforce_frozen_surface:
        count, digest = external_invoke_fingerprint(app_dump)
        selected = PROFILES[profile]
        require(selected["external_count"] is not None and selected["external_sha256"] is not None,
                f"{profile} external invoke surface has not completed manual safety review")
        require(
            count == selected["external_count"],
            "application external invoke count changed",
        )
        require(
            digest == selected["external_sha256"],
            "application external invoke surface changed",
        )


def audit_completion_gate_dex_dump(dex_dump: str) -> None:
    """Proves final DEX COMPLETE control flow and its real ART-result call site."""
    policy_class = dex_class_block(
        dex_dump,
        "Lcom/finduas/ridobserver/ProbeCompletionPolicy;",
    )
    method = dex_method_block(policy_class, "terminalState")
    require(
        "type          : "
        "'(ZZLcom/finduas/ridobserver/ArtIdentityState;)"
        "Lcom/finduas/ridobserver/ProbeRunState;'" in method,
        "completion gate DEX signature changed",
    )
    protocol_register = local_register(method, "protocolBinderCompleted", "Z")
    bridge_register = local_register(method, "localBridgeCompleted", "Z")
    art_register = local_register(
        method,
        "artIdentityState",
        "Lcom/finduas/ridobserver/ArtIdentityState;",
    )
    instructions = [(pc, op) for pc, op in dex_instructions(method) if op != "nop"]
    gate_start = next(
        (
            index for index, (_, operation) in enumerate(instructions)
            if operation.startswith(f"if-eqz {protocol_register}, ")
        ),
        -1,
    )
    require(gate_start >= 0, "completion DEX does not branch on protocol completion")
    gate = instructions[gate_start:]
    require(len(gate) == 8, "completion DEX has unexpected control-flow instructions")

    protocol_branch = re.fullmatch(
        rf"if-eqz {re.escape(protocol_register)}, ([0-9a-f]{{4}})", gate[0][1]
    )
    bridge_branch = re.fullmatch(
        rf"if-eqz {re.escape(bridge_register)}, ([0-9a-f]{{4}})", gate[1][1]
    )
    art_complete_load = re.fullmatch(
        r"sget-object (v\d+), "
        r"Lcom/finduas/ridobserver/ArtIdentityState;\.COMPLETE:"
        r"Lcom/finduas/ridobserver/ArtIdentityState;",
        gate[2][1],
    )
    require(protocol_branch is not None, "protocol completion branch mutated")
    require(bridge_branch is not None, "local bridge completion branch mutated")
    require(art_complete_load is not None, "ART COMPLETE identity load mutated")
    art_complete_register = art_complete_load.group(1)
    art_branch = re.fullmatch(
        rf"if-ne {re.escape(art_register)}, {re.escape(art_complete_register)}, "
        r"([0-9a-f]{4})",
        gate[3][1],
    )
    complete_load = re.fullmatch(
        r"sget-object (v\d+), "
        r"Lcom/finduas/ridobserver/ProbeRunState;\.COMPLETE:"
        r"Lcom/finduas/ridobserver/ProbeRunState;",
        gate[4][1],
    )
    goto_return = re.fullmatch(r"goto ([0-9a-f]{4})", gate[5][1])
    incomplete_load = re.fullmatch(
        r"sget-object (v\d+), "
        r"Lcom/finduas/ridobserver/ProbeRunState;\.INCOMPLETE:"
        r"Lcom/finduas/ridobserver/ProbeRunState;",
        gate[6][1],
    )
    require(art_branch is not None, "ART completion comparison mutated")
    require(complete_load is not None, "ProbeRunState.COMPLETE load mutated")
    require(goto_return is not None, "completion return jump mutated")
    require(incomplete_load is not None, "ProbeRunState.INCOMPLETE load mutated")
    return_object = re.fullmatch(r"return-object (v\d+)", gate[7][1])
    require(return_object is not None, "completion return mutated")

    incomplete_pc = gate[6][0]
    return_pc = gate[7][0]
    branch_targets = {
        int(protocol_branch.group(1), 16),
        int(bridge_branch.group(1), 16),
        int(art_branch.group(1), 16),
    }
    require(branch_targets == {incomplete_pc}, "a completion rejection bypasses INCOMPLETE")
    require(int(goto_return.group(1), 16) == return_pc, "COMPLETE jump misses return")
    result_registers = {
        complete_load.group(1), incomplete_load.group(1), return_object.group(1)
    }
    require(len(result_registers) == 1, "completion paths do not share the returned register")
    require(method.count("ProbeRunState;.COMPLETE:") == 1,
            "completion DEX contains multiple COMPLETE loads")

    call_needle = (
        "Lcom/finduas/ridobserver/ProbeCompletionPolicy;.terminalState:"
        "(ZZLcom/finduas/ridobserver/ArtIdentityState;)"
        "Lcom/finduas/ridobserver/ProbeRunState;"
    )
    require(dex_dump.count(call_needle) == 1, "completion gate must have one DEX call site")
    call_offset = dex_dump.find(call_needle)
    caller_start = dex_dump.rfind("Class descriptor  : '", 0, call_offset)
    require(caller_start >= 0, "completion call-site class could not be isolated")
    caller_end = dex_dump.find("\nClass #", call_offset)
    caller_class = (
        dex_dump[caller_start:] if caller_end < 0 else dex_dump[caller_start:caller_end]
    )
    caller = dex_enclosing_method_block(caller_class, call_needle)
    (
        next_protocol_register,
        next_protocol_start,
        next_protocol_end,
    ) = local_register_lifetime(caller, "nextProtocolCompleted", "Z")
    (
        next_bridge_register,
        next_bridge_start,
        next_bridge_end,
    ) = local_register_lifetime(caller, "nextLocalBridgeCompleted", "Z")
    next_art_register, next_art_start, next_art_end = local_register_lifetime(
        caller,
        "nextArtIdentity",
        "Lcom/finduas/ridobserver/AndroidArtIdentityResult;",
    )
    caller_instructions = [(pc, op) for pc, op in dex_instructions(caller) if op != "nop"]
    calls = [
        index for index, (_, operation) in enumerate(caller_instructions)
        if call_needle in operation
    ]
    require(len(calls) == 1 and calls[0] >= 2, "completion call instruction is ambiguous")
    call_index = calls[0]
    state_get = re.fullmatch(
        rf"invoke-virtual \{{{re.escape(next_art_register)}\}}, "
        r"Lcom/finduas/ridobserver/AndroidArtIdentityResult;\.getState:"
        r"\(\)Lcom/finduas/ridobserver/ArtIdentityState;",
        caller_instructions[call_index - 2][1],
    )
    state_move = re.fullmatch(
        r"move-result-object (v\d+)", caller_instructions[call_index - 1][1]
    )
    require(state_get is not None and state_move is not None,
            "completion call is not immediately fed by nextArtIdentity.getState()")
    call_match = re.fullmatch(
        r"invoke-virtual \{(v\d+), (v\d+), (v\d+), (v\d+)\}, "
        + re.escape(call_needle),
        caller_instructions[call_index][1],
    )
    require(call_match is not None, "completion call register shape changed")
    require(call_match.group(2) == next_protocol_register,
            "completion call does not use nextProtocolCompleted")
    require(call_match.group(3) == next_bridge_register,
            "completion call does not use nextLocalBridgeCompleted")
    require(call_match.group(4) == state_move.group(1),
            "completion call does not use the observed ART result state")
    state_get_pc = caller_instructions[call_index - 2][0]
    completion_call_pc = caller_instructions[call_index][0]
    audit_completion_flag_provenance(
        caller,
        completion_call_pc,
        next_protocol_register,
        next_protocol_start,
        next_protocol_end,
        "Lcom/finduas/ridobserver/ProtocolBinderProbe;.runOnce:()"
        "Lcom/finduas/ridobserver/ProtocolBinderProbeResult;",
        "protocol",
    )
    audit_completion_flag_provenance(
        caller,
        completion_call_pc,
        next_bridge_register,
        next_bridge_start,
        next_bridge_end,
        "Lcom/finduas/ridobserver/LocalBridgeProbe;.run:(Landroid/content/Context;)"
        "Lcom/finduas/ridobserver/LocalBridgeProbeResult;",
        "local bridge",
    )
    audit_art_identity_provenance(
        caller,
        state_get_pc,
        next_art_register,
        next_art_start,
        next_art_end,
    )
    audit_completion_result_storage(caller, completion_call_pc)


def audit_apk(apk: Path, profile: str = CURRENT_PROFILE) -> tuple[int, str]:
    selected = PROFILES[profile]
    require(apk.is_file(), f"APK missing: {apk}")
    apk_size = apk.stat().st_size
    apk_sha = sha256(apk)
    if SEALED_PROFILE:
        require(selected["sealed_size"] is not None and selected["sealed_sha256"] is not None,
                f"{profile} does not have a sealed artifact profile")
        require(apk_size == selected["sealed_size"], f"{profile} artifact size changed")
        require(apk_sha == selected["sealed_sha256"], f"{profile} artifact hash changed")

    badging = run(tool("aapt"), "dump", "badging", apk)
    require("name='com.finduas.ridobserver'" in badging, "application ID mismatch")
    require(f"versionCode='{selected['version_code']}'" in badging, "packaged versionCode mismatch")
    require(f"versionName='{selected['version_name']}'" in badging, "packaged versionName mismatch")
    require("launchable-activity: name='com.finduas.ridobserver.MainActivity'" in badging,
            "launcher Activity mismatch")
    require("uses-permission:" not in badging, "packaged APK requests a permission")

    xmltree = run(tool("aapt"), "dump", "xmltree", apk, "AndroidManifest.xml")
    require(xmltree.count("E: activity ") == 1, "APK must contain exactly one Activity")
    for component in ("service", "receiver", "provider"):
        require(f"E: {component} " not in xmltree, f"APK contains a {component}")
    require("uses-permission" not in xmltree, "manifest tree contains permission")

    with zipfile.ZipFile(apk) as archive:
        names = archive.namelist()
        require(not any(name.startswith("lib/") or name.endswith(".so") for name in names),
                "APK packages a native library")
        dex_names = sorted(name for name in names if re.fullmatch(r"classes\d*\.dex", name))
        require(bool(dex_names), "APK has no DEX")
        dex = b"".join(archive.read(name) for name in dex_names)

    for required in (
        b"Lcom/finduas/ridobserver/AndroidArtIdentityProbe;",
        b"Lcom/finduas/ridobserver/ElfBuildIdReader;",
        b"Lcom/finduas/ridobserver/ArtMapsParser;",
        selected["schema"].encode("utf-8"),
        b"/proc/self/maps",
        b"3ec3d232ad7f4099c42f014b87658be47e83d7e21a7a053fb16c4d146103745d",
        b"5f839ecc60b9ae39764305b5fee6ed37",
        b"android.settings.APPLICATION_DEVELOPMENT_SETTINGS",
        b"android.settings.DEVICE_INFO_SETTINGS",
        b"android.settings.SETTINGS",
        b"art.agent_unload_range.offset",
        b"art.runtime_attach_agent_range.offset",
    ):
        require(required in dex, f"DEX misses required probe marker: {required!r}")
    if profile in ("v11", "v12"):
        require(selected["version_name"].encode("utf-8") in dex, "DEX misses app version marker")
    for forbidden_schema in (b"art.attach_range.", b"art.loader_range."):
        require(forbidden_schema not in dex,
                f"DEX retains a misnamed range field: {forbidden_schema!r}")
    for forbidden in (
        b"Lcom/finduas/ridobserver/ObserverService;",
        b"Lcom/finduas/ridobserver/PassiveWireEngine;",
        b"Lcom/finduas/ridobserver/RidProtocol;",
        b"Ljava/net/Socket;",
        b"Ljava/net/ServerSocket;",
        b"Ljava/net/DatagramSocket;",
        b"Landroid/os/Parcel;",
        b"Ldalvik/system/DexFile;",
        b"Ldalvik/system/VMDebug;",
        b"attachJvmtiAgent",
        b"loadLibrary",
    ):
        require(forbidden not in dex, f"DEX contains forbidden surface: {forbidden!r}")

    dex_dump = run(tool("dexdump"), "-d", apk)
    audit_completion_gate_dex_dump(dex_dump)
    app_dump = application_dex_dump(dex_dump)
    audit_app_dex_safety(app_dump, profile=profile)
    require(app_dump.count(".startActivity:(Landroid/content/Intent;)V") == 1,
            "application DEX does not have exactly one Activity launch site")
    require(app_dump.count("Landroid/content/Intent;.<init>:(Ljava/lang/String;)V") == 1,
            "application DEX does not have exactly one action-only Intent constructor")
    for forbidden_launch in (".setPackage:", ".setComponent:", ".setData:", ".putExtra:"):
        require(forbidden_launch not in app_dump,
                f"application DEX contains a parameterized launch API: {forbidden_launch}")
    for fixed_action in (
        b"android.settings.DEVICE_INFO_SETTINGS",
        b"android.settings.APPLICATION_DEVELOPMENT_SETTINGS",
        b"android.settings.SETTINGS",
    ):
        require(dex.count(fixed_action) == 1,
                f"fixed Settings action count changed: {fixed_action!r}")

    verify = run(tool("apksigner"), "verify", "--verbose", "--print-certs", apk)
    require("Verified using v2 scheme (APK Signature Scheme v2): true" in verify,
            "APK signature v2 did not verify")
    signer_match = re.search(r"Signer #1 certificate SHA-256 digest: ([0-9a-fA-F]+)", verify)
    require(signer_match is not None, "signer certificate digest missing")
    if SEALED_PROFILE:
        require(signer_match.group(1).lower() == EXPECTED_SIGNER, "signer certificate changed")
    alignment = run(tool("zipalign"), "-c", "-v", "4", apk)
    require(
        "Verification successful" in alignment or "Verification succesful" in alignment,
        "zipalign verification failed",
    )
    return apk_size, apk_sha


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=tuple(PROFILES), default=CURRENT_PROFILE)
    parser.add_argument("apk", type=Path, nargs="?")
    args = parser.parse_args()
    profile = args.profile
    default_name = "FindUAS-RID-Bridge-Probe-" + PROFILES[profile]["version_name"] + ".apk"
    apk = (args.apk or PROJECT / "dist" / default_name).resolve()
    try:
        if SEALED_PROFILE:
            audit_prior_artifacts()
            audit_known_profile_source()
        # A historical artifact is checked against its own immutable final-DEX
        # profile. The current checkout is not claimed to be its source.
        if profile == CURRENT_PROFILE:
            audit_sources(profile=profile)
        size, digest = audit_apk(apk, profile=profile)
    except AuditFailure as error:
        print(f"AUDIT_FAIL: {error}", file=sys.stderr)
        return 1
    print("AUDIT_PASS")
    print(f"artifact={apk}")
    print(f"bytes={size}")
    print(f"sha256={digest}")
    mode = "sealed" if SEALED_PROFILE else ("source-only" if profile == CURRENT_PROFILE else "artifact-only")
    print(f"audit_profile={profile}:{mode}")
    print(f"external_invoke_count={PROFILES[profile]['external_count']}")
    print(f"external_invoke_sha256={PROFILES[profile]['external_sha256']}")
    if profile in ("v11", "v12"):
        print(f"report_source_sha256={PROFILES[profile]['report_source_sha256']}")
        print(f"report_dex_sha256={PROFILES[profile]['report_dex_sha256']}")
    if profile == "v12":
        print(f"sample_source_sha256={PROFILES[profile]['sample_source_sha256']}")
        print(f"sample_dex_sha256={PROFILES[profile]['sample_dex_sha256']}")
    if profile != CURRENT_PROFILE:
        print("source_review=historical_artifact_only_not_current_checkout")
    if SEALED_PROFILE:
        for prior_apk, _, prior_sha256 in SEALED_PRIOR_APKS:
            print(f"sealed_{prior_apk.stem}_sha256={prior_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
