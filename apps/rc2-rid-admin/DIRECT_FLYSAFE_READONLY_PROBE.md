# Direct modern FlySafe `11/11` read-only probe

Status: A-027 was built, staged, installed, and run once; it returned a parser-class-only ambiguous
failure. Diagnostic-only successor A-028 is built, audited, and staged to RC 2 removable-SD
`Download`; not yet reported installed or run.

## Why this branch exists

The first live A-026 passive-gate run observed no usable `03/09` Area Info or `03/42`
WhiteList Info callback during a 60,003 ms window. Its privacy-reduced result was:

- `GATE_UNOBSERVED`;
- accepted, ignored, malformed, and failure callback counts all zero;
- `11/11 request count=0` because the gate correctly did not admit a query.

This establishes only that the third-party transaction-2 listener did not form a usable passive
view in that run. It does not establish that the aircraft lacks modern FlySafe support, an
inventory, or a type-6 item. The next minimal diagnostic is therefore one explicit active **GET**
candidate, kept separate from every `11/12` write capability.

## Exact candidate and order

There is one candidate, so there is no route scan or fallback order:

```text
sender   type=2, id=4
receiver type=18, id=4
command  11/11
timeout  6000 ms
```

Reasons for fixing this candidate:

1. A-025 already encoded this RC331 Binder candidate as `02:04 -> 12:04`.
2. Current DJI Fly/MSDK static analysis gives product 139 a final FlySafe receiver of type 18,
   index 4 for V2, V3, and V4.
3. RC331's ordinary app4 Binder sender convention is type 2, index 4. The official native provider
   can replace the sender index with runtime state, which remains unknown when the passive route is
   invisible. Therefore index 4 is a compatibility candidate, not a proven live sender identity.

The probe deliberately rejects:

- sender-index iteration `0..7`;
- the RC2 legacy `0A:05 -> 03:00` parameter route;
- the pre-product-override V3 receiver `03:00`;
- the pre-product-override V4 receiver `11:05`;
- any caller-provided route.

Trying those alternatives sequentially would be a route scan and would make a negative result
harder to interpret.

## Codec boundary

The direct probe is V3/V4-compatible only:

```text
group/start: [00 01]
page N:      [00 ((N << 1) & ff)]
```

V3 and V4 use the same application selectors, so even a canonical result cannot distinguish them.
V2 uses a different single-byte page codec and is not tried. A timeout or rejection may therefore
mean, among other possibilities, that the live session is V2 or that the fixed sender candidate is
wrong.

The selector state machine admits exactly one group selector, then page 0, page 1, and so on. It
rejects a missing/repeated group, skipped/repeated page, wrap, route change, cancellation,
interruption, and reuse.

## Retry and duration bounds

- Application-level retries per selector: **zero**.
- RC331 ActQueue schedule represented by the adjacent Binder ABI: initial attempt plus two internal
  retries, each with the fixed 6,000 ms command timeout.
- Callback wait ceiling per selector: 19,000 ms, covering all three timeout periods plus 1,000 ms.
- Whole inventory parser deadline: 90,000 ms.
- Declared inventory count ceiling: 127.
- Page-call ceiling: 128, including the required terminal page.

The application never resubmits the same selector after failure. A user may deliberately start a
new one-shot operation later, but that is a new experiment rather than an automatic retry.

## Result semantics

Only this sequence is a canonical inventory:

1. group callback succeeds with `ccode=0` and a bounded valid group protobuf;
2. exactly `licenses_count` record pages succeed with `ccode=0` and strict bounded records;
3. the next expected page succeeds with `ccode=1` and no data;
4. parsed count, declared count, selector count, and terminator position agree.

An empty inventory is not a timeout. It requires a valid group with `licenses_count=0`, followed by
a data-less `ccode=1` response for page 0.

Canonical completion permits only these statements:

- this fixed Binder candidate returned one count-consistent V3/V4-compatible inventory at that
  time;
- the privacy-reduced count and RID field-7 level/status values shown by the parser describe that
  returned inventory.

It does not prove official support/version cache state, distinguish V3 from V4, prove that current
DJI Fly typed-parses field 7, prove a license signature or regional applicability, or prove an RF
Remote ID effect.

Timeout, callback failure, nonzero unexpected `ccode`, malformed protobuf, count mismatch,
cancellation observed before the next selector, or any noncanonical end is reported as
`DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`. None means unsupported, empty inventory, no
entitlement, or no RID.

Activity-stop cancellation is cooperative at selector boundaries. It cannot retract an already
authorized Binder request; if that request is the final valid terminator, the completed inventory
may still be reported as canonical after the Activity was backgrounded.

