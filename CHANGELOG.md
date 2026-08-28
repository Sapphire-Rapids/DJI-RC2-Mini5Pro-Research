# Changelog

## 0.4.0 - 2026-08-29

### Added

- Registered C-180--C-182 and A-033: exact DJI Fly official license-manager surface, the
  independently written `0.8.0-flysafe-diagnostic-export` source/artifact audit, and removable-SD
  MTP staging/readback.
- Added a file-manager-readable privacy-reduced report at
  `Download/FindUAS/FindUAS_RID_A033_latest.txt` using zero-permission MediaStore. The fixed direct
  button remains `0x11/0x11` only and never emits `0x11/0x12`.
- Added the one-time assisted sequence for manually inspecting DJI Fly's same-process aircraft
  license list before one A-033 run. The first pass contains no toggle, motor action, or RF test.

### Verification

- A-033 is `204,449` bytes with SHA-256
  `8ce8e0c13ecfcf69517a64e809a475b79bbc750124225744b6b35f281d3d7177`; 132 tests passed, lint
  reported zero errors and 15 warnings, two clean builds were byte-identical, and signature,
  alignment, zero-permission, native/network/socket/shell/external-process checks passed.
- MTP fresh readback matched the registered artifact. The APK is not committed and has not been
  installed or run; source and tests are published under `apps/rc2-rid-admin`.

## 0.3.9 - 2026-08-29

### Added

- Published the independently written RC 2 / Mini 5 Pro research source archive under `apps/`,
  `libraries/`, `host-tools/`, and `experiments/`, with project-local status, build, test, and
  evidence-boundary documentation.
- Added the current FindUAS RC 2 RID administration source, the hidden-settings launcher, and the
  v0.10 admission probe safe source set. Exact historical APKs remain identity records rather than
  redistributed binaries, and later source is not represented as a byte-for-byte reconstruction of
  every historical APK.
- Added host-testable RID codecs, inventory parsing, quiescence and bounded-control models; USB/ADB,
  firmware-acquisition, IMaH and ELF analysis helpers; Ghidra scripts; source-only system-UID bridge
  probes; and the preserved JVMTI experiment sequence.
- Preserved experimental outcomes in source: V2.2 is `RETRACTED`, V2.3 remains `NOT ADMITTED`, the
  ADB userspace-copy patch has not been executed, and build/test success is never promoted into a
  live Remote ID control result.
- Extended CI with 121 stable, device-free host tests for the protocol probes, quiescence model and
  firmware metadata/target-lock helpers, plus compilation of all published Python source.

### Publication boundary

- No DJI APK, firmware, partition, shared library, decompiled vendor source, patched vendor binary,
  raw private capture, device/account identifier, signing/ADB key, or generated APK/JAR/SO/DEX is
  published. A small third-party MIT transport helper and AOSP JVMTI header retain their original
  notices; GPL tooling is referenced externally rather than vendored.

## 0.3.8 - 2026-08-29

### Added

- Registered C-174--C-179 and A-029--A-032 for the exact `07.00.0100` ADB chain: verified signed
  system/`0205` provenance, exact APEX `adbd`, exact packaged `dpad_fuli`, the narrow userspace-copy
  gate patch, MTP staging/readback, and the still-unexecuted live session.
- Recorded the exact APEX path distinction: runtime `/apex/com.android.adbd/bin/adbd`, extracted
  backing `/system/apex/com.android.adbd/bin/adbd`, and no target `/system/bin/adbd` entry.
- Promoted the production/debug-count pre-AUTH return from adjacent-only inference to exact
  target-package `STATIC`; retracted C-032/H-14 only as the obsolete adjacent-parity inference while
  retaining live mounted-hash/property/branch-log unknowns.
- Registered A-032 at `1,497,232` bytes and SHA-256
  `3fceaa1724a77a153c17f725a2e3f3001b0543e31e0830aca0c77d785df9225f`. The patch changes only
  `cset w21, lt` to `mov w21, wzr` at the exact gate-value instruction and preserves the normal
  TLS/auth target.
- Recorded removable-SD `Download/RC2_ADBD_CNXN.bin` staging: a fresh MTP listing matched size and a
  full readback SHA matched. No internal copy, chmod, execution, daemon stop, new ADB response, or
  shell occurred.
- Added the operator handoff: first collect live UID/SELinux/gate/USB/init and exact stock/staged/Fuli
  hashes. Choose an internal executable path only from that output, then generate the second one-shot
  command segment in the same assisted session.

### Provenance

- At the time of this release, the outer aggregate came from a third-party archive, not DJI; the
  evidence anchor is the separately
  verified signed config/`0205` PRAK/checksum chain. No firmware, image, APK, original/patched vendor
  binary, raw disassembly, MTP identifier, device serial, ADB key, or host path is committed.

