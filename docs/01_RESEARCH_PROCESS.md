# Research process

This file records performed work and its evidence boundary. It does not describe subjective intent.

## 1. Hardware enumeration and route separation

`OBSERVED` macOS USB enumeration showed two independently addressable DJI devices:

- aircraft: VID/PID `2ca3:0020`;
- RC 2: VID/PID `2ca3:1021`.

USB strings, device serials, port paths, and storage identifiers were excluded from the public
record. Device visibility established physical presence only; it did not establish DJI MSDK product
support or a safe command session.

The aircraft exposed network, mass-storage, and vendor bulk interfaces. RC 2 exposed vendor bulk,
MTP/PTP, and an ADB-shaped interface. Fixed readers treated aircraft and controller as separate
routes and validated replies by frame length, CRC, reverse source/destination, sequence, command
set/ID, and command-specific application payload.

## 2. Passive traffic and fixed read-only probes

Bounded passive windows were used before active queries. Aggregate frame counts and command IDs
were retained; private payloads were not published.

Observed route facts included:

- traffic consistent with the RC bridge and aircraft flight-controller paths;
- matching UUID/application-state replies on two fixed paths;
- known height/distance parameter reads as positive controls;
- Sky/Ground SDR fixed-address reads;
- FC area and Sky/Ground country GETs;
- bounded observation for RID working-status and FlySafe support/version pushes.

Queries were allow-listed. A missing reply did not trigger receiver scanning, adjacent-command
probing, automatic retry, or a generic raw-command fallback.

## 3. Account, flight-limit, and RID status mapping

Static work separated account state into three layers:

1. cached application session/token material;
2. server acceptance of the current credential;
3. account UID synchronized to the flight system.

Only privacy-minimized Boolean/status observations were retained. No UUID text, token, cookie,
account name, or private response body is published.

Flight-limit work compared configured values with public/runtime status surfaces. Fixed GETs showed
configured height 500 m, radius 5000 m, and radius-limit disabled. These are configuration facts;
they do not resolve whether a separate login-dependent 30/50 m effective layer was active.

RID status work recovered the seven-byte `0x11/0x1C` layout and compared it with public MSDK state
models. A bounded motors-off observation did not contain a strict candidate. That negative was kept
separate from the operator's later observation that actual receiver-visible RID begins after motor
start.

## 4. Region and RF-policy separation

Static and public evidence separated:

- application area strategy;
- FC area code;
- Sky country;
- Ground country;
- RC/DJI Fly policy state;
- legacy Sky SDR assistant selector;
- Android Wi-Fi regulatory state;
- actual O4 channel/EIRP behavior.

These surfaces were not treated as aliases. Fixed GETs established a redacted state snapshot.
After explicit per-surface authorization, one-shot FC and Sky `CN -> US -> CN` state loops were
performed with preconditions, matching ACKs where applicable, fresh readback, restoration, and
final readback. One Ground US request had no strictly matching ACK; the fresh GET remained CN, so no
retry or restore write was sent.

The independent RID receiver was offline during those region transactions. No claim about Remote
ID, available channels, regulatory mode, or RF power was derived from country readback.

## 5. DJI Fly and MSDK static analysis

Current DJI Fly 1.21.10 and MSDK 5.18.0 materials were searched by semantic key, generated mapping,
native registration, request construction, response conversion, and runtime transport ownership.
Older public source snapshots were used as corroboration, not as automatic current-product facts.

The analysis distinguished:

- `RidWorkingStatusPush`;
- France `EIDSwitch`;
- EASA `OperatorRegistrationNumber`;
- Japan DIPS/shared-key import and deletion semantics;
- FlySafe type-6 `RID_UNLOCK`;
- EU C0 cloud/area/CE-class policy;
- broadcast-effect/cloud-control data;
- public UAS area-strategy delegates;
- generated key declarations with no current product-139 native handler.

Address-level native analysis corrected an earlier request-layout error: retry is at
`uav_cmd_req+0x08`, receiver index at `+0x19`, and the product-139 request constructor initializes
retry to 3. The typed GET conditionally clears retry based on live Characteristics state; typed SET
retains 3.

## 6. FlySafe license-chain analysis

The static chain was followed from account-authenticated license-group retrieval through FC serial
filtering, support/version gates, V2/V3/V4 query schemas, protobuf/status parsing, upload, and
set-enable mappings. The record distinguishes:

- schema support for type 6 and EU/China levels;
- public application eligibility;
- actual account inventory;
- live FC support/version;
- current-session route;
- enable-state readback;
- onboard working status;
- independent RF behavior.

