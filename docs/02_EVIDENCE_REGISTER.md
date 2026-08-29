# Evidence register

The canonical machine-readable rows are in [`evidence/claims.csv`](../evidence/claims.csv). This
document groups the same claim IDs for human review. Topic documents contain the detailed evidence
chain.

## Subject and version identity

| ID | Status | Claim | Boundary |
| --- | --- | --- | --- |
| C-001 | `OBSERVED` | RC 2 UI displayed `07.00.0100` | C-174 separately closes one signed target system chain; complete package set and mounted live-file identity remain unobserved |
| C-002 | `STATIC` | Adjacent RC331 `10.00.0700/0205` Android OTA/platform passed the recorded verification boundary | Adjacent version is not exact live v07 identity |
| C-003 | `STATIC` | RC331 `10.00.0700/0200` outer layer passed; protected inner FLYA did not | No verified plaintext inner image |
| C-004 | `STATIC` | WA150/product 139 is the current Mini 5 Pro static route candidate | Runtime owner/route must be re-established live |
| C-005 | `UNKNOWN` | Exact current product ID and private-owner route are not closed | Static product-139 mapping is insufficient |
| C-006 | `STATIC` | DJI Fly 1.21.10 is the principal analyzed app sample | It is not automatically the RC 2 loaded package |
| C-007 | `STATIC` | MSDK 5.18.0 supplies schema/handler cross-checks | MSDK declaration is not consumer-product support |
| C-008 | `OBSERVED` | macOS saw aircraft and RC 2 as separate DJI USB devices | Visibility is neither a supported MSDK session nor stable pair identity |
| C-112 | `CORROBORATED` | Public Mini 5 Pro metadata software versions exactly match WA150 `0802` in 0600 and 0700 | Strong application/camera-stack identity, not exclusive RID ownership |
| C-113 | `INFERENCE` | Public BLE/network advisories plus the two-module 0600-to-0700 manifest delta point to `0802` as the likely network-service repair owner | Not a plaintext diff, handler, or RID-control proof |
| C-114 | `NEGATIVE` | A bounded public search found no WA150 plaintext, target key, recovery image, RID handler, or reproducible 0700 PoC | Private, unindexed, and device-resident material is outside scope |

Details: [07_FIRMWARE_TRUST_BOUNDARY.md](07_FIRMWARE_TRUST_BOUNDARY.md),
[08_ANDROID_ADB.md](08_ANDROID_ADB.md).

## Remote ID state and control surfaces

