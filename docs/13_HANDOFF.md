# Handoff for researchers and coding agents

## Start here

C-273--C-275 close the real RC 2 A-048 loader experiment. The fixed system-mediated attach
succeeded in the existing Fly process, with matching native identity, successful ART TI/API
disposal, unchanged AMS PID/UID and unchanged APK. The verified ordinary file was removed,
independent cleanup found it absent, and B2 STOP/CLOSED STOP completed. A-040 remains unchanged
and unexecuted. Preserve the global A-048 attempt record and do not repeat the successful canary.
Next inspect the exact native_get_sync/cache path identified in C-276 before reading RID state;
Lazy getters, factories, mutable interceptors and default DTOs are not a current-state sample.
The installed Fly 1.19.4/ARMv7 reports, samples and current steps are in
[23_RC2_LIVE_RUNTIME.md](23_RC2_LIVE_RUNTIME.md). The two FLYC candidates are closed by
C-227--C-230, not awaiting another parameter probe. The requested control target also includes
Basic/UAS ID, aircraft position and operator position; keep Operator ID separate and map each
field's owner/readback/RF correspondence independently. Synthetic codecs remain offline.

1. Read [AGENTS.md](../AGENTS.md) completely.
2. Read [02_EVIDENCE_REGISTER.md](02_EVIDENCE_REGISTER.md) and
   [evidence/claims.csv](../evidence/claims.csv).
3. Read the topic document for the selected surface.
4. Check [09_NEGATIVE_RESULTS.md](09_NEGATIVE_RESULTS.md) before repeating an experiment.
5. Check [10_HYPOTHESES_AND_UNKNOWNS.md](10_HYPOTHESES_AND_UNKNOWNS.md) and
   [12_CURRENT_BLOCKERS.md](12_CURRENT_BLOCKERS.md) before promoting an inference.
6. Verify artifact identity in [11_ARTIFACT_REGISTER.md](11_ARTIFACT_REGISTER.md) and
   [evidence/artifacts.csv](../evidence/artifacts.csv).

## Current source-of-truth order

1. This repository's normalized claim/artifact CSV files.
2. Topic documents in this repository.
3. Pinned redacted public documents in the FindUAS repository at or after commit `15f331c`.
4. Exact local audit reports for v0.10 and V2.3, if legally available to the researcher.
5. Older progress indexes only for history; they contain superseded v0.8/V2.1 wording.

The current probe is A-039 v0.12. A-001/v0.10 and A-038/v0.11 are historical and their installers
are archived; V2.2 remains rejected and V2.3 remains unexecuted.

