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
  and the preserved delegate design maps a matching enabled license to `NO_BROADCAST`. That app-side
  branch only mutates an SDK status object; it sends no Key/native/DUML command. Current native
  inventory/set-enable endpoints are `0x11/0x11` and `0x11/0x12`, with product-139 receiver `0x92`.
- Hypothesis: a genuine, eligible Mini 5 Pro license can be inventoried, enabled/disabled, restored,
  consumed by the aircraft-side RID broadcaster, and observed over RF.
- Missing: server eligibility, genuine record, live support/version, exact route, current baseline,
  FC acceptance, aircraft-side consumer, rollback, and independent RF A-B-A.
- Next discriminator: a bounded read-only modern V3/V4 inventory query through the existing system
  Binder. Only a canonical response containing a genuine type-6 record can admit a later same-item
  baseline/readback/restore experiment.
- Current state: `UNKNOWN`.

## H-05 — reason for legacy inventory timeout

- Known facts: two artificial legacy queries timed out while adjacent area/country controls worked.
- Competing hypotheses: wrong FlySafe version, unopened support gate, wrong route/session, wrong
  payload for the negotiated version, wrong endpoint, or no response under current lifecycle.
- Distinguishing evidence: passive support/version pushes or exact current owner/session query
  construction before any inventory request.
- Current state: no hypothesis selected.

## H-06 — motor-state transition and `0x11/0x1C`

- Known facts: A-024's third-party Binder listener was accepted and ran 30 seconds but received zero
  callbacks while an independent detector confirmed RID after operator-initiated motor start.
- Hypotheses: the push requires official subscription, a motor/flight state transition, valid GPS/
  operator position, or a combination.
- Distinguishing evidence: only an official in-process observer or a different validated onboard
  health source, time-aligned with independent RF. Repeating the same Binder listener cannot
  discriminate the hypotheses.
- Current state: `NEGATIVE` for the tested Binder listener as a truth source; official owner behavior
  remains `UNKNOWN`.

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

## H-21 — NLD C0 causal mechanism

- Known facts: NLD `2.0.0.6` obtains server-controlled WireGuard configuration online, relaunches
  DJI Fly under that route, and schedules automatic stop 25 seconds after tunnel UP; its Java C0
  path does not write a visible 500 m or speed value. Actual route breadth and lifetime vary with
  the server response and lifecycle.
- Competing hypotheses: the claimed effect is caused by the routed DJI backend response, the
  NLD-hosted DJI Fly 1.21.4 APK, or a combination.
- Distinguishing evidence: signer/hash comparison of the hosted APK plus a privacy-redacted route/
  host and DJI Fly startup-response comparison under an authorized license.
- Current state: `UNKNOWN`; routing alone is not evidence of interception or response modification.

## H-22 — NLD opaque payload and packaged-profile equivalence

- Known facts: the visible profiles are byte-identical to FreeFCC but have no found loader; the
  reachable FCC path decodes an online or native-offline blob and sends through native DUSS. The
  authenticated envelope, entitlement verification, cache format, decrypted JSON schema, and DUML
  framing are closed, but the package contains no real encrypted command object.
- Hypothesis: the opaque blob may decode to all or part of the visible FreeFCC sequence.
- Distinguishing evidence: a legitimately obtained online response or offline blob in its authorized
  device context, decoded offline and compared with the pinned profiles; any live observation must
  avoid opening a second RCLink client.
- Current state: `UNKNOWN`; file identity is not runtime reachability.

## H-23 — WA150 firmware-resident RID controller

- Known facts: Drone-Hacks documents a firmware-resident CFC with narrow runtime commands on older
  products; the current client has firmware/job/parameter machinery; no Mini 5 Pro CFC, RID command,
  software product, or RID job was found.
- Hypothesis: if WA150's authoritative RID policy/output owner is firmware-resident, a similarly
  narrow controller could provide explicit state, one bounded transition, readback, and restoration.
- Distinguishing evidence: verified WA150 plaintext and ownership path, exact policy/output hook,
  loader/signature acceptance, a recovery route independent of the modified path, and synchronized
  motor-on onboard/RF A-B-A.
- Current state: `UNKNOWN`; architectural precedent is not target applicability or flash admission.

