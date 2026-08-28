# Research source projects

This directory map defines where the published, independently written RC 2 / Mini 5 Pro research
source belongs. It is both a handoff index and an import policy. Presence in this table means the
source is published; it does **not** mean that it was installed, executed, admitted, or proved to
change Remote ID behavior on a device.

## Layout

| Directory | Intended contents | Publication boundary |
| --- | --- | --- |
| `apps/` | Buildable Android research apps, manifests, resources, unit tests, and build scripts | Source only; no APKs, signer material, local SDK paths, Gradle/CMake output, or vendor libraries |
| `experiments/` | Narrow prototypes retained to explain an admitted, rejected, retracted, or unresolved route | Each project must state `OBSERVED`, `NOT ADMITTED`, `RETRACTED`, or `UNKNOWN` and must not imply live success from compilation |
| `libraries/` | Host-testable codecs, parsers, state machines, and synthetic fixtures | Independently written source and synthetic data only |
| `host-tools/` | Small USB/ADB/firmware-analysis probes, patch generators, and tests | No device serials, raw captures, vendor binaries, patched binaries, or generated distributions |

## Published source set

| Destination | Project role | Recorded status at publication |
| --- | --- | --- |
| `apps/rc2-rid-admin/` | Current FindUAS RC 2 RID query/management APK source and unit tests | Mixed: A-028 was built/run; current A-033 was audited and staged but is uninstalled/unrun; the source also contains gated or unresolved controls |
| `apps/rc2-settings-launcher/` | Minimal launcher for hidden Android settings on RC 2 | Utility source; installation/use does not establish RID behavior |
| `apps/rid-admission-probe/` | Zero-permission v0.10 Android admission probe and retained historical observer source | v0.10 `NOT ADMITTED`; historical localhost observer is `RETRACTED` and must remain excluded from the active source set |
| `libraries/rid-switch-controller/` | Bounded-lease/control state model | Host-tested model; not a proven device transport |
| `libraries/rid-switch-wire-codec/` | FlySafe query/set wire codecs and correlator | Static/host-tested; not a live Mini 5 Pro control result |
| `libraries/rid-type6-inventory-parser/` | Strict V3/V4 type-6 inventory parser | Static/host-tested compatibility parser |
| `libraries/rid-quiescence-model/` | Request-quiescence model and Python tests | Model only; does not prove Android runtime quiescence |
| `libraries/protocol-probes/` | Bounded Python codecs, parsers, read probes and passive listeners | 68 synthetic host tests passed; device acceptance and RF effects remain `NOT ADMITTED` |
| `host-tools/adb-handshake-probe/` | Minimal libusb ADB descriptor/handshake probe and tests | Live v07 currently reaches host `CNXN` with no device ADB packet before timeout |
| `host-tools/adbd-userspace-patch/` | Exact-input userspace `adbd` gate patch generator and tests | Patch logic only; do not include input/output binaries; not yet a live v07 shell result |
| `host-tools/system-uid-bridge-probe/` | Small system-UID protocol checks and readonly EID helper source | Research helpers; preserve their local admission contracts |
| `host-tools/device-read-probes/` | Fixed-route RC 2/Mini 5 Pro GET and USB-IN-only probes | Source and synthetic tests; a GET reply is not RF/compliance proof |
| `host-tools/firmware-acquisition/` | Target-locked official-metadata and firmware-download helpers | Source and synthetic tests only; downloaded firmware is excluded |
| `host-tools/imah-analysis/` | IMaH audit and deliberately non-flashable integrity experiment wrappers | Offline source only; upstream GPL tool and firmware are external |
| `host-tools/elf-analysis/` | AArch64 ELF inspection helpers and one fixed runtime-route manifest | Static analysis only; vendor ELF inputs and output are excluded |
| `host-tools/ghidra-scripts/` | Targeted Ghidra symbol/xref/decompiler helpers | Source only; no program database, vendor binary, or decompiler output |
| `host-tools/runtime-dex-scan/` | Small bounded DEX-image scanner for an already authorized raw-memory file | Host-tested source and synthetic tests only; no process dumper, vendor memory, DEX or decompiled output |
| `experiments/device-write/` | Historical bounded country/area round-trip scripts | FC/Sky `CN -> US -> CN` observed; Ground write unacknowledged; no RID/RF conclusion |
| `experiments/jvmti/` | Six source-only Android/JVMTI research stages | V2.2 is `RETRACTED`; V2.3 and the other stages remain `NOT ADMITTED` |

Decompiled DJI/Fly/Fuli trees, extracted framework code, firmware, public-repository clones, Ghidra
projects, virtual environments, raw logs, and downloaded commercial tools remain references rather
than publication candidates.

## Import corrections retained in the published tree

- Redact the live USB serial from the ADB handshake report; public reports may use
  `REDACTED-USB-SERIAL` only.
- Replace machine-specific user-home or mounted-volume absolute paths, Gradle-cache, Android-SDK,
  JDK, JADX, and debug-keystore defaults in READMEs and scripts with `PATH` lookup or documented
  environment variables. Never publish a local absolute path merely because it is not a credential.
- Do not copy `minimal_rid_observer_v10_independent_tmp`; it is an audit workspace duplicate of the
  canonical admission-probe tree.
- Do not copy any `dist/` manifest which identifies or depends on a locally generated patched
  vendor binary. A source-only patch generator may document the expected original hash and exact
  changed instruction without redistributing either binary.

## Import checklist

1. Copy source inputs with an allow-list; never copy a whole working directory and clean it later.
2. Preserve the project's README, tests, manifest/build files, and any local `AGENTS.md`.
3. Remove generated `dist/`, `build/`, `.gradle/`, `.cxx/`, `.idea/`, `local.properties`, APK/JAR/SO,
   compiled helper DEX, signing keys, and machine-local paths.
4. Search for device serials, UAS/operator identity, phone/coordinates, account material, tokens,
   ADB keys, and absolute local paths before staging.
5. Build/test from the copied tree. Record commands and tool versions without committing SDK/NDK.
6. Run the repository validators and inspect `git diff --cached --stat` plus
   `git diff --cached --name-only` before publishing.

The repository-level MIT license applies to original source added here unless a project says
otherwise. Third-party headers or fixtures retain their own notices and must be reviewed before
import; a public upstream repository is not automatically vendored into this archive. The included
third-party source inventory is in [`../THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).