A-039's COMPLETE report and its fixed sample export have been received (C-236--C-238). The
operator then installed original Fuli and confirmed DevActivity opens (C-242). Its post-install
COMPLETE report is now received (C-245): updated-system=true, original code/hash/signer and
two checked DEX entries unchanged, all three component entries enabled, and Fly/ART identity
stable. Earlier directory ABSENT results remain the Observer app's view. C-246 now records
the actual Shell `id` photo: UID/GID 1000/system and `system_app:s0`. C-247 records `/data`
and `/data/app` mode 0771, system:system, labelled `system_data_root_file` and `apk_data_file`
respectively. C-248 identifies directory cleanup in the examined PackageManager scan and
reconciliation paths; those two rules skip ordinary non-APK files. The candidate is a separate
regular `.so` directly in `/data/app`, not a new subdirectory. C-249 shows seven subdirectories:
DJI_FLY at 0777 and six randomized installation roots at 0775, all system:system/apk_data_file.
`finduas_A040_canary.so` was absent. F1 passed independent review, shell syntax checking,
three Java Runtime.exec launch cases and seven shell-body cases with mocked Android commands
(C-250). C-251 records one new SD file and matching full readback. C-252 shows the correctly
entered wrapper failing to open the literal wildcard path; it did not enter F1. C-253 then
records `ls: /storage: Permission denied`; this does not test a known child file. C-254
shows `/storage` mode 0710, shell:everybody and `mnt_user_file`, giving Fuli search but no
directory-read permission; the API identifies one mounted public volume. F2/A-044 uses that
private exact entry without global enumeration. Independent diff review, `sh -n` and eight
host fixtures passed, including an actual search-only mode-0111 parent (C-255). C-256 records
one new `Download/F2.sh`, 6,845-byte matching full readback, and F1 moved to
`Download/FindUAS/Archive/F1.sh` with matching readbacks and no deletion. C-257 now records
F2 execution and a fully received 2,553-byte report passing schema/end/parser validation. It is
INCOMPLETE only because `pidof dji.go.v5` returned rc=1 and empty output. System/system_app,
SELinux Permissive, ro.debuggable=1, wifi_on=0 and A-040 source size/hash passed. C-258 then
records Fly's HOME main-process entry in AMS. C-259's separate proc read then returned a path
error without a mount-options line. F3/A-045 now combines these observations in one window:
C-260 records the 18/14 passing test sets, and C-261 records 10,611-byte matching staging/readback
and F2 moved to Archive with matching readbacks and no deletion. C-262 then records the live
F3 report and heredoc compatibility failure; the current step is in
[the runtime topic](23_RC2_LIVE_RUNTIME.md#下一步).
Unlock registration and the deferred certificate-page screenshot are not prerequisites for
the independent RID-state route.

After each material result, append the completed action to the existing timeline, synchronize
the local evidence/source records and run repository checks. Local commits remain allowed;
the latest user instruction pauses GitHub pushes only. Do not resume pushes until the user
restores authorization. Preserve historical pushed results. Keep the current operator state
in the runtime topic and this handoff.

## Topic entry points

### ADB loader contingency: exact v07 gate and pending identity baseline

Read C-174--C-179/A-029--A-032 in the two registers, then read
[08_ANDROID_ADB.md](08_ANDROID_ADB.md), H-30, and B-21 before touching the device.

Exact target-package facts:

- RC331 `07.00.0100` signed system aggregate: `1,446,604,800` bytes, SHA-256
  `296cfa63e3c6b011fd1ee8dd911c11f64dac9d34a8424a6fbb95b0c237ab1ae3`; its signed config and
  `0205` module passed the recorded PRAK/checksum chain.
- APEX `adbd`: `1,497,232` bytes, SHA-256
  `b300d9bb90f5941fe2952bc9f6dacc30e639a498be4435f59a4ae95134bd5422`. Runtime path is
  `/apex/com.android.adbd/bin/adbd`; extracted backing path is
  `/system/apex/com.android.adbd/bin/adbd`; `/system/bin/adbd` does not exist in the target image.
- Exact `handle_packet(CNXN)` checks `mp_state=production && dbg_cnt<1` and returns before ordinary
  AUTH. This closes target-package code, not the live property values or taken branch.
- Exact packaged `dpad_fuli.apk`: `8,849,471` bytes, SHA-256
  `58b176eb1e17cacb7522914d282a69a677603ea9026993fc143c6a390211e44f`; its operator Shell page is
  exact-v07 static evidence. Both pre- and post-reinstall reports match the original package
  identity (C-237/C-245); post-install entries are enabled. C-246 separately verifies actual
  Shell UID/GID 1000/system and `system_app:s0`; C-247 supplies parent-directory observations.

A-032 changes only `cset w21, lt -> mov w21, wzr` at the exact gate-value instruction and preserves
the normal TLS/auth target. Its `1,497,232`-byte SHA-256 is
`3fceaa1724a77a153c17f725a2e3f3001b0543e31e0830aca0c77d785df9225f`. It is already staged with
matching fresh size/full readback as removable-SD `Download/RC2_ADBD_CNXN.bin`; no binary is in this
repository.

This historical contingency remains `NOT ADMITTED`: no internal copy, chmod, execution, daemon
stop or new ADB response has occurred through A-032; C-246 records the separate Fuli Shell.
Section 11 of the ADB topic preserves its proposed baseline-dependent sequence. It is not the
current operator instruction. Directory contents and storage metadata are complete
(C-249/C-254), F2 report receipt is closed (C-257), and AMS process identity is recorded
(C-258). The staged F3 report replaces further manual proc reads; no reopening Fly, rerunning
F2 or package installation is needed. Follow
[the runtime topic](23_RC2_LIVE_RUNTIME.md#下一步) before selecting a later device action.

Do not return to first-packet public key, WebADB, banner/MAXDATA/checksum variants, USB-debugging
toggle, wireless ADB, or `tcpip 5555` before that discriminator. Never use bootloader/fastboot/OEM
unlock, boot/vendor_boot/vbmeta/Magisk/TEE/QFPROM/eFuse or firmware flash.

### Closed generic-attach path: independent `RIDCtrlEnable`

Read RID-002C in [05_RID_CONTROL_SURFACES.md](05_RID_CONTROL_SURFACES.md), H-27 in
[10_HYPOTHESES_AND_UNKNOWNS.md](10_HYPOTHESES_AND_UNKNOWNS.md), and B-20 in
[12_CURRENT_BLOCKERS.md](12_CURRENT_BLOCKERS.md).

Current exact anchors:

- current SKYROVER `1.2.0` exposes Boolean GET/SET/Listen `RIDCtrlEnable` separately from France
  `EIDSwitch`;
- native mapping: `RIDCtrlEnable -> rid_ctrl_enable_0`;
- parameter hash: `0x3CBD864F`, wire LE `4F 86 BD 3C`;
- commands: FLYC `03/F7` metadata, `03/F8` read, `03/F9` write;
- static modern default route: sender type/index `2/4` (`0x82`) to receiver `18/4` (`0x92`);
- A-023 reached the Binder callback path but target F7 ended in `ECode 1` without a same-route
  positive control.
- A-024 `0.4.1-research` was installed and tested known maximum height on legacy
  `0A:05 -> 03:00` and modern `02:04 -> 12:04` Binder routes. Both returned `ECode 1` with no data
  after about 3.1 seconds, so exact code did not send target F7/F8/F9.

Do not repeat the generic F7 attach route or change only sender/receiver tuples. Reopen this exact
parameter only after finding a materially different official in-process owner/authenticated route
or a verified WA150 handler. A-024's passive timeline is also complete: it produced zero callbacks
while an independent detector confirmed real motor-on RID, so that third-party listener is a
false-negative truth source and must not be repeated.

The independent USB DUML path was separately instrumented in
[`host-tools/rid-switch-tool/rid_switch_control.py`](../host-tools/rid-switch-tool/rid_switch_control.py).
Its source-level gates do not constitute a live switch. C-227--C-230 now record a successful
direct-USB FLYC positive control on `01.00.0600` and positive-controlled absence of both
`rid_ctrl_enable_0` and `EU_CE_enable_c0_rid(_0)`. No target baseline or write followed. The public
index mapping is not authoritative: the live C0 block shifts +1, and its sampled zero-range
registration flags cannot substitute for the absent target. Keep these tools as historical
source; do not repeat the same target/route variants without new owner, handler or version
evidence. The conclusion is limited to the tested surface, not DJI Fly or encrypted `0802`.

### Closed passive branch: A-026 gated FlySafe inventory

A-025 remains the fixed V3/V4 baseline but the user has now reported its installation complete;
launch, execution, and result remain unknown (C-150/C-151/C-154/C-163). Do not run it merely to
produce another ambiguous negative because it lacks the current-connection support/version gate.

A-026 `0.6.0-flysafe-gated` / code 9 was the exact gated candidate (C-160--C-165). Its `135,525`-byte
APK SHA-256 is `3c2ae42ac9f19a9e3dfe669ed6357bb8d2f1c38568af6a0f8d8b8f677fcbfec4`.
It is staged as removable-SD `Download/FindUAS_A026_GATE.apk`; same-session readback SHA matched and
a new MTP session confirmed one unique short name with the registered size. The operator subsequently
reported installation complete and ran the instructed bounded gate flow. The 60,003 ms window ended
`GATE_UNOBSERVED`: both gate inputs and every callback-class count were zero, so no permit was issued
and `11/11 request count=0` (C-165).

A-026 uses one tx2 listener for `03/09 + 03/42`, requires complete actual-route equality, and signs no
same-process permit on malformed/failure/conflict/deadline/cancel. Only support=true plus V3/V4
admits the fixed tx4 `11/11` group/page traversal; page 0..127 and initial + two 6-second retries are
strictly bounded. Its internal sender has no `11/12`, output is privacy-reduced, and process death
cleans the listener.

Two clean build pipelines were byte-identical; 63/63 tests, lint 0 errors/13 warnings, v2 signature,
zipalign, zero `uses-permission`, and no native/network/socket/shell path passed. This is still an
Admin APK: external Developer Assistant is outside the internal allow-list, and gated F9/EID/OPID
writes remain. Never call the whole APK read-only.

That first passive gate step is now complete and negative only for this third-party observation
surface. Treat the absent gate as observer unavailable, not unsupported/no-entitlement/no-RID.
External Binder cannot see DJI's device token; full-route/window equality is only a proxy. Do not
repeat the identical passive window without a materially new official in-process/current-state owner,
safe replay/trigger, or route fact. Only an admitted V3/V4-equivalent state may lead to one bounded
query.
Only a canonical count-consistent result containing a genuine type-6 record may advance to a
separately reviewed same-ID baseline/readback/restore design; RF truth still requires
operator-initiated motors and the independent detector.

### Current result: A-027 active read-only inventory

A-027 `0.7.0-flysafe-direct-readonly` / code 10 is C-166--C-169. Its 196,569-byte APK SHA-256 is
`aa4bcd9c8aa96870cfbae1ba326d366cb8854a50ef4aff223f7bce4290ddcd81`. It admits one fixed
system-Binder transaction-4 `02:04 -> 12:04`, `11/11` V3/V4 group/page traversal, with no route scan
or application-level retry. The product-139/RC331 route is a local exact-static candidate; pinned
`fpv_live`, `dji-firmware-tools`, DJI Cloud API, and MSDK sources do not independently confirm it.

Final audit: 127 tests with zero failures/errors/skips, lint 0 errors/15 warnings, two byte-identical
clean builds, v2 signature, zipalign, zero permissions, and no native/network/socket/shell/
external-process path. MTP staging as `Download/FindUAS_A027_RO.apk` passed fresh size and readback
SHA checks.

The operator installed and ran the active button. It returned
`DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`, stage `ProtocolException`, with
`11/12 request count=0`. No canonical inventory formed and no set-enable request was sent. The UI
did not expose the exception message, so callback, ccode, group, page, and terminator are not yet
separated. Do not call this unsupported, empty inventory, no `RID_UNLOCK`, RID off, or RF evidence.
The result image, identifiers, raw replies, and license material are excluded.

A-028 was the next read-only diagnostic and preserved command, route, selectors, retries, and write
boundary. A materially different official owner remained the parallel alternative.

### Current result: A-028 safe diagnostic

A-028 `0.7.1-flysafe-direct-diagnostic` / code 11 is C-170--C-173. It changes only UI diagnosis over
A-027: static-safe `ProtocolException` text, numeric unexpected group/page ccode with page index,
and terminator data length. Command, fixed route, V3/V4 selectors, and write boundary are unchanged.

The 197,061-byte APK SHA-256 is
`d7c32636e19d1bce1b8b8994206355f42d0278b2f15048b14a948a8bbda1d540`. 127 tests,
lint 0 errors/15 warnings, two byte-identical clean builds, v2 signature, zipalign, zero permissions,
and no packaged native library passed. It is staged as removable-SD
`Download/FindUAS_A028_DIAG.apk`; fresh listing size and readback SHA matched.

The operator installed and ran it. The display showed
`DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`, `ProtocolException`, detail
`group transport callback failed`, and `11/12 count=0` (C-173). The fixed group selector had no
successful transport callback; group protobuf, page, and terminator were not reached.

The next read-only change is to display the already existing Reply failure/ecode/callback diagnostic.
Do not repeat the same black-box request or retain result images, identifiers, raw replies, or
license material.

### Current route: ART TI exact-owner query

The materially different official-owner route is now observed on the disposable Android 11
emulator (C-188--C-191). Standard JVMTI 1.2 crashed the exact non-debuggable target before logging
and is retired for RC 2. ART TI `0x70010200` attached cleanly, found exactly one loaded unlock/event
owner pair, obtained a nonzero current device ID and dispatched the private FC-license query once.
With no aircraft, the callback returned `417`; the DJI Fly PID was unchanged.

The public source-only experiment loads an independent callback DEX and parses only the embedded
license-group envelope. It reports counts, type-6 level and status Booleans, keeps a unique existing
ID in memory only, passes five synthetic host cases and builds its AArch64 agent. See
[jvmti_flysafe_inprocess_query](../experiments/jvmti/jvmti_flysafe_inprocess_query/README.md).

This closes owner/callback plumbing but not RC 2 loading. An ordinary third-party APK cannot attach
into DJI Fly by containing the agent. The next device dependency is a usable userspace ADB shell or
another proved same-process loader, followed by one query-only attach with a fresh callback and
unchanged target PID. Do not add the setter before that RC 2 success callback identifies exactly one
canonical type-6 candidate.

### Historical external comparison: A-033 plus official DJI Fly UI

A-033 `0.8.0-flysafe-diagnostic-export` / code 12 is C-181/C-182 and A-033. It preserves A-028's
fixed `02:04 -> 12:04`, `11/11`, V3/V4 selectors and direct-button zero-`11/12` boundary. It adds
zero-permission MediaStore output at `Download/FindUAS/FindUAS_RID_A033_latest.txt`; reports contain
the privacy-reduced Reply failure/ECode/callback diagnostic but no raw payload or license identity.

The `204,449`-byte APK SHA-256 is
`8ce8e0c13ecfcf69517a64e809a475b79bbc750124225744b6b35f281d3d7177`. 132 tests, lint
0 errors/15 warnings, two byte-identical clean builds, v2/zipalign, zero permissions and no
native/network/socket/shell/external-process path passed. It is staged as removable-SD
`Download/FindUAS_A033_DIAG_EXPORT.apk`; fresh readback size/hash matched. It has not been installed
or run.

A-033 remains useful only as a comparison with the failed external Binder route. The ART TI owner
query above is now the next execution route after an RC 2 loader is admitted. Manual inspection of
the official list remains optional supporting context and must not toggle a row.

Do not interpret a generic row switch as a verified RID switch. Exact current protected Java is now
recovered: it closes the existing-ID native action but defines only license types 0--4 plus unknown,
protobuf fields 1--5, and sends unknown records to a tolerant polygon fallback (C-185/C-186). Thus
current UI type-6 rendering is negatively closed rather than merely unknown. Live RC 2 inventory,
semantic type-6 identity, aircraft application, restore semantics and motor-on independent RF A-B-A
remain open.

### RID working status

Read:

- [04_STATE_ACCOUNT_LIMITS.md](04_STATE_ACCOUNT_LIMITS.md)
- [05_RID_CONTROL_SURFACES.md](05_RID_CONTROL_SURFACES.md)

Static anchors:

- product-139 `PrepareModules -> RidImportModule::Setup -> OnRIDWorkingStatusPush`;
- `KeyRidWorkingStatusPush`, command `0x11/0x1C`, listen/update-only with no GET/SET/action;
- seven-byte raw layout: bits 0/1 RID/EID support, bits 8/9 RID/EID normal, four-byte area,
  one failure byte;
- preserve raw failure reason before a higher model drops it.

Missing evidence: synchronized motor-off/motor-on onboard state plus independent receiver data. The
current app has no active status GET builder; observe the official owner's natural push passively
rather than inventing a request.

Do not treat `UAVOIDManager.native_SetOIDReportEnable(false)` as the missing RF switch. In the exact
`1.21.10` native path it selects app-side China OID network submission versus `DirectSuccess`; no
aircraft broadcast write or gate getter exists. `CN_OPERATE_ID_EFFECT` and
`dji_fly_rid_cloud_control_v2` are distinct namespaces. Read RID-011A/011B/011C in
[05_RID_CONTROL_SURFACES.md](05_RID_CONTROL_SURFACES.md) before reusing any “report enable” name.
The latter is `KeyCloudControlData`, a separate value-routed SET-only `0x00/0xDD` transport. Its
success ACK/cache contains the request, not returned applied RID state.

### RID experiment control matrix

Read [19_RID_EXPERIMENT_CONTROL_MATRIX.md](19_RID_EXPERIMENT_CONTROL_MATRIX.md) before adding a
configuration field or UI control. The target now includes region-specific identity, status,
location-health, timing, managed policy, and a separate synthetic-source lane—not just one toggle.

Every item must be labelled `READ-ONLY LIVE`, `PASSIVE OWNER`, `STATIC LOCKED`, `MANAGED`,
`OPAQUE BLOCKED`, `LEGACY EXCLUDED`, or `SYNTHETIC SOURCE`. An exact static setter remains disabled
until live HostID, baseline, canonical ACK, independent readback, restore, persistence, and RF
A-B-A are all closed. Keep OPID, DIPS, China UOM, France EID, C0, type-6, app location, compliance
serial, LTE phone, and cloud-control as separate planes.

### China UOM identifier and real-name status

Read RID-005B/RID-005B2 in [05_RID_CONTROL_SURFACES.md](05_RID_CONTROL_SURFACES.md) before adding
any China item. Keep two owners separate:

- product-139 `OIDIdentifier` is a static `0x11/0xD6` eight-byte identity surface with fixed
  receiver `0x92`, 500 ms/retry 3, result at response byte 1, and GET value at bytes 2--9;
- conditional `UOMV1` status uses `0x11/0xD1`, receiver 2/0, request `[01,00]`, and appears only
  after runtime function ID `0x6C` admission;
- `SyncUOMRealNameStatus` enters an external account/network helper and has no setter or restore
  semantics.

The identifier GET builder's 16-byte request tail is not visibly initialized in current vendor
code; do not publish it as zero-filled or copy uninitialized behavior. A future diagnostic must
zero its own buffer, strictly require reply lengths 2/10, mask the returned value, and remain
static-locked until live admission/baseline/restore/RF gates close. For status, key-not-admitted and
returned `UNSUPPORTED` are different outcomes. Never log the identifier or opaque Sync material.

### Account and effective limits

Read [04_STATE_ACCOUNT_LIMITS.md](04_STATE_ACCOUNT_LIMITS.md).

Keep separate:

- local cached credential;
- server token acceptance;
- FC UID synchronization;
- configured max height/radius/radius-enable;
- effective runtime restriction and reason.

Do not infer login failure from legacy UUID Boolean values or configured limits.

### France EID same-owner route

Read:

- [05_RID_CONTROL_SURFACES.md](05_RID_CONTROL_SURFACES.md)
- [11_ARTIFACT_REGISTER.md](11_ARTIFACT_REGISTER.md)
- [12_CURRENT_BLOCKERS.md](12_CURRENT_BLOCKERS.md)

Stable static anchors:

- product candidate 139;
- `EIDSwitch`;
- `0x03/0x77`;
- receiver `0x92` before any live HostID override;
- GET `[02]`, SET `[00]/[01]`;
- GET ACK `[result,state]`, SET ACK `[result]`;
- timeout 500 ms;
- retry at request `+0x08`, receiver index at `+0x19`;
- `JNIRawData.native_SendData` as the narrow raw-ACK candidate.

Open gates include exact live identity, privileged caller, V0/V1, independent V2.3 audit,
exception coherence, writer epoch, and terminal quiescence. No live GET/SET path is admitted by this
archive.

### FlySafe type-6 lane

Static mappings:

- query `PackType 0x38 -> 0x11/0x11`;
- set-enable `PackType 0x39 -> 0x11/0x12`;
- V2 one-byte index query; V3/V4 group/status-protobuf flow;
- product-139 final receiver `0x92` for V2/V3/V4;
- separate MSDK 5.18 schema type 6 `RID_UNLOCK`, levels 1 EU and 2 China;
- retained official consumer design maps enabled + region-matched + product-supported type 6 to
  `broadcastRemoteIdEnabled=false` / `NO_BROADCAST`, but that branch only changes the SDK status
  object, starts behind an immediate return, and does not itself send an aircraft command.

Official acquisition/sync chain:

- the type-6 application is on the official FlySafe website, not a recovered type-6-specific DJI Fly
  page; normal Remote-ID registration and generic Unlock-a-Zone are separate;
- website access requires the qualifying account background, exact product
  `support_unlock_type: Rid`, and an account device record matching product and FC serial before an
  official reviewed application;
- current DJI Fly requires a nonempty login token to fetch user context and signed license groups,
  selects server-supplied V2/V3/V4 onboard data by the FC's current support/version/target, imports
  that blob, pulls aircraft inventory, and toggles only an existing license ID;
- server approved/downloaded, FC imported, inventory visible, enabled, aircraft consumed, and
  motor-on RF effect are distinct states. Mini 5 Pro product eligibility remains unknown, and public
  MSDK support does not include it.

Current Fly correction: its exact typed `LicenseData` parser handles fields 1--5 and sends field 7
to `UnknownFieldSet`; only the separate MSDK artifact typed-decodes field 7 as `LicenseDataRID`
(C-152). Its `11/12` setter is generic ID-plus-action, and no current app xref connects type 6,
field 7, or enabled state to WA150 `0802`, motor/armed state, or BLE/Wi-Fi enable (C-153). Receiver
`0x92` is not firmware-module identity.

A-025 is user-reported installed but has no execution/result. Exact A-026 implements and audits the
passive `03/09 + 03/42` gate, was staged/installed, and completed one 60,003 ms live run with
`GATE_UNOBSERVED` and zero `11/11` requests (C-165). Defaults `255/false` and missed pushes remain
unknown. A-026 sends the fixed query only after its same-process V3/V4 permit; this run therefore
cannot turn observer absence into unsupported state.

A-027 then ran the fixed active V3/V4 route and ended
`DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS` at `ProtocolException`; it displayed zero `11/12`
requests (C-169). Because the current UI did not expose the exception message or lower-level stage,
this is not a canonical inventory, support, entitlement, or RF result.

A-028 preserved the same protocol behavior and localized the result to
`group transport callback failed`; `11/12 count=0` (C-173). Protobuf/pages/terminator were not
reached. Its next discriminator is Reply failure/ecode/callback detail, not another identical run.

Missing: the two owner-visible official eligibility booleans, an admitted RC 2 loader for the
observed ART TI query, a canonical success callback, genuine account item, FC
import, aircraft-side consumer, same-item baseline/restore, and RF. If separate approved
instrumentation obtains raw unknown field-7 bytes, keep them only in
excluded private evidence; never create, transfer, or publish license material.

### Region and RF policy

Read [06_REGION_RF_POLICY.md](06_REGION_RF_POLICY.md).

Keep FC, Sky, Ground, RC/app policy, SDR, Android Wi-Fi, and measured RF as separate columns. A
new observation belongs at one evidence level only.

### Firmware and Android

Read:

- [07_FIRMWARE_TRUST_BOUNDARY.md](07_FIRMWARE_TRUST_BOUNDARY.md)
- [08_ANDROID_ADB.md](08_ANDROID_ADB.md)
- [15_LOG_INDEX.md](15_LOG_INDEX.md)

Do not redistribute the local binary corpus. Reproduce static claims only from legally obtained
inputs whose hashes match the artifact/source register.

Public product metadata now independently matches WA150 `0802` versions in both 0600 and 0700, and
public BLE/network advisories make it the strongest network-service repair owner candidate. This is
not a RID ownership proof or firmware-modification path. The current public search found no
plaintext, target key, trust-root replacement, recovery image, exact 0700 diff, or reproducible PoC.

### NLD FCC comparison

Read [16_NLDFCC_STATIC_ANALYSIS.md](16_NLDFCC_STATIC_ANALYSIS.md) before using the NLD or FreeFCC
profiles as protocol evidence. The files are exact public-prior-art matches but have no found NLD
runtime reference. Keep the normal-FCC native payload, C0/VPN orchestration, parameter editor, and
Remote ID claim as four separate evidence paths.

The normal-FCC outer envelope, signed entitlement, offline cache, command JSON schema, and DUML
framing are statically closed. Do not repeat superseded notes claiming hex envelope fields,
lowercase serial normalization, or a zero-length online HMAC key. The actual command plaintext is
still missing because the package contains no real response/blob. Never publish the embedded
symmetric master, entitlement, cache, serial, or device public key.

### Drone-Hacks comparison

Read [17_DRONE_HACKS_STATIC_ANALYSIS.md](17_DRONE_HACKS_STATIC_ANALYSIS.md) before using
Drone-Hacks as protocol or firmware precedent. Keep these layers separate:

- exact signed local client identity;
- generic local DUML/USB/ADB/firmware/parameter executor;
- authenticated server-defined target jobs;
- one-time FCC and separate FCC ModBox compatibility;
- firmware-resident CFC on explicitly listed products;
- explicit RID feature/command/readback, which was not found.

Do not map `wm1695` to Mini 5 Pro; the public definitions map Mini 5 Pro to `wa150` and `wm1695` to
O3 Air Unit. Do not infer software or RID support from the public FCC flag or hardware ModBox list.
The Debug dictionary numerically maps `RID_INFO` to `0x11/0x1A` and `EID_INFO` to `0x11/0x35`, but
it disagrees with current DJI Fly at `0x11/0x0C` and `0x11/0x1C`. Use it only to classify passive
traffic or seed an exact current-handler search; do not construct a request from the label alone.
The useful next handoff question is whether WA150's authoritative RID owner can be closed in verified
plaintext or an exact live read-only path—not how to invoke the generic custom-packet engine.

### Legacy DroneID comparison

Read [18_LEGACY_DRONEID_DETECTION.md](18_LEGACY_DRONEID_DETECTION.md) before reusing
`DataFlycDetection`, `fc_monitor`, or the NDSS DroneID result. Keep these facts together:

- `0x03/0xDA`, subcommands `0x05`/`0x06`, is a high-confidence independently reconstructed match,
  not a tuple disclosed by the paper;
- the paper did not identify the exact switch-test model/firmware or physical source route;
- RF packets continued and selected legacy values became `fake`;
- the target was proprietary OcuSync/AeroScope DroneID, not ASTM/FAA/EU Broadcast RID;
- old generic class presence does not establish a WA150 handler.

Use the tuple only as a static search signature. Do not add it to a current product sender or UI.

## Offline tasks available without device access

- independently audit V2.3 exact bytes and its audit script against hostile mutations;
- normalize claim/source links and add missing exact revision pins;
- reproduce protocol layouts from public MSDK and pinned prior art;
- write synthetic state-machine tests for account/limit/RID evidence classification;
- audit CSV/Markdown consistency and privacy patterns;
- model route mutation and callback quiescence with synthetic interleavings;
- compare public versions without copying vendor code into this repository.

Results from synthetic models remain `STATIC` or `INFERENCE`; they do not become live evidence.

## Recording a new live result

Record only redacted values and include:

- date and displayed version;
- exact action count and route class;
- baseline reads and positive controls;
- strict matcher and timeout;
- result and error classification;
- forward readback;
- restore/final readback, if any state changed;
- whether motors were operator-started;
- whether an independent RID receiver or calibrated RF instrument was online;
- effects that were not measured.

Update claim CSV, topic document, timeline, negative/hypothesis/blocker tables, artifact register if
applicable, and changelog together in the local working tree, then validate before a local
commit. GitHub pushes remain paused until renewed user authorization.

## Publication checks

Run:

```sh
git diff --check
ruby scripts/check_markdown_links.rb
ruby scripts/check_evidence_csv.rb
sh scripts/check_sensitive_patterns.sh
```

Then inspect the staged file list. Independently written source/tests, Markdown, CSV, scripts,
license and repository metadata are expected. APK, SO, firmware, captures, key files, build
directories or host-local paths are
release blockers.

## 2026-08-30 takeover checkpoint

Start with [`../NEXT_AGENT_HANDOFF_PROMPT.md`](../NEXT_AGENT_HANDOFF_PROMPT.md), then read this file,
[`12_CURRENT_BLOCKERS.md`](12_CURRENT_BLOCKERS.md),
[`20_OFFICIAL_FLYSAFE_UI_PATH.md`](20_OFFICIAL_FLYSAFE_UI_PATH.md), and claims C-188--C-231.

Do not repeat these emulator-closed routes on RC 2:

- standard JVMTI 1.2 late attach;
- the carrier's ordinary installed `/data/app/...==/...so` command;
- a generic `trace_data_file` copy;
- an uncommitted PackageInstaller `apk_tmp_file` staging directory;
- the old external Binder F7/F8 route variants or passive `0x11/0x1C` listener.

The original local corpus has been located. Rehashed core DJI Fly/RC331 inputs and selected
A-032/A-033 outputs match their registered identities; no vendor file or private log is imported.
This does not promote the inputs to installed/mounted RC 2 facts or change artifact admission.
The bounded sandbox search did not find the latest 1558-slot/915-name enumeration output or a
completed C-207 timeline. Check old task outputs and existing local history before repeating any
collection; absence from that search is not proof that the records are lost.

Installed-package identity, actual Fuli Shell identity and parent-directory observations are now
recorded in C-245--C-247. C-248 narrows the candidate to a regular `.so` directly in
`/data/app`, with no new subdirectory; C-249 found no matching candidate basename. F1/A-043
staging/readback is closed by C-251. C-252 did not enter the script; C-254 now supplies the
private storage entry and parent permissions. F2 execution/report receipt are closed by C-257;
C-262 establishes live hidepid=2 and the F3 heredoc defect. The corrected F4 report supplied
a stable AMS baseline (C-267), and A-048 subsequently loaded through the verified ordinary-file
path, returned native identity/API success, and had its file removed (C-273--C-275). Advance
the exact RID owner/cache work in C-276; further query execution keeps its own callback and
process-identity checks. The
independent userspace-ADB contingency retains its own baseline and recovery gates.

In parallel, map Basic/UAS ID, aircraft position, operator position and Operator ID independently
using [19_RID_EXPERIMENT_CONTROL_MATRIX.md](19_RID_EXPERIMENT_CONTROL_MATRIX.md). Recover or
complete C-207's written standard-bearer/motor-timing record using
[`21_C207_MOTOR_RID_ABA_OBSERVATION_FORM.md`](21_C207_MOTOR_RID_ABA_OBSERVATION_FORM.md).
No state-changing path follows until its own baseline, route, readback, restore, persistence and
RF design is closed. Synthetic fixtures remain offline.

The existing FindUASMac persisted history was located separately through its source-configured
Application Support location. A bounded read found no explicit motor-transition or aircraft-air-
bearer fields. The writer rate-limits persistence per UAS to one row per two seconds, so rows are
not RF packet counts and do not close C-207. Identifiers, coordinates and raw records stay private.
