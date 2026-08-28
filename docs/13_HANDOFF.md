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

### RID working status

Read:

- [04_STATE_ACCOUNT_LIMITS.md](04_STATE_ACCOUNT_LIMITS.md)
- [05_RID_CONTROL_SURFACES.md](05_RID_CONTROL_SURFACES.md)

Static anchors:

- `RidWorkingStatusPush`, command `0x11/0x1C`;
- seven-byte raw layout: little-endian flag word, four-byte area, one failure byte;
- preserve raw failure reason before a higher model drops it.

Missing evidence: synchronized motor-off/motor-on onboard state plus independent receiver data.

Do not treat `UAVOIDManager.native_SetOIDReportEnable(false)` as the missing RF switch. In the exact
`1.21.10` native path it selects app-side China OID network submission versus `DirectSuccess`; no
aircraft broadcast write or gate getter exists. `CN_OPERATE_ID_EFFECT` and
`dji_fly_rid_cloud_control_v2` are distinct namespaces. Read RID-011A/011B in
[05_RID_CONTROL_SURFACES.md](05_RID_CONTROL_SURFACES.md) before reusing any “report enable” name.

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
- type 6 `RID_UNLOCK`, levels 1 EU and 2 China.

Missing: live support/version, exact route, genuine account item, same-item baseline/restore, and RF.
Never create or publish license material.

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
The useful next handoff question is whether WA150's authoritative RID owner can be closed in verified
plaintext or an exact live read-only path—not how to invoke the generic custom-packet engine.

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
