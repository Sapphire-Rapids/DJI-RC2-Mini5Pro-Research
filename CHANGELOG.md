# Changelog

## 0.3.3 - 2026-08-29

### Added

- Added C-142/C-143 from the installed A-023 read-only Binder probe: service and callback ABI were
  reached, but target F7 ended in `ECode 1` after about 3.1 seconds; adjacent RC331 maps that class
  to retry exhaustion. No F8/F9 or RF effect occurred.
- Registered replacement artifact A-024 `0.4.1-research`, including serialized operation gates,
  per-route maximum-height F7/F8 positive control, validated Boolean metadata/readback/rollback,
  and one full-window passive `0x11/0x1C` state timeline.
- Added C-144 for the A-024 final-artifact audit: 25 unit tests, lint with zero errors, two
  byte-identical clean builds, no permissions/native libraries, v2 signature, and alignment checks.
- Added C-145 from the installed A-024 live result: legacy `0A:05 -> 03:00` and modern
  `02:04 -> 12:04` Binder routes both failed the known-height F7 positive control with `ECode 1` and
  no data after about 3.1 seconds. Target F7/F8/F9 were correctly not sent.
- Added C-146 from the motor-on experiment: the accepted 30-second Binder `0x11/0x1C` listener
  delivered zero callbacks while an independent detector confirmed real RID RF, closing that
  listener as a false-negative truth/readback path.
- Added C-147--C-149 for the official minimum status parser, the type-6 region-matched
  `NO_BROADCAST` design semantics, and the exact current product-139 inventory/set-enable wire.
- Changed the active implementation path to a bounded read-only modern `0x11/0x11` inventory query;
  `0x11/0x12` remains absent and prohibited until a genuine type-6 baseline exists.
- Updated the blocker, handoff, experiment matrix, artifact state, hypothesis, timeline, README, and
  AGENTS contract to close generic parameter attach variants and promote passive status,
  diagnostics, type-6 inventory, and WA150 `0802/E3` ownership as the active dependency chain.

### Provenance

- The two user-supplied result photographs were used only to transcribe redacted protocol outcomes;
  PID, UID, device identity, and image files are not committed.
- A-023/A-024 APKs and all implementation source remain outside this documentation-only repository.
- No target F7, F8, F9, reset, account action, license action, firmware write, or RF claim is made.

## 0.3.2 - 2026-08-28

### Added

- Recovered the current same-family SKYROVER `1.2.0` independent Boolean `RIDCtrlEnable`, its
  GET/SET/Listen flags, connection-time capability probe, and separation from France `EIDSwitch`.
- Closed the native mapping `RIDCtrlEnable -> rid_ctrl_enable_0`, parameter hash `0x3CBD864F`,
  FLYC `03/F7-F9` family, and static modern `0x82 -> 0x92` route as C-136 and C-137.
- Added C-138/H-27/B-20 for the decisive Mini 5 Pro F7/F8 admission test and subsequent reversible
  F9/readback/restore plus motor-on independent RF A-B-A.
- Added C-139/C-140: a full same-family RID configuration inventory found no second closed global
  Boolean, and a fixed public search found no independent Mini 5 Pro implementation. Modern
  FreeFCC transport/framing is retained only as corroboration for a different hash/feature.
- Registered the exact official input as A-022 and the clean-room fixed RC 2 Binder client
  `0.3.0-research` as A-023. The client APK was copied to RC 2 removable storage; install/run/live
  reply remain pending.
- Added C-141 from a live read-only probe: both validated direct routes returned F7 status `0x03`
  for `0x3CBD864F` while same-session known-parameter controls succeeded. Direct USB modern routing
  failed its own height control, so only the RC 2 Binder modern route remains open; no F9 was sent.
- Updated the control matrix, handoff, source index, timeline, README, AGENTS contract, claim CSV,
  and artifact CSV so another researcher can continue at the single live F7/F8 step.

### Provenance

- SKYROVER proprietary APK, shared libraries, DEX, and decompilation output remain excluded.
- The MIT implementation is independently written from protocol facts; no vendor or AGPL source was
  copied.
- No live F7/F8/F9 reply or RF effect is claimed by this documentation update.

## 0.3.1 - 2026-08-28

### Added

- Recovered Drone-Hacks' complete 28-entry ADSB numerical Debug dictionary, including
  `RID_INFO=0x11/0x1A` and `EID_INFO=0x11/0x35`, as claims C-110 and C-111.
- Cross-checked the dictionary against exact DJI Fly `1.21.10` and recorded the mixed agreement and
  semantic collisions that prevent using it as a current Mini 5 Pro request schema.
- Updated README, AGENTS, handoff, blocker, timeline, and negative-result guidance so future work
  uses these IDs only for passive traffic classification or exact static xrefs until a current
  handler and payload are recovered.
- Closed the current product-139 RID state owner through `RidImportModule`, including the exact
  seven-byte status mapping and the absence of a status GET/SET/action surface (C-115/C-116).
- Closed `KeyCloudControlData` as value-routed SET-only `0x00/0xDD`; ACK/cache is the request rather
  than applied RID state, and no active read-only RID query was recovered (C-117/C-118).