| ID | Status | Claim | Boundary |
| --- | --- | --- | --- |
| C-009 | `NEGATIVE` | No ordinary current Boolean master switch spanning the identified regional RID surfaces was found | Bounded static search; managed/product-specific mechanisms remain possible |
| C-010 | `STATIC` | Product-139 France EID is `0x03/0x77`, static receiver `0x92` | France-only, not a global switch |
| C-011 | `CORROBORATED` | France EID is a distinct product/region surface | It cannot decide FAA/EASA/Japan/China state |
| C-012 | `NEGATIVE` | Two artificial direct-USB France-EID GET routes returned no canonical ACK | Private initialized DJI Fly owner path remains untested |
| C-013 | `CORROBORATED` | Timeout/unavailable/absent push is not off/unsupported/empty | Each negative retains route/window scope |
| C-014 | `STATIC` | `0x03/0x78` is EASA operator-registration identity | Not broadcast enable |
| C-015 | `STATIC` | `0x11/0x4B` is Japan DIPS registration | Not a global switch |
| C-016 | `STATIC` | FlySafe type 6 `RID_UNLOCK` is signed account/FC-bound license state | Not a fabricated local Boolean |
| C-017 | `UNKNOWN` | Mini 5 Pro server eligibility for type 6 is unknown | Public form/schema is insufficient |
| C-018 | `UNKNOWN` | Genuine type-6 inventory/validity/level/enabled baseline is unknown | No private license material retained |
| C-019 | `STATIC` | Current static RID working-status handler uses `0x11/0x1C` | Static handler does not establish live route/RF |
| C-020 | `OBSERVED` | Motors-off bounded window contained no strict working-status candidate | No state transition/official subscription closure |
| C-021 | `NEGATIVE` | Absence in that window proves only no observed matching frame | Not a support negative |
| C-022 | `OBSERVED` | Independent receiver-visible RID began after operator motor start | Real identity/location/raw capture excluded |
| C-023 | `UNKNOWN` | No synchronized onboard-status and independent-RF record exists | Onboard normal alone is not RF proof |
| C-056 | `STATIC` | DJI Fly consumes aircraft-reported RID state; it does not perform independent RF reception | Onboard normal is not RF proof |
| C-057 | `STATIC` | The recovered `0x11/0x1C` handler consumes a seven-byte flags/area/failure layout | Static layout does not establish live route or value |
| C-058 | `STATIC` | The public working-state model distinguishes working, idle, location, firmware, no-broadcast, unsupported, and unknown states | Model presence is not current-product reachability |
| C-059 | `OBSERVED` | A redacted historical other-product broker corpus contained strict `0x11/0x1C` and FlySafe push families | Not a current Mini 5 Pro session; raw corpus excluded |
| C-115 | `STATIC` | Product-139 constructs `RidImportModule` and registers `0x11/0x1C` as listen/update-only `KeyRidWorkingStatusPush` | Current app owner, not GET/SET, live state, or RF truth |
| C-116 | `STATIC` | The seven-byte status maps support/normal bits, area code, and failure; product-139 also derives regional support bits | Handler lacks a local length gate; unmapped bits and live values remain open |
| C-117 | `STATIC` | `KeyCloudControlData` is value-routed SET-only `0x00/0xDD`; ACK caches the request rather than returned applied state | No RID correlation, GET/readback, or stable disable semantics |
| C-118 | `NEGATIVE` | No current active RID read-only command, fixed safe tuple, reset/disable/debug handler, or applied-state echo was found | Existing `0x11/0x1C` push may be observed passively; it is not a query |
| C-123 | `STATIC` | Product-139 China `OIDIdentifier` Get/Set uses `0x11/0xD6`, fixed receiver `0x92`, 500 ms / retry 3, and 18-byte requests | GET tail bytes are not visibly initialized; live acceptance, restore, persistence, and RF mapping remain open |
| C-124 | `STATIC` | Product-139 EASA OPID has current `0x03/0x78` GET/SET/DELETE schema | Dynamic HostID, live acceptance, persistence, restore, and RF remain open |
| C-125 | `STATIC` | Product-139 Japan DIPS uses three-stage `0x11/0x4B` credential SET/QUERY | Non-atomic sensitive managed data; no live Mini 5 Pro closure |
| C-126 | `STATIC` | Current app periodically sends validated client location through encrypted `0x11/0x43` | App-to-device does not prove WA150 RF operator-location use |
| C-127 | `NEGATIVE` | The current LTE phone path is set-only LTE HYBRID business state, not Remote ID | Proprietary detector phone source remains unknown |
| C-128 | `STATIC` | `ComplianceSerialNumber` is get/listen-only and derives a compliance-form identity; no setter was found | Static candidate is not proof of RF Basic ID use |
| C-130 | `STATIC` | China `OIDIdentifier` replies put result at byte 1 and an eight-byte GET value at bytes 2--9 | Byte 0/result enum and live ACK remain unknown; defensive minimum lengths are 2/10 |
| C-131 | `STATIC` | China UOM real-name status GET uses `0x11/0xD1`, receiver 2/0, request `[01,00]`, and a status reply | External mappings remain incomplete; this is authentication status, not RID broadcast control |
| C-132 | `STATIC` | Runtime function ID `0x6C` conditionally admits `UOMV1`; Sync and cancellation are server-mediated account/real-name flows whose accepted result is applied through the D1 aircraft lane | No generic local setter/offline restore; live admission, authenticated result, applied readback, persistence, and RF remain unknown |
| C-133 | `STATIC` | `RidCaptureV1` creates exactly nine mixed-access characteristics: four listen-only capabilities, Japan action/result, OPID and France-EID GET+SET, and one SET-only position stream | Nine characteristics are not nine writable settings or a global switch; live Mini 5 Pro key existence is unknown |
| C-134 | `STATIC` | Function-discovery ID `0x37` admits `RidCaptureV1`; ID `0x38` admits unofficial-battery authentication, while `0x00/0xB8` is the general discovery transport | Function IDs, command IDs, and FlySafe PackType values are separate namespaces; live `0x37` admission is unproved |
| C-135 | `STATIC` | Current `0x11/0x0C`, `0x11/0x37`, and `0x11/0x39` surfaces are AirSense/ADS-B receive, agent-switch, and synthetic-target-test paths rather than RID configuration | Current application attribution does not prove every WA150 raw-firmware handler or the live semantics of the inherited agent switch |
| C-136 | `STATIC` | Current same-family SKYROVER `1.2.0` exposes an independent Boolean `RIDCtrlEnable` with GET, SET, Listen, and connection-time capability probing | It is separate from France EID, but dynamic SDK/UI support does not prove Mini 5 Pro admission |
| C-137 | `STATIC` | Native mapping closes `RIDCtrlEnable -> rid_ctrl_enable_0 -> 0x3CBD864F`, using FLYC `03/F7`, `03/F8`, and `03/F9` with default modern route `0x82 -> 0x92` | DJI Fly `1.21.10` lacks the same strings; live type, width, HostID, persistence, and RF effect remain unknown |
| C-138 | `HYPOTHESIS` | A fixed RC 2 Binder client can decide Mini 5 Pro admission only when a same-route known-parameter F7/F8 positive control succeeds before the target probe | A-024's two Binder controls failed, so known generic routes cannot test the target; an official owner/verified handler and all RF effects remain open |
| C-139 | `STATIC` | A full current same-family RID inventory found `rid_ctrl_enable_0` as the only RID-named FCConfig parameter; the remaining writable surfaces are regional identity/actions or opaque cloud policy | No second closed global Boolean/free-form family; catalog-only names and set-only cloud blobs are not implementations |
| C-140 | `NEGATIVE` | Fixed public projects and exact-string indexes contain no independent Mini 5 Pro/RC 2 implementation of `RIDCtrlEnable`; FreeFCC only corroborates modern route/framing with a different feature/hash | Bounded public negative only; unindexed/private work may exist and batch success is not per-command RID acceptance |
| C-141 | `OBSERVED` | Both validated direct F7 routes returned one-byte `0x03` for hash `0x3CBD864F`, while same-session known-parameter F7/F8 positive controls succeeded | Direct-route retrieval failure only; raw USB modern route failed its own positive control, so RC 2 Binder `0x82 -> 0x92` remains unresolved; no F9 sent |
| C-142 | `OBSERVED` | Installed A-023 reached the live `protocol` Binder callback path, but the fixed target F7 ended with `ECode 1` after about 3.1 seconds and no F7 ACK | No same-route positive control; not proof of route health, parameter absence, unsupported RID, or RF state; no F9 sent |
| C-143 | `STATIC` | Adjacent RC331 `ActQueue` emits callback `ECode 1` after request retries are exhausted | Adjacent code explains the terminal class but not the exact live-v07 cause or byte identity |
| C-144 | `STATIC` | A-024 adds per-route height F7/F8 positive control, serialized/gated reversible target handling, and a full-window passive RID-status timeline; final-artifact checks passed | Live positive-control result is C-145; target admission, passive delivery, cleanup, mutation, and RF remain unproved |
| C-145 | `OBSERVED` | Installed A-024's legacy and modern Binder routes both failed the known maximum-height F7 positive control with `ECode 1` after about 3.1 seconds; target F7/F8/F9 were therefore not sent | Closes only those two third-party Binder parameter routes in this session; not target absence, a motor-state result, official-owner failure, or RF evidence |
| C-146 | `OBSERVED` | A-024's accepted 30-second Binder listener received zero `0x11/0x1C` callbacks while motors were started and an independent detector confirmed real RID RF | The third-party listener is false-negative in this setup; this is not evidence that RID was absent or that the official owner has no status source |
| C-147 | `STATIC` | Official MSDK 5.18 registers `0x4011001C` and parses a seven-byte minimum flags/area/failure prefix | Minimum parser layout only; not proof of exact packet length, live delivery, or RF state |
| C-148 | `STATIC` | The preserved official SDK consumer maps an enabled region-matched type-6 `RID_UNLOCK` to `broadcastRemoteIdEnabled=false` / `NO_BROADCAST`; the branch only mutates the SDK status object and sends no command | Design evidence with protected layout; physical suppression must be aircraft-side and current Mini 5 Pro applicability, entitlement, and RF effect remain unproved |
| C-149 | `STATIC` | Current Fly generic transport and separate MSDK map inventory/set-enable to `0x11/0x11` and `0x11/0x12`, with product-139 receiver `0x92`; the MSDK artifact supplies the typed V2/V3/V4 schema | Current Fly's field-7 typed-parser boundary is C-152; live Binder acceptance, genuine type-6 inventory, mutation, restore, and RF remain open, and license material is excluded |
| C-150 | `STATIC` | A-025 implements a bounded modern FlySafe inventory lane over fixed Binder transaction 4, route `02:04 -> 12:04`, `11/11`, 6-second requests, strict V3/V4 selectors/parser, count 127, 128 page calls, and 90-second overall caps | Offline implementation only; the version label covers this lane, not the separately gated older F7/F9, EID, and OPID controls retained in the APK |
| C-151 | `STATIC` | A-025 final APK identity/audit passed 42 tests, lint with 0 errors/9 warnings, clean assemble, byte-identical rebuild, v2-signature/alignment checks, zero permissions, no native/network/socket/shell path, redacted reply handling, and no admitted `11/12`; the old `11/1C` button is removed | Artifact audit alone establishes no device behavior; C-154 records staging and C-163 records only user-reported installation, while execution/result remain unknown and the binary remains outside this repository |
| C-152 | `STATIC` | Exact current DJI Fly `LicenseData` typed parsing stops at fields 1–5; field 7/tag `0x3a` is skipped into `UnknownFieldSet`, while the separate MSDK 5.18 artifact typed-decodes field 7 as `LicenseDataRID` | Unknown bytes may survive, so this does not prove FC field-7 absence or type-6 non-support; A-025 is an independent MSDK-compatible exploration, not proof that current Fly understands field 7 |
| C-153 | `NEGATIVE` | Current Fly's generic `11/12` builder carries only license ID and enable/disable action, and bounded static tracing found no type-6/field-7/set-enable consumer linked to WA150 `0802`, motor state, or BLE/Wi-Fi broadcast enable | Encrypted WA150 plaintext is unavailable, receiver `0x92` is not module identity, and no absence-in-firmware or patch offset is proved; license, status/HMS, cloud policy, and motor-gated RF remain separate chains |
| C-154 | `OBSERVED` | A-025 was written through RC 2 MTP to removable-SD `Download` as `FindUAS_A025_RID.apk`; same-session readback SHA-256 matched the registered artifact, and an unintended long-name duplicate was removed | File staging and cleanup only; C-163 separately records later user-reported installation, but no execution, Binder response, inventory, license, state, or RF result exists, and no storage/USB/device serial is retained |
| C-155 | `STATIC` | Current official FlySafe web code exposes background-gated Mainland/Abroad RID applications, requires exact `Rid` product capability and a matching account device record, then creates an application under `/api/qep/unlock`; no type-6-specific application page was recovered in DJI Fly 1.21.10 | Generic DJI Fly Unlock-a-Zone and ordinary Remote-ID registration UIs are separate; the logged-in Mini 5 Pro capability/approval is unknown and locale/country changes do not grant entitlement |
| C-156 | `STATIC` | Current DJI Fly native code closes the official nonempty-login-token -> user -> signed license-group -> version/target-specific onboard blob -> FC import -> FC inventory -> existing-ID enable/disable chain | Client code does not mint a license; server presence is not FC acceptance, public MSDK support omits Mini 5 Pro, and no account secret, authenticated request, genuine license, or live import was used |
| C-157 | `STATIC` | Current DJI Fly passively derives FlySafe version from current-token `03/09` Area Info and support from `03/42` WhiteList Info before its manager admits an inventory query | Defaults `255/false`, missed/late/unusable pushes, and absent replay are unknown rather than unsupported; no safe active trigger or exact live Mini 5 Pro values were recovered |
| C-158 | `INFERENCE` | A-025's fixed V3/V4 query lacks a current-connection `03/09` + `03/42` admission phase, so failures or noncanonical completion can be gate/session false negatives | A canonical count-consistent completion still describes only the returned inventory; this does not prove passive pushes are third-party-Binder-visible or that A-025 must fail |
| C-159 | `INFERENCE` | The higher-information A-026 design is a bounded passive gate phase that admits one existing V3/V4 query only after usable support=true and version 1/2 | C-160/C-161 record offline implementation/audit, but this rationale is not runtime evidence; external Binder lacks DJI's token and missing pushes remain unknown |
| C-160 | `STATIC` | A-026 implements one tx2 `03/09 + 03/42` passive gate, full route consistency, fail-closed permit issuance, and one fixed V3/V4 `11/11` traversal with strict group/pages and retry-window handling | Offline implementation only; C-165 separately records the later gate-unobserved/zero-query live run; external Developer Assistant is outside the allow-list and the APK retains separately gated F9/EID/OPID writes |
| C-161 | `STATIC` | Exact A-026 is version `0.6.0-flysafe-gated` / code 9, 135,525 bytes, SHA-256 `3c2ae42ac9f19a9e3dfe669ed6357bb8d2f1c38568af6a0f8d8b8f677fcbfec4`; 63 tests, two byte-identical clean build pipelines, lint 0 errors/13 warnings, v2 signature, zipalign, zero permissions, and no native/network/socket/shell path passed | Artifact audit is not passive-push visibility, query behavior, entitlement, inventory, state, or RF evidence; Admin is not globally read-only |
| C-162 | `OBSERVED` | A-026 was written through MTP to removable-SD `Download` as `FindUAS_A026_GATE.apk`; same-session readback SHA matched, and a new-session list confirmed the unique short name and 135,525-byte size | Staging identity/uniqueness only; C-164/C-165 separately record later installation and the gate-unobserved/zero-query run; no object/storage/USB/device serial is retained |
| C-163 | `OBSERVED` | The operator explicitly reported that A-025 installation completed | User-reported installation only; launch, execution, requests, results, state change, and RF remain unknown |
| C-164 | `OBSERVED` | The operator explicitly reported that A-026 installation completed | User-reported installation only; launch, execution, passive callbacks, permit, Binder request/result, inventory, state change, and RF remain unknown |
| C-165 | `NEGATIVE` | Exact installed A-026 completed its instructed 60,003 ms gate run with `GATE_UNOBSERVED`: both `03/09` and `03/42` were unseen/unusable, all callback-class counts were zero, and fail-closed admission kept `11/11` request count at zero | This closes only the third-party system-Binder passive observation surface in that run; it is not evidence of aircraft non-support, absent entitlement, empty inventory, RID off/no RF, or official in-process observer absence; no write, motor action, independent RF observation, identifier, or license material occurred |
| C-166 | `STATIC` | A-027 implements one active read-only fixed system-Binder `02:04 -> 12:04`, `11/11` V3/V4 group/page query with no route scan and no app retry | The product-139/RC331 route is a local exact-static candidate, not independently confirmed by public prior art; failure is ambiguous and canonical inventory is not RF proof |
| C-167 | `STATIC` | Exact A-027 is `0.7.0-flysafe-direct-readonly` / code 10, 196,569 bytes, SHA-256 `aa4bcd9c8aa96870cfbae1ba326d366cb8854a50ef4aff223f7bce4290ddcd81`; 127 tests, lint 0 errors/15 warnings, two byte-identical clean builds, v2 signature, zipalign, zero permissions, and no native/network/socket/shell/external-process path passed | Final-artifact audit does not establish installation, execution, Binder acceptance, inventory, entitlement, state, or RF; sealed APK is excluded and the public tree is a later source successor |
| C-168 | `OBSERVED` | A-027 was staged through MTP as removable-SD `Download/FindUAS_A027_RO.apk`; a fresh listing matched 196,569 bytes and readback SHA-256 matched the register | Staging identity only; C-169 separately records the later install/run result, while identifiers/raw replies/license material remain excluded |
| C-169 | `NEGATIVE` | Installed A-027 entered the strict inventory parser and returned `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS` at `ProtocolException`; `11/12 request count=0`, so no canonical inventory or set-enable request formed | The UI omitted the exception message and lower-level callback/ccode/group/page/terminator class; this is not unsupported, empty inventory, no `RID_UNLOCK`, RID-off, or RF evidence |
| C-170 | `STATIC` | A-028 changes only A-027's safe UI diagnosis: static `ProtocolException` message, numeric unexpected group/page ccode plus page index, and terminator data length; command, route, selectors, and write boundary are unchanged | Offline diagnostic implementation only; it does not identify the A-027 cause before a live A-028 run |
| C-171 | `STATIC` | Exact A-028 is `0.7.1-flysafe-direct-diagnostic` / code 11, 197,061 bytes, SHA-256 `d7c32636e19d1bce1b8b8994206355f42d0278b2f15048b14a948a8bbda1d540`; 127 tests, lint 0 errors/15 warnings, two byte-identical clean builds, v2 signature, zipalign, zero permissions, and no packaged native library passed | Final-artifact audit does not establish installation, execution, Binder result, inventory, entitlement, state, or RF; sealed APK is excluded and the public tree contains the later unversioned diagnostic-file successor |
| C-172 | `OBSERVED` | A-028 was staged through MTP as removable-SD `Download/FindUAS_A028_DIAG.apk`; a fresh listing matched 197,061 bytes and readback SHA-256 matched the register | Staging identity only; C-173 separately records the later install/run result, while identifiers/raw replies/license material remain excluded |
| C-173 | `NEGATIVE` | Installed A-028 returned `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS` / `ProtocolException`, detail `group transport callback failed`, with `11/12 count=0`; the fixed `11/11` group selector got no successful transport callback, so protobuf/pages/terminator were not reached | Reply failure/ecode/callback diagnostic remains hidden; this is not unsupported, empty inventory, no `RID_UNLOCK`, RID-off, or RF evidence, and repeating the same black-box request is not a new discriminator |
| C-071 | `STATIC` | Product 139 maps the EU C0 RID key to `EU_CE_enable_c0_rid_0` | EU C0 policy, not a global switch |
| C-072 | `NEGATIVE` | Two live F7 routes returned status `0x03` without EU C0 metadata; no value/write followed | Refusal reason remains unknown |
| C-073 | `STATIC` | `dji_fly_rid_cloud_control_v2` is an opaque set-only area/product policy | No readback schema; not a stable Boolean |
| C-074 | `NEGATIVE` | Two legacy FlySafe inventory requests had no matching response despite adjacent positive controls | Not evidence of empty inventory or non-support |
| C-075 | `STATIC` | Modern type-6 query/enable mapping uses `0x11/0x11` and `0x11/0x12` with version-dependent sessions | Numeric commands are not safe standalone protocol |
| C-076 | `STATIC` | MSDK area strategy selects region-specific Remote-ID delegates | Does not set authoritative region or RF output by itself |
| C-077 | `STATIC` | Product 139 maps a broadcast-quality key to a product bitmap/quality parameter | Bit semantics and relation to ordinary RID are unknown |
| C-078 | `NEGATIVE` | Two F7 routes returned status `0x03` without broadcast-effect metadata; no value/write followed | Static-key absence and Boolean semantics are not established |
| C-106 | `STATIC` | Current `UAVOIDManager` Boolean gate controls app-side China OID reporting and can return direct success without upload | It has no gate getter and does not control aircraft BLE/Wi-Fi broadcast |
| C-107 | `CORROBORATED` | Current native and adjacent Java policy flows separate China OID network submission from RF RID | Adjacent Java is corroboration; no live network test was run |
| C-108 | `STATIC` | `CN_OPERATE_ID_EFFECT` and `dji_fly_rid_cloud_control_v2` are distinct policy paths | Neither is a recovered global RF Boolean with readback |
| C-109 | `NEGATIVE` | Current exact native search found France-EID wrappers but no product-139 ODID/OpenDroneID/global RF RID setter handler | Firmware, encrypted blobs, managed licenses, and future versions remain outside the negative |

