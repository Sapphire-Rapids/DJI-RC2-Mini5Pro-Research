# Current blockers and dependency gates

This document lists missing evidence. It does not assert that the missing work will produce a RID
control.

## B-01 — exact live RC 2 package identity

Closed for the signed target package:

- RC331 `07.00.0100` system aggregate and verified signed `0205` chain;
- exact APEX `adbd` whole-file identity, init path, and CNXN gate;
- exact packaged `dpad_fuli.apk` identity and byte equality to the audited sample.

Still missing:

- full signed module/package set beyond the verified system/`0205` lane;
- current mounted `/apex/com.android.adbd/bin/adbd` readback hash and live boot properties;
- current installed `com.dpad.fuli` path/hash, process UID, and SELinux context;
- exact live DJI Fly APK/version/signer/splits;
- exact live `framework.jar`, `services.jar`, broker configuration/library, and ART identities;
- live process ABI, UID relation, `ro.debuggable`, SELinux, native-library extraction/path, and
  linker namespace.

Effect: ADB and Fuli statements explicitly tied to C-174--C-176 may be promoted to exact
target-package `STATIC`; they are not live execution facts. Other adjacent Binder, Parcelable,
policy, ART, and installed-file conclusions remain unpromoted.

## B-02 — v0.10 runtime result

Missing: a complete redacted `finduas-rid-probe/v0.10-schema-1` report from the exact reviewed APK.

Effect: live environment, package, Binder descriptor, bridge, ART file/mapping, and named range
gates remain unknown. Offline audit does not establish device compatibility.

## B-03 — side-effect-free privileged caller

Missing: an independently audited live caller that:

- actually runs as an identity accepted by the required Android permission path;
- uses fixed argv;
- preserves stdout, stderr, and exit status;
- does not probe root, start ADB, enter update/recovery, change settings, or invoke arbitrary input.

Effect: neither a no-op attach canary nor even the fixed Binder liveness checker has an admitted
launcher. Exact-v07 stock `dpad_fuli` supplies an operator-visible arbitrary command page for the
bounded ADB baseline, but it still does not supply fixed argv, stderr, exit status, or an automatic
side-effect-free RPC for the general attach path.

## B-04 — V2.3 independent post-fix audit

Missing: a new independent audit of exact V2.3 APK/SO bytes, source, packaged control flow, imports,
gate dominance, host tests, and hostile mutations.

Effect: V2.3 remains sealed evidence only. Even a successful audit would not admit installation or
attach because later gates remain open.

## B-05 — native exception/personality boundary

Missing: proof that all target-owned object construction/destruction and exception paths bind to a
coherent current runtime, including terminate and unwind behavior across interposable DJI DSOs.

Effect: the route resolver's immutable-zero exception gate cannot be changed.

## B-06 — whole-file live mapping identity

Design exists, but no live result proves:

- exact whole-ELF SHA-256 for every target;
- regular extracted-file source with nonzero device/inode;
- two stable maps snapshots and exact offset binding;
- non-writable original load bytes equal current memory;
- stable linker epoch before any runtime-header/symbol use.

Effect: static RVAs/build IDs cannot safely identify the live route.

## B-07 — complete route mutation coverage

Missing:

- exhaustive ProductMgr and HardwareLayer writer inventory;
- known producer threads;
- nested-safe `active_mutators`;
- monotonic `connection_epoch`;
- reviewed lock order;
- a shared reader/writer `route_gate` covering every mutation and final request closure;
- operation tokens for ACK, timeout, disconnect, failure, and rollback finalizers.

Effect: a worker-tail sample cannot establish atomic route ownership.

## B-08 — request terminal quiescence

Missing:

- exact registration witness;
- callback identity/thread and in-flight accounting;
- exact pending-handle membership;
- exact CallbackStopper membership;
- post-terminal normal worker-tail fence;
- lifecycle/connection/mapping stability at commit;
- no-late-callback proof across ACK, timeout, cancellation, and disconnect.

Effect: a live raw GET cannot be admitted merely because a callback returned or time elapsed.

## B-09 — same-owner canonical read baseline

Missing: one canonical same-owner raw France-EID ACK with `result==0`, state byte, exact route,
current epoch, no concurrent typed GET, and terminal quiescence.

Effect: Java false is ambiguous and no write baseline exists.

## B-10 — current FlySafe support/version/session

