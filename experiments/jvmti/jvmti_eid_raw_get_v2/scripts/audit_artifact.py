#!/usr/bin/env python3
"""Fail-closed audit for the offline FindUAS EID raw GET V2 carrier."""

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
EXPECTED_PACKAGE = "com.finduas.jvmti.eidrawget.v2"
EXPECTED_NATIVE_ENTRY = "lib/arm64-v8a/libfinduas_eid_raw_get_v2.so"
EXPECTED_ZIP_ENTRIES = {
    "META-INF/com/android/build/gradle/app-metadata.properties",
    "AndroidManifest.xml",
    "resources.arsc",
    EXPECTED_NATIVE_ENTRY,
}
EXPECTED_NEEDED = {"liblog.so", "libc.so"}
EXPECTED_UNDEFINED = {
    "__android_log_print",
    "__memset_chk",
    "__stack_chk_fail",
    "clock_gettime",
    "memset",
    "pthread_cond_broadcast",
    "pthread_cond_destroy",
    "pthread_cond_init",
    "pthread_cond_timedwait",
    "pthread_condattr_destroy",
    "pthread_condattr_init",
    "pthread_condattr_setclock",
    "pthread_mutex_destroy",
    "pthread_mutex_init",
    "pthread_mutex_lock",
    "pthread_mutex_unlock",
    "pthread_once",
}
EXPECTED_HELPER_CLASS = "Lcom/finduas/ridv2/RawCallback;"
EXPECTED_HELPER_INTERFACE = "Luav/raw/jni/callback/SendInterface;"
EXPECTED_SEND_DESCRIPTOR = "(IIIIIIZIIIIII[BLuav/raw/jni/callback/SendInterface;)J"


class AuditFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditFailure(message)


