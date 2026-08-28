# FindUAS EID route resolver V2.3 — offline, unadmitted carrier

> **DO NOT INSTALL OR ATTACH**

Status: **NOT ADMITTED**. The V2.2 defects are corrected in source, but V2.3 has no independent
post-fix live audit and has never been run on RC 2.

This is a work-only AArch64 JVMTI review artifact for the exact DJI Fly 1.21.10 native samples in
the parent research directory. It is not an EID/RID reader or Remote ID switch and has never been
copied to or run on the RC 2.

## V2.2 is revoked

V2.2 APK SHA-256
`7aa794ff8611582fd7cf27808a9d9eb11c44e307889d615d0511c100522845fb` is rejected and must not be
installed or attached. Its independent audit is preserved byte-for-byte as
[V2_2_REJECTION.md](V2_2_REJECTION.md), SHA-256
`6dcf39e1fcb7db274f192371bf38be7f6e609276dc733cea62024ccf4601b3f7`. V2.3 is a new package,
native library and artifact; it does not overwrite or rehabilitate V2.2.

## V2.3 corrections

V2.3 preserves the fixed-zero exception gate and zero-send boundary, and fixes every V2.2 finding:

1. The pre-epoch identity verifier receives a deliberately narrow 24-byte record containing only
   load bias, path pointer and path length. Its type has no runtime-phdr field. It validates the
   open file's exact ELF header/program headers, whole-file SHA-256 and every original
   `PF_W == 0` file/runtime byte, then completes post-`fstat`, maps-B equality and fd cleanup.
2. Only after that verifier returns success does a unique linker add/sub epoch recheck write the
   private identity-admission magic. The finalizer requires that magic before it first dereferences
   runtime ELF memory, compares the runtime ELF header and all seven program headers to the exact
   compiled profile, parses segments/build ID, or permits symbol resolution.
3. Both maps snapshots reject every currently writable VMA intersecting an original
   `PF_W == 0` `PT_LOAD`, including `rw-p` and `rwxp`. The byte comparator independently requires
   readable, non-writable coverage.
4. File identity now requires nonzero `st_dev`, `st_ino`, link count, regular-file type, exact size,
   `O_NOFOLLOW`, stable pre/post state, and exact maps device/inode/offset binding.

The current `EXTRACTED_ELF_V1` profile still rejects `apk!/`, deleted, memfd, anonymous, relative,
empty, truncated, symlinked or partial sources. Three whole files totaling 107,718,672 bytes are
hashed exactly. The second maps snapshot and linker epoch recheck are mandatory; every failure is
closed before runtime-header parsing, symbol resolution or any dormant DJI-owned call.

## Zero-send boundary

- no DUML, `JNIRawData`, `JNIKeyValue`, GET, SET, listen, observer, socket, Binder, localhost,
  process execution, property access or filesystem write;
- no Android permission, shared UID, component, packaged DEX, constructor table, embedded DEX/ZIP
  or secondary ELF;
- no plain `dlopen`, `RTLD_DEFAULT`, second DJI library load, ZIP/DEFLATE parser, allocation,
  `mmap`, `realpath`, `/proc/self/mem` or root fallback;
- the exception gate is immutable zero, so exact identity/symbol preflight still terminates at
  `EXCEPTION_BOUNDARY_UNPROVEN`; dormant target-owned calls remain unreachable.

## Sealed artifact

```text
package: com.finduas.jvmti.eidroute.v23
version: 0.1.0-offline-unadmitted (1)
ABI: arm64-v8a only
APK: FindUAS-JVMTI-EID-Route-Resolver-V2.3-0.1.0-offline-unadmitted-arm64-v8a.apk
APK bytes: `29019`
APK SHA-256: `49d5d1d3b6e2dcb72b23f48b688effb2be3f320bec6997a9dcb15779904156c2`
packaged SO bytes: `48104`
packaged SO SHA-256: `f57c371b22c1540d13f096fe20fda71148e30881b67aa6bff3401188be3fbb1b`
signer certificate SHA-256: 37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224
```

## Offline verification

```sh
sh scripts/run_host_tests.sh
sh scripts/build_and_audit.sh
sh scripts/reproducibility_check.sh
```

The host suite includes exact target hashes/header/phdrs, SHA boundary vectors and mutations,
split maps, device/inode/offset/coverage/source failures, all-VMAs-writable failure, a single
original-non-writable page changed to `rwxp`, high `PT_LOAD #6` changed to `rw-p`, zero-device
`fstat` and maps fixtures, snapshot drift, and non-writable byte mutation. The packaged audit binds
the exact AArch64 narrow-input canary, internal maps-A/file-header/hash/maps-B order, epoch-admission
block, first runtime Ehdr/phdr comparisons, fail-close edges, fixed-zero gate, and exact
imports/exports/manifest/ZIP/signer inventory.

See [LIVE_ADMISSION.md](LIVE_ADMISSION.md), [ZERO_SEND_CONTRACT.md](ZERO_SEND_CONTRACT.md),
[ARTIFACT_AUDIT.md](ARTIFACT_AUDIT.md), and the parent research reports.
