# RID experiment control matrix

## 1. Purpose

The real-aircraft research target includes a stable Mini 5 Pro Broadcast Remote ID enable/disable
control, Basic/UAS ID, aircraft position and operator position. Operator ID is tracked separately
from both Basic/UAS ID and operator position. This document records existing evidence and the gates
for each requested control; expanding the target does not establish that a device setter exists.

For every switch or field independently, “adjustable” requires all
of the following on the exact subject/version: authoritative owner,
baseline getter, bounded setter/action, canonical ACK, independent readback, restoration, persistence
classification, and motor-on RF A-B-A evidence. A UI control is not evidence that a device accepted
or applied a value.

Synthetic OpenDroneID encode/decode and fixture work remains offline. It cannot replace a
real-aircraft owner, admit a field editor or supply aircraft RF evidence; adding a transmitter
backend is outside the current implementation scope.

New machine-index claims covered here are C-123 (China UOM), C-124 (EASA OPID), C-125 (Japan DIPS),
C-126 (app location), C-127 (telephone exclusion), C-128 (compliance identity), and C-129 (separate
synthetic-source hypothesis). The exact China UOM reply/status closure adds C-130 through C-132.
Dynamic bundle separation adds C-133 through C-135. The independent same-family `RIDCtrlEnable`
chain, Mini 5 Pro admission experiment, full current inventory, and public-prior-art boundary add
C-136 through C-140. A-025's bounded modern FlySafe inventory lane and final-artifact audit add
C-150/C-151; the exact current-Fly field-7 and aircraft-consumer boundaries add C-152/C-153;
A-026's gated implementation/audit/delivery add C-160--C-162; user-reported installation adds C-164,
and its first live gate-unobserved/zero-query result adds C-165. A-027's fixed active read-only lane,
artifact audit, delivery, and first ambiguous live result add C-166--C-169. A-028's diagnostic-only
successor, delivery, and group-transport live result add C-170--C-173.
The exact official UI surface and A-033 diagnostic-export audit/delivery add C-180--C-182.
The privacy-reduced C-207 observation form adds a fixed recording procedure without adding a
machine-index claim until a live A-B-A result exists.
C-227--C-230 add the successful direct-USB FLYC positive control, the two absent target parameters
on `01.00.0600`, and the live EU C0 block's index shift. They do not close any RF control gate.

## 2. Implementation levels

| Level | Meaning | UI rule |
| --- | --- | --- |
| `READ-ONLY LIVE` | Current app/bridge has a bounded read path and preserves `unavailable` | Show current value and capture time; no editor |
| `PASSIVE OWNER` | Exact official owner listens for natural state, but no active GET exists | Show only when obtained without replacing the owner or opening a second broker client |
| `STATIC LOCKED` | Exact getter/setter/schema exists, but live route, baseline, restore, or RF gate is open | Disabled card with the missing gate; never a working-looking toggle |
| `MANAGED` | Server/FC-bound state that must be observed through its official owner | Read through the admitted owner when available; use the separate aircraft-policy lane when it is readback-closed |
| `OPAQUE BLOCKED` | Set-only blob, unknown semantics, absent readback, or name-only command | Do not expose raw editor/replay |
| `LEGACY EXCLUDED` | Proven different protocol/product generation | Search signature only; do not migrate into a sender |
| `SYNTHETIC SOURCE` | Offline standard-message codec and synthetic fixtures | No RF/USB/device-control path; no real identifiers or coordinates; never present codec output as aircraft evidence |

Each implementation row in sections 3.1--3.3 has one primary level from this table. Credential,
privacy, account and non-atomicity restrictions are additional boundaries rather than a second
level; section 3.0 separately lists the requested fields and identity distinctions.

## 3. Current Mini 5 Pro / DJI Fly control surfaces

### 3.0 Requested field boundaries

| Control or separate identity plane | RF field to establish | Current evidence / missing owner link |
| --- | --- | --- |
| RID switch | Independent standard-RID message presence through a controlled transition and restore | No admitted switch; the two FLYC candidates are absent on the tested `01.00.0600` surface (C-227--C-230) |
| Basic/UAS ID | Identity carried in Basic ID | Compliance serial derivation is a static candidate only; live owner, RF correspondence and reversible setter are unclosed (C-128) |
| Aircraft position | Aircraft position in Location/Vector | Exact current source/consumer and any bounded reversible control are unclosed; operator/app position is not a substitute |
| Operator position | Operator-location fields in System | App-location delivery is static evidence, not proof of the RF field's authoritative owner or a reversible control (C-126) |
| Operator ID, separate identity plane | Operator ID message where applicable | EASA OPID and other region-specific identities remain separate; no universal mapping or admitted editor follows from those schemas (C-123--C-125) |

