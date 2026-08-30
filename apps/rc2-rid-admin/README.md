# FindUAS RC 2 RID Admin

Status: **NOT ADMITTED as a general aircraft RID controller.** This is independently written
laboratory source with both read-only diagnostics and explicitly labelled experimental write paths.
It is covered by the repository-root [MIT license](../../LICENSE). Generated APKs, signing material,
vendor code, and live/private captures are intentionally not committed.

## Current source: identity safety lock

Version `0.8.1-identity-safety-locked` / code `14` is a new source revision, not the A-033 artifact
identified below. It has not been staged, installed, or run on RC 2. EID and OPID SET/DELETE/restore
controls are disabled, their handlers reject entry, and the shared protocol sender admits only the
existing GET selectors for these two commands. A successful GET cannot unlock them. The other
experimental F9/FlySafe paths retain their existing boundaries; this is not a globally read-only APK.

OPID output contains only unknown/empty/present and length. Full values do not enter the selectable
result pane or clipboard; transport payloads, callback descriptions and vendor exception text for
OPID are redacted. OPID input is disabled and excluded from Android view-state saving.

The retained EID/OPID transaction code validates the current value and original session baseline
before a write; OPID restoration requires exactly zero or 16 bytes. Once dispatch may have occurred,
an uncertain ACK, readback failure, mismatch, interruption or failed restore reports
`RESTORE_REQUIRED`, retains the baseline only in process memory, and blocks further transitions.
Even a successfully read-back forward change remains locked until the original baseline is read
back. A fresh value that conflicts with the captured baseline or last attempted value invalidates
the session and blocks stale restoration instead of overwriting an unrelated external change.
There is no automatic retry or recovery on an unadmitted route. Any future separately admitted
recovery write must obtain both a canonical ACK and matching final readback; closing/restarting the
app is not restoration. Host tests exercise this logic with fake device state, not with a device
transport.

The existing direct-query report now uses `Download/FindUAS/FindUAS_RID_latest.txt`; its embedded app
version distinguishes this revision without overwriting the historical A-033-named report. No new
query, field setter, broadcaster or RF backend was added.

Local validation on 2026-08-30: 170 JVM tests passed; lint reported zero errors and 15 warnings.
Two clean APK builds have size `225937` bytes and identical SHA-256
`8ee7a4edd36c7f97c631fabf3186ac3df79e6611869ebf05b11e83ccba4e84ba`.
APK Signature Scheme v2, zip alignment, zero declared permissions and absence of packaged native
libraries were verified. These are local source/artifact checks only; the new revision remains
`NOT ADMITTED`, with no device delivery or execution.

RC 2 laboratory APK for the stock DJI `protocol` Binder service found in RC331 firmware.

Implemented runtime operations:

- one-shot passive `0x03/0x09` Area Info plus `0x03/0x42` WhiteList Info gate, using one Binder
  transaction-2 listener, a bounded 60-second window, a same-full-route connection proxy and no
  constructed gate GET;
- same-process modern V3/V4 `0x11/0x11` FlySafe inventory traversal only after the passive gate
  observes `supported=true` and version 1 or 2; V2, unknown, unsupported, missing, malformed or
  conflicting gate states send zero inventory requests;
- an in-memory, owner-bound permit that accepts exactly one group selector followed by page 0,
  page 1, and so on, with a hard 128-page ceiling; duplicate starts, skipped/repeated pages and
  use after process/UI cancellation fail closed;
- privacy-reduced RID_UNLOCK output that retains only counts, RID level and public status bits;
- deterministic listener cleanup through APK process death after the gated operation, working
  around RC331 v10's broken cross-process transaction-5 object-identity removal; leaving the
  Activity requests cancellation but never kills the process in the middle of transaction-2
  registration, and an in-flight transaction-4 waits through RC331's initial send plus two retry
  periods before terminal cleanup;
- live F7 maximum-height positive control over the legacy and modern Binder routes before the
  target hash is interpreted;
- fixed `rid_ctrl_enable_0` (`0x3CBD864F`) F7 metadata probe, F8 read, F9 Boolean write,
  repeated readback, pre-operation rollback and session-baseline restore;
- strict by-hash codec `RidEuC0Parameter` for the wa150 EU C0 row
  `EU_CE_enable_c0_rid_0` (`0xF80992FE`), with the FLYC parameter-name hash recomputed and
  fail-closed name/hash identity; it mirrors the host-tool codec and is now wired to a
  separate EU C0 read-only probe/off/on/restore surface whose write buttons stay disabled
  until an F7/F8 baseline and live route pass;
- candidate France EID GET (`0x03/0x77`); retained SET/restore transaction code is locked;
- candidate masked EU operator-registration-number GET (`0x03/0x78`); retained SET/DELETE/restore
  transaction code is locked;
