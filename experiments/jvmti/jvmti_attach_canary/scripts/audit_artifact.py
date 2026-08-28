#!/usr/bin/env python3
"""Fail-closed audit for the FindUAS Android 11 JVMTI attach canary carrier."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


DJI_PLATFORM_CERT_SHA256 = (
    "a4aa1cdd2ea580cbbe67486b5f6f3cfea83f488889995afa70793daa516687da"
)
EXPECTED_SIGNER_CERT_SHA256 = (
    "37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224"
)
AOSP_JVMTI_HEADER_SHA256 = (
    "229d8607d191a3d7815a887ca32d79da11ffa85b4cb16a43b6a01dbb0929d08d"
)
EXPECTED_PACKAGE = "com.finduas.jvmti.canary.carrier"
EXPECTED_NATIVE_ENTRY = "lib/arm64-v8a/libfinduas_jvmti_canary.so"
EXPECTED_ZIP_ENTRIES = {
    "META-INF/com/android/build/gradle/app-metadata.properties",
    "AndroidManifest.xml",
    "resources.arsc",
    EXPECTED_NATIVE_ENTRY,
}
EXPECTED_NEEDED = {"liblog.so", "libc.so"}
EXPECTED_UNDEFINED = {"__android_log_print", "__stack_chk_fail"}


class AuditFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditFailure(message)


def run_checked(command: list[str]) -> str:
    completed = subprocess.run(command, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        raise AuditFailure(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stdout}{completed.stderr}"
        )
    return completed.stdout + completed.stderr


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def configure_java_runtime() -> None:
    candidates = (
        os.environ.get("FINDUAS_CANARY_JAVA_HOME"),
        os.environ.get("JAVA_HOME"),
    )
    for candidate in candidates:
        if not candidate:
            continue
        java_home = Path(candidate).expanduser().resolve()
        java_binary = java_home / "bin/java"
        if java_binary.is_file():
            os.environ["JAVA_HOME"] = str(java_home)
            os.environ["PATH"] = f"{java_home / 'bin'}:{os.environ.get('PATH', '')}"
            return
    raise AuditFailure(
        "no usable Java runtime; set FINDUAS_CANARY_JAVA_HOME or JAVA_HOME"
    )


def dynamic_symbol_names(output: str) -> set[str]:
    names: set[str] = set()
    for line in output.splitlines():
        fields = line.split()
        if fields:
            names.add(fields[-1].split("@", 1)[0])
    return names


def audit_native_source(project_dir: Path) -> None:
    cpp_dir = project_dir / "app/src/main/cpp"
    source_path = cpp_dir / "canary.c"
    source = source_path.read_text(encoding="utf-8")

    native_sources = sorted(
        path.relative_to(cpp_dir).as_posix()
        for path in cpp_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".c", ".cc", ".cpp", ".s", ".asm"}
    )
    require(native_sources == ["canary.c"], f"unexpected native source set: {native_sources}")

    cmake = (cpp_dir / "CMakeLists.txt").read_text(encoding="utf-8")
    require(
        len(re.findall(r"\badd_library\s*\(", cmake)) == 1
        and re.search(
            r"add_library\s*\(\s*finduas_jvmti_canary\s+SHARED\s+canary\.c\s*\)",
            cmake,
        )
        is not None,
        "CMake native target is not the exact single-source canary",
    )
    require("target_sources" not in cmake, "CMake adds an unreviewed native source")

    forbidden_patterns = {
        "JVMTI capability/event/mutation API": (
            r"\b(?:AddCapabilities|RelinquishCapabilities|SetEventNotificationMode|"
            r"SetEventCallbacks|GenerateEvents|RedefineClasses|RetransformClasses|"
            r"SetBreakpoint|SetFieldModificationWatch|SetFieldAccessWatch|ForceGarbageCollection)\b"
        ),
        "JNI target method invocation": r"\bCall(?:Static|Nonvirtual)?[A-Za-z0-9_]*Method[A-Za-z0-9_]*\b",
        "native loading or injection": r"\b(?:dlopen|dlsym|ptrace)\s*\(",
        "network API": r"\b(?:socket|connect|bind|listen|accept|send|recv|sendto|recvfrom)\s*\(",
        "filesystem API": r"\b(?:open|openat|creat|fopen|freopen|write|pwrite|rename|unlink|mkdir)\s*\(",
        "property API": r"\b(?:__system_property_set|property_set|SystemProperties)\b",
        "process API": r"\b(?:fork|vfork|execve|execl|execvp|system|popen|kill)\s*\(",
        "lifecycle callback other than attach": r"\b(?:JNI_OnLoad|Agent_OnLoad|Agent_OnUnload)\b",
        "native constructor": r"__attribute__\s*\(\(\s*constructor\s*\)\)",
        "inline assembly or embedded binary": r"\b(?:asm|__asm__)\b|\.incbin|\bsvc\s+#|\bsyscall\b",
        "DJI command path": r"\b(?:DUML|EIDSwitchSet|performAction|setValue)\b",
    }
    for label, pattern in forbidden_patterns.items():
        require(re.search(pattern, source) is None, f"native source contains forbidden {label}")

    require(
        set(re.findall(r"\(\*jvmti\)->([A-Za-z0-9_]+)", source))
        == {"GetVersionNumber", "DisposeEnvironment"},
        "JVMTI call set is not the exact read-only allowlist",
    )
    require(
        source.count("DisposeEnvironment") == 2,
        "every post-GetEnv result path must dispose the JVMTI environment",
    )
    require(
        set(re.findall(r"\(\*vm\)->([A-Za-z0-9_]+)", source)) == {"GetEnv"},
        "JavaVM call set is not the exact GetEnv allowlist",
    )
    require("JNIEnv" not in source, "native source must not obtain or use JNIEnv")
    require(source.count("__android_log_print") == 1, "expected exactly one fixed logging call")
    require("%s" not in source and "%p" not in source, "logging must not accept strings or pointers")
    require("Agent_OnAttach" in source, "Agent_OnAttach is missing")
    require("GetClassSignature" not in source, "class signature access is forbidden in V0")
    require("GetLoadedClasses" not in source, "loaded-class enumeration is forbidden in V0")
    for class_marker in ("dji/go/v5", "KeyManager", "KeyEIDSwitch", "RemoteID", "RemoteId"):
        require(class_marker not in source, f"class-name marker is forbidden in V0: {class_marker}")

    header_path = (
        project_dir
        / "app/src/main/cpp/third_party/aosp_android_11_jvmti/jvmti.h"
    )
    require(
        sha256_file(header_path) == AOSP_JVMTI_HEADER_SHA256,
        "vendored Android 11 JVMTI header differs from the pinned AOSP source",
    )


def audit_manifest(aapt: Path, apk: Path) -> None:
    manifest = run_checked([str(aapt), "dump", "xmltree", str(apk), "AndroidManifest.xml"])
    require(f'package="{EXPECTED_PACKAGE}"' in manifest, "unexpected package name")
    require("android:minSdkVersion" in manifest and "0x1e" in manifest, "minSdk 30 missing")
    require("android:targetSdkVersion" in manifest, "targetSdk missing")
    require(
        re.search(r"android:hasCode[^\n]*0x0(?:\s|$)", manifest) is not None,
        "android:hasCode is not false",
    )
    require(
        re.search(r"android:extractNativeLibs[^\n]*0xffffffff(?:\s|$)", manifest) is not None,
        "android:extractNativeLibs is not true",
    )
    require("E: uses-permission" not in manifest, "manifest declares a permission")
    require("android:sharedUserId" not in manifest, "manifest requests a shared UID")
    for component in ("activity", "service", "receiver", "provider", "instrumentation"):
        require(f"E: {component}" not in manifest, f"manifest declares {component}")


def audit_elf(ndk_bin: Path, library_path: Path) -> None:
    readelf = ndk_bin / "llvm-readelf"
    nm = ndk_bin / "llvm-nm"
    strings = ndk_bin / "llvm-strings"

    header = run_checked([str(readelf), "-h", str(library_path)])
    require("Class:                             ELF64" in header, "native library is not ELF64")
    require("Machine:                           AArch64" in header, "native library is not AArch64")

    dynamic = run_checked([str(readelf), "-d", str(library_path)])
    needed = set(re.findall(r"Shared library: \[([^]]+)\]", dynamic))
    require(needed == EXPECTED_NEEDED, f"unexpected DT_NEEDED set: {sorted(needed)}")
    require("(INIT)" not in dynamic and "(INIT_ARRAY)" not in dynamic, "constructor table present")

    defined = dynamic_symbol_names(
        run_checked([str(nm), "-D", "--defined-only", "--extern-only", str(library_path)])
    )
    require(defined == {"Agent_OnAttach"}, f"unexpected exported symbol set: {sorted(defined)}")

    undefined = dynamic_symbol_names(
        run_checked([str(nm), "-D", "--undefined-only", str(library_path)])
    )
    require(
        undefined == EXPECTED_UNDEFINED,
        f"unexpected imported symbol set: {sorted(undefined)}",
    )

    printable = run_checked([str(strings), "-a", str(library_path)])
    for forbidden in (
        "DUML",
        "EIDSwitchSet",
        "performAction",
        "setValue",
        "127.0.0.1",
        "/data/",
        "/sdcard/",
        "/proc/",
        "40007",
        "40009",
    ):
        require(forbidden not in printable, f"forbidden native string present: {forbidden}")


def audit_apk(apk: Path, project_dir: Path, sdk_root: Path, ndk_root: Path) -> None:
    require(apk.is_file(), f"APK does not exist: {apk}")
    aapt = sdk_root / "build-tools/35.0.0/aapt"
    apksigner = sdk_root / "build-tools/35.0.0/apksigner"
    zipalign = sdk_root / "build-tools/35.0.0/zipalign"
    ndk_bin = ndk_root / "toolchains/llvm/prebuilt/darwin-x86_64/bin"
    for tool in (aapt, apksigner, zipalign, ndk_bin / "llvm-readelf"):
        require(tool.exists(), f"missing audit tool: {tool}")

    with zipfile.ZipFile(apk) as archive:
        entries = archive.namelist()
        require(len(entries) == len(set(entries)), "APK contains duplicate ZIP entry names")
        require(set(entries) == EXPECTED_ZIP_ENTRIES, f"unexpected APK ZIP inventory: {entries}")
        require(not any(re.fullmatch(r"classes[0-9]*\.dex", name) for name in entries), "DEX present")
        native_entries = sorted(name for name in entries if name.endswith(".so"))
        require(
            native_entries == [EXPECTED_NATIVE_ENTRY],
            f"unexpected native library inventory: {native_entries}",
        )
        native_info = archive.getinfo(EXPECTED_NATIVE_ENTRY)
        require(
            native_info.compress_type == zipfile.ZIP_DEFLATED,
            "native library is not compressed; extraction behavior is ambiguous",
        )
        library_bytes = archive.read(EXPECTED_NATIVE_ENTRY)

    audit_manifest(aapt, apk)
    run_checked([str(zipalign), "-c", "4", str(apk)])
    signer_output = run_checked([str(apksigner), "verify", "--verbose", "--print-certs", str(apk)])
    require("Verifies" in signer_output, "APK signature verification did not succeed")
    for expected_line in (
        "Verified using v1 scheme (JAR signing): false",
        "Verified using v2 scheme (APK Signature Scheme v2): true",
        "Verified using v3 scheme (APK Signature Scheme v3): false",
        "Verified using v3.1 scheme (APK Signature Scheme v3.1): false",
        "Verified using v4 scheme (APK Signature Scheme v4): false",
        "Verified for SourceStamp: false",
        "Number of signers: 1",
    ):
        require(expected_line in signer_output, f"unexpected APK signing profile: {expected_line}")
    match = re.search(r"certificate SHA-256 digest:\s*([0-9a-fA-F]+)", signer_output)
    require(match is not None, "signer certificate SHA-256 was not reported")
    signer_digest = match.group(1).lower()
    require(signer_digest != DJI_PLATFORM_CERT_SHA256, "carrier unexpectedly uses the DJI platform cert")
    require(
        signer_digest == EXPECTED_SIGNER_CERT_SHA256,
        f"unexpected carrier signer certificate: {signer_digest}",
    )

    apk_digest = sha256_file(apk)
    readme = (project_dir / "README.md").read_text(encoding="utf-8")
    declared_hashes = re.findall(r"SHA-256:\s*([0-9a-f]{64})", readme)
    require(declared_hashes == [apk_digest], "README artifact SHA-256 does not match the APK")

    with tempfile.TemporaryDirectory(prefix="finduas-canary-audit-") as temporary:
        library_path = Path(temporary) / "libfinduas_jvmti_canary.so"
        library_path.write_bytes(library_bytes)
        audit_elf(ndk_bin, library_path)

    print(f"APK SHA-256: {apk_digest}")
    print(f"Signer certificate SHA-256: {signer_digest}")
    print(f"Native entry: {EXPECTED_NATIVE_ENTRY} ({len(library_bytes)} bytes, compressed)")
    print("Manifest: no permissions, no components, no shared UID, extractNativeLibs=true")
    print("DEX: absent")
    print("ELF: AArch64 ELF64; export=Agent_OnAttach; dependencies=liblog.so,libc.so")
    print("Native imports: __android_log_print and compiler hardening __stack_chk_fail")
    print("AUDIT PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("apk", type=Path)
    arguments = parser.parse_args()

    configure_java_runtime()

    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    sdk_setting = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    require(bool(sdk_setting), "set ANDROID_SDK_ROOT or ANDROID_HOME")
    sdk_root = Path(str(sdk_setting)).expanduser().resolve()
    ndk_root = Path(
        os.environ.get("FINDUAS_CANARY_NDK_ROOT")
        or sdk_root / "ndk/27.2.12479018"
    )

    audit_native_source(project_dir)
    audit_apk(arguments.apk.resolve(), project_dir, sdk_root, ndk_root)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditFailure as error:
        print(f"AUDIT FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
