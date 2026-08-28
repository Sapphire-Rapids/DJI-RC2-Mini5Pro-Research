# V1 no-control contract

## Runtime allowlist

- `JavaVM.GetEnv` for JVMTI 1.2 and current-thread JNI 1.6;
- JVMTI `GetLoadedClasses`, `GetClassSignature`, `GetClassLoader`, `Deallocate`,
  `DisposeEnvironment`;
- JNI exception check/owned-exception cleanup and local/global reference management only;
- exact comparison against the two compiled semantic anchor signatures;
- one fixed-format Android log record whose values are numeric only.

Every `jclass` from `GetLoadedClasses` is a JNI local reference and is deleted. Every loader local
reference is deleted. Loader comparison uses at most two temporary global references, both deleted
before return. The JVMTI class array and every signature buffer are deallocated; unused generic
signatures are not requested.
The per-call JVMTI environment is disposed before the agent returns.

## Denylist

- Java class loading/initialization, method lookup/invocation, field access or object construction;
- Kotlin reflection, `Function0`, FlySubject, KeyManager/JNIKeyValue or any DJI business API;
- GET, LISTEN, SET, protocol packet or Remote ID mutation;
- JVMTI events/capabilities/hooks/redefine/retransform;
- network/local socket, file/property, process/thread, Binder/Parcel or DUML;
- raw names, paths, references or identifiers in logs;
- startup/persistent agent behavior.

Any mismatch in the build audit or runtime cardinality is a hard failure.
