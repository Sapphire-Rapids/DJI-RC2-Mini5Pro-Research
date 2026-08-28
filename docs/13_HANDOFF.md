# Handoff for researchers and coding agents

## Start here

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

The current corrections are v0.10, rejected V2.2, and sealed-but-unadmitted V2.3. Do not copy an
older “install v0.8” or “V2.3 in progress” instruction into a current procedure.

## Topic entry points

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

### Current candidate: A-025 modern FlySafe inventory

A-025 `0.5.0-flysafe-readonly` / code 8 is the current offline candidate (C-150/C-151). Its exact
`111,889`-byte APK SHA-256 is
`b137540f041cceb50a215bb95144c9f7ccf57fa4db4d2e7fc2108cb6ae68db80`. A local delivery copy
exists, but it has not been copied to RC 2 removable storage, installed, or run.

The new FlySafe lane is fixed to system `protocol` Binder transaction 4, route
`02:04 -> 12:04`, `11/11`, 6,000 ms, group selector `00 01`, and page selector
`00 (index<<1)`. Count is capped at 127, page calls at 128, and total duration at 90 seconds. It
accepts only ccode 0 records and a data-less ccode 1 terminator, then strictly parses an independently
implemented MSDK-compatible candidate schema. Recognition of
field 7 is a compatibility exploration, not proof that current DJI Fly understands it. The UI reports
only count, RID level, and status bits. License IDs are session-salted only for duplicate
detection; identifiers, signed data, and raw replies are not displayed or retained.

The FlySafe allow-list contains no `11/12` tuple and its test rejects that command. The old
`11/1C` button is removed. The suffix `flysafe-readonly` applies only to the new lane: separately
gated F7/F9, France EID, and OPID experimental controls remain in the APK, so reviewers must not
describe the entire artifact as globally write-free.

The next bounded action is one motors-off A-025 inventory run with the aircraft linked. Treat Binder
failure as query unavailable, not empty inventory. Only a canonical result containing a genuine
type-6 record may advance to a separately reviewed same-ID baseline/readback/restore design; RF truth
still requires operator-initiated motors and the independent detector.

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

Current Fly correction: its exact typed `LicenseData` parser handles fields 1--5 and sends field 7
to `UnknownFieldSet`; only the separate MSDK artifact typed-decodes field 7 as `LicenseDataRID`
(C-152). Its `11/12` setter is generic ID-plus-action, and no current app xref connects type 6,
field 7, or enabled state to WA150 `0802`, motor/armed state, or BLE/Wi-Fi enable (C-153). Receiver
`0x92` is not firmware-module identity.

A-025 now implements the bounded, read-only modern V3/V4 query offline as described in the current
candidate section above. It has not been copied to RC 2 removable storage, installed, or run. A
transport failure is “query unavailable,” not “empty inventory.”

Missing: live support/version, canonical Binder response, genuine account item, aircraft-side
consumer, same-item baseline/restore, and RF. If separate approved instrumentation obtains raw
unknown field-7 bytes, keep them only in excluded private evidence; never create or publish license
material.

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

## Documentation-only tasks available without device access

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
applicable, and changelog in the same commit.

## Publication checks

Run:

```sh
git diff --check
ruby scripts/check_markdown_links.rb
ruby scripts/check_evidence_csv.rb
sh scripts/check_sensitive_patterns.sh
```

Then inspect the staged file list. Only Markdown, CSV, scripts, license, and repository metadata are
expected. APK, SO, firmware, images, captures, key files, build directories, or host-local paths are
release blockers.
