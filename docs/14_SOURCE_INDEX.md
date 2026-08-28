# Public source index

This index records the public sources and revisions used for corroboration. A repository appearing
here does not imply that all of its claims were accepted.

## DJI and Android primary sources

- [DJI Mobile SDK Android V5](https://github.com/dji-sdk/Mobile-SDK-Android-V5/tree/a48aa4e7811d824c27abfa973f5655579bfb8a77)
  at `a48aa4e7811d824c27abfa973f5655579bfb8a77`.
  Used for public key/value models, Remote ID working-state models, UAS area delegates, FlySafe
  license types/levels, and product-support context. Presence in MSDK does not establish Mini 5 Pro
  support.
- [DJI RC 2 specifications](https://www.dji.com/rc-2/specs?startPoint=0).
  Used for published FCC/CE O4 EIRP ceilings.
- [AOSP ADB](https://android.googlesource.com/platform/packages/modules/adb/).
  Used for packet framing, ordinary CNXN/AUTH behavior, USB class expectations, and permission
  boundaries.
- [AOSP platform frameworks/base](https://android.googlesource.com/platform/frameworks/base/).
  Used for Android `attach-agent`, Settings intents, and permission behavior.

## Reverse-source snapshots and protocol prior art

- [SKYROVER_src](https://github.com/MAVProxyUser/SKYROVER_src/tree/8186e19241c913318b140bf37c5eafba005f1e7c)
  at `8186e19241c913318b140bf37c5eafba005f1e7c`.
  Used for area-code strategy, Airlink/FC synchronization, legacy key models, cloud-control writers,
  and generated mappings. It is prior/static source, not a live RC 2 binary identity.
- [DJI-Link](https://github.com/Kolya080808/DJI-Link/tree/13b357f405149674a33e3285780885728f52cafe)
  at `13b357f405149674a33e3285780885728f52cafe`.
  Used to corroborate DUML/hash-command families and RID-status command naming. Documentation/runtime
  parser differences were treated as unresolved until current native evidence closed a layout.
- [dji-firmware-tools](https://github.com/o-gs/dji-firmware-tools/tree/195692263c2684cf1ddc4995f2736be6c0fb135e)
  at `195692263c2684cf1ddc4995f2736be6c0fb135e`.
  Used for DUML dissector behavior and IMaH container tooling/field interpretation. Tool support is
  not target-key availability or signature bypass.
- [N3Live](https://github.com/brendan779/N3Live/tree/bb254b0d0b1f5ac79462e9fe3ea986fc91adeec0)
  at `bb254b0d0b1f5ac79462e9fe3ea986fc91adeec0`.
  Used for Goggles N3 USB/DUML framing corroboration and a generated command-name corpus. It does not
  implement the RC 2 localhost or Mini 5 Pro RID route.
- [DJI-RC-Emulator](https://github.com/o-gs/DJI-RC-Emulator).
  Used only for historical DJI transport context where explicitly cited.

## RC 2 community work

- [whitelewi1-ctrl/dji-rc2-research](https://github.com/whitelewi1-ctrl/dji-rc2-research/tree/fc5949acfe8196e2faccf96615821b62fbe60804)
  at `fc5949acfe8196e2faccf96615821b62fbe60804`.
  Used for public RC 2 firmware/Android precedent and comparison. No complete current RID control
  chain was adopted from it.
- [Dr-Muh/dji-adb](https://github.com/Dr-Muh/dji-adb/tree/027c7815568c89e55fff22bfeede9dd294404660)
  at `027c7815568c89e55fff22bfeede9dd294404660`.
  Its pre-authentication packet profile was reproduced. The live device did not reach AUTH TOKEN.
- [ya-webadb](https://github.com/yume-chan/ya-webadb/tree/340d3fe0f0f6a44830ac41965106a2aea41bc484)
  at `340d3fe0f0f6a44830ac41965106a2aea41bc484`.
  Used to compare split header/payload USB framing and direct-public-key-after-token behavior.
- [dji-neo2-tools](https://github.com/linnin233/dji-neo2-tools/tree/f0b715ad5f064c25439e389cb892befa7c2e3cff)
  at `f0b715ad5f064c25439e389cb892befa7c2e3cff`.
  Used only for public extraction/runtime precedent; product/version transfer was not assumed.

## Community FCC/regulatory tools

- [FreeFCC](https://github.com/doesthings/FreeFCC/tree/597157bd52120dfeb9677f79a8ad46b6027ce8dc)
  at `597157bd52120dfeb9677f79a8ad46b6027ce8dc`.
  Used to inspect community RC 2 loopback frames and issue history. Seven exact profile files also
  match the NLD `2.0.0.6` APK, but no NLD runtime reference to those assets was found. FreeFCC is
  AGPL-3.0; its success UI was not treated as target readback or RF measurement.
- [FreeFCC releases](https://github.com/doesthings/FreeFCC/releases).
  Used for public timing, keepalive, compatibility, update-validation, and write-completion claims;
  release text is project history rather than independent RF or minimal-command evidence.
- [FreeFCC protocol-provenance issue](https://github.com/doesthings/FreeFCC/issues/30).
  Used to preserve the unresolved minimal-causality boundary around the multi-frame profile and
  keepalive.
- [SkylabFCCfree](https://github.com/danusha2345/SkylabFCCfree/tree/aa024985bf1556ab9c3b12f3d0f2305f63b021f5)
  tag/revision `v1.5.50` / `aa024985bf1556ab9c3b12f3d0f2305f63b021f5`.
  Used for its DUML command audit and profile comparison.
- [DJI-FCC-HACK](https://github.com/M4TH1EU/DJI-FCC-HACK/tree/84f149f58a20cad7f2c0abdebb8bd2d100daa94e)
  at `84f149f58a20cad7f2c0abdebb8bd2d100daa94e`.
  Historical mechanism only; not evidence of the RC 2 + O4 implementation.
- [fpv_live legacy source](https://github.com/ctomichael/fpv_live/tree/4c7bb40e5cc5daec67b39cc093235afb959a4bfe).
  Used for the legacy `DataOsdSetSdrAssitantWrite.setForceFcc()` literal and command semantics.

## NLD public product and release material

- [NLD FCC Smart RC product page](https://nolimitdronez.com/nld-fcc-android-smart-rc-license).
  Used only for current vendor claims, compatibility lists, and license scope.
- [NLD FCC 2.0.0.6 release article](https://nolimitdronez.com/nld-fcc-2006-the-remake).
  Used for the vendor's dated rewrite, C0, offline, FCC/4G, editor, macro, and trial claims.
- [NLD downloads page](https://nolimitdronez.com/download).
  Used to record the public Smart RC download and its displayed `2.0.0.1` version mismatch with the
  downloaded `2.0.0.6` manifest.
- [NLD generic Android catalogue page](https://nolimitdronez.com/nldfcc-for-android?orderby=11).
  Used only to record the vendor's generic Remote ID transmission-disable claim. The exact Smart RC
  `2.0.0.6` static sample did not expose a corresponding control.

## Drone-Hacks public release, support, and compatibility material

- [Drone-Hacks current release metadata](https://releases.drone-hacks.com/latest.json).
  Used to identify the official `2.0.29` Windows archive and publication date. The notes/version
  mismatch is retained as metadata, not interpreted as binary identity.
- [Drone-Hacks Windows release notes](https://wiki.drone-hacks.com/en/windows_release_notes).
  Used to corroborate the `2.0.29` release and its public RM700 change.
- [Custom Flight Controller commands](https://wiki.drone-hacks.com/en/dh2-cfc-commands).
  Used for the firmware-resident CFC architecture, Name-field command transport, command list, and
  explicitly listed supported models. No RID command or Mini 5 Pro entry was present.
- [Known issues](https://wiki.drone-hacks.com/en/dh2-known-issues).
  Used for the documented multi-step FCC-to-CE restoration boundary.
- [Custom-firmware release notes](https://wiki.drone-hacks.com/en/drone-hacks-v2/extras/fcfw-release-notes).
  Used only for public custom-firmware version context.
- [Ownership transfer notice](https://wiki.drone-hacks.com/new-era-for-DH).
  Used to corroborate the Skymod Technologies Ltd operator identity shown by Authenticode.
- [Public model definitions](https://drone-hacks.com/api/v1/definitions/models),
  [public model-catalogue application chunk](https://drone-hacks.com/_app/immutable/chunks/CXG_u84T.js),
  [compatible-license definitions](https://drone-hacks.com/api/v1/definitions/compatible-licenses),
  [Mini 5 Pro product search](https://drone-hacks.com/api/v1/products/search?model=wa150),
  [Mini 3 Pro product-search positive control](https://drone-hacks.com/api/v1/products/search?model=wm162), and
  [FCC ModBox compatibility](https://drone-hacks.com/api/v1/configs/fccModBoxCompatibility).
  Anonymous snapshot on 2026-08-28. Used to separate model recognition, software product/license,
  software platform, and FCC-hardware compatibility. No account or device identifier was supplied.
- [Remote-controller compatibility boundary](https://wiki.drone-hacks.com/en/compatible-rc-dji-fly).
  Used to distinguish an official controller remaining compatible with a modified aircraft from
  direct modification support for that controller.

## WA150 public identity, security, and RF-test material

- [Mini 5 Pro 0600-era original photo](https://commons.wikimedia.org/wiki/File:Dji_fly_20260805_075506_0062_1785909768062_photo.jpg).
  Original-file SHA-256 `378089ae600522fb9fc0ab6d9db75d7807ab72ddf6cec8843dee22975f742c6e`;
  used only for the `FC9313` / `10.00.12.83` product-software match. Coordinates and unrelated
  metadata were neither copied nor retained in this repository.
- [Mini 5 Pro 0700-era original photo](https://commons.wikimedia.org/wiki/File:Vue_a%C3%A9rienne_de_Long_(Somme)_2.jpg).
  Original-file SHA-256 `269d2fefcb8b104659e6244c058a83ef56569c00eac7f600c72173386be5f17f`;
  used only for the `FC9313` / `10.00.15.17` product-software match, under the same privacy boundary.
- [NVD CVE-2026-77812](https://nvd.nist.gov/vuln/detail/CVE-2026-77812) and
  [GitHub Advisory CVE-2026-78306](https://github.com/advisories/ghsa-vq46-xr65-w8q7).
  Used to identify the publicly described Mini 5 Pro `<=01.00.0600` BLE DUML and Wi-Fi/network
  configuration surfaces and firmware-update remediation. They do not expose the 0700 file diff or
  a RID control.
- FCC ID `SS3-MT5MFND25` reports:
  [BLE](https://fccid.io/SS3-MT5MFND25/Test-Report/Test-Report-BLE-8307076.pdf),
  [RLAN](https://fccid.io/SS3-MT5MFND25/Test-Report/Test-Report-RLAN-8307219.pdf), and
  [Wi-Fi](https://fccid.io/SS3-MT5MFND25/Test-Report/Test-Report-WiFi-1-8307077.pdf).
  Used only for the laboratory USB-C/`DjiSdrConsole-v2.2.8` test setup and RF-chain description.
  The reports do not publish the tool/protocol or mention Remote ID.

## Legacy proprietary DroneID research

- Schiller et al., [Drone Security and the Mysterious Case of DJI's DroneID](https://www.ndss-symposium.org/wp-content/uploads/2023/02/ndss2023_f217_paper.pdf),
  NDSS 2023, DOI `10.14722/ndss.2023.24217`.
  Used for the proprietary OcuSync DroneID packet model, tested legacy products/firmware, and the
  observed `fake`-field behavior. The paper did not publish the control's tuple or payload.
- [RUB-SysSec/DroneSecurity](https://github.com/RUB-SysSec/DroneSecurity/tree/9ff819843bee48fb140a0704ec78aff757896dea)
  and [DroneSecurity-Fuzzer](https://github.com/RUB-SysSec/DroneSecurity-Fuzzer/tree/1410df748b9aecd0cb81ec15282bc570c595eb26).
  Used as pinned author artifacts; the fuzzer source remains absent from its public repository.
- Pinned DJI-derived
  [DataFlycDetection](https://github.com/MAVProxyUser/SKYROVER_src/blob/8186e19241c913318b140bf37c5eafba005f1e7c/uav/midware/data/model/P3/DataFlycDetection.java)
  and [CmdIdFlyc](https://github.com/MAVProxyUser/SKYROVER_src/blob/8186e19241c913318b140bf37c5eafba005f1e7c/uav/midware/data/config/P3/CmdIdFlyc.java).
  Used to reconstruct the high-confidence `0x03/0xDA`, subcommand `0x05`/`0x06`, eight-field-mask
  correspondence. This reconstruction is not an author-disclosed command or WA150 support proof.

## Synthetic standards-based source references

- [OpenDroneID Core C](https://github.com/opendroneid/opendroneid-core-c).
  Used for the standards-oriented Basic ID, Location/Vector, Authentication, Self ID, System,
  Operator ID, and Message Pack data-model boundary. The library is not a DJI control API.
- [OpenDroneID Linux transmitter](https://github.com/opendroneid/transmitter-linux).
  Used as public precedent for a separate controlled Bluetooth/Wi-Fi laboratory source. It does not
  imply that macOS or the attached DJI aircraft can transmit those messages through the same API.

## Public research baseline

- [FindUAS repository at `15f331c`](https://github.com/Sapphire-Rapids/FindUAS/tree/15f331cf68ce93ae444a8e6aff4c5dc1ed90b5cc).
  Contains the redacted public state, RF, firmware, compatibility, and ADB documents that preceded
  this independent archive.

## Source-handling rule

Public code and documentation provide schemas, names, and precedent. They do not replace exact
current product/version identity, a live route, readback, restoration, or independent RF evidence.
Vendor binaries analyzed locally are listed only by identity in the artifact register and are not
redistributed.
