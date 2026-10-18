# Handoff for researchers and coding agents

## Start here

Latest continuation (2026-10-18, C-483--C-488): the agreed RedFly functional static review is complete. Read
[the report](26_REDFLY_FUNCTIONAL_REVERSE_ENGINEERING.md), [feature index](../evidence/redfly-full-functional-review.json)
and [matrix](../evidence/redfly-feature-matrix.csv). It covers A-104 outer UI and A-105 identified modifications/necessary
host dependencies, reusing C-476--C-482. Device support, readback/restore/persistence and RF remain unverified where stated;
no module was built or deployed. Do not repeat the closed menu/inventory work without a new version or concrete gap.
Use the existing findings to scope an independent module and fixed-version adapter if implementation is requested.

Prior continuation (2026-10-18, C-474/C-475): selected Fly1.21.10 RID bodies read DeviceId and construct caller18/4;
DeviceId/ProductType equivalence and actual binding are unknown. Fly1.19.4 C-286/C-287/C-291 remain unchanged.
RC331 packaged sec_type2 maps to a dji_verify command and the inspected same-name signature/extraction implementation;
live config/PATH binding is unknown. This is separate from dji_decrypt/QSEE and supplies no STUE key or device/RF control.
Details and exact evidence boundaries are in firmware topics21/22.

Prior continuation (2026-10-18, C-471--C-473): 22 carrier directory/map records and four analysis-only views are
checked. Selected Java bodies connect cached client-location to native serialization; valid Android/default altitude
has a conditional meters/WGS84 contract. The inspected branch has no hasAltitude check and can mix newer network
coordinates/time with older GPS altitude. New message times do not prove fresh fixes. Actual provider/valid altitude,
owner/readback/restore/RF, original DEX identity and STUE plaintext remain unestablished.

Prior continuation (2026-10-18,C-466--C-470): selected Android upgrade paths yield no STUE consumer; exact upstream
location type/provider/epoch seconds refine C-126 and correct invalid-coordinate dropping. Conditional HostID routes
and five payload-only CLIs are verified within their offline scopes. A-0661200 is reverified; only A-092 wa140bat1100
is a new distinct container,both stillSTUE with five other1100 variants uninspected. No device,actual control-panel
operation,STUE plaintext or RF success. The final continuation sections carry exact boundaries.

Prior continuation (2026-10-18,C-463--C-465): both status parsers accept a7-byte minimum prefix with private tails;
36 host tests pass. Exact JNI bytes establish22-byte marshalling/84-byte success payload, and A-078 v3 is corrected
with explicit inputs; its4 tests and controlled native components/fragments pass. No complete handler, transport,
APK deployment or RF validation occurred. The control-panel goal and unavailable-device condition remain unchanged.
See the final continuation section; prior59 firmware tests are separate from this36+4 batch.

Prior continuation (2026-10-17, C-454--C-457): A-005's outer clear container contains encrypted TBIE/FLYA;
C-319 is outer-only and C-322 is retracted. Existing OTA integrity/provenance is rechecked, and A-083 bw_secure,
A-084 libtee_util and A-085 dji_decrypt are extracted but never executed. The static chain reaches protected
RPMB-root/HUK-backed TBIE derivation; root inputs and WA150 STUE's own owner/derivation are still unknown.
The fixed480-byte client is not a drop-in decoder for WA150's608-byte header/signature layout. No device is available.

Prior continuation (C-450--C-453): A-082 implements the pinned public-v2 single-key model, with six new
checks and the full 59-test suite passing. Three named hypotheses on real 2603 all miss. The inspected Assistant
method-4/register path preserves downloaded bytes through cache/tar/FTP; no STUE decoder was recovered within that
path. The 25 selected public-source copies add no STUE implementation. Method choice, downstream owner and STUE
applicability remain unproven; there is no device. See the final continuation section before selecting another route.

Prior correction (C-442--C-449): STUE remains unresolved; the Assistant vtable/IV/MD5/NFZ premises
are corrected. A-067/A-068/A-070 v2 passed the recorded offline checks, including ten fixed-WAES misses on 2603.
Read the [corrected checkpoint](../host-tools/firmware-acquisition/AIRCRAFT_STUE_CHECKPOINT.md) and the final audit
handoff section before continuing. There is no device available; the protocol CLIs are offline hex generators,
France EID/AirSense are not global RID control, and position composition remains unverified.

