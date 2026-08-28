# v0.10 Android/ART self-process identity contract

## Scope and disposition

Version `0.10.0-research` is a new artifact. It does not replace or rewrite the sealed v0.9 APK.
It keeps the v0.8 read-only capability inventory and fixes every identity/integrity weakness found
by `INDEPENDENT_AUDIT_V09.md`.

The app still has zero requested permissions, one launcher Activity, and no service, receiver,
provider or native library. It does not open a network/localhost socket, encode or send DUML,
perform a DJI Binder application transaction, run a process, load/attach an agent or library,
inspect another process, or write a target/report file. Clipboard copy and the two fixed Android
Settings actions remain explicit user clicks.

This implementation and its artifact were built and audited offline. The APK was not copied to,
installed on, or launched on the RC 2 during this work.

The independent adversarial disposition is recorded in `INDEPENDENT_AUDIT_V10.md`.

## Strict maps geometry

The ART section reads the normalized exact-basename `libart.so` subset of
`/proc/self/maps`. Every candidate must have:

- one unsigned hexadecimal `start-end` pair whose values fit a positive signed 64-bit
  representation, with no sign prefix;
- `0 < start < end`;
- page-aligned start, end and file offset, using the live `_SC_PAGESIZE` value;
- a checked `fileOffset + (end - start)` with no signed overflow;
- canonical four-character permissions;
- a positive unsigned-decimal inode, an absolute clean path and a non-zero Linux `major:minor`
  device whose two components are unsigned hexadecimal (no explicit `+` or `-`);
- one file identity, plus at least one readable and one executable mapping.

After opening the descriptor, every VMA must fit within the page-rounded exact descriptor size;
address ranges may not overlap. Reversed/zero-length ranges, over-wide hexadecimal values,
unaligned fields, a zero start address, signed device/inode tokens, `00:00`, offset overflow,
overlapping VMAs and beyond-file coverage all reject the ART section.

## Descriptor and stability chain

The exact runtime order is:

1. obtain and validate the live page size;
2. read/parse maps snapshot A and admit one exact identity;
3. `lstat(path)` and reject a final symlink or non-regular/zero-device object;
4. `open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW)`;
5. `fstat(fd)`, reject `st_dev == 0`, and match mapping device/inode to the descriptor;
6. require exact path/descriptor metadata equality, including `st_mtim.tv_sec/tv_nsec` and
   `st_ctim.tv_sec/tv_nsec`;
7. validate every mapping's address/file coverage against the descriptor size;
8. hash exactly the descriptor's bytes with positional `pread`, then parse one bounded ELF64
   little-endian GNU build-id;
9. when the fixed whole-file hash and build-id match, hash the two named fixed ranges below;
10. repeat `fstat(fd)` and `lstat(path)` and require the same nanosecond metadata;
11. read/parse maps snapshot B and require exact data-class equality with normalized snapshot A.

Any second-read error, malformed/rejected second snapshot, permission/offset/path/inode/device
change, or row/order/permission/range change keeps `art.section_complete=false`.

The two range identities are now named after the exact recovered functions:

```text
Agent::Unload
offset 0x5ccfa0, size 0x100
SHA-256 098c16b8613f438294017b8af2e2e45685556a9cf5c6882120f08a5ea315c668

Runtime::AttachAgent
offset 0x56bfc4, size 0xebc
SHA-256 9db764e816c6771623e660b308d2527da4e57d05530ae7a3c8dfdf9d07dec80a
```

The primary recovered profile remains:

```text
libart.so bytes:       8614280
whole-file SHA-256:    3ec3d232ad7f4099c42f014b87658be47e83d7e21a7a053fb16c4d146103745d
GNU build-id:          5f839ecc60b9ae39764305b5fee6ed37
```

An otherwise valid different ART profile can complete the identity inventory with
`art.known_rc2_profile=DIFFERENT`; that does not admit it for a later exact-profile operation. If
the primary identity matches but either named range is unreadable or wrong, the ART section is
hard `INCOMPLETE`.

## Activity recreation and Settings order

