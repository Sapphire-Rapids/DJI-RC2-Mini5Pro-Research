# NLD FCC Smart RC 2.0.0.6 static analysis

This report records a bounded, read-only static analysis of the NLD FCC Smart RC distribution and
separates vendor claims, exact sample facts, inferences, and unresolved runtime behavior. It does
not endorse or reproduce the software.

## 1. Scope and handling

The input was a user-supplied `NLDFCC_Smart_RC.zip`. On 2026-08-28 its size and SHA-256 matched the
file served by the NLD Smart RC download link. The archive was extracted only into excluded local
working storage. The APKs and native libraries were inspected statically; none was installed,
started, dynamically loaded, sent to a controller, or allowed to contact an NLD service.

Instructions inside the archive were treated as untrusted sample content, not as research
instructions. No vendor binary, decompiled source, native disassembly, server response, license
material, or private capture is committed to this repository.

The decompiler recovered useful code with warnings. Claims below therefore use raw manifest/DEX,
resource, ELF/string/import, and cross-reference checks where needed; missing readable strings are
not treated as proof that encrypted or runtime-supplied behavior is absent.

## 2. Exact sample identity

| Component | Exact identity | Static boundary |
| --- | --- | --- |
| Smart RC distribution | 6,932,568 bytes; SHA-256 `e75011e8190098aff12219d687c17b93495993890bf4a96212856174087a5100` | Three ordinary ZIP entries; matched the official download bytes on 2026-08-28 |
| Main app | package `com.nolimitdronez.nldfcc`; version `2.0.0.6`, code 46; 7,278,464 bytes; SHA-256 `1035f0aa22e158fd1703e14dd3bd2198845da4c2113454f9ac3a4569c41ee474` | Minimum SDK 24, target/compile SDK 36; Kotlin/Compose app with two DEX files and two ARM ABIs |
| Main-app signer | valid APK Signature Scheme v2; certificate SHA-256 `72e71df3f2cc7db67a5ec62c1acb513e03ddbcd43f828d365b51e67ff2199a89` | Self-signed NLD certificate identity; differs from the helper signer; exact live-platform signer equality was not tested |
| Package Installer helper | package `com.android.packageinstaller`; Android 11/version code 30; 3,274,224 bytes; SHA-256 `523361acbe62587fa61e00a92369e87daa0d812232b8942deba67771ccf2633a` | Contains valid v1/v2/v3 signatures; Android 11/minimum-SDK-30 verification selects v3; static structure resembles the Android 11 package installer |
| Installer-helper signer | certificate SHA-256 `a4aa1cdd2ea580cbbe67486b5f6f3cfea83f488889995afa70793daa516687da` | Certificate subject names DJI; subject text alone does not prove provenance or privilege on an exact live build |
| Native core | ARM64 SHA-256 `08fd5b8778ca4f2b0bf76e6cd3624e1269fa9ac81029476c468c7b4864575596` | Stripped/obfuscated; exact command plaintext and server protocol remain partly opaque |

The official downloads page still displayed `2.0.0.1` while the downloaded APK manifest and the
vendor's 2026-08-20 release article identify `2.0.0.6`. This is a website-version display mismatch,
not evidence that the analyzed APK is counterfeit.

The helper declares privileged package-install/delete and user-management permissions. An ordinary
sideload receives such powers only if the exact platform recognizes its signer and grants the
permissions. Its presence therefore explains the vendor's installation route, but static analysis
does not prove that every listed controller will accept it as a privileged system replacement.

## 3. Recovered architecture

The important split is between normal FCC, C0 unlock, and the parameter editor:

```text
DIRECT / AUTO_START
  -> qualifying subscription
  -> native request envelope
  -> encrypted online response OR native-handled offline cache
  -> native decode
  -> native DUSS send path

C0_UNLOCK
  -> qualifying subscription state + online VPN-config response
  -> locally generated WireGuard client key + server route/peer configuration
  -> short-lived server-routed VPN
  -> stop and relaunch DJI Fly
  -> schedule automatic stop 25 seconds after successful tunnel UP

Parameter editor
  -> discover receiver and schema
  -> validate typed value
  -> write
  -> read back and classify verified/rejected/unconfirmed
```

These are distinct mechanisms. The C0 path is not a local `height=500` DUML write in the analyzed
Java code, and the parameter editor is not evidence that an arbitrary named parameter exists on the
current Mini 5 Pro.

## 4. Normal FCC path

### 4.1 Actual payload source