The following live-session continuation is retained history:

Historical continuation (C-310--C-315): B6 started and A060 completed once. Baseline/read/independent
cleanup all returned0, the10907-byte export and permanent receipts passed strict validation,
and PID/UID/APK stayed stable. All41 rows are nonempty;36 unique signed payloads verify with
the retained A057 point. These reduce to25 signed header/body messages and six whole-body
patterns:40 rows have13-byte bodies, one has26. Candidate13-byte segmentation gives42 segments
and six patterns; header+6 remains1. Segment byte0 is0/1, while the LE16 at+1 is2/3/4/5 and
bytes+3/+4 need separate-u8 versus mask interpretation. All remain unnamed under H-33.

No new manual step is pending. The bounded related-enum check found no mapping (C-315).
Next seek a13-byte-stride consumer dispatching on segment+1, including the second segment
of the26-byte body. Keep country mappings and complete payloads private. Do not replay A057 or A060. B6 has not received STOP;
retain its original history through any lease expiry. G HUB/host ADB stay off and the no-reset
MTP build remains mandatory. All new results stay local unless another push is requested.

C-273--C-275 close the real RC 2 A-048 loader experiment. The fixed system-mediated attach
succeeded in the existing Fly process, with matching native identity, successful ART TI/API
disposal, unchanged AMS PID/UID and unchanged APK. The verified ordinary file was removed,
independent cleanup found it absent, and B2 STOP/CLOSED STOP completed. A-040 remains unchanged
and unexecuted. Preserve the global A-048 attempt record and do not repeat the successful canary.
C-277--C-282 subsequently close the exact synchronous cache path and A-051 live read. One
cache call returned RID1/1, EID0/0 and failReason0; parse/disposal, file recovery and independent
absence readback succeeded with unchanged Fly PID/UID/APK. B3 STOP/CLOSED STOP is complete.
Preserve both A-048/A-051 permanent receipts. C-283--C-292 add the exact expiry/notification and
cloud-source chain plus A054 live comparison: ProductType139,41 rows,36 distinct candidates,
receiver18/4, candidate match1 and DEFAULT-match0. Its environment/file recovery, independent
receipts and B4 STOP are complete. Preserve A054's permanent receipt too. Next inspect matched
payload structure and its aircraft consumer; actual-area selection and applied readback/restore
remain separate. This historical state is superseded by the B6 continuation above.
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
the follow-on cache result in C-277--C-282: the first actual state has been received and the
probe/session recovered. Further timed sampling keeps its own process and record identity. The
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

### Current prepared action: B5

C-293 closes the hex-to00/DD byte boundary. A057/L4/B5 are now built, tested and SD-staged
(C-294/C-295). B5 started and the23-check baseline passed (C-296). MTP failed before STRUCTURE_READ was
allocated; the operator has been asked to reconnect only the RC-to-host USB cable. Retry in
the original session, collect one READ and the fixed private JSON, analyze matched/DEFAULT,
and independently clean the temporary file. No STOP was sent; retain the receiver during
continuing analysis. Keep A048/A051/A054 history and receipts untouched.

Latest recovery state (C-297/C-298): repeated connection interruptions ceased after G HUB and
ADB were stopped. Automatic whole-device USB reset is now blocked in the host build. The
operator chose controller reboot. Do not reuse a stale B5 worker marker; preserve old history
and explicitly recover the baseline-only session before preparing a new one.

C-299/C-300 close reboot recovery: the operator confirmed reboot/stable link, guarded MTP
reads succeeded, the old baseline-only session was archived under its original SID and one
fresh session was activated. No canonical CLOSED was fabricated. The next operator step is
one B5 launch; run a fresh baseline before the still-unexecuted A057 capture.

Current continuation (C-301--C-305): A057 completed once. Its826-byte private report has
97-byte matched/default policies, one matching row and nonempty DEFAULT. The structure is
20-byte header +13-byte body +64-byte P-256/SHA-256 signature over the first33 bytes; both
verify with one common private-retained verification point. Body+0 is1/0 and remains H-33's
unnamed switch candidate. Independent cleanup and permanent receipts are complete. No STOP
was sent. Continue offline aircraft00/DD owner work; do not repeat A057 or assume DEFAULT
is an off policy merely from its first byte.