One process-lifetime `ProbeSessionCoordinator` owns the immutable running/completed snapshot and
the only worker admission gate. A replacement Activity renders that same snapshot and polls it;
it cannot start a second worker while the first is `RUNNING`. The completed report and Settings
navigation result survive ordinary Activity/configuration recreation within the process.

Settings buttons appear and execute in the supported order:

1. `Settings.ACTION_DEVICE_INFO_SETTINGS` (hidden About/device info);
2. `Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS` (after seven Build-number taps).

Each may fall back only to `Settings.ACTION_SETTINGS`. There is still one app-owned
`startActivity(Intent(action))` site, with no package, component, URI or extras.

## Machine schema and completion gate

Schema is `finduas-rid-probe/v0.10-schema-1`. New/renamed fields include:

```text
art.page_size_bytes
art.second_maps_entry_count
art.second_malformed_entry_count
art.maps_snapshot_stable
art.mapped_device_nonzero
art.final_path_symlink
art.file_device_nonzero
art.map.<n>.start_address
art.map.<n>.end_address
art.agent_unload_range.*
art.runtime_attach_agent_range.*
```

The obsolete/misleading `art.attach_range.*` and `art.loader_range.*` keys do not exist in source
or final DEX.

Overall `COMPLETE` still requires all three real results:

```text
base.protocol_binder_completed == true
base.local_bridge_completed == true
nextArtIdentity.state == ArtIdentityState.COMPLETE
```

The artifact auditor no longer accepts a class/string marker as proof. It parses final dexdump
control flow, requires the two boolean rejection branches plus the exact ART enum comparison,
checks that every rejection reaches `INCOMPLETE`, and proves the single call site is immediately
fed by `nextArtIdentity.getState()` and the two named completion locals. It also proves each
completion local starts false and becomes true only on the normal-return path of its corresponding
probe, proves `nextArtIdentity` is either the real `AndroidArtIdentityProbe.run()` return or the
explicit `FILE_READ_ERROR` exception fallback, and follows the gate result without overwrite into
`ProbeSessionSnapshot.runState` and then `ProbeSessionCoordinator.state`. Nineteen adversarial
dexdump mutations (including false-to-true initialization, forged ART provenance, overwritten
fallback state, unsafe copy mask, discarded gate result and unpersisted snapshot) plus two
load/write boundary mutations are all rejected. The application-owned final DEX also has a frozen
external-invoke multiset and explicit deny rules for native loading, file-output APIs and
socket/send APIs.

## Build and artifact evidence

Commands:

```sh
./scripts/build_and_audit.sh
./scripts/reproducibility_check.sh
```

Results:

```text
safe JVM tests:                 43 passed, 0 failed, 0 skipped
Android lint:                   no issues
packaged source/manifest audit: PASS
final DEX semantic audit:       PASS
DEX audit mutations:            21/21 rejected
APK Signature Scheme v2:        verified
zipalign -c 4:                  verified
native libraries:               none
two clean builds:               byte-for-byte identical
```

Artifact:

```text
dist/FindUAS-RID-Bridge-Probe-0.10.0-research.apk
bytes:   2570983
SHA-256: fdad29bfb1237bc224a805d6eb5a99358a044bd226610d9f0fc33975d94b606c
signer certificate SHA-256:
37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224
```

Important APK members:

```text
classes.dex            a8d456bec894437b7ad001edc1bd2f72c39303723d71f1578880f08390a0f306
classes2.dex           125342d24a7974fa0534e12b47f1d8075d97f4ab68ff7f05f47b42e7af4034f8
classes3.dex           b0241237ec87b5ea0ee3a3e0fd608240bece2db139008928cfc03366ab677e9e
AndroidManifest.xml    f99831d54d27dfc9cead3a136cb7fb320e5e3bb56198e26ce044e8e054aea044
resources.arsc         8367425b0b90a67bcc222ee061e842550166a826417c772853a2d4cbfa76394e
```

Sealed predecessor checks also passed:

```text
v0.9 SHA-256 a59f0f6abb2d1a10aeba44efed76cc85d351086fbf6dff5c1cc377dabe12b97d
v0.8 SHA-256 b67a99621440088a39d212483d2de69a47fdc26850b59ed7fecfa9e1e8c70fb1
```