A legacy fixed inventory query timed out on both artificial routes while immediate area/country
positive controls succeeded. The result was recorded as route/session/schema unresolved, not empty
inventory.

## 7. Assistant 2 and firmware inventory

Assistant 2 work was divided into three classes:

1. metadata inspection;
2. bounded download of named signed packages to a private work area;
3. upgrade/loader paths inspected statically but not invoked.

RC331 `0205` was verified and extracted without force, producing a 29-partition Android platform
inventory. RC331 `0200` passed its outer verification boundary but the protected inner FLYA layer
could not be verified/decrypted with the available public key corpus.

WA150 package/module comparison identified:

- `0802` as the primary main-system candidate;
- `2603` as GNSS;
- protected `0806/DONG` as a communication-related secondary candidate.

The exact RID-owning process/library inside WA150 remained unknown.

## 8. Non-flashable integrity and differential checks

A temporary one-byte ciphertext mutation was created only to observe package integrity fields.
Outer MD5/digest/encrypted-checksum changes could be measured or recomputed, but the correct
modified plaintext checksum was unavailable and the signed message changed while retaining the old
signature. The output was not copied to a device or flashed.

Retained WA150 ciphertext samples were compared for aligned equality and XOR structure. Distinct
wrapped scramble values, no equal aligned 16/32-byte blocks, and random-like XOR statistics did not
support the tested keystream-reuse route. This is a bounded negative, not a complete cryptographic
characterization.

## 9. Public prior-art review

Pinned public repositories were checked for exact call paths, payload ownership, product support,
readback, restoration, and RF verification. Findings from N3Live, DJI-Link, dji-firmware-tools,
FreeFCC/SkylabFCCfree, dji-adb, ya-webadb, MSDK samples, and RC 2 community work were recorded with
their narrow scope.

The search did not find a public Mini 5 Pro + RC 2 implementation that simultaneously demonstrated
baseline GET, canonical ACK/readback, exact restoration, and motor-on independent RID reception.
That statement is limited to the reviewed sources and revisions.

## 10. RC 2 MTP, sideloading, and hidden Settings

Standard MTP/PTP was queried with read-only operations. It exposed a directory skeleton but no
files, exact DJI Fly package, private application directory, or matching native library. Assistant's
RC 2 exporter had implemented data-file functions but log-list/export-all-log stubs; the uncalled
data-export mode contained state transitions and was not treated as a pure read.

A separately prepared removable card allowed user-driven installation of signed PackageInstaller
and FileManager helpers plus an earlier observer APK. A small launcher invoked fixed Android
Settings actions. Device information became visible, and seven taps on Build number opened the real
Developer options dashboard. No Reset or OEM-unlock action was used.

## 11. Localhost observer retraction

Historical observer v0.1-v0.4 connected to RC-local `40007`/`40009` without sending. Later static
evidence from adjacent RC331 `0205` showed both server paths default to one active accepted fd; a
new client may close and replace DJI Fly's existing fd even if the newcomer sends no payload.

The input-only safety premise was therefore retracted. Those versions are offline decoder history
only. The current v0.10 admission probe uses no socket, DUML, application Binder transaction,
process execution, persistence, network send, native library, or attach/load path.

## 12. ADB handshake isolation

The host ADB server was stopped before each custom interface claim. Tests covered stock ADB, a
pinned Dr-Muh pre-authentication profile, and one-variable changes to protocol version, MAXDATA,
banner, and legacy checksum. Split header/payload writes transmitted `CNXN`; no ADB packet returned
before timeout. Combined transfer framing failed at the I/O path and was discarded as a lead.

Later provenance work obtained the target `07.00.0100` signed system chain and independently
verified its signed config/`0205` module. The exact target APEX `adbd` is byte-identical to the
earlier sample, promoting the production/debug-count CNXN return from adjacent explanation to exact
target-package `STATIC`. Its live boot properties and mounted-file hash remain unobserved.

A semantic offline patcher then changed only the exact gate-value instruction while preserving the
normal TLS/auth branch. The derivative output was staged to removable SD through MTP and a fresh
full-file readback hash matched. It was not copied to internal storage, chmodded, or executed; no
daemon was stopped and no new ADB packet/shell resulted. The next operator session begins with
read-only UID/SELinux/property/hash/path-label evidence before any internal path is selected.

No `AUTH` key packet, `OPEN`, shell, install, reboot, fastboot, root, bootloader, boot-image, APEX or
partition modification was sent during the recorded handshake/staging work.

