# FindUAS RID Observer — research-only APK

Status: **source-only v0.11 report-export revision**; device installation/run remain unconfirmed. This
directory contains only independently written `src/safe` and `src/safeTest` code. It is covered by
the repository-root [MIT license](../../LICENSE). Generated APKs, vendor files, and the withdrawn
localhost/socket source are intentionally excluded.

2026-08-30 checkpoint (C-231): the preserved exact v0.10 APK passed the current source/final-DEX
audit and 21/21 mutation checks again. It is now staged as one new removable-SD
`Download/FindUAS_A001_V010.apk`; fresh unique listing and full readback match the registered
size/hash. Installation and execution remain unconfirmed. This does not admit any attach, DJI
protocol transaction or control operation. The historical audit below is unchanged.

Build and source-only audit with Gradle 8.10.2, JDK 21, and Android SDK 35:

```sh
export JAVA_HOME=/path/to/jdk-21
export ANDROID_HOME=/path/to/android-sdk
# Optional when Gradle is not already on PATH:
export GRADLE_BIN=/path/to/gradle-8.10.2/bin/gradle
./scripts/build_and_audit.sh
./scripts/reproducibility_check.sh
```

> **CRITICAL RETRACTION — DO NOT USE OBSERVER v0.1–v0.4.** Those builds open a second
> `127.0.0.1:40007` or `40009` socket. Adjacent official RC331 `10.00.0700/0205`
> configuration and `libduml_frwk.so` now show that these server endpoints default to one active
> client fd rather than a fan-out tap. A new connection may replace the fd already used by DJI
> Fly even when the new client never writes a byte. Do not start their observer service, do not
> use them for passive capture, and do not treat “input-only” as non-disruptive. If one is
> installed, leave it stopped and update in place to v0.10.

## Current v0.11: save the report on SD for host retrieval

The user explicitly requested SD report output. Version `0.11.0-report-export` / code `11`
keeps the same package/signing identity and the existing read-only device checks. It adds no
permission, device command, target-code write, socket, attach, service or automatic network upload.
Only the generated diagnostic report is written.

After tapping **执行只读能力检查**, both `COMPLETE` and `INCOMPLETE` results automatically save
one new UTF-8 file on the unique mounted removable SD volume:

```text
Download/FindUAS/Probe/FindUAS_Probe_v011_<completed-time>_<run-id>_<attempt-id>.txt
```

Keep the app open until the save result. No file picker or clipboard transfer is required. A failed
save offers **重新保存报告到 SD 卡（不重新检查）**. Each attempt has a new name; existing files
are never replaced. No/multiple SD volumes, unavailable MediaStore, oversized/truncated output,
write/close/publish failure and failed pending-row cleanup are separate results. There is no
internal-storage fallback and no broad storage permission.

The report is at most 256 KiB and must end with `report_file_end=true`. Its core machine schema
remains `finduas-rid-probe/v0.10-schema-1`, with `app_version=0.11.0-report-export` added. Export
success never changes the inspection's completion verdict. Report files contain local diagnostic
paths and run metadata; keep them private and do not commit them.

The host must obtain a fresh final-name MTP listing and full readback. `IS_PENDING=0`/the UI's saved
state proves only local publication, not host receipt. Rotation/resume cannot duplicate an export;
process death can lose an unfinished report. See [v0.11 export and audit](REPORT_EXPORT_V11.md).

The following v0.10 design and audit notes describe the preserved historical artifact. Their
blanket file-output ban is unchanged for v0.10; the current source has only the reviewed v0.11
report sink exception above.

## Safe replacement design: v0.10

Version `0.10.0-research` is built from a deliberately separate safe source set. It preserves the
existing `com.finduas.ridobserver` application ID and uses `versionCode 10`, so it can supersede
older installed builds without uninstalling them. The release source set contains only:

- one exported launcher Activity;
- no requested permissions and no service, receiver or provider;
- one user-triggered, non-mutating lookup of service name `protocol`;
- `ServiceManager.checkService()`, `IBinder.pingBinder()` and descriptor comparison against
  `com.dji.protocol.IProtocolManager`;
