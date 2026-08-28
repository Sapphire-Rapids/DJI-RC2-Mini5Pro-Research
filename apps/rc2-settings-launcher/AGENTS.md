# Agent handoff: RC 2 Settings Launcher

## Scope lock

This directory is intentionally independent from `minimal_rid_observer` and every RID/JVMTI
carrier. Keep it a two-button standard-Intent launcher only.

Hard invariants:

- application ID: `com.finduas.rc2settingslauncher`;
- version: `1.0.0` / versionCode 1;
- no permissions;
- exactly one launcher Activity;
- no service, receiver, provider, background work or native library;
- no network, file, shell, subprocess, ADB, Binder, reflection, DJI SDK/protocol or DUML;
- button 1 uses only `android.settings.DEVICE_INFO_SETTINGS`;
- button 2 uses only `android.settings.APPLICATION_DEVELOPMENT_SETTINGS`;
- no direct component enablement, Settings provider write or hidden-fragment launch;
- no automatic settings changes and no automatic retry;
- retain the Chinese order and the warning against OEM unlocking and Reset options.

If either standard action is unavailable or denied, fail closed with an on-screen message. Never
add a privileged fallback.

## Verification

Run both:

```sh
./scripts/build_and_audit.sh
./scripts/reproducibility_check.sh
```

Do not install the artifact as part of build, test or audit. Do not invoke `adb` from this project.
Generated APKs and signing material remain outside Git. Any future source change invalidates the
historical sealed APK hash and requires both checks plus a new static review.
