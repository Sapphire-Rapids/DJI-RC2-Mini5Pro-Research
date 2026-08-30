# DJI Fly same-process FlySafe query experiment

Status: **OBSERVED on a disposable emulator; NOT ADMITTED on RC 2**.

This source-only experiment demonstrated a narrow Android 11 ART TI path into DJI Fly `1.21.10`
on a disposable emulator. The query agent locates already-loaded FlySafe owner classes, obtains
the current device ID and invokes the existing private FC-license query with a small callback
loaded from an in-memory DEX. It does not implement the type-6 setter. A separate pure ART TI
canary now tests only environment availability, without enumerating classes or querying DJI.

On a disposable AArch64 Android 11 emulator, the query was dispatched in the existing DJI Fly PID
and returned callback error `417`, which is consistent with the emulator having no connected
aircraft. The process stayed alive. This proves the same-process owner/callback route, not an RC 2
deployment path, aircraft inventory, entitlement, RID state or RF effect.

## Exact installed 1.19.4 compatibility

`STATIC`, exact RC 2 DJI Fly `1.19.4` / code `3113157`, from the verified installed-app export
(C-239): the package contains `armeabi-v7a` native libraries. Its selected Java query chain is
`FlightRestrictImpl` → `JNIFSUnlockManager.queryFCLicensesJni` → `native_queryFCLicense`;
`libuavfs_jni.so` registers the matching native method and delegates to `libflysafecore.so`.
Owner names, callback descriptors and the parsed inventory envelope match this independent
agent. The app still has typed `LicenseData` fields 1--5 only; field-7 RID recognition remains
the parser's separate MSDK compatibility extension.

