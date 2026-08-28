# Live admission — intentionally not satisfied

This V2.1 artifact is **DO NOT INSTALL OR ATTACH**. Its exception gate is compiled to zero and has
no input or setter. Satisfying future research gates does not change this binary; a separately
versioned source review and artifact would be required.

## Current blockers

1. **Target exception/personality boundary:** `SDKFrameworkCore::GetKey()` copies a target-owned
   string and constructs a heap-backed 12-byte prefix vector. Allocation can throw. No compatible,
   narrowly caught exception boundary has been proven across the DJI static-libc++ objects and the
   carrier.
2. **Runtime whole-file identity:** the offline manifest verifies exact whole-file SHA-256, but the
   current in-process carrier verifies build IDs, mapping ownership, RVAs and code signatures only.
   A live build must independently bind the loaded objects to the exact complete files or provide
   an equally strong relocation-aware identity proof.
3. **Caller/attach gate:** V0 no-op attach and V1 semantic-anchor-only artifacts have not passed the
   complete target-firmware admission sequence on this RC 2.
4. **Pointer-read boundary:** every future heap/private-field read needs a bounded, proven readable
   mapping contract before dereference; exact owners reduce races but do not make arbitrary pointer
   corruption safe.
5. **Connection epoch:** the normal datalink add/remove path is on the same SDK worker, but the
   ProductMgr listener producer, detector create/delete path and complete HardwareLayer mutation
   surface are not. No official monotonic route token is known. A worker-tail sample is therefore
   only `STABLE_OBSERVED`; future requests require reviewed `active_mutators`, `connection_epoch`
   and shared reader/writer `route_gate` coverage.
6. **Terminal lifetime:** callback thread, duplicate/late callback quiescence, agent mapping
   lifetime, completion wakeup, timeout, and final route recheck are not closed.

## Required sequence before any GET review

1. Complete v0.8 capability snapshot, then separately review and run V0; restart DJI Fly normally.
2. Only after a clean V0 result, separately review V1 and prove the exact two semantic anchors and
   ClassLoader topology.
3. Close the exception/personality and runtime whole-file identity blockers in a new route-only
   artifact. It must still have no GET/SET/listen/send.
4. Run that new route-only artifact once, obtain only numeric diagnostics, restart DJI Fly, and
   confirm no crash or connection-state change.
5. Independently design a new read-only GET artifact with a tail-inserted SDK-worker closure,
   caller-owned completion gate, raw result visibility, terminal quiescence, and post-ACK route
   recheck. Do not reuse this APK by flipping a byte or hidden option.

## Mutation remains a separate project phase

No SET is admitted by any route-only or GET result. A future mutation review still requires an
applicable regional control (France EID is not global), raw baseline, one SET, immediate raw GET
readback, unconditional bounded restoration, final GET, and independent motor-on RF validation.
Software must never start the motors.
