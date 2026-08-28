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