`STATIC` (C-082): DIRECT and AUTO_START select a qualifying subscription app ID, pass the
controller type to the native core, and obtain an opaque request. The request is posted as form data
to an API URL decoded by the native library as
`https://buttrocket.flysafe-unlock.com/androidapi/`. The response is passed back through the native
decoder, which invokes a Java `write(byte[])` callback. On a Smart RC, that callback returns each
decoded frame to the native send function.

The native core also recognizes an offline sentinel and exposes names for an offline-entitlement
signature and offline FCC blob. The normal FCC path can therefore operate from a
previously provisioned cache without exposing the command sequence in Java.

Follow-up native control-flow analysis closed the outer envelope (C-102):

```text
V1##Base64(16-byte IV)##Base64(nonempty block-aligned ciphertext)##Base64(32-byte tag)
```

For a selected outer key, the decoder derives an encryption key with
`HMAC-SHA256(Kouter, "OUTER|ENC")` and a MAC key with
`HMAC-SHA256(Kouter, "OUTER|MAC")`. It authenticates ASCII `V1`, IV, and ciphertext with
HMAC-SHA256, compares the tag in constant time, decrypts with AES-256-CBC, and strictly checks
PKCS#7 padding. The envelope fields are Base64; only the later command `PAYLOAD` field is hex.

An empty key argument on the online path selects a fixed embedded 32-byte master as `Kouter`; it
does not use a zero-length HMAC key. For an offline blob, the outer key is the Base64 text of
`HMAC-SHA256(master, "OFFLINE_FCC_V1|" + UPPERCASE_SERIAL)`. The serial is normalized to uppercase.
The master location and use were confirmed statically, but its value is intentionally excluded as
key/license material.

`STATIC` (C-105): after decryption, the accepted command object is either a top-level array or a
`packets` array. Each entry uses `RECV`, `RECV_INDEX`, `CMD_SET`, `CMD`, and a hex-byte `PAYLOAD`.
Native code constructs a DJI DUML frame with start byte, length/version, CRC8, endpoints,
little-endian sequence, control, command set/ID, payload, and little-endian CRC16. It invokes Java
`write(byte[])` once per frame, stops on false/exception, and spaces successful frames by 150 ms.

`UNKNOWN`: the APK/ZIP contains no usable encrypted response, offline blob, or real command object.
No vendor API was called and no licensed cache was obtained. Therefore the actual command values,
frame count/order, restore behavior, success semantics, and RF effect remain unresolved even though
the envelope and framing logic are now statically closed.

### 4.2 Transport

`STATIC`: the reachable RCLink path connects as a client to `127.0.0.1:40009`, receives/parses data,
and maintains readiness/epoch state. The Smart-RC writer does not simply copy an asset frame to
that TCP socket; native code validates/converts the DUML data and sends through DJI's abstract Unix
DUSS message-bus paths.

The native binary contains separate explicit RCLink handover, connection-table probing, and
auxiliary `hijack` code. No DEX call site or native internal cross-reference to the explicit
handover/probe entry points was found. Their presence is `STATIC`; use by the current FCC main path
is `UNKNOWN`. It would be incorrect to describe 2.0.0.6 as proven to invoke an explicit broker
takeover API.

The app also contains process-management paths that stop `dji.go.v5`; the C0/VPN flow can trigger a
one-shot maintenance service, and an installation/repair path performs three stop requests spaced
300 ms apart. This is lifecycle choreography, not the FCC transport itself.

### 4.3 Identity, startup, and privilege boundaries

`STATIC` (C-092): the runtime inquiry path normalizes a returned product/model token, including an
`fcNNN` to `wmNNN` form, and uses longest-prefix matching against a controller model table. This
supports model classification. It does not establish exact RC firmware, the exact aircraft product
ID, or a complete firmware compatibility gate.

`STATIC` (C-091): the boot receiver normally posts the app notification. It starts
`AUTO_START_FCC` only when the mode-specific `auto_start_armed` preference is set; stopping that
mode clears the preference. The DUML foreground service is sticky, but this is not unconditional
FCC activation at every boot. User stop intent and current lifecycle state remain material.

`NEGATIVE` within the bounded static search (C-090): the main APK contains no identifiable ADB
client, `su`/Magisk path, mount/remount path, DJI configuration/database patch, or Binder FCC
channel. The one found app-native shell property action reads/writes
`persist.dji.sysboot.set_fly_home` for a launcher-selection workflow, not for the FCC payload. This
does not exclude behavior hidden in opaque native data, the server, a separately installed helper,
or the separately hosted DJI Fly APK.

