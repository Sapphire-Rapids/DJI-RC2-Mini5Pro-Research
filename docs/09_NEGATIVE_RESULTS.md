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

## N-29 — NLD 2.0.0.6 explicit Remote ID control

- Status: `NEGATIVE` within a fixed static scope.
- Scope: both DEX files, decompiled sources, manifest, all localized resources, seven packaged
  profiles, and printable strings from both native ABIs.
- Result: no identifiable NLD Remote ID UI, switch, setting, command, profile, service, or handler.
- Does not establish: absence of an indirect effect from an opaque native/server payload, a generic
  raw frame, server-selected region policy, or the separately hosted DJI Fly APK.
- Consequence: the generic vendor catalogue claim cannot be treated as a stable Mini 5 Pro RID
  control implementation.

## N-30 — NLD packaged-profile runtime attribution

- Status: `NEGATIVE` for runtime-source attribution.
- Positive fact: all seven files are byte-identical to pinned FreeFCC profiles.
- Scope: filename, path, JSON-key, DEX/source, native string/import, asset-manager, and archive
  loader searches in exact NLD `2.0.0.6`.
- Result: no application runtime loader or reference was found; the only asset-manager call belongs
  to AndroidX compiler-profile installation.
- Does not establish: that a hidden custom parser is impossible, or that an opaque online/offline
  payload cannot decode to similar bytes.
- Consequence: the visible 21-frame batch, keepalive, CE restore, and labels cannot be attributed to
  the current NLD execution path merely because the files are packaged.

## N-31 — NLD main-app root or file-patch path

- Status: `NEGATIVE` within a bounded static scope.
- Scope: manifest/components, all DEX/decompiled sources, both native import/string sets, and
  identifiable process/property calls in NLD `2.0.0.6`.
- Result: no ADB client, `su`/Magisk, mount/remount, DJI configuration/database patch, or Binder FCC
  path was found. The only found native shell property operation belongs to launcher selection.
- Does not establish: absence of behavior encoded in opaque data, performed by NLD services, a
  separately installed helper, or the separately hosted DJI Fly APK.

## N-32 — Drone-Hacks 2.0.29 explicit Remote ID control

- Status: `NEGATIVE` within a fixed static/public scope.
- Scope: MSI payload identities, direct Tauri command schema, mobile feature enum, Rust type and
  source-path metadata, endpoints, model tokens, UI/resource strings, generic DUSS names, public
  compatibility/license/product data, and public CFC documentation.
- Result: no identifiable RID feature, switch, local command, parameter, CFC Name command, server
  job name, or Mini 5 Pro RID implementation was found.
- Positive clues kept separate: a generic DUSS vocabulary contains ADSB RID/EID labels; a broad
  server job engine can send custom packets; a firmware-resident CFC exists for listed older models.
- Does not establish: absence of an opaque authenticated server job, unpublished firmware code, a
  different private product, or a future version.
- Consequence: Drone-Hacks cannot currently be cited as a working Mini 5 Pro RID control or protocol
  implementation.

## N-33 — China OID report-enable as an RF Remote ID switch

- Status: `NEGATIVE` for RF-switch attribution; the app-side gate itself is `STATIC`.
- Positive fact: current DJI Fly `1.21.10` native exposes report/simulator/mock Booleans through
  `UAVOIDManager`.
- Result: the normal Boolean selects network `Submit` versus `DirectSuccess` after OID push parsing.
  It has no recovered gate getter and no aircraft broadcast writer.
- Corroboration: the adjacent Java path binds it to `CN_OPERATE_ID_EFFECT`, not to the distinct
  opaque `dji_fly_rid_cloud_control_v2` policy.
- Does not establish: absence of an aircraft-side RID switch in encrypted firmware, managed license,
  opaque cloud payload, or a later app.
- Consequence: `setOIDReportEnable(false)` must not be presented as stopping BLE/Wi-Fi RID.

## N-34 — current exact app/native global RID setter

- Status: `NEGATIVE` within DJI Fly `1.21.10` readable app/native surfaces.
- Result: the targeted registration/function search found France EID switch wrappers and helper
  validation, but no product-139 EID broadcast-enable, EID open/close, ODID/OpenDroneID, or global RF
  setter handler. MSDK's America broadcast-enable method mutates a status object, not the device.
- Does not establish: absence inside WA150 encrypted firmware, server-selected opaque policy, signed
  type-6 state, or future versions.

## N-35 — Drone-Hacks ADSB display table as a current WA150 schema

- Status: `NEGATIVE` for current-schema attribution; the numerical recovery itself is `STATIC`.
- Positive fact: the exact Drone-Hacks `2.0.29` Debug path maps `RID_INFO` to `0x11/0x1A`,
  `EID_INFO` to `0x11/0x35`, and 26 other ADSB labels to exact command IDs.
- Conflict: it calls `0x11/0x0C` `PASS_THROUGH_REPORT` and `0x11/0x1C` `DEVICE_LIST_GET`, while
  exact DJI Fly `1.21.10` maps those tuples to ADSB on/off handling and RID working-status push.