Static source is now closed: current DJI Fly gets version only from passive `03/09` Area Info and
support from passive `03/42` WhiteList Info; cache defaults `255/false` do not distinguish
uninitialized from unsupported. Exact current runtime recovery now also closes the official
same-process owner from Activity/view model through `FlightRestrictImpl` and
`JNIFSUnlockManager.queryFCLicensesJni` to the native current-device query (C-183/C-184). Missing:

- usable current-connection observations of both passive pushes;
- current support=true and negotiated V2/V3/V4 version derived from those observations;
- exact current-session receiver/product/device tuple;
- one manual same-process result from DJI Fly's non-exported aircraft-license Activity, including
  login/link/version/support errors rather than collapsing them to an empty list;
- fresh canonical query correlation; A-028 localized the current failure to the group transport
  callback; A-033 can export Reply failure/ecode/callback detail but has not been installed or run;
- privacy-minimized type-6 inventory result.

Effect: fixed legacy inventory requests, version guessing, cache defaults, missed pushes, A-027's
ambiguous result, and A-028's group transport callback failure are not evidence of unsupported or
empty inventory. External Binder cannot see DJI's device token; a same-sender/window pair is only a
proxy, and missing pushes remain unknown. C-180/C-184 identify the official same-process UI as the
next ground-truth transport read. C-185 also proves that current Java cannot semantically identify
type 6 and may map an unknown record to an ordinary polygon row, so UI presence/text/switch is not
type-6 identity or RF proof.

## B-11 — genuine type-6 entitlement

The legal acquisition/sync architecture is now static: official FlySafe website background gate ->
exact `Rid` product capability -> account product/FC-SN record -> reviewed application -> signed
server group -> FC import -> FC inventory -> existing-ID enable. DJI Fly 1.21.10 has no recovered
type-6-specific application page; ordinary Remote-ID registration and generic Unlock-a-Zone are
separate. Missing:

- the owner-visible official RID application card and Mini 5 Pro RID product selector yes/no;
- approved official server eligibility for the exact product/account/background;
- genuine account-issued, FC-bound type-6 item;
- successful FC import/visibility rather than server presence alone;
- provenance, validity, enabled baseline, and matching region level;
- a semantic type-6 oracle independent of current Fly Java's 0--4/fields-1--5 model and tolerant
  polygon fallback (C-185);
- same-item readback after any transition;
- exact restore and final inventory;
- onboard status and independent motor-on RF A-B-A.

Effect: static SetEnable schema, region/country changes, a copied license, or a server-list item cannot
establish a stable Mini 5 Pro switch. If either official visibility Boolean is false, the lawful path
is a DJI FlySafe research/experimental support request or a separately supported aircraft for parser
validation; never fabricate, transfer, or replay a license. The exact current generic action
(C-186) changes only an existing ID and has not been executed; it does not remove any of these gates.

## B-12 — effective 30/50 m restriction observation

Missing: a session in which the restriction is positively known to be active, accompanied by
read-only effective/reason status while stored configuration remains known.

Effect: account/login owner and any debug override remain hypotheses. Configured 500/5000/disabled
values do not answer the effective restriction question.

## B-13 — synchronized motor-on RID observation

Missing a single redacted timeline containing:

- powered/motors-off baseline;
- operator-initiated motor start;
- GPS/operator-location readiness;
- raw onboard `0x11/0x1C` or equivalent official state/HMS;
- independent receiver frame count/standard/field presence;
- stop/post-state.

Effect: onboard status and RF reception remain separate evidence sets.

Current static narrowing: product-139's official owner listens to natural `0x11/0x1C` push and has
no GET builder. The onboard half must therefore observe the already-subscribed push passively; an
invented polling request is not an allowed substitute.

## B-14 — exact Ground country route

Missing: passive evidence or exact current handler registration resolving Ground receiver/context,
plus a new action-specific experiment record if a future state test is considered.

Effect: the earlier no-ACK result cannot be retried or generalized into support/non-support.

## B-15 — current O4 selector and RF measurement

Missing:

- exact ownership/meaning of selector value 5;
- minimal current handler and readback for any candidate regulatory state;
- final authority/persistence across reconnect/reboot;
- calibrated spectrum/power measurement in a controlled environment.

Effect: no dBm/EIRP claim can be made from country, graph, RSSI, range, or selector alone.

## B-16 — WA150 verified plaintext and recovery