The exact event owner initializes its device ID to `-1`, and the native JNI bridge does not reject
that sentinel. The agent now rejects `-1` as well as its existing zero guard before dispatch.
This is a concrete initialization fix, not a recovered rule for every possible device ID.
Both ARMv7 and ARM64 builds pass; neither this static match nor the new ARMv7 build establishes
RC 2 loading or a successful aircraft callback. The high-level evidence is recorded in
[the official-owner note](../../../docs/20_OFFICIAL_FLYSAFE_UI_PATH.md); vendor samples and
derived analysis remain excluded.

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
FINDUAS_ANDROID_ABI=armeabi-v7a sh scripts/build.sh
sh scripts/run_canary_host_tests.sh
sh scripts/build_canary.sh
```

Run these commands from this experiment directory. The query build accepts `armeabi-v7a` and
`arm64-v8a`, retaining ARM64 as its default; set `FINDUAS_ANDROID_ABI` explicitly for the installed
32-bit Fly. It produces `build/dex/classes.dex` and `build/out/libfinduas_flysafe_query.so` and
recreates the whole `build/` directory. Build the canary afterwards if retaining both outputs.

`build_canary.sh` defaults to `armeabi-v7a` and writes
`build/canary/armeabi-v7a/libfinduas_artti_canary.so`; the same ABI variable selects ARM64.
The canary requires only the NDK to build; its host tests also require a JDK and host C compiler.
Both builds reuse the vendored AOSP Android 11 `jvmti.h` and notices from the adjacent
attach-canary project. Generated DEX/SO files remain excluded.

## Pure canary and current artifacts

`STATIC`, source/build audit and host tests (C-243): the pure canary requests only ART TI
`0x70010200`, reads the interface version and emits one status log. It has no helper DEX, class
enumeration, DJI owner lookup or query. Ten host cases pass, including failed/null environment
and version-query cases; four deliberately incorrect variants were separately rejected by the
test checks. These are synthetic host results, not RC 2 execution evidence.

| Artifact | ARMv7 size / SHA-256 | RC 2 disposition |
| --- | --- | --- |
| A-040, ART TI canary V1 | `4,340` bytes; `9b02f2b3a7e5a8e2afb200bd7d1fae2e75d2753eaa9c7ea86071dd47cccf086a` | `OBSERVED`: removable-SD staging/readback matched; no internal copy or execution |
| A-042, query with `-1` guard | `15,464` bytes; `88d88ba10396a790d5d6675e70b44a21c01a71bbb92b4c80978998837ae75e25` | `STATIC`: offline build only; not staged, loaded or queried |

Both remain `NOT ADMITTED` for RC 2 execution. Artifact identities and distribution boundaries are
indexed in [the artifact register](../../../docs/11_ARTIFACT_REGISTER.md).

## Fixed Fuli baseline report script

`scripts/rc2_fuli_baseline.sh` is the current F2 revision (A-044), staged and run with a received
report (C-257). Its SD name is `Download/F2.sh`. It accepts no arguments, validates the hexadecimal volume name
in its exact `$0` path and requires the existing report directory on that same SD. It exclusively
creates `Download/FindUAS/Probe/FindUAS_F2_<UTC-date>_<pid>.txt`; no internal library copy or attach
is performed.

A-043/F1 remains historical with its original identity and source at commit `463c0d5`. Its device
launch retained the unexpanded SD wildcard (C-252). The later `/storage` directory observation
shows why enumeration cannot be assumed. F2 removes only the global `/storage` glob/uniqueness
check and updates its filename, schema and output markers; all other read/write bounds remain.

The recorded launch used the privately observed volume ID. In this three-token Fuli
`Runtime.exec(String)` example, replace `XXXX-XXXX` before use; the completed run is not currently
being repeated:

```text
sh -c (sh${IFS}/storage/XXXX-XXXX/Download/F2.sh)2>&1
```

The fixed `finduas-rc2-fuli-baseline/v2` report records identity, SELinux/Wi-Fi/debuggable reads,
the existing Fly PID/domain/executable and selected process fields, PID/starttime stability,
`/data/app` entries and the staged A-040 size/hash. Each command retains stderr and its exit code;
Binder reads and hashing require the available `timeout` tool with a three-second limit. Output
is capped per command. Missing/nonunique Fly PID, read failures or source mismatch produce
`INCOMPLETE`; `COMPLETE` means the baseline reads completed. The script reports zero protocol
requests, attaches and internal copies. File preparation and loading remain separate steps.

`F2_SAVED` prints the report path; retrieve it through fresh MTP enumeration/full readback and
require `report_end=true`. Startup/storage failure prints `F2_ERROR` instead. Reports and actual
volume identifiers remain private. No media-scan broadcast is sent. Current operator instructions
are maintained in the [live-runtime steps](../../../docs/23_RC2_LIVE_RUNTIME.md#下一步).

C-257's 2,553-byte report passed complete MTP receipt and envelope validation. Its sole failed
command was `pidof dji.go.v5` (rc 1, empty); the other eleven commands passed, including A-040's
source size/hash. The current discriminator is the system service's package-filtered process record.

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
RC 2 `07.00.0100` still needs an admitted same-process loader. C-245's received and validated
post-installation `COMPLETE` report now shows Fuli as an updated system app with all three inspected
Activities enabled. Its original version code 155, APK hash, signer and two audited DEX hashes are
unchanged, as are the Fly and ART identity readings. Directory `ABSENT` is still an Observer-view
result.

`OBSERVED`, operator-supplied Shell output (C-246): commands execute with system UID/GID identity
in the `system_app` domain. The read-only directory listing (C-247) shows `/data` and `/data/app`
owned by `system:system`, both mode `0771`, with `system_data_root_file` and `apk_data_file` labels
respectively. No internal test directory/file has been created or library copied there;
the target Fly process domain and canary loading remain unverified. See
[the live-runtime record](../../../docs/23_RC2_LIVE_RUNTIME.md).

Do not unlock the bootloader, modify boot/TEE, or treat an attach request as proof that the agent
loaded. The proposed first load is the pure canary, followed only after its evidence is closed by
one query with a fresh callback and unchanged DJI Fly PID. Neither has run on RC 2, and no RID
transition has occurred through this route.
