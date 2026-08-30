# Official DJI Fly FlySafe inventory path

## Scope

This note preserves the DJI Fly `1.21.10` disposable-emulator results and records the separately
verified installed DJI Fly `1.19.4` ARMv7 owner chain. It separates three facts:

1. the official same-process UI and native calls exist;
2. the inspected Java models have no typed field-7 FlySafe `RID_UNLOCK` representation;
3. neither fact proves that Mini 5 Pro accepts type 6 or that a license transition changes
   Broadcast Remote ID RF.

No vendor APK, process dump, extracted DEX or decompiled source is published.

## Installed DJI Fly 1.19.4: static owner and ARMv7 build

`STATIC`, exact installed-app export, DJI Fly `1.19.4` / code `3113157`, RC 2 `07.00.0100`
(C-239): the verified APK contains only `armeabi-v7a` native libraries. Targeted Java and native
inspection independently closes `FlightRestrictImpl` → `JNIFSUnlockManager.queryFCLicensesJni`
→ `native_queryFCLicense`, registered in `libuavfs_jni.so` and delegated to `libflysafecore.so`.
The owner methods and erased callback signatures match the clean-room query agent. The parsed
inventory envelope also matches, while typed `LicenseData` remains limited to fields 1--5.

`JNIFSEventManager` initializes the current device ID to `-1`; its JNI query bridge forwards the
signed value without a sentinel check. The independent agent now rejects `-1` alongside its
existing zero guard before its sole query call. The corrected ARMv7 query is A-042, `15,464`
bytes, SHA-256 `88d88ba10396a790d5d6675e70b44a21c01a71bbb92b4c80978998837ae75e25`.
It has only been built offline; ARM64 build support is retained. No loaded owner, current device
ID or query callback has yet been observed in the RC 2 DJI Fly process.

The independent [experiment source and build instructions](../experiments/jvmti/jvmti_flysafe_inprocess_query/README.md)
and [artifact register](11_ARTIFACT_REGISTER.md) publish the reproducible code and hashes.
The verified vendor inputs and derived Java/native analysis remain local and excluded.

## DJI Fly 1.21.10 runtime recovery

`OBSERVED`, disposable ARM64 Android 11 emulator, exact official DJI Fly `1.21.10`:

- the ordinary privacy onboarding completed and the main DJI Fly Activity opened;
- a privileged emulator shell started the manifest-declared, non-exported
  `com.uav.unlocklicenselist.UnlockLicenseManagerActivity` directly;
- the Activity rendered account and aircraft unlocking-license tabs;
- without a linked aircraft, the aircraft tab reported that an aircraft connection was required;
- a direct Frida attach found runtime DEX candidates but destroyed the script/application before
  producing an output file; this path is a recorded negative and must not be repeated on RC 2;
- a read-only root `/proc/PID/mem` copy of the app's private read/write mapping succeeded in the
  disposable emulator; the independently written boundary scanner recovered 22 structurally valid
  DEX images for local analysis.

This observation proves the exact Activity can render in a disposable emulator. It says nothing
about RC 2 package identity, aircraft inventory, entitlement, enable state or RF.

## DJI Fly 1.21.10 owner chain

`STATIC`, recovered runtime Java plus exact native entry points, DJI Fly `1.21.10`:

1. `LicenseManageComponent` implements the component action that starts
   `UnlockLicenseManagerActivity` and another action that supplies its management view.
2. The Activity hosts `UnlockLicenseManageView`.
3. The aircraft tab uses `ULUavLicenseView` and `ULUavLicenseVM`.
4. The view model calls the current `IUAVFlightRestrict` implementation.
5. `FlightRestrictImpl` calls `JNIFSUnlockManager.queryFCLicensesJni`.
6. The JNI wrapper invokes the native FC-license query with the current device ID and callback.

This closes the same-process owner path that A-026 could not observe and A-027/A-028 could not reach
through a third-party Binder proxy. It also explains why another guessed external sender/receiver
tuple is lower information than observing the official aircraft tab.

## DJI Fly 1.21.10 generic switch path

`STATIC`, DJI Fly `1.21.10`, never executed in this research:

1. the aircraft-license adapter reads `WhiteListLicense.isEnabled()`;
2. enabling shows an ordinary confirmation dialog while disabling proceeds directly;
3. the adapter passes the selected existing license ID and desired Boolean through
   `IUAVFlightRestrict` and `FlightRestrictImpl`;