Record field presence and privacy-reduced equality/change/restoration results, never full IDs or
coordinates in public evidence. Natural GNSS/location updates and cloud/account writers must be
distinguished from an experiment's controlled variable. All requested field writes remain locked
until that field's owner, baseline, readback, restore and independent RF correspondence are closed.

### 3.1 State, diagnostics, timing, and identity

| Surface | Owner and path | Read | Write | Current disposition |
| --- | --- | --- | --- | --- |
| Global Broadcast RID master | same-family SDK `RIDCtrlEnable -> rid_ctrl_enable_0`; authoritative WA150 broadcaster control unclosed | `rid_ctrl_enable_0` is absent on the positive-controlled `01.00.0600` direct-USB FLYC surface, with no matching name in the reported enumeration (C-227/C-230); Binder controls previously failed | no admitted write | `STATIC LOCKED`; do not repeat the same target/route; reopen only with materially new owner, handler or version evidence |
| RID/EID working status | product-139 `RidImportModule`, natural `0x11/0x1C` push | support/normal flags, area, failure | none | `PASSIVE OWNER`; no GET builder and onboard normal is not RF truth |
| Regional capability | product-139 interpretation of the same push | US bit 0, Cloud bit 10, EU/Japan/France bits 11/12/13 in explicit mode | none | `PASSIVE OWNER`; show capability separately from real area and RF standard |
| RID health/diagnostics | FC health manager plus Remote ID delegate | working/idle/location/firmware/no-broadcast/unsupported/unknown | none | `PASSIVE OWNER`; preserve the raw failure class without coordinates |
| Broadcast start/stop timing | aircraft firmware plus independent receiver | A-024 Binder listener was false-negative while the independent detector confirmed real motor-on RID | no safe trigger | `READ-ONLY LIVE`; use the independent receiver for RF truth and do not repeat the tested Binder listener |
| Operator-location health | RC/Android location provider -> link -> aircraft | permission, age, accuracy, RID failure class | no admitted selector or coordinate setter | `PASSIVE OWNER`; current health observation is separate from the requested, still-locked operator-position control |
| Aircraft/UAS identity | FC/device identity and compliance derivation | static get/listen-only candidate; no admitted live read | no current setter found | `STATIC LOCKED`; live route, privacy-safe read, and actual RF Basic ID correspondence remain unclosed |
| RF bearer | aircraft BLE/Wi-Fi scheduler | external receiver observation; the operator confirmed with a verified standard Remote ID detector plus the FindUAS host that the Mini 5 Pro broadcasts plaintext standardized Remote ID with a readable Basic ID (C-207). The standardized Bluetooth/Wi-Fi Remote ID is a plaintext protocol per EN 4709 / ASTM F3411 (C-203, C-206); the DJI-private OcuSync DroneID encrypted-O4 boundary (C-202) is parked and out of scope for the current switch work | no selector found | `READ-ONLY LIVE`; use the standard Remote ID receiver for RF truth, show only an independently observed bearer, never infer it from China cloud tracking masks |

The seven-byte working-status layout is:

- bit 0 RID support, bit 1 EID support;
- bit 8 RID normal, bit 9 EID normal;
- bytes 2--5 signed little-endian area code;
- byte 6 failure value.

The current handler does not enforce a local length check, so every independent parser must require
at least seven bytes before reading fields.

Current `ComplianceSerialNumber` observes ordinary serial state and, for a 14-character input,
derives a 20-character `1581F + serial + 0` compliance form; otherwise it preserves the input. This
is a strong Basic-ID candidate shape, but there is no setter and no static proof that WA150 RF uses
the derived value. Full serials must never enter public logs.

The exact app-location lane sends validated/quantized client location about every 500 ms through
encrypted `0x11/0x43` `app_update_pos_enc`. It proves app-to-device delivery, not final Broadcast
RID use. Conversely, the current set-only LTE phone command belongs to LTE HYBRID business logic,
has no getter/readback, and is explicitly excluded from the RID configuration catalog.

