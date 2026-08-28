# AGENTS.md

This file applies to the entire repository. It is the handoff contract for humans and coding
agents maintaining the RC 2 / Mini 5 Pro research record.

## Repository boundary

This repository contains independently written research documentation and machine-readable indexes.
It is not DJI software and does not contain a device-control product, firmware patch, unlock tool,
root package, Remote ID transmitter, license generator, account client, or radio-power profile.

Do not commit vendor APKs, firmware, partitions, shared libraries, decompiled vendor code, raw
private captures, accounts, sessions, signed licenses, device authorization keys, or temporary
patched images. Hashes and high-level independently written findings are allowed.

## Evidence discipline

Use only these status labels:

- `OBSERVED`
- `STATIC`
- `CORROBORATED`
- `NEGATIVE`
- `INFERENCE`
- `HYPOTHESIS`
- `UNKNOWN`
- `RETRACTED`
- `NOT ADMITTED`

Every new claim must state:

1. subject/version;
2. evidence type;
3. preconditions and route;
4. exact observation or static fact;
5. what it does not establish;
6. public source/document reference;
7. privacy/distribution disposition.

Do not use confidence percentages. Do not turn a timeout, absent push, or missing static string into
unsupported/off/empty. Do not turn an ACK, UI graph, onboard status, or socket write into RF proof.

## Source precedence

When records conflict, prefer:

1. later direct live evidence with positive controls and a recorded restore state;
2. exact final-artifact audit;
3. exact current static binary/source evidence;
4. pinned public primary source;
5. pinned prior art for the same product/version;
6. adjacent-version evidence;
7. inference or hypothesis.

Later retractions override earlier progress summaries.

## Current non-negotiable corrections

1. RC 2 UI firmware is `07.00.0100`; adjacent RC331 `10.00.0700/0205` evidence does not become
   an exact live-build fact without a matching package/hash.
2. Product-139 France EID static receiver is type/index 18/4 (`0x92`), not the older `0x03`
   assumption. `0x03/0x77` is France EID only.
3. `uav_cmd_req+0x08` is retry; receiver index is `+0x19`. Constructor retry is 3. Static
   product-139 EID Characteristics `+0x30` begins at 0, so the initial typed GET retains 3; a live
   update may cause its conditional clear. Typed SET retains 3. A retry-0 raw GET is a labelled
   laboratory single-shot, not exact typed policy.
4. `0x03/0x78` is EASA operator-registration identity; `0x11/0x4B` is Japan DIPS registration;
   neither is a global broadcast switch.
5. FlySafe type 6 `RID_UNLOCK` is signed account/FC-bound license state, not a locally fabricated
   Boolean. Never publish or synthesize license IDs, tokens, signatures, or blobs.
6. Historical localhost observer v0.1-v0.4 is `RETRACTED`. A second connection to RC-local
   `40007`/`40009` can replace DJI Fly's single active fd even if no payload is written.
7. v0.10 is the current zero-permission admission-probe candidate. Its exact APK SHA-256 is
   `fdad29bfb1237bc224a805d6eb5a99358a044bd226610d9f0fc33975d94b606c`; it has not been copied,
   installed, or run on RC 2.
8. V2.2 SHA-256 `7aa794ff8611582fd7cf27808a9d9eb11c44e307889d615d0511c100522845fb`
   is permanently rejected. V2.3 SHA-256
   `49d5d1d3b6e2dcb72b23f48b688effb2be3f320bec6997a9dcb15779904156c2` fixes the documented
   three defects but remains zero-send, fixed-zero-gated, unexecuted, `NOT ADMITTED`, and without a
   new independent post-fix audit report.
9. The global same-worker route-epoch assumption is withdrawn. A worker-tail sample is only
   `STABLE_OBSERVED` until all writers, lock order, `active_mutators`, `connection_epoch`, and
   shared `route_gate` are proven.
