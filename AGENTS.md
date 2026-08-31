# AGENTS.md

This file applies to the entire repository. It is the handoff contract for humans and coding
agents maintaining the RC 2 / Mini 5 Pro research record.

For a new Codex task, start from the concise authorized-lab scope in
[`CODEX_PROJECT_PROMPT.md`](CODEX_PROJECT_PROMPT.md). It states the project outcome, allowed local
work, reversible-device boundary and completion evidence once; this file then supplies the detailed
repository and evidence rules.
For an immediate takeover of the current research state, use
[`NEXT_AGENT_HANDOFF_PROMPT.md`](NEXT_AGENT_HANDOFF_PROMPT.md).

The current research objective includes the real-aircraft RID switch, Basic/UAS ID, aircraft
position and operator position. Keep Operator ID separate from both Basic/UAS ID and operator
position. Each control needs an independent owner/baseline/readback/restore/RF evidence chain;
the scope extension does not admit a field editor. Synthetic OpenDroneID codecs remain offline.

## Repository boundary

This repository contains independently written research documentation, machine-readable indexes,
reproducible host tools, tests, and research Android source code. It is not DJI software and must
not be presented as an official, production-ready, or compliance-approved device-control product.

Source under `apps/`, `experiments/`, `libraries/`, and `host-tools/` may be committed when it is
independently written, reviewable, and its observed/admitted state is documented. Keep source,
tests, build instructions, and synthetic fixtures; do not commit generated APK/JAR/native binaries,
Gradle/CMake output, local SDK paths, or signing material. A source tree being public does not
change an experiment from `NOT ADMITTED`, `RETRACTED`, or `UNKNOWN` to a validated capability.

Do not commit vendor APKs, firmware, partitions, shared libraries, decompiled vendor code, copied
vendor disassembly, raw private captures, device authorization keys, patched vendor binaries,
flashable images, or temporary runtime dumps. Hashes, offsets,
minimal independently written patch/probe code, and high-level findings are allowed when the
corresponding evidence and redistribution boundary are explicit.

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

1. RC 2 UI firmware is `07.00.0100`. The verified signed-v07 system/`0205` chain now supplies exact
   target-package hashes for APEX `adbd` and `dpad_fuli`; those static facts still do not become
   mounted/installed live-file facts without live hash/property/context readback. Unmatched adjacent
   RC331 evidence remains adjacent only.
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
7. v0.12 (A-039) is the current zero-permission probe, staged as
   `Download/FindUAS_A039_V012.apk`, SHA-256
   `46eb6ef19971256a02514fc51a94b21522c488d82294c8853a7beb52fbab3ce4`.
   Its COMPLETE report and fixed Fly 1.19.4 APK/SDK samples were received and verified
   (C-236--C-238). Output is limited to generated reports under `Download/FindUAS/Probe/`
   and the user-requested fixed sample ZIP under `Download/FindUAS/Samples/`.
   A-001/v0.10 and A-038/v0.11 are historical; their installers are now archived (C-244).
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
11. Standard ADB is silent before RSA. Exact signed-v07 APEX `adbd` contains the
    `mp_state=production && dbg_cnt<1` pre-AUTH return and runs at
    `/apex/com.android.adbd/bin/adbd`; `/system/bin/adbd` is not the target path. v0.12 read
    `mp_state=production` and an empty `dbg_cnt` string; mounted adbd hash and branch log remain
    unobserved. A-032 changes only gate materialization, has
    matching removable-SD MTP readback, but has not been copied internally, chmodded or executed.
    Do not preselect an internal path before the live UID/SELinux/path-label baseline. First-packet
    public key remains an unexecuted, state-changing, non-default hypothesis.
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
    lacks the same strings, which by itself did not resolve Mini 5 Pro support. Correction 40 now
    records the later direct-USB FLYC result; do not reopen that question from the static mapping.
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
29. A-025 `0.5.0-flysafe-readonly` is the historical fixed inventory baseline. Its exact SHA-256 is
    `b137540f041cceb50a215bb95144c9f7ccf57fa4db4d2e7fc2108cb6ae68db80`; it was copied through MTP
    to RC 2 removable SD `Download` as `FindUAS_A025_RID.apk`, and same-session readback hash matched.
    An unintended long-name duplicate was removed. The user later explicitly reported installation
    complete; launch, execution, Binder activity, and result remain unknown. A-025 is superseded by
    gate-aware A-026.
    Its new lane is fixed to system-Binder transaction 4,
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
31. Current official FlySafe derives unlock version from passive current-token `03/09` Area Info and
    support from `03/42` WhiteList Info. Defaults `255/false`, missed/late/unusable pushes, and no
    replay are unknown, not unsupported. A-025 skips this gate and assumes V3/V4, so failure or a
    noncanonical completion is not an empty-inventory or no-entitlement result. Exact A-026 observes
    both in one bounded complete-route proxy window before admitting one `11/11`; in its first live
    60,003 ms run, neither push nor any callback class was observed, the gate remained
    `GATE_UNOBSERVED`, and the fail-closed sender issued zero `11/11` requests (C-165). This closes
    only that third-party passive-listener run, not aircraft support, entitlement, inventory, RID,
    RF, or the official in-process observer; external Binder cannot see DJI's device token.
