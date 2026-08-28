# Adjacent RC331 Binder ABI audit for the hard-coded France EID GET

Date: 2026-08-28 (Asia/Shanghai)

Scope: pure static comparison of the offline probe against the locally extracted official
adjacent RC331 `10.00.0700/0205` framework and service artifacts. Nothing in this audit was copied
to or executed on RC 2 or the aircraft.

## 1. Binder service transaction

The adjacent `IProtocolManager.Stub` declares:

```text
descriptor       com.dji.protocol.IProtocolManager
isEnable         transaction 1
addPackListener  transaction 2
send             transaction 3
sendWithListen   transaction 4
removeListener   transaction 5
```

Its transaction-4 decoder performs this exact sequence:

```text
enforceInterface(descriptor)
readInt() != 0
Pack.CREATOR.createFromParcel(data)
IPackListener.Stub.asInterface(data.readStrongBinder())
sendWithListen(pack, listener)
reply.writeNoException()
```

The offline probe mirrors that sequence with one synchronous `IBinder.transact(4, ..., 0)` and
then calls `reply.readException()`. DEX disassembly contains exactly one outbound
`IBinder.transact` callsite and no copied `com.dji.*` class.

Evidence:

- excluded RC331 `IProtocolManager` static audit; transaction and Parcel spans are retained in the evidence record
- decompiled-source SHA-256
  `b896a474362db1b42b683564b773b3d6703f413409694802bbaebd1613920f9a`

## 2. `Pack` request Parcelable

`Pack.writeToParcel` and `Pack(Parcel)` use the following order. The probe writes the request in
the same order; `explicit data length` and the length internal to `writeByteArray` are separate
values and are both present.

| Position | Vendor field | Hard-coded request value |
|---:|---|---:|
| 1 | `sof` byte | `0x55` |
| 2 | `version` int | `1` |
| 3 | `length` int | `0`, recomputed in server |
| 4 | `crc8` int | `0`, recomputed in server |
| 5 | `senderId` int | `4` |
| 6 | `senderType` int | `2` |
| 7 | `receiverId` int | `4` |
| 8 | `receiverType` int | `0x12` |
| 9 | `seq` int | `-1`, allocated in server |
| 10 | `cmdType` int | `0` request |
| 11 | `isNeedAck` int | `2` ACK-after-exec |
| 12 | `cmdType` int again | `0` request |
| 13 | `encryptType` int | `0` clear/default |
| 14 | `cmdSet` int | `0x03` |
| 15 | `cmdId` int | `0x77` |
| 16 | explicit data length int | `1` |
| 17 | byte array | `[0x02]` GET |
| 18 | `ccode` int | `0` |
| 19 | `crc16` int | `0`, recomputed in server |
| 20 | `timeOut` int | `500` |
| 21 | `retryCnt` int | `0` |

Evidence:

- excluded RC331 `Pack` static audit; write/read order is retained in the evidence record
- decompiled-source SHA-256
  `863a2885b916f035e2ba503bbc4976099f9df340a612718690524d792bd905a1`

The duplicated `cmdType` is not a documentation typo. Both vendor reader and writer contain it.
`maxRetryCnt` is absent. The vendor constructor initializes the server-side value to two before
reading this Parcel, so a 500 ms timeout can result in two retries and three total transmissions.
This is safe only because the sole available operation is an idempotent GET.

The adjacent `Pack.Builder` defaults encryption to zero and has no encryption setter. This probe
uses that lane. DJI Fly's separate product-139 native provider requests selector three, so the two
paths must not be described as byte-for-byte equivalent.

## 3. Callback Binder ABI

The adjacent callback interface declares:

```text
descriptor  com.dji.protocol.IPackListener
onSuccess   transaction 1, one-way
onFailure   transaction 2, one-way
```

The probe attaches that exact descriptor to its local Binder and handles only transaction 1,
transaction 2, and standard `INTERFACE_TRANSACTION`. Unknown codes go to `Binder.onTransact`.

For transaction 1 it reads the presence int and then the same 21-field `Pack` Parcel order. For
transaction 2 it reads the presence int and then the `ECode` layout:

```text
id:int
explicit description length:int
description:byte[] when length > 0
```

Evidence:

- excluded RC331 `IPackListener` static audit; callback spans are retained in the evidence record
- `IPackListener.java` SHA-256
  `8b4ee4113fc9314cf5032da1308f1e13f75f7ed5091e9cc3905bda4d4270339d`
- excluded RC331 `ECode` static audit; failure layout is retained in the evidence record
- `ECode.java` SHA-256
  `993703913c046518aa6b7de381c6d3ea7a3cb54218a173b570b491635bc6406c`

## 4. Success acceptance set

The callback reports a state only if every condition below holds:

1. no trailing Parcel bytes;
2. `sof == 0x55`, version `1`, and canonical ACK length `15`;
3. sender `0x12/4` and receiver `2/4`, the exact reverse of the request;
4. sequence is within unsigned DUML-v1 range;
5. both duplicated `cmdType` fields equal ACK `1`;
6. ACK policy is clear response `0` or mirrored ACK-after-exec `2`;
7. encryption selector is `0`;
8. command remains `0x03/0x77`;
9. `ccode == 0`;
10. exposed `data` is exactly one byte and that byte is exactly `0` or `1`.

The service's `ActQueue` performs the request-sequence/reverse-endpoint correlation before invoking
this per-request callback. The client cannot independently compare the request sequence because
the server assigns it after reconstructing its private `Pack`; the client nevertheless validates
the returned sequence domain and exact route/command.

## 5. Build audit result

`audit.sh` performs:

- deterministic rebuild;
- DEX checksum verification with `dexdump -c`;
- DEX disassembly and JADX decompilation;
- ten source/artifact contract tests;
- artifact-level socket, output-stream, shell-exec, activity-launch, property-write, localhost,
  and port-literal denylist;
- check that the DEX contains exactly three FindUAS classes and no bundled DJI classes;
- check that the DEX has exactly one `IBinder.transact` callsite.

Final artifact:

```text
file    FindUAS-France-EID-GET-readonly.jar
size    5,286 bytes
SHA-256 f288ebb5da11afc66f90eee19dae0a27c309e68e80a69ad619d5f8e909b6b0e4
```

Runner:

```text
file    runner/run-france-eid-get-readonly.sh
size    381 bytes
SHA-256 acfb44082e0e2ff85eaac3ae05c7d706481c30de7498a6bf4bf0fbd4e8358aea
```

Two consecutive builds produced the same artifact SHA-256.

## 6. Fail-closed live boundary

This audit proves fidelity only to the adjacent RC331 artifacts. It does not prove that live RC 2
firmware `07.00.0100` publishes the service, permits lookup/calls under its SELinux policy, uses the
same Parcelable ABI, accepts the fixed route, or supports France EID on the connected aircraft.
Those remain mandatory preconditions before any live execution. There is no socket or raw-DUML
fallback if any precondition fails.