### Current prepared action: B6 (C-308/C-309)

A060 exports the entire existing RID policy row set with one guarded MMKV decode and one
ProductType cache read, zero CloudControlData reads and no SET. It retains only country_code,
data_hex and product-blocked status per row, in an at-most32768-byte private JSON. The native
artifact is26624 bytes with the A060 hash in the artifact index. L5/A061 and B6/A062 are pinned
and fully SD-readback verified. B5 is now canonically closed; preserve its completed history.

After the already-requested B6 startup, keep one session and read only the newly prepared
CATALOG lane. Validate native enter/export/result, file length/counts and immutable receipts.
Use existing envelope/P-256 verification on all nonempty rows and compare body-byte domains
without assigning field names. Keep the receiver available during offline analysis until explicit
STOP or lease expiry. Full payloads and country rows stay in excluded private storage.


### Completed B6 capture (C-310--C-314)

The prepared A060 action is complete:23 successful baseline checks, one MMKV decode, one
ProductType query, zero CloudControlData queries, stable target, saved/private-validated report
and independently absent temporary file. Its copy/attempt records are permanent. Preserve all
three collected tasks and the private receipt/completion index. No additional capture is needed
to repeat the now-available global value-domain comparison.

Next, use the private2/3/4/5-to-config-label grouping to compare official enum definitions,
and seek the actual branch consuming segment byte0 and bytes3/4. The26-byte body supports
continued repeated-record analysis; header+6 is not that candidate count. The independent
envelope tool exposes this interpretation as HYPOTHESIS and all52 related public tests pass.


C-315 closes the bounded named-enum comparison without a match. Continue from actual receiver
control flow instead of reusing runtime-state/registration enum numbers as policy field names.


## 2026-10-16 firmware lane (C-316--C-322)

Six current modules were fetched over the official Assistant path and matched official size/MD5 plus
registered SHA-256 (C-316). RC331 `0205` decrypts fully and is byte-identical to A-030/A-031
(C-317/C-318). C-319 describes only outer clear headers; A-005/0200 contains encrypted inner TBIE/FLYA (C-454),
and C-322's all-RC-plaintext inference is retracted. WA150 modules
are `enc_key=STUE`; no public key, derived/mode/IV/v1-v2 brute is zero-hit (C-320), and the wa150
3072-bit PRAK is absent (C-321). A local PKCS1-v1.5 fallback was needed because wa150 signs PKCS1
while header_version2 makes the tool assume PSS.

Firmware samples and derived outputs are gitignored under
`host-tools/firmware-acquisition/firmware/`; layout and method are in its `EXTRACTION_NOTES.md` (an
excluded local file). Do not re-brute `STUE` without new key material, do not alias it onto an
existing key, and do not treat decrypt as live mounted or flash admission.

Next for this lane: obtain `STUE` (whitebox/TEE extraction or later public release) per B-23/H-34,
then decrypt `0802` and locate the RID broadcaster owner/enable parameter in plaintext before any
protocol validation. RC-side static work is unblocked and can run in parallel.

## 2026-10-17 audit correction handoff (C-442--C-449)

Start with the corrected [STUE checkpoint](../host-tools/firmware-acquisition/AIRCRAFT_STUE_CHECKPOINT.md).
The original address-dependent seed, MD5 KDF, nonzero IV and ordinary-firmware-to-NFZ claims are retracted.
The confirmed NFZ key is a constant 32-byte buffer, published only by length/hash, and its IV is zero.
One direct application to the exact 2603 chunk failed checksum; ordinary firmware dispatch must be traced independently.
Do not resume random pointer/tail sweeps or promote the NFZ helper to STUE without a concrete data-flow edge.

C-446 records the audited probe defects; C-447 records corrected implementation validation separately. A passing test or
fix does not retroactively validate the old C-326 sweep. Artifact size/hash and Markdown/CSV state must agree before handoff.
Raw binaries, key bytes, vendor disassembly and private evidence remain excluded.

The current user has no device. France EID, AirSense, EU C0 policy and app-location are separate surfaces; the old
"complete control"/"all preconditions met"/"only hardware values remain" wording is withdrawn. The six protocol CLIs generate
offline hex only, position encoding remains approximate, and WorkingStatusPush has no proven SET-to-applied/RF relationship.
Use docs/05 RID-002B, RID-003, RID-005C, RID-009 and RID-011C as the established semantic and live-evidence boundaries.

