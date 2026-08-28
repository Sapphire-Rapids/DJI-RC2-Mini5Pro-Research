# Negative results and retractions

Each entry states the tested scope, positive control where available, observed result, and the
stronger conclusion that cannot be drawn.

## N-01 — no ordinary global RID Boolean found

- Status: `NEGATIVE`.
- Scope: current DJI Fly 1.21.10, MSDK 5.18.0 mappings, product-139 registration, generated key
  inventory, and reviewed public implementations.
- Result: no ordinary Boolean handler was found that spans France EID, EASA OPID/C0, Japan DIPS,
  FAA/US, China OID, and general Broadcast Remote ID.
- Does not establish: that no hidden firmware, server entitlement, region-specific product, or
  different build has such a control.

## N-02 — fixed direct France-EID GET routes

- Status: `NEGATIVE`.
- Preconditions: exact product-139 static receiver candidate `0x92`, GET `0x03/0x77 [02]`, strict
  CRC/route/sequence/command matcher, one request per artificial route, three-second window.
- Result: neither the aircraft direct route nor RC USB artificial route returned a canonical ACK.
- Positive controls: ordinary fixed queries on the same physical paths returned valid replies.
- Does not establish: France EID off, unsupported, absent, or unreachable from DJI Fly's private
  already-initialized owner/session.

## N-03 — two RID-policy hash F7 probes

- Status: `NEGATIVE`.
- Scope: `EU_CE_enable_c0_rid_0` and the second current RID-policy candidate, over both fixed
  direct/RC routes.
- Result: F7 returned one-byte status `0x03` rather than parameter metadata.
- Positive controls: known height/distance hash parameters returned usable metadata/value data on
  the same route family.
- Consequence: no F8 current-value snapshot or F9 rollback target existed; no F9 was sent.
- Does not establish: the exact enum meaning of status `0x03`, or whether a private owner/other
  product session implements the parameter.

## N-04 — legacy FlySafe inventory query

- Status: `NEGATIVE`.
- Scope: one fixed legacy `0x11/0x11` request on each artificial route.
- Result: both timed out.
- Positive controls: FC area and Sky/Ground country queries around the same work returned valid
  responses.
- Does not establish: empty inventory, no type-6 license, no FlySafe support, or the correct
  V2/V3/V4 session/version/route.
- Disposition: the unchanged request is not a useful repeat until support/version and exact current
  route are known.

## N-05 — passive support/version and RID status windows

- Status: `NEGATIVE`.
- Scope: bounded passive direct USB windows with strict CRC-valid DUML classification.
- Result: no `0x11/0x1C`, `0x03/0x09`, `0x03/0x42`, `0x03/0x77`, `0x11/0x11`, `0x11/0x12`, or
  `0x11/0x4B` candidate in the specified windows.
- Other observed traffic: ordinary CRC-valid traffic and active frames involving packed receiver
  `0x92` were present.
- Does not establish: lack of module, capability, subscription, state transition, or motor-on RID.

## N-06 — Ground country US request

- Status: `NEGATIVE`.
- Preconditions: two baseline Ground GETs returned CN; one authorized US SET was sent.
- Result: no strictly matching ACK; the following fresh GET remained CN.
- Consequence: no retry and no restore SET were sent because no forward change was observed.
- Does not establish: permanent Ground-route non-support. Route/session/target/authorization remain
  possible variables.

## N-07 — legacy RC PowerMode GET

- Status: `NEGATIVE`.
- Scope: legacy `0x06/0x21` on the two fixed candidate routes.
- Result: no response.
- Does not establish: CE or FCC state, actual transmit power, or absence of a modern replacement.

## N-08 — SDR selector value naming

- Status: `UNKNOWN` after an `OBSERVED` read.
- Observation: both endpoints returned `0xFFFF0048=5` and `0xFFFF0063=0` with result 0.
- Static positive fact: legacy `setForceFcc()` writes literal 2 to `0xFFFF0048`; legacy
  `0xFFFF0063=0` is dual-band.
