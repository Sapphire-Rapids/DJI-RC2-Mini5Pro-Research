# Evidence register

The canonical machine-readable rows are in [`evidence/claims.csv`](../evidence/claims.csv). This
document groups the same claim IDs for human review. Topic documents contain the detailed evidence
chain.

## Subject and version identity

| ID | Status | Claim | Boundary |
| --- | --- | --- | --- |
| C-001 | `OBSERVED` | RC 2 UI displayed `07.00.0100` | Exact complete signed live package set was not obtained |
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
| C-132 | `STATIC` | Runtime function ID `0x6C` conditionally admits `UOMV1`, whose sync action is account/network state and has no setter | Exact Mini 5 Pro admission and external helper route are unknown; no reversible configuration semantics |
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
| C-032 | `INFERENCE` | Adjacent production gate currently explains live silence | Requires live binary/package identity for exact proof |
| C-033 | `HYPOTHESIS` | First-packet AUTH public-key branch may reach confirmation | State-changing, unexecuted, not a result |

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
| C-047 | `NEGATIVE` | Exact complete v07 package set not found in audited local locations | Adjacent evidence remains adjacent |
| C-048 | `CORROBORATED` | ACK is not state readback; readback is not persistence | Record evidence stage separately |
| C-049 | `CORROBORATED` | Onboard normal is not independent RF reception | External receiver/analyzer required |
| C-050 | `CORROBORATED` | Generated key name is not live handler evidence | Exact handler/route required |
| C-051 | `STATIC` | Repository is documentation/index only | No control/patch/root/transmitter/account product |
| C-052 | `CORROBORATED` | Complete state-change evidence needs baseline, forward readback, restore, final readback, and unmeasured-effects statement | Motor-on RF remains independently observed |
| C-053 | `UNKNOWN` | Stable recoverable Mini 5 Pro RID control remains unproven | Static paths, ACKs, UI, and onboard state are insufficient |
| C-054 | `STATIC` | Artifact hash may be public identity metadata | Hash does not permit redistribution |
| C-055 | `UNKNOWN` | No new independent V2.3 post-fix audit conclusion exists | V2.3 remains `NOT ADMITTED` |
| C-129 | `HYPOTHESIS` | A separate external OpenDroneID source could provide synthetic configurable standards fields | No RF backend/hardware/readback/stop/reception evidence is implemented or admitted |

## Promotion rules

A claim changes status only when new evidence directly satisfies the missing boundary. Examples:

- `STATIC -> OBSERVED`: exact live subject/version and route execute with strict result matching.
- `HYPOTHESIS -> OBSERVED/NEGATIVE`: a predeclared discriminating experiment runs once and records
  positive controls and final state.
- `UNKNOWN -> STATIC`: exact current implementation evidence answers the question without a live
  action.
- `NEGATIVE -> RETRACTED`: later evidence shows the original test premise or interpretation was
  invalid; the original row remains in history.
