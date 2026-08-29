# FindUAS RC 2 FlySafe agent carrier

Status: **NEGATIVE on a disposable emulator; NOT ADMITTED on RC 2**.

This source-only Android app packages the independently written AArch64 ART TI query agent from
[`../../experiments/jvmti/jvmti_flysafe_inprocess_query/`](../../experiments/jvmti/jvmti_flysafe_inprocess_query/).
Its launcher displays the exact extracted library path and provides copy buttons for three fixed
commands:

1. read the current DJI Fly PID;
2. ask Android ActivityManager to attach the query agent to `dji.go.v5`;
3. read only the agent's privacy-reduced log tag.

The carrier does **not** execute a command, attach to another process, access DJI data, send a
FlySafe setter, start motors, or request Android permissions. Installation alone has no effect on
DJI Fly or aircraft state.

## Observed delimiter failure

On Android 11, ActivityManager parses an agent specification as `library[=options]`. A normal modern
installed path contains `==`, for example `/data/app/~~...==/.../lib/arm64/...so`. The disposable
emulator therefore truncated the displayed path at its first `=` and failed before loading the
agent. DJI Fly's PID remained unchanged and no FindUAS canary or query callback appeared.

This closes the carrier's ordinary installed-path command as a loader candidate. The source is
retained because it reproduces the exact failure and packages the same independently written agent
bytes used by the positive control. Do not install or run this APK on RC 2 for the same experiment.

Any replacement RC 2 loader remains query-only. Success requires all of the following in one
session:

- DJI Fly PID recorded before attach;
- one `FLYSAFE_RAW_AGENT ... dispatched=1` line;
- one success or failure callback line;
- the same DJI Fly PID after attach.

A callback failure is still useful transport evidence but is not inventory, entitlement, RID state
or RF evidence. No setter is packaged by this agent.

## Build

Set the local tool roots without editing checked-in files:

```sh
export FINDUAS_ANDROID_SDK_ROOT=/path/to/android-sdk
export FINDUAS_JDK_ROOT=/path/to/jdk
export FINDUAS_ANDROID_NDK_ROOT=/path/to/android-ndk
export FINDUAS_GRADLE_BIN=/path/to/gradle
sh scripts/build_and_test.sh
```

The script first tests/builds the adjacent query agent, copies its generated SO into an ignored
Gradle JNI input directory, then runs unit tests, lint and `assembleDebug`. Generated DEX, SO and APK
files remain local and must not be committed.

## Distribution boundary

Only original source, tests and documentation are published. The repository contains no DJI APK,
firmware, runtime dump, decompiled source, account material, license data, device identifier or
generated native/APK binary.