32. Type-6 acquisition is the official FlySafe website background/product/device approval path,
    followed by DJI Fly's logged-in signed-group download, FC-SN/version/target-matched import,
    aircraft inventory, and existing-ID action. Normal Remote-ID registration and generic
    Unlock-a-Zone are separate. Never infer Mini 5 Pro eligibility from the public map catalog,
    region/country, or MSDK schema; never export credentials or create, transfer, or replay a license.
33. A-026 `0.6.0-flysafe-gated` / code 9 is `135,525` bytes with SHA-256
    `3c2ae42ac9f19a9e3dfe669ed6357bb8d2f1c38568af6a0f8d8b8f677fcbfec4`. Its tx2 gate withholds
    the same-process permit on malformed/failure/conflict/deadline/cancel and admits fixed tx4
    `11/11` only for support=true plus V3/V4. Two clean builds, 63 tests, lint 0 errors/13 warnings,
    v2 signature, zipalign, zero permissions, and no native/network/socket/shell path passed. It is
    staged as `FindUAS_A026_GATE.apk` with matching readback and new-session unique short-name/size
    confirmation; the operator subsequently reported installation complete (C-164) and ran its
    bounded gate flow (C-165). That run completed with both gate inputs unobserved, zero callbacks of
    every reported class, and zero `11/11` requests. External Developer Assistant is outside its
    sender allow-list, and retained gated F9/EID/OPID writes make it Admin rather than globally
    read-only.
34. A-027 `0.7.0-flysafe-direct-readonly` / code 10 is the current direct-query result. The
    `196,569`-byte APK has SHA-256
    `aa4bcd9c8aa96870cfbae1ba326d366cb8854a50ef4aff223f7bce4290ddcd81`; 127 tests, lint
    0 errors/15 warnings, two byte-identical clean builds, v2 signature, zipalign, zero permissions,
    and no native/network/socket/shell/external-process path passed. Its one-shot lane uses only the
    fixed `02:04 -> 12:04`, `11/11`, V3/V4 selectors, with no route scan or app retry. MTP staging as
    `Download/FindUAS_A027_RO.apk` passed fresh size and readback-hash checks. The operator then
    installed and ran its active button; it returned `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`
    at `ProtocolException`, with `11/12 request count=0`. Because the UI omitted the exception
    message, callback/ccode/group/page/terminator cannot be separated. This is not unsupported,
    empty inventory, no `RID_UNLOCK`, RID-off, or RF evidence.
    Public MSDK/Cloud API and community DUML prior art support only the generic families; they do not
    independently confirm this product-139/RC331 fixed route; C-169's ambiguous live result did not
    canonically confirm it.
35. A-028 `0.7.1-flysafe-direct-diagnostic` / code 11 is the current diagnostic result. It changes
    only safe UI classification: static `ProtocolException` text, numeric unexpected group/page
    ccode with page index, and terminator data length; command, route, selectors, and write boundary
    are unchanged. The `197,061`-byte APK has SHA-256
    `d7c32636e19d1bce1b8b8994206355f42d0278b2f15048b14a948a8bbda1d540`; 127 tests,
    lint 0 errors/15 warnings, two byte-identical clean builds, v2 signature, zipalign, zero
    permissions, and no packaged native library passed. MTP staging as
    `Download/FindUAS_A028_DIAG.apk` passed fresh size and readback-hash checks. The operator then
    installed and ran it: `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`, `ProtocolException`, detail
    `group transport callback failed`, `11/12 count=0`. Thus the fixed `11/11` group selector got no
    successful transport callback and protobuf/pages/terminator were not reached. The next
    discriminator is the already available Reply failure/ecode/callback diagnostic; do not repeat
    the same black-box request or call the result unsupported/empty/no-`RID_UNLOCK`.