## 0.3.7 - 2026-08-29

### Added

- Registered A-027 and C-166--C-169 for the active read-only FlySafe inventory candidate:
  `0.7.0-flysafe-direct-readonly` / code 10, fixed `02:04 -> 12:04`, `11/11`, V3/V4 selectors,
  no route scan, and no application-level retry.
- Recorded exact final identity and audit: 196,569 bytes, SHA-256
  `aa4bcd9c8aa96870cfbae1ba326d366cb8854a50ef4aff223f7bce4290ddcd81`; 127 tests with
  zero failures/errors/skips, lint 0 errors/15 warnings, two byte-identical clean builds, v2
  signature, zipalign, zero permissions, and no native/network/socket/shell/external-process path.
- Recorded MTP staging as `Download/FindUAS_A027_RO.apk`; a fresh listing matched the registered size
  and readback SHA-256 matched.
- Recorded the first installed A-027 run: the active button returned
  `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS` at `ProtocolException`, and displayed
  `11/12 request count=0`. The UI did not expose the exception message or lower-level failure stage.
- Added the public-evidence boundary: pinned `fpv_live`, `dji-firmware-tools`, DJI Cloud API, and MSDK
  support generic transport/FlySafe context but do not independently confirm the product-139/RC331
  fixed route; A-027/A-028's noncanonical live results did not confirm it.
- Registered A-028 and C-170--C-173: `0.7.1-flysafe-direct-diagnostic` / code 11 changes only safe UI
  diagnosis while preserving command, route, selectors, and write boundary. Exact identity is
  197,061 bytes, SHA-256
  `d7c32636e19d1bce1b8b8994206355f42d0278b2f15048b14a948a8bbda1d540`; 127 tests,
  lint 0 errors/15 warnings, two byte-identical clean builds, v2 signature, zipalign, zero
  permissions, and no packaged native library passed.
- Recorded A-028 MTP staging as `Download/FindUAS_A028_DIAG.apk`; fresh listing size and readback SHA
  matched.
- Recorded the installed A-028 run: `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`,
  `ProtocolException`, detail `group transport callback failed`, `11/12 count=0`. The fixed group
  selector therefore did not reach a successful transport callback; protobuf/pages/terminator were
  not reached. The next discriminator is Reply failure/ecode/callback detail, not another identical
  black-box run.

### Provenance

- At the time of this release, no APK, implementation source, result image, device identifier, raw
  reply, license ID, or account material was committed. Source was published later in 0.3.9; sealed
  APK bytes and private/live material remain excluded. Failure remains ambiguous rather than
  unsupported/no-license, and canonical inventory would not establish RF RID.

## 0.3.6 - 2026-08-29

### Added

- Added C-165 from the first live A-026 gate run. The instructed 60,003 ms window ended
  `GATE_UNOBSERVED`: `03/09` and `03/42` were both unseen/unusable, every reported callback-class
  count was zero, and fail-closed admission kept `11/11` request count at zero.
- Updated A-026 device-use state to `installed-and-run-gate-unobserved-zero-query` and propagated the
  result through the evidence/artifact registers, timeline, RID surfaces, negative results,
  hypotheses, blockers, handoff, control matrix, README, and agent handoff rules.

### Provenance

- This is a narrow third-party Binder passive-listener negative. It is not evidence that the
  aircraft lacks RID support, a type-6 entitlement is absent, inventory is empty, RID/RF was off,
  or the official in-process observer cannot receive the pushes. No raw frame, identifier, license
  material, write, motor action, or independent RF observation is recorded.

## 0.3.5 - 2026-08-29

### Added

- Registered A-026 `0.6.0-flysafe-gated` and C-160/C-161: tx2 passive `03/09 + 03/42` gate,
  complete-route consistency, fail-closed same-process permit, fixed tx4 V3/V4 `11/11`, strict
  group/page 0..127 traversal, and an initial-plus-two-retry callback window.
- Recorded exact A-026 identity: code 9, 135,525 bytes, SHA-256
  `3c2ae42ac9f19a9e3dfe669ed6357bb8d2f1c38568af6a0f8d8b8f677fcbfec4`; two clean
  test/lint/assemble runs were byte-identical, 63/63 tests passed, lint was 0 errors/13 warnings,
  v2 signature/zipalign passed, and the APK has zero permissions and no native/network/socket/shell
  path.
- Added C-162 for MTP delivery as `FindUAS_A026_GATE.apk`: same-session readback SHA matched and a
  new session confirmed one unique short name with the registered size.
- Added C-163: the operator explicitly reported A-025 installation complete. This does not establish
  launch, execution, Binder requests, inventory, state change, or RF result.
- Added C-164: the operator explicitly reported A-026 installation complete. This establishes only
  installation; launch, execution, passive callbacks, permit, Binder requests/results, inventory,
  state change, and RF remain unknown.