The visible FCC/CE/country and CE-restore values occur only in the seven profiles whose runtime
reachability was not found. The region command, persistence behavior, and restore sequence inside
the actual opaque online/offline payload remain `UNKNOWN`.

### 4.4 The seven packaged profiles

The APK contains seven JSON profiles. Every file is byte-identical to the file of the same name in
FreeFCC at pinned commit `597157bd52120dfeb9677f79a8ad46b6027ce8dc`:

| File | SHA-256 | Visible frame count |
| --- | --- | ---: |
| `4g.json` | `657ffc30cc92c80849b7ed3c1bc83f5def02985952985b12b4600a279f1ca9d6` | profile-specific sequence |
| `ce_restore.json` | `b482c3a5d77f00f961c0744c49f8e7f14cfb05727ca9995e46c6def208d45e22` | 1 |
| `device_info.json` | `f074547407527f2e861a147129b05eddbca48619b29a286f2368f3ef7a66827e` | 1 |
| `fcc.json` | `e6df4a963256b97424c90378f18f171f2c1c53d2405e54cf0f981809fdd69c15` | 21 |
| `fcc_keepalive.json` | `29423757dd58b447e1209fcff14f920c48d871a8ab6d48ace224293a83278282` | 4 |
| `led_off.json` | `0bd75e51825bcb2572ffb3471ae4fe3982c175fd2c1bd9b3571aa7a7fd5a6508` | 1 |
| `led_on.json` | `4386a8b77277315326c718c6c041a98adf4b5ba12984f3794cc7e386efb840fc` | 1 |

`STATIC` (C-081): complete DEX, decompiled-source, both-ABI native string/import, filename, path,
and JSON-key searches found no application loader or reference for these seven files. The only
application-wide `getAssets()` call belongs to AndroidX ProfileInstaller and reads baseline compiler
profiles, not these JSON files. Native imports also contain no Android asset-manager or archive
reader supporting an alternative obvious loader.

Therefore the JSON files are protocol prior art, not evidence of the current runtime payload. They
may be unused development/legacy assets. Their mere presence cannot prove that NLD sends the visible
21-frame batch, repeats it twice, runs the visible keepalive, or performs the visible CE restore.
A custom hidden archive parser is theoretically possible, but no static indication of one was
found.

The exact copies also create a licensing/provenance issue for an MIT project: the matching FreeFCC
files are published under AGPL-3.0, while the direction or common source of copying is not proved by
byte identity alone. Ideas and independently re-established protocol facts may be studied, but the
matching code or asset files should not be copied into this MIT archive or product without a
compatible licensing decision.

## 5. C0, 500 m, and speed path

`STATIC` (C-084): C0_UNLOCK is a license-controlled, online orchestration path:

1. It requires a qualifying subscription and nonempty values it treats as controller/aircraft
   identity; exact firmware identity is not closed by the model-classification path.
2. The installed DJI Fly version gate accepts `>=1.13.10` and `<1.21.8`; it does not always force
   replacement of every compatible version.
3. If its repair/install flow is entered, it downloads a controller-specific DJI Fly 1.21.4 APK.
4. It asks Android for VPN permission, generates the client Curve25519 keypair locally, obtains
   peer/address/route configuration from the server, and starts the tunnel.
5. It stops and relaunches DJI Fly while the tunnel is up.
6. After the tunnel reports UP, it schedules an automatic stop with a literal 25,000 ms delay.

The VPN response model contains endpoint/server key, client addresses, MTU, allowed IPs, target
hosts, DNS, and a `VPN_SECONDS` value. If allowed IPs are absent, the app resolves the supplied
target hosts and installs their IPv4 `/32` routes as a fallback. If allowed IPs are present, their
breadth is entirely server-controlled; without an actual response it is `UNKNOWN` whether the route
is narrow or includes a default/wider prefix. WireGuard persistent keepalive is 25 seconds. In this
version, `VPN_SECONDS` is checked only for being positive; raw DEX control-flow confirmation shows
that the automatic-stop delay is the fixed 25,000 ms literal. An explicit stop, failure, generation
replacement, or process lifecycle can end it earlier, and handler scheduling can execute later.

The repair download is accepted after a 300–700 MiB size range, parseable APK, package name
`dji.go.v5`, and a version string that its numeric comparator treats as equal to `1.21.4`. The
comparator ignores a suffix after the first non-numeric character and treats missing numeric parts
as zero, so this is weaker than exact string equality. No fixed file hash or allowed signer check
was found in that validation path (C-088). The downloaded DJI Fly APK was not included in the
supplied ZIP and was not downloaded, so this analysis cannot determine whether it is an unmodified
DJI release.

