# Independent audit — FindUAS RID Bridge Probe v0.10

Audit date: 2026-08-28 (Asia/Shanghai)

Audited artifact:

- `dist/FindUAS-RID-Bridge-Probe-0.10.0-research.apk`
- Bytes: `2570983`
- SHA-256: `fdad29bfb1237bc224a805d6eb5a99358a044bd226610d9f0fc33975d94b606c`

This was an independent, adversarial, offline audit. I read the safe source set, tests, build configuration, audit scripts, and required design/audit documents; independently inspected the final APK; and used separately compiled hostile variants to test the auditor. I did not install or copy an APK to a device, connect to a device, or perform any runtime probe.

## Verdict

The exact APK identified above passes the v0.10 offline release boundary as a zero-permission, read-only research probe.

There are no unresolved P0, P1, P2, or P3 findings in the reviewed artifact and final auditor. All P2/P3 issues found during this audit were fixed and independently retested before this report was written.

This verdict is deliberately narrow. It does not establish RC 2 runtime compatibility, grant approval to attach JVMTI, load native code, send DUML/Binder application transactions, change firmware, or alter Remote ID behavior.

## Findings found and fixed during v0.10 audit

### P2 — final-DEX COMPLETE proof had provenance and storage blind spots

Earlier auditor revisions could accept mutations that initialized a probe-completion flag to true, discarded `ProbeCompletionPolicy.terminalState()` and stored a forced `COMPLETE`, or failed to prove that the ART state came from the real `AndroidArtIdentityProbe.run()` result or its fail-closed `FILE_READ_ERROR` fallback.

The final auditor now isolates the exact caller method, constructs normal and exception-aware CFGs, checks local lifetimes and dominating false initialization, requires a true write only on the normal return path of each prerequisite probe, proves both ART result origins, rejects fallback-register overwrite, and proves that the gate result becomes the retained snapshot's `runState`. It also requires one retained-state store and an exact `copy$default` mask of `0xec0`, with all six observed fields supplied rather than defaulted.

Status: fixed and mutation-tested.

### P2 — write/load safety audit could certify reachable forbidden behavior

An earlier auditor revision accepted a separately compiled Activity containing both a reachable Kotlin file write and `System.load()`. The shipped APK itself did not contain either operation, but this was a future-certification failure in the auditor.

The final auditor now applies source and app-owned DEX bans for native loading, process execution, file persistence, sockets/network sends, Android `Os` write/send calls, Binder transaction/Parcel surfaces, and code-loading/debug APIs. It also freezes the app-owned external-invoke canonical multiset at 2,361 calls with SHA-256 `c3b4ed26b563e2be2e4806b57ba0d21b8ea15ee3e6fa276d4223e0749d32ed29`.

Status: fixed and tested with real compiled hostile APKs.

### P3 — `/proc/self/maps` parser admitted non-canonical identities

The earlier v0.10 parser admitted a zero mapping start and explicit `+` signs in device or inode fields. Those forms weakened strict canonical parsing even though the exact final APK had no device-derived input yet.

The parser now rejects `start <= 0`, accepts only unsigned hexadecimal device components and unsigned decimal inode text, rejects `00:00`, enforces positive inode, checked address/file-offset arithmetic, page alignment, and page-rounded file coverage. Tests include zero start, signed fields, oversized identities, overflow, reversed/empty ranges, alignment, overlap, and rounded-size overflow.

Status: fixed; the final ART parser test suite passes.

### P3 — Kotlin `writeText$default` was initially covered only by the frozen invoke surface

A compiled `File.writeText(...)` call lowers to `FilesKt.writeText$default`. The first explicit DEX deny regex matched `writeText:` but not the `$default` form; the frozen external-invoke surface still rejected the APK, so the final artifact was not exposed.

The explicit DEX rule and its mutation were updated to cover the optional `$default` suffix. The separately compiled write-only variant is now rejected by the direct denylist even when frozen-surface enforcement is disabled.

Status: fixed and independently retested.

## Core source review

The final ART identity path is fail-closed on the reviewed source:

- It reads only `/proc/self/maps`, selects exact-basename `libart.so` entries, and requires one non-zero device/inode/path identity with readable and executable mappings.
- Mapping addresses and file offsets are positive/canonical, checked for overflow, page-aligned, non-overlapping by virtual address, and bounded by the page-rounded descriptor size.
- It rejects a final symlink with `lstat` and `O_NOFOLLOW`, then verifies a non-zero `fstat.st_dev`, positive inode, regular-file type, and exact path/descriptor identity.
- Exact metadata includes size, mode, device, inode, and modification/change seconds plus nanoseconds. It is compared before and after positional reads.
- Whole-file SHA-256 and the ELF64 little-endian GNU build ID are read from the already opened descriptor. The ELF note parser is bounded and requires one unique build ID.
- The second normalized maps snapshot must be exactly equal to the first; malformed counts, ordered entries, permissions, addresses, offsets, device, inode, path, and deleted state therefore all participate.
- The two machine-report ranges are correctly named `art.agent_unload_range.*` and `art.runtime_attach_agent_range.*`.
- `COMPLETE` requires protocol-probe completion, local-bridge completion, and `ArtIdentityState.COMPLETE`.

