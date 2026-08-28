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
chain and Mini 5 Pro admission experiment add C-136 through C-138.

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
| Global Broadcast RID master | same-family current SDK `RIDCtrlEnable -> rid_ctrl_enable_0`; live Mini 5 Pro owner pending | fixed F7/F8 probe implemented; no live reply yet | fixed F9 path implemented behind successful baseline read | `STATIC LOCKED`; this is now a concrete candidate rather than an absent-name search, but Mini 5 Pro admission is unresolved |
| RID/EID working status | product-139 `RidImportModule`, natural `0x11/0x1C` push | support/normal flags, area, failure | none | `PASSIVE OWNER`; no GET builder and onboard normal is not RF truth |
| Regional capability | product-139 interpretation of the same push | US bit 0, Cloud bit 10, EU/Japan/France bits 11/12/13 in explicit mode | none | `PASSIVE OWNER`; show capability separately from real area and RF standard |
| RID health/diagnostics | FC health manager plus Remote ID delegate | working/idle/location/firmware/no-broadcast/unsupported/unknown | none | `PASSIVE OWNER`; preserve the raw failure class without coordinates |
| Broadcast start/stop timing | aircraft firmware plus independent receiver | event timeline not yet implemented | no safe trigger | `STATIC LOCKED`; one prior motor-start/RF observation exists, but no synchronized motor/onboard/RF read path or timeline is implemented |
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
| Independent RID control | current same-family `RIDCtrlEnable` maps to `rid_ctrl_enable_0`, hash `0x3CBD864F`, FLYC `03/F7-F9`, default route `0x82 -> 0x92` | self-developed RC 2 Binder client performs F7 metadata, F8 baseline, one F9 change, F8 readback, and baseline restore; live F7/F8 reply and RF A-B-A remain pending | `STATIC LOCKED`; fixed APK is staged, and a successful F7/F8 will promote this row directly to a bounded live transaction candidate |
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
| FlySafe type-6 `RID_UNLOCK` | signed account/FC-bound inventory and enable state; product eligibility, live support/version/session, genuine item, restore, and RF effect remain open | `MANAGED`; official-owner masked inventory only, never fabricate/upload/replay a license |
| RID cloud-control V2 | area/product-selected value-routed SET-only `0x00/0xDD`; success caches the request and has no applied-state echo | `OPAQUE BLOCKED`; no blob editor, replay, or toggle |
| CCC broadcast-effect parameter | current mapping exists, but live metadata is unavailable and bitmap semantics/wire width/RF effect are open | `OPAQUE BLOCKED` |
| Drone-Hacks ADSB dictionary | numerical display vocabulary with current semantic collisions | `LEGACY EXCLUDED`; passive/static search only |
| Legacy FlyC `Detection` | `0x03/0xDA` `0x05`/`0x06` field mask; paper reports packets continue with `fake` fields | `LEGACY EXCLUDED`; proprietary OcuSync/AeroScope, no WA150 transfer |
| Name-only ADS-B debug/test commands | labels without current product-139 caller/schema/readback | `OPAQUE BLOCKED`; no guessed packets |

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
2. Add a privacy-reduced synchronized timeline for motor state, onboard RID state, receiver RF
   first/last seen, bearer, and message-type presence.
3. Close a safe official-owner access route for the natural `0x11/0x1C` push without opening a
   second RC-local broker client.
4. Locate the dependency that owns the external China UOM status mappings and Sync helper, then
   close runtime function-ID `0x6C` admission; keep identifier editing locked until live
   baseline/restore/RF gates are met.
5. Close OPID/Japan runtime Characteristics and read-only admission; never retain credential data.
6. Pursue verified WA150 `0802` plaintext or legitimate on-device production-owner evidence to find
   the actual broadcaster, motor/GNSS gates, region format selector, and any firmware-level control.
7. In parallel, implement a separately reviewed synthetic OpenDroneID source adapter for fields
   that a DJI aircraft cannot safely or legitimately expose as free-form controls.

No current surface in this matrix is admitted as a stable Mini 5 Pro RID transmitter switch or
free-form device editor.