`INFERENCE`: because no C0-specific Java path writes a 500 m or speed value, the visible candidates
for the claimed effect are DJI Fly's startup/backend interaction through the vendor-provided route,
the vendor-hosted 1.21.4 APK, or both. The server-side behavior and hosted APK are missing, so the
causal mechanism is unresolved. Routing through a gateway is not itself evidence of TLS
interception or modified responses.

## 6. License and offline operation

`STATIC` (C-086): subscription refresh creates or retrieves an Android Keystore EC P-256 key under
alias `NLD_DEVICE_ID_V1` and sends the X.509 public key as device identity. Subscription entries
carry an app ID/name plus activation and optional expiry times. On connection failure, Java passes
the same public-key bytes to a native offline-state function. Native printable names include
`offlineEntitlement`, `offlineEntitlementSignature`, and `offlineFccBlob`.

Follow-up analysis closed the entitlement verification boundary (C-103). The native code Base64
decodes the entitlement and signature, hashes the raw entitlement with SHA-256, and verifies a
384-byte RSA signature with an embedded 384-byte modulus and exponent 65537 using the PKCS#1 v1.5 /
SHA-256 mode. The verified JSON must have `v == 1` and match `sn`, `deviceType`, and
`devicePublicKey`; the last value is compared with the Java-supplied X.509 P-256 public key.

The exact connection-failure sentinel is
`NLD::SUBSCRIPTIONS::CONNECTION_FAILURE::V1`. It restores only the previously cached successful
subscription response, which is parsed and signature-checked again. The embedded RSA public key can
verify an entitlement but cannot create a valid signature.

`STATIC` (C-104): the no-backup cache file is `offline_fcc_cache.bin` with a temporary sibling. Its
format is:

```text
[8-byte magic][u32BE blob length][u32BE subscription length]
[offlineFccBlob][original successful subscription response]
```

Both sections must be nonempty, the total length must match exactly and remain at or below 8 MiB,
and the writer uses mode 0600, complete writes, file `fsync`, atomic rename, and parent-directory
`fsync`. There is no extra whole-file encryption: the first section is already the encrypted FCC
envelope, and the second is the signed subscription response.

The asymmetric device public key binds the entitlement but is not the FCC blob's outer-key input.
The offline blob uses the fixed-master/uppercase-serial derivation described above. Trial entries
have an expiry and are blocked from offline use. C0 is different: an offline VPN-setup sentinel
produces an error, so each new C0 activation needs a successful online VPN-config response tied to a
qualifying subscription. It does not necessarily perform a separate subscription refresh before
every start.

The reusable design idea is device-bound asymmetric identity plus signed, expiring offline state.
For an open research tool, the more appropriate default is no license telemetry at all; if signed
lab profiles are ever needed, they should be transparent, locally verifiable, and collect no
unnecessary controller or aircraft identifiers.

## 7. Parameter editor and macros

`STATIC` (C-087): the parameter editor implements the strongest generally reusable design in this
sample. It discovers live parameter schema, separates Flight Controller/AircraftOS/Vision receiver
families, represents type/size/minimum/maximum/default/current values, validates typed edits, writes,
and performs a post-write readback. Its result model distinguishes verified, rejected, and not
confirmed outcomes instead of equating local write completion with success. These paths were not
executed in this review; schema coverage and matching readback on the exact RC 2/Mini 5 Pro pair are
unverified.

The architecture is worth reproducing independently:

- discover capabilities and schema from the exact connected subject rather than maintaining one
  global model list;
- retain receiver, product, and firmware identity with every value;
- enforce type, range, and safety allowlists before sending;
- require strict response matching and fresh readback;
- store macros as symbolic parameter/value transactions with compatibility gates and rollback.

Hard-coded Mavic Air 2/Lito X1 values found in the UI code are preview fixtures. They are not live
Mini 5 Pro defaults and must not seed an implementation.

## 8. Remote ID result

`NEGATIVE` within a fixed static scope (C-085): searches covered both DEX files, all decompiled
sources, the manifest, all localized resources, all seven JSON profiles, and printable strings from
both native ABIs. Terms covered Remote ID/RID, UAS ID, operator ID, OpenDroneID/ODID, ASTM F3411,
EN 4709, FAA, and broadcast-ID variants. No identifiable NLD Remote ID UI, switch, setting, command,
profile, service, or handler was found. Matches were unrelated Android broadcast/receiver or remote
controller terms.