- launcher for the stock DJI Developer Assistant protocol page.

The passive-gated and direct-read-only query entry points admit only `0x11/0x11`; their query proof
cannot authorize `0x11/0x12`. The shared sender also contains a separate, gated validation-pulse
SET path that is not wired to the direct-read-only button. The Developer Assistant launcher opens
an external DJI UI and is not governed by this APK's internal allow-list. The APK also contains
the explicitly labelled experimental F9 controls listed above, so the artifact
as a whole is an **Admin** build, not a globally read-only build.

The Activity uses process label `com.dpad.fuli` because RC331
`ProtocolManagerService` v10 authorizes third-party callers by resolving the caller process label
as a package and accepting system-package flags. The APK's Linux UID is unchanged. This behavior
must be confirmed on RC 2 firmware `07.00.0100`; the local service ABI was recovered from adjacent
RC331 `10.00.0700/0205` artifacts.

Version `0.8.0-flysafe-diagnostic-export` obtains the service Binder through the controller's own
`com.dji.protocol.ProtocolManager`, avoiding an ordinary app's direct hidden-API lookup. It retains
`ServiceManager.checkService()` only as a compatibility fallback. The result pane is selectable and
copyable and reports the exact service lookup, Binder transaction, callback and DUML ACK stage.

`RIDCtrlEnable` is independent from France EID in the current SKYROVER 1.2.0 same-family SDK. Its
FC mapping is `rid_ctrl_enable_0`, routed through the modern `0x82 -> 0x92` F7/F8/F9 family. This
APK fixes the name/hash and refuses to write until the target aircraft itself returns matching F7
metadata and an F8 Boolean baseline. Mini 5 Pro support is therefore decided by the live F7/F8
result, not inferred from the SKYROVER application.

The app does not send any command merely by opening. Operations are serialized, candidate write
buttons remain disabled until a successful F7/F8 baseline, and a candidate-parameter readback is
never labelled as proof of RF Remote ID. The FlySafe one-shot button registers only the two passive
gate filters during its observation phase. If and only if the in-memory gate admits modern query,
the same call stack performs the fixed inventory traversal. A callback failure, malformed Pack,
deadline, route/value conflict, Activity stop, wrong selector sequence or query-count overflow
permanently denies that one-shot permit. The gate is never persisted as a reusable permit. The app
synchronously stores only the privacy-reduced terminal result and then terminates its process so
Binder death removes the listener; reopening only displays that result.

The `rid_ctrl_enable_0` surface and the `EU_CE_enable_c0_rid_0` surface are independent controls
with independent metadata/baseline/route state. The EU C0 surface re-probes F7/F8 before every F9,
reads back twice, restores the baseline on any unconfirmed state, and reports that one F8 readback
does not imply persistence across a DJI Fly reconnect: pinned FreeFCC prior art documents a C0
class runtime flag that overrides flight-controller parameters on every connection (C-198). This is
a probe/inventory semantics label, not RF proof, and `EU_CE_enable_c0_rid_0` remains an EU C0
policy candidate rather than a global RID master switch.

Build:

```sh
export JAVA_HOME=/path/to/jdk-21
export ANDROID_HOME=/path/to/android-sdk
gradle --no-daemon clean testDebugUnitTest lintDebug assembleDebug
```

Audited A-026 artifact:

- version: `0.6.0-flysafe-gated` / code `9`;
- size: `135525` bytes;
- SHA-256: `3c2ae42ac9f19a9e3dfe669ed6357bb8d2f1c38568af6a0f8d8b8f677fcbfec4`;
- two independent clean builds were byte-identical;
- 63 unit tests passed; lint reported zero errors and 13 non-blocking warnings;
- APK Signature Scheme v2 and zip alignment verified; the manifest declares zero permissions and
  the APK contains no native library, network, socket, shell or process-execution path;
- staged through MTP as removable-SD `Download/FindUAS_A026_GATE.apk`; same-session byte comparison
  and SHA-256 matched, and a fresh device listing confirmed one short-name copy.

These checks prove the local implementation/artifact and delivery identity only. Installation,
the target RC 2 Binder behavior, gate visibility, inventory contents and RF Remote ID behavior
remain live-device observations.

## A-027 live result and A-028 diagnostic successor

The first user-supplied A-026 run subsequently showed `GATE_UNOBSERVED` after 60,003 ms with zero
accepted/ignored/malformed/failure callbacks and `11/11 request count=0`. This is a narrow passive
listener visibility result, not an unsupported/no-inventory result.

