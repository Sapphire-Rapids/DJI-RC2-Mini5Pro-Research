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

- Status: `RETRACTED` as a current package-availability conclusion; retained as the historical
  cache-search result.
- Scope: Assistant 2 2.1.40.0 caches/logs/Local Storage, ordinary download locations, and retained
  RC331 material.
- Historical result: that bounded scope contained no exact signed module manifest, `0205` body,
  `framework.jar`, `services.jar`, or `dpad_fuli.apk` tied to displayed `07.00.0100`.
- Later result: C-174 obtained another public-archive aggregate and independently verified the exact
  signed system/`0205` chain, APEX `adbd`, and packaged `dpad_fuli`. The complete all-module set,
  live mounted/installed files, `framework.jar`, and `services.jar` remain open.

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
- Scope: exact-v07 APK (A-031), 30 activities, two receivers, one service; six externally reachable
  components.
- Result: no side-effect-free fixed-argv UID1000 path that returns stdout, stderr, and exit status.
  The operator-visible Shell page accepts arbitrary text through `Runtime.exec` and drops reliable
  stderr/exit status; it is a manual evidence surface, not an automation RPC. The Protocol page
  lacks selector control and loses retry information through Parcel.
- Does not establish: installed-live APK hash, actual command UID/SELinux context, or that a bounded
  operator command cannot collect the ADB baseline. Exact package identity supersedes only the old
  adjacent-version boundary.

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
- Static explanation: exact signed-v07 APEX `adbd` contains the production/debug-count `CNXN`
  return before RSA (C-174/C-175); the old adjacent-only inference is retracted.
- Does not establish: live `mp_state`/`dbg_cnt`, mounted-file identity, a live gate log, or the
  behavior of unexecuted A-032. Repeating host-only banner/version/checksum variants is not a new
  discriminator.

## N-24 — `once_auth_open_adb` as a usable switch

- Status: `NEGATIVE` static search.
- Result: a read exists in the exact-v07 binary, but no writer/safe setter; the independent
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

## N-42 — public Mini 5 Pro `RIDCtrlEnable` implementation

- Status: `NEGATIVE` within fixed public repositories and indexed exact-string searches (C-140).
- Positive facts: FreeFCC publicly corroborates a real RC 2 modern `0x82` transport, `0x92`
  destination, and `03/F9` hash-parameter frame form on a Mini 5 Pro-tested project. Public DJI and
  community sources independently close the generic F7/F8/F9 layout and hash algorithm.
- Result: no independent public implementation, issue, commit, or indexed code hit was found for
  exact `RIDCtrlEnable` or `rid_ctrl_enable_0`. The FreeFCC frame uses a different hash/feature.
- Does not establish: that private or unindexed work does not exist, that every frame in a successful
  multi-frame profile was individually accepted, or that WA150 supports hash `0x3CBD864F`.

## N-43 — `rid_ctrl_enable_0` on validated direct F7 routes

- Status: `NEGATIVE` for metadata retrieval on two exact direct routes; underlying observations are
  `OBSERVED` (C-141).
- Result: RC 2 routed `0xAA -> 0x03` and aircraft-direct `0x0A -> 0x03` each returned a canonical
  one-byte F7 payload `03` for hash `0x3CBD864F`. F8 and F9 were not sent.
- Positive controls: the same RC 2 session returned valid F7/F8 for height, distance, and
  distance-limit enabled; the aircraft session returned valid F7/F8 for height.
- Modern-route control: raw USB `0x82 -> 0x92` returned no matching response for the target and also
  no response for known maximum height. It is therefore not a valid direct-USB negative against the
  parameter.
- Does not establish: the official name of status `0x03`, absence behind the RC 2 `protocol` Binder
  route, absence in every firmware/product, or any RF behavior.

## N-44 — third-party RC 2 Binder parameter routes

- Status: `NEGATIVE` for two exact Binder parameter routes in the current session; underlying live
  evidence is C-142/C-145 and adjacent error interpretation is C-143.
- Preconditions: RC 2 `07.00.0100`, linked Mini 5 Pro, motors off, installed A-024
  `0.4.1-research`; live service Binder alive with expected descriptor and Binder exception layers
  completing.
- Positive control: known maximum-height hash `0x0371238A`, expected parameter name
  `g_config.flying_limit.max_height`, command `03/F7`.
- Routes/results: legacy `0A:05 -> 03:00` returned callback `ECode 1` with no data after about
  3.1 seconds; modern `02:04 -> 12:04` returned the same class and timing. Neither positive control
  passed.