def configure_java_runtime() -> None:
    candidates = (
        os.environ.get("FINDUAS_V2_JAVA_HOME"),
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def render_expected_helper_include(data: bytes) -> str:
    rows: list[str] = []
    for offset in range(0, len(data), 12):
        chunk = data[offset : offset + 12]
        rows.append("    " + ", ".join(f"0x{value:02x}" for value in chunk) + ",")
    digest = sha256_bytes(data)
    return "\n".join(
        [
            "#ifndef FINDUAS_EID_RAW_GET_V2_HELPER_DEX_INC",
            "#define FINDUAS_EID_RAW_GET_V2_HELPER_DEX_INC",
            "",
            "static const unsigned char kFinduasRawCallbackDex[] = {",
            *rows,
            "};",
            "static const unsigned int kFinduasRawCallbackDexLength =",
            "    (unsigned int)sizeof(kFinduasRawCallbackDex);",
            f'static const char kFinduasRawCallbackDexSha256[] = "{digest}";',
            "",
            "#endif",
            "",
        ]
    )


def audit_source(project_dir: Path) -> None:
    cpp_dir = project_dir / "app/src/main/cpp"
    cmake = (cpp_dir / "CMakeLists.txt").read_text(encoding="utf-8")
    native_sources = sorted(
        path.name
        for path in cpp_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".c", ".cc", ".cpp", ".s", ".asm"}
    )
    require(
        native_sources == ["agent.c", "jni_bridge.c", "route_snapshot.c", "state.c"],
        f"unexpected native source set: {native_sources}",
    )
    require(
        cmake.count("-mno-outline-atomics") == 1,
        "outline atomics are not disabled exactly once",
    )

    agent = (cpp_dir / "agent.c").read_text(encoding="utf-8")
    bridge = (cpp_dir / "jni_bridge.c").read_text(encoding="utf-8")
    route = (cpp_dir / "route_snapshot.c").read_text(encoding="utf-8")
    helper = (
        project_dir / "helper/src/main/java/com/finduas/ridv2/RawCallback.java"
    ).read_text(encoding="utf-8")
    helper_dex = (project_dir / "build/helper/classes.dex").read_bytes()
    generated_include = (project_dir / "build/generated/helper_dex.inc").read_text(
        encoding="utf-8"
    )
    require(helper_dex.startswith(b"dex\n"), "generated helper input is not DEX")
    require(
        generated_include == render_expected_helper_include(helper_dex),
        "generated helper include is not the exact deterministic DEX wrapper",
    )

    require(
        route.count("return ROUTE_STATUS_UNRESOLVED;") == 1,
        "offline route resolver is not exactly unresolved",
    )
    require("ROUTE_STATUS_RESOLVED" not in route, "route source contains a live resolution path")
    require(route.count("return false;") == 1, "epoch check is not permanently false")
    require("getenv" not in route and "#if" not in route, "route source has a hidden enable path")

    route_resolution_index = agent.find("route_status = route_snapshot_resolve(&route);")
    bridge_call_index = agent.find("bridge_error = jni_bridge_send_once(")
    require(
        route_resolution_index >= 0
        and bridge_call_index >= 0
        and route_resolution_index < bridge_call_index,
        "bridge call is not downstream of route resolution",
    )
    require(
        "if (route_status != ROUTE_STATUS_RESOLVED)" in agent
        and "error = AGENT_ERROR_ROUTE_UNRESOLVED;" in agent,
        "agent lacks unresolved-route hard stop",
    )
    require(
        agent.count("JVMTI_CLASS_STATUS_INITIALIZED") == 1,
        "raw JNI class initialization gate mismatch",
    )
    require(
        agent.count("targets->on_loader, targets->raw_loader") == 1
        and agent.count("targets->on_loader, targets->interface_loader") == 1,
        "raw/interface ClassLoader identity gates are absent",
    )

    require(
        bridge.count("CallStaticLongMethodA") == 1,
        "source does not contain exactly one raw send invocation",
    )
    require(
        bridge.count('"native_SendData"') == 1,
        "native_SendData method lookup count mismatch",
    )
    require(
        bridge.count(EXPECTED_SEND_DESCRIPTOR) == 1,
        "native_SendData descriptor mismatch",
    )
    require(
        re.search(r"send_arguments\[11\]\.i\s*=\s*0\s*;", bridge) is not None,
        "retryTimes is not fixed to zero",
    )
    require(
        re.search(r"const jbyte selector\s*=\s*0x02\s*;", bridge) is not None,
        "France EID GET body is not exactly selector 0x02",
    )
    require(
        bridge.count("attempt_state_note_send_call(attempt)") == 1,
        "single-send atomic guard count mismatch",
    )
    require(
        "snapshot.callback_count != 1u" in bridge
        and "snapshot.duplicate_count != 0u" in bridge
        and "attempt_state_wait_for_quiet_window" in bridge,
        "callback cardinality/quiescence gate is absent",
    )
    require("for (" not in bridge and "while (" not in bridge, "send bridge contains a loop")
    require(
        bridge.count("CallStaticVoidMethodA") == 1
        and bridge.count('"native_CancelSend"') == 1,
        "deadline cleanup is not one cancel-only call site",
    )

    combined = "\n".join(path.read_text(encoding="utf-8") for path in cpp_dir.glob("*.[ch]"))
    require(
        "pthread_condattr_setclock(&condition_attributes, CLOCK_MONOTONIC)" in combined
        and "clock_gettime(condition_clock_id(), &deadline)" in combined,
        "Android monotonic deadline implementation is absent",
    )
    for forbidden in (
        "native_SendDataWithTcpPort",
        "native_RegisterObserver",
        "native_UnregisterObserver",
        "getOrNull",
        "JNIKeyValue",
        "FlySubject",
        "performAction",
        "setValue",
        "SetByteArrayRegion(jni, body, 0, 1, &(jbyte){0x00}",
        "SetByteArrayRegion(jni, body, 0, 1, &(jbyte){0x01}",
        "127.0.0.1",
        "40007",
        "40009",
    ):
        require(forbidden not in combined, f"forbidden control/second-route string: {forbidden}")
    for pattern, label in (
        (r"\b(?:socket|connect|bind|listen|accept|sendto|recvfrom)\s*\(", "network API"),
        (r"\b(?:open|openat|creat|fopen|write|pwrite|rename|unlink)\s*\(", "filesystem API"),
        (r"\b(?:dlopen|dlsym|ptrace)\s*\(", "dynamic injection API"),
        (r"\b(?:fork|vfork|execve|system|popen)\s*\(", "process API"),
    ):
        require(re.search(pattern, combined) is None, f"source contains forbidden {label}")

    require(helper.count("public native void onReceivedData") == 1, "helper response method mismatch")
    require(helper.count("public native void onTimeout") == 1, "helper timeout method mismatch")
    require("static {" not in helper, "helper contains a static initializer")
    require("native_SendData" not in helper, "helper can issue a DJI send")