## Code separation from `11/12`

`DirectFlysafeReadonlyPass` is privately constructed and implements a private query-authorization
interface. Its public-to-the-enclosing-client operation validates only route plus the V3/V4 query
selector sequence. The Activity calls a method whose signature accepts only that pass and a
selector payload; command set, command ID, route, timeout, retry count, and write payload are not
caller parameters.

The shared low-level sender treats query authorization and a SET dispatch as distinct proof types:

- `11/11` requires one query authorization and no SET dispatch;
- `11/12` requires no query authorization and a separately consumed SET dispatch;
- supplying the direct read-only proof to `11/12` fails before Parcel/Binder dispatch.

The direct Activity path additionally uses the parser's `queryReadOnly` entry point. It preserves
only the public RID level/status view, clears each exact license ID immediately after duplicate-ID
checking, and returns a result that cannot issue an opaque control handle. Direct-pass completion
also rejects a result created by the control-capable parser mode.

No direct-probe UI code can request, receive, or convert a write permit. This does not make the
whole Admin APK globally read-only: other pre-existing experimental controls remain separate, and
the unreleased source tree contains a separately gated validation-pulse setter that is not wired to
this button.

## A-027 build and delivery checkpoint

`testDebugUnitTest` passes 127 tests with zero failures/errors/skips. Seven focused assertions cover:

- the sole exact route and V3/V4 selector order;
- rejection of V2 and all route fallbacks;
- cancellation before another selector;
- canonical group-plus-terminator accounting;
- rejection when the query proof is presented to `11/12` before Binder access;
- rejection of a control-capable parser result and inability of a genuine public-read-only RID
  result to issue a control handle;
- zero application retries and the three-attempt RC331 transport ceiling.

Exact artifact `0.7.0-flysafe-direct-readonly` / code 10 is 196,569 bytes with SHA-256
`aa4bcd9c8aa96870cfbae1ba326d366cb8854a50ef4aff223f7bce4290ddcd81`. Two independent clean
builds were byte-identical; lint had zero errors, APK Signature Scheme v2 and zip alignment were
verified, and the manifest declares zero permissions. It was staged through MTP as removable-SD
`Download/FindUAS_A027_RO.apk`; a fresh listing plus MTP readback matched size and SHA-256.

The subsequent A-027 live run returned `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`, exception
class `ProtocolException`, and `11/12 request count=0`. Because A-027 omitted the exception message,
this does not yet distinguish callback, ccode, group, page, or terminator failure.

A-028 changes diagnostics only. It shows the parser's fixed non-sensitive reason and, where
applicable, the group/page ccode, page index, or terminator data length. Protocol route, selectors,
retry policy, and write separation are unchanged. Exact A-028 is version
`0.7.1-flysafe-direct-diagnostic` / code 11, 197,061 bytes, SHA-256
`d7c32636e19d1bce1b8b8994206355f42d0278b2f15048b14a948a8bbda1d540`. It passed the same 127
tests and lint with zero errors, two clean builds were byte-identical, and v2 signature, zip
alignment, zero permissions, fresh MTP listing, and MTP readback identity were verified. It is
staged as `Download/FindUAS_A028_DIAG.apk`. The operator installed and ran it; the result was
`DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`, `ProtocolException`, detail
`group transport callback failed`, with `11/12 request count=0`. The query did not reach group
protobuf/page/terminator parsing and did not send the set-enable command. This is not evidence of
an empty inventory, no `RID_UNLOCK`, RID-off state, or RF behavior.

## Unbuilt diagnostic-file successor

The current source tree additionally writes the terminal result of every active direct `11/11`
operation to the app-specific external-files path
`getExternalFilesDir("diagnostics")/latest.txt`. The UI prints the actual absolute path, or only
the write exception class if the atomic replacement fails. The UTF-8 file uses schema
`finduas-rc2-rid-direct-diagnostic/v1` and records version, UTC time, fixed operation name, and the
same complete privacy-reduced result displayed by the Activity. A temporary file is synced and
atomically moved over `latest.txt`, preserving the previous complete result if replacement fails.

For a direct transport callback failure, the result now includes the privacy-reduced failure text,
`ccode`/ECode number and the existing redacted Binder/ACK diagnostic. It never includes
`Reply.data`, a raw payload, an ECode description, a license ID, or protobuf bytes. This source
change has not been assigned a new release version, installed, or run. A repository-import
source-only verification build passed 131 JVM tests, lint, and `assembleDebug`; the generated APK
is excluded and is not a sealed successor artifact.