One generic NLD Android catalogue page claims it can disable Remote ID packet transmission when
enabled. The current Smart RC product page does not list that feature, and the exact 2.0.0.6 sample
does not expose it. The web statement is therefore a vendor claim, not implementation evidence for
this APK or Mini 5 Pro.

The result does not prove that NLD can never affect RID. A native/encrypted command, the opaque
server payload, a generic raw frame, the server-selected regional policy, or the separately hosted
DJI Fly APK could have an indirect side effect. What is established is narrower: this package gives
us no identifiable, independently callable, readback-capable Remote ID control to borrow.

No NLD-derived RID switch should be claimed until one exact path has:

1. a motors-on independent RF baseline;
2. a recognized command or policy transition rather than an opaque blob;
3. an onboard state readback and strict response result;
4. a restore and final readback;
5. an independent RF A-B-A observation using the same aircraft state.

## 9. What can be borrowed

| Decision | Element | Reason and required correction |
| --- | --- | --- |
| Borrow the architecture | Live parameter discovery and typed post-write readback | Directly improves correctness; add safety allowlists, transaction logs, rollback, and exact product/version binding |
| Borrow the architecture | Explicit mode state machine, foreground status, conditional boot intent, and offline-state reporting | Useful for reliable RC operation; preserve an armed flag, clear it on stop, and keep user intent authoritative |
| Borrow the concept | Signed offline profile/entitlement envelope | Useful only if transparent and locally verifiable; an open tool should avoid NLD-style opaque licensing and fingerprinting |
| Borrow the test pattern | Version gates and deterministic app lifecycle around a compatibility experiment | Pin signer/hash as well as version; never accept a large APK by name/numeric-version/size alone |
| Study, then independently reproduce | Data-driven protocol profiles | The packaged files are unreferenced and byte-identical to files published in the AGPL-3.0 FreeFCC repository; copying direction/provenance is unresolved, so independently establish minimal causality, ACK/readback, restore, and licensing first |
| Do not borrow | Encrypted server-supplied device commands | They prevent peer review, per-command consent, rollback analysis, and causal attribution |
| Do not borrow | Blind multi-frame replay or socket-write success | Neither proves target state nor RF output; use minimal commands, strict matching, readback, and RF measurement |
| Do not borrow | Unverified DJI Fly download and opaque C0 gateway dependency | Supply-chain and reproducibility boundary is too weak for a research control panel |
| Do not borrow | Hidden handover/hijack capability or concurrent second-client assumptions | Current main-path reachability is unproven and adjacent broker evidence shows connection ownership can be destructive |
| Do not borrow | Any claimed RID disable behavior | No explicit 2.0.0.6 implementation or closed live evidence was found |

## 10. Recommended follow-up

The most productive follow-up is not to clone NLD wholesale. It is to implement three independent,
observable layers:

1. a read-only RC/aircraft identity and schema inventory;
2. a single-owner transport with one-command-at-a-time matching, readback, rollback, and immutable
   audit records;
3. an independent Remote ID receiver timeline synchronized with onboard status and operator-started
   motor transitions.

For NLD-specific causality, the immediate missing input is now precise: a legitimately obtained
online response or `offlineFccBlob` plus its matching authorized-device context. An independent
offline parser could then authenticate, decrypt, and list DUML commands without executing the
vendor native library. A future dynamic experiment would still need to record post-decode output
and the actual VPN route/host set while keeping license and identity material redacted. It must not
attach a second localhost broker client. A no-op run, normal FCC action, C0 action, and restore would
then be compared separately. Until such a record exists, the actual commands and C0 server behavior
remain `UNKNOWN`.

## 11. Public references

- [NLD FCC Smart RC product page](https://nolimitdronez.com/nld-fcc-android-smart-rc-license)
- [NLD FCC 2.0.0.6 release article](https://nolimitdronez.com/nld-fcc-2006-the-remake)
- [NLD downloads page](https://nolimitdronez.com/download)
- [NLD generic Android catalogue page](https://nolimitdronez.com/nldfcc-for-android?orderby=11)
- [FreeFCC pinned comparison revision](https://github.com/doesthings/FreeFCC/tree/597157bd52120dfeb9677f79a8ad46b6027ce8dc)
- [FreeFCC release history](https://github.com/doesthings/FreeFCC/releases)
- [FreeFCC protocol-provenance issue](https://github.com/doesthings/FreeFCC/issues/30)

Public pages support vendor claims and public-project provenance only. Exact implementation
conclusions in this report come from the registered static samples, not from marketing text.
