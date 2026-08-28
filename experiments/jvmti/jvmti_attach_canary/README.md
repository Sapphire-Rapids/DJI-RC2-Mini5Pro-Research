# FindUAS Android 11 JVMTI attach canary

Status: **NOT ADMITTED**. Offline implementation and static audit complete; never installed and
never attached to the RC 2.

This is a deliberately narrow V0 carrier APK for one future question: can Android 11 load a
harmless, ABI-matched JVMTI agent into the already-running DJI Fly process? It does not inspect DJI
classes and does not test or change aircraft behavior.

## Distributable artifact

```text
dist/FindUAS-JVMTI-Attach-Canary-0.1.0-arm64-v8a.apk
SHA-256: 4a3867251a745ce5db6c0513c23def5c97e53a57e17f4d611621895e4e323c73
applicationId: com.finduas.jvmti.canary.carrier
versionCode/versionName: 1 / 0.1.0-research
ABI: arm64-v8a only
native entry: lib/arm64-v8a/libfinduas_jvmti_canary.so
```

The APK uses an ordinary local Android debug certificate. It is not DJI-platform-signed, requests
no shared UID and gains no privilege from PackageInstaller/FileManager helpers.

## Runtime behavior

`Agent_OnAttach` performs exactly one bounded pass:

1. rejects any non-empty options without parsing or logging them;
2. obtains only a JVMTI 1.2 environment;
3. reads the runtime JVMTI version;
4. releases the per-call JVMTI environment on both success and version-read failure;
5. emits one fixed line and returns.

It never calls `GetLoadedClasses` or any class-inspection API, never obtains a `JNIEnv`, and has no
class-name matching strings. `GetLoadedClasses` is intentionally omitted: JVMTI returns JNI local
references that require management, and V0 refuses to introduce `JNIEnv` merely to retain a class
count. See the [JVMTI 11 `GetLoadedClasses` contract](https://docs.oracle.com/en/java/javase/11/docs/specs/jvmti.html#GetLoadedClasses).

The only possible log shape is:

```text
FINDUAS_JVMTI_CANARY_V0 abi=arm64 error_code=N jvmti_version=0xNNNNNNNN
```

`error_code=0` is success; fixed errors `1..5` cover non-empty options, null VM, unavailable JVMTI,
version failure and JVMTI-environment disposal failure. There is no class
count/reference/name/signature, path, device ID, serial,
address, package version or DJI data in the log.

The library never requests JVMTI capabilities, events, callbacks, redefine/retransform, breakpoint
or watch access. It never invokes a Java method; opens no socket; accesses no file or Android
property; starts no process/thread; performs no Binder, Parcel, localhost, DUML, key, FlySafe or SET
operation. It never obtains a `JNIEnv` and never makes a JNI Java-method or field call. See
[NO_WRITE_DENYLIST.md](NO_WRITE_DENYLIST.md).

## Carrier shape

- `android:extractNativeLibs=true` and legacy JNI packaging force a standalone extracted `.so` on
  Android 11;
- no Android permission;
- no Activity, Service, Receiver, Provider, instrumentation or launcher;
- `android:hasCode=false` and no `classes.dex` in the distributable;
- one compressed native entry, `arm64-v8a` only;
- pure C; no `libc++`;
- exported ELF symbol set is exactly `Agent_OnAttach`;
- dependencies are exactly `liblog.so` and `libc.so`;
- imported ELF symbol set is exactly `__android_log_print` plus the compiler hardening guard
  `__stack_chk_fail`;
- no native constructor table.

The `arm64-v8a` decision follows the locally verified official DJI Fly 1.21.10 native payload
(`libsdk_jni.so` and `libnative-lib.so` are AArch64). It still does not replace the live packaged ABI
gate from observer v0.8.

## Build and fail-closed audit

Pinned local inputs:

- Android Gradle Plugin 8.7.0 / Gradle 8.10.2;
- Android SDK 35 / build-tools 35.0.0;
- NDK 27.2.12479018 / CMake 3.22.1;
- AOSP Android 11 JVMTI header from `android-platform-11.0.0_r40`, vendored byte-for-byte.

Build from this directory:

```sh
sh scripts/build_and_audit.sh
```

Audit an existing artifact:

```sh
python3 scripts/audit_artifact.py \
  dist/FindUAS-JVMTI-Attach-Canary-0.1.0-arm64-v8a.apk
```

The audit checks the exact single native source, source-call/inline-assembly denylist, pinned header
hash, exact four-entry ZIP inventory, manifest, compression/extraction intent, expected one-signer
v2-only signature, README artifact hash, alignment, DEX absence, ELF class/machine, exports,
imports, dependencies, constructor absence and forbidden strings. Any deviation fails the build.

AGP internally generates an empty `R` class despite `hasCode=false`; the packaging script removes
that DEX, realigns the APK and signs it again. Only the post-processed `dist/` APK is admissible.

## Future live gate — not executed here

Do not install this package or attempt an attach based only on the offline build. First collect the
complete v0.8 capability page and satisfy every gate in
[ANDROID11_LOAD_BOUNDARY.md](ANDROID11_LOAD_BOUNDARY.md), especially:

- live DJI Fly process/package identity;
- `ro.debuggable`, package debuggability and helper permission;
- live AArch64 process and packaged native ABI;
- SELinux mode plus the extracted library's actual owner/mode/label;
- safe device state with aircraft motors off.

No command caller is currently admitted. The adjacent stock `dpad_fuli` shell page automatically
attempts `adb shell su` and runs `adb version` when opened, then captures stdout without stderr or
exit status. Do not open it for this experiment. The completed adjacent-package exported-component
audit found no alternate stock carrier. An ordinary app cannot obtain the AOSP signature
permission `SET_ACTIVITY_WATCHER` merely by being debuggable or by executing `/system/bin/cmd`;
target debuggability is a separate condition. A side-effect-free caller that demonstrably holds
the permission and preserves argv/stdout/stderr/exit status requires a separate audit before the
steps below are usable.

Cross-package loading is plausible on baseline AOSP 11 but **must not be assumed to work on DJI's
build**. Copying into DJI Fly's `code_cache` is a write to target data, is not implemented, and
requires a separate same-UID/SELinux/rollback admission. `startup_agents` is explicitly forbidden.

## Read-only result verification after a separately authorized attach

After a separately authorized attach through a separately audited caller, reading the
already-existing log buffer does not change DJI Fly or aircraft state:

```sh
logcat -d -s 'FindUAS-JVMTI-Canary:I' '*:S'
```

A successful canary requires one fresh line from the authorized attempt with `error_code=0` and a
nonzero JVMTI version. A command reporting that attach was accepted, or an undated/stale matching
line already present in the log buffer, is not enough. Any environment-disposal failure is a hard
stop before V1.

Most importantly, canary success proves only ABI/JVMTI/linker reachability. It does **not** prove
that Remote ID works, that any DJI class is present, that
`KeyEIDSwitch` is callable, that the aircraft supports a switch, or that any RID operation is safe.
This artifact deliberately contains no class-name, method-call or control path.