### 3.2 Region-specific identity and policy

| Surface | Exact or bounded path | Readback / restore boundary | Current disposition |
| --- | --- | --- | --- |
| Independent RID control | same-family `RIDCtrlEnable` maps to `rid_ctrl_enable_0`, hash `0x3CBD864F`, FLYC `03/F7-F9`, default route `0x82 -> 0x92` | C-227/C-230 record positive-controlled absence on the `01.00.0600` direct-USB FLYC surface; no target baseline or write | `STATIC LOCKED`; only materially new owner, handler or version evidence can reopen the row; app/other-surface/0802 absence is not established |
| France EID | product-139 `0x03/0x77`; GET `[02]`, SET off/on `[00]`/`[01]`; GET ACK `[result,state]` | static destination `0x92` may be runtime-overridden; two artificial live GET routes returned no canonical ACK; persistence/RF untested | `STATIC LOCKED`; the Mac app may show conditional `unavailable`, not a switch |
| EASA OPID | product-139 `0x03/0x78`; GET `[02]`, DELETE `[01]`, SET `[00][0x10][16B]`; SDK validates 20-character input | dynamic HostID; original string must be backed up; empty restore requires DELETE; live route/persistence/RF remain open | `STATIC LOCKED`; display only masked present/empty/unknown when a safe owner exists |
| Japan DIPS credential | current `0x11/0x4B` three-part registration/key/nonce SET and QUERY; DELETE is three zero SETs | non-atomic credential; requires all-three backup, verify, and restore; contains sensitive material | `MANAGED`; current live route/readback/restore gates remain closed, and the UI must never log or expose key/nonce/editor/delete |
| China OID/UOM tag | current product-139 `OIDIdentifierGet/Set` uses `0x11/0xD6`, fixed receiver `0x92`, 500 ms/retry 3, and 18-byte requests with an eight-byte value; GET tail bytes are not visibly initialized | result is response byte 1 and GET value is bytes 2--9; byte 0, live ACK, baseline, restore, persistence, and RF relation remain open | `STATIC LOCKED`; exact parser is closed, but only a future masked read may be considered after live owner admission |
| China UOM real-name status | conditional `UOMV1` direct GET uses `0x11/0xD1`, receiver 2/0, request `[01,00]`; module appears only after runtime function ID `0x6C` admission | status parser is bounded, but external result mappings, exact live admission, and account/network Sync helper remain open; no setter/restore exists | `STATIC LOCKED`; show a redacted enum only through an admitted official key and never expose Sync as a switch |
| China OID app report gate | RC/App `UAVOIDManager`, `CN_OPERATE_ID_EFFECT` | no aircraft wire or gate getter; false selects network `DirectSuccess` | `STATIC LOCKED`; app-cloud diagnostic only, never label as aircraft RF control |
| EU C0 RID policy | `IsEuCeEnableC0Rid` -> `EU_CE_enable_c0_rid_0` (`0xF80992FE`); static codecs do not admit device use | C-227/C-228 record positive-controlled absence by hash and named enumeration on `01.00.0600`; no target baseline or write | `STATIC LOCKED`; no repeated old-index/hash probe without new evidence; adjacent C0 flags are not a substitute |
| EU C0 registration flags | Live block is shifted +1 from the public WA150 table (C-229) | sampled values and zero-range metadata are observed; no write or RF effect | `READ-ONLY LIVE`; verify onboard names rather than public indices and do not label the flags as a RID switch |
| EU C-class support | certification/status keys | state only; no RID setter | `PASSIVE OWNER`; read-only capability only |
| MSDK area strategy | SDK-local delegate selector | no aircraft ACK/readback; process-local policy | `STATIC LOCKED`; display delegate separately from authoritative real area and never present it as a region switch |
| FC/Sky/Ground region | FC area `0x03/0xAF`; Sky/Ground country `0x07/0x19` reads; distinct write families | FC and Sky completed one CN-US-CN loop; Ground US had no matching ACK; RC/Fly policy remains unknown | `READ-ONLY LIVE`; never label these as RID standard selectors |

Ordinary standards-based Broadcast RID does not define an operator telephone field. A telephone
shown by a vendor detector is more plausibly a proprietary China OID/UTMISS, account, or registry
association and must not be inferred from Basic ID or stored in public logs.

### 3.3 Managed, opaque, and legacy surfaces