## 13. Same-owner runtime-route research

After the localhost path was retracted, static work focused on the already initialized DJI Fly
owner:

1. semantic Java anchors for `electronicIDBroadcastOn` and `electronicIDBroadcastExisted`;
2. exact product-139 `EIDSwitch` characteristics and request/ACK conversion;
3. a raw ACK boundary before Boolean conversion;
4. `JNIRawData.native_SendData` as a narrower same-owner raw-response candidate;
5. runtime tuple sources for productId, deviceId, senderIndex, HostID, receiver, selector, timeout,
   and retry;
6. loader/symbol identity, target static-libc++ exception behavior, route mutation, callback
   lifetime, pending/Stopper presence, and mapping retention.

The route became more precise, but a live request was never admitted. Static tuple recovery did not
close execution safety or current-device identity.

## 14. Offline artifact iterations

- V0: no-op JVMTI reachability canary.
- V1: already-loaded semantic-anchor topology resolver.
- V2: raw-GET carrier with permanently unresolved route gates.
- V2.1: route-only resolver with immutable-zero exception gate.
- V2.2: whole-file identity revision rejected after independent review found early runtime-header
  trust, writable-map acceptance, and missing zero-device rejection.
- V2.3: distinct corrected route-only artifact; still fixed-zero-gated and zero-send.
- Android probe v0.10: zero-permission environment/ART admission probe with an artifact-specific
  independent audit.
- Host quiescence model 0.1.1: synthetic state-machine verifier only.

None of these artifacts produced a live RID read or write in the recorded work.

## 15. NLD FCC Smart RC comparison

The supplied Smart RC ZIP was treated as untrusted input. Archive structure, manifest, APK
signatures, hashes, permissions, components, DEX/resources, both native ABIs, and public NLD pages
were inspected without installing or executing the apps or contacting their API.

The main paths were traced separately:

- normal FCC from subscription selection through opaque online/native-offline payload decode and
  native DUSS send;
- C0 from version gate through locally generated client key, server-controlled WireGuard routes,
  DJI Fly lifecycle, and the conditional 25-second automatic-stop schedule;
- subscription identity and offline cache binding;
- parameter schema discovery, typed write, and post-write verification;
- bounded Remote ID term/control search.

All seven packaged JSON profiles were hashed and compared with pinned FreeFCC. Exact equality was
recorded, followed by a separate DEX/native reachability audit. Because no loader/reference was
found, the files were not described as the active NLD command source. The opaque runtime payload was
not requested, decoded, replayed, or copied into this repository.

The detailed results and reusable-design review are in
[16_NLDFCC_STATIC_ANALYSIS.md](16_NLDFCC_STATIC_ANALYSIS.md).

A follow-up control-flow pass closed the native envelope, online/offline key-selection distinction,
RSA-bound entitlement checks, durable cache framing, decrypted JSON schema, and DUML frame/write
loop. Earlier provisional readings of a hex envelope, lowercase serial normalization, or an empty
online HMAC key were rejected. No embedded symmetric key value, licensed cache, response payload,
or command plaintext was admitted to the repository.

## 16. Drone-Hacks Windows comparison

The supplied `2.0.29` MSI was first matched byte-for-byte against the MSI in the official release
ZIP. MSI and PE Authenticode signatures, package metadata, embedded-file hashes, and release
metadata were then recorded before inspecting functionality. The installer and both payloads were
kept offline and never executed.

Static strings, Rust/Tauri type metadata, command schemas, endpoint names, model tables, and public
anonymous compatibility APIs were analyzed as separate evidence classes. The client-side executor
was distinguished from server-owned modification/job payloads. The FCC quick action, generic
parameter editor, firmware/CFC path, and Remote ID search were also kept separate so a generic DUML
name or an FCC feature could not be promoted into a RID implementation.

The current public model, license, product, platform, and FCC ModBox views were queried with no
account or device identifier. Positive controls were used where possible: a known Mini 3 Pro model
returned a software product while `wa150` did not. No authenticated API, license, private job, or
device action was used.

Detailed methods, exact identities, results, and design implications are in
[17_DRONE_HACKS_STATIC_ANALYSIS.md](17_DRONE_HACKS_STATIC_ANALYSIS.md).

## 17. Current RID-setter and China OID gate re-audit