Activity recreation uses a synchronized process-lifetime coordinator. A replacement Activity renders and polls the retained immutable snapshot instead of starting another worker. Probe, copy, and Settings buttons are disabled while a run is active. Settings navigation is user-triggered, action-only, and fixed in safe UI order: Device information, then Developer options; only `Settings.ACTION_SETTINGS` is used as the fallback.

## Manifest, DEX, signature, and ZIP results

Independent APK inspection found:

- Package `com.finduas.ridobserver`, versionCode `10`, versionName `0.10.0-research`.
- minSdk `29`, targetSdk `35`.
- Zero requested permissions.
- One exported launcher Activity; no service, receiver, or provider.
- Exactly four package-visibility queries: `dji.go.v5`, `com.dpad.fuli`, `com.finduas.jvmti.canary.carrier`, and `com.finduas.jvmti.eidresolver.v1`.
- Backup disabled; debug build/debbugable flag present.
- Fourteen ZIP members and no `lib/` native entries.
- Seventy-five app-owned DEX class blocks.
- Exactly one app-owned `/proc` string: `/proc/self/maps`.
- Exactly three Settings action strings, one action-only `Intent(String)` construction, and one `startActivity` call.
- No app-owned DEX invocation of file-output/persistence, native load, process execution, socket/connect/send, `IBinder.transact`, `Parcel`, DexFile/VMDebug/JVMTI attach, or Android `Os` write/send APIs.
- Framework-only reflection remains limited to the documented `android.os.ServiceManager`, `android.os.SystemProperties`, and `android.os.SELinux` targets. It performs read-only metadata lookup/ping/descriptor/property checks, not an application Binder transaction.
- APK Signature Scheme v2 verification succeeds with one Android Debug signer, certificate SHA-256 `37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224`.
- `zipalign -c -v 4` succeeds.

Critical APK member hashes:

| Member | Bytes | SHA-256 |
| --- | ---: | --- |
| `AndroidManifest.xml` | 2844 | `f99831d54d27dfc9cead3a136cb7fb320e5e3bb56198e26ce044e8e054aea044` |
| `classes.dex` | 2335104 | `a8d456bec894437b7ad001edc1bd2f72c39303723d71f1578880f08390a0f306` |
| `classes2.dex` | 1664 | `125342d24a7974fa0534e12b47f1d8075d97f4ab68ff7f05f47b42e7af4034f8` |
| `classes3.dex` | 214092 | `b0241237ec87b5ea0ee3a3e0fd608240bece2db139008928cfc03366ab677e9e` |
| `resources.arsc` | 2236 | `8367425b0b90a67bcc222ee061e842550166a826417c772853a2d4cbfa76394e` |
| `res/drawable/ic_observer.xml` | 724 | `7245397ae602effac65940b1955955b5c1608e00c25a861d1b8b1059338742fd` |

## Build, tests, and adversarial checks

An offline clean run of `testDebugUnitTest`, `lintDebug`, and `assembleDebug` completed successfully:

- 43 tests; 0 failures, 0 errors, 0 skipped.
- Android lint: `No issues found.`
- The rebuilt APK is byte-identical to the reviewed `dist` artifact.

Two additional independent `--offline --no-daemon clean assembleDebug` builds were byte-identical to each other and to the reviewed artifact. Both had SHA-256 `fdad29bfb1237bc224a805d6eb5a99358a044bd226610d9f0fc33975d94b606c`; both passed the final artifact audit and mutation suite.

The final dexdump mutation suite rejected 21 of 21 mutations, covering the gate branches/result, prerequisite completion initialization and provenance, ART success/fallback provenance, fallback overwrite, snapshot argument/mask/store integrity, and explicit native-load/file-write surfaces.

Three separately compiled hostile APKs were also checked against the final rules:

| Compiled mutation | Bytes | SHA-256 | Expected rejection |
| --- | ---: | --- | --- |
| Discard `terminalState()` and force stored `COMPLETE` | 2571075 | `3fd59be8f0ce806f80c3ac7297363c573c59c1b892cd49d4406e08ba3776c84d` | `terminalState() result is overwritten before snapshot storage` |
| Reachable `File.writeText` plus `System.load` | 2571311 | `ca4a16d476bb01d263b456eac0413976208241a1a887e7d1a56053d54876400d` | forbidden `Ljava/lang/System;.load` invocation |
| Reachable `File.writeText` only | 2571227 | `567fff9643e580c359322e67912fbceb3175cee8009a1ea0cacea9e7d1bf9e6d` | direct `FilesKt.writeText$default` write/send deny rule, independently confirmed with frozen-surface enforcement disabled |