- Updated C-159 from an unimplemented direction to the inference rationale now realized offline by
  A-026; runtime passive-push visibility remains unknown.
- Preserved the Admin boundary: external DJI Developer Assistant is outside A-026's internal
  allow-list, and gated F9/EID/OPID write controls remain, so the APK is not globally read-only.

### Provenance

- No object/storage/USB/device serial, local absolute path, account material, raw payload, or license
  material is recorded. A-026 implementation/audit is `STATIC`; delivery and user-reported
  installation are `OBSERVED`; execution and all live behavior remain `UNKNOWN`.

## 0.3.4 - 2026-08-29

### Added

- Added C-154 and updated A-025 disposition: the exact APK was written through RC 2 MTP to
  removable-SD `Download` as `FindUAS_A025_RID.apk`; same-session readback SHA-256 matched, and an
  unintended long-name duplicate was removed. Installation and execution remain unconfirmed.
- Added C-155/C-156 for the current official type-6 chain: FlySafe website background qualification,
  exact `Rid` product capability, product/FC-SN account record, reviewed application, nonempty-login
  signed group download, version/target-specific onboard blob selection, FC import, inventory, and
  existing-ID enable/disable.
- Recorded the visible-surface boundary: DJI Fly has ordinary Remote-ID registration/status and
  generic Unlock-a-Zone license lists, but no type-6-specific application page was recovered. Mini 5
  Pro capability/approval remains unknown, country/locale changes do not grant entitlement, and
  public MSDK support omits the product.
- Added C-157 for exact passive FlySafe admission: `03/09` Area Info populates unlock version and
  `03/42` WhiteList Info populates support; default `255/false`, missed pushes, and absent replay are
  unknown rather than unsupported.
- Added C-158 for A-025's false-negative boundary. Its fixed V3/V4 query lacks a current-connection
  passive gate, so failure or noncanonical completion cannot establish unsupported/no-license/empty
  inventory; only a canonical count-consistent completion describes returned inventory.
- Added C-159/H-28 for the A-026 direction: bounded passive observation first, one existing V3/V4
  query only after usable support=true and version 1/2, and fail-closed result classes otherwise.
  No final A-026 APK, version/hash, audit, installation, or live result exists.
- Updated the evidence/artifact registers, timeline, control surfaces, hypotheses, blockers,
  handoff, source index, README, and AGENTS correction. At this release the repository was
  documentation-only; source was added later in 0.3.9. Binaries and account/license material remain
  excluded.

### Provenance

- No local absolute path, storage/USB/device serial, account token/Cookie/HAR/SN, signed license,
  authenticated request, FC import, setter, or RF result is recorded.
- Public web and current-app evidence is static; A-025 staging is observed; A-025 execution,
  Mini 5 Pro entitlement, passive-gate visibility, and all A-026 behavior remain unobserved.

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
- Registered A-025 `0.5.0-flysafe-readonly` and C-150/C-151: the fixed, bounded, privacy-reduced
  system-Binder `11/11` inventory lane and its exact final-artifact audit. The FlySafe lane admits no
  `11/12`, and the false-negative `11/1C` UI button is removed.
- Recorded the exact A-025 boundary: 42 passing tests, lint with zero errors, byte-identical clean
  rebuild, zero permissions, no packaged native library or inspected network/socket/shell path, and
  no copy to RC 2 removable storage, install, or execution. The version suffix is lane-specific;
  separately gated older F7/F9, EID, and OPID controls remain.
- Added C-152 to separate the exact current DJI Fly 1.21.10 fields-1--5 `LicenseData` parser from the
  independent MSDK 5.18 field-7 `LicenseDataRID` schema used by A-025's compatibility decoder.
- Added C-153 for the bounded aircraft-consumer negative: current Fly `11/12` carries only license ID
  and action, with no recovered edge to WA150 `0802`, motor/armed state, or BLE/Wi-Fi enable. This
  does not cover encrypted aircraft firmware or establish a patch offset.
- Changed the active implementation path to a bounded read-only modern `0x11/0x11` inventory query;
  `0x11/0x12` remains absent and prohibited until a genuine type-6 baseline exists.
- Updated the blocker, handoff, experiment matrix, artifact state, hypothesis, timeline, README, and
  AGENTS contract to close generic parameter attach variants and promote passive status,
  diagnostics, type-6 inventory, and WA150 `0802/E3` ownership as the active dependency chain.

### Provenance

- The two user-supplied result photographs were used only to transcribe redacted protocol outcomes;
  PID, UID, device identity, and image files are not committed.
- At the time of this release, A-023/A-024/A-025 APKs and implementation source were outside the
  documentation-only repository. Later successor source was published in 0.3.9; the sealed APK
  bytes and exact historical snapshots remain excluded.
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
