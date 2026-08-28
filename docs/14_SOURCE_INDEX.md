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
  Used to inspect community RC 2 loopback frames and issue history. Its success UI was not treated
  as target readback or RF measurement.
- [SkylabFCCfree](https://github.com/danusha2345/SkylabFCCfree/tree/aa024985bf1556ab9c3b12f3d0f2305f63b021f5)
  tag/revision `v1.5.50` / `aa024985bf1556ab9c3b12f3d0f2305f63b021f5`.
  Used for its DUML command audit and profile comparison.
- [DJI-FCC-HACK](https://github.com/M4TH1EU/DJI-FCC-HACK/tree/84f149f58a20cad7f2c0abdebb8bd2d100daa94e)
  at `84f149f58a20cad7f2c0abdebb8bd2d100daa94e`.
  Historical mechanism only; not evidence of the RC 2 + O4 implementation.
- [fpv_live legacy source](https://github.com/ctomichael/fpv_live/tree/4c7bb40e5cc5daec67b39cc093235afb959a4bfe).
  Used for the legacy `DataOsdSetSdrAssitantWrite.setForceFcc()` literal and command semantics.

## Public research baseline

- [FindUAS repository at `15f331c`](https://github.com/Sapphire-Rapids/FindUAS/tree/15f331cf68ce93ae444a8e6aff4c5dc1ed90b5cc).
  Contains the redacted public state, RF, firmware, compatibility, and ADB documents that preceded
  this independent archive.

## Source-handling rule

Public code and documentation provide schemas, names, and precedent. They do not replace exact
current product/version identity, a live route, readback, restoration, or independent RF evidence.
Vendor binaries analyzed locally are listed only by identity in the artifact register and are not
redistributed.