- Result: the table is suitable for passive classification and static xref searches, not for
  constructing a Mini 5 Pro request or inferring a RID setter.
- Does not establish: that `0x11/0x1A` or `0x11/0x35` is unsupported by WA150 firmware; exact
  current handler ownership, direction, payload, route, and product gate remain unknown.

## N-36 — public WA150 plaintext, target key, and recovery route

- Status: `NEGATIVE` within the fixed public scope searched on 2026-08-28.
- Positive facts: public Mini 5 Pro metadata independently matches both known `0802` module versions;
  public advisories identify BLE DUML/network surfaces through 0600; FCC reports identify a vendor
  engineering test tool.
- Result: no `0802` plaintext, symbols, target PRAK/STUE, replacement trust root, recovery image,
  RID handler, 0700 plaintext diff, or reproducible public PoC was found.
- Does not establish: absence from private/unindexed sources or from decrypted content resident on a
  legitimately running device. It does not reduce the firmware-modification admission gate.

## N-37 — active read-only RID status command in current DJI Fly

- Status: `NEGATIVE` within the closed DJI Fly 1.21.10 product-139 status/cloud-control paths.
- Positive fact: product-139 mounts `RidImportModule` and listens for `0x11/0x1C`; the seven-byte
  status layout and regional capability bits are statically closed.
- Result: the status key has no GET/set/action and the separate `0x00/0xDD` cloud-control key is
  SET-only, value-routed, and returns no applied-state echo. No fixed safe receiver tuple,
  reset/disable/debug handler, or static correlation between the two surfaces was found.
- Does not establish: that firmware cannot emit the push or implement a hidden control. The only
  admitted current read path is passive observation of a naturally emitted push after the official
  owner has subscribed; it is not an active query or independent RF proof.

## N-38 — legacy FlyC `Detection` mask as a Mini 5 Pro RID switch

- Status: `NEGATIVE` for modern-product attribution; the legacy schema is `STATIC` and its
  correspondence to the paper is a bounded `INFERENCE`.
- Positive fact: DJI-derived midware maps `0x03/0xDA` subcommands `0x05`/`0x06` to an eight-field
  DroneID mask matching the NDSS description.
- RF result: the paper reports packets continued and selected fields were replaced with `fake`;
  the control did not suppress the proprietary OcuSync DroneID transmission.
- Result: no public primary evidence shows WA150 registers this handler or maps it to ASTM/FAA/EU
  Broadcast RID. Current DJI Fly retaining the generic old class is not product support.
- Does not establish: permanent absence from WA150 firmware. Exact current handler/route evidence
  would be required before even a read experiment, and a write additionally requires full
  baseline/readback/restore/RF closure.

## N-39 — LTE phone upload as a Remote ID operator-phone field

- Status: `NEGATIVE` for RID attribution in exact DJI Fly 1.21.10.
- Positive fact: `LteUserPhoneNumberSet` is a set-only `0x03/0xDA` LTE HYBRID business path whose
  caller periodically uploads bound/encrypted telephone state and has no getter/readback.
- Result: the path is unrelated to the product-139 Broadcast RID identity/configuration surfaces;
  ordinary standards-based Broadcast RID has no operator telephone message element.
- Does not establish: the source of a telephone displayed by proprietary detection software. A
  China OID/UTMISS, account, or registration-service association remains possible and must be
  investigated without retaining the real number.

## N-40 — China UOM real-name status/sync as a RID broadcast switch

- Status: `NEGATIVE` for broadcast-switch attribution; the current getter/admission chain is
  `STATIC` (C-131/C-132).
- Positive fact: conditionally loaded `UOMV1` exposes a `0x11/0xD1` status GET and a separate Sync
  action that connects device parameters, China-only DeviceCenter account/server validation, D1
  application of server-derived state, and a device check result. Official cancellation is likewise
  server-mediated before D1 synchronization.
- Result: the surface reports/synchronizes China real-name authentication state. It has no generic
  local setter or offline restore and no evidence of controlling BLE/Wi-Fi Broadcast RID output.
- Does not establish: whether the current Mini 5 Pro runtime inventory admits function ID `0x6C`,
  whether the server accepts the current account/device state, whether the final value is applied or
  persists, or whether authentication influences a separate aircraft policy. Key absence and returned
  `UNSUPPORTED` must remain distinct.

## N-41 — current AirSense tuples as RID controls

- Status: `NEGATIVE` for RID attribution; exact current AirSense ownership is `STATIC` (C-135).
- Positive facts: `0x11/0x0C` is a read/write AirSense traffic-receive switch; inherited
  `0x11/0x37` is an ADSB agent switch with readback but no current RID/DIPS/EID caller; and
  `0x11/0x39` is a set-only synthetic traffic-target test action.
- Result: all three are excluded from the RID configuration catalog. In particular, command
  `0x11/0x37` is unrelated to function-discovery ID `0x37` even though the numbers match.
- Does not establish: that WA150 firmware rejects every raw request or that the inherited agent
  switch has no undocumented live side effect. Those questions require a separate passive trace and
  AirSense-specific experiment; they do not justify a RID toggle.
