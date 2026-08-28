# V2.3 packaged artifact audit

Date: 2026-08-28 (Asia/Shanghai)
State: **offline only; not copied, installed, attached or executed on a device**

V2.2 is revoked. The exact rejecting report is
[V2_2_REJECTION.md](V2_2_REJECTION.md), SHA-256
`6dcf39e1fcb7db274f192371bf38be7f6e609276dc733cea62024ccf4601b3f7`.

## Sealed V2.3 artifact

```text
APK dist/FindUAS-JVMTI-EID-Route-Resolver-V2.3-0.1.0-offline-unadmitted-arm64-v8a.apk
bytes 29019
SHA-256 49d5d1d3b6e2dcb72b23f48b688effb2be3f320bec6997a9dcb15779904156c2

packaged lib/arm64-v8a/libfinduas_eid_route_resolver_v2_3.so
bytes 48104
SHA-256 f57c371b22c1540d13f096fe20fda71148e30881b67aa6bff3401188be3fbb1b

signer certificate SHA-256
37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224
```

## Fixed findings and packaged evidence

- The compiled route constructs a distinct three-entry, 24-byte-per-entry narrow identity input
  holding only base/path/length. Source and packaged canary audits reject adding runtime-phdr data;
  exact whole-function hashes also lock the route, identity verifier, maps reader, file-header
  check, whole-file/non-W comparator, epoch admission and runtime-header finalizer.
- Exact AArch64 call order is maps-A, file-only Ehdr/phdr, whole SHA plus all original
  `PF_W == 0` runtime/file bytes, maps-B and snapshot equality. Only the success edge reaches the
  unique linker epoch admission call.
- The admission helper clears its magic, performs the unique add/sub recheck, and writes magic only
  on zero. The finalizer checks the magic before the first runtime Ehdr and phdr `memcmp`; segment,
  build-ID and symbol work follows.
- Identity, epoch and finalizer failure edges each set a fail-closed status, close all target
  handles and jump over symbol and dormant target routes.
- The private exception gate remains a zero word in an R--/non-X load with no relocation and one
  check site. It dominates the only dormant helper call.

## Negative tests

Host tests pass for all exact file/hash/header profiles and mutations, source/device/inode/offset/
coverage/snapshot failures, split VMAs, all relevant VMAs made writable, one first-load page made
`rwxp`, high original-nonwritable `PT_LOAD #6` made `rw-p`, zero-device `fstat` and maps fixtures,
and runtime non-writable byte mutation. The packaged audit passes exact profile-table, CFG,
exception-gate, imports/exports, ZIP/manifest/signer and zero-send checks.

Two clean end-to-end builds were byte-identical under `scripts/reproducibility_check.sh`. The
expected terminal result remains `EXCEPTION_BOUNDARY_UNPROVEN`.
