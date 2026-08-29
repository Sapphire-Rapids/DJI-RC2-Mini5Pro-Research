# RID experiment control matrix

## 1. Purpose

The research target now includes both a stable Mini 5 Pro Broadcast Remote ID enable/disable
control and other RID configuration surfaces that could help test independent detection equipment.
This document records what can be observed, what is statically writable but not yet admitted, what
is official managed state, and what should instead be implemented on a separate synthetic laboratory
source.

“Adjustable” requires all of the following on the exact subject/version: authoritative owner,
baseline getter, bounded setter/action, canonical ACK, independent readback, restoration, persistence
classification, and motor-on RF A-B-A evidence. A UI control is not evidence that a device accepted
or applied a value.

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

## 2. Implementation levels

| Level | Meaning | UI rule |
| --- | --- | --- |
| `READ-ONLY LIVE` | Current app/bridge has a bounded read path and preserves `unavailable` | Show current value and capture time; no editor |
| `PASSIVE OWNER` | Exact official owner listens for natural state, but no active GET exists | Show only when obtained without replacing the owner or opening a second broker client |
| `STATIC LOCKED` | Exact getter/setter/schema exists, but live route, baseline, restore, or RF gate is open | Disabled card with the missing gate; never a working-looking toggle |
| `MANAGED` | Account/server/FC-bound licensed or credential state | Read only through the official authenticated owner; never synthesize or replay material |
| `OPAQUE BLOCKED` | Set-only blob, unknown semantics, absent readback, or name-only command | Do not expose raw editor/replay |
| `LEGACY EXCLUDED` | Proven different protocol/product generation | Search signature only; do not migrate into a sender |
| `SYNTHETIC SOURCE` | Standard message field suitable for a separate controlled RF source | Implement only with synthetic identity, lab lease, explicit RF backend, stop, and independent receiver |

Every matrix row below has exactly one primary implementation level from this table. Credential,
privacy, account, and non-atomicity restrictions are additional boundaries rather than a second
level.

## 3. Current Mini 5 Pro / DJI Fly control surfaces

### 3.1 State, diagnostics, timing, and identity