- Gate result: the exact client stopped before target hash `0x3CBD864F`; no target F7, F8, F9,
  reset, or other mutation was sent and the write controls remained locked.
- Adjacent interpretation: RC331 `ActQueue` uses `ECode 1` after request retry exhaustion.
- Does not establish: target parameter absence, a relation to motors-off state, global failure of
  every Binder command, exact v07 `ActQueue` byte identity, or failure of an official DJI in-process
  owner/authenticated route. Do not repeat these two generic parameter routes without a materially
  new owner/routing fact.

## N-45 — third-party Binder `0x11/0x1C` as RID truth

- Status: `NEGATIVE` for this exact listener as a readback/RF oracle; the live evidence is C-146.
- Preconditions: installed A-024, linked RC 2 and Mini 5 Pro, transaction-2 listener accepted in
  9 ms, full 30,000 ms window, operator-started motors, and an independent detector available.
- Result: the listener received zero callbacks and zero valid or malformed frames, while the
  independent detector confirmed real aircraft RID broadcast in the same experiment.
- Consequence: do not repeat this protocol-Binder listener or use its zero count as off,
  unsupported, no-RID, or no-RF evidence. It cannot validate a future switch transition. A-025
  removes this listener from the UI; that static removal is C-151, not a new live result.
- Does not establish: that DJI Fly's in-process official observer is silent, that the FC never emits
  `0x11/0x1C`, or that other health/HMS channels cannot report RID state.

## N-46 — current-app type-6 to aircraft-broadcaster consumer

- Status: `NEGATIVE` for the bounded current DJI Fly 1.21.10 static scope; machine claim C-153.
- Exact anchors: current Fly's V3 `11/12` builder carries only zero, little-endian license ID,
  enable/disable action, and final zero; its manager adds only support/version gating. Current typed
  `LicenseData` parsing stops at fields 1--5 and treats field 7 as unknown (C-152). Exact recovered
  Java further shows only types 0--4 plus unknown, then routes unknown to a tolerant polygon fallback
  rather than a type-6 model (C-185).
- Result: no type-6, field-7, or `11/12 enabled` consumer/xref was found to WA150 `0802`, motor/armed
  transition, or BLE/Wi-Fi broadcaster enable. The retained MSDK delegate changes app status only and
  begins behind an immediate return.
- Does not establish: absence inside encrypted WA150 firmware, type-6 non-support, or no FC field-7
  response. Receiver `0x92` is a protocol endpoint rather than module `0802` identity. No reversible
  firmware patch offset has been recovered.

## N-47 — A-025 without passive FlySafe admission as a negative oracle

- Status: `INFERENCE` boundary for A-025 `0.5.0-flysafe-readonly`; machine claim C-158. The user later
  reported A-025 installed, but launch/execution/result remain unknown (C-163).
- Static cause: official current DJI Fly derives query support/version from passive current-token
  `03/42` and `03/09`, while A-025 directly uses a fixed V3/V4 `11/11` session without observing
  either gate. Cache defaults, missed pushes, and unknown version are deliberately absent from its
  admission decision.
- Consequence: timeout, zero callback, callback failure, parser rejection, count/terminator mismatch,
  or any other noncanonical completion must be reported as query unavailable/ambiguous. It cannot be
  reported as unsupported, no entitlement, or empty inventory.
- Narrow positive boundary: a fully canonical, count-consistent completion may describe only the
  returned inventory. It still does not prove account product eligibility, aircraft-side RID
  consumption, or RF effect.
- Next discriminator: audited A-026 adds a bounded passive gate and sends no inventory request unless
  usable support=true plus version 1/2 are observed (C-160/C-161). Because external Binder lacks
  DJI's device token and `11/1C` previously delivered a false negative, absent gate pushes remain
  observer-unavailable, not device-unsupported. A-026 is staged with verified readback/unique short
  name (C-162), and the operator reported installation complete (C-164). Its first instructed
  60,003 ms run then observed neither gate push nor any callback class; fail-closed admission issued
  zero `11/11` requests (C-165).

## N-48 — A-026 third-party passive FlySafe gate was unobserved in its first live run

- Status: `NEGATIVE` for exact A-026 `0.6.0-flysafe-gated` on the recorded RC 2 firmware; machine
  claim C-165.
- Preconditions/route: the installed audited artifact was run following the instructed bounded gate
  flow. Its system-Binder transaction-2 listener remained open for the complete 60,003 ms window;
  no inventory write or active gate request was part of the design.