## Known ART reference

The local reference `firmware/rc331/10.00.0700/0205/working/art_release_exact/libart.so` was independently checked:

- Bytes: `8614280`
- Whole-file SHA-256: `3ec3d232ad7f4099c42f014b87658be47e83d7e21a7a053fb16c4d146103745d`
- GNU build ID: `5f839ecc60b9ae39764305b5fee6ed37`
- `art::ti::Agent::Unload()`: offset `0x5ccfa0`, size `0x100`, range SHA-256 `098c16b8613f438294017b8af2e2e45685556a9cf5c6882120f08a5ea315c668`
- `art::Runtime::AttachAgent(...)`: offset `0x56bfc4`, size `0xebc`, range SHA-256 `9db764e816c6771623e660b308d2527da4e57d05530ae7a3c8dfdf9d07dec80a`

These are identity/range observations only. The app does not resolve, call, attach to, or load either range.

## Exact current audit inputs

| Input | SHA-256 |
| --- | --- |
| `app/src/safe/java/com/finduas/ridobserver/AndroidArtIdentityProbe.kt` | `7cab113e788b5c9042190febd225757ccd1f08ad02c643724e67fbe377669b8a` |
| `app/src/safe/java/com/finduas/ridobserver/MainActivity.kt` | `0411a52627901c5a0910621b60ab709780b286016ef4455a4e6381c12440424d` |
| `app/src/safe/java/com/finduas/ridobserver/LocalBridgeProbe.kt` | `8cc9ea6450a30af465181c5fe003176210f6392e2c29527a00a64bf224f8685b` |
| `app/src/safe/java/com/finduas/ridobserver/ProtocolBinderProbe.kt` | `a3e1471006b6de53c6576e587cad3e9bab77731ad3c9248cfb4a41657ffad590` |
| `app/src/safe/java/com/finduas/ridobserver/ArchiveFingerprint.kt` | `ed7dc9c7133bac5d1330b95aa95387a13e70d6b74faba7b46608f8701b0273ff` |
| `app/src/safe/AndroidManifest.xml` | `97dee9c249c4c1a650990d747c9b91a2110b0979a526217d1e88e75e6aa86ae5` |
| `app/src/safeTest/java/com/finduas/ridobserver/AndroidArtIdentityProbeTest.kt` | `d3a4c461f1048245ee2f8215a97f565beedfceef661565c92c11940081c2d63e` |
| `scripts/audit_artifact.py` | `d040c9920e90335eb6d6e99b7f7f8b592b5847af66247d74ceea972122e30e52` |
| `scripts/test_audit_mutations.py` | `116c61e36a2a9d6f5a437d45416841560524186b0b47a517900e5d5f79227f78` |
| `app/build.gradle.kts` | `37366f0e5c700661449cc9816b84b648fd1c44d3687a6893d29de193632c65b4` |

Sealed predecessor APK identities were also preserved:

- v0.8: `b67a99621440088a39d212483d2de69a47fdc26850b59ed7fecfa9e1e8c70fb1`
- v0.9: `a59f0f6abb2d1a10aeba44efed76cc85d351086fbf6dff5c1cc377dabe12b97d`

## Remaining limitations

- No device-side execution was performed in this audit. Runtime UI behavior, RC 2 policy/SELinux access, actual maps contents, and live output remain unverified until a separately authorized device test.
- This is a static, artifact-specific audit with targeted CFG/data-flow checks and adversarial mutations, not a general formal verifier for arbitrary Kotlin/DEX programs.
- The APK is a debuggable research build signed by an Android Debug certificate, not a production release-signed package.
- Retention is process-lifetime. Android process death resets the coordinator; ordinary Activity recreation within the same process is covered.
- `pingBinder()` and `interfaceDescriptor` are read-only Binder metadata operations, not “no Binder interaction” in the absolute kernel sense. The verified boundary is no application `transact`, no `Parcel`, and no DJI protocol command.
- The user-triggered copy button writes the already displayed report to the Android clipboard, and the two Settings buttons launch fixed Android Settings actions. Neither action occurs automatically.

## Recommended disposition

Retain only the exact APK hash `fdad29bfb1237bc224a805d6eb5a99358a044bd226610d9f0fc33975d94b606c` as the reviewed v0.10 candidate. Any source, build-tool, signer, dependency, audit-script, or APK change requires a new independent audit and new artifact identity.