Details: [04_STATE_ACCOUNT_LIMITS.md](04_STATE_ACCOUNT_LIMITS.md),
[05_RID_CONTROL_SURFACES.md](05_RID_CONTROL_SURFACES.md).

## Account identity layers

| ID | Status | Claim | Boundary |
| --- | --- | --- | --- |
| C-060 | `STATIC` | Local login is primarily a cached session-material layer | UI login does not prove server or FC state |
| C-061 | `STATIC` | Server validation and the local approximately 90-day validity window are a distinct layer | Local validity is not fresh server acceptance |
| C-062 | `STATIC` | DJI Fly separately attempts to synchronize nonempty account identity to the flight-limit subsystem | Attempt/log success is not equality proof |
| C-063 | `OBSERVED` | Both live transports returned false for `GetIsSetUUID` and legacy `GetUAVAppFlag` | Does not identify local-login or server-token state |
| C-064 | `STATIC` | Diagnostic 3000003 is derived from local app login state | Its absence cannot prove current token or FC identity |
| C-065 | `INFERENCE` | Correct-login evidence requires local session, server validation, and current-account/FC equality layers | Third layer remains unclosed; private values excluded |

Details: [04_STATE_ACCOUNT_LIMITS.md](04_STATE_ACCOUNT_LIMITS.md).

