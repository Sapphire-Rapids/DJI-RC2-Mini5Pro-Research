# Independent offline audit — EID route resolver V2.1

Audit date: 2026-08-28 (Asia/Shanghai)
Scope: source, host tests, exact DJI native samples, packaged APK and packaged AArch64 ELF only.
Device boundary: no ADB command, install, attach, process inspection, network connection or device
operation was performed.

## Decision for the reviewed bytes

**PASS as a work-only, permanently unadmitted preflight artifact.**
**NOT ADMITTED for installation, attachment, route execution, GET, SET or any live use.**

The reviewed APK is:

```text
FindUAS-JVMTI-EID-Route-Resolver-V2.1-0.1.0-offline-unadmitted-arm64-v8a.apk
bytes: 16731
SHA-256: 7f0159619f89f7c6a9849b1028003a1070d97988838da7a6ef027e09626ada0d
```

Its packaged native library is:

```text
lib/arm64-v8a/libfinduas_eid_route_resolver_v2_1.so
bytes: 23032
SHA-256: 3c2a293e167531ecc9d352c2825ad20c8f35a3e829c66aad6896d06eabad3365
```

This decision applies only to those exact bytes. The carrier cannot reach its target-owned route:
its private exception gate is zero in a read-only load segment and the only call to the dormant
route helper is dominated by that gate. Reaching module, anchor or symbol failure earlier is also
possible; `EXCEPTION_BOUNDARY_UNPROVEN` is the expected route terminal status only when preflight
reaches the gate.

## Independent checks completed

### APK boundary

- ZIP inventory is exactly four unique entries: AGP metadata, one `arm64-v8a` ELF, binary manifest
  and `resources.arsc`.
- No `classes*.dex`, second ELF, embedded ELF, embedded DEX or embedded ZIP was found.
- Manifest contains only `manifest`, `uses-sdk` and `application`: no permission, shared UID,
  activity, service, receiver, provider or instrumentation; `hasCode=false`.
- APK is 4-byte aligned and signed by exactly one local Android debug certificate with V2 only:
  `37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224`.
- The inspection mirror is byte-identical to the packaged SO.

### ELF and zero-send boundary

- ELF is AArch64/ELF64 and exports only `Agent_OnAttach`.
- `DT_NEEDED` is exactly `liblog.so`, `libdl.so`, `libc.so`.
- Undefined imports are limited to logging, checked memory operations, stack protection,
  `dl_iterate_phdr`, `dlopen`/`dlclose`/`dlsym`/`dladdr`/`dlerror`, and `memcmp`.
- No INIT, INIT_ARRAY, PREINIT_ARRAY, FINI, FINI_ARRAY, text relocation, RPATH or RUNPATH exists.
- Source, imports and binary strings contain no DJI GET/SET/listen/send/observer route, DUML/raw
  bridge, socket, Binder, localhost broker, process execution, property access or filesystem-write
  surface.
- The only compiled `dlopen` call receives flags `6`, i.e. `RTLD_NOW | RTLD_NOLOAD`; there is no
  `RTLD_DEFAULT` path.

### Fixed-zero exception gate

- Local gate object is at ELF RVA `0x0fe4`, has four zero bytes, lies in the first read-only
  `PT_LOAD`, and has no relocation.
- Gate function at `0x4e38` loads that object and returns true only when it equals `1`.
- The dormant target-call helper starts at `0x4e4c`; its only call site is `0x4ce4`, on the true
  branch after the gate check. The false branch records status `5` and closes no-load handles.
- The gate is not exported, has no setter, and non-empty JVMTI options are rejected.

### Exact module and symbol profile

An independent parser, separate from the project audit's target list, parsed `PT_DYNAMIC` through
`PT_DYNAMIC.p_vaddr` and the file-backed `PT_LOAD` mapping. It directly compared the C runtime
profile with the three exact native samples:

| Module | Whole-file SHA-256 | GNU build ID | true dynsym count |
| --- | --- | --- | ---: |
| `libsdk_jni.so` | `5abd990c86bcd00c9a652a21e329ad4580a20ec9f80188075ada61f5a7b46286` | `c892b3c06664df91d643f84ae9e59a906387068b` | 78496 |
| `libsdk_key_value.so` | `09f4aa8aef65f720da09a1dad79c8851e05d619affaf73708bf6747341208336` | `877a01a5b4b17e0a0f1b9153ccfe24891fb3c230` | 51801 |
| `libsdk_base.so` | `e5b290ebc6aa6e409e116cc0d3b84fb4e49c70f6c552feffacd5b15c7c83e873` | `de104ddaca91438807b21688baf08455d5ade20c` | 14944 |

