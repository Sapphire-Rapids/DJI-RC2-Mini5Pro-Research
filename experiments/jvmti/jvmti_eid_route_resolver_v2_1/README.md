# FindUAS EID route resolver V2.1 — offline, unadmitted carrier

> **DO NOT INSTALL OR ATTACH**

Status: **NOT ADMITTED**.

This is a work-only AArch64 JVMTI review artifact for the exact DJI Fly 1.21.10 native samples in
the parent research directory. It is not a working EID/RID reader and is not a Remote ID switch.
It has never been copied to or run on the RC 2.

## What the reviewed artifact can do

On `Agent_OnAttach`, the carrier can:

1. enumerate already-loaded classes and require exactly one
   `electronicIDBroadcastOn` anchor and one `electronicIDBroadcastExisted` anchor in the same
   ClassLoader;
2. enumerate already-loaded ELF modules with `dl_iterate_phdr`;
3. require one exact basename and GNU build ID for each of `libsdk_jni.so`,
   `libsdk_key_value.so`, and `libsdk_base.so`;
4. obtain only `RTLD_NOW | RTLD_NOLOAD` handles and validate 21 fixed symbols with `dlsym`,
   `dladdr`, exact module base + RVA, segment permissions, and bounded AArch64 entry signatures;
5. read only whether the existing `g_pModuleMediator` slot is non-null;
6. emit one numeric, identifier-free log record and dispose the JVMTI environment.

The source contains the next target-owned string/CacheKey/owner route for ABI review. The only
artifact fixes a private, non-exported `const volatile` gate to zero before that path. It therefore
always reports `EXCEPTION_BOUNDARY_UNPROVEN` and cannot call target-owned string construction,
`SDKFrameworkCore::GetKey`, map lookup, Characteristics lookup, GET, SET, listen, or send.

## What it does not do

- no DUML, `JNIRawData`, `JNIKeyValue`, GET, SET, listen, observer, socket, Binder, localhost,
  process execution, property access, or file write;
- no Android permission, shared UID, component, packaged DEX, constructor table, embedded DEX/ZIP,
  or second ELF;
- no creation of the DJI SDK singleton and no second loaded copy of a DJI SO;
- no claim that France `EIDSwitch` is an FAA/global RID switch;
- no device state, UAS identity, coordinate, registration value, account token, or payload logging.

Runtime checking currently proves exact build IDs, mappings, RVAs, symbol owners, segment ranges,
and code prefixes. The separate host manifest verifies the complete on-disk sample SHA-256 values.
This carrier does **not** yet recompute whole-file SHA-256 inside the target process. Runtime
whole-file identity and the target static-libc++ exception/personality boundary are both live
admission blockers; see [LIVE_ADMISSION.md](LIVE_ADMISSION.md).

## Reviewed artifact

```text
package: com.finduas.jvmti.eidroute.v21
version: 0.1.0-offline-unadmitted (1)
ABI: arm64-v8a only
APK: FindUAS-JVMTI-EID-Route-Resolver-V2.1-0.1.0-offline-unadmitted-arm64-v8a.apk
APK bytes: `16731`
APK SHA-256: `7f0159619f89f7c6a9849b1028003a1070d97988838da7a6ef027e09626ada0d`
packaged SO bytes: `23032`
packaged SO SHA-256: `3c2a293e167531ecc9d352c2825ad20c8f35a3e829c66aad6896d06eabad3365`
signer certificate SHA-256: 37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224
```

The digest block is checked by the artifact audit. If source or toolchain output changes, rebuild,
re-audit, and update it only after the new artifact has been independently inspected.

## Offline verification

```sh
sh scripts/run_host_tests.sh
sh scripts/build_and_audit.sh
sh scripts/reproducibility_check.sh
```

The audit validates the exact target samples offline, including true dynsym attributes, RVAs,
function sizes, and signatures that never extend past `st_size`. It also audits the APK manifest,
signer, ZIP inventory, native imports/exports, no-constructor boundary, x8 hidden-sret shims, source
denylist, and the immutable exception gate.

## Related evidence

- `../eid_framework_route_resolver_audit_20260828.md`
- `../eid_same_owner_jni_raw_get_route_20260828.md`
- `../eid_work_thread_epoch_audit_20260828.md`
- `../runtime_route_manifest_20260828.md`
- [ZERO_SEND_CONTRACT.md](ZERO_SEND_CONTRACT.md)