## 2026-10-17 public-v2 and method-4 continuation (C-450--C-453)

A-082 is a single-candidate checker, not a key search or plaintext exporter. It reads raw candidate key bytes from stdin,
verifies payload SHA256/encrypted checksum first, then tests the pinned AES-ECB-unwrap/AES-128-CTR model. Clear chunks
and storage gaps do not advance CTR; plain checksum includes decrypted padding. There is no signature check.
Its six new tests include an independent frozen OpenSSL mixed-chunk fixture; the retained full-suite log is 59/59.

Do not repeat C-451's three candidates without new input: NFZ32-as-KEK, WAES-decrypt(scram)-as-content16 and
WAES-encrypt(scram)-as-content16 all miss the exact 2603 checksum. Keep C-445 direct CBC and C-447 fixed-WAES results
separate. A checksum miss only excludes the tested interpretation; no valid STUE plaintext has been obtained.

C-452 follows only method 4 / DJIFirmRegisterUpgrader in the exact x86_64 UavService library: download callbacks
preserve/cache the buffer, size/MD5 checks retain it, tar packaging copies it, and FTP consumes it. New investigation
must establish an actual consumer edge or inspect an already available offline receiver sample; this does not prove
WA150 method selection, all-Assistant absence or a specific RC/aircraft/TEE key owner. Raw evidence stays excluded.

C-453 screened 517 fork metadata rows but inspected only 17 selected default-branch and 8 nondefault IMaH source
files; all are byte-identical to the pinned upstream and lack STUE. Do not present it as all-fork or whole-web coverage.
The current protocol/RID work remains offline, with the C-448/C-449 boundaries unchanged.

## 2026-10-17 RC331 protected-chain continuation (C-454--C-457)

The search for the RC331 components is complete: A-083/A-084/A-085 are identified, extracted from verified local
OTA inputs and statically traced. Do not list finding bw_secure as the next step. No new download, vendor binary run,
RSA reverification or live mounted identity was performed. The artifact register contains their exact identities.

A-005 has clear outer header/payload integrity and an encrypted TBIE/FLYA inner layer beginning at480 with ciphertext
at960. No FLYA plaintext is available. The six public-TBIE prefix probes were not full checksum exclusions.
The dji_decrypt client passes header scram through QSEE commands0x17/0x18 but assumes a480-byte header; current WA150
uses608. Do not execute the extracted client as a general STUE decoder.

The trusted-app key init reaches RPMB derivation type0x0c, CMAC label IMAGE ENC KEY/context TBIE and a protected
root read with HUK-backed unwrap/authentication. The TBIE context is assembled as an immediate, explaining the absent
literal-string hit. No device RPMB block, HUK output, root key or usable payload key was recovered. Mode constants1/2
are not independently named. Continue only from concrete available inputs or a separate STUE consumer edge; do not
assume RC/WA150 keys or schemes match, or infer that all offline methods are impossible.

## 2026-10-17 SDK keychain and position continuation (C-458--C-462)

The full goal includes a Remote ID switch and broadcast-parameter control panel, with unchanged per-control device/RF
acceptance. A-086's mapped dynamic table contains actual definitions, correcting the old embedded-only account.
A-087 uses Unicorn2.1.4 to run the complete Get(0x37) in isolated CPU memory:32-byte result, padding removal,
three block roundtrips and exact48-byte CBC rewrap pass. Only result length/hash is public; no Android OS/device runs.

At C-459, A-078 v2 selected the wrong key from ciphertext[:32]. That history remains retracted. C-464/C-465 later
establish22-byte marshalling and84-byte payload, and repair v3; no full handler, transport or RF validation follows. C-460 is a static bw_secure key/position envelope with unconfirmed numeric
algorithm enums; SDK/TEE key equivalence and RF position control are unproven.

A-088's inspected file-check/XMODEM path yields no STUE consumer; C-462's pinned independent sources and opened
official documents add no key/PRAK/decoder within their bounded coverage. No TA, updater or hardware request was run.
Keep these observations distinct from WA150 STUE and RC331 TBIE root-input gaps, which remain open.

## 2026-10-18 parser and payload-model continuation (C-463--C-465)