The A-027 candidate adds one independent button for a fixed active-read-only
modern compatibility query. It tries only `02:04 -> 12:04`, `11/11`, uses the common V3/V4
`00 01` then ordered page selectors, performs zero application retries, and never scans routes or
tries the V2 codec. Only a count-consistent data-less-terminator completion is displayed as a
canonical inventory; every failure remains ambiguous. A private one-shot query proof is type-
separated from the private SET dispatch, and tests prove that presenting it to `11/12` is rejected
before Binder dispatch. Its dedicated public-read-only parser clears exact license IDs after
duplicate checking, cannot issue a control handle, and is the only parser mode accepted by direct
pass completion. See [DIRECT_FLYSAFE_READONLY_PROBE.md](DIRECT_FLYSAFE_READONLY_PROBE.md).

Exact A-027 artifact:

- version: `0.7.0-flysafe-direct-readonly` / code `10`;
- size: `196569` bytes;
- SHA-256: `aa4bcd9c8aa96870cfbae1ba326d366cb8854a50ef4aff223f7bce4290ddcd81`;
- 127 JVM tests passed with zero failures/errors/skips; lint reported zero errors and 15
  non-blocking warnings;
- two independent clean builds were byte-identical;
- APK Signature Scheme v2 and zip alignment were verified; the manifest declares zero permissions
  and the APK contains no native library, network, socket, shell, or external-process execution
  path;
- staged through MTP as removable-SD `Download/FindUAS_A027_RO.apk`; fresh listing and MTP readback
  confirmed the expected size and SHA-256.

These checks do not establish installation, Binder success, inventory contents, RID_UNLOCK state,
or any RF Remote ID effect. Those remain live-device observations.

The operator then installed and ran A-027. The fixed direct button returned
`DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`, exception class `ProtocolException`, and
`11/12 request count=0`. A-027 did not display the parser exception message, so this result proves
only that strict parsing did not reach a canonical inventory; it does not distinguish callback,
ccode, group, page, or terminator failure.

A-028 changes diagnostics only: it displays the parser's fixed non-sensitive reason string and,
where relevant, the group/page ccode, page index, or terminator data length. Route, selectors,
query command, retry policy, and write separation are unchanged. Exact A-028 artifact:

- version: `0.7.1-flysafe-direct-diagnostic` / code `11`;
- size: `197061` bytes;
- SHA-256: `d7c32636e19d1bce1b8b8994206355f42d0278b2f15048b14a948a8bbda1d540`;
- 127 JVM tests passed; lint had zero errors and 15 non-blocking warnings;
- two independent clean builds were byte-identical; APK Signature Scheme v2, zip alignment, zero
  manifest permissions, and no native library were verified;
- staged through MTP as removable-SD `Download/FindUAS_A028_DIAG.apk`; fresh listing and readback
  matched the expected size and SHA-256;
- the operator installed and ran it; the fixed read-only query ended at `ProtocolException` with
  detail `group transport callback failed` and `11/12 request count=0`.

That live result closes only the tested group transport callback. It does not establish an empty
inventory, missing `RID_UNLOCK`, aircraft support, RID-off state, or any RF behavior, and it issued
no `11/12` request.

## A-033 diagnostic export candidate

A-033 persists each completed active direct `11/11` result as UTF-8 in two places:

- private app external storage at `getExternalFilesDir("diagnostics")/latest.txt`, replaced through
  a synced temporary file and atomic rename;
- public MediaStore Downloads at `Download/FindUAS/FindUAS_RID_A033_latest.txt`, so the stock RC 2
  file manager can return the report without ADB or a storage permission.

Schema `finduas-rc2-rid-direct-diagnostic/v1` contains the app version, UTC time, fixed operation
name, and complete privacy-reduced result. Direct callback failures include failure text,
`ccode`/ECode and the already-redacted Binder/ACK diagnostic, but never `Reply.data`, raw payload,
license ID, account data, aircraft serial, or coordinates. No permission, network, service, startup
receiver, background retry, or protocol write was added. Protocol command, route, selectors and the
zero-`11/12` direct-button boundary remain identical to A-028.

Exact A-033 artifact:

- version: `0.8.0-flysafe-diagnostic-export` / code `12`;
- size: `204449` bytes;
- SHA-256: `8ce8e0c13ecfcf69517a64e809a475b79bbc750124225744b6b35f281d3d7177`;
- 132 JVM tests passed; lint reported zero errors and 15 non-blocking warnings;
- two independent clean builds were byte-identical;
- APK Signature Scheme v2 and zip alignment verified; the manifest declares zero permissions and
  the APK contains no native library, network, socket, shell, or external-process execution path;
- staged through MTP as removable-SD `Download/FindUAS_A033_DIAG_EXPORT.apk`; a fresh readback
  matched the expected size and SHA-256.

The A-033 APK binary remains excluded; the hashes above identify that historical build, not the
current source revision. Staging is not installation or execution. A-033 has not produced a live Binder result and does not establish
inventory, entitlement, RID state, aircraft control, or RF behavior.