## Flight limits, region, and RF

| ID | Status | Claim | Boundary |
| --- | --- | --- | --- |
| C-024 | `OBSERVED` | Configured height=500 m, distance=5000 m, distance-limit disabled | Configured values are not the effective envelope |
| C-025 | `UNKNOWN` | A distinct unauthenticated 30/50 m runtime restriction remains unresolved | Config reads cannot confirm or exclude it |
| C-026 | `OBSERVED` | FC area completed `CN -> US -> CN` with readback/restoration | No RID/channel/RF conclusion |
| C-027 | `OBSERVED` | Sky country completed `CN -> US -> CN` with readback/restoration | No RID/channel/RF conclusion |
| C-028 | `NEGATIVE` | Ground US had no matching ACK and fresh GET remained CN | No applied change or permanent non-support claim |
| C-029 | `CORROBORATED` | Country/area state is not RID format, channel plan, power, or EIRP evidence | Requires separate policy/RF measurement |
| C-066 | `STATIC` | Modern area policy combines multiple inputs and synchronizes distinct surfaces | Final authority/convergence remains unknown |
| C-067 | `STATIC` | Internal debug sync and mock-country controls are separate | Neither is a production FCC toggle |
| C-068 | `STATIC` | DJI publishes region- and band-specific O4 EIRP ceilings | Ceiling is not current output or measurement |
| C-069 | `OBSERVED` | Sky and Ground read 5 at `0xFFFF0048` and 0 at `0xFFFF0063` | Values do not identify FCC/CE or RF output |
| C-070 | `NEGATIVE` | Legacy `0x06/0x21` PowerMode GET had no response on two fixed routes | Current mode and permanent support remain unknown |
| C-079 | `OBSERVED` | Final probes reported FC/Sky/Ground CN; RC/DJI Fly policy country unavailable | No power-cycle-persistence or complete-convergence proof |

