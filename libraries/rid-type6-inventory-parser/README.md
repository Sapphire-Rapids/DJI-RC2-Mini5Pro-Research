# Strict V3/V4 RID inventory parser (work-only research)

This isolated Kotlin/JVM module implements a bounded, read-only semantic parser for the DJI
FlySafe V3/V4 FC license inventory recovered by offline static analysis. Status: **STATIC** and
read-only; entitlement or device-control use is **NOT ADMITTED**. It does not perform
device, socket, file, cloud, or setter I/O. The independently written source is covered by the
repository-root [MIT license](../../LICENSE).

## Evidence boundary

The parser is based on local static analysis whose public evidence boundaries and claim references
are maintained in [`../../docs/02_EVIDENCE_REGISTER.md`](../../docs/02_EVIDENCE_REGISTER.md) and
[`../../docs/05_RID_CONTROL_SURFACES.md`](../../docs/05_RID_CONTROL_SURFACES.md). Vendor/decompiled
inputs are intentionally not distributed.

The recovered V3/V4 response schema is:

```text
group response body: protobuf LicenseGroupInfo
record response body: status byte + protobuf License

License.data field 6 -> protobuf LicenseData
LicenseData.rid field 7 -> protobuf LicenseDataRID
LicenseDataRID.level field 1 -> uint32
```

`RID_UNLOCK` is **domain type 6**. The nested protobuf RID oneof is **field 7**. They are not the
same numbering layer. V2 is deliberately unrepresentable: observed version code 0 is rejected and
cannot be upgraded into a type-6 candidate.

Static evidence proves this schema and parser route in the analyzed DJI Fly/MSDK artifacts. It does
not prove that the currently connected Mini 5 Pro exposes a genuine type-6 record, that an account
owns it, that a signature is valid, or that enabling it changes over-the-air Remote ID. This module
therefore returns only `UnverifiedRidInventoryCapability`; it has no path to the controller's
`VerifiedRidUnlockLicense` type and no write API.

## Security and privacy properties

- All APIs are Kotlin `internal` by default.
- A parser cannot accept a record until a one-shot correlation capability binds the observed V3/V4
  session, exact read-only `0x11/0x11` ACK metadata, sequence, status byte, and protobuf bytes.
- Group output contains only `licenses_count` and a truncated SHA-256 pseudonym. Group ID,
  timestamp, aircraft serial, and user ID are validated but never returned or logged.
- RID output contains only domain type 6, classified level, and externally supplied status-bit
  state. Bits 3..7 are preserved as uninterpreted data because static evidence assigns semantics
  only to bits 0..2. Description and time fields are parsed/discarded. The raw uint32 ID exists
  only as little-endian bytes in an `AutoCloseable` capability; its scoped callback copy and
  backing bytes are wiped, and its string form is redacted.
- Non-RID records expose only a type classification and aggregate count; IDs, geometry, identity,
  description, and time values are not retained.
- The handwritten wire reader caps top-level and nested lengths, nesting depth, field counts,
  licenses/page count, and varint width. It rejects truncation, overflow, non-canonical varints,
  invalid tags, protobuf
  groups, wrong wire types, duplicate known singular fields, oneof conflicts, invalid UTF-8,
  non-canonical booleans, zero license IDs, and count/terminator disagreement.
- Unknown fields are skipped only within the same strict byte/field budget. They are never logged.

The response-correlation factory is a typed boundary for a future read-only transport. It is not a
cryptographic proof of DJI signature, account binding, or license applicability. A later verifier
must independently establish those properties before producing any controller credential.

## Test

Use JDK 21; emitted bytecode targets JVM 17:

```sh
export JAVA_HOME=/path/to/jdk-21
gradle clean test
```