- read-only package/component inventory for DJI Fly, `com.dpad.fuli`, and the fixed V0/V1 JVMTI
  carrier package names, including system/updated-system/debuggable flags, exact UID relationships,
  process name/visibility, signer certificate SHA-256, APK ABI and
  `DevActivity`/`ProtocalActivity`/`ShellCommandActivity` state;
- read-only `stat`, observer-view access bits and SELinux file context for package APK/data/native
  paths, plus SHA-256 of the fixed expected native library when readable;
- fixed reads of `ro.debuggable`, `persist.dji.upgrade.fuli`, Android build/ABI and SELinux state;
  it never launches either DJI activity and never writes a property;
- fixed-entry, size-bounded ZIP hashing of DJI Fly's packaged `libsdk_jni.so` and the adjacent
  `dpad_fuli` `classes16.dex`/`classes23.dex`, plus an exact whole-APK hash for `dpad_fuli`;
- independent read-only hashes for `/system/framework/framework.jar`, `services.jar`,
  `/vendor/etc/dji.json` and `/system/lib64/libduml_frwk.so`;
- three deliberately separate reference verdicts: exact adjacent `dpad_fuli` package identity,
  exact adjacent framework/server ABI, and exact adjacent single-active-client broker files;
- an Android/ART identity section that reads **only this probe process's** `/proc/self/maps`,
  strictly parses/page-aligns every exact-basename `libart.so` range and file offset, rejects
  zero start addresses, overflow, explicitly signed device or inode tokens, `00:00`,
  overlapping/beyond-file coverage and ambiguous identities, then requires a second normalized
  maps snapshot to be exactly equal;
- `lstat` plus read-only `O_NOFOLLOW` open/fstat of that exact non-symlink regular file, explicit
  non-zero `st_dev`, exact nanosecond `st_mtim`/`st_ctim` pre/post snapshots, whole-file SHA-256
  and unique GNU build-id;
- two fixed range hashes only when whole-file SHA-256 and GNU build-id both match the recovered
  RC2 ART profile: `Agent::Unload` at `0x5ccfa0 + 0x100`, and `Runtime::AttachAgent` at
  `0x56bfc4 + 0xebc`; a matching primary identity with either wrong or unreadable range keeps the
  overall run `INCOMPLETE`;
- one process-lifetime immutable probe snapshot/worker gate, so Activity recreation cannot start a
  duplicate read-only scan and the replacement Activity restores the running/completed report;
- a user-triggered local clipboard copy of the already rendered report; no report leaves the RC 2.
- two explicit user-triggered Android navigation buttons in Device info then Developer-options order;
  they open only fixed `Settings` actions, fall back to the Android Settings root when the primary
  page is absent, and render opened/not-found/denied/failed locally.

It contains no socket or network API, no `40007`/`40009` connection, no DUML parser or frame, no
`Parcel`, no Binder application `transact`, no protocol proxy, no listener registration and no
`Pack` send. The ART section performs no attach, agent load, symbol lookup, native entry-point
call, private ART/DJI reflection, or class enumeration. The pre-existing v0.8 checks retain only
their already-audited Android-framework reflection for `ServiceManager`, system properties and
SELinux; v0.10 adds no new reflective surface. The result is only an enum such as service available, absent, lookup denied, hidden
API blocked, unreachable or descriptor mismatch. A matching descriptor proves only that the
Binder is visible and alive; it does not prove that a side-loaded app may execute DJI protocol
transactions or that a RID switch is supported.

The older localhost implementation is retained only as a documented retraction; its source is not
present in this public tree. Gradle v0.10 explicitly packages `src/safe` and tests `src/safeTest`.
Static guards reject permissions/background components, Java sockets, loopback ports,
`Parcel.transact`, protocol listeners and Pack builders in the published source set.