10. A callback return, cancel return, or fixed 100 ms delay is not request quiescence. Exact pending
    and Stopper membership, in-flight zero, lifecycle stability, and a worker-tail fence remain open.
11. Standard ADB is silent before RSA. The adjacent `adbd` production gate explains but does not
    prove byte identity with live v07. A first-packet public-key branch is an unexecuted,
    state-changing hypothesis.
12. FC/Sky `CN -> US -> CN` state loops do not establish RID, channel, regulatory mode, or EIRP.
    Ground US did not receive a matching ACK and readback remained CN.
13. NLD FCC Smart RC `2.0.0.6` packages seven JSON profiles byte-identical to pinned FreeFCC, but
    no runtime reference was found. Its reachable FCC path uses an opaque native-decoded online or
    native-handled offline payload. Do not attribute the visible 21-frame batch, keepalive, restore,
    or any Remote ID effect to the current runtime without independent dynamic evidence.
14. NLD's envelope is Base64/HMAC/AES-256-CBC, not hex. Online empty-argument selection loads a
    fixed embedded master; offline derivation uses an uppercase serial. Do not publish that master,
    licenses, caches, or device binding. Closing crypto/framing does not reveal the absent payload.
15. Drone-Hacks `wm1695` is O3 Air Unit, not Mini 5 Pro (`wa150`). A generic ADSB RID command name,
    FCC flag, FCC ModBox entry, or server job engine is not Mini 5 Pro software/CFC/RID support.
16. `UAVOIDManager.native_SetOIDReportEnable` controls app-side China OID network submission and can
    return direct success without upload. It is not an aircraft BLE/Wi-Fi RID switch and has no
    recovered state getter. `CN_OPERATE_ID_EFFECT` is distinct from RID cloud-control V2.
17. Drone-Hacks' Debug dictionary maps `RID_INFO` to `0x11/0x1A`, but it conflicts with current DJI
    Fly semantics at `0x11/0x0C` and `0x11/0x1C`. Treat it as passive/search vocabulary, not a WA150
    packet schema, getter, setter, or authorization to send guessed payloads.
18. Product-139 mounts `RidImportModule`, but `KeyRidWorkingStatusPush` is listen/update-only and
    `0x11/0x1C` has no recovered GET builder. The separate `KeyCloudControlData` is value-routed
    SET-only `0x00/0xDD`; its ACK/cache is not an applied RID readback. Do not invent a polling
    packet or promote cloud-control success to RF state.
19. Public metadata matching both WA150 `0802` versions and public BLE/network advisories make
    `0802` the strongest main/network owner candidate, not a proved RID owner or modifiable image.
    No public plaintext, target key, trust-root replacement, recovery image, or 0700 PoC was found.
20. Legacy FlyC `Detection` `0x03/0xDA`, subcommands `0x05`/`0x06`, is a high-confidence match for
    the NDSS multi-field DroneID mask. The reported RF effect retained packets and substituted
    selected fields with `fake`. It is proprietary OcuSync/AeroScope history, not a WA150
    ASTM/FAA/EU Broadcast RID switch; never migrate it into a current sender from class inventory.
21. Treat OPID `0x03/0x78`, Japan DIPS `0x11/0x4B`, China UOM `0x11/0xD6`, app location
    `0x11/0x43`, compliance serial, France EID, and type-6 as separate identity/policy planes.
    Exact schemas do not admit an editor without live HostID, baseline, readback, restore,
    persistence, and RF closure. LTE phone and UTMISS app-report paths are not Broadcast RID fields.
22. Product-139 China `OIDIdentifier` has no HostID ExtraParam and uses fixed receiver `0x92`,
    timeout 500 ms, retry 3. Its GET builder establishes only `[01,02]` in an 18-byte request; the
    tail is not visibly initialized, so never publish it as zero-filled or reproduce undefined
    bytes. Replies use result byte 1 and an eight-byte GET value at bytes 2--9; enforce minimum
    lengths 2/10 and keep the value masked. Separate conditional `UOMV1` status `0x11/0xD1` from
    this tag: runtime function ID `0x6C` must admit the module, its Sync action enters an external
    account/network helper, and it has no setter or restore semantics. Neither surface is an RF
    switch.