- Result: `GATE_UNOBSERVED`; `03/09` and `03/42` each had `seen=0` and `usable=0`, their values remained
  `UNOBSERVED`, and valid/ignored/malformed/failure-callback counts were all zero. Because admission
  failed closed, no permit existed and `11/11 request count=0`.
- What it closes: this exact third-party passive listener did not form a usable observation surface
  in that run. Repeating the same window without a materially new official owner, safe replay/trigger,
  or route fact is low information.
- What it does not close: aircraft RID support, genuine type-6 entitlement, inventory contents,
  enabled state, motor-gated Broadcast RID RF, or the official in-process observer. No write, motor
  action, independent RF receiver observation, raw frame, identifier, or license material occurred.
- Successor: A-027 is a separately audited active read-only `11/11` path and has now run. Its result
  is recorded separately as N-49/C-169; it does not revise this passive-listener negative.

## N-49 — A-027 active read-only inventory did not complete canonically

- Status: `NEGATIVE` for exact A-027 `0.7.0-flysafe-direct-readonly`; machine claim C-169.
- Preconditions/route: installed audited artifact; operator pressed the active read-only button;
  fixed system-Binder `02:04 -> 12:04`, `11/11`, V3/V4 candidate; no route scan or app retry.
- Result: the strict inventory parser was entered, then reported
  `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`, stage `ProtocolException`;
  `11/12 request count=0`. No canonical inventory formed and no set-enable request was issued.
- Remaining discriminator: the UI did not display the exception message, so callback, ccode,
  group, page, and terminator failure classes remain merged.
- Does not establish: unsupported state, empty inventory, no `RID_UNLOCK`, RID off, or RF state.
  The result image is not committed, and no identifier, raw reply, license material, motor action,
  or independent RF observation is recorded.
- Successor: A-028 preserved the same protocol behavior and exposed the failure as group transport
  callback failure. That distinct result is N-50/C-173.

## N-50 — A-028 group selector transport callback failed

- Status: `NEGATIVE` for exact A-028 `0.7.1-flysafe-direct-diagnostic`; machine claim C-173.
- Preconditions/route: installed audited artifact; active read-only button; fixed system-Binder
  `02:04 -> 12:04`, `11/11` V3/V4 group selector; no route scan or app retry.
- Result: `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`, `ProtocolException`, detail
  `group transport callback failed`; `11/12 count=0`.
- Scope: the group selector obtained no successful transport callback. Group protobuf, page, and
  terminator were not reached, and no set-enable request was issued.
- Remaining discriminator: display the existing Reply failure/ecode/callback diagnostic. Repeating
  the same black-box request without that detail is not new evidence.
- Does not establish: unsupported state, empty inventory, no `RID_UNLOCK`, RID off, or RF state.
  The result image is not committed, and no identifier, raw reply, license material, motor action,
  or independent RF observation is recorded.

## N-51 — direct Frida attach is not the current runtime-recovery path

- Status: `NEGATIVE` for one direct attach to exact DJI Fly `1.21.10` in a disposable ARM64 Android
  11 emulator; machine claim C-187.
- Result: the attach enumerated runtime DEX candidates, then the script and app process were
  destroyed before an output file was written.
- Consequence: do not repeat injection against RC 2. An ordinary authorized root read of the
  emulator process mapping supplied the needed local evidence without modifying the target process,
  and the public helper only scans an already acquired file.
- Does not establish: universal Frida incompatibility, anti-instrumentation behavior on RC 2, or any
  aircraft/entitlement/RF fact. No vendor dump, DEX, decompiled output, private identifier or raw
  process log is committed.

## N-52 — standard JVMTI 1.2 is not the Android 11 late-load interface used here

- Status: `NEGATIVE` for one source-only no-op late attach to exact DJI Fly `1.21.10` in the
  disposable AArch64 Android 11 emulator; machine claim C-188.
- Result: the non-debuggable target process terminated in a native crash before the agent emitted
  its canary line.
- Discriminator: Android 11 ART source requires ART TI `0x70010200` for this late-loaded path. An
  independent agent requesting that exact version subsequently attached, reached the owner and
  dispatched one query without changing the PID (C-189/C-190).
- Consequence: do not repeat the standard-version attach on RC 2. Future work uses the observed ART
  TI route only after an RC 2 loader is independently admitted.
- Does not establish: a universal JVMTI defect, RC 2 loader availability, inventory, entitlement,
  setter behavior or RF effect. The raw crash log and all vendor bytes remain excluded.