The machine section is newline-delimited `key=value`, uses schema
`finduas-rid-probe/v0.10-schema-1`, percent-escapes `%`, `=`, CR/LF and ASCII control characters,
and ends with `machine_section_end=true`. `COMPLETE` requires the v0.8 Protocol Binder check, the
v0.8 local capability inventory, and a `COMPLETE` ART identity section. Any ART ambiguity or
identity/range failure produces `INCOMPLETE`; it is never silently promoted. See
[`ART_IDENTITY_V10.md`](ART_IDENTITY_V10.md) for the exact state and field contract. The final-DEX
auditor proves the three-input completion control flow, false-to-success provenance of both base
completion flags, the real-run/fail-closed origin of `nextArtIdentity.state`, and the unchanged
gate result's persistence as the session `runState`. It also freezes the application-owned
external invoke surface and explicitly rejects native-load, file-output and socket/send calls;
twenty-one adversarial mutations are rejected.

File `r/w/x` results are explicitly labelled as the ordinary observer app's UID/SELinux view. They
do not prove UID1000 write access, cross-package placement, DJI Fly linker-namespace admission or
successful JVMTI attach. An unreadable carrier library hash remains a hard stop before V0.

### Evidence boundary

The single-active-fd conclusion is static evidence from adjacent official RC331
`10.00.0700/0205`, not yet a runtime measurement of the user's RC 2 `07.00.0100`:

```text
/vendor/etc/dji.json
SHA-256 dfc986823188115ef4f75599144342be427c08aca52d004d2cf141de77a08155

/system/lib64/libduml_frwk.so
SHA-256 a5257965135fa46118451480bdd04f109e0ec29858827e764ffeaabaf6c270a2
```

`dji.json` declares both `40007` and `40009` as TCP servers and supplies no connection-retention
flags. The framework's `tcp_listen_thread` uses default flags `0`: when an fd already exists, it
logs `get a new connection, close the old one` and replaces it. Only bit 0 changes the behavior to
`WL TCP already connected, reject the new connection`; that bit is not enabled by the recovered
configuration. Exact `07.00.0100` code/configuration may differ, but uncertainty is not permission
to keep using a potentially disruptive observer. The public repository records this correction in
[`../../docs/09_NEGATIVE_RESULTS.md`](../../docs/09_NEGATIVE_RESULTS.md).

### Next stable-switch branches

1. Run only the v0.10 capability snapshot. It opens no DJI transport and sends no command.
2. If the exact descriptor is visible, verify the precise live framework ABI and authorization
   boundary before considering a separately reviewed, read-only Binder transaction. A matching
   descriptor alone does not authorize `send`, `sendWithListen` or a RID setter.
3. If lookup is absent or denied, prefer an official/system-identity component or an in-process
   DJI Fly instrumentation/sidecar that shares the already-owned transport. It must not create a
   second broker socket.
4. Root/system modification remains a last-resort transport-enablement branch, not a protocol
   shortcut. Any eventual writer still needs genuine type-6 provenance or the exact applicable
   regional EID contract, baseline GET, same-session SET/readback, restoration and independent RF
   confirmation after the user starts the motors.

Reviewed v0.10 artifact (built and audited offline; not installed or run on a device in this task):

```text
dist/FindUAS-RID-Bridge-Probe-0.10.0-research.apk
bytes: 2570983
SHA-256: fdad29bfb1237bc224a805d6eb5a99358a044bd226610d9f0fc33975d94b606c
signature: APK Signature Scheme v2 verified
signer certificate SHA-256: 37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224
schema: finduas-rid-probe/v0.10-schema-1
safe JVM tests: 43 passed
DEX/safety audit mutations: 21/21 rejected
Android lint: No issues found
zipalign: verified
native libraries: none
```

The hash above identifies the historical reviewed artifact; the APK itself is not distributed in
this repository. A fresh source build may use a different local debug signing certificate. The
default public audit validates the source/manifest/DEX safety contract without requiring the
private historical signer or exact vendor ART input. Set `FINDUAS_SEALED_AUDIT=1` and provide
`FINDUAS_KNOWN_ART_PATH` only when independently holding all sealed reference inputs.

See [`INDEPENDENT_AUDIT_V10.md`](INDEPENDENT_AUDIT_V10.md) for the separate adversarial audit,
including three real compiled hostile variants and the remaining offline/runtime limitations.