| Surface | Owner and path | Read | Write | Current disposition |
| --- | --- | --- | --- | --- |
| Global Broadcast RID master | same-family current SDK `RIDCtrlEnable -> rid_ctrl_enable_0`; live Mini 5 Pro owner pending | direct target routes failed metadata with positive controls; both third-party Binder routes failed known-height positive control before target | fixed F9 path exists but remained locked and unsent | `STATIC LOCKED`; all known generic attach routes are closed for this session; reopen only with an official owner or verified WA150 handler |
| RID/EID working status | product-139 `RidImportModule`, natural `0x11/0x1C` push | support/normal flags, area, failure | none | `PASSIVE OWNER`; no GET builder and onboard normal is not RF truth |
| Regional capability | product-139 interpretation of the same push | US bit 0, Cloud bit 10, EU/Japan/France bits 11/12/13 in explicit mode | none | `PASSIVE OWNER`; show capability separately from real area and RF standard |
| RID health/diagnostics | FC health manager plus Remote ID delegate | working/idle/location/firmware/no-broadcast/unsupported/unknown | none | `PASSIVE OWNER`; preserve the raw failure class without coordinates |
| Broadcast start/stop timing | aircraft firmware plus independent receiver | A-024 Binder listener was false-negative while the independent detector confirmed real motor-on RID | no safe trigger | `READ-ONLY LIVE`; use the independent receiver for RF truth and do not repeat the tested Binder listener |
| Operator-location health | RC/Android location provider -> link -> aircraft | permission, age, accuracy, RID failure class | no current selector or coordinate setter | `PASSIVE OWNER`; privacy-reduced status only, never location spoofing |
| Aircraft/UAS identity | FC/device identity and compliance derivation | static get/listen-only candidate; no admitted live read | no current setter found | `STATIC LOCKED`; live route, privacy-safe read, and actual RF Basic ID correspondence remain unclosed |
| RF bearer | aircraft BLE/Wi-Fi scheduler | external receiver observation | no selector found | `READ-ONLY LIVE`; show only an independently observed bearer, never infer it from China cloud tracking masks |

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
| Independent RID control | current same-family `RIDCtrlEnable` maps to `rid_ctrl_enable_0`, hash `0x3CBD864F`, FLYC `03/F7-F9`, default route `0x82 -> 0x92` | direct target routes returned status `03` with controls; A-024 Binder legacy/modern known-height controls both timed out, so target and all F9 operations were gated off | `STATIC LOCKED`; known generic routes are exhausted; no live baseline or RF A-B-A exists and only a new official owner/verified handler can reopen the row |
| France EID | product-139 `0x03/0x77`; GET `[02]`, SET off/on `[00]`/`[01]`; GET ACK `[result,state]` | static destination `0x92` may be runtime-overridden; two artificial live GET routes returned no canonical ACK; persistence/RF untested | `STATIC LOCKED`; the Mac app may show conditional `unavailable`, not a switch |
| EASA OPID | product-139 `0x03/0x78`; GET `[02]`, DELETE `[01]`, SET `[00][0x10][16B]`; SDK validates 20-character input | dynamic HostID; original string must be backed up; empty restore requires DELETE; live route/persistence/RF remain open | `STATIC LOCKED`; display only masked present/empty/unknown when a safe owner exists |
| Japan DIPS credential | current `0x11/0x4B` three-part registration/key/nonce SET and QUERY; DELETE is three zero SETs | non-atomic credential; requires all-three backup, verify, and restore; contains sensitive material | `MANAGED`; current live route/readback/restore gates remain closed, and the UI must never log or expose key/nonce/editor/delete |
| China OID/UOM tag | current product-139 `OIDIdentifierGet/Set` uses `0x11/0xD6`, fixed receiver `0x92`, 500 ms/retry 3, and 18-byte requests with an eight-byte value; GET tail bytes are not visibly initialized | result is response byte 1 and GET value is bytes 2--9; byte 0, live ACK, baseline, restore, persistence, and RF relation remain open | `STATIC LOCKED`; exact parser is closed, but only a future masked read may be considered after live owner admission |
| China UOM real-name status | conditional `UOMV1` direct GET uses `0x11/0xD1`, receiver 2/0, request `[01,00]`; module appears only after runtime function ID `0x6C` admission | status parser is bounded, but external result mappings, exact live admission, and account/network Sync helper remain open; no setter/restore exists | `STATIC LOCKED`; show a redacted enum only through an admitted official key and never expose Sync as a switch |
| China OID app report gate | RC/App `UAVOIDManager`, `CN_OPERATE_ID_EFFECT` | no aircraft wire or gate getter; false selects network `DirectSuccess` | `STATIC LOCKED`; app-cloud diagnostic only, never label as aircraft RF control |
| EU C0 RID policy | `IsEuCeEnableC0Rid` -> `EU_CE_enable_c0_rid_0` | two live metadata reads returned status `0x03`; no F8 baseline or F9 write | `STATIC LOCKED`; value remains unavailable |
| EU C-class support | certification/status keys | state only; no RID setter | `PASSIVE OWNER`; read-only capability only |
| MSDK area strategy | SDK-local delegate selector | no aircraft ACK/readback; process-local policy | `STATIC LOCKED`; display delegate separately from authoritative real area and never present it as a region switch |
| FC/Sky/Ground region | FC area `0x03/0xAF`; Sky/Ground country `0x07/0x19` reads; distinct write families | FC and Sky completed one CN-US-CN loop; Ground US had no matching ACK; RC/Fly policy remains unknown | `READ-ONLY LIVE`; never label these as RID standard selectors |

Ordinary standards-based Broadcast RID does not define an operator telephone field. A telephone
shown by a vendor detector is more plausibly a proprietary China OID/UTMISS, account, or registry
association and must not be inferred from Basic ID or stored in public logs.

### 3.3 Managed, opaque, and legacy surfaces

| Surface | Facts | Current disposition |
| --- | --- | --- |
| FlySafe type-6 `RID_UNLOCK` | official web background + exact `Rid` product + account product/FC-SN approval; signed group/import/inventory/existing-ID action chain; exact generic `0x11/0x11` / `0x11/0x12` wire; exact current package declares and emulator-renders a non-exported official license-manager Activity; recovered current owner reaches native query/set with current device ID; A-026 passive gate ended unobserved/zero-query; A-027 ended `ProtocolException`/ambiguous; A-028 localized it to group transport callback failure before protobuf/pages/terminator, with zero `11/12`; A-033 adds privacy-reduced export but is unrun; current Fly Java has only types 0--4/unknown and fields 1--5, then misroutes unknown to a tolerant polygon fallback, while separate MSDK defines field-7 RID | `MANAGED`; official aircraft tab is same-process transport evidence but not semantic type-6 truth; next query is that tab followed by one A-033 diagnostic, not another route guess; no canonical inventory, support, entitlement, RID, or RF evidence exists; never fabricate/upload/replay a license, and require same-item restore plus a proved aircraft consumer/RF result before calling it a switch |
| RID cloud-control V2 | area/product-selected value-routed SET-only `0x00/0xDD`; success caches the request and has no applied-state echo | `OPAQUE BLOCKED`; no blob editor, replay, or toggle |
| CCC broadcast-effect parameter | current mapping exists, but live metadata is unavailable and bitmap semantics/wire width/RF effect are open | `OPAQUE BLOCKED` |
| Drone-Hacks ADSB dictionary | numerical display vocabulary with current semantic collisions | `LEGACY EXCLUDED`; passive/static search only |
| Legacy FlyC `Detection` | `0x03/0xDA` `0x05`/`0x06` field mask; paper reports packets continue with `fake` fields | `LEGACY EXCLUDED`; proprietary OcuSync/AeroScope, no WA150 transfer |
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
The next live dependency is an admitted RC 2 same-process loader, not another external route guess;
see [20_OFFICIAL_FLYSAFE_UI_PATH.md](20_OFFICIAL_FLYSAFE_UI_PATH.md).

