# FindUAS DJI Fly EID semantic-anchor resolver V1

Status: **NOT ADMITTED**. Offline implementation only; never copied to a device, installed or
attached.

This ARM64 JVMTI agent is the read-only step after the V0 attach canary. It answers only whether
the already-running DJI Fly process has loaded exactly one France-EID subject thunk and exactly
one current France-EID capability-gate thunk under one shared ClassLoader.

## Artifact

```text
dist/FindUAS-JVMTI-EID-Resolver-V1-0.1.0-arm64-v8a.apk
SHA-256: ccdf198c83ecdd3d33a54192e2bffeb9ab89ce65289497643d16f5a00bff62b2
applicationId: com.finduas.jvmti.eidresolver.v1
ABI: arm64-v8a only
native entry: lib/arm64-v8a/libfinduas_eid_resolver_v1.so
```

The ordinary local signer grants no DJI/system privilege. The APK has no DEX, permission,
component or shared UID.

## Exact runtime scope

`Agent_OnAttach`:

1. rejects non-empty options;
2. obtains JVMTI 1.2 and the current thread's `JNIEnv` without attaching a new thread;
3. enumerates already-loaded classes once;
4. compares class signatures only with the two exact semantic anchors embedded in the binary;
5. verifies that exact matches use one ClassLoader;
6. deletes every returned class/loader local reference, every temporary global loader reference,
   and every JVMTI-allocated class array/signature buffer;
7. releases the per-call JVMTI environment;
8. emits one fixed-format line whose values are numeric only, and returns.

The two exact anchors are DJI Fly's generated Kotlin function-reference classes for
`electronicIDBroadcastOn` and `electronicIDBroadcastExisted`. V1 does not initialize or load them,
does not access a field, and does not invoke `Function0` or any Java method.

```text
FINDUAS_EID_RESOLVER_V1 error_code=N loaded_count=N on_anchor_count=N \
gate_anchor_count=N unique_loader_count=N
```

Success requires `error_code=0`, both anchor counts exactly 1 and loader count exactly 1. This
proves only the semantic anchor/ClassLoader topology for the France EID path. It is not a GET,
does not prove the aircraft supports EID, and says nothing about FAA/global RID.

## Hard exclusions

- no class initialization/loading or Java method/field access;
- no `Function0.invoke`, key/subject access, GET, LISTEN or SET;
- no socket, localhost, file, property, process/thread, Binder, Parcel or DUML;
- no JVMTI capability, event, hook, breakpoint, redefine or retransform;
- no class names, loader identities, paths, identifiers or DJI data in logs;
- no background callback, startup-agent entry point or persistence mechanism.

See [NO_CONTROL_CONTRACT.md](NO_CONTROL_CONTRACT.md) and [LIVE_ADMISSION.md](LIVE_ADMISSION.md).

## Build and audit

```sh
sh scripts/build_and_audit.sh
```

The final auditor enforces source/JVMTI/JNI allowlists, exactly two allowed `com.uav` anchor
strings, pinned AOSP header hash, exact ZIP inventory, constrained manifest/signature/ELF surfaces,
README artifact hash and forbidden strings. Two clean builds produced the same APK hash. Only the
postprocessed `dist/` APK is admissible for later review.

## Live order — not authorized yet

1. Run v0.8 and close the exact RC 2 identity/debug/ABI/helper/SELinux/load-path gates.
2. Install and attach V0 only after separate review; require a successful V0 log and stable DJI Fly.
3. Only then may V1 be considered, with motors off and a planned DJI Fly restart as rollback.
4. A V1 success does not authorize the getter or any setter.