- Negative: no exact current evidence assigns semantic name CE/FCC/auto/power level to selector 5.
- Does not establish: current O4 mode or EIRP.

## N-09 — public FCC profile causality

- Status: `NEGATIVE` for minimal-protocol attribution.
- Scope: reviewed FreeFCC/Skylab profiles, keepalives, source labels, and issue history.
- Result: profiles contain country, legacy SDR, flight-limit, safety, activation, and unidentified
  commands; local socket-write success is the primary success signal.
- Does not establish: which frame causes the visible effect, that every frame is required, that a
  CE restore is complete, or that RF power changed.

## N-10 — Android Wi-Fi regdomain as O4 evidence

- Status: `NEGATIVE` inference boundary.
- Result: O4 radio/platform services and ordinary Android Wi-Fi are separate surfaces.
- Does not establish: that a Linux/Android Wi-Fi country change modifies O4 country, channel table,
  or transmit power.

## N-11 — standard MTP package recovery

- Status: `NEGATIVE`.
- Scope: read-only PTP/MTP `GetDeviceInfo`, `GetStorageIDs`, `GetObjectHandles`, and
  `GetObjectInfo`.
- Result: one storage and a directory skeleton; no files, exact DJI Fly package, exposed private
  application directory, or matching `libsdk_jni.so`.
- Does not establish: those files are absent inside Android or unavailable through a separately
  authorized vendor export mode.

## N-12 — Assistant RC 2 log export

- Status: `NEGATIVE`.
- Static result: the active RC 2 exporter implements data-file functions, while `GetLogList` and
  `ExportAllLog` are unsupported stubs despite the front-end route.
- Does not establish: no logs exist on the controller. It establishes that those specific front-end
  calls cannot be treated as a working backend.

## N-13 — exact `07.00.0100` local package set

- Status: `NEGATIVE`.
- Scope: Assistant 2 2.1.40.0 caches/logs/Local Storage, ordinary download locations, and retained
  RC331 material.
- Result: no exact signed module manifest, `0205` body, `framework.jar`, `services.jar`, or
  `dpad_fuli.apk` tied to displayed `07.00.0100`.
- Does not establish: that the package is unavailable from DJI or cannot be read from another
  authorized source.

## N-14 — WA150 Assistant plaintext readback

- Status: `NEGATIVE`.
- Result: retail Assistant paths exposed diagnostic log/data FTP, not `0802` plaintext readback;
  the ESC `ReadFlashData` UI had no recovered WA150 backend binding.
- Does not establish: no manufacturing/service readback exists. No such safe retail path was found.

## N-15 — WA150 public key/material availability

- Status: `NEGATIVE`.
- Result: available public PRAK/STUE material did not validate/decrypt the target protected modules.
  Force output remained protected/unverified data.
- Does not establish: the container is cryptographically impossible to recover with authorized
  target keys or future public material.

## N-16 — checksum repair as patch acceptance

- Status: `NEGATIVE`.
- Result: public outer values could be recomputed after a ciphertext mutation, but the correct
  modified plaintext checksum was not established and the signature-covered message changed while
  retaining the old signature.
- Does not establish: a signature bypass, decryption, valid plaintext, or loader acceptance.

## N-17 — cross-version ciphertext reuse

- Status: `NEGATIVE`.
- Scope: retained `01.00.0600`/`01.00.0700` `0802` samples and five STUE samples.
- Result: unique wrapped values, no equal aligned 16/32-byte blocks, random-like XOR statistics.
- Does not establish: the complete cipher mode. It rejects the tested simple reuse/crib route.

## N-18 — 2026 public breakthrough search

- Status: `NEGATIVE` within the reviewed source set.
- Result: no reproducible WA150 decrypt/re-sign/readback/recovery chain and no public Mini 5 Pro +
  RC 2 RID switch with baseline/readback/restore/RF closure was found.
- Does not establish: that no private or future implementation exists.

## N-19 — N3Live scope

