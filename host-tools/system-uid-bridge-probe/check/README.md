# FindUAS system-UID protocol Binder check

This directory contains a deliberately narrow, read-only `app_process` command-line
probe for the DJI RC 2 research track. It has **not** been executed on the RC 2.

## What it does

The Java entry point performs exactly these operations:

1. Rejects execution unless the child process actually inherited Android UID `1000`.
2. Resolves `android.os.ServiceManager.checkService`.
3. Looks up the fixed service name `protocol`, pings it, and requires the exact descriptor
   `com.dji.protocol.IProtocolManager`.
4. Sends synchronous Binder transaction `1` with interface token
   `com.dji.protocol.IProtocolManager`.
5. Reads the boolean returned by `ProtocolManagerService.isEnable()`, rejects trailing Parcel
   data, and prints a
   machine-readable result.

On the adjacent official RC331 firmware used to recover this ABI, transaction 1 only
returns the service's `mEnable` field. `TRANSPORT_ENABLED` therefore means that DJI's
local protocol transport service reports itself enabled. It does **not** mean Remote ID
is enabled, disabled, valid, or broadcasting.

## What it cannot do

- No TCP/UDP/Bluetooth socket is opened.
- No DUML packet is built or sent.
- No listener is registered.
- No arbitrary command or child process is invoked by the Java program.
- No setting, property, file, flight parameter, country, or Remote ID state is written.
- The fixed runner accepts no arguments and only replaces itself with `app_process`.

The probe is an ABI/capability check, not a Remote ID switch.

## Source and build

Requirements used by the checked build:

- OpenJDK 21
- Android SDK platform 35
- Android build tools 35.0.0
- D8/R8 from Android command-line tools
- min API 30 (Android 11)

Build and audit:

```sh
./scripts/build.sh
```

Verify that two clean builds are byte-identical:

```sh
./scripts/verify-reproducible.sh
```

Tool paths can be overridden with the task-specific variables
`FINDUAS_JDK_HOME`, `FINDUAS_ANDROID_SDK`, `FINDUAS_ANDROID_API`,
`FINDUAS_BUILD_TOOLS`, `FINDUAS_MIN_API`, `FINDUAS_R8_JAR`, and
`FINDUAS_JADX_JAR`.

At minimum set `FINDUAS_R8_JAR` to the installed command-line-tools `r8.jar`. JDK and Android SDK
paths may be supplied through `JAVA_HOME`/`ANDROID_SDK_ROOT` or their `FINDUAS_*` equivalents;
`FINDUAS_JADX_JAR` is required by the artifact audit.

Build products:

- `dist/finduas-protocol-check.jar` — DEX JAR for `app_process`
- `dist/run-protocol-check.sh` — fixed, no-argument device runner
- `dist/STATIC_AUDIT.txt` — generated source/DEX/decompilation audit summary
- `dist/SHA256SUMS` — hashes of the three files above

## Result meanings

Successful IPC exits 0 and yields one of:

- `TRANSPORT_ENABLED` / `is_enable=true`
- `TRANSPORT_DISABLED` / `is_enable=false`

Fail-closed results include:

- `SERVICE_ABSENT` — no service was published as `protocol`
- `WRONG_UID` — the launcher did not actually inherit system UID 1000
- `SERVICE_UNREACHABLE` or `DESCRIPTOR_MISMATCH` — the live Binder is not the recovered service
- `LOOKUP_UNAVAILABLE` or `LOOKUP_DENIED` — hidden-API or SELinux/access boundary
- `TRANSACTION_UNSUPPORTED` — service exists but transaction 1 was rejected
- `TRANSACTION_DENIED` — service-side permission denial
- `REMOTE_ERROR` or `MALFORMED_REPLY` — Binder/ABI mismatch or service failure

No failure result falls back to a socket or another transaction.

## Device staging (not performed)

The fixed runner expects both generated files at these paths:

```text
/sdcard/Download/finduas-protocol-check.jar
/sdcard/Download/run-protocol-check.sh
```

It is intentionally not run automatically. Before any RC 2 execution, the parent
research workflow must separately establish that the launcher really inherits DJI's
system-app/system-UID context, that the `protocol` service is present on firmware
`07.00.0100`, and that the DJI upgrade-recovery marker is clear. The recovered ABI is
from adjacent official RC331 firmware, so a live read-only check is still required.

## Evidence boundary

The transaction number and Parcel layout are grounded in excluded, hash-identified RC331 platform
artifacts. See [`docs/08_ANDROID_ADB.md`](../../../docs/08_ANDROID_ADB.md) and the repository
evidence register; the vendor classes and decompiled source are not redistributed here.

The generated audit requires exactly one `IBinder.transact` instruction, verifies it
decompiles as transaction `1` with flags `0`, and rejects networking, DUML/listener,
process-execution, device-setting, and known local broker strings.
