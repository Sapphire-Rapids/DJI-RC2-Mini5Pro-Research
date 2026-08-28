# Current blockers and dependency gates

This document lists missing evidence. It does not assert that the missing work will produce a RID
control.

## B-01 — exact live RC 2 package identity

Missing:

- exact `07.00.0100` package/module manifest;
- exact live DJI Fly APK/version/signer/splits;
- exact `framework.jar`, `services.jar`, `dpad_fuli.apk`, broker configuration/library, and ART
  identities;
- live process ABI, UID relation, `ro.debuggable`, SELinux, native-library extraction/path, and
  linker namespace.

Effect: adjacent RC331 `0205` Binder, Parcelable, package, policy, ADB, and ART conclusions cannot
be promoted to exact live facts.

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
launcher. Adjacent stock `dpad_fuli` does not supply one.

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

Missing:

- current support=true from an official populated gate;
- negotiated V2/V3/V4 version;
- exact current-session receiver/product/device tuple;
- fresh query correlation;
- privacy-minimized type-6 inventory result.

Effect: fixed legacy inventory requests and version guessing are not admissible evidence.

## B-11 — genuine type-6 entitlement

Missing:

- official server eligibility for the exact product;
- genuine account-issued, FC-bound type-6 item;
- provenance, validity, enabled baseline, and matching region level;
- same-item readback after any transition;
- exact restore and final inventory;
- onboard status and independent motor-on RF A-B-A.

Effect: static SetEnable schema cannot establish a stable Mini 5 Pro switch.

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

## B-17 — NLD runtime causality

Missing:

- exact post-decode DUSS frames for no-op, normal FCC, restore, and C0 actions;
- strict command/ACK/readback correlation rather than socket-write completion;
- a signer/hash comparison for the separately hosted DJI Fly 1.21.4 APK;
- a privacy-redacted actual VPN route/host record and controlled DJI Fly startup comparison;
- independent onboard and motor-on RF A-B-A evidence for any claimed RID effect.

Effect: the opaque NLD payload cannot be copied into an auditable implementation, the packaged
FreeFCC profiles cannot be called its runtime source, and its generic RID marketing claim cannot be
promoted to a Mini 5 Pro control surface.

## Dependency order

The evidence dependencies are:

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
official account eligibility
  -> support/version populated
  -> fresh privacy-minimized inventory
  -> genuine type-6 item and baseline
  -> bounded same-item transition/readback/restore
  -> onboard status + independent motor-on RF A-B-A
```

Failure or `UNKNOWN` at a gate does not authorize trial-and-error at the next gate.
