# V2.2 independent offline audit

Date: 2026-08-28 (Asia/Shanghai)
Scope: source plus final packaged AArch64 APK/SO; no device access
Verdict: **REJECTED for independent admission — DO NOT INSTALL OR ATTACH**

The artifact remains zero-send, and its fixed-zero exception gate prevents the dormant DJI-owned
route helper from being called. However, two implementation defects violate the stated whole-file
identity boundary, and one lower-severity fail-closed check from the design is missing. The passing
project audit and reproducibility result do not close these findings.

## Findings, ordered by severity

### [P1] Runtime program headers are dereferenced before the claimed identity gate succeeds

`runtime_identity.c` performs the following order for every module:

1. open/fstat and maps snapshot A;
2. `runtime_headers_match(...)`;
3. `hash_and_compare_file(...)`;
4. post-fstat;
5. after all modules, maps snapshot B and linker-epoch recheck.

`runtime_headers_match` checks the pointer value and readable maps coverage, then executes:

```c
memcmp(module->runtime_phdr, profile->phdrs, sizeof(file_phdrs))
```

This is a runtime `dlpi_phdr` dereference before the whole-file SHA-256, original-non-writable
runtime/file byte comparison, maps-B equality and final linker recheck have succeeded. The final
packaged AArch64 `.text` confirms the same order:

```text
0x942c  BL runtime_headers_match
0x9494  BL hash_and_compare_file
```

The stripped packaged SO and the symbol-bearing unstripped build have byte-identical `.text`, so
the symbol names used to label those final RVAs do not come from a different code build.

This contradicts all of the following explicit project claims:

- `AGENTS.md`: runtime phdr/build-ID/segment parsing occurs only after identity success;
- `LIVE_ADMISSION.md`: all original non-writable bytes are compared before any runtime program
  header use;
- `ARTIFACT_AUDIT.md`: runtime header reads occur only after the whole-file/maps/non-writable-memory
  gate succeeds.

It does not use the runtime phdr to define the maps or hash ranges; those ranges correctly come
from the compiled profile. It is nevertheless on the wrong side of the declared trust boundary,
and the packaged audit incorrectly certifies the stronger ordering. `audit_artifact.py` checks only
that the initial `dl_iterate_phdr` callback does not index `info->dlpi_phdr`; it does not prove the
internal order of `runtime_headers_match`, hash/compare, maps-B and linker recheck.

Required correction:

- split file header/phdr validation from runtime-phdr validation;
- perform file-only validation while the fd is open;
- complete whole-file SHA/non-writable comparison, post-fstat, maps-B equality and linker recheck;
- only then compare/dereference the runtime phdr in the post-identity finalizer, before parsing
  segments/build-ID or resolving symbols;
- add a final binary-CFG assertion for this internal ordering, rather than only checking the outer
  `identity -> finalizer -> symbol resolver` order.

### [P1] A writable runtime phdr/original-non-writable mapping is accepted

The maps parser records each VMA's writable bit, but for every relevant fragment it rejects only
unreadable or non-private mappings. `finduas_snapshot_contains_readable_range` likewise checks only
coverage and readability. `runtime_headers_match` therefore accepts the program-header table from
an `rw-p` or `rwxp` mapping.

That violates the design requirement that the runtime phdr table be inside a verified readable,
**non-writable** target mapping. It also leaves every original `PF_W == 0` segment acceptable when
the current mapping has gained write permission, provided its bytes happen to match during the
comparison.

An independent negative fixture changed every generated relevant VMA, including original R-X
loads, to writable. The complete existing host suite still returned `Host tests: PASS`. This is a
testable acceptance gap, not only a documentation issue.

Required correction:

- require `writable == 0` across the complete runtime-phdr range;
- preferably reject current write permission for every page belonging exclusively to an original
  `PF_W == 0` `PT_LOAD`, while continuing to permit original `PF_W != 0` pages that have become
  read-only through RELRO;
- add `rw-p` and `rwxp` mutations for the phdr/first load and high `PT_LOAD #6`.

### [P2] `st_dev == 0` is not rejected

The approved design requires both `st_dev` and `st_ino` to be nonzero. `capture_file_state` rejects
zero inode, negative size and non-positive link count, but it does not reject `status->st_dev == 0`.
The maps parser can then accept device `00:00` if it matches the captured value.

