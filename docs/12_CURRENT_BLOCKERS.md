# Current blockers and dependency gates

This document lists missing evidence. It does not assert that the missing work will produce a RID
control.

A-048/A-051 close the basic loader and one RID cache value. C-283 explains retained-value
expiry and notification deduplication. A054 now closes the guarded existing-MMKV/two-SDK-cache
comparison (C-286--C-292): ProductType139,41 policy rows,36 distinct nonempty candidates,
receiver18/4 and a candidate match with DEFAULT-match0. Parsing/disposal, stable PID/APK,
file removal, independent cleanup/receipts and B4 closure all passed.
The next gap is the matched payload's structure and aircraft consumer, together with applied
readback/restore; candidate matching does not choose an actual area or identify a writer.
See [the runtime topic](23_RC2_LIVE_RUNTIME.md). Prior commits through `2f31394` were pushed on
one explicit request; new results remain local unless another push is requested.
C-227--C-230 have already answered the two tested FLYC parameter
candidates on `01.00.0600`; they are not pending probes. Basic/UAS ID, aircraft position,
operator position and the separate Operator ID plane require their own evidence chains (B-22).

## B-01 — exact live RC 2 package identity

Closed for the signed target package:

- RC331 `07.00.0100` system aggregate and verified signed `0205` chain;
- exact APEX `adbd` whole-file identity, init path, and CNXN gate;
- exact packaged `dpad_fuli.apk` identity and byte equality to the audited sample.

Closed by the first live reports and samples (C-235--C-238): installed Fly 1.19.4/ARMv7 and its
signer/APK/SDK library identities; pre-reinstall Fuli and framework/services hashes; the probe's
32-bit ART identity; `ro.debuggable=1`, `mp_state=production` and SELinux enforcing=false.
C-245 also closes post-reinstall Fuli metadata: updated-system=true, unchanged original
code/hash/signer and two checked DEX entries, with all three component entries enabled. Fly/ART
identity remains stable. Earlier directory ABSENT results describe only the Observer app's view.
C-246 establishes actual Shell UID/GID 1000/system and `system_app:s0`; C-247 establishes
`/data` and `/data/app` mode 0771, system:system, with `system_data_root_file` and
`apk_data_file` labels respectively.

Still missing:

- full signed module/package set beyond the verified system/`0205` lane;
- current mounted adbd hash/branch result; the reported `dbg_cnt` was an empty string;
- mounted identities outside the tested lane, including any userspace-ADB alternative;
- broader process mappings and other payload/namespace behavior beyond A-048.

C-274/C-275 close the tested ordinary SO identity/label/hash, native target identity, load result
and file restoration. The complete process mapping inventory was not collected.

The installed-file matches support the specific framework/service and package comparisons in
C-237/C-241/C-245. Actual Shell identity now has its own direct evidence (C-246); target-process
loading is now observed for A-048 in C-274; other payloads retain their own scope.

## B-02 — runtime report and SD export

Initial report/export work is closed: v0.11's INCOMPLETE report and v0.12's COMPLETE report were
received, followed by the verified fixed sample ZIP. A-039 is current; A-038 is archived.

The post-install A-039 report has also been received and is COMPLETE (C-245). No further
capability report is currently requested. The separate Shell and parent-directory results are
also received (C-246/C-247); remaining loading work is listed in B-03.

## B-03 — actual Shell caller and loading path

The original Fuli package is reinstalled and DevActivity opens (C-242); the post-install report
confirms all three entries enabled (C-245). The operator subsequently opened the Shell page,
ran `id` and returned the photo (C-246), followed by the directory listing (C-247). The stock
page's startup checks and Runtime.exec(String) behavior are documented in
[the Android topic](08_ANDROID_ADB.md); it is a manual interface, not an automatic command RPC.

The Shell itself reports UID/GID 1000/system and `system_app:s0`. Both parent directories have
mode 0771 and system:system ownership; their labels are recorded in C-247. These observations
do not test a payload file or a target-process load. C-248 statically shows that scanDirLI
treats directories as package candidates and failure may remove them; systemReady reconciliation
can also remove unregistered directories. Both examined rules skip ordinary non-APK files.
The candidate is therefore a separate regular `.so` directly in `/data/app`, not a subdirectory.

C-249 supplies the complete listing: seven subdirectories, with DJI_FLY at 0777 and six
randomized installation roots at 0775; all are system:system and apk_data_file. The candidate
`finduas_A040_canary.so` was absent. F1/A-043 staging/readback matched (C-251);
C-252 shows the correctly entered wrapper reaching `sh` but failing to open the literal
wildcard path, with no F1 marker. C-253 supplies the precise stderr result:
`ls: /storage: Permission denied`. Listing refusal does not establish that an exact known child
file is unreadable. C-254 records `/storage` mode 0710, shell:everybody and `mnt_user_file`.
Fuli's supplementary everybody group (9997) has search but no directory-read permission. The
storage API reports one mounted public volume; its identifier remains private.