The exact registered JNI surface in DJI Fly `1.21.10` was re-enumerated for RID/EID/OID broadcast,
open/close, simulator, report, cloud-reset, and OpenDroneID/ODID terms. Every Boolean was followed to
its consumer rather than classified by name. This identified a real OID report-enable gate but
showed that its false branch bypasses network submission through a direct-success result.

The gate was then separated from the opaque RID cloud-control V2 namespace, France EID wrappers,
MSDK status-object setters, and firmware-only unknowns. Adjacent Java code was used only to
corroborate the China cloud namespace and default policy; it was not described as exact 1.21.10
Java. No code was executed and no network/device state changed.

## 18. Legacy DroneID command correspondence

The NDSS 2023 paper, pinned author repositories, DJI-derived midware, current app enum bytes, and
community command ancestry were compared without sending a packet. The paper's undisclosed
multi-field control was treated as an inference target rather than assumed equal to the nearest
command name.

The analysis independently reconstructed FlyC `Detection` `0x03/0xDA` subcommands `0x05`/`0x06`
and its eight-field mask, then retained two decisive boundaries: the paper did not publish this
tuple or identify the exact switch-test model/firmware, and its RF experiment kept packets while
substituting selected values with `fake`. Proprietary OcuSync/AeroScope DroneID was kept separate
from ASTM/FAA/EU Broadcast RID. Details are in
[18_LEGACY_DRONEID_DETECTION.md](18_LEGACY_DRONEID_DETECTION.md).

## 19. RID configuration-surface inventory

The target was expanded beyond one master switch. Exact product-139 registration, access types,
wire templates, parser behavior, caller context, credential sensitivity, readback, restore,
persistence, and RF evidence were inventoried independently for working status, OPID, Japan DIPS,
China UOM, app location, compliance serial, France EID, C0, type-6, and cloud-control surfaces.

Each row was assigned an implementation level rather than converted directly into a UI control.
LTE telephone upload, China app/cloud reporting, legacy masks, and set-only blobs were explicitly
excluded from modern Broadcast RID editing. A separate synthetic OpenDroneID source was recorded as
an architecture hypothesis for fields a DJI aircraft cannot expose safely. The normalized result is
[19_RID_EXPERIMENT_CONTROL_MATRIX.md](19_RID_EXPERIMENT_CONTROL_MATRIX.md).

## 20. China UOM exact route, parser, and admission pass

The exact `OIDIdentifier` registration block, typed constructor, GET/SET wrappers, reply lambdas,
`UOMV1` registration, direct status getter, runtime function-discovery callback, and recovered Sync
response handlers were followed in the same DJI Fly `1.21.10` native input. Address/name evidence
was used locally; no vendor disassembly was copied into the repository.

This pass corrected an earlier assumption that all 18 GET-request bytes were zero-initialized: only
the `[01,02]` prefix is visibly written. It separately closed the result/value reply offsets and the
conditional function ID `0x6C` admission of `UOMV1`. A follow-up exact pass then closed the helper at
the high-level trust boundary: Sync and cancellation both depend on China-only server validation
before a server-derived result is synchronized through the D1 aircraft lane. Endpoint details,
account material, opaque response content, live acceptance, and applied RF effect remain excluded or
unknown. No GET, Sync/cancel action, network request, or device operation was executed.

## 21. Dynamic RID bundle and AirSense-candidate separation

The exact `RidCaptureV1::CreateCharacteristics`, `BindKey`, full `CommonFcAbs` function-discovery
callback switch, general discovery request type, and current AirSense registrations/callers were
cross-checked in DJI Fly 1.21.10. The resulting inventory was normalized by access class rather than
by name: four listen-only capabilities, one Japan action, one result getter, two GET+SET identity
surfaces, and one SET-only location stream.

The full callback switch corrected a preliminary off-by-one interpretation: raw function ID `0x37`
creates `RidCaptureV1`, while `0x38` creates unofficial-battery authentication. The general
function-discovery transport `0x00/0xB8`, the AirSense command `0x11/0x37`, and FlySafe
`PackType 0x38` were treated as separate namespaces. Current `0x11/0x0C`, `0x11/0x37`, and
`0x11/0x39` paths were then positively identified as AirSense/ADSB surfaces and excluded from RID
configuration attribution.

Only independently written names, access classes, owners, and boundaries enter the public archive.
No vendor decompilation was copied; no function-discovery, AirSense, D1, account-server, or device
request was executed.

## 22. Current same-family `RIDCtrlEnable` recovery and implementation