C-463 implements C-147's minimum7-byte status prefix in Java and Python. Unknown tails are copied/immutable and
excluded from display, repr or Python equality; existing fields, CRC/routes and sender gates are unchanged.
The Java parser/timeline15 tests and Python21 tests pass; no APK build/install or device action occurred.

A-089 matches the official APK member. Exact function bytes, mapped dynamic calls and original HMAC-map init show
22-byte marshalling,256 AES key bits,32-byte ciphertext and a final84-byte payload: LE32(80), ct32, originalIV16,
SHA256-HMAC32 over ct+IV. C-464 corrects C-414; C-415/C-426/C-427 helper facts are retained with key-bit units clarified.
C-467 clarifies pre-scaled lat/lon/alt inputs and epoch seconds; original altitude unit/reference and exact Java supplier
were unknown at that stage. C-473 later advances the selected Java/default-provider path with conditional units. This SDK fixed-IV path is separate from the QSEE random-IV branch.

C-465/A-078 v3 now accepts serialized22/key32/IV16 explicitly, removes v2's stored-key prefix, fake headers and256-byte
ct field, and passes4 independent/synthetic host tests. Original marshalling/packing instruction fragments and official
AES/HMAC helpers were separately checked under controlled buffers/registers/map input. No full handler, SendSetPack,
Android constructor or transport ran. Continue from concrete full-path/field-semantics evidence; an offline encoder is
not a device editor. Total host tests for this batch are36+4; C-450's59 tests are prior independent evidence.

## 2026-10-18 bounded Android upgrade continuation (C-466)

A-090 matches the existing official APK member and has not been executed. The inspected config extractor copies
chunk0; its helper returns pointers. The observed slot0x0b whitebox caller signs a version/timestamp request.
DeCrypt returns1 without callees. File-transfer bodies read/copy supplied data while updating MD5; the directly
inspected base header verifier uses a literal256-byte signature. None supplies a concrete target STUE consumer.

Preserve this selected-function scope. It does not establish WA150 runtime use, missing authentication throughout
the SDK, all-APK decoder absence or a new firmware key. Evidence/function identities are in firmware topic16;
raw vendor code, snapshots and local paths stay excluded. Existing STUE/root/RF gaps remain open.

## 2026-10-18 scoped routing and codec continuation (C-468/C-469)

C-385 is retracted: Characteristics+0x30 is callback-captured, not receiver. Conditional single/multiple HostID
selection feeds the actual SetReceiverIndex at base ELF0x2ec25c (req+0x19, flags+0x0a OR2). Free EID/position
KeyHandlers templates use virtual+0x10; preserve C-386's+0x128 only for the separate BaseAbstraction EID overload.
Six original-prefix/helper cases passed without a full SendSetPack/callback/initializer/transport or live owner.

The five legacy CLIs now emit payloads only; sender/receiver arguments and fake32-byte object headers are removed.
France EID,18B UOM,OPID GET02/DELETE01/SET0010+exact16,AirSense1B and empty height GET keep distinct business scope.
Eight schema tests/nine valid CLI cases/five obsolete-argument rejections are host-only results. OPID full20-character
validation is outside the codec; UOM GETzero tail is a local choice. No device, UI write or RF capability is established.

## 2026-10-18 exact location semantics and small-module continuation (C-467/C-470)

C-126 already supplied latitude/longitude×1e6 and altitude×100; C-467 closes the exact MobileDevicePositionMsg
constructor/40-byte SDK serialization,Java clientLocation():byte[] boundary and libc epoch-second timestamp.
Invalid finite coordinates clear the second field but continue scaling/time/queue construction. Do not call this
upload rejection or reinterpret the field as a proved receiver/GPS-quality enum. C-473 later advances the selected
Java/default-provider chain; actual provider/valid altitude/reference remain open. No new typed position editor or BroadcastRID/aircraft-navigation setter
is established; A-078 remains explicit22-byte input.

C-306's seven missing small entries was historical. C-323 already acquired A-0661200; C-470 reacquires the same hash
and inspects new A-092 smallest1100 wa140bat. Two containers are now checked,with five other1100 variants uninspected.
Both are STUE/PRAK with384-byte signature and verified outer digest/checksum,but no RSA verification,key trial,
plaintext or inner consumer. There is no duplicate artifact for1200 and no native-battery hardware inference.

