# DJI Fly same-process FlySafe query experiment

Status: **OBSERVED on a disposable emulator; NOT ADMITTED on RC 2**.

This source-only experiment demonstrates a narrow Android 11 ART TI path into the exact DJI Fly
`1.21.10` process. It locates the already-loaded FlySafe owner classes, obtains the current device
ID and invokes the existing private FC-license query with a small callback loaded from an
in-memory DEX. It does not implement the type-6 setter.

On a disposable AArch64 Android 11 emulator, the query was dispatched in the existing DJI Fly PID
and returned callback error `417`, which is consistent with the emulator having no connected
aircraft. The process stayed alive. This proves the same-process owner/callback route, not an RC 2
deployment path, aircraft inventory, entitlement, RID state or RF effect.

## Why ART TI rather than standard JVMTI 1.2

Android 11's late-loaded OpenJDK JVMTI plugin uses the ART TI environment version
`0x70010200`. A standard JVMTI 1.2 attach to the exact non-debuggable DJI Fly emulator process was
followed by a process crash before the canary logged. The ART TI version attached cleanly and was
used for the successful owner and query observations. This is an emulator result; it is not a
claim about RC 2 process policy or an instruction to repeat the standard attach there.

## Data boundary

The injected callback parses only the independently reconstructed protobuf envelope needed to
count records and recognize the separate MSDK-compatible `LicenseData` field-7 RID candidate. It
reports only:

- declared and observed record counts;
- RID candidate count;
- whether exactly one candidate exists;
- RID level and three public status Booleans.

The license ID remains an in-memory integer needed for a future same-item readback/restore flow and
is never logged. Raw callback bytes, group identity, aircraft/account data and vendor code are not
written or published.

## Build and host test

Set tool roots without editing the scripts:

```sh
export FINDUAS_ANDROID_SDK_ROOT=/path/to/android-sdk
export FINDUAS_JDK_ROOT=/path/to/jdk
export FINDUAS_ANDROID_NDK_ROOT=/path/to/android-ndk
sh scripts/run_host_tests.sh
sh scripts/build.sh
```

The build produces a helper DEX and AArch64 agent under ignored `build/`. It reuses the vendored
AOSP Android 11 `jvmti.h` and notices from the adjacent attach-canary project; generated DEX/SO
files are intentionally excluded.

## Exact observed emulator result

The privacy-reduced log shapes were:

```text
FLYSAFE_RAW_AGENT stage=0 exception=0 ... unlock=1 event=1 device_id_nonzero=1 dispatched=1
FLYSAFE_RAW_QUERY callback=failure error_code=417
```

The PID before and after attach was identical. Because no aircraft was present, the success-side
type-6 parser has synthetic host coverage but no real callback input yet.

## RC 2 boundary

An ordinary third-party APK cannot attach an agent to DJI Fly merely because it contains this
library. The emulator observation used an authorized root shell and an executable file label.
RC 2 `07.00.0100` still needs an admitted same-process loader or a usable userspace ADB shell.
Do not unlock the bootloader, modify boot/TEE, or treat an attach request as proof that the agent
loaded. A first RC 2 run must remain query-only and must record a fresh callback plus unchanged DJI
Fly PID before any setter is added.