23. Current SKYROVER `1.2.0` adds an independent Boolean `RIDCtrlEnable`, distinct from France
    `EIDSwitch`, and exact native evidence maps it to FC parameter `rid_ctrl_enable_0`, hash
    `0x3CBD864F`, through `0x03/F7-F9` with default modern route `0x82 -> 0x92`. DJI Fly `1.21.10`
    lacks the same strings, so Mini 5 Pro support is a live F7/F8 question, not a static transfer.
    A-023 was the first fixed clean-room Binder client for that question. It was installed and run;
    Binder lookup, transaction 1, callback transaction 4, and exception parsing succeeded, but the
    target F7 ended in callback `ECode 1` after about 3.1 seconds without an F7 ACK. This is not a
    parameter-absence result because that build lacked a same-route positive control. Do not
    reinterpret France EID or AirSense as substitutes.
24. Live direct F7 is now closed for hash `0x3CBD864F`: RC 2 routed `0xAA -> 0x03` and
    aircraft-direct `0x0A -> 0x03` both returned one-byte status `03`, while same-session known
    height/distance controls succeeded. Direct USB `0x82 -> 0x92` also failed a known-height
    positive control, so it is not evidence about parameter support. Do not repeat raw USB route
    variants. A-024 `0.4.1-research` is the installed historical replacement: it first requires a
    maximum-height F7/F8 positive control on a Binder route before interpreting the RID target,
    serializes operations, keeps F9 locked behind validated metadata/range/baseline, and adds one
    full-window passive `0x11/0x1C` timeline. It was installed and both legacy and modern Binder
    routes failed the known-height F7 positive control with `ECode 1` after about 3.1 seconds; code
    therefore did not send target F7/F8/F9. Its passive timeline was later closed as the
    false-negative result in correction 26.
25. Adjacent RC331 `ActQueue` maps callback `ECode 1` to request retry exhaustion. This explains the
    observed A-023/A-024 terminal class but does not prove exact v07 byte identity, packet
    transmission, receiver support, parameter absence, or RF state. C-145 closes the two tested
    third-party Binder parameter routes for the current session; do not repeat generic route/address
    variants without a materially new official owner or verified firmware handler.
26. A-024's transaction-2 `0x11/0x1C` listener was accepted and ran the full 30-second window but
    delivered zero callbacks while the operator started the motors and an independent detector
    confirmed real RID RF. Treat this exact third-party Binder listener as a false-negative route;
    do not repeat it or use its zero count as off/unsupported/no-RF evidence. The official
    in-process observer remains a separate unknown.
27. Official MSDK 5.18 consumes a seven-byte minimum `0x11/0x1C` prefix but does not enforce a
    payload-length gate. Independent parsers require at least seven bytes and retain trailing bytes;
    never state that the wire packet is proven to be exactly seven bytes.
28. The preserved MSDK `DefaultUASDelegate` implementation maps an enabled, area-matched type-6
    `RID_UNLOCK` to `broadcastRemoteIdEnabled=false` and `NO_BROADCAST` when its product gate is
    true. This is design/static evidence with a protected leading-return layout, not proof that the
    current Mini 5 Pro executes it. Current native inventory/set-enable endpoints are `0x11/0x11`
    and `0x11/0x12`, with product-139 receiver `0x92`; query only through a bounded read-only probe,
    never invent or expose license IDs or send set-enable before a genuine baseline exists.
