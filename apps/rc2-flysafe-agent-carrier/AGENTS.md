# AGENTS.md

This file applies to `apps/rc2-flysafe-agent-carrier/`.

## Scope

This project is a minimal carrier and command-display utility for the source-only ART TI agent in
`../../experiments/jvmti/jvmti_flysafe_inprocess_query/`. It packages the independently written
AArch64 library with legacy native-library extraction enabled, displays its exact installed path,
and lets a foreground operator copy fixed diagnostic commands.

The app must never execute those commands itself, request privileged permissions, bundle vendor
code, write DJI state, or imply that installation alone attaches the agent. The normal extracted
library path is now a known emulator negative because modern `/data/app/...==/...` paths are split
at the first `=` by the Android 11 agent-spec parser. Keep this project as a reproducible negative,
not an RC 2 candidate. RC 2 execution remains `NOT ADMITTED` until a different admitted loader
records a same-process query callback and an unchanged DJI Fly PID.

## Build boundary

- Build the agent from the adjacent public source; never commit the generated DEX, SO, APK, signer,
  SDK path, or Gradle output.
- Keep `android:extractNativeLibs="true"` and legacy JNI packaging: reproducing the exact modern
  installed path and its delimiter failure is the purpose of this carrier.
- Keep the target package fixed to `dji.go.v5` unless exact live evidence requires a documented
  change.
- The command must not contain shell quoting. DJI Developer Assistant's observed implementation
  passes one string to `Runtime.exec(String)`, where quote characters would be literal tokens.
- Logs may contain only the privacy-reduced ART TI result already defined by the agent. Never add
  license IDs, raw callback bytes, account/device identifiers, or coordinates.

## Validation

Run host tests, build the adjacent agent, build/lint the APK, and inspect the final manifest/native
entry. The disposable-emulator reproduction is complete; do not propose or repeat the same normal
installed-path attach on RC 2. Do not unlock a bootloader or modify boot, vendor_boot, vbmeta, TEE,
QFPROM, or eFuse.