| Surface | Facts | Current disposition |
| --- | --- | --- |
| FlySafe type-6 `RID_UNLOCK` | official web background + exact `Rid` product + account product/FC-SN approval; signed group/import/inventory/existing-ID action chain; current official owner/query callback is emulator-observed; external Binder attempts remain narrow negatives; current Fly Java has only types 0--4/unknown and fields 1--5, with a tolerant polygon fallback | `MANAGED`; next device dependency is read-only RC 2 identity, then an admitted loader and one official query-only callback; UI rows are not semantic type-6 truth, and A-033 is a historical comparison; genuine entitlement, canonical inventory, same-item restore and aircraft consumer/RF effect remain required |
| RID cloud-control V2 | area/product-selected value-routed SET-only `0x00/0xDD`; success caches the request and has no applied-state echo | `OPAQUE BLOCKED`; no blob editor, replay, or toggle |
| CCC broadcast-effect parameter | current mapping exists, but live metadata is unavailable and bitmap semantics/wire width/RF effect are open | `OPAQUE BLOCKED` |
| Drone-Hacks ADSB dictionary | numerical display vocabulary with current semantic collisions | `LEGACY EXCLUDED`; passive/static search only |
| Legacy FlyC `Detection` | `0x03/0xDA` `0x05`/`0x06` field mask; NDSS paper reports packets continue with `fake` fields; pinned CIAJeepDoors reproduces the same `fc_monitor` family and its author warns the mask only sends NULL/`fakeSN`, some firmware still randomly sends valid location packets, and later DJI Fly/iOS reset the bits | `LEGACY EXCLUDED`; proprietary OcuSync/AeroScope field substitution, no WA150 transfer and not a reliable transmitter-off control (C-200/C-201) |
| Name-only ADS-B debug/test commands | labels without current product-139 caller/schema/readback | `OPAQUE BLOCKED`; no guessed packets |

A-025 fixes the candidate inventory request to system-Binder transaction 4,
`02:04 -> 12:04`, `11/11`, 6,000 ms, with `00 01` start and `00 (index<<1)` pages. It caps
count/page calls/total duration at 127/128/90 seconds, accepts only ccode 0 records and a data-less
ccode 1 terminator, and strictly parses an independently implemented MSDK-compatible candidate
schema while displaying only counts, RID level, and status bits. Field-7 recognition is compatibility
exploration, not proof that current DJI Fly understands it. The exact APK was staged through MTP as
`FindUAS_A025_RID.apk` with same-session readback hash equality; user-reported installation now
exists but execution/result do not. Its FlySafe allow-list has no `11/12` tuple; this does not remove the separately gated
older F7/F9, France EID, and OPID controls from the same APK.

The official manager first derives version from passive `03/09` and support from passive `03/42`.
A-025 skips this gate and assumes V3/V4, so failure/noncanonical completion is not unsupported or
empty inventory. Exact A-026 classifies both on a complete-route proxy and sends no inventory request
unless support=true plus version 1/2 are usable. Its final artifact/audit and staged readback are
closed (C-160--C-162), and user-reported installation is C-164. Its first 60,003 ms run observed
neither gate nor any callback class; it correctly issued zero `11/11` requests (C-165). External
Binder cannot see DJI's device token, so missing pushes remain unknown rather than unsupported,
no-entitlement, empty inventory, or RID-off. Developer Assistant and retained gated F9/EID/OPID writes
remain outside the claim that the new FlySafe lane is read-only.

A-027 next fixed the active read-only lane to `02:04 -> 12:04`, `11/11`, V3/V4 selectors with no
route scan or app retry. Its artifact audit and MTP identity checks passed (C-166--C-168). The
installed run returned `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS` at `ProtocolException`, with
`11/12 request count=0` (C-169). Because the UI omitted the exception message, callback, ccode,
group, page, and terminator remain merged. The result is not unsupported, empty inventory, no
`RID_UNLOCK`, RID-off, or RF evidence. Public prior art corroborates only generic families, not the
exact product-139/RC331 fixed route.

A-028 preserves all of A-027's protocol behavior and only adds safe UI classification: static
`ProtocolException` text, numeric unexpected group/page ccode and page index, and terminator data
length. Its artifact audit and MTP identity checks passed (C-170--C-172). The installed run returned
`group transport callback failed`, `11/12 count=0`; protobuf/pages/terminator were not reached
(C-173). The next discriminator is Reply failure/ecode/callback detail.

