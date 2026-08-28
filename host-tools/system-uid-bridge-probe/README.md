# RC 2 stock system-identity bridge staging index

Date: 2026-08-28 (Asia/Shanghai)

Status: offline artifacts only. Nothing in this directory has been copied to or executed on the
user's RC 2. No aircraft or controller setting has been written.

## Why this branch exists

Adjacent official RC331 firmware contains a DJI-platform-signed, debuggable `com.dpad.fuli`
system application. Although a child it starts would inherit UID 1000, its stock shell page is not
an admitted launcher: opening it automatically attempts `adb shell su`, writes a test command and
runs `adb version`; the executor also drops stderr and exit status. The offline child artifacts
therefore have no approved live launcher. This directory does not authorize opening that page,
patching/resigning the DJI APK or using a second `40007`/`40009` socket.

The exact-v07 package now closes the Fuli package identity, but the Binder Parcelable layout below
still comes from the separately identified adjacent RC331 platform artifact. Live UID, SELinux,
service publication and ABI remain unobserved. The current admission probe is the zero-permission
v0.10 source under `apps/rid-admission-probe`; it is itself `NOT ADMITTED`. Artifact B is not a
staging candidate and remains **DO NOT RUN**.

Only source, tests and fixed runners are published here. Generated JAR/DEX files and their local
audit output remain excluded.

## Artifact A: transport capability check

Directory: `check/`

```text
dist/finduas-protocol-check.jar
bytes 3547
SHA-256 f5965ab122b8c93db8b3aba2606aea09bc27ebbc55fbaee6f9253af1de9f9c70

dist/run-protocol-check.sh
bytes 977
SHA-256 d8960b197acf52761e161eb74f2cea2729ef1c4202daf1a40e81579c831c599e
```

The runner and Java entry point both reject execution outside UID 1000. The program performs
`ServiceManager.checkService("protocol")`, Binder ping, exact descriptor comparison, and one
synchronous transaction `1` (`isEnable`). It rejects trailing reply data. It has no socket, DUML
packet, listener, child-process API or device write. A true result means only that the local DJI
protocol transport service reports `mEnable=true`; it says nothing about RID state.

This is the first protocol candidate that may eventually be staged, but only after the v0.8 page
confirms the stock package/component/signing/upgrade-marker/ABI gates and a separately audited
caller closes the execution boundary. It has not yet been authorized for live use.

## Artifact B: fixed France EID GET

Directory: `eid-get/`

```text
FindUAS-France-EID-GET-readonly.jar
bytes 5286
SHA-256 f288ebb5da11afc66f90eee19dae0a27c309e68e80a69ad619d5f8e909b6b0e4

runner/run-france-eid-get-readonly.sh
bytes 381
SHA-256 acfb44082e0e2ff85eaac3ae05c7d706481c30de7498a6bf4bf0fbd4e8358aea
```

The only constructible command is fixed sender `2/4` to receiver `0x12/4`, command `0x03/0x77`,
body `[0x02]`, timeout 500 ms, through Binder transaction `4`. It has no SET, generic packet
builder, socket, external process or device-state write. The callback accepts only an exact
reverse-route, clear, successful ACK with one state byte in `{0,1}`.

This artifact is **DO NOT RUN**, including after the v0.8 and transaction-1 checks. The exact live
manager/callback/`Pack` Parcelable ABI is missing. The adjacent `Pack` omits `maxRetryCnt`, so its
server reconstructs the default limit of two and can transmit this idempotent GET up to three
times. The generic Binder lane also uses clear selector 0, unlike the product-139 DJI Fly native
request's selector-3 intent. These are hard admission failures for the current artifact, not merely
facts to note. Most importantly, `0x03/0x77` is France EID, not FAA Remote ID and not a global RID
switch.

## Admission order

1. Review the current v0.10 admission-probe source and its `NOT ADMITTED` boundary.
2. If a later operator session admits that probe, capture its complete result page.
3. Require a clear upgrade-recovery marker, expected DJI stock `dpad_fuli` identity, UID1000,
   exported/enabled DevActivity, compatible Android/ABI facts and no unexplained signer mismatch.
4. Stop before copying Artifact A until a separately audited, side-effect-free UID1000 launcher
   exists. The stock shell page is not eligible. Only a later review may admit one fixed execution;
   stop on any missing service, UID/descriptor mismatch, denial or malformed reply.
5. Recover the exact live manager/callback/`Pack` Parcelable ABI, preserve native selector 3 and
   explicitly audit the chosen retry profile before designing any replacement for Artifact B. The
   constructor initializes retry 3, typed GET conditionally clears it from Characteristics `+0x30`,
   and typed SET retains 3; a raw retry-0 GET may only be labelled a laboratory single-shot. The
   current Artifact B must not run; prefer the reviewed DJI Fly in-process getter after a no-op
   attach canary.
6. No SET exists in this directory. Any future writer must independently implement baseline GET,
   one transition, exact readback, restoration, final GET and motor-on RF verification.

## Separate in-process fallback

If the Binder service is absent or unusable, do not fall back to a second localhost connection.
Adjacent Android 11 evidence suggests a caller that actually holds the signature permission
`android.permission.SET_ACTIVITY_WATCHER` may be able to use `cmd activity attach-agent` when the
target is JDWP-allowed. Merely executing `/system/bin/cmd` from an ordinary debuggable app does not
elevate its UID or grant that permission. A no-op, ABI-matched JVMTI agent could
then enter the existing DJI Fly process and reuse its initialized KeyManager/JNI state, with a
process restart as rollback. AOSP recommends a target-APK native-library directory or the target
app's own data directory; installing an ordinary carrier APK does not by itself make its library
cross-package loadable. That path remains research-only: live property, SELinux, target ABI,
target-owned placement and linker access are not closed, the audited stock `dpad_fuli` exports no
safe fixed-command carrier, and no agent has been run or installed.

See [`docs/08_ANDROID_ADB.md`](../../docs/08_ANDROID_ADB.md) for the current exact-v07 evidence
and pending userspace-only test boundary.