The sealed v0.9 artifact record remains preserved by hash; the binary is not distributed here.
`FindUAS-RID-Bridge-Probe-0.9.0-research.apk` was 2,538,215 bytes with
SHA-256 `a59f0f6abb2d1a10aeba44efed76cc85d351086fbf6dff5c1cc377dabe12b97d`).
The prior v0.8 artifact record likewise identifies a 2,477,789-byte binary with
SHA-256 `b67a99621440088a39d212483d2de69a47fdc26850b59ed7fecfa9e1e8c70fb1`).

Final application-DEX inspection found no socket/loopback connection, file-output stream,
`Parcel`, DJI protocol application transaction, attach/load entry point or process execution in
the app classes. The sole Activity launch site accepts only the three fixed Android Settings
actions described above.
Two consecutive clean builds were byte-identical. A reference match is only identity evidence:
the `dpad_fuli` verdict does not prove framework/Parcelable ABI or expose a safe UID1000 caller;
the framework verdict does not prove target-process linker admission; and the broker verdict never
revives v0.1-v0.4.

## Superseded v0.4 history — offline reference only, DO NOT RUN

Version `0.4.0-research` was an independently packaged, input-only observation client for DJI RC 2.
It keeps the existing `com.finduas.ridobserver` package/update path and exposes two mutually
exclusive sessions selected manually by the user:

- `127.0.0.1:40007` strictly decodes the RID/FlySafe status pushes under study.
- `127.0.0.1:40009` passively correlates observed official `0x11/0x11 QueryLicense` requests with
  exact same-sequence, reverse-route ACKs. It never emits a query.

The 40009 parser accepts direct DUML and only the exact `55 cc 49 57` or `55 cc 30 75` logical
envelopes. Every inner DUML frame must independently pass version, length, CRC-8 and CRC-16 checks.

Type-6 inventory summaries are enabled only when the current single connection has observed fresh
V3/V4 version metadata, usable support=true, a valid modern start, strictly consecutive pages and
an exact normal terminator. Any timeout, route/sequence mismatch, page gap, duplicate ID, count
mismatch or protobuf violation clears the in-memory run. The UI exposes only counts, RID level
distribution and enabled/disabled counts. Exact IDs and response bodies are never stored or shown;
duplicate checking uses a per-epoch salted fingerprint that is wiped at reset.

The app also recognizes the fixed `0x03/0x77` France EID command as a separate passive visibility
canary. GET must be exactly `[02]`; SET-shaped traffic must be a one-byte boolean, but its value is
not retained. GET ACKs require an exact two-byte result/state shape; SET ACKs require one result
byte. Both require exact transaction correlation, and only plaintext response flags `0x80/0xC0`
are accepted.
The UI explicitly labels this **France EID only — not FAA Remote ID and not a global RID switch**.

All parser, pending transaction, inventory and UI state is cleared on stop, channel switch,
disconnect, error or epoch replacement. Late callbacks from an older worker are rejected. There is
no automatic reconnect, raw dump or persistence.

The APK contains no FCC logic, request/set command encoder, output stream use, boot receiver,
external network target, accessibility service, package installer, log reader, Wi-Fi control,
storage access, location access or root path. `WIRE_CORRELATED` is deliberately weaker than DJI's
in-process provider result: localhost DUML does not expose provider `PackState`, and the app never
fabricates it.

## Withdrawn historical build

The withdrawn historical artifact is `outputs/FindUAS-RID-Observer-0.4.0-research.apk`:

```text
versionCode / versionName: 4 / 0.4.0-research
bytes: 2488150
SHA-256: a6818d7b7d6b826b04c245328f8fcaebc1b6a7e8404723d648f299d582290b76
signature: APK Signature Scheme v2 verified
signer certificate SHA-256: 37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224
observer tests: 44 passed
wire-codec regression tests: 31 passed
type-6 parser regression tests: 20 passed
Android lint: No issues found
zipalign: verified
native libraries: none
```

The package name and signer match v0.3, but the artifact must no longer be installed or started.
Its parser, privacy and no-write claims remain useful offline facts; the earlier assumption that a
second input-only connection was safe was wrong because establishing that connection may itself
replace DJI Fly's active fd. Do not work around this by reconnecting, weakening correlation gates
or adding an active sender.
