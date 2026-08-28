# Hypotheses and unknowns

Every hypothesis below is testable and remains separate from factual findings.

## H-01 — product-139 live ownership

- Known facts: current DJI Fly 1.21.10 maps WA150/product candidate 139 to UAV139 handlers;
  product-139 static EID receiver is `0x92`.
- Hypothesis: the connected Mini 5 Pro live DJI Fly session uses the same product owner and no
  runtime HostID override replaces `0x92`.
- Distinguishing evidence: exact live package/profile match plus read-only current subject,
  productId/deviceId, characteristics, HostID, and receiver tuple from the initialized owner.
- Current state: `UNKNOWN`.
## H-02 — private-owner France-EID GET support

- Known facts: the current static handler and ACK converter are exact; two artificial USB routes
  returned no canonical reply.
- Hypothesis: the already initialized DJI Fly owner/session can reach the product-139 France-EID
  handler even though artificial routes cannot.
- Distinguishing evidence: one same-owner GET with canonical raw `[result=0,state]`, exact route/
  epoch binding, and proven terminal quiescence.
- Current state: `NOT ADMITTED`; no request sent.

## H-03 — meaning of typed Java `false`

- Known fact: the native converter can fold nonzero protocol result into Boolean false.
- Hypothesis alternatives: false may mean canonical off, or a protocol/application failure.
- Distinguishing evidence: raw same-owner ACK with explicit `result==0` and state byte.
- Current state: `UNKNOWN`.

## H-04 — stable control via genuine type-6 `RID_UNLOCK`

- Known facts: signed account/FC-bound type 6 exists in public MSDK schema, has EU/China levels,
  and matching enabled license can produce `NO_BROADCAST` in static delegate logic.
- Hypothesis: a genuine, eligible Mini 5 Pro license can be inventoried, enabled/disabled, restored,
  reflected in working status, and observed over RF.
- Missing: server eligibility, genuine record, live support/version, exact route, current baseline,
  FC acceptance, rollback, and independent RF A-B-A.
- Current state: `UNKNOWN`.

## H-05 — reason for legacy inventory timeout

- Known facts: two artificial legacy queries timed out while adjacent area/country controls worked.
- Competing hypotheses: wrong FlySafe version, unopened support gate, wrong route/session, wrong
  payload for the negotiated version, wrong endpoint, or no response under current lifecycle.
- Distinguishing evidence: passive support/version pushes or exact current owner/session query
  construction before any inventory request.
- Current state: no hypothesis selected.

## H-06 — motor-state transition and `0x11/0x1C`

- Known facts: no strict candidate in motors-off windows; independent receiver-visible RID began
  after operator-initiated motor start.
- Hypotheses: the push requires official subscription, a motor/flight state transition, valid GPS/
  operator position, or a combination.
- Distinguishing evidence: time-aligned passive onboard status and independent receiver capture
  across powered, motors-off, motor-start, and stable-position stages.
- Current state: `UNKNOWN`.

## H-07 — login-dependent 30/50 m effective restriction

- Known facts: configured limits read 500 m/5000 m/disabled; account state has multiple layers;
  public logic has effective/reason status separate from stored configuration.
- Hypothesis: an unverified/not-logged-in runtime layer can enforce 30 m height / 50 m distance
  without overwriting configured values.
- Missing: confirmed active restriction during the same session and read-only effective/reason
  evidence.
- Current state: `UNKNOWN`; no debug switch found.

## H-08 — exact owner of the effective restriction

- Candidate owners: server-validated account state, FC-synchronized UID, activation/authorization,
  FlySafe/runtime state, or a product-specific combination.
- Distinguishing evidence: controlled login-state transitions with configuration unchanged and
  effective-reason/status captured.
- Current state: `UNKNOWN`.

## H-09 — EU C0 RID policy status `0x03`

- Known facts: static hash registration exists; both fixed F7 probes returned status `0x03`; known
  hash controls succeeded.
- Competing hypotheses: missing registration on the live target, product/runtime gate, unsupported
  route, or explicit rejection.
- Distinguishing evidence: exact enum mapping or same-owner key-value metadata result from a
  matching live build.
- Current state: `UNKNOWN`; no F8/F9 baseline exists.

## H-10 — RC 2 SDR selector value 5

- Known facts: both endpoints read 5; legacy force-FCC writes 2.
- Hypotheses: 5 is a modern auto/regulatory state, a product-specific selector, or another mode.
- Distinguishing evidence: current O4 handler/table mapping and calibrated, contained state/RF
  correlation. UI graph alone is insufficient.