def audit_helper_dex(dexdump: Path, helper_dex: Path) -> bytes:
    require(helper_dex.is_file(), f"missing helper DEX: {helper_dex}")
    dex_bytes = helper_dex.read_bytes()
    require(dex_bytes.startswith(b"dex\n"), "helper is not a DEX file")
    output = run_checked([str(dexdump), "-d", str(helper_dex)])
    descriptors = re.findall(r"Class descriptor\s+:\s+'([^']+)'", output)
    require(descriptors == [EXPECTED_HELPER_CLASS], f"unexpected DEX definitions: {descriptors}")
    require(EXPECTED_HELPER_INTERFACE in output, "DEX does not reference exact DJI interface")
    require("name          : 'onReceivedData'" in output, "DEX response callback absent")
    require("name          : 'onTimeout'" in output, "DEX timeout callback absent")
    require("name          : '<clinit>'" not in output, "DEX contains a class initializer")
    for forbidden in ("JNIRawData", "native_SendData", "java/io/", "java/net/", "android/os/"):
        require(forbidden not in output, f"helper DEX contains forbidden reference: {forbidden}")
    return dex_bytes


def audit_manifest(aapt: Path, apk: Path) -> None:
    manifest = run_checked([str(aapt), "dump", "xmltree", str(apk), "AndroidManifest.xml"])
    elements = re.findall(r"^\s*E:\s+([^\s(]+)", manifest, flags=re.MULTILINE)
    require(elements == ["manifest", "uses-sdk", "application"], f"unexpected elements: {elements}")
    require(f'package="{EXPECTED_PACKAGE}"' in manifest, "unexpected package")
    for label, pattern in {
        "versionCode 1": r"android:versionCode[^\n]*\(type 0x10\)0x1(?:\s|$)",
        "versionName": r'android:versionName[^\n]*="0\.1\.0-offline-unresolved"',
        "minSdk 30": r"android:minSdkVersion[^\n]*\(type 0x10\)0x1e(?:\s|$)",
        "targetSdk 30": r"android:targetSdkVersion[^\n]*\(type 0x10\)0x1e(?:\s|$)",
        "fixed label": r'android:label[^\n]*="FindUAS EID raw GET V2 offline carrier"',
        "hasCode false": r"android:hasCode[^\n]*\(type 0x12\)0x0(?:\s|$)",
        "debuggable true": r"android:debuggable[^\n]*\(type 0x12\)0xffffffff(?:\s|$)",
        "allowBackup false": r"android:allowBackup[^\n]*\(type 0x12\)0x0(?:\s|$)",
        "extractNativeLibs true": r"android:extractNativeLibs[^\n]*\(type 0x12\)0xffffffff(?:\s|$)",
        "cleartext false": r"android:usesCleartextTraffic[^\n]*\(type 0x12\)0x0(?:\s|$)",
    }.items():
        require(re.search(pattern, manifest) is not None, f"manifest missing {label}")
    require("E: uses-permission" not in manifest, "manifest declares a permission")
    require("android:sharedUserId" not in manifest, "manifest requests a shared UID")
    for component in ("activity", "service", "receiver", "provider", "instrumentation"):
        require(f"E: {component}" not in manifest, f"manifest declares {component}")