The official current SKYROVER Android distribution was downloaded from its direct vendor URL,
hashed, and analyzed offline. High-level model registration, characteristic flags, connection-time
visibility logic, and the native key/config mapping were followed independently. The complete chain
closed as Boolean GET/SET/Listen `RIDCtrlEnable`, distinct from France `EIDSwitch`, mapped to FC
parameter `rid_ctrl_enable_0` and FLYC F7/F8/F9. The parameter hash was independently recomputed as
`0x3CBD864F` using the already corroborated DJI hash algorithm.

An allow-listed clean-room Android client was then implemented on the already recovered RC 2
`protocol` Binder ABI. The fixed path uses modern sender/receiver `0x82 -> 0x92`, F7 metadata and F8
value reads, F7-derived value encoding, F9 write, immediate F8 readback, and a captured per-session
baseline for restore. Offline tests exercised success, status errors, identity mismatch, width/type
mismatch, both F8 layouts, Boolean rejection, and write encoding. The final artifact was checked at
manifest, permission, signature, alignment, DEX, command constant, and clean-build levels before it
was copied to RC 2 removable storage.

This process did not copy vendor implementation code or distribute vendor artifacts. Static
same-family support was kept separate from Mini 5 Pro support: the next evidence is one live fixed
F7/F8 result from the exact client, not another broad symbol search or a France-EID substitution.

A subsequent direct read-only pass added the fixed hash to the previously positive-controlled USB
probe and kept F9/FA unreachable. RC 2 routed and aircraft-direct legacy endpoints both returned
one-byte F7 status `03`; immediately adjacent known height/distance controls returned valid F7/F8.
The static modern `0x82 -> 0x92` tuple was then tested directly on USB, but a known maximum-height
control also timed out. This separated a real direct-route parameter retrieval failure from an
unusable raw-USB modern route and, at that stage, reduced the remaining live test to the RC 2
Binder client. Section 23 records the later Binder result.

## 23. Live Binder result and positive-control/passive-timeline revision

The exact A-023 client was installed and its fixed read-only RID target probe was run. The result
was transcribed without publishing PID, UID, device identity, or raw packet content. The intended
process-label compatibility path resolved a live `com.dji.protocol.IProtocolManager` Binder;
manager transaction 1, callback transaction 4, and both exception layers completed. The target
`03/F7` for hash `0x3CBD864F` then ended with callback `ECode 1` after about 3.1 seconds and produced
no F7 ACK. No F8, F9, reset, or other mutation followed.

Adjacent RC331 `ActQueue` was checked to interpret only the callback class: that implementation
emits `ECode 1` after retries are exhausted. Because A-023 did not first exercise a known parameter
over the same Binder route, the observation was recorded as a transport/protocol timeout rather
than parameter absence.

A-024 `0.4.1-research` was then built as the replacement. It serializes operations and probes known
maximum height with F7/F8 on each candidate route before sending the target F7. Target F9 remains
locked until exact metadata identity, read/write attribute, width, range, and a Boolean F8 baseline
are all established. Any admitted write uses repeated readback and a captured pre-operation value
for rollback/restore.

Separately, the exact adjacent Binder listener ABI was implemented for a local-only transaction-2
filter on `0x11/0x1C`. One process-lifetime listener records the full 30-second window, folds only
adjacent identical semantic states on the same actual route, preserves A-B-A transitions and
malformed/failure events, synchronously persists a bounded result, and then terminates the APK
process so Binder death performs deterministic cleanup. This workaround follows the adjacent
RC331 removal implementation, which compares cross-process wrapper identity and may acknowledge a
transaction-5 removal without deleting the listener.

Twenty-five unit tests, lint with zero errors, two byte-identical clean builds, manifest,
permission, signer, alignment, and native-library checks passed. The final 92,569-byte artifact
with SHA-256 `68f9b0d42d42e1bcb674ddba88a3996229d06978e35e30a355f253678a8e2b95`
was copied to RC 2 removable storage. Installation and the dual-route known-height positive-control
experiment subsequently completed: both routes returned `ECode 1`, so target requests stayed gated
off. The listener then completed its full 30-second window after a 9 ms registration acceptance but
received no callback. The operator started the motors and an independent detector confirmed actual
RID RF in the same experiment. The tested Binder listener was therefore classified as a false
negative and removed from the active readback plan; the RF observation was not reinterpreted through
the empty callback set. No device write occurred.

## 24. FlySafe type-6 control-semantics and modern inventory path

