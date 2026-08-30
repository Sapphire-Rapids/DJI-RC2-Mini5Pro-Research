# DJI Fly same-process FlySafe query experiment

Status: **A-048 identity loading OBSERVED on RC 2; FlySafe query OBSERVED only on the disposable emulator**.

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

## Self-identity canary A-048

The separate `src/native/art_ti_identity_canary.c` preserves A-040 unchanged. It accepts exactly
one 16-character lowercase-hex session token, records its own PID/UID/GID, bounded self-proc
SELinux context and starttime, then requests ART TI `0x70010200`, reads the interface version and
disposes that newly allocated environment once. A valid entry returns `JNI_OK` even when a check
fails, preventing a framework fallback from repeating initialization. The canonical result log's
`ready` field, tied to the session and process, carries the outcome.

Thirty-two host cases, sanitizer checks and six compiled behavior mutations pass. Two ARMv7
builds match 8,372 bytes, SHA-256
`28b96744bef7f4cf3e64911134683ee71a6c950c44a88193fae2fdc7b60b4f4b` (C-269).
`Download/FindUAS_ARTTI_V2.so` was fully read back from SD (C-270), then A-048 loaded once
in the original Fly process with canonical identity/API/disposal success. The verified ordinary
file was removed and independently confirmed absent; B2 closed by STOP (C-273--C-275).
Build and test with the same tool-root variables above:

```sh
sh scripts/run_identity_canary_host_tests.sh
sh scripts/build_identity_canary.sh
```

Generated output is `build/identity-canary/armeabi-v7a/libfinduas_artti_identity.so` and stays
excluded. The canary does not query DJI classes or aircraft state. It releases its environment;
the native agent and JVMTI plugin mappings can remain until the target process exits.

## Fixed loader L1 and canary receiver B2

`scripts/rc2_canary_loader.sh` (A-049) implements the fixed baseline, one-load and cleanup
operations for A-048. `scripts/rc2_sd_canary_bridge.sh` (A-050) runs that SHA-pinned helper
through the existing finite mailbox protocol. Neither changes the original B1/F4 source.
Thirteen real-mksh loader tests cover 39 scenarios, two Java/mksh composition cases pass,
and the extended host client passes 29 synthetic tests. C-271 records the code checks;
C-272 records matching staging; C-273--C-275 subsequently record successful baseline/load,
independent cleanup and session closure.

The ordinary internal file is created exclusively after baseline checks and verified by its
actual descriptor identity, hash and label. A permanent attempt record precedes the sole
fixed-name dispatch. Normal cleanup requires canonical matching native completion and the
same file identity; partial or uncertain copies are retained. Details and host commands are in
[the SD client](../../../host-tools/rc2-sd-bridge/README.md).

## Fixed Fuli baseline report script

`scripts/rc2_fuli_baseline.sh` is the F4 source revision. It has been SD-staged with matching
full readback and executed through B1; its strictly parsed report is received (C-267). Its required SD name is `Download/F4.sh`; it accepts no arguments, validates the
hexadecimal volume name in its exact `$0` path and requires the existing report directory on that
same SD. It exclusively creates `Download/FindUAS/Probe/FindUAS_F4_<UTC-date>_<pid>.txt` using
noclobber. There is no global storage enumeration, internal library copy, attach, permission/mount
change, Fly launch request or DJI protocol action.

The `finduas-rc2-fuli-baseline/v4` report keeps F2's identity, SELinux/Wi-Fi/debuggable reads,
`/data/app` listing, candidate-file check and staged A-040 size/hash checks. It adds two fixed
`dumpsys activity -p dji.go.v5 lru` reads, each limited to three seconds, around the process reads:

- An AMS result supplies a PID only with command rc=0, at most 4,096 raw output bytes, no
  truncation, and the exact `ACTIVITY MANAGER LRU PROCESSES (dumpsys activity lru)` header.
- Only records whose first token is `#` plus ASCII digits plus `:` are parsed. A complete target
  token must be a positive ASCII PID without leading zero, followed by `:dji.go.v5/` and a
  nonempty UID token. Prefix/suffix process names and `:aux` processes do not match.
- Exactly one matching record is required. Duplicate lines are rejected even if their PIDs agree;
  multiple matching tokens in one line are rejected too. The PID is revalidated immediately
  before constructing `/proc/<PID>` paths.
- The original pidof reads remain diagnostic. Their failure marks the report INCOMPLETE but
  cannot suppress AMS or any target `/proc` reads admitted by the first AMS result. Each target
  stat/context/cmdline/exe/status read records its own stderr and rc and continues after failure.
  The second AMS read also runs when the first AMS result is unusable or all target reads fail.