4. `JNIFSUnlockManager.setLicenseEnableJni` invokes the native setter with the current device ID;
5. a successful callback returns a Boolean array and the adapter refreshes all displayed row states.

This is an existing-license state action, not a license generator. No write was executed, and a
generic switch does not identify its row as type 6 or prove an aircraft/RF effect.

## DJI Fly 1.21.10 type-6 incompatibility in Java

`STATIC`, DJI Fly `1.21.10`:

- `LicenseType` defines only values 0--4 (`GEO`, circle, country, parameter and pentagon) plus
  `UNKNOWN(255)`; it has no `RID_UNLOCK` member;
- the current `LicenseData` protobuf oneof defines only fields/tags 1--5; no field 7
  `LicenseDataRID` exists in this app;
- `LicenseType.find` checks only those five typed fields and returns `UNKNOWN` when none is present;
- `WhiteListLicense.parseFromProtoBufData` routes known types 0--3 explicitly and sends every other
  value, including `UNKNOWN`, to the pentagon fallback;
- that fallback tolerates a missing polygon body, so a current type-6 record would not necessarily
  crash or disappear: it can be represented with the wrong ordinary license semantics.

The separate MSDK `5.18.0` schema contains type 6 and field 7, but it is a different artifact. The
exact current DJI Fly Java UI therefore cannot be treated as a semantic type-6 reader or a stable
RID switch. This does **not** prove that the native layer, FC firmware or a server-supplied opaque
record lacks type-6 support.

## Android 11 ART TI same-process query

`NEGATIVE` then `OBSERVED`, exact DJI Fly `1.21.10` on the disposable AArch64 Android 11 emulator:

- a no-op late-load agent requesting standard JVMTI 1.2 ended in a native DJI Fly process crash
  before its canary logged (C-188);
- Android 11 ART source identifies `0x70010200` as the late-loaded ART TI environment version;
- an independently written agent using that version attached without restarting the process,
  enumerated the already-loaded classes once, found exactly one unlock owner and one event owner,
  obtained their singleton objects and a nonzero current device ID (C-189);
- a second source-only agent loaded a tiny callback through `InMemoryDexClassLoader`, registered
  only its two callback natives, invoked the existing private current-device FC-license query once,
  and received failure code `417` (C-190);
- agent stage was zero, dispatch count was one, and the DJI Fly PID before and after was identical.

The emulator had no aircraft, so `417` is the boundary of this run: it validates the exact
same-process owner, private-native invocation and callback plumbing, but supplies no successful
inventory bytes. The public experiment contains an independent parser for the returned
`LicenseGroupModel` envelope. It reconciles declared/observed record counts, recognizes the
separate MSDK-compatible field-7 RID candidate and keeps a unique existing license ID only in
memory; five synthetic host cases and the source build pass (C-191).

This materially supersedes another external Binder route guess. It does not yet solve how an
ordinary APK on RC 2 loads into DJI Fly: the emulator observation used an authorized root shell
and an executable file label. The RC 2 admission dependency is now a usable userspace ADB shell or
another proved same-process loader, followed by one query-only run with a fresh callback and stable
PID.

### Loader path experiments

Three narrow emulator experiments now refine that admission dependency:

- the A-035 carrier's normal `/data/app/...==/...so` path was split at the first `=` by the
  ActivityManager agent-spec parser; no load occurred (C-208);
- the exact same SO bytes under delimiter-free `trace_data_file` terminated the target before
  canary, while delimiter-free `apk_data_file` loaded them, dispatched once, returned `417`, and
  retained the PID (C-209);
- the A-036 uncommitted PackageInstaller session produced delimiter-free `apk_tmp_file` staging,
  but target directory search was denied before load; abandon removed it (C-210).

These results leave a precise RC 2 question: which legitimate file type or mediated descriptor is
both creatable by the actual privileged caller and searchable/readable/mappable/executable by the
actual DJI Fly domain, without `=` in the agent specification (C-211)? Until signer/domain and
matching policy answer that question, neither source-only APK is an RC 2 candidate.

## DJI Fly 1.19.4 official UI: deferred observation