Current Fly's generic set-enable payload contains only license ID and action; bounded static tracing
found no edge from type 6/field 7/`11/12` to WA150 `0802`, motor state, or BLE/Wi-Fi enable. This is a
current-app negative, not an encrypted-aircraft-firmware result. Keep license enable, RID status/HMS,
RID cloud policy, and independently observed motor-gated RF as four separate matrix rows/evidence
chains. Packed receiver `0x92` must never be relabelled as firmware module `0802`.

## 4. Separate synthetic-source lane

A real DJI aircraft is a poor source for freely changing every standards message: many fields are
device identity, GNSS-derived, region policy, signed credentials, or official managed state. A
separate OpenDroneID transmitter is the appropriate backend for detector compatibility tests that
need fully synthetic values.

The public OpenDroneID core model provides these standard message groups:

- Basic ID;
- Location/Vector;
- Authentication;
- Self ID;
- System/operator-location;
- Operator ID;
- Message Pack.

Candidate adjustable laboratory fields include a clearly synthetic Basic ID, protocol/profile,
aircraft type, location/vector trajectory, operator-location type and synthetic offset, self-ID or
emergency description, operator ID, accuracy classes, status, and transport bearer. Actual RF
requires an explicit external backend such as a reviewed Linux, ESP32, or nRF OpenDroneID source;
the macOS app must remain no-RF until that adapter reports concrete capabilities.

The source adapter contract must require:

1. no real device/account/operator identity;
2. controlled test area and regulatory authorization;
3. a 5--15 minute lease, manual stop, timeout stop, and fail-closed lockout;
4. configuration readback from the source, not just write completion;
5. independent receiver confirmation of bearer, message types, field values, and cessation;
6. no automatic resume after app restart or reconnect;
7. redacted audit logs containing no coordinates, full IDs, credentials, or raw frames.

Primary public implementation references are
[OpenDroneID Core C](https://github.com/opendroneid/opendroneid-core-c) and its
[Linux transmitter example](https://github.com/opendroneid/transmitter-linux). Their availability
does not mean the current Mac or attached DJI aircraft has a compatible transmit API.

## 5. Product implementation order

1. Expand the administrator panel with a truth-labelled configuration inventory. Existing live
   USB region/France-EID results stay read-only; locked/managed/opaque/legacy items remain disabled.
2. Treat A-026's `GATE_UNOBSERVED`, A-027's ambiguous `ProtocolException`, and A-028's group
   transport callback failure as historical narrow negatives. The exact ART TI owner/query callback
   is now emulator-observed; admit an RC 2 loader and run the query-only agent once. Do not repeat
   another external route guess or standard JVMTI 1.2 attach.
3. Advance only after one canonical privacy-reduced inventory; report type-6 count/level/enabled/
   valid and preserve unavailable versus empty.
4. If and only if a genuine type-6 item exists, implement exact same-item baseline, one transition,
   inventory readback, restoration, and final readback; keep the license ID process-private.
5. Correlate the controlled state with operator-started motor-on independent RF. The tested
   `0x11/0x1C` Binder listener is false-negative and must not be reused as truth.
6. Locate the dependency that owns the external China UOM status mappings and Sync helper, then
   close runtime function-ID `0x6C` admission; keep identifier editing locked until live
   baseline/restore/RF gates are met.
7. Close OPID/Japan runtime Characteristics and read-only admission; never retain credential data.
8. Pursue verified WA150 `0802` plaintext or legitimate on-device production-owner evidence to find
   the actual broadcaster, motor/GNSS gates, region format selector, and any firmware-level control.
9. In parallel, implement a separately reviewed synthetic OpenDroneID source adapter for fields
   that a DJI aircraft cannot safely or legitimately expose as free-form controls.

No current surface in this matrix is admitted as a stable Mini 5 Pro RID transmitter switch or
free-form device editor.
