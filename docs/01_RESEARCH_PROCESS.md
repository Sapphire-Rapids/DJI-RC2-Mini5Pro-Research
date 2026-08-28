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

Static analysis of the exact adjacent unstripped `adbd` found a DJI production check in the CNXN
branch before normal authentication. No `AUTH` key packet, `OPEN`, shell, install, reboot, fastboot,
root, or bootloader operation was sent during the handshake work.

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