The official MSDK 5.18 retained consumer was followed from `LicenseDataRID.level` through
`FlySafeHelper` and `FlyZoneManager` into `DefaultUASDelegate`. The retained body requires type 6,
enabled state, and level/area match; when the product gate is true it emits
`broadcastRemoteIdEnabled=false` and `NO_BROADCAST`. The same branch contains no Key write, native
call, or DUML send, so it was recorded as app-side design/status evidence rather than physical RF
control. If physical suppression exists, the aircraft must consume the signed license state changed
by FlySafe `SetEnable`.

Current DJI Fly and MSDK native implementations were then cross-compared: inventory and set-enable
are `0x11/0x11` and `0x11/0x12`; product 139 resolves to receiver `0x92`; V3/V4 begin with `[00,01]`
and return group/status-plus-protobuf records. Exact follow-up separated their schemas: current Fly
typed `LicenseData` parsing stops at fields 1--5 and sends field 7 to `UnknownFieldSet`, whereas the
independent MSDK artifact typed-decodes field 7 as `LicenseDataRID`. A strict offline compatibility
parser distinguishes domain type 6 from MSDK protobuf oneof field 7, caps
page/count/field/length/varint behavior, and does not expose raw IDs or identity fields.

A-025 was then scoped to a single read-only modern inventory function through the already used
system Binder. Its FlySafe lane allows `0x11/0x11` only, starts with the V3/V4 group query, bounds
page selection below wrap, and reports only aggregate type-6 level/enabled/valid state.
`0x11/0x12` is not admitted in this stage. Only a canonical genuine type-6 result can admit the later
baseline-transition-readback-restore experiment and motor-on independent RF A-B-A.

## 25. Passive-gate result and direct read-only successor

A-026 added one bounded passive `03/09 + 03/42` gate before the A-025 inventory lane. Its first live
60,003 ms run delivered no callback of any class, left both inputs unobserved, and correctly sent no
`11/11`. That result closed the third-party passive listener as the next discriminator without
reinterpreting it as aircraft non-support or empty inventory.

A-027 therefore isolates the active read-only question. It uses one non-reusable permit for one
fixed system-Binder transaction-4 `02:04 -> 12:04`, `11/11` V3/V4 group/page traversal. It does not
scan routes and adds no application-level retry. A result is promoted to inventory only after the
existing count/page/terminator/schema checks complete canonically; timeout, callback failure, or
noncanonical data remains ambiguous. Public MSDK/Cloud API and pinned `fpv_live`/
`dji-firmware-tools` evidence corroborate generic families only, not this product-139/RC331 fixed
route, which comes from local exact static analysis and remains a live candidate.

The exact versionCode-10 `0.7.0-flysafe-direct-readonly` APK passed 127 tests, lint with zero errors
and 15 warnings, two byte-identical clean builds, v2-signature/zipalign checks, zero-permission
inspection, and no-native/network/socket/shell/external-process inspection. Its registered size is
196,569 bytes and SHA-256 is
`aa4bcd9c8aa96870cfbae1ba326d366cb8854a50ef4aff223f7bce4290ddcd81`. It was staged through MTP
as removable-SD `Download/FindUAS_A027_RO.apk`; a fresh listing matched the size and readback SHA
matched. The operator then installed it and ran the active button. The result was
`DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`, stage `ProtocolException`, with displayed
`11/12 request count=0`. Because the UI omitted the exception message, this run did not separate
callback, ccode, group, page, or terminator failure. The result image was not retained in this
repository and no identifier or license material was recorded.

A-028 was then built as a diagnostic-only successor. It preserves A-027's protocol command, fixed
route, selectors, and no-write boundary; only UI classification changed. `ProtocolException` now
uses a static safe message, unexpected group/page ccode reports its numeric value and page index,
and terminator mismatch reports data length. The versionCode-11
`0.7.1-flysafe-direct-diagnostic` APK is 197,061 bytes with SHA-256
`d7c32636e19d1bce1b8b8994206355f42d0278b2f15048b14a948a8bbda1d540`. Its 127 tests,
lint 0 errors/15 warnings, two byte-identical clean builds, v2 signature, zipalign, zero permissions,
and no-packaged-native check passed. MTP staging as `Download/FindUAS_A028_DIAG.apk` passed fresh
size and readback-SHA checks. The operator then installed and ran it. The result remained
`DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS` / `ProtocolException`, but the new classifier showed
`group transport callback failed`; `11/12 count=0`. The fixed `11/11` group selector therefore had
no successful transport callback, and the run did not reach group protobuf, page, or terminator.
The next useful read-only change is to display the existing Reply failure/ecode/callback diagnostic,
not to repeat the identical black-box request.