Details: [04_STATE_ACCOUNT_LIMITS.md](04_STATE_ACCOUNT_LIMITS.md),
[06_REGION_RF_POLICY.md](06_REGION_RF_POLICY.md).

## NLD FCC Smart RC static comparison

| ID | Status | Claim | Boundary |
| --- | --- | --- | --- |
| C-080 | `STATIC` | The official Smart RC ZIP matched the analyzed `2.0.0.6` APK bytes | The downloads page still displayed `2.0.0.1`; no APK was executed |
| C-081 | `STATIC` | Seven packaged profiles are byte-identical to pinned FreeFCC but have no found runtime reference | Packaged data is not proof of the current command sequence |
| C-082 | `STATIC` | Normal FCC uses a native-built request, opaque online or native-offline payload, native decode, and native DUSS send | Exact frames, ordering, restore, and effect remain hidden |
| C-083 | `STATIC` | The reachable path connects to RCLink and sends through DUSS; explicit handover/hijack code exists but has no found current call site | Main-path broker takeover is not established |
| C-084 | `STATIC` | C0 obtains online VPN configuration, starts server-routed WireGuard, relaunches DJI Fly, and schedules automatic stop 25 seconds after tunnel UP | Actual route breadth, earlier/later stop, server behavior, and the claimed 500 m/speed causal step remain unknown |
| C-085 | `NEGATIVE` | No identifiable RID UI, command, profile, setting, service, or handler was found in the bounded `2.0.0.6` static search | Opaque native/server or external-DJI-Fly side effects remain possible |
| C-086 | `STATIC` | Native verifies an RSA-3072/SHA-256 entitlement bound to version, serial, device type, and the Android-keystore P-256 public key | Verification cannot mint a license; server decisions remain unavailable |
| C-087 | `STATIC` | The parameter editor models live schema, typed validation, write result, and post-write verification | Target-pair live success/coverage is unverified; UI preview values are not Mini 5 Pro parameters |
| C-088 | `STATIC` | The C0 repair path validates hosted DJI Fly by size, package, and numeric version-equivalence to 1.21.4 without a found fixed hash or signer allowlist | The comparator is weaker than exact version-string equality; the hosted APK was not independently obtained |
| C-089 | `STATIC` | The bundled Android 11 Package Installer contains valid v1/v2/v3 DJI-subject signatures and privileged declarations | Android 11 selects v3; subject text does not prove provenance or live-build privilege |
| C-090 | `NEGATIVE` | No identifiable ADB/root/remount/DJI-file-patch/Binder-FCC path was found in the bounded main-app search | Opaque data, server behavior, helpers, and hosted DJI Fly remain outside the negative |
| C-091 | `STATIC` | Boot normally posts a notification and starts auto FCC only when its armed preference is set; stop clears it | Sticky service presence is not unconditional boot activation or proof of FCC effect |
| C-092 | `STATIC` | Runtime inquiry normalizes and longest-prefix maps a returned model token | Model classification is not exact controller firmware or aircraft-product identity |
| C-102 | `STATIC` | FCC payload uses authenticated Base64 envelope, HMAC key separation, AES-256-CBC, and strict PKCS#7; offline key derivation binds an uppercase serial | No real response/blob or embedded-master value is published |
| C-103 | `STATIC` | Offline entitlement uses RSA-3072 PKCS#1 v1.5/SHA-256 and exact device binding | Public verification material cannot create a valid entitlement |
| C-104 | `STATIC` | Offline cache framing, bounds, permissions, fsync, and atomic replacement are closed | No licensed cache or decrypted command was obtained |
| C-105 | `STATIC` | Decrypted command schema and native DUML framing/write loop are closed | Actual commands, ACK/readback, restore, and RF effect remain unknown |

