# Timeline

Times are Asia/Shanghai unless explicitly stated. File modification times were used only to order
work when a report did not contain a more precise timestamp.

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
