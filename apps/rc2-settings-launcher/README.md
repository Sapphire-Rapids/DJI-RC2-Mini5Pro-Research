# FindUAS RC 2 Settings Launcher

Status: **STATIC**. The source contract performs no automatic device action. This independently
written source is covered by the repository-root [MIT license](../../LICENSE). Generated APKs and
signing material are intentionally not committed.

Version 1.0.0 is a deliberately minimal, user-driven launcher for two standard Android Settings
pages that DJI removed from the visible RC 2 menu. It was designed against the exact archived
RC331 10.00.0700/0205 Settings APK audit.

## What it does

The launcher shows exactly two buttons:

1. `android.settings.DEVICE_INFO_SETTINGS` — opens the hidden device/about page.
2. `android.settings.APPLICATION_DEVELOPMENT_SETTINGS` — opens Developer options after Android's
   normal seven-tap gate has been completed.

The on-device sequence is:

1. Open device information.
2. Tap **版本号** seven times until Android reports **您现在处于开发者模式！**.
3. Return to this launcher and open Developer options.
4. Manually enable **USB 调试** and accept Android's warning.

Do **not** enable OEM unlocking and do **not** use Reset options.

## Deliberate safety boundary

- No Android permissions.
- One launcher Activity; no service, receiver, provider or background component.
- No network, socket, file, shell, ADB, Binder, native library, JNI, DJI API, DJI protocol or DUML.
- No setting is read or written. Navigation occurs only after a foreground user click.
- `ActivityNotFoundException`, `SecurityException` and other runtime launch failures produce a
  Chinese status/toast rather than a crash.
- It does not bypass Android's Developer-options gate. Before the seven taps, the exact RC 2
  firmware routes the second action to its toast-only disabled activity.

## Build and audit

Requirements used for the sealed build:

- Android Gradle Plugin 8.7.0
- Gradle 8.10.2
- JBR/OpenJDK 21.0.8 (the app bytecode target remains Java 8 for Android compatibility)
- Android SDK / Build Tools 35.0.0

Run:

```sh
export JAVA_HOME=/path/to/jdk-21
export ANDROID_HOME=/path/to/android-sdk
# Optional when Gradle 8.10.2 is not already on PATH:
export GRADLE_BIN=/path/to/gradle-8.10.2/bin/gradle
./scripts/build_and_audit.sh
./scripts/reproducibility_check.sh
```

The first command runs 3 JVM contract tests, Android lint, assembles the debug-signed APK, then
performs a fail-closed manifest/ZIP/DEX/signature/zipalign audit. The second command performs two
independent clean assemblies and requires byte-for-byte equality.

## Sealed artifact record

The historical reviewed APK was named `FindUAS-RC2-Settings-Launcher-1.0.0.apk`; the binary is not
distributed in this source repository.

- size: 15,805 bytes
- SHA-256: `ea418e791635e2e2bf9c4be5ab7a59bf278719a85736d8a02ab6cfd44941930a`
- signer certificate SHA-256:
  `37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224`
- package/version: `com.finduas.rc2settingslauncher`, `1.0.0` (`versionCode 1`)
- audit: 0 permissions; 1 Activity; 0 services/receivers/providers/native libraries; exact two
  standard Settings actions; signature and zipalign verified
- verification: 3/3 JVM contract tests and Android lint passed; two clean assemblies were
  byte-for-byte identical

The original delivery-session SD-card copy matched the sealed SHA-256 immediately after copying;
the local volume path and device media are intentionally omitted here.

This project does not install the APK. Installation and every settings change remain separate,
explicit user actions.
