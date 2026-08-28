# Zero-send contract

The reviewed V2.3 APK is an identity/loader/symbol preflight, not a protocol client. V2.2 is
revoked and is not an alternative artifact.

## Enforced binary boundary

- Only ELF export: `Agent_OnAttach`; no DEX, Android component, permission, shared UID, secondary
  ELF or constructor table.
- No socket, Binder, property, process, allocation, filesystem-write, DUML or DJI
  GET/SET/listen/send API.
- Read-only filesystem access is limited to `/proc/self/maps` and three exact already-loaded paths,
  all opened with `O_RDONLY | O_CLOEXEC | O_NOFOLLOW`.
- The sole `dlopen` expression is `RTLD_NOW | RTLD_NOLOAD`; no plain load, `RTLD_DEFAULT`, second
  copy or alternate transport exists.
- The narrow identity verifier cannot access runtime-phdr metadata. Exact whole-file/non-writable
  memory/maps success uniquely precedes the linker-epoch admission; admission uniquely precedes
  runtime Ehdr/phdr reads, symbol resolution and the immutable-zero exception gate.
- The gate is a zero word in read-only/non-executable storage with no relocation. Its false branch
  closes handles and jumps over the sole dormant DJI-owned route helper.

One bounded log line emits only numeric result/stage/count fields. It never emits paths, addresses,
inode/timestamps, identifiers, payloads, device identity, location, account or registration data.

Expected terminal status after exact preflight is `EXCEPTION_BOUNDARY_UNPROVEN`, meaning target
calls were deliberately not attempted. Do not install or attach this artifact. Do not add any gate
setter, component, DEX, signal, file, socket, Binder, debugger or byte-patch bypass.