Missing:

- legitimate target PRAK/STUE or a public verified plaintext source;
- correct plaintext checksum and signature validation after any change;
- loader acceptance and recovery path proven without device risk.

Effect: ciphertext patching cannot produce a flashable Remote ID modification.
Public Mini 5 Pro photo metadata now independently ties both `0802` versions to the product, and
public BLE/network advisories make `0802` the likely 0700 network-service repair owner. A fixed
public search still found no plaintext, target key, trust-root replacement, recovery image, RID
handler, exact 0700 diff, or reproducible PoC; the admission gate is unchanged.

## B-17 — NLD runtime causality

Missing:

- a legitimately obtained online response or offline FCC blob and matching authorized-device
  context for offline authentication/decryption;
- exact post-decode DUSS frames for no-op, normal FCC, restore, and C0 actions;
- strict command/ACK/readback correlation rather than socket-write completion;
- a signer/hash comparison for the separately hosted DJI Fly 1.21.4 APK;
- a privacy-redacted actual VPN route/host record and controlled DJI Fly startup comparison;
- independent onboard and motor-on RF A-B-A evidence for any claimed RID effect.

Effect: the now-understood envelope/framing still cannot supply actual commands; the opaque NLD
payload cannot be copied into an auditable implementation, the packaged
FreeFCC profiles cannot be called its runtime source, and its generic RID marketing claim cannot be
promoted to a Mini 5 Pro control surface.

## B-18 — Drone-Hacks target recipe and WA150 CFC applicability

Missing:

- a public or legitimately obtained Mini 5 Pro software product/license and exact target job;
- a WA150 CFC image or verified plaintext, exact firmware hook, loader/signature acceptance, and
  recovery route;
- an explicit RID command/parameter with baseline, forward readback, restore, and final readback;
- synchronized onboard status and independent motor-on RF A-B-A.

Effect: the generic local executor, server-owned job model, FCC quick action, FCC ModBox support,
parameter editor, and older-product CFC cannot be promoted to a Mini 5 Pro RID implementation.
The recovered ADSB numerical display table does not change this blocker because current DJI Fly
already demonstrates command-name collisions and the table contains no payload/caller/readback.

## B-19 — region-specific RID identity/config editors

Static schemas now exist for France EID, EASA OPID, Japan DIPS, China UOM identifier, app-location
upload, and several managed/opaque policy inputs. China UOM identifier now additionally has a fixed
product-139 route and reply layout, while its separate real-name status owner is conditionally
admitted by runtime function ID `0x6C`. Missing per surface:

- exact live product/owner/HostID and a safe caller that does not replace DJI Fly's broker fd;
- privacy-reduced baseline getter and canonical ACK/result parser where not statically closed; for
  China UOM identifier, response byte 0/result enumeration and the first live ACK remain open;
- write-then-GET independent readback rather than request cache or setter ACK;
- bounded restore for empty, nonempty, partial, timeout, disconnect, and third-party-change states;
- reboot/reconnect persistence and automatic cloud/area writer precedence;
- synchronized onboard state and independent motor-on RF message-field evidence;
- for China UOM status, exact live `0x6C` admission plus the external Sync helper/result mappings;
  Sync has account/network semantics and no reversible setter.

Effect: these rows may appear only as read-only or disabled truth-labelled cards. DIPS secrets,
OPID, UOM identifiers, full serials, coordinates, telephone data, signed licenses, and cloud blobs
must not enter public logs or editable fixtures. No current static schema is admitted as a Mini 5
Pro free-form RID editor.

## B-20 — live `rid_ctrl_enable_0` admission and RF closure

Current same-family static evidence closes `RIDCtrlEnable -> rid_ctrl_enable_0 -> 0x3CBD864F ->
03/F7-F9`, but every known generic access route is now bounded by live evidence.

Both previously validated direct routes have now answered F7 with one-byte status `0x03` while
same-session known-parameter controls succeeded (C-141). Raw USB `0x82 -> 0x92` is not an alternate
answer because its maximum-height positive control also timed out. A-023 reached the RC 2
`protocol` Binder callback but target F7 ended in `ECode 1` without a same-route control (C-142).
A-024 then tested both legacy and modern Binder routes with known maximum height; both positive
controls ended in `ECode 1` after about 3.1 seconds, so target F7/F8/F9 were not sent (C-145).

