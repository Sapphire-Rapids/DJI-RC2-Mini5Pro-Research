# Timeline

Times are Asia/Shanghai unless explicitly stated. File modification times were used only to order
work when a report did not contain a more precise timestamp.

[Latest progress: 2026-08-31](#2026-08-31) ·
[Current device step](23_RC2_LIVE_RUNTIME.md#下一步)

## 2026-08-27

### 02:33–05:12 — USB routes and fixed read-only state

- `OBSERVED`: aircraft and RC 2 enumerated as separate DJI USB devices.
- `OBSERVED`: bounded passive bulk summaries and fixed UID/application/parameter probes were run.
- `OBSERVED`: at 05:12:42.250–05:12:54.893, fixed SDR Assistant reads returned the same values at
  both endpoints: `0xFFFF0048=5`, `0xFFFF0063=0`, result 0.
- `NEGATIVE`: legacy RC PowerMode `0x06/0x21` returned no response on the two candidate routes.

### 05:12–13:33 — account, limit, RID, and RF model separation

- `OBSERVED`: both fixed paths returned privacy-minimized UUID/application Boolean results.
- `OBSERVED`: configured height=500 m, radius=5000 m, radius-limit-enabled=0 on both paths.
- `STATIC`: login state was separated into cached credential, server validation, and FC UID sync.
- `STATIC`: configured limit values were separated from an unresolved runtime/effective 30/50 m
  layer.
- `STATIC`: RID working-status, France EID, FlySafe exception, EU C0, and broadcast-effect surfaces
  were separated.

### 13:33–15:12 — bounded area/country state transactions

- `OBSERVED`: FC area completed `CN/156 -> US/840 -> CN/156`, with ACK and fresh GET after each
  write and a final read-only confirmation.
- `OBSERVED`: Sky country completed double-CN precheck, `US` write/readback, `CN` restore/readback.
- `NEGATIVE`: Ground country completed double-CN precheck and one US request, but no strictly
  matching ACK arrived; the following GET remained CN. No retry or restore SET followed.
- `OBSERVED`: later independent reads returned FC/Sky/Ground all CN.
- `UNKNOWN`: the receiver was offline, so no RID, channel, or RF effect was measured.

### 16:28–19:09 — Assistant and exact static inputs

- `STATIC`: Assistant metadata and named package inventory were collected.
- `STATIC`: RC331 `0205` verified/extracted without force; RC331 `0200` outer verification passed
  while inner FLYA remained protected.
- `STATIC`: WA150 `0802`, `2603`, and protected `0806/DONG` roles were compared.
- `STATIC`: official DJI Fly 1.21.10 became the current targeted app sample.

### 19:23–23:59 — RID and FlySafe schema recovery

- `STATIC`: working-status layout, hash-parameter family, license inventory, type-6 models,
  cloud-control writers, and runtime transport components were mapped.
- Work-only parsers and state models were built and tested offline. No parser result was described
  as a live license or live RID status.

## 2026-08-28

### 00:40–03:37 — exact control-surface separation

- `STATIC`: FlySafe query/set-enable V2/V3/V4 structures and support/version gates were recovered.
- `STATIC`: product-139 France EID was resolved to `0x03/0x77`, receiver `0x92`, GET `[02]`, SET
  `[00]/[01]`, and canonical ACK layouts.
- `STATIC`: EASA operator-registration `0x03/0x78` was separated from broadcast enable.
- `OBSERVED/NEGATIVE`: one fixed France-EID GET was sent on each of two artificial direct routes;
  neither returned a canonical ACK within the fixed window. No SET, retry, or route scan occurred.

### 05:17–05:32 — live-version gap and localhost retraction

- `NEGATIVE`: Assistant caches, logs, ordinary download locations, and retained material did not
  contain the exact complete `07.00.0100` signed package/ABI set.
- `STATIC`: adjacent RC331 `0205` broker configuration and code showed single-active-fd default
  behavior on `40007`/`40009`.
- `RETRACTED`: observer v0.1-v0.4 live procedures were withdrawn because `connect()` alone can
  replace DJI Fly's fd.

### 06:34–08:16 — no-root and semantic-anchor artifacts

- V0 attach canary and V1 semantic resolver were built and audited offline.
- Public precedent was rechecked.
- `NEGATIVE`: the complete exported-component review of adjacent `dpad_fuli` found no
  side-effect-free fixed-command UID1000 carrier preserving argv/stdout/stderr/exit status.

### 08:45–13:23 — same-owner tuple and lifecycle analysis

- `STATIC`: current native tuple, true dynsym/RVA, route worker, mutator, exception, callback,
  pending, Stopper, and mapping boundaries were analyzed.
- V2 raw carrier and V2.1 route-only artifact were sealed with send paths unreachable.
- `RETRACTED`: global same-worker epoch and fixed 100 ms callback quiet-time assumptions were
  withdrawn.

### 13:42–14:09 — mapping/quiescence audit and V2.2 rejection

- `STATIC`: exact adjacent ART mapping-retention behavior was bounded.
- Host-only quiescence model 0.1.1 passed 17 synthetic tests after independent corrections.
- `RETRACTED`: V2.2 was rejected by independent review: runtime headers were trusted too early,
  writable mappings could be accepted for original non-writable loads, and `st_dev==0` was not
  rejected.

### 14:22–14:36 — hidden Settings, V2.3, and v0.9 audit

- `STATIC/OBSERVED`: fixed Android Settings intents were mapped; a launcher artifact was copied to
  removable media with matching hash. Copy did not itself prove installation.
- `STATIC/OFFLINE`: V2.3 fixed the three V2.2 defects, retained immutable-zero exception gating and
  zero-send behavior, and was sealed. No separate new independent post-fix audit report exists.
- `RETRACTED`: v0.9 remained sealed after independent audit found attestation/provenance weaknesses.

### 15:03–15:15 — live ADB handshake

- `OBSERVED`: stock ADB backends, the pinned Dr-Muh profile, and five isolated pre-auth variants
  transmitted `CNXN` but received no ADB packet; bulk-IN timed out at about 15 seconds.
- No `AUTH` public key, `OPEN`, shell, install, or device command was sent.
- `STATIC`: adjacent unstripped `adbd` production CNXN drop branch explained the same boundary.

### 15:49–15:50 — v0.10 probe closure

- `STATIC/OFFLINE`: v0.10 fixed the v0.9 audit findings.
- Exact artifact passed 43 tests, lint, final manifest/DEX/signature/zipalign checks, 21/21
  adversarial mutations, two byte-identical clean builds, and independent review with no unresolved
  P0–P3.
- The APK was not copied, installed, or run on RC 2.

### 16:16 — public research synchronization

- Redacted ADB, v0.10, retry-layout, route, exception, mapping, and quiescence conclusions were
  synchronized to the FindUAS repository at commit `15f331c`.

### 17:10–17:41 — NLD FCC Smart RC 2.0.0.6 static comparison

- `STATIC`: the supplied Smart RC ZIP matched the current official download bytes; the embedded
  app identified itself as `2.0.0.6` even though the downloads page displayed `2.0.0.1`.
- `STATIC`: seven packaged profiles were byte-identical to pinned FreeFCC, but no application or
  native runtime reference to them was found.
- `STATIC`: normal FCC was traced through native online/native-offline payload decode and DUSS;
  the exact command sequence remained opaque.
- `STATIC`: C0 was traced through online VPN configuration, server-routed WireGuard, DJI Fly
  lifecycle, and a 25-second automatic-stop schedule after tunnel UP.
- `NEGATIVE`: a bounded full-package search found no identifiable Remote ID control surface.
- No APK was installed or executed, no NLD API was contacted, and no controller or aircraft state
  changed.

### 18:05–19:10 — Drone-Hacks 2.0.29 static comparison

- `STATIC`: the supplied MSI was byte-identical to the MSI in the official release ZIP; the MSI
  and both embedded PEs carried valid Skymod Technologies Authenticode signatures.
- `STATIC`: the Rust/Tauri client exposed a broad DUML/USB/ADB/firmware/parameter executor and
  server-driven job model; the direct `dhfc_config` schema contained only FCC, NFZ, and height.
- `CORROBORATED`: public data recognized `wa150` as Mini 5 Pro but exposed no software platform,
  compatible license, or software product; separate FCC ModBox compatibility did include `wa150`.
- `NEGATIVE`: no explicit Drone-Hacks RID feature, switch, local command, parameter, job, or Mini 5
  Pro RID implementation was found in the bounded client/public search.
- `STATIC`: public CFC documentation supplied a firmware-resident runtime-control precedent for
  listed older products, but neither Mini 5 Pro nor RID was documented.
- No installer or PE was executed, no account/authenticated API/private job was used, and no device
  read/write action occurred.

### 2026-08-28 follow-up — NLD native envelope and cache closure

- `STATIC`: the outer Base64/HMAC/AES-CBC envelope, online default-master selection, offline
  uppercase-serial derivation, and strict padding/MAC checks were closed.
- `STATIC`: RSA-3072/SHA-256 entitlement verification and version/serial/type/device-key binding
  were closed; cached subscription responses are reverified after the exact connection-failure
  sentinel.
- `STATIC`: offline cache framing and durable-write behavior plus decrypted JSON and DUML framing/
  write-loop semantics were closed.
- `UNKNOWN`: no real encrypted payload or command object exists in the package, so actual commands,
  restore behavior, readback, and RF effects remain unresolved.
- The embedded symmetric key value and all license/cache material were excluded. No vendor code or
  API was executed.

### 2026-08-28 follow-up — exact RID setter and China OID gate re-audit

- `STATIC`: current `UAVOIDManager` report/simulator/mock Booleans and their consumer branches were
  closed in DJI Fly `1.21.10` native code.
- `CORROBORATED`: report-enable controls China OID app-side network submission and can direct-success
  without upload; it is distinct from aircraft BLE/Wi-Fi transmission and from the opaque RID cloud
  V2 namespace.
- `NEGATIVE`: a current exact setter search found France EID wrappers but no product-139
  ODID/OpenDroneID/global RF setter handler. The encrypted WA150 firmware boundary remains.
- No vendor code, network call, or device action was executed.

### 2026-08-28 follow-up — Drone-Hacks ADSB dictionary recovery

- `STATIC`: the exact `DumlPacket` Debug control flow closed the ADSB command set as `0x11` and
  recovered all 28 numerical display-name mappings, including `RID_INFO=0x1A` and `EID_INFO=0x35`.
- `STATIC`: a current DJI Fly `1.21.10` cross-check found collisions at `0x0C` and `0x1C`, while
  `0x43` and `0x50` agreed. The table was therefore classified as legacy/general vocabulary, not a
  current WA150 packet schema.
- No executable was started, no guessed packet was sent, and no controller or aircraft state changed.

### 2026-08-28 follow-up — current product-139 RID owner closure

- `STATIC`: product-139's main abstraction was traced through `RidImportModule` registration to the
  listen/update-only `KeyRidWorkingStatusPush` and `0x11/0x1C` observer.
- `STATIC`: the seven-byte status bit/area/failure layout and US/Cloud/EU/Japan/France capability
  interpretations were closed; runtime link/device identity prevents a fixed request tuple inference.
- `STATIC/NEGATIVE`: the separate `KeyCloudControlData` path was closed as value-routed SET-only
  `0x00/0xDD`; success caches the request and has no applied-state echo. No status GET, stable
  disable/reset/debug handler, or correlation between the surfaces was found.
- No active query, write, vendor-code execution, or device-state change occurred.

### 2026-08-28 follow-up — WA150 public subsystem corroboration

- `CORROBORATED`: two independent public Mini 5 Pro originals reported software versions exactly
  matching the respective 0600 and 0700 WA150 `0802` modules; private/location metadata was excluded.
- `INFERENCE`: public BLE/network advisories covering firmware through 0600, combined with the
  two-module manifest delta and `2603`'s explicit GNSS role, make `0802` the likely 0700 network-
  service repair owner.
- `NEGATIVE`: a fixed public search found no verified plaintext, target key, replacement trust root,
  recovery image, RID handler, 0700 plaintext diff, or reproducible PoC.

### 2026-08-28 follow-up — legacy proprietary DroneID switch identification

- `STATIC/INFERENCE`: public DJI-derived midware and exact DJI Fly enum bytes identified
  `0x03/0xDA` subcommands `0x05`/`0x06` as the high-confidence correspondence for the NDSS
  multi-field DroneID control.
- `STATIC`: the eight legacy field names, logical APP-to-FLYC builder route, and get/set mask layouts
  were recorded with the paper-disclosure and live-polarity boundaries intact.
- `STATIC/NEGATIVE`: the paper's RF experiment retained packets and substituted selected fields with
  `fake`; no public evidence transfers the legacy OcuSync/AeroScope handler to WA150 or modern
  ASTM/FAA/EU Broadcast RID.
- No device command was sent and no executable sender was created.

### 2026-08-28 follow-up — RID configuration-surface expansion

- The target expanded from one global toggle to a truth-labelled RID experiment control matrix.
- `STATIC`: current product-139 schemas were closed for EASA OPID `0x03/0x78`, Japan DIPS
  `0x11/0x4B`, China UOM identifier `0x11/0xD6`, app-location upload `0x11/0x43`, and get/listen-only
  compliance serial identity.
- `NEGATIVE`: the LTE phone lane was identified as unrelated LTE HYBRID business data, not a
  standards-based Remote ID field; a proprietary detector's phone source remains unknown.
- Every surface was classified as live read-only, passive-owner, static-locked, managed,
  opaque-blocked, legacy-excluded, or separate synthetic-source candidate. No newly recovered
  schema was promoted to an admitted device editor.
- No identity, credential, coordinate, policy, cloud blob, or device state was read or written.

### 2026-08-28 follow-up — China UOM exact reply and admission closure

- `STATIC`: product-139 `OIDIdentifier` was closed to fixed receiver `0x92`, 500 ms timeout,
  retry 3, 18-byte SET/GET allocation, response result at byte 1, and an eight-byte GET value at
  bytes 2--9. The GET builder only visibly initializes `[01,02]`; previous assumed zero tail wording
  was corrected.
- `STATIC`: direct `UOMRealNameStatusGet` uses `0x11/0xD1`, receiver 2/0, request `[01,00]`, and a
  bounded status response. `UOMV1` is registered only after runtime function ID `0x6C` admission.
- `NEGATIVE`: the separate Sync action enters an external account/network real-name helper, has no
  setter or restore semantics, and is not a RID broadcast switch.
- No UOM request/action was sent, and no real identifier, account data, network response, or raw
  payload was read or retained.

### 2026-08-28 follow-up — independent `RIDCtrlEnable` recovery and fixed client

- `STATIC`: official SKYROVER `1.2.0` was frozen by exact hash. Its current FlyModel exposes a
  Boolean GET/SET/Listen `RIDCtrlEnable` independently from France `EIDSwitch`, and the UI performs
  a fresh capability GET after aircraft connection before showing the switch.
- `STATIC`: exact native mapping closes `RIDCtrlEnable -> rid_ctrl_enable_0`, hash `0x3CBD864F`,
  FLYC commands `03/F7`, `03/F8`, `03/F9`, and default modern route `0x82 -> 0x92`.
- `STATIC`: a clean-room RC 2 Binder client `0.3.0-research` was built with a fixed command set,
  F7 metadata/F8 Boolean parsing, baseline capture, F9 write, authoritative F8 readback, and restore.
  Eleven unit tests, lint, two byte-identical clean builds, final manifest/permission, signature,
  zipalign, and decompiled-artifact checks passed.
- `OBSERVED`: the exact `64,745`-byte APK with SHA-256
  `271ca3a415c7258919889a44983145671d6771be64803f6fe75289937bdc7c59` was copied to RC 2
  removable storage. Installation, launch, Binder result, F7/F8 reply, F9 action, and RF effect were
  not observed in this record.
- The proprietary SKYROVER APK, libraries, and decompilation output remain excluded. No SKYROVER
  code was copied into the MIT implementation or documentation repository.
- `STATIC`: a full current same-family RID inventory found no second RID-named FCConfig parameter.
  The remaining writable items were classified as regional EID/identity/registration commands or
  opaque set-only cloud policy; status, support, import-result, and compliance keys were read-only.
- `NEGATIVE`: fixed public repositories plus indexed exact-string searches found no independent
  Mini 5 Pro/RC 2 `RIDCtrlEnable` implementation. FreeFCC corroborated the modern route and F9 frame
  form only; its feature and hash were different.

### 22:59–23:04 — live `rid_ctrl_enable_0` direct F7 probe

- `OBSERVED`: fixed F7 hash `0x3CBD864F` returned a canonical one-byte `03` payload through both
  RC 2 routed `0xAA -> 0x03` and aircraft-direct `0x0A -> 0x03` paths.
- `OBSERVED`: in the same sessions, RC 2 height/distance/distance-enable and aircraft height
  controls returned valid F7 metadata and F8 values; current configured values were unchanged.
- `NEGATIVE`: direct-route metadata retrieval failed for the candidate. No target F8, F9, reset, or
  other mutation was sent.
- `NEGATIVE` only for route usability: raw USB `0x82 -> 0x92` timed out for both the candidate and a
  known height control. This leaves the RC 2 `protocol` Binder modern route unresolved.

### 2026-08-28 follow-up — installed A-023 Binder F7 result

- `OBSERVED`: exact A-023 `0.3.0-research` was installed and opened on RC 2. Its process label was
  resolved through the intended compatibility path; the live Binder was alive and reported
  descriptor `com.dji.protocol.IProtocolManager`.
- `OBSERVED`: manager transaction 1 and callback transaction 4 both returned through their Binder
  exception layers. The fixed target command was `03/F7` for hash `0x3CBD864F`.
- `OBSERVED`: after approximately 3.1 seconds the callback returned failure `ECode 1`; no F7 ACK
  payload, F8, F9, reset, or other mutation followed.
- `STATIC`: adjacent RC331 `ActQueue` emits `ECode 1` after the queued request exhausts retries.
- Boundary: A-023 did not run a same-Binder-route known-parameter positive control. The result proves
  Binder lookup and callback delivery, not healthy target routing, parameter absence, unsupported
  RID, or any RF state.

### 2026-08-28 to 2026-08-29 — A-024 positive-control and passive-timeline replacement

- `STATIC`: A-024 `0.4.1-research` tries the validated legacy Binder route before modern routing and
  requires a maximum-height F7/F8 positive control before it interprets the RID target reply.
- `STATIC`: candidate writes are serialized and remain locked until exact F7 metadata, read/write
  attribute, 0/1 range, and F8 Boolean baseline are all available. Write verification uses repeated
  F8 samples and restores the pre-operation value after ambiguity.
- `STATIC`: a local transaction-2 `0x11/0x1C` listener records the complete 30-second window as a
  bounded state-change timeline. The app synchronously saves the result and intentionally exits so
  Binder death removes the listener despite adjacent RC331's cross-process removal defect.
- `STATIC`: 25 unit tests, lint with zero errors, two byte-identical clean builds, package/version,
  no-permission, signature, zipalign, and no-native-library checks passed. Final artifact is 92,569
  bytes with SHA-256 `68f9b0d42d42e1bcb674ddba88a3996229d06978e35e30a355f253678a8e2b95`.
- `OBSERVED`: A-024 was copied to RC 2 removable storage as `RID-Admin.apk`; only superseded
  self-developed FindUAS APK copies were removed.
- `OBSERVED`: with the aircraft linked and motors off, legacy Binder route `0A:05 -> 03:00` and
  modern Binder route `02:04 -> 12:04` each sent the known maximum-height F7 positive control. Both
  returned callback `ECode 1`, no data, after approximately 3.1 seconds.
- `OBSERVED/STATIC`: the exact code stopped after both positive controls failed, so target hash
  `0x3CBD864F`, F8, and F9 were not sent and the write buttons remained locked. This closes the two
  exact third-party Binder parameter routes in that session, not the target parameter or an official
  in-process owner path.
- `OBSERVED`: the separate transaction-2 `0x11/0x1C` listener was accepted in 9 ms and ran the full
  30,000 ms, but callback, valid-frame, malformed-frame, and state counts were all zero. The operator
  started the motors during that window and an independent detector confirmed that the aircraft was
  broadcasting RID. This makes the tested third-party Binder listener a false-negative path; it does
  not negate the RF observation or close DJI Fly's own in-process observer.

### 2026-08-29 — FlySafe type-6 control-semantics closure

- `STATIC`: official MSDK 5.18 retained logic maps an enabled `RID_UNLOCK` whose level matches the
  current EU/China area strategy to `broadcastRemoteIdEnabled=false` and `NO_BROADCAST` when the
  product capability gate is true. US has no type-6 level and its delegate disables this gate.
- `STATIC`: that consumer branch only mutates the SDK status object; it contains no Key write,
  native call, or additional DUML request. Any physical RF suppression must therefore be consumed
  inside the aircraft after the FC's genuine signed-license enabled state changes.
- `STATIC`: current native inventory/set-enable endpoints are `0x11/0x11` and `0x11/0x12`; product
  139 resolves to receiver `0x92`. V3/V4 group and record protobuf layouts are now strict-parser
  inputs. No current genuine type-6 ID, enabled baseline, mutation, restore, or RF effect exists.
- Implementation direction changed to a bounded, privacy-reduced, read-only modern inventory query.
  The next APK version must not implement or send `0x11/0x12` until inventory proves a genuine item.

### 2026-08-29 — official type-6 application/account/sync chain closure

- `STATIC`: the current official FlySafe website, not a recovered type-6-specific DJI Fly page,
  exposes Mainland and Abroad RID applications. Background qualification, a product row whose
  `support_unlock_type` contains exact `Rid`, and an account device record matching product plus FC
  serial all precede `POST /api/qep/unlock`.
- `STATIC`: current DJI Fly 1.21.10 native code requires a nonempty official login token, obtains
  user context, downloads signed license groups, and selects server-supplied V2/V3/V4 onboard data
  by current FC support/version/target before import. FC inventory and generic existing-ID enable/
  disable remain separate states.
- `UNKNOWN`: the logged-in Mini 5 Pro product capability row, account background eligibility,
  approval, genuine type-6 record, FC import, and enabled baseline are not available. No login,
  authenticated request, license acquisition, import, or setter was performed.
- `STATIC`: changing Sky/Ground country, locale, app region, or SDK area strategy does not create
  this server entitlement. Public MSDK support omits Mini 5 Pro, so public API availability cannot be
  inferred from DJI Fly's internal components.

### 2026-08-29 — A-025 modern FlySafe inventory checkpoint

- `STATIC`: A-025 `0.5.0-flysafe-readonly` / code 8 added one system-Binder transaction-4
  `sendWithListen` query lane fixed to `02:04 -> 12:04`, `11/11`, and 6,000 ms. It sends group
  selector `00 01`, then bounded page selectors `00 (index<<1)`, accepts ccode 0 records and only a
  data-less ccode 1 terminator.
- `STATIC`: the independent parser caps declared count at 127, page calls at 128, and total duration
  at 90 seconds. It strictly checks protobuf shape and count/terminator agreement; duplicate IDs are
  detected only through session-salted fingerprints. Identity, description, signed material, and raw
  replies are not emitted, and temporary reply/fingerprint material is cleared.
- `STATIC`: the FlySafe request allow-list has no `11/12` tuple and its test rejects that command.
  The false-negative `11/1C` listener button was removed. The version suffix describes this FlySafe
  lane only; separately gated earlier F7/F9, France EID, and OPID controls remain in the APK.
- `STATIC`: clean unit tests, lint, and assemble completed; 42 tests passed, lint reported 0 errors
  and 9 warnings, and a second clean build was byte-identical. V2 signature and zip alignment checks
  passed. The exact `111,889`-byte APK has SHA-256
  `b137540f041cceb50a215bb95144c9f7ccf57fa4db4d2e7fc2108cb6ae68db80`, declares zero Android
  permissions, packages no native library, and has no inspected network/socket/shell path.
- `OBSERVED`: A-025 was written through RC 2 MTP to removable SD `Download` as
  `FindUAS_A025_RID.apk`; a same-session readback SHA-256 matched the registered artifact. An
  unintended long-name duplicate was deleted. This proves staging byte identity only; installation
  was not yet confirmed at that point. The operator later explicitly reported that A-025 installation
  completed (`OBSERVED`, C-163); launch, execution, Binder ACK, inventory, license, state, and RF
  result remain unknown. Storage/USB/device serials and the sealed APK remain excluded; the later
  evolving clean-room source is now published under `apps/rc2-rid-admin` without claiming it is
  the exact A-025 snapshot.

### 2026-08-29 — exact current-Fly field-7 and aircraft-consumer boundary

- `STATIC`: exact DJI Fly 1.21.10 `libflightrestrictcore.so` parsing was compared with the separate
  MSDK 5.18 FlySafe core. Current Fly typed `LicenseData` parsing handles fields 1--5 and sends field
  7 to `UnknownFieldSet`; MSDK alone typed-decodes field 7 as `LicenseDataRID`.
- `STATIC`: current Fly's generic V3 `11/12` setter carries license ID and enable/disable action but
  no license type, RID level, region, motor/armed, bearer, or module field.
- `NEGATIVE`: bounded app-side tracing found no edge from type 6/field 7/set-enable to WA150 `0802`,
  motor transition, or BLE/Wi-Fi enable. Encrypted aircraft plaintext was unavailable, so no
  firmware-absence conclusion or patch offset was recorded.

### 2026-08-29 — passive FlySafe gates and A-026 direction

- `STATIC`: current DJI Fly passively populates unlock version from current-token `03/09` Area Info
  and support from `03/42` WhiteList Info. Cache defaults are `255/false`; without usable pushes they
  are unknown, not evidence of unsupported state. The official query manager stops before sending
  when support is false or version is outside 0/1/2.
- `STATIC`: observer registration sends no business GET and replays no earlier frame; no safe active
  push trigger was recovered. A-025 does not first observe these gates and directly assumes V3/V4.
- `INFERENCE`: A-025 transport failure, zero callbacks, parser rejection, or any noncanonical
  completion can therefore be a session/gate false negative and cannot mean no type-6 entitlement or
  empty inventory. A canonical count-consistent result would still describe only returned inventory.
- `INFERENCE`: the A-026 direction was a bounded passive `03/09 + 03/42` phase admitting the existing
  one-shot V3/V4 query only after usable support=true and version 1/2. C-160/C-161 now record the
  offline implementation and artifact audit; that does not turn the design inference into live proof.
  Because third-party Binder lacks DJI's device token, a matching route/window remains only a proxy
  and missing pushes remain unknown.

### 2026-08-29 — A-026 gated FlySafe artifact and delivery checkpoint

- `STATIC`: A-026 `0.6.0-flysafe-gated` / code 9 registers one tx2 listener for `03/09` version and
  `03/42` support. It requires both callbacks' complete actual route to agree and signs no permit on
  malformed/failure/conflict/deadline/cancel. Only support=true plus version V3/V4 yields a
  same-process permit for the fixed `11/11` lane.
- `STATIC`: after admission, group is followed by strict page 0..127 traversal; selector/count/page/
  terminator bounds fail closed. The internal sender has no `11/12` path, and tx4 callback waiting
  covers the initial request plus two 6-second retries. Privacy-reduced results are followed by
  listener cleanup and process termination.
- `STATIC`: external DJI Developer Assistant is outside the internal sender allow-list. The APK also
  retains separately gated F9, France-EID, and OPID write controls, so it is an Admin artifact and not
  globally read-only.
- `STATIC`: two clean `testDebugUnitTest lintDebug assembleDebug` pipelines produced byte-identical
  APKs; 63/63 tests passed, lint reported 0 errors/13 warnings, v2 signature and zipalign passed,
  manifest has zero `uses-permission`, and no native/network/socket/shell path was found. Exact
  `135,525`-byte SHA-256 is
  `3c2ae42ac9f19a9e3dfe669ed6357bb8d2f1c38568af6a0f8d8b8f677fcbfec4`.
- `OBSERVED`: A-026 was written through MTP to removable SD `Download` as
  `FindUAS_A026_GATE.apk`; same-session readback SHA matched, and a new MTP session confirmed one
  unique short-name entry with the registered size. No object/storage/USB/device serial is retained.
- `OBSERVED`: the operator subsequently reported that A-026 installation completed (C-164).
- Boundary at that checkpoint: the user report established installation only; no package-manager
  telemetry or private device identifier was retained.

### 2026-08-29 — first A-026 live gate run

- `NEGATIVE`: after installation, the operator ran exact A-026 following the instructed bounded gate
  flow. The listener window completed at 60,003 ms with `GATE_UNOBSERVED` (C-165).
- `OBSERVED` values within that negative: `03/09` Area Info was `seen=0`, `usable=0`,
  `version=UNOBSERVED`; `03/42` WhiteList Info was `seen=0`, `usable=0`,
  `supported=UNOBSERVED`. Valid, ignored, malformed, and failure-callback counts were each zero.
- Fail-closed behavior held: no permit was issued and `11/11 request count=0`. No inventory query,
  write, motor action, independent RF observation, raw frame, identifier, or license material formed
  part of the run.
- Boundary: this run establishes only that the third-party system-Binder passive listener did not
  form an observation surface in that window. It does not establish aircraft non-support, absent
  type-6 entitlement, empty inventory, RID off/no RF, or absence of the official in-process observer.

### 2026-08-29 — A-027 active read-only inventory checkpoint

- `STATIC`: A-027 `0.7.0-flysafe-direct-readonly` / code 10 removes the failed passive gate from the
  next experiment and admits one one-shot active read-only system-Binder transaction-4 query. The
  route is fixed to `02:04 -> 12:04`, command `11/11`, V3/V4 group/page selectors; it performs no
  route scan and no application-level retry.
- `STATIC`: only a canonical count/page/terminator/schema completion may be reported as inventory.
  Timeout, callback failure, and noncanonical completion remain ambiguous and cannot mean
  unsupported or no license. A canonical inventory would still not prove aircraft-side consumption
  or RF RID.
- `STATIC`: the fixed product-139/RC331 route comes from local exact static analysis. Pinned
  `fpv_live`, `dji-firmware-tools`, DJI Cloud API, and MSDK sources corroborate generic DUML/FlySafe
  families but do not independently confirm that exact route.
- `STATIC`: both clean builds produced byte-identical APKs; 127 tests passed with zero failures,
  errors, or skips; lint reported 0 errors/15 warnings; v2 signature, zipalign, zero permissions, and
  no native/network/socket/shell/external-process path passed. Exact size is `196,569` bytes and
  SHA-256 is `aa4bcd9c8aa96870cfbae1ba326d366cb8854a50ef4aff223f7bce4290ddcd81`.
- `OBSERVED`: MTP staging to removable-SD `Download/FindUAS_A027_RO.apk` completed. A fresh listing
  matched the registered size and readback SHA-256 matched the registered artifact (C-168).
- `NEGATIVE`: after installation the operator ran the active button. It entered the strict inventory
  parser and reported
  `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`, stage `ProtocolException`, and
  `11/12 request count=0` (C-169). No canonical inventory formed and no set-enable request was sent.
- Boundary: the UI did not expose the exception message or a lower-level callback, ccode, group,
  page, or terminator class. The result is not evidence of unsupported state, empty inventory, no
  `RID_UNLOCK`, RID off, or RF. The image is not committed; no identifier, raw reply, license
  material, motor action, or independent RF observation is recorded.

### 2026-08-29 — A-028 read-only diagnostic checkpoint

- `STATIC`: A-028 `0.7.1-flysafe-direct-diagnostic` / code 11 changes only A-027's safe UI output:
  static `ProtocolException` text, numeric unexpected group/page ccode with page index, and
  terminator data length. Protocol command, fixed route, selectors, and write boundary are unchanged.
- `STATIC`: 127 tests passed; lint reported 0 errors/15 warnings; two clean builds were byte-identical;
  v2 signature, zipalign, zero permissions, and no packaged native library passed. Exact size is
  `197,061` bytes and SHA-256 is
  `d7c32636e19d1bce1b8b8994206355f42d0278b2f15048b14a948a8bbda1d540`.
- `OBSERVED`: MTP staging as removable-SD `Download/FindUAS_A028_DIAG.apk` completed; a fresh listing
  matched 197,061 bytes and readback SHA-256 matched (C-172).
- `NEGATIVE`: after installation the active button reported
  `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`, `ProtocolException`, detail
  `group transport callback failed`, and `11/12 count=0` (C-173).
- The fixed `02:04 -> 12:04`, `11/11` group selector obtained no successful transport callback;
  group protobuf, page, and terminator were not reached, and no set-enable request was sent.
- Boundary: the current UI does not expose Reply failure/ecode/callback detail. This is not
  unsupported, empty inventory, no `RID_UNLOCK`, RID off, or RF evidence. The result image is not
  committed; no identifier, raw reply, license material, motor action, or independent RF observation
  is recorded. Repeating the same black-box request is not the next discriminator.

### 2026-08-29 — exact v07 ADB package, gate patch, and staging checkpoint

- `STATIC`：the RC331 `07.00.0100` system aggregate matched its archived SHA-256; signed config and
  `0205` module passed `PRAK-2020-01` header-signature plus stored/plaintext checksum verification
  without force, skip, or truncate (C-174/A-029).
- `STATIC`：the extracted APEX `adbd` is `1,497,232` bytes, SHA-256
  `b300d9bb90f5941fe2952bc9f6dacc30e639a498be4435f59a4ae95134bd5422`, and byte-identical to the
  prior sample. Target-v07 code therefore exactly contains the `mp_state=production && dbg_cnt<1`
  `CNXN` early return before ordinary AUTH (C-175/A-030). Runtime path is
  `/apex/com.android.adbd/bin/adbd`; `/system/bin/adbd` is absent.
- `STATIC`：the exact package `dpad_fuli.apk` is `8,849,471` bytes, SHA-256
  `58b176eb1e17cacb7522914d282a69a677603ea9026993fc143c6a390211e44f`, and byte-identical to the
  audited developer assistant. Its ShellCommandActivity behavior is now exact-v07 package evidence,
  while installed-live hash/UID/SELinux remain unobserved (C-176/A-031).
- `STATIC`：a semantic userspace-copy patch changed only gate materialization
  `cset w21, lt -> mov w21, wzr`, retaining the normal TLS/auth target. A-032 is `1,497,232` bytes,
  SHA-256 `3fceaa1724a77a153c17f725a2e3f3001b0543e31e0830aca0c77d785df9225f` (C-177).
- `OBSERVED`：A-032 was written by MTP as removable-SD `Download/RC2_ADBD_CNXN.bin`; a fresh
  session confirmed one same-name object with the registered size, and full readback SHA matched
  (C-178). MTP object/storage/USB/device identifiers are excluded.
- `NOT ADMITTED`：the copy was not moved to internal storage, chmodded, or executed; init `adbd` was
  not stopped for this experiment and no new ADB response/shell exists. The prepared next session
  first collects live UID/SELinux/properties/hashes; only that output may determine a second-stage
  internal path and one-shot launch (C-179).

### 2026-08-29 — official FlySafe UI route and A-033 staging

- `STATIC`：exact DJI Fly 1.21.10 declares a non-exported
  `UnlockLicenseManagerActivity`, license-manager actions/resources, and native query/set-enable
  entry names (C-180).
- `STATIC`：A-033 `0.8.0-flysafe-diagnostic-export` adds zero-permission MediaStore export at
  `Download/FindUAS/FindUAS_RID_A033_latest.txt` without changing A-028's fixed `11/11` protocol or
  zero-`11/12` direct-button boundary. Two clean builds were byte-identical; 132 tests, lint
  0 errors/15 warnings, v2/zipalign and final-artifact checks passed (C-181/A-033).
- `OBSERVED`：`FindUAS_A033_DIAG_EXPORT.apk` was staged to removable-SD Download and a fresh
  readback matched `204,449` bytes and SHA-256
  `8ce8e0c13ecfcf69517a64e809a475b79bbc750124225744b6b35f281d3d7177` (C-182).
- `UNKNOWN`：A-033 has not been installed or run. The prepared next RID session is manual read-only
  inspection of DJI Fly's aircraft-license tab, followed by one A-033 diagnostic run; no toggle,
  motor action, or RF experiment is included.

### 2026-08-29 — exact DJI Fly 1.21.10 runtime owner recovery

- `OBSERVED`：a disposable ARM64 Android 11 emulator completed exact official DJI Fly `1.21.10`
  onboarding and rendered the non-exported license-manager Activity through an authorized emulator
  shell. Account and aircraft tabs appeared; without an aircraft, the aircraft tab requested a
  connection (C-183). This is not an RC 2 or aircraft result.
- `NEGATIVE`：a direct Frida attach identified runtime DEX candidates but destroyed the script and
  application before producing output. The injection path is not to be repeated on RC 2 (C-187).
- `OBSERVED`：an ordinary read-only root copy of the emulator process's private read/write mapping
  succeeded. A small independently written boundary scanner recovered 22 structurally valid DEX
  images for local analysis; vendor memory, DEX and decompiled output remain excluded (C-183).
- `STATIC`：exact current Java closes the official aircraft tab through the component, Activity,
  view model, `FlightRestrictImpl`, `JNIFSUnlockManager.queryFCLicensesJni` and the native query with
  current device ID (C-184).
- `STATIC`：the exact generic row action passes an existing license ID and Boolean through the
  current-device native setter, then refreshes displayed row states from a Boolean-array callback.
  The action was not executed (C-186).
- `STATIC`：exact current `LicenseType` and `LicenseData` model only types/tags 0--4/1--5. Unknown
  values fall into a tolerant polygon model, so this Java UI cannot semantically identify type 6
  `RID_UNLOCK`; separate MSDK 5.18 type-6 support remains a different artifact (C-185).

### 2026-08-29 — ART TI same-process FlySafe query callback

- `NEGATIVE`: a source-only no-op late-load agent requesting standard JVMTI 1.2 caused the exact
  non-debuggable DJI Fly emulator process to terminate in a native crash before its canary logged.
  Android 11 ART source instead identifies `0x70010200` as the applicable ART TI version (C-188).
- `OBSERVED`: the ART TI canary attached cleanly. The owner probe enumerated the loaded classes
  once, found exactly one unlock and event owner, obtained both singletons plus a nonzero current
  device ID, and left the PID unchanged (C-189).
- `OBSERVED`: the query agent loaded an independent callback through `InMemoryDexClassLoader`,
  registered only its callback natives and invoked the exact private current-device FC-license
  query once. Stage was zero, dispatch count one, callback failure was `417`, and the PID was still
  unchanged (C-190).
- The disposable emulator had no aircraft, so no success payload or inventory existed. Error `417`
  is not support, entitlement, empty-inventory, RID-off or RF evidence.
- `STATIC`: the public source-only successor adds an independent embedded-group parser, keeps a
  unique license ID in memory only, exposes counts/level/status Booleans, passes five synthetic
  host cases and builds its helper DEX plus AArch64 agent. Generated binaries and all vendor data
  remain excluded (C-191).

### 2026-08-29 — EU C0 panel wiring and reconnect-override boundary

- `CORROBORATED`: pinned public FreeFCC text (`597157bd52120dfeb9677f79a8ad46b6027ce8dc`) states
  that DJI Fly enforces the 120 m CE ceiling through a C0 class runtime flag that overrides
  flight-controller parameters on every connection, and that `cmd_set=3`/`cmd_id=0xF9` DUML writes
  are overridden on reconnect (C-198). The text names no `EU_CE_enable_c0_rid_0` owner and does not
  prove the RID-related C0 flag shares the altitude C0 cap layer.
- `STATIC`: `MainActivity` adds an independent EU C0 surface for `EU_CE_enable_c0_rid_0`
  (`0xF80992FE`): read-only F7/F8 probe, off/on/restore buttons gated on an F7/F8 baseline and live
  route, F7/F8 re-probe before each F9, double F8 readback, and baseline restore on any unconfirmed
  state; the existing `rid_ctrl_enable_0` surface is unchanged and the client allow-list admits the
  EU C0 F7/F8/F9 tuples separately (C-199).
- `STATIC`: panel positive-control name corrected to `g_config.flying_limit.max_height_0` for hash
  `0x0371238A`. Offline source and synthetic tests only; no live EU C0 read/write is claimed.

### 2026-08-29 — legacy mask corroboration and O4 receiver boundary

- `CORROBORATED`: pinned `CIAJeepDoors.py` (`a9a8b4430e847f22c75d4f89b14fe17388c82602`) reproduces
  the legacy `0x03/0xDA` (cmd 218) `fc_monitor` family `01`–`06` (purpose/DroneID-name/privacy-mask
  get-set) with sender PC 10/1 -> receiver FLYC 3/6 and DroneID at mask bit 3 (C-200).
- `NEGATIVE`: the same project's root README (`baedd24600cecd100d8d66f8350cae336f799dbf`) states the
  legacy mask only sends NULL/`fakeSN`, some firmware still randomly sends valid location packets,
  later DJI Fly/iOS reset the bits, and it is not reliable (C-201).
- `CORROBORATED`: public DragonSDR DroneID docs (`8d0126b91b943f5c22a0503a8414bc2441892328`) state
  DJI-private OcuSync DroneID is encrypted on O4 (Mini 5) and receiver-alone yields session hash +
  frequency/RSSI, with full telemetry requiring a licensed DragonScope config and broadcast only
  while motors spin (C-202). This encrypted boundary is limited to DJI's private DroneID protocol.
- `CORROBORATED`: public RUB-SysSec DroneSecurity NDSS 2023 README FAQ states DJI's Drone-ID is not
  the same as the standardized Bluetooth/Wi-Fi Remote ID, which follows EN 4709 (EU) / ASTM F3411
  (US) and is readable by a plain smartphone app (C-203). The standardized Remote ID bearer is
  therefore plaintext and independent-receiver A-B-A on it reads Basic ID without any DJI decoder.

### 2026-08-29 — official FlySafe type-6 enable surface and standard-RID plaintext receiver

- `CORROBORATED`: official DJI Cloud API FlySafe (`4ec6b0c7f9472aeb09a0a47949855d19c473ea07`)
  defines the device methods `unlock_license_switch` (`license_id` + `enable`) and
  `unlock_license_list` whose `type` 6 is "RID unlocking" and `rid_unlock.level` is 1=EU / 2=China
  (C-204).
- `CORROBORATED`: official MSDK 5.8.0 defines `RidUnlockType` (EUROPEAN/CHINA),
  `FlyZoneLicenseInfo.getRidUnlockType()`, and `setFlyZoneLicensesEnabled(info, isEnabled, cb)` for
  enabling/disabling an unlock license (C-205).
- `CORROBORATED`: OpenDroneID receiver-android README states the example receiver complies with
  ASTM F3411 / prEN 4709-002 BLE, WiFi NAN, and WiFi Beacon and decodes detailed content with no
  decryption or DJI-licensed decoder (C-206).

### 2026-08-29 — standard Remote ID bearer confirmed plaintext

- `OBSERVED`: the operator confirmed with a verified standard Remote ID detector plus the FindUAS
  host that the Mini 5 Pro broadcasts plaintext standardized Remote ID with a readable Basic ID
  when motors spin (C-207). The switch work now targets the standard ASTM F3411 / EN 4709 bearer;
  the DJI-private DroneID family is parked.
### 2026-08-30 — ART TI loader path discrimination

- `NEGATIVE`: the source-built carrier installed normally on the disposable Android 11 emulator,
  but its extracted `/data/app/...==/...so` path was split at the first `=` by the agent-spec parser.
  No canary or callback appeared and DJI Fly's PID stayed unchanged (C-208/A-035).
- `NEGATIVE`: copying the exact same SO bytes to a delimiter-free `trace_data_file` path terminated
  the target before canary. The bytes were then copied to a delimiter-free `apk_data_file` path;
  attach completed, the query returned `417`, and the target PID stayed unchanged. This controlled
  comparison closes that trace-label/path class rather than the agent bytes (C-209).
- `NEGATIVE`: a system-UID uncommitted PackageInstaller session accepted a streamed source-built
  payload, but the `apk_tmp_file` staging directory denied target search before agent load. No
  canary/callback appeared, PID stayed unchanged, and session abandon removed the directory
  (C-210/A-036).
- No RC 2, aircraft, account, motor, RF or setter action occurred. Both Android projects are
  published as source-only negative experiments. The next loader discriminator is the actual RC 2
  caller/target SELinux domains and a legitimate delimiter-free shared executable path or mediated
  descriptor (C-211).

### 2026-08-30 — RC 2 loopback by-index DUML cross-check

- `STATIC`: the public djiparam editor confirms the by-index FLYC family (`0xE0`-`0xE3`) is live on
  the RC 2 localhost bus (`40008` inject src `0x02` -> dst `0x03`, `40007` read), recording
  end-to-end get_info/read/write on wa151 (Lito X1) incl. a `forearm_led_ctrl` index-23 write, and
  noting `40009` only routes privileged-uid injects and the `40007` reader churns DJI Fly's FPV
  mirror (C-218).
- `STATIC`: WA150_Mini5Pro and WA151_LitoX1 share firmware table CRC `0x5f8b2ae1` and are
  disambiguated by count (1557 vs 1593) plus codename fallback (C-219).
- These reconcile the GlassFalcon direct-USB `0x0a` sender gate (C-213) as transport-specific: the
  by-index family can be reached under `0x02` over RC 2 localhost, but that deployment path requires
  an unlocked RC (system shell + permissive SELinux), outside this repository's boundary.

### 2026-08-30 — public DUML / Remote ID community survey

- `STATIC`: public GlassFalcon SDK records that the by-index FLYC family `0x03/0xE0`-`0xE3` is
  honored only under the PC/assistant source identity `0x0a`, not under mobile-app `0x02` (C-213).
- `STATIC`: the wa150 table shows `EU_CE_enable_c0_rid` inside a contiguous EU C0 block whose
  `EU_CE_Reg_RID_Enable` and `eu_ce_support_remote_set_level` rows are declared min 0 / max 0
  (C-214); the same project documents a Neo 2 firmware-revision index shift (C-215).
- `STATIC`: public Mini 5 Pro O4 DroneID research resolves the AA/87 + AES-128-CTR chain with the
  SM2 AA-to-note step and GNSS/takeoff trigger granularity (C-216).
- `CORROBORATED`: FreeFCC publishes `NO_REMOTE_ID.md` declaring no Remote ID disable ever, and its
  profiles carry no RID parameter (C-217).
- No vendor material, firmware, raw capture, serial, or credential was imported; the new facts are
  recorded as pinned public-reference claims and a survey note (22_COMMUNITY_DUML_RID_SURVEY.md).
### 2026-08-30 — aircraft firmware version confirmed

- `OBSERVED`: the operator confirmed the Mini 5 Pro aircraft firmware is `01.00.0600` (C-220),
  inside the CVE-2026-78306 / CVE-2026-77812 affected window; no RID-control conclusion changes.
### 2026-08-30 — community survey refinements

- `STATIC`: the public wa150 table has no `rid_ctrl_enable_0` or `ccc_broadcast_signal_quality`
  row (only `EU_CE_enable_c0_rid` 1306 and `EU_CE_Reg_RID_Enable` 1308); `ccc_broadcast_signal_quality`
  appears only in the wa020 Neo 2 table (C-221).
- `CORROBORATED`: the dated survey found no second Mini 5 Pro global-RID Boolean implementation
  beyond the SKYROVER `rid_ctrl_enable_0` chain (C-222).
### 2026-08-30 — standardized Remote ID synthetic codec

- `STATIC`: an independently written Python codec re-implements the standardized OpenDroneID
  25-byte message set and Message Pack; its encode reference vectors match the upstream Core C
  library byte-for-byte and 12 self-contained tests pass (C-223). It is confined to the separate
  synthetic source lane: no RF, socket, USB, DUML, or aircraft-control path.
### 2026-08-30 — by-index family third-source corroboration

- `CORROBORATED`: the public `o-gs/dji-firmware-tools` tooling sends parameter requests with sender
  `PC` (0x0a) to `FLYCONTROLLER` (0x03) and its get_info reply layout matches this repository's
  `rid_param_index_protocol.py` (C-224); the wa150 table also carries `ccc_unsupport_control_type`
  (250) and `ccc_poor_position_accuracy_on` (251) as China-broadcast siblings (C-221 refinement).
### 2026-08-30 — cross-model EU C0 / RID parameter inventory

- `STATIC`: across the public djiparam model tables, `EU_CE_enable_c0_rid` exists only in wa150/wa151
  (index 1306), the zero-range EU C0 registration block spans wa020/wa150/wa151/wa234/wa341, and
  `ccc_broadcast_signal_quality` exists only in wa020 (C-225).
### 2026-08-30 — wa150 RID-family by-hash bridge matched to o-gs

- `CORROBORATED`: the full wa150 RID/EU C0/China family was re-bridged to by-hash and matched
  `o-gs` `flyc_parameter_compute_hash` across 15 names (`EU_CE_enable_c0_rid_0` 0xF80992FE,
  `EU_CE_Reg_RID_Enable_0` 0xA2C325CE, `eu_ce_support_remote_set_level_0` 0xA8E96A09, and the
  remaining rows) (C-226).
### 2026-08-30 — host-tool importlib loader fix

- Registered `importlib`-loaded sibling modules in `sys.modules` across 16 host-tool/library/experiment
  files so the by-index/by-hash read-only probes (which load `@dataclass` protocol modules) no longer
  crash on Python 3.13+; added a one-shot `readonly_baseline_session.sh` wrapper for a write-free
  same-session baseline capture.
### 2026-08-30 — live Mini 5 Pro FLYC route: positive-controlled absence of both candidates

- `OBSERVED`: aircraft-direct USB FLYC route live — table 0 CRC `0x5F8B2AE1` count 1558; positive
  control `max_height_0` (0x0371238A) F7/F8 canonical (type 1/size 2/value 500) (C-227).
- `NEGATIVE`: `EU_CE_enable_c0_rid` absent — by-index 915-name enumeration has no such row (1306
  returns 0x0E) and by-hash `EU_CE_enable_c0_rid_0` (0xF80992FE) returns 0x03, positive-controlled
  by `max_height_0` and the neighbouring EU C0 rows (C-228).
- `OBSERVED`: EU C0 block index-shifted +1 vs the public wa150 table; sampled values Level 0,
  RID_Enable 0, fscap_EU_CE_Support 1, remote_set_level 0, all min 0 / max 0 (C-229).
- `NEGATIVE`: `rid_ctrl_enable_0` absent — by-hash F7 (0x3CBD864F) returns 0x03 and the by-index
  enumeration has no `rid_ctrl_enable` name, positive-controlled (C-230).
- No F9/E3/0x11/0x12 write, no license change, no motor or RF action was performed.
### 2026-08-30 — live Mini 5 Pro FLYC positive control and candidate absence

- `OBSERVED`: aircraft-direct USB FLYC route (0x0A→0x03) is live: table 0 CRC `0x5F8B2AE1`,
  count 1558; by-hash positive control `max_height_0` (0x0371238A) F7 metadata canonical
  (type 1, size 2, min 20, max 500, def 120) and F8 value 500.
- `NEGATIVE`: `EU_CE_enable_c0_rid` is absent on this FC — by-index enumeration of 915 named
  parameters has no such row (index 1306 returns status-only 0x0E) and by-hash F7 for
  `EU_CE_enable_c0_rid_0` (0xF80992FE) returns status 0x03, positive-controlled by the
  neighbouring EU C0 rows `EU_CE_Reg_RID_Enable_0` (0xA2C325CE) and
  `eu_ce_support_remote_set_level_0` (0xA8E96A09) returning canonical metadata (C-228).
- `OBSERVED`: the EU C0 block is index-shifted +1 vs the public wa150 table — EU_CE_Reg_Level 1308,
  EU_CE_Reg_RID_Enable 1309, … eu_ce_support_remote_set_level 1316 (C-229); public index 1306/1308
  are no longer authoritative for 01.00.0600.
- `NEGATIVE`: `rid_ctrl_enable_0` is absent on this FC — by-hash F7 (0x3CBD864F) returns status 0x03
  and the by-index enumeration has no `rid_ctrl_enable` row, positive-controlled (C-230).
- No F9/E3/0x11/0x12 write, no license change, no motor action, no RF experiment was performed.

### 2026-08-30 — takeover baseline and exact read-only probe staging

- Established a new work branch from the latest committed research; preserved all old checkouts and uncommitted drafts without importing them. Core excluded input/artifact hashes were rechecked against their existing register.
- Re-ran exact A-001 source/final-DEX audit and 21 audit mutations, then staged one new removable-SD `Download/FindUAS_A001_V010.apk`; fresh unique listing and same-session full readback matched the registered bytes/hash (C-231).
- A separate-session stock getfile attempt failed. The read-only exact-name enumeration/download in one session succeeded; no second upload or overwrite was performed.
- Asked the operator to install/open the probe and run its read-only capability check. Installation, execution and report remain unconfirmed. No ADB start, attach, DJI command, aircraft write, motor or RF action occurred.

- Built the distinct A-037 identity-safety revision offline: 170 JVM tests and two matching clean builds, with v2/zipalign/permission/native-entry checks (C-232). No Admin APK was staged or executed. Host fault tests now cover ACK uncertainty, recovery, frame/table validation and report failures; these fixes do not reopen the rejected FLYC candidates.

### 2026-08-30 — requested SD report export

- Implemented v0.11 report export in the same probe package, preserving read-only device checks and adding only the explicitly requested new SD report file. Both terminal results export; failures retry without rerunning the inspection.
- Completed 69 JVM tests, 8 auditor tests, final-DEX review, 30 adversarial mutations and two byte-identical clean builds (C-233). Retested the historical v0.10 artifact/21 mutations separately.
- Staged exact A-038 as `Download/FindUAS_A038_V011.apk` through the RC 2-only MTP target and verified full same-session readback (C-234). No existing file was overwritten.
- Requested operator installation and one check, followed by a simple saved-state confirmation so the host can fetch the report directly. Installation, run and report receipt remain unconfirmed; no ADB/attach/aircraft command/motor/RF operation occurred.

### v0.11 — first SD report received

- `OBSERVED`: retrieved the complete A-038 v0.11 report through RC 2 removable-SD MTP (C-235).
  It identified installed Fly `1.19.4` / code `3113157`, ARMv7. The report was `INCOMPLETE` because
  the old ELF64-only parser could not read the actual 32-bit ART build ID.
- The two original inspection sections completed. The full report remains private.

### v0.12 — complete report and sample-export revision

- `STATIC`: built A-039 v0.12 with ELF32 support, runtime component-enabled checks, fixed boot
  properties and an explicit APK/SDK sample-export button. 94 JVM tests, 8 auditor tests,
  37 rejected mutations and two identical clean builds passed (C-236).
- `OBSERVED`: staged `Download/FindUAS_A039_V012.apk` with matching readback; the operator ran it
  and the returned report was `COMPLETE`. The same ART file now supplied its GNU build ID;
  Fuli's three queried components were identified as disabled (C-237).
- Report completion times on the device clocks, converted to Asia/Shanghai: v0.11 at 23:08:57
  and v0.12 at 23:49:02.

## 2026-08-31

### 实机样本到达并完成校验

- `OBSERVED`：读取约 510 MB 的导出包，APK 与三份 SDK 库齐全；ZIP、manifest、逐文件
  SHA-256、APK 版本/ABI/签名及 APK 内库一致性检查通过（C-238，A-041）。
- 修复本地读取器对 libmtp 末次进度中 16 字节开销的误判；已落盘的完整内容独立验证通过，
  操作者无需重导。13 个离线边界向量通过，原始日志与样本保留在本地。

### 实机版本接口定位与 ARMv7 适配

- `STATIC`：定位 1.19.4 的 Java → JNI → FlySafe core 查询链，确认旧查询程序的接口和
  返回 envelope 可复用；增加未初始化设备 ID `-1` 的拒绝条件与 ARMv7 构建，解析器测试
  和两种 ABI 构建通过（C-239，A-042）。
- `STATIC`：另外定位独立 RID 状态链 `11/1C → RidImportModule → KeyRidWorkingStatusPush`
  及 Java 模型/监听入口，记录初值和缓存重放行为（C-240）。
- 操作者说明未办理解禁且暂时无法提供证书页截图；人工页面查看暂缓，后续优先独立 RID
  状态观测。该说明未被写成已读取的许可证清单。

### 开发助手入口恢复

- `STATIC`：确认生产模式启动策略会禁用 Fuli 整包，普通设置主按钮受平台签名限制；
  标准同版本、原签名替换在成功收尾恢复 DEFAULT，卸载更新与重启有对应恢复路径（C-241）。
- `OBSERVED`：USB 重连后，原始 A-031 包 staged 为 `Download/RC2_FULI_ORIG.apk`，完整
  MTP 回读匹配。操作者安装后确认开发助手可正常打开，内部按钮未点击（C-242）。

### 加载测试与 SD 文件整理

- `STATIC`：新增纯 ARMv7 ART TI canary，10 项 fake-VM 测试通过，4 个故障变体被拒绝；
  ARMv7/ARM64 构建成功。ARMv7 A-040 已放入 SD 卡并完整回读，尚未内部复制或执行（C-243）。
- `OBSERVED`：8 个旧研究 APK 移至 `Download/FindUAS/Archive/`，前后文件名/大小清单一致，
  没有删除文件；当前 A-039、Fuli 原包与其他当前工具留在 Download（C-244）。
- 已明确下一次操作者动作：打开 A-039，执行能力检查并保存开发助手安装后的新报告。

### 持续同步到 GitHub

- 按操作者要求补齐本轮源码、脱敏进度和证据/工件索引，并在首页加入本时间线入口。
- 协作规则已加入每次新结果后的 timeline、校验、提交及 GitHub 同步步骤。

### 安装后报告与直接 Shell 基线

- `OBSERVED`：安装后的 A-039 报告已完整收到，结果为 COMPLETE；Fuli 为 updated-system，
  原版本/hash/signer 与两份已检查 DEX 一致，三个固定入口均已启用；Fly/ART 身份未变（C-245）。
- `OBSERVED`：操作者在 Shell 页执行 `id`，照片确认 UID/GID 1000（system）和
  `u:r:system_app:s0`（C-246）。
- `OBSERVED`：随后执行 `ls -ldZ /data /data/app`，两目录均为 system:system、771；
  标签分别为 system_data_root_file 和 apk_data_file（C-247）。原始照片保留本地。
- 操作者要求暂时停止 GitHub 同步，后续变更仅更新本地仓库；当前尚未创建内部测试文件
  或执行 canary。
- `STATIC`：核对匹配 services 的扫描及启动清理规则：未登记子目录会进入包处理，而普通
  非 APK 文件在两处检查中被跳过；据此放弃新建测试子目录（C-248）。

### 目录内容确认

- `OBSERVED`：收到 `ls -laZ /data/app` 的两张重叠照片，覆盖七个子目录；拟用 canary
  文件名未出现（C-249）。固定 `DJI_FLY` 目录与此前报告路径一致，无需重复检查。

### F1 报告脚本准备

- `STATIC`：完成独立只读 F1 脚本，将进程身份与 SD 源文件校验合并到一次运行和一份
  SD 报告。源码审查、shell 语法、三项真实 Java 启动检查和七项主机模拟场景通过（C-250）。
- `OBSERVED`：将 A-043 暂存为 `Download/F1.sh`，完整回读与 7,196-byte 源码一致（C-251）。
  已给出单行启动命令；等待操作者运行后读取报告。本轮仍只同步本地。
- `OBSERVED`：操作者尝试后回传命令与错误照片：`sh` 未匹配到通配 SD 路径，尚未进入
  F1 脚本（C-252）。已改为先读取 `/storage` 目录内容，不重复原启动命令。
- `OBSERVED`：合并 stderr 后，目录命令明确返回 `/storage: Permission denied`（C-253）。
  下一项改为目录自身权限/标签及系统 volume 信息读取。

### 精确卷路径与 F2

- `OBSERVED`：读取到 `/storage` 为 0710、shell:everybody、mnt_user_file；已知调用方组
  可穿过该目录而不能列举。系统接口返回唯一 mounted public 卷，卷标识只保留本地（C-254）。
- `STATIC`：F2 仅去除全局目录枚举并更新版本标记；八个主机场景通过，含实际不可列举、
  可穿过父目录的启动测试（C-255）。
- `OBSERVED`：F2 已暂存到 SD，完整回读与 6,845-byte 源码匹配；旧 F1 移入 Archive，
  移动前后完整回读一致，没有删除（C-256）。已给出精确路径的单行启动命令，等待报告。
- `OBSERVED`：F2 已执行，2,553-byte 报告完整回传并通过格式检查。十二条命令只有 pidof
  返回 1/空；其余检查及 A-040 源文件大小/哈希通过。Shell 写 SD、主机读取的流程闭合（C-257）。
  目标进程检查转为 AMS 的单包记录，不重复 F2。
- `OBSERVED`：AMS 单包 LRU 查询返回 Fly HOME 主进程的非零 PID；主进程名精确匹配。
  记录 PID 后改为直接读取目标标签与 `/proc` 挂载信息，未重启 Fly（C-258）。
- `OBSERVED`：直接目标标签路径返回文件不存在，未显示挂载选项行；转为准备同次采集
  AMS 前后 PID 与 proc 信息的 F3 报告（C-259）。

### F3 同次进程报告

- `STATIC`：F3 加入严格 AMS 主进程解析、前后 AMS 查询、独立的 PID/starttime 稳定性
  字段、完整 proc 挂载行和调用方状态。修复额外冒号前缀及失败输出保存边界；14 个独立
  parser/capture 向量和 18 个完整 host 场景通过（C-260）。
- `OBSERVED`：F3 暂存及完整回读与 10,611-byte 审阅源码匹配；F2 移入 Archive，移动前后
  完整读回一致，无删除。已提供精确路径启动命令，等待报告（C-261）。
- `OBSERVED`：F3 的 3,677-byte 原始报告已完整收到。两个原始 AMS 记录的主 PID 一致；
  proc 挂载包含 gid=3009/hidepid=2。AMS 解析处的 heredoc 在 mksh 上尝试写内部临时文件，
  被拒绝两次，导致目标分支未进入及严格格式校验失败（C-262）。原始报告保留不改。
- 操作者请求省去逐条手工输入；开始实现有限会话的 SD 检查任务接收器与主机客户端。

### F4 兼容性修复与 SD 任务收发

- `STATIC`：F4 用 printf 管道替代 heredoc；Android mksh 的 18 个完整场景及 12 个临时
  目录权限对照通过，固定读取范围不变（C-263）。
- `STATIC`：B1 的 Java 页面启动快速返回、任务提交/输出校验、非法或不完整输入、结果
  冲突、内存中已验 helper 执行、TTL 与 64 项上限测试通过；主机 C 传输器编译、自测、
  sanitizer 与独立复核完成（C-264）。
- `OBSERVED`：F4/B1 已经 SD 完整读回核对。两次快速连续 MTP 准备在只读查询时报错；
  保留同一会话标识、加入调用间隔后准备成功，active 文件最后发布。状态为等待启动，
  已向操作者提供一次性启动命令（C-265）。进度仍仅保留本地。
- `OBSERVED`：操作者启动 B1 一次后，主机取得 READY，顺序发送 PING → SNAPSHOT → PING，
  三项 accepted/report/done 的身份、长度和摘要全部核验，返回码 0/10/0（C-266）。
- `OBSERVED`：F4 的 4,036-byte 报告严格解析成功，heredoc 问题已修复。前后 AMS 解析
  成功且 PID 相同；八项 pidof/proc 读取失败、其余十五项成功，`hidepid=2` 和 A-040
  源校验均读回（C-267）。未新增内部复制、attach 或飞机操作。

### 最小身份加载探针准备

- `STATIC`：核对 exact v07 的 system/AMS 加载入口、固定进程名选择及 ART TI 新环境的
  申请/释放路径（C-268）。
- `STATIC`：A-048 身份探针构建完成，32 项测试、sanitizer 及 6 个故障变体通过，两次 ARMv7
  构建同字节；A-040 保留不变（C-269）。
- `OBSERVED`：A-048 已在 SD 完整回读匹配。随后 B1 的第 4 项 STOP 和 CLOSED STOP
  均读回核验，为 B2 会话准备腾出入口；未停止 Fly（C-270）。
- `STATIC`：L1 通过 13 个真实 mksh 测试、39 场景，B2 通过 2 个 Java/mksh 分派测试，
  host client 的 29 个测试通过。修正了 FD3 继承、原生身份日志匹配和返回版本判定（C-271）。
- `OBSERVED`：L1/B2/身份探针在 SD 的完整回读全部匹配；旧 active 记录归档核验完成，
  新会话准备并最后发布 active，等待一次 B2 启动。精确操作已私下发给操作者（C-272）。
- `OBSERVED`：操作者启动 B2 后，CANARY_BASELINE 的 23 个检查全部通过，报告完整读回（C-273）。
- `OBSERVED`：CANARY_LOAD 在同一 Fly 进程中成功执行 A-048，原生身份、ART TI 与环境释放
  均成功，PID/UID/APK 未变；匹配的测试文件已删除（C-274）。
- `OBSERVED`：独立 CLEANUP 再次确认文件已不存在；copy/attempt 记录回读匹配，B2 的
  STOP 和 CLOSED STOP 均确认，无第二次 attach、未重启 Fly（C-275）。
- `STATIC`：继续核对 RID getter，区分 Lazy/默认 DTO、可变拦截器与 native_get_sync；
  下一步聚焦该原生同步入口的缓存语义（C-276）。

### 官方 RID 缓存采集准备

- 按操作者一次性请求，将既有六个提交直接推送至 GitHub main，终点 `2f31394`。
- `STATIC`：闭合 exact Fly 1.19.4 原生同步缓存链、现存 owner 门及序列化格式（C-277）。
- `STATIC`：完成独立 A-051、L2/B3 及解析/故障/恢复测试，核对 v07 app syscall 过滤器（C-278）。
- `OBSERVED`：USB 会话打开失败后经操作者重新插拔恢复；三份采集文件 SD 完整回读匹配，
  新会话已准备，并给出一次 B3 启动命令（C-279）。本轮尚未进行缓存读取，更新保持本地。
- `OBSERVED`：操作者启动 B3，基线 23 项全部通过（C-280）。
- `OBSERVED`：A-051 一次同步读取取得真实缓存值：RID 支持/正常1/1、EID0/0、失败码0；
  原生解析及环境释放成功，Fly PID/UID/APK 稳定，测试文件回收（C-281）。
- `OBSERVED`：独立清理确认文件不存在，copy/attempt 回读匹配，STOP/CLOSED STOP 完成；
  没有第二次读取或 Fly 重启（C-282）。代码、结果和时间线继续同步本地。
