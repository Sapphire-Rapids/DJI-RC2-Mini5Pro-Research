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
