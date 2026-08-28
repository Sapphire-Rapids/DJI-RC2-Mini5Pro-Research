# Scope, evidence classes, and redaction

## Included systems

The record covers:

- DJI Mini 5 Pro / WA150 aircraft;
- DJI RC 2 / RC331 controller;
- DJI Fly state, native key-value, runtime transport, account, FlySafe, and Remote ID surfaces;
- configured and effective flight-limit evidence;
- FC, Sky, Ground, app-area, O4 regulatory, and SDR state surfaces;
- DJI Assistant 2 metadata/download behavior and firmware trust boundaries;
- RC 2 Android, MTP, hidden Settings, sideloading, development assistant, and ADB;
- public prior art relevant to those same surfaces;
- work-only parsers, admission probes, state-machine models, and route-only artifacts, indexed by
  identity rather than distributed.
- self-developed staged APK identity/audit/delivery records, including A-027/A-028, without
  committing the APK, source, host path, device identifier, raw reply, or license material.

FindUAS receiver and macOS client implementation details remain in the separate
[FindUAS repository](https://github.com/Sapphire-Rapids/FindUAS). This repository records only the
receiver fact needed for DJI RF validation: in the retained observation, actual RID reception began
after operator-initiated motor start.

## Evidence classes

The canonical labels are defined in [README.md](../README.md) and [AGENTS.md](../AGENTS.md).
Each factual statement is scoped to a route, version, and observation window. Static findings from
adjacent firmware stay adjacent-version evidence until live file identity is proven.

## Redaction boundary

Public records may retain:

- public product/app/firmware versions and USB VID/PID values;
- command set/ID, payload schema, symbolic names, timeouts, aggregate counts, status values, and
  non-identifying state such as CN/US;
- public URLs and pinned revisions;
- hashes, sizes, ABI, manifest surface, test count, audit result, and disposition of a local
  research artifact;
- independently written static descriptions and short pseudocode required to state a control-flow
  finding.

Public records exclude:

- device serials, USB locations, storage IDs, host volume names, and local absolute paths;
- real UAS, FC, RC, receiver, registration, operator, account, UID, phone, or coordinate data;
- tokens, cookies, signed URLs, license IDs/descriptions/blobs, ADB/public authorization records,
  private keys, and signer private material;
- raw private BLE/Wi-Fi/DUML/USB/network/logcat/Assistant captures;
- vendor APKs, firmware, partitions, shared libraries, decompiled vendor source, disassembly logs,
  and non-flashable mutation outputs.

The local work corpus contains excluded vendor binaries and generated analysis logs. Their
existence, family, input hash, and supported conclusion may be indexed, but their contents are not
part of this repository.

## Version boundary

- `07.00.0100` is the RC 2 version displayed to the operator.
- A later third-party archive supplied the exact corresponding RC331 signed system aggregate; its
  config/`0205` chain passed independent PRAK/signature/checksum verification. This closes only the
  registered target-package `adbd`/`dpad_fuli` static bytes, not the complete package set or current
  mounted/installed live-file identity.
- RC331 `10.00.0700/0205` is a verified adjacent Android OTA/platform sample.
- RC331 `10.00.0700/0200` passed an outer verification boundary; protected inner FLYA content was
  not recovered.
- DJI Fly 1.21.10 is the current analyzed app sample. Its native behavior is static evidence until
  the live package and mapped-library identities match.

## Interpretation boundaries

- `connected USB` is not an official MSDK session.
- `ACK` is not state readback.
- `state readback` is not persistence.
- `country changed` is not RF power changed.
- `onboard normal` is not independent RF reception.
- `Java false` is not necessarily canonical protocol success because a converter may fold a
  nonzero protocol result into false.
- `unavailable` is not off, unsupported, or empty.
- a generated key name is not a live handler.
- a fixed product-route candidate is not independently corroborated merely because public sources
  document the generic DUML or FlySafe family.