`STATIC`, the verified `1.19.4` APK (C-239): the navigation is **我的 → 设置 → 飞行解禁 →
飞机内证书**. `证书列表` is the destination title, not the Settings entry. The destination
`UnlockLicenseManagerActivity` is non-exported. The reviewed entry requires account login and
the aircraft list requires a normal aircraft connection. The aircraft view queries when attached;
selecting its tab changes the displayed page, with no automatic import or enable action found in
that reviewed path. Avoid an immediate extra refresh if the first query is still completing.

`OBSERVED` by operator report: the page cannot currently be opened, and the operator has not
applied for unlocking.
This UI shortcut is deferred and is **not a prerequisite** for the continuing runtime and RID
status research. It does not establish empty inventory or lack of entitlement.

If the UI is revisited, keep motors stopped and leave import, delete and row switches untouched.
Record the title/tab, completion or error message, row count and visible generic status; redact
account, aircraft and license identifiers. Positive rows can establish what the UI displayed, but
an empty list is not a canonical inventory result: this exact Java wrapper catches a protobuf
decode error and can return an empty or partial list as success. Neither a generic row nor its
switch proves type 6 or an RF effect.

## RC 2 loader preparation and independent RID status

`STATIC`, independent pure ART TI canary source/build audit (C-243): the canary requests the
`0x70010200` environment, reads its interface version and logs one result. It performs no class
enumeration or DJI query. Ten host tests pass and four deliberately incorrect variants were
detected. A-040 is the default ARMv7 build, `4,340` bytes, SHA-256
`9b02f2b3a7e5a8e2afb200bd7d1fae2e75d2753eaa9c7ea86071dd47cccf086a`.
`OBSERVED`: its removable-SD copy was read back with a matching hash, but it has not been copied internally
or executed; A-042 remains offline only. Both are `NOT ADMITTED` for RC 2 execution.

`OBSERVED`, C-245: the post-installation v0.12 report was received and validated as `COMPLETE`.
Fuli now has `updated-system=true` and all three inspected Activities enabled; its original version
code 155, APK hash, signer and two audited DEX hashes are unchanged. Fly and ART identity readings
match the earlier report. Directory `ABSENT` remains the Observer's view.

`OBSERVED`, operator-supplied Shell output (C-246): commands execute with system UID/GID identity
and the `system_app` domain. A separate read-only listing (C-247) establishes `/data` and `/data/app`
as `system:system` directories with mode `0771`; their labels are `system_data_root_file` and
`apk_data_file` respectively. The target Fly process domain and canary loading are pending.
No internal test directory/file has been created or library copied internally.

The independent RID working-status owner route is tracked under C-240 in
[the live-runtime note](23_RC2_LIVE_RUNTIME.md). It does not depend on applying for an unlock
license or obtaining a UI row, and it does not supply an admitted RID setter. No RID transition
has occurred in this work.

## Official type-6 enable surface

The FlySafe type-6 path's per-license enable/disable surface is now pinned at two official levels:

- DJI Cloud API FlySafe device method `unlock_license_switch` takes `license_id` + `enable` bool and
  returns `result` + `license_id`; `unlock_license_list` returns `type` 6 "RID unlocking" with
  `rid_unlock.level` 1=EU / 2=China (C-204).
- MSDK 5.8.0 defines `RidUnlockType` (EUROPEAN/CHINA), `FlyZoneLicenseInfo.getRidUnlockType()`, and
  the generic `setFlyZoneLicensesEnabled(info, isEnabled, callback)` setter (C-205).

These pin the official switch shape but remain account/FC-bound managed state: they do not prove
Mini 5 Pro entitlement, a genuine type-6 license, aircraft acceptance, or a standardized-RID RF
effect. The standardized Remote ID bearer is plaintext (ASTM F3411 / EN 4709), so the independent
detector A-B-A on that bearer needs no DJI-licensed decoder (C-203, C-206).

## Current disposition

The `1.21.10` emulator query/callback observation remains intact; the installed `1.19.4` Java/JNI
chain and ARMv7 build are separately closed statically. RC 2 still has no admitted same-process
loader or successful inventory callback. The UI shortcut is deferred, the independent RID status
route continues, and the staged pure canary remains unexecuted. No genuine Mini 5 Pro type-6 row,
license toggle, `0x11/0x12` action or RF effect has been established through this path.