Details: [16_NLDFCC_STATIC_ANALYSIS.md](16_NLDFCC_STATIC_ANALYSIS.md).

## Drone-Hacks static comparison

| ID | Status | Claim | Boundary |
| --- | --- | --- | --- |
| C-093 | `STATIC` | The analyzed MSI matches the official `2.0.29` release bytes and has a valid Skymod Authenticode signature | Signed provenance is not feature proof; nothing was executed |
| C-094 | `STATIC` | The Rust/Tauri client is a broad DUML/USB/ADB/firmware/parameter executor for server-defined jobs | Exact production jobs and restore logic are not all in the MSI |
| C-095 | `STATIC` | Public CFC uses a firmware-resident hook plus runtime Name-field commands on listed older models | Mini 5 Pro and RID are not listed |
| C-096 | `NEGATIVE` | No explicit RID feature, switch, local command, parameter, job, or Mini 5 Pro implementation was found | Generic command names and private server jobs remain outside the negative |
| C-097 | `CORROBORATED` | Public data recognizes `wa150` but exposes no software platform/license/product; separate FCC ModBox compatibility exists | Hardware FCC compatibility is not software/CFC/RID support |
| C-098 | `STATIC` | Generic DUSS vocabulary includes ADSB RID/EID/parameter labels | Names are not command semantics, reachability, readback, restore, or RF proof |
| C-099 | `STATIC` | One-time FCC is server-authorized and cached per device/model | FCC path is not RID evidence |
| C-100 | `STATIC` | Parameter workflow retains original/current typed values and verification-aware outcomes | No RID-owned WA150 parameter is established |
| C-101 | `UNKNOWN` | CFC is a plausible architecture for a stable target-owned RID control | WA150 plaintext, signing, hook, recovery, RID semantics, and RF closure are missing |
| C-110 | `STATIC` | Drone-Hacks' Debug path numerically maps ADSB `RID_INFO` to `0x11/0x1A`, `EID_INFO` to `0x11/0x35`, and related IDs | Display mapping is not a caller, payload, getter, setter, product gate, or RF effect |
| C-111 | `STATIC` | Its `0x0C`/`0x1C` labels conflict with current DJI Fly while `0x43`/`0x50` agree | The mixed table is not an authoritative WA150 protocol schema |

Details: [17_DRONE_HACKS_STATIC_ANALYSIS.md](17_DRONE_HACKS_STATIC_ANALYSIS.md).

## Legacy proprietary DroneID comparison

| ID | Status | Claim | Boundary |
| --- | --- | --- | --- |
| C-119 | `STATIC` | Legacy DJI midware maps FlyC `Detection` to `0x03/0xDA`; subcommands `0x05`/`0x06` set/get an eight-field mask | Named polarity is not independently live-confirmed |
| C-120 | `INFERENCE` | This is the high-confidence match for the NDSS paper's undisclosed multi-field DroneID control | The paper did not publish tuple/payload or exact switch-test model/firmware |
| C-121 | `STATIC` | The paper reports packets continued while selected legacy fields became literal `fake` | It did not suppress packets and is not modern ASTM/FAA/EU RID |
| C-122 | `NEGATIVE` | No public primary evidence transfers the handler or mask to WA150/Mini 5 Pro | Generic old class inventory is not current aircraft support |