- Added independent public identity evidence for both WA150 `0802` versions, the bounded
  network-service ownership inference, and the still-negative public plaintext/key/recovery search
  (C-112--C-114).
- Added a focused legacy DroneID report: FlyC `0x03/0xDA` subcommands `0x05`/`0x06` are the
  high-confidence match for the NDSS multi-field mask, whose reported RF effect retained packets
  and changed selected values to `fake`; no WA150/modern Broadcast RID transfer is established
  (C-119--C-122).
- Expanded the target into a RID experiment-control matrix with explicit live-read, passive-owner,
  static-locked, managed, opaque, legacy, and synthetic-source implementation levels.
- Closed exact current identity/data surfaces for EASA OPID, Japan DIPS, China UOM identifier,
  app-location upload, and compliance serial; excluded the LTE phone path from RID (C-123--C-128).
- Recorded a separate synthetic OpenDroneID source as a controlled-lab hypothesis, not as a current
  Mac or DJI-device capability (C-129).
- Closed the current China UOM identifier receiver/timeout/retry and reply parser, corrected its
  GET-tail bytes from assumed zeroes to undefined vendor initialization, and separated conditional
  `UOMV1` real-name status/sync from broadcast control (C-130--C-132).

### Safety and provenance

- The Drone-Hacks executables were not run, no guessed DUML request was sent, and no device state
  changed. Vendor binaries and disassembly output remain excluded.
- No active RID query or cloud-control write was sent. Public image coordinates and unrelated
  metadata were excluded; only product/software version and whole-file hashes were retained.
- No legacy `Detection` command was sent and no executable sender was added to the repository.
- No OPID, DIPS, UOM, location, telephone, compliance identity, cloud policy, or license data was
  read or written. Secret credentials and real identity fixtures remain excluded.
- No China UOM GET or Sync action was sent; the new result is exact static analysis only.

## 0.3.0 - 2026-08-28

### Added

- Added a bounded static analysis of the official Drone-Hacks `2.0.29` Windows distribution,
  including exact provenance, Authenticode identity, Rust/Tauri command surface, server-driven job
  architecture, parameter editor, one-time FCC path, and firmware-resident CFC precedent.
- Recorded the current public Mini 5 Pro boundary: `wa150` is recognized, but no software platform,
  compatible license, product, CFC image, or explicit RID control was found; separate FCC ModBox
  compatibility is not software/RID support.
- Added Drone-Hacks artifacts A-019 through A-021, claims C-093 through C-101, a fixed-scope RID
  negative result, one architecture hypothesis, one blocker, source links, and handoff guidance.
- Closed NLD's native FCC envelope, entitlement verification, offline-cache framing, decrypted
  command schema, and DUML write loop as claims C-102 through C-105 while retaining the absent-real-
  payload and absent-RF-evidence boundary.
- Closed DJI Fly's current China OID report-enable Boolean as an app-side network-submission gate,
  not an aircraft RF switch; added the distinct cloud-namespace boundary and current exact global-
  setter negative as C-106 through C-109.

### Safety and provenance

- The user-supplied MSI matched the MSI in the official release ZIP and its signature validated.
- The MSI and embedded PEs were never installed or executed. No account, authenticated endpoint,
  license, private job payload, device identifier, or device read/write operation was used.
- Vendor binaries, extracted strings, decompiled material, credentials, and device data remain
  excluded from this repository.
- The fixed NLD symmetric master and all license/cache material remain excluded; only algorithm and
  framing facts are recorded.

## 0.2.0 - 2026-08-28

### Added

- Added a bounded static analysis of NLD FCC Smart RC `2.0.0.6`, including exact input identities,
  normal FCC native/server flow, C0 server-routed WireGuard orchestration, device-keyed offline
  licensing, parameter-editor design, and Package Installer boundary.
- Recorded that seven packaged JSON profiles are byte-identical to pinned FreeFCC but have no found
  NLD runtime reference.
- Added a fixed-scope negative result for an explicit NLD Remote ID control and preserved opaque
  native/server and hosted-DJI-Fly side effects as unknown.
- Added NLD artifacts A-016 through A-018, claims C-080 through C-092, two hypotheses, three
  negative results, one blocker, source links, and handoff guidance.

### Safety and provenance

- No NLD APK was installed or executed, no NLD API was contacted, and no device state changed.
- Vendor binaries, decompiled code, native libraries, license material, and private traffic remain
  excluded. Files matching AGPL-3.0 FreeFCC profiles were not copied into this MIT repository.

## 0.1.0 - 2026-08-28

### Added

- Created an independent RC 2 / Mini 5 Pro research archive with an evidence vocabulary, claim
  ledger, experiment timeline, topic reports, negative-result register, artifact identities,
  blockers, source index, and coding-agent handoff.
- Added automated Markdown-link, evidence-index, privacy-boundary, and whitespace validation.
- Recorded v0.10 as the current offline admission-probe candidate.
- Recorded V2.2 as rejected and V2.3 as the corrected but still unadmitted, zero-send route-only
  artifact without a new independent post-fix audit conclusion.

### Privacy

- Excluded vendor binaries, decompiled vendor code, private captures, serials, accounts, tokens,
  keys, licenses, real identifiers, coordinates, telephone numbers, and host-specific paths.