- Current state: `UNKNOWN`.

## H-11 — final country authority and persistence

- Known facts: application strategy, FC, Sky, Ground, RC policy, and platform country storage are
  separate; FC/Sky loops were reversible in-session.
- Hypothesis: one layer becomes authoritative after reconnect/reboot and rewrites the others.
- Distinguishing evidence: read-only multi-surface snapshots across controlled lifecycle events,
  without fighting the synchronizer.
- Current state: `UNKNOWN`.

## H-12 — WA150 `0802` RID ownership

- Known facts: `0802` is the strongest main-system candidate; `2603` is GNSS; `0806/DONG` is a
  protected communication-related secondary module.
- Hypothesis: primary RID behavior resides in `0802`, possibly with supporting radio work in
  `0806`.
- Distinguishing evidence: legitimately verified plaintext/code ownership or a documented symbol/
  task/driver path. Ciphertext strings or module number alone are insufficient.
- Current state: `UNKNOWN`.

## H-13 — first-packet ADB public key

- Known facts: live host CNXN receives no reply; adjacent `adbd` AUTH switch handles a public-key
  packet independently and may call key confirmation.
- Hypothesis: an `AUTH/RSAPUBLICKEY` sent as the first ADB packet may produce an authorization
  prompt despite CNXN drop.
- State effect: may display a prompt and persist a key.
- Current state: unexecuted `HYPOTHESIS`, not a result or general workaround.

## H-14 — adjacent `adbd` parity with live v07

- Known facts: adjacent binary behavior exactly explains the live trace shape.
- Hypothesis: live `07.00.0100` uses the same CNXN production gate implementation.
- Distinguishing evidence: exact live binary/file hash or a device-side read-only build identity.
- Current state: `INFERENCE`, not exact proof.

## H-15 — v0.10 live compatibility

- Known facts: exact offline APK passed artifact-specific audit; it reads only its own process and
  fixed read-only system/package surfaces.
- Hypothesis: it can run to `COMPLETE` on the live RC 2 and produce the expected exact package/ABI/
  Binder/ART gate report without side effects beyond explicit clipboard/Settings actions.
- Distinguishing evidence: complete redacted `finduas-rid-probe/v0.10-schema-1` device result.
- Current state: never copied/installed/run.

## H-16 — V2.3 identity gate correctness

- Known facts: project host tests/audit report the V2.2 corrections; two builds are identical;
  immutable-zero gate keeps dormant calls unreachable.
- Hypothesis: an independent adversarial audit will find no remaining P0–P3 identity/audit flaw.
- Distinguishing evidence: a new independent audit of exact APK/SO bytes and hostile mutations.
- Current state: no such post-fix independent report.

## H-17 — target static-libc++ exception coherence

- Known facts: minimal NDK catch-all imports more than the initially proposed three symbols; DJI
  DSOs allow interposition and contain separate static-libc++ behavior.
- Hypothesis: exact live GOT/PLT ownership might be coherent enough for a narrowly bounded target
  object route.
- Distinguishing evidence: exact loaded-library identity and runtime binding proof for personality,
  throw/catch, TLS globals, terminate, unwind/resume, and cleanup.
- Current state: `UNKNOWN`; immutable-zero exception gate remains.

## H-18 — route epoch closure

- Known facts: some datalink mutations are worker-serialized; all ProductMgr/HardwareLayer writers
  are not closed.
- Hypothesis: complete nested-safe mutation hooks plus a shared route gate can create a stable
  current-owner read epoch.
- Distinguishing evidence: exhaustive writer inventory, lock-order proof, coverage telemetry, and
  adversarial lifecycle tests.
- Current state: design only.

## H-19 — raw GET terminal quiescence

- Known facts: `SessionMgr::IsSending` can conservatively test a unique tuple but is not
  handle-specific; CallbackStopper lacks a public read predicate.
- Hypothesis: exact locked handle/Stopper membership hooks plus a normal worker-tail fence can prove
  no pending or late callback remains.
- Distinguishing evidence: exact implementation and interleaving tests covering ACK, timeout,
  cancellation, disconnect, and late callback.
- Current state: host model only; live witnesses absent.

## H-20 — Remote ID region behavior

- Known facts: country/area state and RID control surfaces are separate; region experiments lacked
  an independent receiver.
- Hypothesis: different region/account/permit combinations alter which RID standard/data/timing is
  emitted.
- Distinguishing evidence: synthetic or authorized real test matrix with the same aircraft state,
  exact onboard status, and independent receiver decode evidence. Country readback alone is not
  sufficient.
- Current state: `UNKNOWN`.
