# FindUAS FlySafe ART TI staging payload

Status: **NEGATIVE on a disposable emulator; NOT ADMITTED on RC 2**.

This source-only project puts the adjacent query-only ART TI library into an APK as an uncompressed,
page-aligned native entry. The manifest has no launcher, service, receiver, provider or permission,
and no application classes are written. AGP nevertheless emits one 600-byte synthetic `R`-class
DEX, so the final APK is not described as DEX-free. It has no network path or setter and is not meant
to be installed.

## Why a temporary install session is needed

Android 11's agent loader treats the first `=` in an agent specification as the beginning of agent
options. A normal modern `/data/app/~~...==/.../lib/...so` path is therefore truncated and cannot be
passed directly to `attach-agent`. A generic writable trace path was also rejected in the emulator:
the exact agent entered a native crash before its canary, while the same bytes loaded cleanly from
an `apk_data_file` path.

An uncommitted PackageInstaller session provides a temporary path shaped like:

```text
/data/app/vmdl<session>.tmp/base.apk!/lib/arm64-v8a/libfinduas_flysafe_query.so
```

It contains no `=` and can be abandoned after a one-shot experiment. On the disposable emulator,
system UID could create the session and stream the payload, but the staging directory received the
`apk_tmp_file` label. DJI Fly was denied directory search before the agent loaded; no canary or query
callback appeared and the PID remained unchanged. Abandon succeeded and removed the staging
directory. This is a completed negative, not an RC 2 candidate.

## Build

```sh
export FINDUAS_ANDROID_SDK_ROOT=/path/to/android-sdk
export FINDUAS_JDK_ROOT=/path/to/jdk
export FINDUAS_ANDROID_NDK_ROOT=/path/to/android-ndk
export FINDUAS_GRADLE_BIN=/path/to/gradle
sh scripts/build_and_test.sh
```

Generated DEX/SO/APK files remain ignored. The final APK's agent entry must be `Stored`, not deflated;
the synthetic `R` DEX must be recorded rather than hidden.

## RC 2 boundary

Do not repeat this staging route on RC 2 merely because Developer Assistant has system UID. The
emulator `apk_tmp_file` denial and RC 2's still-unobserved live target domain/path policy must first
be replaced by positive static or live evidence for a target-searchable executable label. Any future
first RC 2 execution remains query-only; no motor action or RF claim follows from it.
