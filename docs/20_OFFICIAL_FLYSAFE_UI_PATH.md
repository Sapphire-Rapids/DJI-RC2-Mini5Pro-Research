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

## Prepared operator observation

Keep motors stopped and do not toggle a license in this pass.

1. Link RC 2 and Mini 5 Pro normally and open DJI Fly.
2. Open Profile/Me, Settings, then `证书列表` / `Unlocking License List`.
3. Select `飞机内证书` / `Aircraft Unlocking Licenses` and refresh once if offered.
4. Record whether the page completes, asks for login/link/update, reports empty, or shows rows.
5. If rows exist, record only visible generic type/status/validity/switch state. Do not infer type 6
   from an unlabeled row and do not open identity details.
6. Close the page normally without changing any switch.
7. Install and run A-033 once, then return
   `Download/FindUAS/FindUAS_RID_A033_latest.txt` from removable storage.

Interpretation:

- a completed official aircraft list is same-process inventory evidence for that session;
- an empty result is valid only if login, link, support and version errors are excluded;
- a malformed-looking polygon/unknown row is a type-classification lead, not proof of type 6;
- A-033 remains an external diagnostic and may still fail before a canonical inventory;
- any later state experiment requires exact existing-item identity, baseline, immediate readback,
  restore, final readback and operator-started motor-on independent RF A-B-A closure.

## Current disposition

The exact current owner and generic existing-ID action are now closed statically, while current
Java type-6 semantics are closed negatively. The RC 2 official-page observation and A-033 run remain
pending operator availability. No license toggle, `0x11/0x12` action, motor start or RF experiment
has been performed as part of this path.