- `ams_pid_stable` compares the two independently admitted AMS PIDs. `proc_starttime_stable`
  separately compares field 22 from the two target stat reads. Each is `true`, `false` or
  `unknown`; unavailable stat data is not evidence that the process stopped.

The same window records every `/proc` mount line from `/proc/self/mountinfo`, rather than filtering
only for hidepid. It also records Pid/PPid/NSpid/Uid/Gid/Groups from `/proc/$$/status`, where `$$`
is the collecting shell identity. The script does not hardcode a live PID or volume identifier.

Every executed command retains its rc; AMS parser outcomes have separate before/after rc fields.
Command output is bounded before normalization, including trailing newline bytes. Nonzero rc,
truncation, unusable AMS data, unknown/false stability or source mismatch produces INCOMPLETE;
none of those outcomes aborts the remaining admitted reads. `COMPLETE` describes these baseline reads only.
The report still records zero protocol requests, attaches and internal copies.

`F4_SAVED` prints the report path for either report status; startup/write failure prints `F4_ERROR`,
with `F4_END` as the final console marker. A received report must retain its schema and
`report_end=true`. Reports, actual volume identities and process identifiers stay private; no
media-scan broadcast is sent. Deployment and the next operator command remain in
[the live-runtime steps](../../../docs/23_RC2_LIVE_RUNTIME.md#下一步).

F3/A-045's exact source remains recoverable at commit `34c04be`. Its raw live report (C-262)
contains two mksh heredoc temporary-file errors outside the report sections and fails strict
parsing. F4 feeds the same AMS parser through a `printf` pipe, without a heredoc or temporary file.
Eighteen complete host fixtures passed using the Android 11 mksh source; a separate twelve-case
comparison reproduces the heredoc failure and verifies the pipe in writable and denied-temp cases.

F2/A-044 and its source remain recoverable at commit `238b902`; its SD script is archived.
C-257's 2,553-byte F2 report passed full MTP/envelope validation. Its sole failed command was
`pidof dji.go.v5` (rc 1, empty); the other eleven commands passed, including A-040 source size/hash.
AMS later reported a HOME main-process entry (C-258), while a separate read of that earlier
process's context returned a path error without a mount-options line (C-259). F3's raw report
then records proc `gid=3009,hidepid=2`, while the caller lacks group 3009. F4 preserves the paired
AMS/proc collection and records each read failure independently.

F1/A-043 remains historical, with its original source at commit `463c0d5`. Its launcher retained
the unexpanded SD wildcard (C-252). F2 removed global `/storage` enumeration and changed its
filename/schema/markers; its earlier launch is not an instruction to repeat F1 or F2 now.

## B1 SD diagnostic receiver

`scripts/rc2_sd_bridge.sh` starts one finite mailbox worker from `Download/B1.sh`. It reads the
host-prepared active session, detaches its standard streams from Fuli's synchronous Shell page,
and accepts only `PING`, `SNAPSHOT` and `STOP`. It stops after one hour or 64 sequential jobs.
Each job is claimed once; a complete closed report precedes its size/hash-bound done marker.
SNAPSHOT verifies and executes the fixed F4 text from memory with a 45-second timeout.

The eleven real mksh/Java integration scenarios cover startup EOF, inherited FD3, partial/invalid
jobs, prior-result collisions, helper replacement, TTL and the task limit. A-046/A-047 are
SD-staged with full matching readback. One operator startup then enabled the verified
PING/SNAPSHOT/PING round trip and F4 report receipt (C-266/C-267). The [host client, protocol and tests](../../../host-tools/rc2-sd-bridge/README.md)
keep live session state and output outside the published source tree.

## Exact observed emulator result

The privacy-reduced log shapes were:

```text
FLYSAFE_RAW_AGENT stage=0 exception=0 ... unlock=1 event=1 device_id_nonzero=1 dispatched=1
FLYSAFE_RAW_QUERY callback=failure error_code=417
```

The PID before and after attach was identical. Because no aircraft was present, the success-side
type-6 parser has synthetic host coverage but no real callback input yet.

## RC 2 execution state

The exact post-install Fuli identity and system-UID Shell are recorded in C-245--C-247. The
A-048 identity canary now loaded once through the normal fixed-name AMS route on RC 2
`07.00.0100` / Fly `1.19.4` (C-273--C-275), with canonical native identity/API/disposal success.
The ordinary internal file had the verified apk_data_file label and registered hash; it was
removed and an independent cleanup job confirmed absence. AMS PID/UID and Fly APK stayed stable.
B2 closed by STOP. Original A-040 and the FlySafe query A-042 remain unexecuted on RC 2.

No bootloader, boot partition, TEE or proc permission changed. The canary's environment was
released, while native agent/plugin mappings were not unloaded from the running Fly process.
Preserve the permanent attempted marker and do not replay this successful canary. Further
RID state reads must follow the exact initialized-owner and native_get_sync review in C-276;
no current RID value or transition was read by A-048. See
[the live-runtime record](../../../docs/23_RC2_LIVE_RUNTIME.md).

## A-051: one official RID cache read

Status: **OBSERVED** in the existing RC 2 Fly 1.19.4 process (C-281/C-282). One call returned
RID support/normal1/1, EID0/0 and failReason0; JNI/parse/disposal succeeded, PID/APK stayed stable,
and file removal plus independent cleanup and B3 STOP were verified. Preserve the global attempt
record; this completed probe is not a recurring sampler.

The independent ARMv7 cache probe uses exact Fly 1.19.4 initialized JNI/key metadata and the
existing native SDK owner. It bypasses model factories, default DTOs and Rx interceptors,
then invokes `JNIKeyValue.native_get_sync` once for the original working-status key.
C-277 records the synchronous cache chain and serializer. The probe checks the already-loaded
SDK build ID and owner before/after the read, parses the strict `16+L` byte structure, and emits
only four status booleans plus numeric RID failure. It does not copy the area string.

A null cache returns a completed `ready=1/value_present=0` result with unavailable boolean
sentinels. JNI, metadata, owner, parsing and disposal errors keep separate numeric stages.
Every valid entry returns JNI_OK; an atomic once guard prevents repeated execution by the same
loaded DSO. New ART TI environments are disposed and JNI references are released.
The returned cached value has no recovered receive timestamp.

```sh
FINDUAS_ANDROID_NDK_ROOT=/path/to/android-ndk sh scripts/build_rid_cache_probe.sh
FINDUAS_JDK_ROOT=/path/to/jdk sh scripts/run_rid_cache_probe_host_tests.sh
```

The host suite covers 25 synthetic JNI/metadata/parser/cleanup cases with ASan and UBSan;
Android linker and owner reads use a test double there. The real ARMv7 build and version-specific
system checks are recorded separately. L2/B3 add fixed baseline/read/cleanup SD jobs using a
new internal test filename and A-051 receipts. See [the host transport](../../../host-tools/rc2-sd-bridge/README.md)
and [the runtime record](../../../docs/23_RC2_LIVE_RUNTIME.md) for staging and execution state.

## A054: existing cloud-policy source comparison

Status: **OBSERVED** on RC2 with Fly1.19.4 (C-291/C-292): one guarded MMKV read and two SDK
cache reads returned ProductType139,41 rows,36 distinct candidates and match1/default0. All
native/parser/disposal checks passed, PID/APK stayed stable, the file was removed and independently
confirmed absent, and B4 closed normally. Keep the completed probe's permanent attempt receipt.

This independent probe uses initialized namespace/key/MMKV metadata, verifies the loaded SDK
and MMKV build IDs, and reads one existing default-MMKV key under bounded trylocks. Native
instance, load mode and Java-handle checks select the memory-only read path. It releases both
MMKV locks before parsing or making one SDK cache call each for CloudControlData and ProductType.
It does not call the app area/service predicate, namespace lifecycle or cloud writer.

The fixed UTF8 parser derives possible candidates using first-country/DEFAULT, product exclusions
and nonempty strings. The report contains only numeric presence/receiver/product/count/error data;
it omits source strings and hashes. It keeps missing namespace/cache/product, malformed policy
and guard failures separate. Candidate string equality does not select an actual area or identify
the writer of the shared last-SET cache.

```sh
FINDUAS_ANDROID_NDK_ROOT=/path/to/android-ndk sh scripts/build_cloud_cache_probe.sh
FINDUAS_JDK_ROOT=/path/to/jdk sh scripts/run_cloud_cache_probe_host_tests.sh
sh scripts/run_cloud_policy_parser_host_tests.sh
```

The native/JNI harness has40 cases with sanitizers; the parser has101 native checks plus a
Python differential suite. Android linker/instance ownership is simulated in host tests and
statically checked against the exact samples. L3/B4 provide fixed baseline/read/cleanup jobs
with separate A054 receipts. [Current execution state](../../../docs/23_RC2_LIVE_RUNTIME.md)
is recorded independently of host tests. The original A048/A051 bytes are unchanged.
