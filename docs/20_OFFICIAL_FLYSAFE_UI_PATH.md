# Official DJI Fly FlySafe inventory path

## Scope

This note records the exact DJI Fly `1.21.10` aircraft-license inventory and enable-state path. It
separates three facts that must not be collapsed:

1. the official same-process UI and native calls exist;
2. the current Java model cannot semantically represent FlySafe type 6 `RID_UNLOCK`;
3. neither fact proves that Mini 5 Pro accepts type 6 or that a license transition changes
   Broadcast Remote ID RF.

No vendor APK, process dump, extracted DEX or decompiled source is published.

## Exact-version runtime recovery

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

## Exact current owner chain

`STATIC`, recovered runtime Java plus exact current native entry points, DJI Fly `1.21.10`:

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

## Exact current generic switch path

`STATIC`, never executed in this research:

1. the aircraft-license adapter reads `WhiteListLicense.isEnabled()`;
2. enabling shows an ordinary confirmation dialog while disabling proceeds directly;
3. the adapter passes the selected existing license ID and desired Boolean through
   `IUAVFlightRestrict` and `FlightRestrictImpl`;
4. `JNIFSUnlockManager.setLicenseEnableJni` invokes the native setter with the current device ID;
5. a successful callback returns a Boolean array and the adapter refreshes all displayed row states.

This is an existing-license state action, not a license generator. No write was executed, and a
generic switch does not identify its row as type 6 or prove an aircraft/RF effect.

## Exact type-6 incompatibility in current Java

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

## Prepared operator observation

Keep motors stopped and do not toggle a license in this pass.

1. Link RC 2 and Mini 5 Pro normally and open DJI Fly.
2. Open Profile/Me, Settings, then `证书列表` / `Unlocking License List`.
3. Select `飞机内证书` / `Aircraft Unlocking Licenses` and refresh once if offered.
4. Record whether the page completes, asks for login/link/update, reports empty, or shows rows.
5. If rows exist, record only visible generic type/status/validity/switch state. Do not infer type 6
   from an unlabeled row and do not open identity details.
6. Close the page normally without changing any switch.
7. Keep A-033 available only as the historical external-Binder comparison. The next higher-value
   assisted run is the source-only same-process query after an RC 2 loader is admitted.

Interpretation:

- a completed official aircraft list is same-process inventory evidence for that session;
- an empty result is valid only if login, link, support and version errors are excluded;
- a malformed-looking polygon/unknown row is a type-classification lead, not proof of type 6;
- A-033 remains an external diagnostic and may still fail before a canonical inventory;
- any later state experiment requires exact existing-item identity, baseline, immediate readback,
  restore, final readback and operator-started motor-on independent RF A-B-A closure.

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

The exact current owner and generic existing-ID action are closed statically, current Java type-6
semantics are closed negatively, and the exact private query plus callback is now observed in the
disposable emulator through ART TI. The success-side raw inventory parser is implemented and
synthetically tested, but the emulator cannot produce an aircraft callback. RC 2 still lacks an
admitted same-process loader. The official per-license enable/disable surface is pinned at the
Cloud API and MSDK 5.8 levels, but no genuine type-6 row has been observed on Mini 5 Pro. No license
toggle, `0x11/0x12` action, motor start or RF experiment has been performed as part of this path.
