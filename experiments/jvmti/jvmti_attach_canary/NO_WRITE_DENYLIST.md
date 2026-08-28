# Canary no-write / no-control contract

This contract applies to the code that executes inside the target process. Build and audit tooling is
outside that process.

## Exact runtime allowlist

The carrier library may do only the following:

1. `JavaVM.GetEnv` for a JVMTI 1.2 environment only;
2. JVMTI `GetVersionNumber` and `DisposeEnvironment`;
3. one `INFO` log entry under the fixed tag `FindUAS-JVMTI-Canary`.

The log contains only a literal ABI, fixed numeric error code and numeric JVMTI version. It never
requests or contains a loaded-class count, class reference, class signature, class name, path,
package version, device identifier, serial, address or DJI payload. Non-empty agent options are
rejected without logging their content.

## Denied surfaces

- JVMTI capabilities, event callbacks, breakpoints, watches, retransformation and redefinition;
- obtaining a `JNIEnv`, JNI Java method invocation of any kind, field access, object construction,
  local-reference inspection or class loading;
- JVMTI loaded-class enumeration or any other API that returns JNI local references;
- JVMTI class signature/name, method, field, bytecode or annotation inspection;
- dynamic native loading after entry, symbol lookup, tracing or injection;
- network and local-socket creation, connection, accept, transmit or receive;
- filesystem reads/writes, directory creation, rename, deletion or memory mapping initiated by the
  canary;
- Android property reads or writes;
- process/thread creation, command execution, signals or privilege changes;
- Binder, Parcel, DJI protocol manager, localhost ports, DUML, key GET/SET, FlySafe and aircraft
  commands;
- `JNI_OnLoad`, `Agent_OnLoad`, `Agent_OnUnload`, native constructors or background callbacks.

## Enforced checks

`scripts/audit_artifact.py` fails unless:

- the C source calls exactly the allowlisted JavaVM/JVMTI/JNI table entries;
- the build contains exactly one native source and no inline assembly or embedded binary source;
- prohibited source tokens are absent;
- the ELF exports only `Agent_OnAttach`;
- the only ELF imports are `__android_log_print` and the compiler hardening guard
  `__stack_chk_fail`;
- the only ELF dependencies are public Android `liblog.so` and `libc.so`;
- there is no ELF constructor table;
- the APK has no DEX, permission, component or shared UID;
- the APK has only one native entry, at the exact `arm64-v8a` path;
- the complete APK ZIP inventory is the four-entry allowlist;
- the signer is the expected local certificate, the APK is single-signer/v2-only, and the known
  DJI platform certificate is not the signer;
- the README artifact SHA-256 matches the audited APK.

Any audit mismatch is a hard failure. It is not downgraded to a warning.