A-025 now closes only the offline implementation prerequisite for the next branch. Its FlySafe lane
is fixed to system-Binder transaction 4, `02:04 -> 12:04`, `11/11`, bounded V3/V4 traversal and
privacy-reduced output. The exact final artifact passed its recorded audit and was written through
MTP to removable SD `Download` as `FindUAS_A025_RID.apk`; same-session readback SHA matched, and the
unintended long-name duplicate was removed (C-150/C-151/C-154). The user subsequently reported
installation complete (C-163), but launch, execution, query, and result remain unknown, so no live
inventory fact exists.

Static session analysis adds a new precondition. Official current Fly populates support/version only
from passive `03/42` and `03/09`; A-025 neither observes those gates nor supports V2 before its fixed
V3/V4 request. Thus a failure or noncanonical completion is a possible false negative rather than a
no-license result (C-157/C-158). A-026 now implements the bounded passive gate and admits one fixed
V3/V4 request only after usable support=true and version 1/2; its exact final artifact passed the
recorded audit and was staged as unique `FindUAS_A026_GATE.apk` with matching readback SHA and size
(C-159--C-162). The operator subsequently reported installation complete (C-164) and completed the
first instructed 60,003 ms gate run. It ended `GATE_UNOBSERVED`, with both gate pushes and every
callback class at zero; fail-closed admission therefore sent no `11/11` (C-165). This closes only
that third-party passive observation window, not aircraft support, entitlement, inventory, RID/RF,
or the official in-process observer.
The external Developer Assistant remains outside its internal allow-list, and retained gated
F9/EID/OPID controls make A-026 an Admin artifact rather than globally read-only.

A-027 then isolated one active read-only fixed-route candidate. Its 127-test/15-warning final audit,
byte-identical builds, signature/alignment, zero-permission and no-native/network/socket/shell/
external-process checks passed; MTP fresh size/readback SHA matched (C-166--C-168). The operator
installed it and ran the active button. It returned
`DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS` at `ProtocolException` with
`11/12 request count=0` (C-169). No canonical inventory formed and no set-enable request was issued.
The UI did not expose the exception message, so callback, ccode, group, page, and terminator remain
undifferentiated. This is not a support, entitlement, empty-inventory, RID, or RF result.

A-028 changes only that diagnostic surface: it adds static-safe `ProtocolException` text, numeric
unexpected group/page ccode with page index, and terminator data length while preserving command,
route, selectors, and write boundary. Its 127-test/15-warning audit, byte-identical builds,
v2/zipalign, zero-permission, no-native check, and MTP fresh size/readback SHA are closed
(C-170--C-172). The installed run returned `group transport callback failed`, `11/12 count=0`
(C-173). Thus group protobuf/page/terminator were not reached.

The current app-side schema also no longer supplies the missing aircraft consumer. Exact DJI Fly
1.21.10 typed `LicenseData` parsing stops at fields 1--5 and treats field 7 as unknown; the separate
MSDK schema is what identifies it as `LicenseDataRID` (C-152). Current Fly's generic `11/12` carries
only ID and action, and bounded app-side tracing found no edge to `0802`, motor/armed state, or the
BLE/Wi-Fi broadcaster (C-153). This does not close encrypted aircraft firmware.

The official-owner transport is no longer hypothetical. On the disposable Android 11 emulator an
ART TI `0x70010200` agent reached the exact loaded owners, obtained a nonzero current device ID and
dispatched the private FC-license query once. The callback returned `417` because the emulator had
no aircraft, and the DJI Fly PID remained unchanged (C-189/C-190). The independent success-side
group/type-6 parser is implemented and synthetically tested (C-191). This closes the external-route
guessing problem; it does not close RC 2 loading or produce a real inventory.

Missing:

- an admitted RC 2 loader for the already-observed ART TI same-process query, preferably a usable
  userspace ADB shell; an ordinary third-party APK alone cannot attach into DJI Fly;
- one RC 2 query-only run with fresh stage/callback output and unchanged target PID;
- one canonical, privacy-reduced genuine type-6 inventory baseline without retaining license material;
- aircraft-side evidence that changing the genuine type-6 enabled state is consumed by the RID
  broadcaster rather than only reflected in an SDK status object;
- only after a new owner path passes a same-route positive control: target metadata/value baseline,
  opposite-state write/readback, baseline restore, and final readback;
- reconnect/power-cycle persistence classification;
- external detector online plus operator-initiated motor-on RF A-B-A.

