# Timeline

Times are Asia/Shanghai unless explicitly stated. File modification times were used only to order
work when a report did not contain a more precise timestamp.

## 2026-08-27

### 02:33–05:12 — USB routes and fixed read-only state

- `OBSERVED`: aircraft and RC 2 enumerated as separate DJI USB devices.
- `OBSERVED`: bounded passive bulk summaries and fixed UID/application/parameter probes were run.
- `OBSERVED`: at 05:12:42.250–05:12:54.893, fixed SDR Assistant reads returned the same values at
  both endpoints: `0xFFFF0048=5`, `0xFFFF0063=0`, result 0.
- `NEGATIVE`: legacy RC PowerMode `0x06/0x21` returned no response on the two candidate routes.

### 05:12–13:33 — account, limit, RID, and RF model separation

- `OBSERVED`: both fixed paths returned privacy-minimized UUID/application Boolean results.
- `OBSERVED`: configured height=500 m, radius=5000 m, radius-limit-enabled=0 on both paths.
- `STATIC`: login state was separated into cached credential, server validation, and FC UID sync.
- `STATIC`: configured limit values were separated from an unresolved runtime/effective 30/50 m
  layer.
- `STATIC`: RID working-status, France EID, FlySafe exception, EU C0, and broadcast-effect surfaces
  were separated.

### 13:33–15:12 — bounded area/country state transactions

- `OBSERVED`: FC area completed `CN/156 -> US/840 -> CN/156`, with ACK and fresh GET after each
  write and a final read-only confirmation.
- `OBSERVED`: Sky country completed double-CN precheck, `US` write/readback, `CN` restore/readback.
- `NEGATIVE`: Ground country completed double-CN precheck and one US request, but no strictly
  matching ACK arrived; the following GET remained CN. No retry or restore SET followed.
- `OBSERVED`: later independent reads returned FC/Sky/Ground all CN.
- `UNKNOWN`: the receiver was offline, so no RID, channel, or RF effect was measured.

### 16:28–19:09 — Assistant and exact static inputs

- `STATIC`: Assistant metadata and named package inventory were collected.
- `STATIC`: RC331 `0205` verified/extracted without force; RC331 `0200` outer verification passed
  while inner FLYA remained protected.
- `STATIC`: WA150 `0802`, `2603`, and protected `0806/DONG` roles were compared.
- `STATIC`: official DJI Fly 1.21.10 became the current targeted app sample.

### 19:23–23:59 — RID and FlySafe schema recovery

- `STATIC`: working-status layout, hash-parameter family, license inventory, type-6 models,
  cloud-control writers, and runtime transport components were mapped.
- Work-only parsers and state models were built and tested offline. No parser result was described
  as a live license or live RID status.

## 2026-08-28

### 00:40–03:37 — exact control-surface separation

- `STATIC`: FlySafe query/set-enable V2/V3/V4 structures and support/version gates were recovered.
- `STATIC`: product-139 France EID was resolved to `0x03/0x77`, receiver `0x92`, GET `[02]`, SET
  `[00]/[01]`, and canonical ACK layouts.
- `STATIC`: EASA operator-registration `0x03/0x78` was separated from broadcast enable.
- `OBSERVED/NEGATIVE`: one fixed France-EID GET was sent on each of two artificial direct routes;
  neither returned a canonical ACK within the fixed window. No SET, retry, or route scan occurred.

### 05:17–05:32 — live-version gap and localhost retraction

- `NEGATIVE`: Assistant caches, logs, ordinary download locations, and retained material did not
  contain the exact complete `07.00.0100` signed package/ABI set.
- `STATIC`: adjacent RC331 `0205` broker configuration and code showed single-active-fd default
  behavior on `40007`/`40009`.
- `RETRACTED`: observer v0.1-v0.4 live procedures were withdrawn because `connect()` alone can
  replace DJI Fly's fd.

### 06:34–08:16 — no-root and semantic-anchor artifacts

- V0 attach canary and V1 semantic resolver were built and audited offline.
- Public precedent was rechecked.
- `NEGATIVE`: the complete exported-component review of adjacent `dpad_fuli` found no
  side-effect-free fixed-command UID1000 carrier preserving argv/stdout/stderr/exit status.

### 08:45–13:23 — same-owner tuple and lifecycle analysis

- `STATIC`: current native tuple, true dynsym/RVA, route worker, mutator, exception, callback,
  pending, Stopper, and mapping boundaries were analyzed.
- V2 raw carrier and V2.1 route-only artifact were sealed with send paths unreachable.
- `RETRACTED`: global same-worker epoch and fixed 100 ms callback quiet-time assumptions were
  withdrawn.

### 13:42–14:09 — mapping/quiescence audit and V2.2 rejection

- `STATIC`: exact adjacent ART mapping-retention behavior was bounded.
- Host-only quiescence model 0.1.1 passed 17 synthetic tests after independent corrections.
- `RETRACTED`: V2.2 was rejected by independent review: runtime headers were trusted too early,
  writable mappings could be accepted for original non-writable loads, and `st_dev==0` was not
  rejected.

### 14:22–14:36 — hidden Settings, V2.3, and v0.9 audit

- `STATIC/OBSERVED`: fixed Android Settings intents were mapped; a launcher artifact was copied to
  removable media with matching hash. Copy did not itself prove installation.
- `STATIC/OFFLINE`: V2.3 fixed the three V2.2 defects, retained immutable-zero exception gating and
  zero-send behavior, and was sealed. No separate new independent post-fix audit report exists.
- `RETRACTED`: v0.9 remained sealed after independent audit found attestation/provenance weaknesses.

### 15:03–15:15 — live ADB handshake

- `OBSERVED`: stock ADB backends, the pinned Dr-Muh profile, and five isolated pre-auth variants
  transmitted `CNXN` but received no ADB packet; bulk-IN timed out at about 15 seconds.
- No `AUTH` public key, `OPEN`, shell, install, or device command was sent.
- `STATIC`: adjacent unstripped `adbd` production CNXN drop branch explained the same boundary.

### 15:49–15:50 — v0.10 probe closure

- `STATIC/OFFLINE`: v0.10 fixed the v0.9 audit findings.
- Exact artifact passed 43 tests, lint, final manifest/DEX/signature/zipalign checks, 21/21
  adversarial mutations, two byte-identical clean builds, and independent review with no unresolved
  P0–P3.
- The APK was not copied, installed, or run on RC 2.

### 16:16 — public research synchronization

- Redacted ADB, v0.10, retry-layout, route, exception, mapping, and quiescence conclusions were
  synchronized to the FindUAS repository at commit `15f331c`.

### 17:10–17:41 — NLD FCC Smart RC 2.0.0.6 static comparison

- `STATIC`: the supplied Smart RC ZIP matched the current official download bytes; the embedded
  app identified itself as `2.0.0.6` even though the downloads page displayed `2.0.0.1`.
- `STATIC`: seven packaged profiles were byte-identical to pinned FreeFCC, but no application or
  native runtime reference to them was found.
- `STATIC`: normal FCC was traced through native online/native-offline payload decode and DUSS;
  the exact command sequence remained opaque.
- `STATIC`: C0 was traced through online VPN configuration, server-routed WireGuard, DJI Fly
  lifecycle, and a 25-second automatic-stop schedule after tunnel UP.
- `NEGATIVE`: a bounded full-package search found no identifiable Remote ID control surface.
- No APK was installed or executed, no NLD API was contacted, and no controller or aircraft state
  changed.