## H-24 — separate synthetic OpenDroneID source（C-129）

- Known facts: a DJI aircraft does not expose every standards message as a free-form setting;
  OpenDroneID supplies public encoders and external Linux/embedded transmitter precedents; the
  existing Mac administrator lab already has a no-RF lease/checklist/lockout state machine.
- Hypothesis: a separately reviewed external source adapter can provide synthetic Basic ID,
  Location, System, Self ID, Operator ID, status, and bearer combinations for detector compatibility
  testing without modifying WA150 firmware or real identity/account data.
- Distinguishing evidence: exact hardware/firmware identity, source configuration readback,
  time-bounded transmit/stop proof, independent receiver decode, restart-no-resume behavior, and a
  privacy-redacted test matrix in a controlled RF environment.
- Current state: architecture candidate only. The current Mac build has no RF backend and must not
  present dry-run state as transmitted or received evidence.

## H-25 — live Mini 5 Pro admits conditional `UOMV1`

- Known facts: exact current native code adds `UOMV1` only after runtime function discovery reports
  function ID `0x6C` with the required flag; the module then exposes a real-name status GET and Sync
  action, but no setter (C-131/C-132).
- Hypothesis: the current Mini 5 Pro session may report this capability and make the official
  privacy-reduced status key available.
- Distinguishing evidence: same-owner read-only function inventory or official key-existence result,
  followed only if admitted by a masked enum GET that distinguishes key absence from
  `UNSUPPORTED`.
- Current state: `UNKNOWN`; static product-139 identity does not establish live admission, and no
  raw `0x11/0xD1` probe is authorized by this hypothesis.

## H-26 — live Mini 5 Pro admits `RidCaptureV1`（C-133、C-134）

- Known facts: exact current native code maps raw function-discovery ID `0x37` to the nine-entry
  `RidCaptureV1` bundle and maps adjacent ID `0x38` to unofficial-battery authentication. The SDK's
  `0x00/0xB8` transport downloads a general function inventory and may replay cached state; it is not
  an RID-specific one-bit getter.
- Hypothesis: the current Mini 5 Pro session may report ID `0x37` with the required version/flag and
  expose some or all official RID keys through the same owner already initialized by DJI Fly.
- Distinguishing evidence: an official same-owner read-only function-inventory or key-existence
  result bound to the exact current session, with cache provenance separated from a fresh device
  response. Only after admission may a privacy-reduced getter be considered.
- Current state: `UNKNOWN`. This hypothesis does not authorize a handcrafted `0x00/0xB8` request,
  reuse command `0x11/0x37`, infer admission from product number, or enable any setter/action.

## H-27 — Mini 5 Pro exposes `rid_ctrl_enable_0`（C-136--C-138）

- Known facts: SKYROVER `1.2.0` independently exposes a Boolean GET/SET/Listen
  `RIDCtrlEnable`, maps it to FC parameter `rid_ctrl_enable_0`, and uses hash `0x3CBD864F` through
  FLYC F7/F8/F9. Its application probes GET capability after connection before showing the switch.
  DJI Fly `1.21.10` does not contain the same two names.
- Hypothesis: the current Mini 5 Pro FC may still expose the parameter even though DJI Fly does not
  register a wrapper for it.
- Distinguishing evidence: from the installed RC 2 client, one fixed `03/F7` response for hash
  `0x3CBD864F`; on success, one fixed `03/F8` response whose echoed hash, width, and Boolean value
  match the F7 metadata. A one-byte nonzero F7 response rejects the transfer-by-name hypothesis for
  this current product/session without issuing F9.
- Follow-on if positive: capture baseline, write the opposite Boolean once with F9, confirm by F8,
  restore the captured baseline, and confirm again. Reconnect persistence and motor-on independent
  RF A-B-A are separate observations.
- Current state: direct legacy routes are `NEGATIVE` for target F7 metadata with same-session
  positive controls (C-141). Installed A-024 then showed that both tested third-party Binder routes
  fail the known-height F7 positive control with `ECode 1` (C-145), so code correctly did not send
  target F7/F8/F9. This hypothesis is no longer actionable through the known generic attach routes.
  It remains open only for a materially different official in-process owner/authenticated route or
  a verified WA150 handler; RF effect has never been tested.
