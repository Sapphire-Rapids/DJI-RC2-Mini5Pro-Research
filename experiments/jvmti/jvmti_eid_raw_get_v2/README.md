# FindUAS JVMTI EID raw GET V2 — offline unresolved carrier

Status: **NOT ADMITTED — DO NOT INSTALL OR ATTACH**. This artifact has not been copied to or run
on the RC 2.

This work-only Android 11/AArch64 carrier tests the buildability and static safety boundary of a
future same-owner, read-only France-EID raw GET. It contains the exact DJI callback interface shape
and one guarded `JNIRawData.native_SendData` call site, but the route resolver is deliberately and
permanently `UNRESOLVED`; the epoch check is permanently false. Therefore the packaged build cannot
reach the send call and its audited `send_call_count` remains zero.

It is not part of the public MIT FindUAS application. It has no Android permissions, components,
shared UID or packaged DEX. The only helper class is embedded as bytes inside the native library and
can be loaded only after future live admission. No SET body, typed getter, observer registration,
second broker/TCP route, socket, filesystem write, process execution or dynamic symbol lookup is
present.

## Fixed protocol shape, unreachable in this build

- command: France EID `0x03/0x77` GET body `[0x02]`;
- raw ACK: exactly `[protocol_result,state]`;
- selector intent: `3`;
- timeout: 500 ms;
- retry: explicit `0`, labelled `LAB_SINGLE_SHOT`, not official-exact typed behavior;
- callback: the unreachable prototype currently samples one response XOR timeout, matching handle,
  exact two-byte response and result `0`, then waits 100 ms; that fixed quiet window has since been
  rejected as insufficient and must not be copied into a live build;
- local deadlines use Android `CLOCK_MONOTONIC`; cancel is cleanup only and never proves that a
  remote operation did not execute.

## Artifact identity

APK SHA-256: `70d2995fb2f4d464a5d9314d924b15ff3503c81e823c0792c8ab660a297b32bf`

APK bytes: `16722`

packaged AArch64 SO SHA-256:
`1bd39e46fbc998f585e7d3ae10a9e371cc67054a09a213a046ce04633ac85d7d`

packaged AArch64 SO bytes: `19728`

helper DEX SHA-256: `3857b7a382f0798fab9d24f424207516fadb672eea5aad9d687761443b581ed7`

The final values are inserted only after a successful clean build and then re-audited. The signer
must be the local FindUAS research certificate
`37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224`, never the DJI platform
certificate.

## Build and audit

```sh
sh scripts/build_and_audit.sh
```

The audit requires the hashes above to match, so the first build intentionally stops at that final
metadata gate. Record the generated APK/helper hashes with `apply_patch`, then rerun the command.
Afterward perform a second clean build and require byte-identical APK/helper hashes.

`build/inspect.so` is a generated inspection mirror, never a staging artifact. The build removes any
older copy before compilation and recreates it atomically from the final signed APK. The audit fails
unless that mirror is a regular file byte-identical to the packaged AArch64 library. Only the exact
APK under `dist/` is the reviewed carrier; `app/build/` and `build/package-stage/` are intermediate
outputs and must not be installed.

See `LIVE_ADMISSION.md` and `NO_WRITE_SINGLE_SEND_CONTRACT.md` before changing
`route_snapshot.c`. A resolved route must never be added merely to make the APK send.
The required callback-owner and worker-tail quiescence proof is recorded in
`../eid_callback_lifetime_audit_20260828.md`.