A-033 packages that privacy-reduced diagnostic into a file-manager-readable MediaStore report while
preserving the same command/route/selectors and zero-`11/12` direct-button boundary (C-181/C-182).
It remains an external-Binder comparison. C-180/C-183/C-184 establish the official same-process
owner, and C-188--C-190 now observe its exact private query/callback through Android 11 ART TI in a
disposable emulator. With no aircraft the callback was `417`; target PID remained stable. C-191
adds the source-only success parser, while C-185 retains the current Java UI type-6 incompatibility.
The next live dependency is an admitted RC 2 same-process loader, not another external route guess.
C-208--C-210 retire ordinary installed-path, generic trace-label and uncommitted staging shortcuts;
C-211 narrows the work to the actual caller/target policy intersection or a system-mediated loader.
See [20_OFFICIAL_FLYSAFE_UI_PATH.md](20_OFFICIAL_FLYSAFE_UI_PATH.md).

Current Fly's generic set-enable payload contains only license ID and action; bounded static tracing
found no edge from type 6/field 7/`11/12` to WA150 `0802`, motor state, or BLE/Wi-Fi enable. This is a
current-app negative, not an encrypted-aircraft-firmware result. Keep license enable, RID status/HMS,
RID cloud policy, and independently observed motor-gated RF as four separate matrix rows/evidence
chains. Packed receiver `0x92` must never be relabelled as firmware module `0802`.

## 4. Offline synthetic codec lane

The independent OpenDroneID codec supports encode/decode, reference vectors and artificial test
fixtures. It has no RF, socket, USB, DUML or aircraft-control path. Its results validate the codec,
not Mini 5 Pro control, field ownership or receiver behavior over RF.

The public OpenDroneID core model provides these standard message groups:

- Basic ID;
- Location/Vector;
- Authentication;
- Self ID;
- System/operator-location;
- Operator ID;
- Message Pack.

Fixtures may use clearly artificial Basic ID, aircraft position, operator position and Operator ID
as distinct inputs. Do not feed these fixtures into the aircraft or add a radio/source adapter as
part of this scope. Previously proposed transmitter work is deferred; a codec success does not
satisfy the real-aircraft research objective.

Primary public implementation references are
[OpenDroneID Core C](https://github.com/opendroneid/opendroneid-core-c) and its
[Linux transmitter example](https://github.com/opendroneid/transmitter-linux). An independently written, byte-compatible Python codec for this message set is kept at
[`libraries/opendroneid-synthetic-codec/`](../libraries/opendroneid-synthetic-codec/README.md) (C-223). Their availability
does not mean the current Mac or attached DJI aircraft has a compatible transmit API.

## 5. Product implementation order

1. Recover provenance for the already recorded FLYC session and any existing receiver history.
   Do not repeat C-227--C-230 or interpret unlocated output files as lost evidence.
2. Establish exact read-only RC 2 installed/mounted identities and caller/target policy facts;
   admit a legitimate loader or mediated descriptor before one official query-only callback with
   unchanged DJI Fly PID. Do not repeat closed Binder or emulator-loader variants.
3. Interpret any canonical inventory with a semantic type-6 parser, preserve unavailable versus
   empty, and keep existing license identity private. A generic UI row is not type-6 proof.
4. Independently map the controls and separate identity plane in section 3.0, starting with owner/read-only
   correspondence. Keep panel controls disabled where the field's own evidence gates remain open.
5. Recover or complete C-207's standard bearer and operator motor-transition record using
   [`21_C207_MOTOR_RID_ABA_OBSERVATION_FORM.md`](21_C207_MOTOR_RID_ABA_OBSERVATION_FORM.md).
   Record presence/timing/counts only, without full identifiers, coordinates or raw frames.
6. Only after a particular surface is admitted, evaluate one bounded transition, strict readback,
   exact restore, final readback, persistence and independent motor-on RF A-B-A. A type-6 action
   additionally requires a genuine same-item baseline; a field action needs its own owner chain.
7. Keep synthetic codec tests offline. Static research into unresolved owners may continue, but
   encrypted `0802`, cloud blobs and adjacent products do not admit a firmware or packet experiment.

No current surface in this matrix is admitted as a stable Mini 5 Pro RID transmitter switch or
free-form device editor.