Details: [18_LEGACY_DRONEID_DETECTION.md](18_LEGACY_DRONEID_DETECTION.md).

## ADB and Android access

| ID | Status | Claim | Boundary |
| --- | --- | --- | --- |
| C-030 | `OBSERVED` | Host sent ADB `CNXN`; RC 2 returned no ADB packet | Live trace alone does not identify implementation reason |
| C-031 | `STATIC` | Adjacent unstripped `adbd` has production-state CNXN drop before RSA | Adjacent binary is not exact live-v07 identity |
| C-032 | `RETRACTED` | The adjacent-version-only explanation is superseded by exact signed-v07 package evidence | C-174/C-175 promote target-package static code, not live property/branch observation |
| C-033 | `HYPOTHESIS` | First-packet AUTH public-key branch may reach confirmation | State-changing/unexecuted and may persist a key; not the default while A-032 ordinary auth is untested |
| C-174 | `STATIC` | The verified signed `07.00.0100` system chain yielded exact APEX `adbd` identity: 1,497,232 bytes, SHA-256 `b300d9...422b`, Build ID `c30245...5422` | Target-package static evidence; not readback of the currently mounted live file; vendor bytes excluded |
| C-175 | `STATIC` | Exact v07 `handle_packet(CNXN)` contains the `mp_state=production && dbg_cnt<1` early return before AUTH; runtime executable is `/apex/com.android.adbd/bin/adbd` | Live property values and branch log remain unobserved; `/system/bin/adbd` is not the target path |
| C-176 | `STATIC` | Exact v07 `dpad_fuli.apk` is byte-identical to the audited package and contains the system-shared-UID shell-command page using `Runtime.exec` | Installed-live package hash, actual UID/SELinux context, and any command result remain unobserved |
| C-177 | `STATIC` | A-032 changes only exact-v07 gate materialization `cset w21, lt -> mov w21, wzr`, preserving the normal TLS/auth path; output SHA-256 is `3fceaa...225f` | Offline derivative design only; no loader/FunctionFS/auth/shell result and no binary redistribution |
| C-178 | `OBSERVED` | A-032 was staged by MTP as removable-SD `Download/RC2_ADBD_CNXN.bin`; fresh size and full readback SHA matched | Staging only; no internal copy, chmod, execution, daemon stop, ADB result, or state change |
| C-179 | `NOT ADMITTED` | One bounded operator session is prepared to capture live gates and try the exact staged userspace copy before one host `CNXN` | Entire execution remains pending; any mismatch stops before launch and shell identity must be read, not inferred |

Details: [08_ANDROID_ADB.md](08_ANDROID_ADB.md).

## Retracted paths and offline artifacts

| ID | Status | Claim | Boundary |
| --- | --- | --- | --- |
| C-034 | `RETRACTED` | Localhost observer v0.1-v0.4 withdrawn | Do not reconnect or use live |
| C-035 | `CORROBORATED` | Adjacent broker can replace the single active fd on newcomer connect | Offline decoder correctness cannot make coexistence safe |
| C-036 | `NOT ADMITTED` | v0.10 is current exact admission-probe candidate | Never copied/installed/run on RC 2 |
| C-037 | `STATIC` | v0.10 reports environment/identity, not RID state/control | A successful run would remain a gate result |
| C-038 | `RETRACTED` | V2.2 exact artifact permanently rejected | Two P1 + one P2; never install/attach |
| C-039 | `NOT ADMITTED` | V2.3 fixes those three defects | Zero-send/fixed-zero/unexecuted; no new independent post-fix audit |
| C-040 | `RETRACTED` | Global same-worker route epoch withdrawn | Cannot admit a request |
| C-041 | `INFERENCE` | Worker-tail result is only `STABLE_OBSERVED` | Complete writers/locks/epoch/gate absent |
| C-042 | `NEGATIVE` | Callback return, cancel return, or 100 ms delay does not prove quiescence | Exact pending/Stopper/fence evidence required |
| C-043 | `UNKNOWN` | Private-owner GET lifecycle/route/quiescence gates remain open | No GET or SET admitted |
| C-044 | `STATIC` | Retry is request `+0x08`; receiver index `+0x19`; constructor retry 3 | Retry-0 raw request is a labelled lab profile, not typed equivalence |
| C-045 | `STATIC` | Static EID Characteristics `+0x30=0`; initial typed GET retains retry 3 | Runtime value/conditional behavior unobserved |
| C-046 | `STATIC` | Typed France-EID SET retains retry 3 | Static schema is not authorization |

Details: [09_NEGATIVE_RESULTS.md](09_NEGATIVE_RESULTS.md),
[11_ARTIFACT_REGISTER.md](11_ARTIFACT_REGISTER.md),
[12_CURRENT_BLOCKERS.md](12_CURRENT_BLOCKERS.md).

## Evidence interpretation and final state

| ID | Status | Claim | Boundary |
| --- | --- | --- | --- |
| C-047 | `RETRACTED` | The old cache-only search found no exact complete v07 set; C-174 later closed the exact signed system/`0205` lane from another archive | Complete all-module set and mounted live identity remain open; unmatched adjacent evidence stays adjacent |
| C-048 | `CORROBORATED` | ACK is not state readback; readback is not persistence | Record evidence stage separately |
| C-049 | `CORROBORATED` | Onboard normal is not independent RF reception | External receiver/analyzer required |
| C-050 | `CORROBORATED` | Generated key name is not live handler evidence | Exact handler/route required |
| C-051 | `STATIC` | Repository is documentation/index only | No control/patch/root/transmitter/account product |
| C-052 | `CORROBORATED` | Complete state-change evidence needs baseline, forward readback, restore, final readback, and unmeasured-effects statement | Motor-on RF remains independently observed |
| C-053 | `UNKNOWN` | Stable recoverable Mini 5 Pro RID control remains unproven | Static paths, ACKs, UI, and onboard state are insufficient |
| C-054 | `STATIC` | Artifact hash may be public identity metadata | Hash does not permit redistribution |
| C-055 | `UNKNOWN` | No new independent V2.3 post-fix audit conclusion exists | V2.3 remains `NOT ADMITTED` |
| C-129 | `HYPOTHESIS` | A separate external OpenDroneID source could provide synthetic configurable standards fields | No RF backend/hardware/readback/stop/reception evidence is implemented or admitted |