If separate approved instrumentation captures a raw unknown field-7 reply, retain it only in excluded
private evidence for schema verification; public output remains limited to redacted counts, level,
status bits, and result class.

Effect: known generic F7/F8 attach routes are closed for the current session. The third-party
`0x11/0x1C` Binder listener is also closed as a false-negative oracle by independent RF evidence
(C-146). Do not repeat either route family. The exact official private query and callback plumbing
are now observed on the emulator; the shortest active dependency is an RC 2 same-process loader,
which directly couples this blocker to B-21. A-026/A-027/A-028 remain historical third-party Binder
comparisons rather than the next execution route. Only a canonical success callback may advance.
Same-item enable-state readback/restore and WA150 `0802` aircraft-side ownership follow only after a
genuine canonical record.
Static discovery of another setter is
insufficient without baseline, readback, restore, persistence, and RF observation.

## B-21 — A-032 live userspace execution and shell identity

Closed offline:

- exact signed-v07 APEX `adbd` identity and pre-AUTH gate;
- semantic one-instruction A-032 design and output hash;
- removable-SD MTP staging, fresh size, and full readback hash.

Missing live:

- `id`, `getenforce`, `mp_state`, `dbg_cnt`, init/USB/FunctionFS state;
- mounted stock `adbd`, staged copy, and installed Fuli hashes;
- a proven internal location that is both writable by the observed caller and executable under the
  observed mount/SELinux policy;
- internal copy size/hash, mode, label, and successful process start;
- exclusive FunctionFS ownership after stopping only the init-managed daemon;
- first returned ADB packet after one host `CNXN`;
- if transport becomes `device`, actual shell UID/GID/SELinux context and fixed property readback.

Effect: A-032 remains `NOT ADMITTED`. Do not guess `/data` paths, run from removable storage, change
APEX/partition/boot state, or describe the staged file as an ADB workaround. The first operator batch
collects the baseline; only that evidence may generate the second command batch in the same assisted
session.

## Dependency order

The evidence dependencies are:

```text
exact A-026 first run = GATE_UNOBSERVED / zero query (C-165)
  -> A-027 fixed active read-only 11/11 = ProtocolException / ambiguous (C-169)
  -> A-028 = group transport callback failed before protobuf/page/terminator (C-173)
  -> exact owner + private query callback observed through emulator ART TI (C-189/C-190)
  -> admit an RC 2 same-process loader
  -> one canonical privacy-reduced native-query inventory
  -> privacy-reduced genuine type-6 level/enabled/valid baseline
  -> prove exact same-item 11/12 response and 11/11 readback/restore design
  -> verified 0802/aircraft-side consumer or independent RF effect
  -> one reversible transition + restore
  -> reconnect persistence + independent RF A-B-A
```

The F7 route matrix is closed at the generic attach level, and the tested Binder status listener is
closed as a truth source. Continue with exact type-6 inventory/state and verified WA150
plaintext/firmware analysis. Do not repeat the old generic attach or listener chains merely to
answer the same fixed questions.

```text
exact live identity
  -> v0.10 runtime inventory
  -> privileged caller proof
  -> V0 no-op reachability
  -> restart/revalidate
  -> V1 semantic topology
  -> independently audited route-only identity
  -> exception + mutation + quiescence gates
  -> one same-owner canonical GET
  -> read-only status correlation
  -> only then evaluate whether any mutation experiment has a complete baseline/restore/RF design
```

The FlySafe path is separate:

```text
official RID application card + Mini 5 Pro Rid product selector yes/no
  -> approved official account/product/FC-SN entitlement
  -> signed group download + FC import
  -> passive support/version populated for the current connection
  -> fresh privacy-minimized inventory
  -> genuine type-6 item and baseline
  -> bounded same-item transition/readback/restore
  -> onboard status + independent motor-on RF A-B-A
```

Failure or `UNKNOWN` at a gate does not authorize trial-and-error at the next gate.

The ADB path is independent and currently shortest:

```text
exact signed-v07 adbd + gate (C-174/C-175)
  -> live baseline and mounted-file identities
  -> choose one proven internal executable path
  -> verify copied A-032 hash/mode/label
  -> stop only init-managed adbd
  -> launch one userspace copy
  -> one host CNXN and exact first-packet classification
  -> if device: adb shell id + fixed properties
```
