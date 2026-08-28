# V2.2 packaged artifact audit

Date: 2026-08-28 (Asia/Shanghai)
State: **offline only; not copied, installed, attached or executed on a device**

## Sealed artifact

```text
APK
dist/FindUAS-JVMTI-EID-Route-Resolver-V2.2-0.1.0-offline-unadmitted-arm64-v8a.apk
bytes 29019
SHA-256 7aa794ff8611582fd7cf27808a9d9eb11c44e307889d615d0511c100522845fb

packaged lib/arm64-v8a/libfinduas_eid_route_resolver_v2_2.so
bytes 47512
SHA-256 8059d9c5544fb11d0c4be37e8595adbbac92322c7da42377f23b2eae83d97c12

signer certificate SHA-256
37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224
```

Two clean end-to-end builds were byte-identical. The original V2.1 APK remains 16,731 bytes with
SHA-256 `7f0159619f89f7c6a9849b1028003a1070d97988838da7a6ef027e09626ada0d`.

## Whole-file identity evidence

The packaged native profile table was parsed back from the final ELF and compared to independent
local target samples. Each of the three contiguous 536-byte entries exactly contains:

- basename relocation;
- 20-byte GNU build ID;
- fixed `EXTRACTED_ELF_V1` source kind;
- exact file size and 32-byte whole-file SHA-256;
- exact 64-byte ELF header;
- exact `e_phnum == 7`, zero reserved bytes and all seven 56-byte program headers.

The route's packaged AArch64 control flow was also checked at fixed RVAs. The sole whole-file
identity call is followed by a `CBZ` success edge; its failure edge writes status 16, closes all
target `RTLD_NOLOAD` handles and branches over module finalization, symbol resolution and the
dormant target route. The sole post-identity finalizer has its own fail-close edge before the sole
symbol resolver call. The private exception gate is a zero word in an original read-only,
non-executable `PT_LOAD`, has no relocation, has one check call and uniquely dominates the only
dormant target-route helper call.

Pre-identity module discovery does not dereference `dlpi_phdr`: it records only unique path/base/
phdr-pointer/count and linker counters. Runtime header/build-ID/segment reads occur only after the
whole-file/maps/non-writable-memory gate succeeds.

## Binary boundary

- APK inventory is exactly manifest/resources/app metadata plus one compressed AArch64 ELF; no DEX.
- Manifest has no permission, component or shared UID and has `hasCode=false`.
- Only exported symbol: `Agent_OnAttach`.
- Needed DSOs: `liblog.so`, `libdl.so`, `libc.so`.
- Exact read/loader imports include `__openat_2`, `__read_chk`, `__pread64_chk`, `fstat`, `close`,
  `getpagesize`, `dl_iterate_phdr`, `dlopen`, `dlsym`, `dladdr` and their bounded support functions.
- No socket, Binder, property, process, allocation, write, mmap, ZIP/DEFLATE, DJI GET/SET/listen/
  send or observer import/source route exists.
- The sole source `dlopen` expression is `RTLD_NOW | RTLD_NOLOAD`; `RTLD_DEFAULT` is absent.

The four ELF magics in the packaged SO are the carrier header plus the three exact 64-byte target
profile headers; there is no embedded secondary ELF payload.

## Host negative tests

`scripts/run_host_tests.sh` passes and covers:

- SHA-256 empty/`abc` and 55/56/63/64/65-byte padding boundaries plus constant-time digest compare;
- all three exact 107,718,672 target bytes and exact headers/program headers;
- first, middle and final byte flips, including a tail mutation that leaves build-ID data intact;
- exact extracted path plus `apk!/`, deleted, memfd and relative-path rejection;
- split VMA success and device, inode, offset, private/readable permission and coverage-gap failures;
- explicit rejection of a deleted relevant map and the wrong `p_offset == p_vaddr` assumption for
  high `PT_LOAD #6`;
- missing final newline, overlong maps line and snapshot drift;
- current non-writable runtime/file equality, byte mutation failure, writable segment exclusion and
  high-segment file-offset-to-runtime-address translation.

`scripts/build_and_audit.sh` and `scripts/reproducibility_check.sh` both pass without an audit
warning.

## What this does not prove

This is not live admission and not a RID control. It does not prove target static-libc++ exception/
personality coherence, the archived ART profile on the live controller, a global connection mutation
epoch, callback quiescence, GET semantics or SET restoration. The fixed exception gate remains zero
and the expected identity-success terminal result remains `EXCEPTION_BOUNDARY_UNPROVEN`.

The archived RC 2 `0205` `libart.so` exact profile now proves that `Runtime::AttachAgent()` retains a
successful agent and exact `Agent::Unload()` does not close the native library. V2.2 deliberately did
not add a self-`RTLD_NOLOAD` pin: future mapping retention should use that characterized MappingLease
only after a live whole-file/maps/function-range probe matches
`../eid_agent_mapping_lease_audit_20260828.md`.