def audit_elf(ndk_bin: Path, library_path: Path, helper_dex: bytes) -> None:
    readelf = ndk_bin / "llvm-readelf"
    nm = ndk_bin / "llvm-nm"
    strings = ndk_bin / "llvm-strings"

    header = run_checked([str(readelf), "-h", str(library_path)])
    require("Class:                             ELF64" in header, "library is not ELF64")
    require("Machine:                           AArch64" in header, "library is not AArch64")

    dynamic = run_checked([str(readelf), "-d", str(library_path)])
    needed = set(re.findall(r"Shared library: \[([^]]+)\]", dynamic))
    require(needed == EXPECTED_NEEDED, f"unexpected dependencies: {sorted(needed)}")
    require(
        all(
            tag not in dynamic
            for tag in ("(INIT)", "(INIT_ARRAY)", "(PREINIT_ARRAY)", "(FINI)", "(FINI_ARRAY)")
        ),
        "constructor/destructor table present",
    )
    require(
        "Library soname: [libfinduas_eid_raw_get_v2.so]" in dynamic,
        "unexpected or absent SONAME",
    )
    require(
        all(tag not in dynamic for tag in ("(TEXTREL)", "(RPATH)", "(RUNPATH)")),
        "unsafe ELF dynamic path or text relocation",
    )

    defined = dynamic_symbol_names(
        run_checked([str(nm), "-D", "--defined-only", "--extern-only", str(library_path)])
    )
    require(defined == {"Agent_OnAttach"}, f"unexpected exports: {sorted(defined)}")

    undefined = dynamic_symbol_names(
        run_checked([str(nm), "-D", "--undefined-only", str(library_path)])
    )
    require(undefined == EXPECTED_UNDEFINED, f"unexpected ELF imports: {sorted(undefined)}")
    for forbidden in (
        "socket",
        "connect",
        "open",
        "openat",
        "write",
        "dlopen",
        "dlsym",
        "ptrace",
        "fork",
        "execve",
        "getauxval",
        "__system_property_get",
    ):
        require(forbidden not in undefined, f"forbidden ELF import: {forbidden}")

    printable = run_checked([str(strings), "-a", str(library_path)])
    for required in (
        "FindUAS-EID-Raw-Get-V2",
        "FINDUAS_EID_RAW_GET_V2 error_code=",
        "native_SendData",
        EXPECTED_SEND_DESCRIPTOR,
        "com.finduas.ridv2.RawCallback",
    ):
        require(required in printable, f"required ELF evidence absent: {required}")
    for forbidden in (
        "native_SendDataWithTcpPort",
        "native_RegisterObserver",
        "getOrNull",
        "JNIKeyValue",
        "127.0.0.1",
        "40007",
        "40009",
        "/data/",
        "/sdcard/",
    ):
        require(forbidden not in printable, f"forbidden ELF string: {forbidden}")

    library_bytes = library_path.read_bytes()
    require(library_bytes.count(helper_dex) == 1, "helper DEX is not embedded exactly once")
    require(library_bytes.count(b"dex\n") == 1, "unexpected embedded DEX magic count")
    require(library_bytes.count(b"\x7fELF") == 1, "unexpected embedded ELF magic count")
    require(b"PK\x03\x04" not in library_bytes, "embedded ZIP payload present")


def audit_readme(
    project_dir: Path,
    apk_digest: str,
    apk_size: int,
    library_digest: str,
    library_size: int,
    helper_digest: str,
) -> None:
    readme = (project_dir / "README.md").read_text(encoding="utf-8")
    require(f"APK SHA-256: `{apk_digest}`" in readme, "README APK digest mismatch")
    require(f"APK bytes: `{apk_size}`" in readme, "README APK size mismatch")
    require(library_digest in readme, "README packaged SO digest mismatch")
    require(
        f"packaged AArch64 SO bytes: `{library_size}`" in readme,
        "README packaged SO size mismatch",
    )
    require(f"helper DEX SHA-256: `{helper_digest}`" in readme, "README helper digest mismatch")
    require("DO NOT INSTALL OR ATTACH" in readme, "README lacks offline warning")


