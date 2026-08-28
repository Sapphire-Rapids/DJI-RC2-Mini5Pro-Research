# Zero-send contract

The reviewed V2.1 APK is a loader/symbol preflight, not a route result and not a protocol client.

## Enforced binary boundary

- The only exported ELF symbol is `Agent_OnAttach`.
- The APK contains no DEX, Android component, permission, shared UID, secondary ELF, or constructor
  table.
- Source and ELF imports exclude sockets, Binder, property APIs, process execution, filesystem
  writes, DUML and DJI GET/SET/listen/send APIs.
- `dlopen` occurs exactly once in source and only as `RTLD_NOW | RTLD_NOLOAD` after unique loaded
  module enumeration. Every `dlsym` result must resolve to the expected existing module base and
  exact RVA.
- Function signatures have an explicit size and must satisfy
  `0 < signature_size <= dynsym st_size`; short 8-byte functions are checked as 8 bytes.
- The private exception boundary gate is fixed to zero, is not exported, and is evaluated after
  module/symbol preflight but before the first target-owned method call.

## Observable output

The carrier emits one bounded numeric log line. It contains counts/statuses only: no class names,
paths, addresses, identifiers, payloads, device identity, location, account state, or registration
data.

`EXCEPTION_BOUNDARY_UNPROVEN` is the expected terminal route status for the exact reviewed build.
It means “target calls deliberately not attempted,” not “EID unavailable” and not “RID disabled.”

## Forbidden changes

Do not add or expose an option, JNI method, environment/property gate, component, DEX, signal,
file, socket, Binder transaction, debugger command, byte patch, or exported symbol that changes the
exception gate. Do not install or attach this artifact. Any future route-only experiment requires
a new version, new package/artifact hashes, full independent audit, and the admission sequence in
[LIVE_ADMISSION.md](LIVE_ADMISSION.md).
