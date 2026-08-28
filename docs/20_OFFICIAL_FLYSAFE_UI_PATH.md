# Official DJI Fly FlySafe inventory path

## Scope

This note records the highest-information next read-only experiment for the `RID_UNLOCK` branch.
It does not claim that a type-6 license exists, that Mini 5 Pro consumes one, or that a license UI
state changes Broadcast Remote ID RF.

## Exact current-package facts

`STATIC`, DJI Fly `1.21.10`:

- the manifest declares `com.uav.unlocklicenselist.UnlockLicenseManagerActivity`;
- the Activity has no exported declaration and is not an ordinary third-party APK launch target;
- resources include the license-manager settings entry and account/aircraft license-list labels;
- the protected current package contains the component actions `action_to_manage_activity` and
  `action_get_manage_view`, plus the native entry names `queryFCLicensesJni` and
  `setLicenseEnableJni`;
- current native analysis already maps the aircraft inventory/action family to `0x11/0x11` and
  `0x11/0x12`.

The exact current Java bodies behind the protected bundle were not recovered. Therefore the menu
location, current rendering of type 6, and whether a generic row switch is shown on this RC 2 remain
live questions.

## Adjacent executable control flow

Pinned same-family Java at the repository revision recorded in
[14_SOURCE_INDEX.md](14_SOURCE_INDEX.md) supplies a readable implementation of this narrow flow:

1. the aircraft-settings license-manager item checks power/firmware/login gates;
2. the component action starts `UnlockLicenseManagerActivity`;
3. the aircraft-license view model calls `queryFCLicensesJni` when a product is connected;
4. a generic aircraft-license row exposes a switch whose handler calls
   `setLicenseEnableJni(enabled, licenseId, callback)`.

This is adjacent-version corroboration, not proof of exact `1.21.10` UI behavior. In particular,
an older generic model may misclassify an unknown type-6 record. A visible switch would establish
only an official same-process management surface; it would not by itself establish type-6 identity,
aircraft application, or RF effect.

## Why this precedes another external Binder guess

A-026's third-party passive gate saw no callbacks. A-027/A-028's fixed external transaction-4
`0x11/0x11` route ended before a successful group transport callback. DJI Fly's own Activity runs
inside the authenticated owner process, with its current device token, negotiated FlySafe version,
support state, login context, and product binding. Its aircraft tab is therefore the correct
ground-truth query surface before changing another external sender/receiver tuple.

## One-time assisted test

Keep motors stopped. Do not toggle a license in this first pass.

1. Link RC 2 and Mini 5 Pro normally and open DJI Fly.
2. Open Profile/Me, then Settings, then the entry labelled `证书列表` / `Unlocking License List`.
3. Select the aircraft-side tab (`飞机内证书` / `Aircraft Unlocking Licenses`).
4. Refresh once if the UI provides a refresh action.
5. Capture the whole screen and any toast/error. If rows exist, capture their visible type, status,
   validity and switch state without opening identity details.
6. Do not change any switch. Close the page normally.
7. Open A-033 and run its fixed active read-only `11/11` diagnostic once.
8. In File Manager, copy `Download/FindUAS/FindUAS_RID_A033_latest.txt` back to the host. The file is
   privacy-reduced and intentionally omits raw reply bytes and license identifiers.

Interpretation:

- an official aircraft-list result is same-process inventory evidence for that session;
- an empty list is evidence only if the UI completed without login/link/version/support error;
- an error must be preserved as an error, not rewritten as empty or unsupported;
- any candidate type-6 row remains read-only until its exact identity and baseline are established;
- no later enable/disable experiment may be called an RID switch without restore and independent
  motor-on RF A-B-A closure.

## Current disposition

The official UI test and the A-033 run are pending operator availability. No license toggle,
`0x11/0x12` action, motor start, or RF experiment is part of the prepared first pass.
