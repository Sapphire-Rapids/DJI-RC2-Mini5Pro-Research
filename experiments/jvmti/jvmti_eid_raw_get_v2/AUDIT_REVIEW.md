# Independent V2 artifact review

Reviewed: 2026-08-28 (Asia/Shanghai)

Scope: read-only source and packaged-artifact review. No RC 2, aircraft, ADB, APK installation or
agent attachment was used.

## Packaged artifact

- APK SHA-256: `70d2995fb2f4d464a5d9314d924b15ff3503c81e823c0792c8ab660a297b32bf`
- APK bytes: `16722`
- packaged SO SHA-256: `1bd39e46fbc998f585e7d3ae10a9e371cc67054a09a213a046ce04633ac85d7d`
- packaged SO bytes: `19728`
- helper DEX SHA-256: `3857b7a382f0798fab9d24f424207516fadb672eea5aad9d687761443b581ed7`
- signer certificate SHA-256:
  `37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224`

The APK has four ZIP entries, no packaged DEX, no permission, component or shared UID, and one
compressed AArch64 library. APK Signature Scheme v2 verifies with one non-DJI signer. The ELF has no
init/preinit/fini array, exports only `Agent_OnAttach`, depends only on `liblog.so` and `libc.so`, has
an exact pthread/clock/log/memory import allowlist, and uses non-executable stack, RELRO and immediate
binding. The embedded 792-byte DEX occurs once and defines only `RawCallback`: one trivial
constructor plus the two native callback declarations.

## Zero-send proof for this build

In the packaged code's corresponding unstripped image:

1. `route_snapshot_resolve` at module RVA `0x444c` zeroes the snapshot and returns `1`
   (`ROUTE_STATUS_UNRESOLVED`).
2. `Agent_OnAttach` compares that return to `ROUTE_STATUS_RESOLVED == 0` and branches from
   `0x2818` to the release path at `0x2830`; it cannot fall through to the bridge.
3. `route_snapshot_epoch_unchanged` at `0x44ac` independently returns false. Both the agent and
   `jni_bridge_send_once` test it before the attempt/send guard.
4. The only `CallStaticLongMethodA` vtable slot load is at `0x3dbc`, downstream of all three gates.

The unreachable call shape is exactly version `1`, command `0x03/0x77`, command type `2`, request,
encryption-selector intent `3`, route-supplied sender/receiver, retry `0`, interval `500`, and one-byte
body `[0x02]`. There is no loop or second send call site. A single `native_CancelSend` call site is
reachable only after the local deadline of a hypothetical admitted send.

## Callback lifetime and residual race

The callback pointer targets process-static `AttemptState`; it is deliberately not cleared, so a late
callback does not dereference stack or freed state. DJI's raw path establishes a Java global reference
for the callback and releases it through the shared callback owner. Android 11 ART also deliberately
does not close an agent library when the temporary `Agent` is destroyed, including a nonzero
`Agent_OnAttach` return, so registered native callback code remains mapped. This was cross-checked
against AOSP Android 11 `runtime/ti/agent.cc`.

There is nevertheless a terminal-quiescence race in a future live build. The bridge treats a quiet
100 ms interval as success, but ACK delivery precedes pending-node erase, timeout delivery precedes
copied-owner destruction, and explicit cancel only posts core cleanup after removing the SDK Stopper
ID. A callback already admitted through the Stopper can still finish after cancel returns. The static
state prevents memory corruption, but it does not make the success verdict fail closed. A future
build requires ordered registration, callback-return/in-flight-zero proof, and a post-terminal worker
tail fence that proves the exact pending handle and Stopper ID absent. The permanent unresolved route
means this cannot occur in the reviewed APK. See `../eid_callback_lifetime_audit_20260828.md`.

There are two related future-live gaps. First, the current epoch checks occur before in-memory helper
construction and are not repeated immediately before the JNI call or after callback quiescence, so a
connection change during setup/wait is not yet excluded. Second, the Android 11 AOSP no-`dlclose`
behavior protects late callbacks on the reference runtime, but the target vendor runtime must be
verified or the live agent must retain itself independently of the operation's success status. Neither
gap changes the zero-send conclusion for the packaged offline carrier.

## Audit hardening

An older `build/inspect.so` was found with constructor entries and outline-atomic runtime imports. It
was not the packaged library, but its ambiguous name could mislead a later reviewer. The build now
removes that generated mirror before compilation, recreates it atomically from the final signed APK,
and the audit requires byte identity. The audit also checks the README's APK/SO sizes and hashes, an
exact ELF import allowlist, all init/preinit/fini tags, and the deterministic generated helper include.

Only the exact APK in `dist/` is reviewed. Files under `app/build/` and `build/package-stage/` are
intermediate products and must not be installed.
