# FindUAS adjacent-RC331 France EID GET bridge probe

Status: **offline artifact only; do not run on RC 2 yet.**

This directory contains a one-shot `app_process` command-line probe for one narrowly defined,
read-only operation through DJI's adjacent RC331 `protocol` Binder service. It is intentionally
not an APK and intentionally does not connect to localhost ports `40007`/`40009`.

## Exact operation

The executable can construct only this request:

| Field | Fixed value |
|---|---:|
| Binder service | `protocol` |
| Binder descriptor | `com.dji.protocol.IProtocolManager` |
| Binder transaction | `4` (`sendWithListen`) |
| sender | type `0x02`, id `0x04` |
| receiver | type `0x12`, id `0x04` |
| command | cmdset `0x03`, cmdid `0x77` |
| request kind | request, ACK-after-exec |
| encryption selector | `0` (the adjacent `Pack.Builder` default) |
| body | exactly one byte, `0x02` (GET) |
| timeout | `500 ms` |

The callback descriptor is `com.dji.protocol.IPackListener`; callback transaction `1` is success
and transaction `2` is failure. A successful response is accepted only when the Parcelable frame
is an exact reverse-route `0x03/0x77` ACK with `ccode == 0` and exactly one state byte in `{0,1}`.
Anything else is reported as `FAIL_CLOSED`.

`0x03/0x77` is a **France EID** candidate, not a universal Remote ID switch and not an FAA RID
master control. This probe has no SET request.

## Safety properties

- the process rejects every command-line argument;
- it exits before Binder lookup unless its UID is exactly `1000`;
- it uses `ServiceManager.checkService`, `pingBinder`, and an exact descriptor check;
- its only outbound application Binder call is synchronous transaction `4`;
- it has no socket, file output, shell execution, activity launch, property write, SET payload, or
  generic DUML builder;
- it does not ship any copied DJI framework class; raw Parcels mirror the adjacent ABI;
- the runner has a fixed classpath and class name and forwards no arguments.

The adjacent `Pack` Parcelable writes `cmdType` twice and omits `maxRetryCnt`. This implementation
reproduces that ABI exactly. Consequently the server reconstructs its default retry limit of two,
even though this client never asks for retries. Since this is an idempotent GET, that is bounded,
but it remains an important behavior to account for during eventual live validation.

## Provenance and unresolved boundary

The ABI was recovered from the locally extracted official adjacent RC331 `10.00.0700/0205`
artifacts:

- `framework.jar` SHA-256
  `4422ab980097dd40f0daa1b6d304ba2c0239ecad1ead0b9796952213b706043c`;
- `services.jar` SHA-256
  `1372cd839fc8f495d4e166bd4f29e08a446ca7fcd4154bfa642174ca4e7352ed`.

The live RC 2 is firmware `07.00.0100`. Its service publication, SELinux lookup permission,
Parcelable ABI, and route have not yet been proven identical. The adjacent policy also suggests
that service publication may fail because `protocol` lacks an explicit service context. Therefore
the artifact must remain offline until the separate safe APK confirms all preconditions and the
live ABI is checked. A missing service, hidden-API denial, descriptor mismatch, permission denial,
timeout, malformed callback, or noncanonical state all stop without a fallback transport.

There is also an intentional semantic difference from DJI Fly's product-139 native provider:
that provider requests encryption selector `3`, while the adjacent RC331 generic `Pack.Builder`
has no encryption setter and emits selector `0`. The probe follows the Binder/`Pack.Builder` lane
specified here; it does not claim byte-for-byte equivalence to DJI Fly's internal session.

## Build and audit

No network access is required after the toolchain is installed. Set `JAVA_HOME` and
`ANDROID_SDK_ROOT` (or `ANDROID_HOME`); the build uses Android API/build-tools 35 and targets
Android API 30 bytecode:

```sh
./build.sh
./audit.sh
```

`audit.sh` rebuilds the artifact, verifies the DEX checksum, decompiles it with JADX, executes ten
source/artifact contract tests, checks a built-artifact capability denylist, verifies that only
the three expected FindUAS classes exist, and verifies a single outbound `IBinder.transact`
callsite. Build hashes are written to `SHA256SUMS`.

## Staged runner (not authorized for use yet)

The supplied runner assumes these eventual fixed paths:

```text
/sdcard/Download/FindUAS-France-EID-GET-readonly.jar
/sdcard/Download/run-france-eid-get-readonly.sh
```

If and only if live preflight later closes the ABI and identity gates, the fixed invocation would
be performed by the DJI system-UID diagnostic process as:

```sh
/system/bin/sh /sdcard/Download/run-france-eid-get-readonly.sh
```

Do not invoke it now. This task produced and audited an offline candidate only; it did not copy,
launch, or execute anything on RC 2 or the aircraft.