36. A-033 `0.8.0-flysafe-diagnostic-export` / code 12 preserves A-028's fixed read-only `11/11`
    protocol behavior and adds a zero-permission MediaStore report at
    `Download/FindUAS/FindUAS_RID_A033_latest.txt`. Its exact SHA-256 is
    `8ce8e0c13ecfcf69517a64e809a475b79bbc750124225744b6b35f281d3d7177`; MTP staging/readback is
    closed, but installation, execution and a live result are not. Exact DJI Fly 1.21.10 declares
    a non-exported official license-manager Activity; inspect its aircraft list manually before
    another external Binder route experiment. A UI row or switch is inventory/management evidence,
    not type-6 identity, aircraft application, or RF proof.
37. Exact DJI Fly `1.21.10` runtime Java is no longer an unresolved protected-body gap. A disposable
    ARM64 Android 11 emulator rendered the non-exported license Activity, and authorized read-only
    process-memory recovery closed the current owner through `FlightRestrictImpl` and
    `JNIFSUnlockManager`. The current Java model defines only license types 0--4 plus unknown and
    protobuf fields 1--5; unknown falls into a tolerant polygon fallback. Therefore an official row
    is transport/inventory evidence but cannot semantically prove type 6. The generic existing-ID
    setter exists but was never executed. Direct Frida attach produced no artifact and must not be
    repeated on RC 2. Vendor APK/memory/DEX/decompiled output remain local and excluded; only the
    independent boundary scanner and evidence record are public.
38. Android 11 same-process FlySafe reachability is now observed on the disposable emulator.
    Standard JVMTI 1.2 late attach crashed the exact non-debuggable DJI Fly process before its
    canary logged; do not repeat it on RC 2. ART TI `0x70010200` attached cleanly, found exactly one
    loaded unlock/event owner pair, obtained a nonzero current device ID, dispatched the private
    FC-license query once, received callback `417` with no aircraft, and left the PID unchanged
    (C-188--C-190). The independent success parser is source-only, synthetically tested and keeps
    any unique existing license ID in memory/out of logs (C-191). This proves emulator owner/callback
    plumbing, not an RC 2 loader, inventory, entitlement, setter, restore or RF effect. The next
    route is an admitted RC 2 same-process loader; A-033 remains an external-Binder comparison.
39. Three emulator deployment variants are now closed and must not be repeated on RC 2 without new
    evidence. A normal extracted `/data/app/...==/...so` path is truncated at the first `=` by the
    agent-spec parser (C-208). A delimiter-free `trace_data_file` path terminated the target before
    canary while the same bytes worked from delimiter-free `apk_data_file` (C-209). An uncommitted
    PackageInstaller `apk_tmp_file` staging directory denied target search and was abandoned
    (C-210). The next discriminator is the actual RC 2 caller/target domains and a legitimate shared
    executable path or mediated descriptor; neither source-only APK is an active RC 2 candidate.
40. C-227--C-230 record a live `01.00.0600` direct-USB FLYC positive control, table count 1558
    and 915 named rows. Both `EU_CE_enable_c0_rid(_0)` and `rid_ctrl_enable_0` have
    positive-controlled absence on that surface. The neighbouring EU C0 block is shifted +1
    relative to the public table and its sampled flags have min/max 0. Do not repeat old parameter
    or route variants, treat index 1306 as authoritative, or unlock a neighbour as a substitute.
    This does not establish absence in DJI Fly, another firmware surface or encrypted `0802`.
    C-235--C-238 now supply the first RC 2 identity reports and installed Fly samples;
    C-245--C-247 add the post-install Fuli report and direct Shell identity/directory baseline;
    C-273--C-275 now close the tested A-048 loader and target self-identity baseline.
41. The installed Fly is `1.19.4` / code `3113157`, ARMv7. Earlier `1.21.10` results keep their
    emulator/static version labels. C-239/C-240 map the actual FlySafe and independent RID-state
    owners. Fuli's original same-version reinstall has been operator-confirmed to open DevActivity
    (C-241/C-242). C-245 confirms updated-system state and enabled components. Direct Shell
    `id` reports UID/GID 1000 and `u:r:system_app:s0` (C-246); `/data` and `/data/app` are
    mode 771, owned by system:system, with system_data_root_file/apk_data_file labels respectively
    (C-247). A-040 is the ARMv7 ART TI-only canary, built/tested and SD-staged but not executed
    (C-243). The separate A-048 later supplies the tested target identity/path in correction 42.
    Unlock registration is not a prerequisite for
    investigating the independent RID-state route.
