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