- Status: `NEGATIVE` for earlier attribution.
- Result: pinned N3Live reads Goggles N3 USB interface 4. It has no RC-local `40007`/`40009`, RID
  decoder, encryption-selector parser, or proven Mini 5 Pro control path.
- Positive contribution: DUML v1 framing/CRC/address behavior and a generated command-name corpus.
- Does not establish: current RC 2 transport, clear O4 payload, RID request schema, or safe setter.

## N-20 — second localhost observer safety

- Status: `RETRACTED`.
- Earlier assumption: no-output client meant no transport side effect.
- Later static result: adjacent broker defaults to one active accepted fd; a newcomer can close and
  replace the prior fd on connect.
- Disposition: observer v0.1-v0.4 live use withdrawn. Decoder tests remain offline evidence only.

## N-21 — stock `dpad_fuli` command carrier

- Status: `NEGATIVE`.
- Scope: 30 activities, two receivers, one service; six externally reachable components.
- Result: no side-effect-free fixed-argv UID1000 path that returns stdout, stderr, and exit status.
  The private Shell page automatically tries `adb shell su` and `adb version`, and drops stderr/
  exit status. The Protocol page lacks selector control and loses retry information through Parcel.
- Does not establish: that no other signed system package or future audited carrier exists.

## N-22 — ordinary app attach-agent privilege

- Status: `NEGATIVE`.
- Static result: Android 11 `attach-agent` requires signature permission
  `SET_ACTIVITY_WATCHER`; executing `/system/bin/cmd` does not change an ordinary app's UID.
- Does not establish: whether an actual, separately audited UID1000 caller on the live build can
  pass all other target/debug/SELinux/load-path gates.

## N-23 — stock ADB troubleshooting variants

- Status: `NEGATIVE`.
- Result: stock legacy/libusb backends, pinned DJI-oriented pre-auth profile, and isolated
  version/MAXDATA/banner/checksum changes all stopped after host `CNXN` with no device packet.
- Static explanation: adjacent `adbd` production CNXN drop before RSA.
- Does not establish: exact binary identity with live v07 or the behavior of an unexecuted
  first-packet AUTH public-key experiment.

## N-24 — `once_auth_open_adb` as a usable switch

- Status: `NEGATIVE` static search.
- Result: a read was found in the adjacent binary, but no writer/safe setter; the independent
  per-CNXN production gate does not consult it.
- Does not establish: absence of an external privileged writer in another component. It is not a
  documented usable debug switch in the current evidence.

## N-25 — global same-worker route epoch

- Status: `RETRACTED`.
- Result: main datalink add/remove work is serialized, but ProductMgr callbacks inherit unresolved
  producer threads and the complete HardwareLayer writer set is not closed.
- Consequence: worker-tail recheck is only `STABLE_OBSERVED`, not atomic route ownership.

## N-26 — fixed 100 ms quiescence window

- Status: `RETRACTED`.
- Result: ACK delivery precedes pending-node erase; timer delivery precedes copied-owner
  destruction; explicit cancel posts asynchronous cleanup and may suppress Java timeout through
  Stopper state.
- Consequence: callback return, cancel return, or elapsed time cannot prove terminal cleanup.

## N-27 — V2.2 artifact admission

- Status: `RETRACTED` and rejected.
- Independent findings: early runtime program-header dereference, writable-map acceptance for
  original non-writable content, and missing `st_dev != 0` enforcement.
- Positive fact: fixed-zero exception gate still prevented the dormant send route.
- Disposition: exact V2.2 artifact permanently `DO NOT INSTALL OR ATTACH`; V2.3 is a distinct build.

## N-28 — V2.3 as live permission

- Status: `NEGATIVE` boundary.
- Result: V2.3's own packaged audit and host tests report the three V2.2 corrections, deterministic
  builds, fixed-zero gate, and zero-send inventory.
- Missing: new independent post-fix audit and every live admission gate.
- Does not establish: safe attach, valid live identity, request support, or RID state.