42. A-048, `8,372` bytes with SHA-256
    `28b96744bef7f4cf3e64911134683ee71a6c950c44a88193fae2fdc7b60b4f4b`, loaded once through
    the normal fixed-name AMS route in the existing Fly `1.19.4` process (C-273--C-275).
    Canonical native identity, ART TI and DisposeEnvironment results succeeded; the observed
    base domain is `untrusted_app`, interface version is `0x70010200`, and AMS PID/UID/APK
    remained stable. The verified ordinary SO was removed, independent cleanup confirmed
    absence, and B2 closed by STOP. Preserve its permanent attempt record; do not repeat the
    successful canary. File/environment cleanup did not unload agent/plugin mappings or restart
    Fly. No RID getter or aircraft request ran. C-276 identifies the next exact
    `native_get_sync`/cache question: Lazy factories, mutable interceptors and default DTOs must
    remain distinct from an observed current RID value.

43. C-277--C-282 close the exact Fly `1.19.4` synchronous cache route and first live A-051 read.
    A-051 is `14,376` bytes, SHA-256
    `3dea20698eee556706189fd9910705fa60a1d80d0d18ba31a496fa443b38837b`; it uses initialized
    JNI/key metadata and existing SDK owners, bypassing Lazy/Rx wrappers. One cache call returned
    RID support/normal `1/1`, EID `0/0`, and formal failReason `0`; JNI/parse/disposal succeeded.
    PID/UID/APK were stable, the file was removed and independently confirmed absent, receipts
    matched, and B3 closed by STOP. Preserve A-051's permanent attempt marker. This is a cache
    snapshot without a receive timestamp or paired RF record; the next work is temporal/RF
    correlation and an authoritative reversible control owner.

44. C-283 closes exact1.19.4 RID cache freshness: UpdateType1000 is a1000ms expiry; the
    synchronous getter ignores it. Same-valued pushes refresh the CacheValue timestamp but
    do not notify change listeners. JNI exposes no timestamp; listener cancellation queues
    worker cleanup. Retain A051 as a cache observation, not a packet-arrival sample.
45. C-286--C-292 close RID cloud-source selection and A054's live comparison. ProductType
    cache is139; one fixed MMKV decode and one read of each ProductType/CloudControlData cache
    succeeded.41 rows and36 distinct nonempty candidates yield candidate match1/default match0
    with receiver18/4; this is set membership, not unique-country or applied-state attribution.
    PID/UID/APK were stable, file recovery and independent receipts passed, and B4 closed by
    STOP. A054 is22336 bytes, SHA-256
    `23c769203a26c6649c95770f50f49676965b06b30d292a302ddb2ce6eba8ea7f`.
    Preserve its permanent attempt record. Next resolve matched payload structure/receiver
    semantics rather than repeat the completed baseline or fabricate a cloud policy.

46. C-293 closes the exact paired-hex decode to complete00/DD payload boundary; the sender adds
    no RID-specific inner header/version/length. A057/L4/B5 are the new two-payload capture,
    host-tested and SD-staged with matching readbacks (C-294/C-295). C-296 then confirms B5
    startup and all23 L4 baseline checks; A057 itself is not yet executed. They keep
    matched-row count and missing/empty first DEFAULT separate, write only the two eligible hex
    strings to a private SD MediaStore report, and log numeric metadata. MTP failed before READ
    allocation; reconnect only USB and continue the original B5 session. No STOP was sent.
    Preserve A048/A051/A054 receipts and do not replay their completed probes.

47. C-297 records operator-reported connection instability during MTP recovery, then stable
    connection after G HUB and host ADB were stopped. Keep G HUB off per operator request.
    C-298 replaces the host transport with static libmtp plus a local guard against both
    automatic whole-device USB reset sites; do not use the old dynamic build or restart ADB
    as a transport fallback. A057 READ remains unallocated. The operator chose controller
    reboot; preserve old session/attempt history and prepare a new session after confirmation.

48. C-299/C-300 close operator-confirmed controller reboot recovery. Guarded MTP reads now
    succeed, including interception of close-time reset calls. The completed baseline-only
    session was archived with original history and a separate operator-reboot receipt, not
    a fabricated worker CLOSED. One fresh B5 session is activated and awaits startup.
    A057 remains unexecuted; repeat the post-reboot baseline before capture. Keep G HUB and
    host ADB stopped and retain the no-reset transport build.

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
7. After each material new result, append the completed action to `docs/03_TIMELINE.md` and
   synchronize and validate the local source/evidence records. The operator paused GitHub
   synchronization on 2026-08-31: keep changes local and do not push until they request resumption.
   Keep raw/private material excluded; preserve earlier published history.

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

The repository includes independently written research source code. Keep every imported project in
the directory class defined by `projects/README.md`, preserve its local README/AGENTS contract, and
exclude packaged binaries and generated output. Before publishing source, inspect it for private
identifiers, absolute local paths, credentials, vendor-derived code, and stale claims about live or
admitted status.