This is unlikely for the expected `/data/app/.../lib/arm64` installation filesystem, and the whole
hash plus inode/maps checks still provide substantial binding. It is nevertheless a direct missing
fail-closed condition from the fixed `EXTRACTED_ELF_V1` contract.

Required correction: reject `status->st_dev == 0` before converting major/minor values, and add a
zero-device fstat/maps fixture.

## Independently confirmed properties

The following surfaces passed independent source and packaged-control-flow inspection:

- no socket, Binder, property, process execution, filesystem write, DJI GET/SET/listen/send,
  observer or hidden alternate transport path;
- only exported ELF symbol is `Agent_OnAttach`; imports are the expected log, loader, read/stat,
  memory and stack-check functions;
- no DEX, Android permission/component/shared UID, constructor table, secondary ELF, RPATH,
  RUNPATH or text relocation;
- exactly one source `dlopen`, using `RTLD_NOW | RTLD_NOLOAD`; no `RTLD_DEFAULT` or plain-load
  fallback;
- exact absolute extracted-source rejection for `apk!/`, deleted, memfd, anonymous, relative,
  empty and truncated paths, with `O_NOFOLLOW` on both target and maps opens;
- exact size, all-file EOF, whole SHA-256, pre/post fstat state, device/inode/offset/private/readable
  maps binding, dual maps snapshots and linker add/sub recheck are present;
- non-writable file/runtime translation uses `load_bias + p_vaddr + (file_offset - p_offset)` and
  correctly handles the three nontrivial high `PT_LOAD #6` entries;
- all opened target handles and target/maps fds have fail-closed cleanup paths;
- final route control flow is
  `identity -> finalizer -> exact dlsym/dladdr/RVA/signature -> mediator read -> fixed-zero gate`;
- the gate word at RVA/file offset `0x1240` is zero in an original R-- PT_LOAD, has no relocation,
  has one call site at `0x8070`, and the sole dormant helper call at `0x80c0` is reached only from
  the gate's nonzero branch.

The last point proves zero-send behavior for this exact artifact. It does not cure the identity
findings, and it must not be interpreted as live admission.

## Independent mutation tests

Three temporary source copies were mutated one at a time, compiled with the real host suite, and
then moved to Trash:

| Mutated production gate | Expected negative-test result | Observed |
| --- | --- | --- |
| remove `!/` source rejection | APK-in-path assertion aborts | PASS (mutation detected) |
| bypass maps offset equality | wrong-offset assertion aborts | PASS (mutation detected) |
| bypass non-writable byte `memcmp` | flipped-runtime-byte assertion aborts | PASS (mutation detected) |

A fourth independent fixture changed all relevant VMAs to writable without changing production
code. The entire host suite still passed, exposing the second P1 finding.

## Builds, hashes and unchanged predecessor

The following commands completed successfully before this verdict:

```text
sh scripts/run_host_tests.sh
sh scripts/build_and_audit.sh
sh scripts/reproducibility_check.sh
```

Two clean V2.2 builds were byte-identical. Independent hashes after the final build:

```text
V2.2 APK bytes  29019
V2.2 APK SHA-256
7aa794ff8611582fd7cf27808a9d9eb11c44e307889d615d0511c100522845fb

V2.2 packaged SO bytes  47512
V2.2 packaged SO SHA-256
8059d9c5544fb11d0c4be37e8595adbbac92322c7da42377f23b2eae83d97c12

local signer certificate SHA-256
37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224
```

The original V2.1 artifact was not rebuilt or edited and remains unchanged:

```text
V2.1 APK bytes  16731
V2.1 APK SHA-256
7f0159619f89f7c6a9849b1028003a1070d97988838da7a6ef027e09626ada0d

V2.1 packaged SO SHA-256
3c2a293e167531ecc9d352c2825ad20c8f35a3e829c66aad6896d06eabad3365
```

Independent target-sample hashes match the compiled profiles:

```text
libsdk_jni.so       87313856 bytes
5abd990c86bcd00c9a652a21e329ad4580a20ec9f80188075ada61f5a7b46286

libsdk_key_value.so 12684576 bytes
09f4aa8aef65f720da09a1dad79c8851e05d619affaf73708bf6747341208336

libsdk_base.so       7720240 bytes
e5b290ebc6aa6e409e116cc0d3b84fb4e49c70f6c552feffacd5b15c7c83e873
```

No RC 2, aircraft, ADB, storage volume, network service or DJI process was accessed during this
audit.
