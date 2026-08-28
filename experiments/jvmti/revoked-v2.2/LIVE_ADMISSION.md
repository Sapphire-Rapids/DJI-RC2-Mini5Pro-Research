# Live admission — intentionally not satisfied

This V2.2 artifact is **DO NOT INSTALL OR ATTACH**. Offline whole-file identity success does not
admit a live attach, target call, GET or SET. The private exception gate is compiled to zero and has
no input or setter.

## What this version closes offline

- The exact current profile admits only three extracted regular ELF files with fixed size,
  whole-file SHA-256, ELF header, seven program headers and build ID.
- The open fd is bound to every file-backed runtime `PT_LOAD` through two bounded maps snapshots,
  exact device/inode/offset/private/readable checks and linker epoch stability.
- All original non-writable file bytes are compared to current memory before any runtime program
  header, build-ID, symbol or dormant target-owned route use.
- Every failure terminates before symbol resolution. Even identity success terminates later at
  `EXCEPTION_BOUNDARY_UNPROVEN`.

## Current blockers

1. **Target exception/personality boundary:** the three static-libc++ DJI runtimes do not yet have
   proven live GOT/PLT exception coherence. Whole-file correctness does not solve relocated
   writable runtime state.
2. **Caller/attach gate:** V0 no-op attach and V1 semantic-anchor-only artifacts have not passed the
   complete target-firmware sequence on this RC 2.
3. **Live MappingLease admission:** the archived RC 2 `0205` ART is now exactly characterized:
   `libart.so` SHA-256 `3ec3d232ad7f4099c42f014b87658be47e83d7e21a7a053fb16c4d146103745d`
   (build ID `5f839ecc60b9ae39764305b5fee6ed37`) retains successful agents in
   `Runtime::agents_`, and its exact `Agent::Unload()` does not close the native mapping. That is a
   usable future MappingLease mechanism only after a read-only live probe proves the same ART file,
   maps inode/offsets and exact function ranges. V2.2 does not perform that probe and must not add a
   speculative self-`dlopen` pin.
4. **Pointer-read boundary:** future live owner/private-field reads still need bounded readable-map
   contracts and lifecycle ownership.
5. **Connection epoch:** ProductMgr/detector/HardwareLayer writer coverage and a shared/unique route
   gate remain incomplete.
6. **Terminal callback lifetime:** registration completion, callback return/in-flight zero,
   pending/Stopper absence and final worker-tail route recheck are not yet closed.

## Required sequence before any GET review

1. Collect the complete v0.8 capability snapshot, then separately review/run V0 and restart DJI Fly.
2. Review/run V1 only after a clean V0 result.
3. Independently review this exact V2.2 source, packaged control flow and hashes.
4. Prove the exact ART MappingLease profile live and resolve exception/personality coherence in a
   new version; do not patch this artifact's fixed gate.
5. Only then consider a one-shot route-only live preflight. Restart DJI Fly after it and verify no
   crash or connection-state change.
6. Design a separate read-only GET with a tail-inserted SDK-worker closure, raw result visibility,
   terminal quiescence and post-ACK route recheck.

No SET follows automatically from any route-only or GET result. Mutation still requires baseline,
one write, immediate raw readback, unconditional restoration, final readback and independent
motor-on RF verification. Software must never start the motors.