## Official FlySafe UI, exact current owner, and A-033 handoff

| ID | Status | Claim | Boundary |
| --- | --- | --- | --- |
| C-180 | `STATIC` | Exact DJI Fly 1.21.10 declares the non-exported license-manager Activity and current runtime recovery closes its same-process component/view-model/native query and generic set-enable owner chain | Current Java type-6 semantics are separately negative; UI state is not RF proof |
| C-181 | `STATIC` | A-033 is the exact zero-permission diagnostic-export build; 132 tests, lint, reproducible build, signing/alignment and final-artifact checks passed | No install/run/Binder/inventory/RF result; direct button remains `11/11` only |
| C-182 | `OBSERVED` | A-033 removable-SD staging and fresh full readback matched its registered size and SHA-256 | Staging only; device and MTP identifiers are excluded |
| C-183 | `OBSERVED` | Exact DJI Fly 1.21.10 completed onboarding and rendered its non-exported license Activity in a disposable ARM64 Android 11 emulator; authorized root process-memory reading recovered 22 bounded runtime DEX images locally | Emulator only; no RC 2/aircraft/inventory/RF evidence and no vendor bytes are published |
| C-184 | `STATIC` | Exact current Java closes the aircraft tab through `FlightRestrictImpl` and `JNIFSUnlockManager.queryFCLicensesJni` to the native current-device query | Same-process ownership is not a successful live RC 2 query or type-6/RF proof |
| C-185 | `STATIC` | Exact current Java defines license types 0--4 plus unknown and protobuf fields 1--5 only; an unknown record falls through to a tolerant polygon model | Current Java cannot semantically identify type 6; native/FC/opaque-server support remains open |
| C-186 | `STATIC` | Exact current generic row switch passes an existing license ID and Boolean through the native current-device setter, then refreshes row states from its Boolean-array callback | Never executed; no entitlement creation, type-6 identity, restore, aircraft application, or RF proof |
| C-187 | `NEGATIVE` | Direct Frida attach in the disposable emulator found candidates but destroyed the script/app before output; read-only root process-memory copying worked instead | Narrow emulator result; do not repeat injection on RC 2 and do not publish vendor dumps/DEX/output |
| C-188 | `NEGATIVE` | Standard JVMTI 1.2 late attach to exact non-debuggable DJI Fly in the disposable emulator ended in a native process crash before the canary logged | Emulator only; Android 11's ART TI version is the applicable late-load interface and the standard attach must not be repeated on RC 2 |
| C-189 | `OBSERVED` | An independent ART TI `0x70010200` agent found the exact loaded FlySafe owner classes, obtained both owners plus a nonzero current device ID, and left the DJI Fly PID unchanged | Authorized emulator-shell reachability is not an RC 2 loader, inventory, setter or RF result |
| C-190 | `OBSERVED` | The same-process agent dispatched the exact private current-device FC-license query once and received callback error `417`; stage was zero, dispatch count one and PID unchanged | No aircraft was attached, so no success payload/type-6 inventory existed; the error is not unsupported/no-license/RID-off/RF evidence |
| C-191 | `STATIC` | The public source-only helper parses the embedded LicenseGroup envelope, reconciles counts and identifies a unique MSDK-compatible field-7 RID candidate while keeping its ID out of logs; five synthetic cases and the source build pass | No real success callback, RC 2 loader, genuine item, setter, restore or RF effect is established |
| C-192 | `STATIC` | The public `lmdegreeds/djiparam` editor recovers a by-index FLYC family (`0xE0` table, `0xE1` get_info, `0xE2` read, `0xE3` write) and a wa150 Mini 5 Pro table whose RID rows are `EU_CE_enable_c0_rid` (index 1306), `EU_CE_Reg_RID_Enable` (1308), and `eu_ce_support_remote_set_level` (1315) | Community prior art for a third parameter path beside by-hash F7/F8/F9; EU C0 policy candidates, not a global RID master switch; no live by-index result here |
| C-193 | `STATIC` | An independently written offline codec implements the `0xE0`/`0xE1`/`0xE2`/`0xE3` commands with strict table/index/name/width validation and a gated `0xE3` encoder; a read-only USB probe verifies table CRC/count then re-checks each RID index name before `0xE2`, and never reaches `0xE3` | Synthetic tests do not establish Mini 5 Pro acceptance, parameter application, or RF behaviour; no live read/write result is claimed |

Details: [20_OFFICIAL_FLYSAFE_UI_PATH.md](20_OFFICIAL_FLYSAFE_UI_PATH.md),
[11_ARTIFACT_REGISTER.md](11_ARTIFACT_REGISTER.md),
[RC 2 RID Admin source](../apps/rc2-rid-admin/README.md), and the
[same-process query experiment](../experiments/jvmti/jvmti_flysafe_inprocess_query/README.md).

## Promotion rules

A claim changes status only when new evidence directly satisfies the missing boundary. Examples:

- `STATIC -> OBSERVED`: exact live subject/version and route execute with strict result matching.
- `HYPOTHESIS -> OBSERVED/NEGATIVE`: a predeclared discriminating experiment runs once and records
  positive controls and final state.
- `UNKNOWN -> STATIC`: exact current implementation evidence answers the question without a live
  action.
- `NEGATIVE -> RETRACTED`: later evidence shows the original test premise or interpretation was
  invalid; the original row remains in history.
