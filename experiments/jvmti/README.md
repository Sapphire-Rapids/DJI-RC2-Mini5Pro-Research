# JVMTI research experiments

These are independently written, source-only Android 11/AArch64 experiments from the RC 2 / Mini
5 Pro research record. Generated APK/JAR/SO/DEX files, Gradle/CMake output, signing keys, vendor
binaries and decompiled vendor source are intentionally absent.

None of these directories is a supported Remote ID control product. The preserved status labels
are part of the result:

| Directory | Status | Meaning |
| --- | --- | --- |
| `jvmti_attach_canary/` | `NOT ADMITTED` | Minimal no-op attach canary; never installed or attached. |
| `jvmti_eid_resolver_v1/` | `NOT ADMITTED` | Semantic-anchor resolver only; never installed or attached. |
| `jvmti_eid_raw_get_v2/` | `NOT ADMITTED` | Permanently unresolved, fixed-zero-gated raw-GET prototype. |
| `jvmti_eid_route_resolver_v2_1/` | `NOT ADMITTED` | Offline route/symbol preflight with a fixed-zero exception gate. |
| `revoked-v2.2/` | `RETRACTED` | Rejected artifact retained for audit history; do not install or attach. |
| `jvmti_eid_route_resolver_v2_3/` | `NOT ADMITTED` | V2.2 corrections implemented, but no independent post-fix live admission and no device run. |

Each project contains its original status, contracts, build inputs and audit scripts. Host tests
that need exact DJI Fly native samples require an external, lawfully obtained fixture tree; those
vendor files are not redistributable and are not included here. Set
`FINDUAS_RESEARCH_FIXTURE_ROOT` to that external research root when a script explicitly requests
it.

## Common build inputs

The projects were authored for Android Gradle Plugin 8.7.0, Gradle 8.10.2, SDK/build-tools 35,
CMake 3.22.1 and NDK 27.2.12479018. Configure tools through environment variables rather than
editing scripts:

```sh
export ANDROID_SDK_ROOT=/path/to/android-sdk
export JAVA_HOME=/path/to/jdk
export FINDUAS_RESEARCH_FIXTURE_ROOT=/path/to/private-research-fixtures
```

Put `gradle` on `PATH`, or set the project-specific `FINDUAS_*_GRADLE_BIN` variable documented by
the script. A debug keystore defaults to `$HOME/.android/debug.keystore`; its private key is never
part of this repository.

## Sealed hashes and relocated rebuilds

Artifact hashes recorded by individual projects describe historical reviewed binaries, which are
not redistributed here. A source assembly from another checkout may complete and then stop at the
final digest check. In the attach-canary verification, the only stripped-native-library difference
was the 20-byte GNU build ID, which changed with the build environment. This fail-closed result is
intentional: do not replace a sealed hash or weaken an audit merely to admit a relocated rebuild.
A newly versioned artifact needs its own review and status decision.

The repository's MIT license applies only to independently written material. The vendored AOSP
Android 11 `jvmti.h` has its own GPLv2-with-Classpath-Exception terms; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
