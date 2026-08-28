# FindUAS EID route resolver V2.2 — revoked source record

> **REJECTED — DO NOT INSTALL OR ATTACH**

Status: **RETRACTED**. The source and audits are retained only to preserve the three defects that
caused independent rejection; V2.3 does not rehabilitate this artifact.

This is a work-only AArch64 JVMTI review artifact for the exact DJI Fly 1.21.10 native samples in
the parent research directory. It is not an EID/RID reader and is not a Remote ID switch. It has
never been copied to or run on the RC 2.

## What V2.2 adds

V2.2 preserves V2.1's fixed-zero exception gate and adds the current-build
`EXTRACTED_ELF_V1` whole-file identity gate. After unique `dl_iterate_phdr` discovery and
`RTLD_NOW | RTLD_NOLOAD` pins, but before symbol resolution or any dormant target-owned call, it:

1. admits only absolute extracted-library paths; `apk!/`, deleted, memfd, anonymous, relative,
   empty and truncated sources fail closed;
2. opens each already-loaded target with `O_RDONLY | O_CLOEXEC | O_NOFOLLOW`, requires a regular
   file with nonzero link/inode and the exact compiled size, and compares pre/post `fstat` state;
3. computes the exact whole-file SHA-256 for all 107,718,672 target bytes using internal bounded
   code and a constant-time digest comparison;
4. parses `/proc/self/maps` with fixed limits, binds every file-backed `PT_LOAD` page to the open
   fd's device/inode and exact page offset, and requires readable private mappings;
5. compares every original `PF_W == 0` `PT_LOAD.p_filesz` byte to its current runtime byte,
   including each library's nontrivial high `PT_LOAD #6` mapping;
6. compares exact file/runtime ELF headers and all seven program headers, takes a second maps
   snapshot, and rejects any relevant VMA or linker add/sub epoch drift;
7. closes every target/maps fd on one bounded cleanup path and emits numeric diagnostics only.

Only after identity succeeds does the carrier parse the already-validated runtime program headers,
verify the exact GNU build IDs and continue V2.1's fixed symbol/RVA/signature preflight. The private
exception gate is still immutable zero, so the reviewed artifact then terminates at
`EXCEPTION_BOUNDARY_UNPROVEN`. No target-owned string, CacheKey, owner, map, Characteristics or
protocol call is reachable.

## What it does not do

- no DUML, `JNIRawData`, `JNIKeyValue`, GET, SET, listen, observer, socket, Binder, localhost,
  process execution, property access or filesystem write;
- no Android permission, shared UID, component, packaged DEX, constructor table, embedded DEX/ZIP
  or secondary ELF;
- no plain `dlopen`, `RTLD_DEFAULT`, second DJI library load, ZIP parser, DEFLATE support,
  allocation, `mmap`, `realpath`, `/proc/self/mem` or root fallback;
- no claim that France `EIDSwitch` is an FAA/global RID switch;
- no device state, UAS identity, coordinate, registration value, account token or payload logging.

## Reviewed artifact

```text
package: com.finduas.jvmti.eidroute.v22
version: 0.1.0-offline-unadmitted (1)
ABI: arm64-v8a only
APK: FindUAS-JVMTI-EID-Route-Resolver-V2.2-0.1.0-offline-unadmitted-arm64-v8a.apk
APK bytes: `29019`
APK SHA-256: `7aa794ff8611582fd7cf27808a9d9eb11c44e307889d615d0511c100522845fb`
packaged SO bytes: `47512`
packaged SO SHA-256: `8059d9c5544fb11d0c4be37e8595adbbac92322c7da42377f23b2eae83d97c12`
signer certificate SHA-256: 37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224
```

The final digest block is checked by the artifact audit. Source/toolchain changes require a new
clean build, hashes, reproducibility result and review.

## Offline verification

```sh
sh scripts/run_host_tests.sh
sh scripts/build_and_audit.sh
sh scripts/reproducibility_check.sh
```

Host tests cover SHA-256 known answers and boundary lengths, exact local sample hashes/headers/
program headers, first/middle/tail byte mutations, source-kind rejection, split VMAs, device/inode/
offset/permission/coverage mutations, deleted mappings, high `PT_LOAD #6`, snapshot drift and
non-writable runtime-byte mutations. The packaged audit validates the compiled identity profiles,
identity-success control-flow dominance, fixed-zero exception gate, exact imports/exports,
manifest/ZIP/signer inventory and zero-send source boundary.

## Related evidence

- `../eid_runtime_whole_file_identity_audit_20260828.md`
- `../eid_exception_personality_bridge_audit_20260828.md`
- `../eid_agent_mapping_lease_audit_20260828.md`
- `../eid_framework_route_resolver_audit_20260828.md`
- `../eid_same_owner_jni_raw_get_route_20260828.md`
- [LIVE_ADMISSION.md](LIVE_ADMISSION.md)
- [ZERO_SEND_CONTRACT.md](ZERO_SEND_CONTRACT.md)
