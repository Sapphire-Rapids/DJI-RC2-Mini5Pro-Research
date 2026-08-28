# Android 11 cross-package JVMTI load boundary audit

Updated: 2026-08-28 (Asia/Shanghai)

## Conclusion

An absolute path to the carrier's extracted library is **plausible on baseline AOSP Android 11, but
is not admitted for the RC 2 yet**.

AOSP has three favorable properties:

1. `ActivityThread.handleAttachAgent()` first passes DJI Fly's class loader and, after an
   `IOException`, retries once with a null class loader.
2. Android 11 app linker namespaces put `/data` and `/mnt/expand` in the permitted path list for
   absolute native loads. The namespace search path still belongs to the target APK, but an
   absolute path under `/data/app/...` is not rejected solely because it is outside that search
   path.
3. AOSP SELinux permits `appdomain` to search/read/execute `apk_data_file`; this is the label normally
   used for installed APK/native-library material.

Those are necessary facts, not proof about DJI firmware `07.00.0100`. OEM linker configuration,
actual DAC modes, actual labels, target ABI, target process flags and system-server permission can
still reject the operation. No install or attach was performed in this work.

V0 stops after `GetVersionNumber`. It deliberately does not call `GetLoadedClasses`: the JVMTI
contract says the returned `jclass` objects are JNI local references that must be managed. Keeping a
class count would therefore require a `JNIEnv` and expand the in-process surface. The official
contract is [JVMTI 11 `GetLoadedClasses`](https://docs.oracle.com/en/java/javase/11/docs/specs/jvmti.html#GetLoadedClasses).

## Exact AOSP path

The one-shot path is:

```text
privileged caller
  -> ActivityManagerShellCommand attach-agent
  -> ActivityManagerService.attachAgent
  -> target ActivityThread.handleAttachAgent
  -> VMDebug.attachAgent
  -> ART Runtime::AttachAgent
  -> AgentSpec::DoDlOpen / OpenNativeLibrary
  -> dlsym("Agent_OnAttach")
```

Important details:

- The shell command requires `android.permission.SET_ACTIVITY_WATCHER`, declared by AOSP with
  `protectionLevel="signature"`. Running `/system/bin/cmd` does not elevate an ordinary app: the
  new process and its Binder shell-command call retain the originating app UID. Baseline AOSP
  `checkComponentPermission()` grants a verified actual UID 1000 caller through its system-UID fast
  path, but merely executing `cmd` or being debuggable does not make an ordinary app UID 1000.
- `ActivityManagerService.attachAgent()` accepts a non-debuggable application only when
  `ro.debuggable=1`.
- Zygote also sets `DEBUG_ENABLE_JDWP` for every newly spawned app when `ro.debuggable=1`; ART's
  native entry then independently checks `Dbg::IsJdwpAllowed()`.
- ART uses the supplied class loader's library search path, calls `OpenNativeLibrary`, resolves
  exactly `Agent_OnAttach`, and calls it. A nonzero result is treated as initialization failure.
- The first load uses the target app class-loader namespace. On AOSP 11 its absolute permitted path
  includes `/data`, while dependencies remain restricted. This canary depends only on `liblog.so`
  and `libc.so`, both public system libraries.
- The null-class-loader retry uses plain `dlopen()` in the process context. It is a fallback, not a
  promise that an OEM anonymous/default namespace accepts the path.

Primary sources:

- [Android 11 `ActivityThread.handleAttachAgent`](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-11.0.0_r48/core/java/android/app/ActivityThread.java#3922)
- [Android 11 shell permission check for `attach-agent`](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-11.0.0_r48/services/core/java/com/android/server/am/ActivityManagerShellCommand.java#2863)
- [Android 11 `ActivityManagerService.attachAgent`](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-11.0.0_r48/services/core/java/com/android/server/am/ActivityManagerService.java#20078)
- [Android 11 Zygote `ro.debuggable` handling](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-11.0.0_r48/core/java/com/android/internal/os/Zygote.java#895)
- [Android 11 ART `VMDebug_nativeAttachAgent`](https://android.googlesource.com/platform/art/+/refs/tags/android-platform-11.0.0_r40/runtime/native/dalvik_system_VMDebug.cc#573)
- [Android 11 ART agent loading and callback resolution](https://android.googlesource.com/platform/art/+/refs/tags/android-platform-11.0.0_r40/runtime/ti/agent.cc#52)
- [Android 11 `OpenNativeLibrary`](https://android.googlesource.com/platform/art/+/refs/tags/android-platform-11.0.0_r40/libnativeloader/native_loader.cpp#106)
- [Android 11 app namespace `/data` permitted path](https://android.googlesource.com/platform/art/+/refs/tags/android-platform-11.0.0_r40/libnativeloader/library_namespaces.cpp#57)
- [Android 11 `apk_data_file` read/execute policy](https://android.googlesource.com/platform/system/sepolicy/+/refs/tags/android-11.0.0_r48/public/app.te#278)

The adjacent RC331 image's compiled policy independently contains the corresponding
`appdomain -> apk_data_file` search/read/map/execute rules in:

```text
work/rc2_research/firmware/rc331/10.00.0700/0205/working/
system_static_full/etc/selinux/plat_sepolicy.cil
```

That adjacent image is evidence, not a substitute for live `07.00.0100` labels.

Target admission is a separate gate. AOSP ActivityManager permits attach only when the target
application is debuggable or the build is globally debuggable; ART then independently requires
`Dbg::IsJdwpAllowed()`. Making only the *caller* app debuggable satisfies neither the signature
permission nor the target-side ART condition. The start-time `ProfilerInfo.agent` field does not
provide a safe shortcut: it requires a target lifecycle transition/exported start surface and a
target-readable agent path, and is therefore more invasive than this already-unadmitted one-shot
path.

## Mandatory live gates before any attach

There is currently no admitted command launcher. A complete static audit of all 30 activities,
two receivers and one service in the adjacent stock `dpad_fuli` found no exported Intent,
PendingIntent, receiver, service or Binder route that executes one fixed command as UID1000 and
returns argv/stdout/stderr/exit status. In addition, opening `ShellCommandActivity` automatically
calls `haveRoot()`, which starts `adb shell su` and writes a
test command, and then runs `adb version`. Its executor preserves only stdout, not stderr or the
exit status; AOSP `runAttachAgent()` emits no success text. Therefore a blank result cannot prove
success, and that page must not be opened for V0. An exact-target, side-effect-free caller that
demonstrably passes `SET_ACTIVITY_WATCHER` enforcement, with argv/stdout/stderr/exit-status
capture, is an
additional hard gate.

The component-by-component evidence is recorded in
`../dpad_fuli_exported_caller_audit_20260828.md`.

The v0.8 capability page must establish all of the following from the actual RC 2:

1. Android release/API and `ro.debuggable=1`;
2. DJI Fly package/process is really `dji.go.v5`, its `ApplicationInfo.FLAG_DEBUGGABLE`, appId,
   signer and packaged/native ABI;
3. `com.dpad.fuli` is stock, DJI-platform-signed, enabled, UID/appId 1000 and able to run only the
   intended command surface;
4. target process is 64-bit AArch64 and the packaged DJI Fly native ABI agrees;
5. SELinux mode plus the carrier library's exact `nativeLibraryDir`, owner, mode and label;
6. target process exists and is stable while aircraft motors are off;
7. no upgrade/recovery marker or other unsafe device state is active.

The v0.8 exact `dpad_fuli` package verdict can transfer the adjacent exported-surface audit only
when the whole APK, version, signer, split count and scan-stability gates all match. The independent
framework/server verdict is still required for AOSP/DJI service ABI reasoning; neither verdict
creates a caller.

The carrier is **arm64-v8a only**. A missing or contradictory live ABI value is a stop condition,
not a reason to try the library.

## Copy-to-target `code_cache` audit

Copying the library into DJI Fly's `code_cache` could avoid the cross-package native-library path,
but it is a target-data write and is therefore **not implemented and not authorized by this
artifact**.

The path is feasible only if live evidence proves every one of these conditions:

- DJI Fly and the privileged helper share the exact appId/UID, or another legitimate mechanism can
  write as DJI Fly's UID;
- DAC ownership/mode permits traversal and creation;
- the writer's SELinux domain may create the target label and the DJI Fly domain may map/execute it;
- a new, collision-free filename is used and its SHA-256 is verified after the copy;
- DJI Fly can be safely restarted before cleanup, with aircraft/motors off.

If DJI Fly does not share UID 1000, stock Android 11 `run-as` does not solve this from
`com.dpad.fuli`: AOSP restricts `run-as` callers to root or shell, and separately requires the
package's own debuggable flag. `ro.debuggable=1` does not change that package flag. See the
[Android 11 `run-as` checks](https://android.googlesource.com/platform/system/core/+/refs/tags/android-11.0.0_r48/run-as/run-as.cpp#164).

Do not use `code_cache/startup_agents`. Android intentionally auto-loads every file there on later
debuggable app starts; that is persistent behavior, not a one-shot canary. The AOSP behavior is in
[`handleAttachStartupAgents`](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-11.0.0_r48/core/java/android/app/ActivityThread.java#3937).

If a future, separately approved code-cache experiment is admitted, rollback must be: restart DJI
Fly so the agent is no longer executing, remove only the unique verified canary file, then prove the
file is absent. Never overwrite an existing file and never place the canary in `startup_agents`.

## Closed failure set

| Gate/failure | Observable result | Canary effect |
|---|---|---|
| wrong/missing AArch64 ABI | ELF loader error | `Agent_OnAttach` never runs |
| carrier library was not extracted | path absent | attach rejected before entry |
| DAC or SELinux denial | permission/AVC error | attach rejected before entry |
| target linker namespace denial | `dlopen` error; framework may try null loader once | no class scan unless retry succeeds |
| missing public dependency or missing exported symbol | loader/symbol error | entry never runs |
| caller lacks signature permission `SET_ACTIVITY_WATCHER` | shell-command security failure | target receives no attach request |
| target not JDWP-allowed | framework/ART security failure | library not loaded |
| non-empty agent options | fixed error code `1`, return `JNI_ERR` | options are not parsed or logged |
| JVMTI environment unavailable | fixed error code `3`, return `JNI_ERR` | no JVMTI query runs |
| JVMTI version read fails | fixed error code `4`, return `JNI_ERR` | no further action |
| JVMTI environment disposal fails | fixed error code `5`, return `JNI_ERR` | stop before V1 |

Even a minimal native library runs inside DJI Fly. A loader/ABI bug can still crash the process;
therefore the closed failures above are design expectations, not a zero-risk guarantee. This is why
the live gates precede an authorized attach.