F2/A-044 passed review/tests and staging/readback (C-255/C-256); F1 was archived without
deletion. C-257 now closes script execution, SD report saving and complete MTP receipt with
schema/end/parser validation. The report is INCOMPLETE only for `pidof dji.go.v5`: rc=1 and
empty output. System/system_app identity, SELinux Permissive, ro.debuggable=1, wifi_on=0 and
A-040 source size/hash all passed.

C-258 records a DJI Fly HOME main-process entry with a private nonzero PID. C-259 separately
returned a target-context path error without a mount-options line. F3/A-045 then supplied
the live proc mount options, but its heredoc failed under Android mksh (C-262). F4 preserves
the paired AMS/proc collection through a pipe and its report now passes strict parsing (C-267).
The remaining target-proc visibility failure is recorded; do not repeat that same diagnostic.

C-274 resolves the loader objective through a self-reading canary without changing proc permissions.
Its target base domain is untrusted_app; identity/API/disposal checks succeeded, the ordinary SO
was removed and independently confirmed absent (C-275). C-277 subsequently closed native_get_sync;
A-051 returned a real cached RID status in C-281 and its independent recovery closed in C-282.

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

Recording procedure: use the fixed privacy-reduced form in
[`21_C207_MOTOR_RID_ABA_OBSERVATION_FORM.md`](21_C207_MOTOR_RID_ABA_OBSERVATION_FORM.md). It
captures the independent receiver's exact bearer class, message presence, frame count, and motor
transition times, while excluding full identifiers, coordinates, raw frames, captures, and private
DroneID telemetry. Completing the form does not authorize any write or toggle.

Effect: onboard status and RF reception remain separate evidence sets.

Current static narrowing: product-139's official owner listens to natural `0x11/0x1C` push and has
no GET builder. The onboard half must therefore observe the already-subscribed push passively; an
invented polling request is not an allowed substitute.

Independent-receiver narrowing: public DragonSDR documentation states DJI-private OcuSync DroneID is
encrypted on O4 (Mini 5), so a DroneID receiver without a licensed DragonScope decoder yields only a
per-session hash ID plus frequency/RSSI, and that private DroneID is sent only while motors are
spinning (C-202). This boundary is limited to DJI's private DroneID protocol. Public RUB-SysSec
DroneSecurity NDSS 2023 FAQ states DJI's Drone-ID is not the same as standardized Bluetooth/Wi-Fi
Remote ID, which follows EN 4709 (EU) / ASTM F3411 (US) and is readable by a plain smartphone app
(C-203). Standardized Broadcast Remote ID is therefore plaintext and a standard Remote ID receiver
reads Basic ID directly without any DJI decoder; only the DJI-private O4 DroneID telemetry is limited
to hash/RSSI without DragonScope.

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

## B-20 — closed FLYC candidates and official inventory dependency

C-227--C-230 close the later `01.00.0600` aircraft-direct FLYC session: the known-height F7/F8
positive control succeeded, table 0 reported CRC `0x5F8B2AE1`/count 1558, and enumeration reported
915 named parameters. `EU_CE_enable_c0_rid(_0)` and `rid_ctrl_enable_0` were absent on that
surface with same-session positive controls. The EU C0 registration block was shifted +1 from
the public table and the sampled flags had min/max 0. There is no target baseline to promote to
a write; the neighbouring registration flags are not substitute RID switches. These results do
not establish absence in DJI Fly, another firmware surface or encrypted WA150 `0802`.

The earlier route and inventory sequence below is retained as history, not a list of retries.

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

- the contingency-specific daemon/USB/FunctionFS baseline; C-246 supplies the Fuli Shell identity
  and C-237 supplies probe-visible boot properties, but no ADB Shell identity has been obtained;
- mounted stock `adbd` and the selected staged copy hashes; Fuli's post-install hash is closed by C-245;
- a proven internal location that is both writable by the observed caller and executable under the
  observed mount/SELinux policy;
- internal copy size/hash, mode, label, and successful process start;
- exclusive FunctionFS ownership after stopping only the init-managed daemon;
- first returned ADB packet after one host `CNXN`;
- if transport becomes `device`, actual shell UID/GID/SELinux context and fixed property readback.

Effect: A-032 remains `NOT ADMITTED`. Do not guess `/data` paths, run from removable storage, change
APEX/partition/boot state, or describe the staged file as an ADB workaround. This contingency list
is not the current operator instruction. B-03 proceeds through corrected F4 diagnostics and
the SD task receiver; internal-file baselines remain pending.

Bricking precedent: the pinned public RC 2 report C-212 records framework/TEE tamper followed by a
DJI Fly update boot-logo loop and failure of every documented software recovery attempt. Before any
privileged runtime experiment, require an explicit no-auto-update state, a bounded one-session
action list, and a documented recovery stop point. Do not modify TEE/eFuse state, relock a modified
boot chain, flash startup partitions, or treat physical EDL as an authorized fallback.

## Dependency order

The current evidence dependencies are:

```text
verified Fly 1.19.4 samples and post-install A-039 COMPLETE report (C-245)
  -> actual Shell identity and parent-directory observations received (C-246/C-247)
  -> complete directory listing received; candidate basename absent (C-249)
  -> F1 reviewed/tested and SD-staged with matching readback (C-250/C-251)
  -> F1 wrapper path-open failure; script not entered (C-252)
  -> /storage enumeration refused (C-253)
  -> search-only parent and unique mounted public volume confirmed (C-254)
  -> F2 validated and SD-staged/readback matched; F1 archived (C-255/C-256)
  -> F2 report received: source checks pass; pidof rc1/empty is the only failure (C-257)
  -> AMS HOME main-process record received; PID retained privately (C-258)
  -> separate target-context path error received (C-259)
  -> F3 reviewed/tested and SD-staged/readback matched (C-260/C-261)
  -> F3 received: live hidepid=2; mksh heredoc temp creation failed (C-262)
  -> F4/B1 staged and started; three host jobs and strict F4 receipt verified (C-266/C-267)
  -> A-048/L1/B2 build, tests, exact staging and live baseline (C-268--C-273)
  -> A-048 native identity/API success; stable Fly PID/UID/APK (C-274)
  -> test-file removal, independent absence readback and CLOSED STOP (C-275)
  -> exact RID synchronous cache path closed (C-277)
  -> one real cached status and verified cleanup/session closure (C-280--C-282)
  -> retained-cache freshness and exact cloud source closed (C-283--C-288)
  -> existing RID candidate / shared-cache content match and recovery (C-289--C-292)
  -> matched payload schema/aircraft consumer; receive-time/RF correlation and reversible control owner
  -> verified independent RID-state observation and callback provenance
```

The earlier FlySafe inventory branch retains this emulator and transport history:

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
closed as a truth source. Current work follows C-240/C-243/C-245--C-261; FlySafe inventory remains a
separate branch. The older resolver sequence below is historical context, not the current operator
procedure:

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

The userspace ADB path is an independent loader contingency, not a pre-admitted shortcut:

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

## 2026-08-30 loader checkpoint

The ART TI query code and exact owner/callback path are no longer the immediate blocker. Three
deployment shortcuts are now retired on emulator evidence:

1. normal `/data/app/...==/...so` direct attach: parser delimiter failure (C-208);
2. delimiter-free generic trace path: target terminated before canary, while identical bytes worked
   under delimiter-free `apk_data_file` (C-209);
3. uncommitted PackageInstaller staging: target search denied on `apk_tmp_file`, session abandoned
   (C-210).

Within the same-process lane, signer/package identities are now recorded in C-237/C-245. The
Fuli Shell caller identity and parent-directory labels are now recorded in C-246/C-247. The
remaining C-211 blocker is the target-process baseline and a verified test-file path/descriptor
at their policy intersection. If no intersection exists, prioritize the already separate
userspace-ADB route or an existing system-mediated loader only after its own baseline and recovery
gates close. C-207's written standard-RID bearer/timing record remains open, independently of the
FLYC result. Do not repeat the C-192--C-199 candidates to rediscover C-227--C-230. A-035 and A-036
should not be installed on RC 2 as currently written.

## B-22 — requested fields: owner, readback and RF correspondence

The expanded target covers Basic/UAS ID, aircraft position and operator position in addition to
the RID switch. Operator ID remains a separate identity plane. Missing for each field:

- an exact current authoritative owner and admitted privacy-reduced read path;
- correspondence between that owner's value and the intended standard-RID RF field;
- a bounded control with baseline, strict readback, exact restore and final readback;
- automatic writer precedence and reconnect/reboot persistence classification;
- independent receiver confirmation of the field transition and restoration.

Compliance serial derivation does not establish RF Basic ID, and app-location delivery does not
establish the System/operator-location field. Aircraft GNSS, operator position, Operator ID,
OPID/DIPS/UOM identity and cloud policy must not substitute for one another. See the field matrix
in [19_RID_EXPERIMENT_CONTROL_MATRIX.md](19_RID_EXPERIMENT_CONTROL_MATRIX.md). Synthetic codecs
remain offline and cannot close a real-aircraft gate.

## Handoff evidence availability

The original local corpus has been located and selected fixed DJI Fly/RC331 samples and A-032/
A-033 outputs were rehashed against their registered identities. This restores access to static
inputs, not live RC 2 identity or execution evidence. No private material is imported here.

The bounded sandbox search did not locate the latest 1558-slot/915-name enumeration output or a
completed C-207 RF timeline. Recover old task output or an existing local record before planning
another device action; in particular, account for unnamed/status/error entries in the enumeration.
This is a search limitation, not evidence that the records were lost or that the recorded live
results did not occur.

The existing FindUASMac persisted history was located separately through its source-configured
Application Support location. A bounded read found no explicit motor-transition or aircraft-air-
bearer fields. The writer rate-limits persistence per UAS to one row per two seconds, so rows are
not RF packet counts and do not close C-207. Identifiers, coordinates and raw records stay private.
