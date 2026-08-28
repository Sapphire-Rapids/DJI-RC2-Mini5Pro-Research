# Live admission — intentionally not satisfied

V2.3 is **DO NOT INSTALL OR ATTACH**. V2.2 is separately revoked by
[V2_2_REJECTION.md](V2_2_REJECTION.md). Offline whole-file identity success does not admit a live
attach, target call, GET or SET. The private exception gate is compiled to zero and has no input or
setter.

## Closed offline in V2.3

- The pre-epoch verifier's input type contains only base/path/length; it cannot name runtime phdr.
- File-only Ehdr/phdr, exact SHA-256, all original `PF_W == 0` runtime/file bytes, post-`fstat`,
  maps-B equality and fd accounting succeed before the linker epoch admission call.
- Runtime Ehdr/phdr memory is first dereferenced by the admission-gated finalizer after the unique
  add/sub epoch recheck succeeds.
- Original non-writable loads fail if any covering VMA is currently writable; `rw-p`, `rwxp`, a
  one-page permission mutation and high `PT_LOAD #6` are negative fixtures.
- Regular file, nonzero device/inode/link count, exact size, `O_NOFOLLOW` and dual exact maps
  device/inode/offset/private/readable checks fail closed.
- Every failure terminates before symbols. Success still terminates at
  `EXCEPTION_BOUNDARY_UNPROVEN` before every DJI-owned call.

## Still blocking live admission

1. Target static-libc++ exception/personality coherence remains unproven.
2. V0 no-op attach and V1 semantic-anchor-only artifacts have not completed the target-firmware
   sequence on this RC 2.
3. The archived `0205` ART profile conditionally supports MappingLease, but a read-only live probe
   must first match exact ART file SHA/build ID, maps identity and function ranges. V2.3 performs no
   self-`dlopen` pin or speculative live probe.
4. Future pointer reads need bounded readable-map and lifecycle ownership contracts.
5. Product/detector/HardwareLayer connection epoch coverage and terminal callback quiescence remain
   incomplete.

No GET or SET follows from this artifact. Any future experiment requires a new version and an
independent review. Software must never start motors.
