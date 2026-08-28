# RID switch wire codec (offline research module)

This is a standalone pure Kotlin/JVM codec for the high-confidence **application payload and ACK
body** structures recovered from DJI MSDK 5.18 FlySafe V2/V3/V4. Status: **STATIC** and offline;
device traffic is **NOT ADMITTED**. It does not make Remote ID control operational. The
independently written source is covered by the repository-root [MIT license](../../LICENSE).

## Hard scope boundary

The module contains:

- fixed QueryLicenseFromFC request payload encoding;
- fixed SetLicenseEnable request payload encoding;
- parsing of provider-level application ACK bodies whose first byte is the result code;
- immutable evidence metadata for PackType `0x38` and `0x39`;
- zeroizable wrappers for license IDs, SetEnable payloads, and sensitive query ACK data.

It deliberately contains no Android code, socket, USB, serial, device, cloud, file, database,
DUML-frame, CRC, retry, timeout, sequence, receiver, sender, or route implementation. There is no
generic raw-command API and no method that accepts PackType, cmdset, cmdid, or route. Nothing in
this module can transmit a payload.

## Fixed evidence metadata

| Operation | PackType | tuple | endpoint |
|---|---:|---|---|
| Query licenses | `0x38` | `11 11 00 01` | cmdset `0x11`, cmdid `0x11`, ACK result prefix present |
| Set license enable | `0x39` | `11 12 00 01` | cmdset `0x11`, cmdid `0x12`, ACK result prefix present |

Static product-139 analysis produced packed route candidate `0x92`, but it still requires runtime
observation. `Product139RouteResearchMetadata` records that fact with
`RUNTIME_OBSERVATION_REQUIRED`; all codec methods ignore it and no route encoder exists.

## Request payloads

### Query

| Version | Operation | application payload | enforced index bound |
|---|---|---|---:|
| V2 | page `index` | `[index]` | `0..255` |
| V3/V4 | start | `00 01` | n/a |
| V3/V4 | page `index` | `00 (index << 1)` | `0..127` |

The V3/V4 bound rejects index 128 instead of silently wrapping the shifted value back into one
byte. V2 has no separate start selector.

### SetEnable

| Version | application payload |
|---|---|
| V2 | `[licenseId:u32LE][enable & 1][00]` (6 bytes) |
| V3/V4 | `[00][licenseId:u32LE][01 if enabled, 02 if disabled][00]` (7 bytes) |

The SetEnable encoder and `SensitiveLicenseId` are currently `internal`: external consumers cannot
turn an arbitrary four-byte value into a write payload. Within this quarantine module,
`SensitiveLicenseId.consumeLittleEndian` accepts exactly four bytes, copies them into owned memory,
and zeroes the caller array even if validation fails. The returned ID and encoded
`SensitiveApplicationPayload` are `AutoCloseable`, redact `toString`, and zero their backing arrays
when closed. Scoped byte copies are also zeroed when the callback returns.

```kotlin
val source = byteArrayOf(0x78, 0x56, 0x34, 0x12)
SensitiveLicenseId.consumeLittleEndian(source).use { id ->
    SetEnableRequestCodec.encode(FlySafeWireVersion.V3, id, enable = false).use { payload ->
        payload.useBytes { applicationPayload ->
            // Supply only to a separately reviewed, typed integration boundary.
            // This research module itself has no transport.
        }
    }
}
```

Do not print, hex-dump, persist, or interpolate the scoped array into errors.

## ACK parsing

All parser entry points are named `consume...`: they always zero the caller-owned ACK body on
success or failure. The expected input is the complete **application ACK body**:

```text
[resultCode:u8][provider data...]
```

`PassiveQueryTransactionCorrelator` now provides an input-only full-frame gate for observed
`0x11/0x11 QueryLicense` traffic. It validates DUML-v1 length/CRC, exact request and response
command types, request shape, sequence, reverse route and command. An exact same-route/same-page
retransmission refreshes the six-second correlation window; a conflicting use of the same sequence,
an ACK replay or an expired transaction fails closed. A matched response is released as a
zeroizable application body. The gate has no transport and cannot create or send a frame.

Transport provider `PackState` and legal broker-session ownership remain outside this module.
Consequently, ACK parser entry points and the setter remain `internal`: passive wire pairing is not
an unforgeable provider-owned `PackState == 0` capability and does not authorize active traffic.

- V2 query page: result `1` is accepted only as the exact one-byte end marker; a record requires
  result `0` and at least 40 data bytes, retained as an opaque zeroizable record. Other result
  codes are rejected.
- V3/V4 start: result must be `0`; the remaining non-empty bytes are retained as opaque,
  zeroizable `LicenseGroupInfo` protobuf. Protobuf semantic decoding is intentionally out of scope.
- V3/V4 page: result `1` is accepted only as the exact one-byte end marker. A record requires
  result `0`; its first data byte is decoded as status bits
  (`invalid`, `enable`, `in_valid_date`), high bits are preserved without guessing, and the
  remaining non-empty bytes are retained as opaque zeroizable `License` protobuf.
- SetEnable success is deliberately narrower than DJI's vector parser because this module encodes
  exactly one license ID: the full ACK must be exactly `[00, 01, status]`. V2 treats the sole
  nonzero status as true; V3/V4 test bit 1. Count zero, multiple items, truncation and extension
  tails are rejected.
- V3/V4 SetEnable result codes `1..5` map to SDK numeric errors
  `407, 406, 408, 405, 409`; other result codes map to `404`. V2 nonzero results map to `404`.

The parser imposes a local 64 KiB application-body cap. V2 records are independently restricted to
40..80 provider-data bytes, preventing the oversized tail accepted by DJI's unsafe native copy.
These are defensive module limits, not recovered DJI protocol constants. The parser also strengthens
native behavior by rejecting short records
before reading them and by rejecting nonzero record results that DJI's native queue parser can
permissively continue parsing.

The current native V2 decoder only materializes area/circle records. This codec keeps V2 records
opaque and does not claim that a V2 type-6 RID inventory can be selected safely.

## Build and test

JDK 21 is used to run Gradle; emitted bytecode targets JVM 17.

```sh
export JAVA_HOME=/path/to/jdk-21
gradle clean test
```

The tests cover exact byte vectors, index bounds and shift-wrap rejection, fixed endpoint metadata,
ACK length/result/count handling, V2 versus V3/V4 boolean rules, error-code mapping, full-frame
CRC/sequence/reverse-route correlation, duplicate/replay/expiry rejection, input consumption,
redaction/zeroization lifecycle, and static absence of device/network/USB/logging or generic-command
capabilities.

Public evidence boundaries and claim references are maintained in
[`../../docs/02_EVIDENCE_REGISTER.md`](../../docs/02_EVIDENCE_REGISTER.md) and
[`../../docs/05_RID_CONTROL_SURFACES.md`](../../docs/05_RID_CONTROL_SURFACES.md).