29. A-025 `0.5.0-flysafe-readonly` is the current offline inventory candidate. Its exact SHA-256 is
    `b137540f041cceb50a215bb95144c9f7ccf57fa4db4d2e7fc2108cb6ae68db80`; it has not been copied to
    RC 2 removable storage, installed, or run. Its new lane is fixed to system-Binder transaction 4,
    route `02:04 -> 12:04`, `11/11`, bounded selectors/parser, and privacy-reduced output. It has no
    admitted `11/12` tuple and the old `11/1C` button is removed. The suffix applies only to the
    FlySafe lane: separately gated legacy F7/F9, France EID, and OPID controls remain in the APK, so
    never call the entire artifact globally write-free.
30. Current DJI Fly 1.21.10 typed `LicenseData` parsing stops at fields 1--5; field 7/tag `0x3a` is
    retained only as an unknown field. `LicenseDataRID` field-7 semantics come from a separate MSDK
    5.18 artifact and make A-025 an independent compatibility decoder, not proof that current Fly
    recognizes type 6. Current Fly `11/12` carries only license ID and action, and no app-side edge to
    WA150 `0802`, motor state, or BLE/Wi-Fi enable was found. Do not turn that bounded negative into
    firmware absence, equate receiver `0x92` with module `0802`, or claim a patch offset.

## Privacy and redaction

Never commit:

- device/USB/Android/storage serials or local port topology;
- real UAS, registration, operator, account, UID, phone, or coordinate data;
- tokens, cookies, signed URLs, license IDs/blobs, ADB keys, or signer private material;
- exact local absolute paths, volume names, inode/mtime maps, or run UUIDs from a live probe;
- full raw telemetry/DUML/USB/network/logcat/Assistant captures;
- vendor binaries or copied vendor disassembly/decompilation logs.

Use `TEST-*` identifiers and artificial coordinates in fixtures. A public artifact hash is not a
license to redistribute the artifact.

## Document map and ownership

- `docs/02_EVIDENCE_REGISTER.md` and `evidence/claims.csv` are the normalized claim index.
- Topic documents contain detail and should reference claim IDs.
- `docs/03_TIMELINE.md` records actions, not intent.
- `docs/09_NEGATIVE_RESULTS.md` records failed paths and what they do not prove.
- `docs/10_HYPOTHESES_AND_UNKNOWNS.md` is the only place a new untested interpretation may be
  introduced before it is promoted to the evidence register.
- `docs/11_ARTIFACT_REGISTER.md` and `evidence/artifacts.csv` must agree exactly on hashes, sizes,
  audit state, device-use state, and disposition.
- `docs/13_HANDOFF.md` records dependency order and repository update procedure.
- `docs/15_LOG_INDEX.md` indexes excluded local log families; never copy those logs here.

## Updating a claim

1. Add or update a stable claim ID in `evidence/claims.csv`.
2. Update the corresponding Markdown topic and evidence register.
3. If the new result invalidates an older claim, mark the old claim `RETRACTED`; do not erase its
   history.
4. Update `docs/03_TIMELINE.md`, `docs/09_NEGATIVE_RESULTS.md`,
   `docs/10_HYPOTHESES_AND_UNKNOWNS.md`, or `docs/12_CURRENT_BLOCKERS.md` as applicable.
5. Update `CHANGELOG.md`.
6. Run link, CSV, whitespace, and sensitive-pattern checks before publishing.

## Live-experiment record minimum

A live record must include the date, subject/version, physical route, precondition reads, positive
controls, request count, timeout, strict matcher, result, final readback, restoration result, and
whether independent RF observation existed. Do not include private identifiers or raw frames.

A state change is not complete evidence without baseline, exact forward readback, exact restore,
final readback, and a statement of unmeasured effects. Software must not start motors; motor-on RF
observation is operator initiated.

## Repository validation

Before handoff:

```sh
git diff --check
ruby scripts/check_markdown_links.rb
ruby scripts/check_evidence_csv.rb
sh scripts/check_sensitive_patterns.sh
```

The repository is documentation-only. Do not add a build system or executable device code without
an explicit repository-scope decision.
