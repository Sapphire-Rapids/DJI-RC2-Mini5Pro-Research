# Zero-send contract

The reviewed V2.2 APK is an identity/loader/symbol preflight, not a protocol client.

## Enforced binary boundary

- The only exported ELF symbol is `Agent_OnAttach`.
- The APK contains no DEX, Android component, permission, shared UID, secondary ELF or constructor
  table.
- Source and imports exclude socket, Binder, property, process, allocation, filesystem-write,
  DUML and DJI GET/SET/listen/send APIs.
- Filesystem access is read-only and fixed in purpose: `/proc/self/maps` plus the three exact
  already-loaded `dlpi_name` paths. Each uses `openat` with `O_RDONLY | O_CLOEXEC | O_NOFOLLOW`;
  there is no create, write, mmap, ZIP, map-files, mem, symlink, root or permission fallback.
- `dlopen` occurs exactly once in source and only as `RTLD_NOW | RTLD_NOLOAD` after unique loaded
  module enumeration. Every `dlsym` result remains bound to the expected existing module and RVA.
- The compiled identity-success edge uniquely dominates module finalization and symbol resolution.
  Identity failure closes target handles and exits over every dormant target-owned call.
- The private exception boundary gate remains fixed zero in read-only, non-executable storage and
  uniquely dominates the dormant target-owned route helper.

## Observable output

One bounded log line contains numeric result codes, module/stage numbers, errno, aggregate byte/VMA/
fd counts and route counters. It never emits paths, addresses, inode values, timestamps, code bytes,
identifiers, payloads, device identity, location, account state or registration data.

For exact identity success, the expected terminal route status remains
`EXCEPTION_BOUNDARY_UNPROVEN`. It means “target calls deliberately not attempted,” not “EID absent”
or “RID disabled.”

## Forbidden changes

Do not add an option, JNI method, environment/property switch, component, DEX, signal, file, socket,
Binder transaction, debugger command, byte patch or export that changes the exception gate. Do not
add `apk!/`/DEFLATE fallback or weaken any file/maps/hash/memory failure into build-ID-only success.
Do not install or attach this artifact. Any future experiment requires a new version, hashes,
independent audit and the sequence in [LIVE_ADMISSION.md](LIVE_ADMISSION.md).