## 2026-10-18 carrier views and selected Java location continuation (C-471--C-473)

A-093's22 BE directory entries match independent DEX maps. Four A-095--A-098 views preserve every byte after relative
0x20000; A-094 rebuilds only the header and protected string_ids from surviving constraints. DEX035/link fields and new
checksums do not establish original DEX identity, decryption, all-app unpacking or ART verification. Five segments with
protected type tables remain unknown. Tool input is explicit and fixed; output directory must be new and private.

Independent review confirmed four-view structure/code preservation and30 selected method IDs/prototypes/code offsets.
The Java chain reaches lifecycle registration, two caches, LocationCoordinate3D and JNI clientLocation. Valid Android/default
altitude has a conditional meters/WGS84-ellipsoid contract, but the method has no hasAltitude guard and can retain newer
network coordinates/time while copying older GPS altitude. NaN does not take its near-zero fallback. AMap/runtime choice
and separate GPS/barometric IClientAltitudeProvider remain distinct. Source-fix time/accuracy is not carried with the three
scalars; C-467's native message-construction epoch seconds do not prove fix freshness. Caches refresh on demand, not at1Hz.

Existing JADX1.5.6 performed selected static decoding/API reads; the Java review did not re-review native wire/clock behavior.
A-078 remains explicit22-byte input. Continue only from new concrete provider, owner or field/RF evidence; these static paths
do not admit device controls. Carrier/views/vendor code remain excluded. No device, STUE plaintext, actual control-panel
operation or RF success occurred; GitHub synchronization stays paused. Detailed offsets and limits are in firmware topic20.

## 2026-10-18 selector version and packaged verify continuation (C-474/C-475)

C-474 is an exact-version source distinction, not a numeric DeviceId/ProductType inequality or a bug in the historical
Fly1.19.4 tool. A-099 is the only new view used for this conclusion. Independent class_data decoding locates13 methods;
their code offsets match JADX API, while IDs/prototypes are retained for location.
The literal caller18/4 does not change generic KeyCloudControlData's value routing or add GET/applied/RF evidence.

C-475's package configuration condition does not establish live type2 selection: vendor config differs from the init
service's system path, whose exact member is absent in the inspected image listing. The wrapper uses a command name;
PATH resolution is also unobserved. Selected same-name dji_verify uses dynamic header+signature payload offset but a
fixed256-byte RSA call and digest/copy mode. Product-entry negatives stay bounded. C-456/C-457, STUE/root gaps and full
per-control readback/restore/persistence/RF requirements remain unchanged; no vendor execution or new device instruction. In continuing this work, use a new concrete input or call edge rather than repeating this closed static inspection.

## 2026-10-18 RedFly new-input checkpoint (C-476--C-479)

The supplied installer A-104 and embedded modified Fly A-105 are a new concrete input. See the
[focused review](24_REDFLY_BUILD245_STATIC_REVIEW.md) and [independent locations](../evidence/redfly-build245-static.json).
The32 regular DEX files make selected modified Java available; do not silently substitute it for official A-006.
RID guards, legacy mask/EID work, default-on behavior and missing original-state restore are now located.
Installer root/property success, aircraft acceptance and standard RID RF remain unobserved. Host location settings,
aircraft GPS parameters and flight-record UI-map export are separate; the latter does not close firmware decryption.

Use these exact classes for targeted comparisons with unresolved original methods. Do not repeat the completed
inventory or reopen closed legacy senders from names alone. No app installation or modified-app deployment was requested
or performed. Vendor inputs/derived source stay outside the repository; GitHub synchronization remains paused.

## RedFly development-path follow-up (C-480--C-482)

The user wants to borrow the implementation or develop on top of it and supplied redfly.app; no source project is
available yet. The [assessment](25_REDFLY_DEVELOPMENT_PATH.md) recommends independently maintained module source and
a small same-process host adapter. This is a proposed next build,not a completed module or admitted controller.
Parameter metadata and E2 readback paths are now located;do not repeat the whole-app inventory. Keep hardcoded
attribute1,limited completeness,non-atomic identity/state checks and missing durable baseline/rollback explicit.
Re-signing needs its own package/install/update strategy because the existing wizard fixes signer and payload hashes.
Use pinned A-105;the site's standalone hash is different and that file was not acquired. GitHub remains paused.