def audit_apk(apk: Path, project_dir: Path, sdk_root: Path, ndk_root: Path) -> None:
    require(apk.is_file(), f"missing APK: {apk}")
    build_tools = sdk_root / "build-tools/35.0.0"
    aapt = build_tools / "aapt"
    apksigner = build_tools / "apksigner"
    zipalign = build_tools / "zipalign"
    dexdump = build_tools / "dexdump"
    ndk_bin = ndk_root / "toolchains/llvm/prebuilt/darwin-x86_64/bin"

    helper_path = project_dir / "build/helper/classes.dex"
    helper_bytes = audit_helper_dex(dexdump, helper_path)

    with zipfile.ZipFile(apk) as archive:
        entries = archive.namelist()
        require(len(entries) == len(set(entries)), "duplicate ZIP entry")
        require(set(entries) == EXPECTED_ZIP_ENTRIES, f"unexpected ZIP inventory: {entries}")
        native_info = archive.getinfo(EXPECTED_NATIVE_ENTRY)
        require(native_info.compress_type == zipfile.ZIP_DEFLATED, "native library not compressed")
        library_bytes = archive.read(EXPECTED_NATIVE_ENTRY)

    inspection_mirror = project_dir / "build/inspect.so"
    require(
        inspection_mirror.is_file() and not inspection_mirror.is_symlink(),
        "missing regular build/inspect.so packaged-library mirror",
    )
    require(
        inspection_mirror.read_bytes() == library_bytes,
        "build/inspect.so does not exactly match the packaged library",
    )

    audit_manifest(aapt, apk)
    run_checked([str(zipalign), "-c", "4", str(apk)])
    signer_output = run_checked(
        [str(apksigner), "verify", "--verbose", "--print-certs", str(apk)]
    )
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

    with tempfile.TemporaryDirectory(prefix="finduas-v2-audit-") as temporary:
        library_path = Path(temporary) / "libfinduas_eid_raw_get_v2.so"
        library_path.write_bytes(library_bytes)
        audit_elf(ndk_bin, library_path, helper_bytes)

    apk_digest = sha256_file(apk)
    library_digest = sha256_bytes(library_bytes)
    helper_digest = sha256_bytes(helper_bytes)
    audit_readme(
        project_dir,
        apk_digest,
        apk.stat().st_size,
        library_digest,
        len(library_bytes),
        helper_digest,
    )

    print(f"APK SHA-256: {apk_digest}")
    print(f"Packaged SO SHA-256: {library_digest}")
    print(f"Helper DEX SHA-256: {helper_digest}")
    print(f"Signer certificate SHA-256: {signer_digest}")
    print(f"Native entry: {EXPECTED_NATIVE_ENTRY} ({len(library_bytes)} bytes, compressed)")
    print("Inspection mirror: build/inspect.so is byte-identical to packaged SO")
    print("Manifest: no permissions, no components, no shared UID, hasCode=false")
    print("Packaged DEX: absent; one-class helper DEX embedded exactly once in ELF")
    print("Route: permanently UNRESOLVED; epoch check permanently false")
    print("Send: one guarded JNI call site; retryTimes=0; no typed/observer/TCP route")
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
        os.environ.get("FINDUAS_V2_NDK_ROOT", str(sdk_root / "ndk/27.2.12479018"))
    ).resolve()

    audit_source(project_dir)
    audit_apk(arguments.apk.resolve(), project_dir, sdk_root, ndk_root)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditFailure as error:
        print(f"AUDIT FAILED: {error}")
        raise SystemExit(1)