All 21 runtime targets have one defined, default-visibility true dynamic symbol with the expected
binding, kind and RVA. All 17 function profile sizes equal true `st_size`. All four object ranges
fit inside true `st_size`. Six short functions use exactly eight-byte signatures; no signature
crosses a symbol boundary. A negative regression test restored the old 16-byte signature for the
8-byte `HardwareLayer::GetAbstraction` thunk and the audit rejected it with
`instruction signature exceeds dynsym size`.

### ABI, ownership and route identity

- All three AArch64 hidden-sret shims were inspected in packaged machine code. They move the return
  storage to `x8`; the `GetKey` bridge also moves the ninth C argument from `[sp]` to target `x6`.
- `GetFrameworkCore()` output is treated as a weak owner. Successful target `lock()` must return
  the same control block; the getter weak owner is then released exactly once and the pinned strong
  owner is released exactly once during cleanup.
- An impossible, different control pointer returned by `lock()` is not passed to an arbitrary
  refcount release call.
- Each successful abstraction lookup owns one strong reference and every marked reference is
  released once. Target string and CacheKey destruction counters match their construction counters.
- A Characteristics hit must be non-null and not the exact
  `Characteristics::Invalid @ libsdk_key_value.so+0x00c19d78` singleton, both before and after the
  second same-object/same-control lookup.
- These checks describe dormant reviewed code, not an executed live route; the gate prevents every
  target-owned call in this APK.

### Tests and reproducibility

- `scripts/run_host_tests.sh`: PASS.
- Final existing-artifact `scripts/audit_artifact.py`: PASS; audit-script SHA-256 is
  `81b67218c17dcea3bec143ac4c396b5aa7e2deb03235ef4c56400f39b6c7820b`.
- `scripts/reproducibility_check.sh`: two clean Gradle/native/package/sign cycles were byte-identical.
- Rebuilt APK and SO retained the exact hashes listed above.
- A deliberately truncated temporary APK was rejected. The negative path currently exits nonzero
  through Python `BadZipFile`, which is safe but not a polished diagnostic.
- A packaged-profile RVA mutation was rejected with `compiled profile RVA mismatch`.
- Replacing the compiled gate-result reload at `0x4cac` with `mov w8,#1` was rejected with
  `gate result data-flow/control block mismatch`.
- Restoring a 16-byte signature on an eight-byte target thunk was rejected with
  `instruction signature exceeds dynsym size`.

## Fixed blocker found during this audit

Before the reviewed bytes were sealed, six `st_size == 8` target thunks used fixed 16-byte entry
signatures, crossing into adjacent functions. The audit also discarded the parsed `st_size`.
This was reported as blocking and corrected to per-symbol sizes before the hashes above were
produced. The final runtime and offline audit both enforce bounded signature lengths.

The same review removed a cleanup path that would have called `release_shared()` on an impossible,
unknown pointer returned by weak `lock()`. The final artifact fails without invoking that unknown
pointer.

## Built-in audit regression coverage — resolved in final review

The first independent pass identified two future-regression gaps. They were subsequently
machine-checked and independently retested without changing the APK or packaged-SO hashes:

1. The audit now parses the packaged SO's RELA entries and the exact contiguous compiled module
   and symbol profile tables. It proves that all three compiled build IDs and all 21 compiled
   module IDs, symbol kinds, RVAs, profile sizes, signature sizes and signature bytes equal the
   separately verified true-dynsym manifest. Mutating a compiled profile RVA is rejected.
2. The audit now proves the packaged gate is zero, in a readable but non-writable/non-executable
   `PT_LOAD`, and has no relocation. It locks the complete 72-byte gate-result data-flow/control
   block, checks the gate and helper BL targets and unique call sites, and verifies the false edge
   skips the dormant helper. A negative mutation replacing the result reload with `mov w8,#1` is
   rejected.

No known blocker remains in the automated offline audit for the exact work-only bytes reviewed
here. These checks remain intentionally exact-build and fail closed when compiler layout or target
profiles change; any such change requires a new artifact and independent review.

## Live blockers remain intentionally open

This audit does not close the target static-libc++ exception/personality boundary, runtime
whole-file identity, bounded pointer-read proof, worker/connection epoch, terminal callback
lifetime, V0/V1 attach sequence, raw GET or any mutation/restoration plan. The README and
`LIVE_ADMISSION.md` correctly distinguish offline sample SHA verification from the weaker current
runtime identity checks. No wording in this result authorizes installing or attaching this APK.
