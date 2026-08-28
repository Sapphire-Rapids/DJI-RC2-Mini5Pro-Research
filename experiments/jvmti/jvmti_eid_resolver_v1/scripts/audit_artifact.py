#!/usr/bin/env python3
"""Fail-closed audit for the FindUAS JVMTI EID semantic-anchor resolver V1."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path


EXPECTED_SIGNER_CERT_SHA256 = (
    "37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224"
)
DJI_PLATFORM_CERT_SHA256 = (
    "a4aa1cdd2ea580cbbe67486b5f6f3cfea83f488889995afa70793daa516687da"
)
AOSP_JVMTI_HEADER_SHA256 = (
    "229d8607d191a3d7815a887ca32d79da11ffa85b4cb16a43b6a01dbb0929d08d"
)
EXPECTED_PACKAGE = "com.finduas.jvmti.eidresolver.v1"
EXPECTED_NATIVE_ENTRY = "lib/arm64-v8a/libfinduas_eid_resolver_v1.so"
EXPECTED_ZIP_ENTRIES = {
    "META-INF/com/android/build/gradle/app-metadata.properties",
    "AndroidManifest.xml",
    "resources.arsc",
    EXPECTED_NATIVE_ENTRY,
}
EXPECTED_LOG_TAG = "FindUAS-EID-Resolver-V1"
EXPECTED_LOG_FORMAT = (
    "FINDUAS_EID_RESOLVER_V1 error_code=%d loaded_count=%d on_anchor_count=%d "
    "gate_anchor_count=%d unique_loader_count=%d"
)
EXPECTED_NEEDED = {"liblog.so", "libc.so"}
EXPECTED_UNDEFINED = {"__android_log_print", "__stack_chk_fail"}


class AuditFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditFailure(message)


def configure_java_runtime() -> None:
    candidates = (
        os.environ.get("FINDUAS_RESOLVER_JAVA_HOME"),
        os.environ.get("JAVA_HOME"),
    )
    for candidate in candidates:
        if not candidate:
            continue
        java_home = Path(candidate).expanduser().resolve()
        if (java_home / "bin/java").is_file():
            os.environ["JAVA_HOME"] = str(java_home)
            os.environ["PATH"] = f"{java_home / 'bin'}:{os.environ.get('PATH', '')}"
            return
    raise AuditFailure("no usable Java runtime")


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


def dynamic_symbol_names(output: str) -> set[str]:
    names: set[str] = set()
    for line in output.splitlines():
        fields = line.split()
        if fields:
            names.add(fields[-1].split("@", 1)[0])
    return names


def audit_native_source(project_dir: Path) -> None:
    cpp_dir = project_dir / "app/src/main/cpp"
    source_path = cpp_dir / "resolver.c"
    source = source_path.read_text(encoding="utf-8")

    native_sources = sorted(
        path.relative_to(cpp_dir).as_posix()
        for path in cpp_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".c", ".cc", ".cpp", ".s", ".asm"}
    )
    require(native_sources == ["resolver.c"], f"unexpected native source set: {native_sources}")

    cmake = (cpp_dir / "CMakeLists.txt").read_text(encoding="utf-8")
    require(
        len(re.findall(r"\badd_library\s*\(", cmake)) == 1
        and re.search(
            r"add_library\s*\(\s*finduas_eid_resolver_v1\s+SHARED\s+resolver\.c\s*\)",
            cmake,
        )
        is not None,
        "CMake target is not the exact single-source resolver",
    )
    require("target_sources" not in cmake, "CMake adds an unreviewed source")

    forbidden_patterns = {
        "JVMTI mutation/event API": (
            r"\b(?:AddCapabilities|RelinquishCapabilities|SetEventNotificationMode|"
            r"SetEventCallbacks|GenerateEvents|RedefineClasses|RetransformClasses|"
            r"SetBreakpoint|SetFieldModificationWatch|SetFieldAccessWatch|ForceGarbageCollection)\b"
        ),
        "Java method or field access": (
            r"\b(?:Call(?:Static|Nonvirtual)?[A-Za-z0-9_]*Method[A-Za-z0-9_]*|"
            r"Get(?:Static)?MethodID|Get(?:Static)?FieldID|Get(?:Static)?[A-Za-z0-9_]*Field|"
            r"Set(?:Static)?[A-Za-z0-9_]*Field|FindClass|DefineClass|NewObject|AllocObject|"
            r"RegisterNatives)\b"
        ),
        "native loading or injection": r"\b(?:dlopen|dlsym|ptrace)\s*\(",
        "network API": r"\b(?:socket|connect|bind|listen|accept|send|recv|sendto|recvfrom)\s*\(",
        "filesystem API": r"\b(?:open|openat|creat|fopen|freopen|write|pwrite|rename|unlink|mkdir)\s*\(",
        "property API": r"\b(?:__system_property_set|__system_property_get|property_set|SystemProperties)\b",
        "process API": r"\b(?:fork|vfork|execve|execl|execvp|system|popen|kill)\s*\(",
        "inline assembly or embedded binary": r"\b(?:asm|__asm__)\b|\.incbin|\bsvc\s+#|\bsyscall\b",
        "persistent lifecycle callback": r"\b(?:JNI_OnLoad|Agent_OnLoad|Agent_OnUnload)\b",
        "native constructor": r"__attribute__\s*\(\(\s*constructor\s*\)\)",
        "DJI command/control path": r"\b(?:DUML|EIDSwitch|KeyManager|FlySafe|performAction|setValue)\b",
    }
    for label, pattern in forbidden_patterns.items():
        require(re.search(pattern, source) is None, f"source contains forbidden {label}")

    require(
        set(re.findall(r"\(\*jvmti\)->([A-Za-z0-9_]+)", source))
        == {
            "GetLoadedClasses",
            "GetClassSignature",
            "GetClassLoader",
            "Deallocate",
            "DisposeEnvironment",
        },
        "JVMTI call set differs from resolver allowlist",
    )
    require(
        set(re.findall(r"\(\*vm\)->([A-Za-z0-9_]+)", source)) == {"GetEnv"},
        "JavaVM call set differs from GetEnv",
    )
    require(
        set(re.findall(r"\(\*jni\)->([A-Za-z0-9_]+)", source))
        == {
            "ExceptionCheck",
            "ExceptionClear",
            "DeleteLocalRef",
            "IsSameObject",
            "NewGlobalRef",
            "DeleteGlobalRef",
        },
        "JNI call set differs from reference-management allowlist",
    )
    require(source.count("__android_log_print") == 1, "expected one fixed logging call")
    require("%s" not in source and "%p" not in source, "log format accepts string/pointer")
    require(source.count("RemoteIDModelImpl$electronicIDBroadcastOn$2$1;") == 1, "on anchor mismatch")
    require(source.count("RemoteIDModelImpl$electronicIDBroadcastExisted$2$1;") == 1, "gate anchor mismatch")

    header_path = (
        project_dir.parent
        / "jvmti_attach_canary/app/src/main/cpp/third_party/aosp_android_11_jvmti/jvmti.h"
    )
    require(sha256_file(header_path) == AOSP_JVMTI_HEADER_SHA256, "JVMTI header hash mismatch")


def audit_manifest(aapt: Path, apk: Path) -> None:
    manifest = run_checked([str(aapt), "dump", "xmltree", str(apk), "AndroidManifest.xml"])
    elements = re.findall(r"^\s*E:\s+([^\s(]+)", manifest, flags=re.MULTILINE)
    require(elements == ["manifest", "uses-sdk", "application"], f"unexpected elements: {elements}")
    require(f'package="{EXPECTED_PACKAGE}"' in manifest, "unexpected package")
    for label, pattern in {
        "versionCode 1": r"android:versionCode[^\n]*\(type 0x10\)0x1(?:\s|$)",
        "versionName": r'android:versionName[^\n]*="0\.1\.0-research"',
        "compileSdk 35": r"android:compileSdkVersion[^\n]*\(type 0x10\)0x23(?:\s|$)",
        "compileSdk codename": r'android:compileSdkVersionCodename[^\n]*="15"',
        "minSdk 30": r"android:minSdkVersion[^\n]*\(type 0x10\)0x1e(?:\s|$)",
        "targetSdk 30": r"android:targetSdkVersion[^\n]*\(type 0x10\)0x1e(?:\s|$)",
        "fixed label": r'android:label[^\n]*="FindUAS EID resolver V1 carrier"',
        "hasCode false": r"android:hasCode[^\n]*\(type 0x12\)0x0(?:\s|$)",
        "debuggable true": r"android:debuggable[^\n]*\(type 0x12\)0xffffffff(?:\s|$)",
        "allowBackup false": r"android:allowBackup[^\n]*\(type 0x12\)0x0(?:\s|$)",
        "extractNativeLibs true": (
            r"android:extractNativeLibs[^\n]*\(type 0x12\)0xffffffff(?:\s|$)"
        ),
        "usesCleartextTraffic false": (
            r"android:usesCleartextTraffic[^\n]*\(type 0x12\)0x0(?:\s|$)"
        ),
    }.items():
        require(re.search(pattern, manifest) is not None, f"manifest missing {label}")
    require(
        re.search(r"android:hasCode[^\n]*0x0(?:\s|$)", manifest) is not None,
        "hasCode is not false",
    )
    require(
        re.search(r"android:extractNativeLibs[^\n]*0xffffffff(?:\s|$)", manifest) is not None,
        "extractNativeLibs is not true",
    )
    require("E: uses-permission" not in manifest, "manifest declares permission")
    require("android:sharedUserId" not in manifest, "manifest requests shared UID")
    for component in ("activity", "service", "receiver", "provider", "instrumentation"):
        require(f"E: {component}" not in manifest, f"manifest declares {component}")


def audit_elf(ndk_bin: Path, library_path: Path) -> None:
    readelf = ndk_bin / "llvm-readelf"
    nm = ndk_bin / "llvm-nm"
    strings = ndk_bin / "llvm-strings"

    header = run_checked([str(readelf), "-h", str(library_path)])
    require("Class:                             ELF64" in header, "library is not ELF64")
    require("Machine:                           AArch64" in header, "library is not AArch64")

    dynamic = run_checked([str(readelf), "-d", str(library_path)])
    needed = set(re.findall(r"Shared library: \[([^]]+)\]", dynamic))
    require(needed == EXPECTED_NEEDED, f"unexpected dependencies: {sorted(needed)}")
    require("(INIT)" not in dynamic and "(INIT_ARRAY)" not in dynamic, "constructor table present")

    defined = dynamic_symbol_names(
        run_checked([str(nm), "-D", "--defined-only", "--extern-only", str(library_path)])
    )
    require(defined == {"Agent_OnAttach"}, f"unexpected exports: {sorted(defined)}")

    undefined = dynamic_symbol_names(
        run_checked([str(nm), "-D", "--undefined-only", str(library_path)])
    )
    require(undefined == EXPECTED_UNDEFINED, f"unexpected imports: {sorted(undefined)}")

    printable = run_checked([str(strings), "-a", str(library_path)])
    require(printable.count(EXPECTED_LOG_TAG) == 1, "ELF log tag mismatch")
    require(printable.count(EXPECTED_LOG_FORMAT) == 1, "ELF log format mismatch")
    for required_anchor in (
        "Lcom/uav/flymodel/generated/impl/flight/regulation/"
        "RemoteIDModelImpl$electronicIDBroadcastOn$2$1;",
        "Lcom/uav/flymodel/generated/impl/flight/regulation/"
        "RemoteIDModelImpl$electronicIDBroadcastExisted$2$1;",
    ):
        require(printable.count(required_anchor) == 1, "ELF semantic anchor mismatch")
    require(printable.count("Lcom/") == 2, "ELF contains an unreviewed com.uav class signature")
    for forbidden in (
        "DUML",
        "EIDSwitch",
        "KeyManager",
        "FlySafe",
        "Function0",
        "FlySubject",
        "JNIKeyValue",
        "UAVKey",
        "performAction",
        "setValue",
        "127.0.0.1",
        "/data/",
        "/sdcard/",
        "/proc/",
        "40007",
        "40009",
    ):
        require(forbidden not in printable, f"forbidden ELF string: {forbidden}")


def audit_apk(apk: Path, project_dir: Path, sdk_root: Path, ndk_root: Path) -> None:
    require(apk.is_file(), f"missing APK: {apk}")
    aapt = sdk_root / "build-tools/35.0.0/aapt"
    apksigner = sdk_root / "build-tools/35.0.0/apksigner"
    zipalign = sdk_root / "build-tools/35.0.0/zipalign"
    ndk_bin = ndk_root / "toolchains/llvm/prebuilt/darwin-x86_64/bin"

    with zipfile.ZipFile(apk) as archive:
        entries = archive.namelist()
        require(len(entries) == len(set(entries)), "duplicate ZIP entry")
        require(set(entries) == EXPECTED_ZIP_ENTRIES, f"unexpected ZIP inventory: {entries}")
        native_info = archive.getinfo(EXPECTED_NATIVE_ENTRY)
        require(native_info.compress_type == zipfile.ZIP_DEFLATED, "native library not compressed")
        library_bytes = archive.read(EXPECTED_NATIVE_ENTRY)

    audit_manifest(aapt, apk)
    run_checked([str(zipalign), "-c", "4", str(apk)])
    signer_output = run_checked([str(apksigner), "verify", "--verbose", "--print-certs", str(apk)])
    for expected_line in (
        "Verifies",
        "Verified using v1 scheme (JAR signing): false",
        "Verified using v2 scheme (APK Signature Scheme v2): true",
        "Verified using v3 scheme (APK Signature Scheme v3): false",
        "Verified using v3.1 scheme (APK Signature Scheme v3.1): false",
        "Verified using v4 scheme (APK Signature Scheme v4): false",
        "Verified for SourceStamp: false",
        "Number of signers: 1",
    ):
        require(expected_line in signer_output, f"unexpected signing profile: {expected_line}")
    match = re.search(r"certificate SHA-256 digest:\s*([0-9a-fA-F]+)", signer_output)
    require(match is not None, "signer digest absent")
    signer_digest = match.group(1).lower()
    require(signer_digest == EXPECTED_SIGNER_CERT_SHA256, "unexpected signer")
    require(signer_digest != DJI_PLATFORM_CERT_SHA256, "unexpected DJI platform signer")

    with tempfile.TemporaryDirectory(prefix="finduas-resolver-audit-") as temporary:
        library_path = Path(temporary) / "libfinduas_eid_resolver_v1.so"
        library_path.write_bytes(library_bytes)
        audit_elf(ndk_bin, library_path)

    apk_digest = sha256_file(apk)
    readme = (project_dir / "README.md").read_text(encoding="utf-8")
    declared_hashes = re.findall(r"SHA-256:\s*([0-9a-f]{64})", readme)
    require(declared_hashes == [apk_digest], "README artifact hash disagrees with APK")

    print(f"APK SHA-256: {apk_digest}")
    print(f"Signer certificate SHA-256: {signer_digest}")
    print(f"Native entry: {EXPECTED_NATIVE_ENTRY} ({len(library_bytes)} bytes, compressed)")
    print("Manifest: no permissions, no components, no shared UID, extractNativeLibs=true")
    print("DEX: absent")
    print("ELF: AArch64 ELF64; export=Agent_OnAttach; dependencies=liblog.so,libc.so")
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
        os.environ.get("FINDUAS_RESOLVER_NDK_ROOT")
        or sdk_root / "ndk/27.2.12479018"
    )

    audit_native_source(project_dir)
    audit_apk(arguments.apk.resolve(), project_dir, sdk_root, ndk_root)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditFailure as error:
        print(f"AUDIT FAIL: {error}", file=os.sys.stderr)
        raise SystemExit(1)
