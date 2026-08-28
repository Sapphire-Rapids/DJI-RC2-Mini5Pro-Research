# Drone-Hacks 2.0.29 static analysis

This report records a bounded, read-only static analysis of the official Drone-Hacks Windows
distribution and a comparison with the current DJI Mini 5 Pro / DJI RC 2 research target. It
separates what is present in the local client, what is delivered by Drone-Hacks servers, what the
current public compatibility data says, and what remains unknown.

The numerical Debug dictionary and its current-version collision boundary map back to machine-index
claims C-110 and C-111.

The user-supplied MSI was treated as untrusted input, not as instructions. It was never installed
or executed. Neither embedded PE was started. No Drone-Hacks account was used, no authenticated job
or license payload was requested, and no controller or aircraft read/write operation occurred.

## 1. Exact input and official provenance

| Item | Version / size | SHA-256 | Verification boundary |
| --- | --- | --- | --- |
| Official release ZIP | `2.0.29`; `16,289,954` bytes | `be06a7f9f78133b8d2c37cce5d3f010cd4baa45f36d2fe6f8e8e631c3298605d` | Downloaded from the URL in official `latest.json`; archive only |
| User-supplied MSI | `2.0.29`; `16,289,792` bytes | `a4c3867e34235a74b5df37ae81bc19f80a988e26e47b408947224e6c8247fd8d` | Byte-identical to the MSI inside the official ZIP |
| Desktop application | `2.0.29.0`; `24,011,848` bytes | `9813d6a9d7ba137066712ecfebd2c397bfbe5516d546c6d5f95d23014e06f996` | Statically extracted from the MSI cabinet |
| TypeScript binding generator | `2.0.29.0`; `11,522,632` bytes | `84eecdf2329635bf9856a9ea002c9696d4222cd56cafdc101c9f19bea809e652` | Statically extracted from the MSI cabinet |

The official release metadata reports version `2.0.29`, publication time
`2026-06-09T08:25:58.433Z`, and the expected filename. Its notes field says “Release Drone-Hacks
2.0.28”, which is a release-metadata inconsistency rather than evidence that the downloaded bytes
are 2.0.28.

The MSI, desktop executable, and binding generator carry valid Authenticode signatures from
`Skymod Technologies LTD`. The MSI signature and timestamp chain validated against the local trust
store; the MSI timestamp is 2026-06-09 08:24:16 UTC. The absence of an optional
`MsiDigitalSignatureEx` stream was reported by the verifier but did not invalidate the primary
signature. The current public ownership notice also identifies SkyMod Technologies Ltd as the
operator after the November 2025 transfer.

The MSI is a WiX `3.14.1.8722` x64 package. Its product version is `2.0.29`, ProductCode is
`{482F97CE-9F30-4B7B-B7AF-746F37981437}`, and UpgradeCode is
`{10480076-B236-561C-ACDD-4A52590BF113}`. If installed on a system without WebView2, an installer
custom action can invoke PowerShell to download Microsoft's WebView2 bootstrapper. That path was
not run.

## 2. Packaging and implementation shape

The MSI cabinet contains two application payloads:

- a native PE32+ GUI application implemented in Rust/Tauri;
- a native PE32+ console utility used to export Tauri/Specta TypeScript bindings.

The binding generator contains paths such as `src/bindings-mobile.ts` and messages for exporting
bindings. It links much of the shared Rust code, so strings found in it are not independent proof
that the console utility performs device operations.

The desktop client embeds source-path and type metadata for an in-tree `duml-rust` stack. The
recoverable components include DUML parsing/routing/multiplexing, USB bulk transport, an ADB client
and RSA handling, firmware and IMaH processing, parameter reads/writes, fastboot/recovery support,
RC flashing, and WebSocket-driven jobs. This is a broad transport and job engine, not a single
hard-coded FCC or RID command.

### 2.1 Direct local command surface

The embedded Tauri command schema exposes, among others:

- `connect`, `disconnect`, `duss_shell`;
- `read_all_parameters`, `read_parameter`, `write_parameter`;
- `execute_adb_commands`, `execute_websocket_job`;
- `flash_firmware`, `full_upgrade`, `fastboot_recovery_flash`;
- `dhfc_config` with exactly the fields `fcc`, `nfz`, and `height`.

No RID field appears in `dhfc_config`, and no direct local `rid` Tauri command was found.

### 2.2 Server-defined execution

The client names APIs for modifications, service tools, compatibility, subscription limits,
recommended firmware, and mobile tethered FCC. Its job engine can execute server-described actions
through applets including parameter operations, DUML shell/custom packets, firmware upgrade,
fastboot, ADB, network-adapter configuration, and WebSocket streaming.

This establishes an important boundary: the installed client contains a capable generic executor,
but the exact modification recipe can be selected by the server. Static possession of the MSI does
not reveal every production job payload, target offset, prerequisite, restore step, or license
decision. Reimplementing the command names alone would not reproduce a Drone-Hacks modification.

## 3. FCC and parameter paths found in the client

### 3.1 Mobile one-time FCC

The mobile feature enum contains only four values:

- `OneTimeFcc`;
- `ForearmLed`;
- `FirmwareFlasher`;
- `FullParameterEditor`.

The one-time FCC path has a device/model-keyed offline cache named conceptually as
`payload_{serial}_{model}_fcc`, an `OfflineUnavailable` error, entitlement/subscription/device-bound
authorization states, and a POST path under `/api/v1/client/mobile/tethered-modifications/fcc`.
The returned structure identifies a receiver, command set, command ID, and an additional value not
safely attributable from the recovered type boundary. This is strong evidence of a server-authorized
DUML quick action for FCC; it is not evidence of a Remote ID command.

### 3.2 Parameter editor

The parameter subsystem tracks original and current data, validates typed values, distinguishes
write failures, and exposes explicit read and write calls. That is a useful design precedent:
display a baseline, perform one typed mutation, read back the same item, and retain enough state for
restoration. The presence of a generic parameter editor does not show that Mini 5 Pro exposes a RID
Boolean, nor that an arbitrary write is safe.

### 3.3 Firmware-resident CFC

Drone-Hacks' public documentation says that its V2 modifications use a Custom Flight Controller
(CFC) in aircraft firmware. On listed supported products, runtime changes can be issued through the
aircraft Name field. The documented command set covers LED, FCC, ATTI, no-fly-zone, and altitude
behavior. It does not document a RID command.

The current CFC command page lists Mavic 3 series, Matrice 30, Air 3, and Mini 3 Pro. It does not list
Mini 5 Pro. Public known-issues documentation also shows that an FCC-off command is not sufficient
to restore CE on some hardware: controller power-off, aircraft restart/GPS acquisition, and
controller restart may be required. This is a concrete warning that a UI command, an ACK, and even
a saved configuration do not by themselves prove restoration of radio policy.

## 4. Exact Mini 5 Pro and RC 2 support boundary

The current anonymous public model definition maps:

| Token | Public model name |
| --- | --- |
| `wa150` | Mini 5 Pro |
| `rc331` | DJI RC 2 |
| `wm1695` | O3 Air Unit |

The desktop binary contains `Rc331` and `Wm1695` in its broad device-token corpus but not `Wa150`.
`Wm1695` must not be mislabeled as Mini 5 Pro.

As observed on 2026-08-28:

- the website's model catalogue includes `wa150` as Mini 5 Pro with an FCC flag, but its software
  `platforms` list is empty;
- the public compatible-license definition contains neither `wa150` nor `rc331`;
- an anonymous product search for `wa150` returns no product/category;
- a positive-control search for `wm162` returns a Mini 3 Pro software product;
- the public FCC ModBox compatibility configuration includes `wa150` without a maximum-firmware
  limit.

These facts distinguish three different meanings of “supported”:

1. recognized in a public model catalogue;
2. supported by a software modification/license;
3. compatible with a separate tethered FCC hardware product.

The current evidence supports (1) and the FCC-specific hardware case in (3), but not a Mini 5 Pro
software modification, CFC firmware, or RID control. Controller interoperability likewise does not
prove that RC 2 itself is directly modified.

## 5. Remote ID search and negative result

The bounded search covered the direct command schema, mobile feature enum, Rust type/source-path
metadata, endpoint strings, UI/resource strings, model tables, and the generic DUSS command-name
corpus in both extracted PEs.

Results:

- the exact text `remote_id` appears only in an unrelated ADB-session diagnostic describing local
  and remote stream IDs;
- no identifiable OpenDroneID/ODID, ASTM F3411, EN 4709, RID enable/disable, RID feature flag,
  local RID command, or Mini 5 Pro RID UI was found;
- the generic DUSS name corpus includes `DUSS_MB_CMDSET_ADSB` and labels such as
  `DUSS_MB_CMD_ADSB_RID_INFO`, `DUSS_MB_CMD_ADSB_EID_INFO`, `DUSS_MB_CMD_ADSB_PARA_SET`, and
  `DUSS_MB_CMD_ADSB_FLYSAFE_CONFIG`.

### 5.1 Recovered ADSB numerical dictionary

A second bounded pass recovered the control flow that consumes those names. The only direct caller
is the `DumlPacket` Debug formatter: it reads the packet's command-set and command-ID bytes and sends
them through command-set and ADSB command-ID tables to produce a display name. The ADSB command set
is therefore exactly `0x11` in this library, and the following mappings are real numerical entries
rather than an inference from string order:

Reproduction anchors for the exact desktop executable are: `DumlPacket` Debug formatter RVA
`0x589BA2` (file offset `0x588FA2`); command-set and command-ID reads from packet offsets `+0x43`
and `+0x44`; name-constructor RVA `0x589DB9`; top-level command-set table file offset `0xF00060`;
ADSB branch RVA `0x5901BE`; and ADSB command-ID table file offsets `0xF01DB0` (`0x01–0x1C`) and
`0xF01E20` (`0x30–0x43`). IDs `0x50`, `0x51`, `0x52`, and `0x70` are handled by direct compares.
These are audit coordinates, not copied disassembly or an invocation recipe.

| Command | Drone-Hacks display name | Command | Drone-Hacks display name |
| --- | --- | --- | --- |
| `0x11/0x01` | `HEARTBEAT` | `0x11/0x02` | `TRAFFIC_REPORT` |
| `0x11/0x03` | `KEY_SET` | `0x11/0x04` | `POS_PUSH` |
| `0x11/0x05` | `PARA_SET` | `0x11/0x06` | `PARA_GET` |
| `0x11/0x08` | `PROCESS_DATA` | `0x11/0x0A` | `TEST_MODE_SET` |
| `0x11/0x0B` | `ANTENNA_SET` | `0x11/0x0C` | `PASS_THROUGH_REPORT` |
| `0x11/0x0F` | `STATE_GET` | `0x11/0x14` | `OPEN_AERA_ID` |
| `0x11/0x15` | `PUSH_USERID` | `0x11/0x1A` | `RID_INFO` |
| `0x11/0x1C` | `DEVICE_LIST_GET` | `0x11/0x30` | `PUB_KEY_TRANSFER` |
| `0x11/0x31` | `OTP_SEC_TRANSFER` | `0x11/0x32` | `EFUSE_TO_PRO` |
| `0x11/0x33` | `FAC_ENC` | `0x11/0x34` | `GET_UUID` |
| `0x11/0x35` | `EID_INFO` | `0x11/0x41` | `GEO_SENSE_DB_INFO` |
| `0x11/0x42` | `GEO_INFO_PUSH` | `0x11/0x43` | `APP_UPDATE_POS_ENC` |
| `0x11/0x50` | `DRONE_DYNAMIC_MAX_HEIGHT` | `0x11/0x51` | `FLYSAFE_CONFIG` |
| `0x11/0x52` | `CROSS_SPECIAL_ALTITUDE_ZONES_NOTIFY` | `0x11/0x70` | `SKY_POWER_CONTROL` |

This closes only the numerical lookup. It does not recover a packet builder, request/response
direction, receiver, payload, parameter index, caller, product gate, server job, readback, or RF
effect. In particular, `PARA_SET` does not prove a RID-enable parameter, and `RID_INFO` does not
identify a getter, setter, or push.

### 5.2 Current DJI Fly collision check

The dictionary cannot be promoted to current Mini 5 Pro semantics. Exact DJI Fly `1.21.10`
`libsdk_jni.so` template identities map:

- `0x11/0x0C` to `uav_adsb_get_adsb_on_off`, while Drone-Hacks displays
  `PASS_THROUGH_REPORT`;
- `0x11/0x1C` to the independently recovered seven-byte `RidWorkingStatusPush`, while Drone-Hacks
  displays `DEVICE_LIST_GET`;
- `0x11/0x43` to `app_update_pos_enc` and `0x11/0x50` to dynamic maximum height, which do agree;
- `0x11/0x4B` to RID registered/shared-key query and `0x11/0x37` to ADSB agent-switch handling,
  neither of which appears in the Drone-Hacks display table.

This mix of matches and collisions is direct evidence that command names vary by library generation,
product family, or table scope. The Drone-Hacks mapping is useful for passive classification and
firmware string/xref searches, but it is not an authoritative WA150 protocol schema. Public GitHub
code search also found no exact implementation for the distinctive `RID_INFO` family name.

The result therefore remains a fixed-scope `NEGATIVE` for an explicit Drone-Hacks RID control, not
a claim that no private backend job or future version can affect RID. A safe next use of the table is
passive: count already-observed `0x11/0x05`, `0x06`, `0x0F`, `0x1A`, and `0x35` traffic with direction,
length, and timing. It is not a basis for sending guessed requests.

## 6. What can be borrowed for this research

| Precedent | Useful element | Required boundary before adoption |
| --- | --- | --- |
| Generic DUML/USB engine | Separate transport, parser, command, and job layers | Exact WA150 route and current handler still required |
| Typed parameter editor | Baseline, original/current values, typed validation, post-write verification | A real RID-owned parameter and restore semantics are not yet known |
| Server job model | Prerequisites, staged progress, limits, recovery, and target-specific recipes | Opaque server payloads are not reproducible protocol evidence |
| Firmware-resident CFC | Persistent hook plus a narrow runtime control channel | No WA150 plaintext/signing/hook/recovery chain and no RID command were found |
| One-time FCC cache | Device/model binding and explicit offline availability state | It is FCC-specific licensing, not RID state or RF validation |
| Known restore issue | Treat off/restore as a multi-stage operation, not a Boolean UI event | Final readback and independent RF A-B-A remain mandatory |

The CFC architecture is the most relevant conceptual clue for a stable RID switch: identify the
actual aircraft policy/output owner, add a narrowly scoped runtime control at that owner, expose
readback, and preserve a stock-restoration path. Drone-Hacks does not supply the missing Mini 5 Pro
firmware plaintext, signature/loader acceptance, hook location, recovery path, RID semantics, or RF
proof. It therefore improves the architecture hypothesis but does not close an implementation.

## 7. Result for the current RID objective

`UNKNOWN`: a stable Mini 5 Pro RID switch remains unproven.

Drone-Hacks 2.0.29 contributes four concrete leads:

1. a reusable separation between a broad host executor and target-specific server jobs;
2. a firmware-resident control architecture already used on older DJI products;
3. typed parameter/readback patterns and an example showing that regulatory-mode restoration may
   require more than one command;
4. a numerically recovered legacy/general ADSB dictionary that can seed passive classification and
   exact firmware xref searches, subject to the demonstrated current-version collisions.

It does not contribute any of the following required evidence:

- a Mini 5 Pro software license or supported CFC image;
- a RID control command or parameter;
- a WA150 firmware hook or verified plaintext;
- a server job payload for RID;
- baseline, forward readback, restoration, final readback, or motor-on independent RF A-B-A.

The next discriminating work is still target-owned: close the current DJI Fly/FC RID policy owner
and status path first, then determine whether the same owner is a writable parameter, a managed
license, a server policy blob, or firmware-only logic. Only after an exact readback and restoration
surface exists should a firmware-resident runtime control be designed.

## 8. Public sources

- [Drone-Hacks 2.0.29 release metadata](https://releases.drone-hacks.com/latest.json)
- [Drone-Hacks Windows release notes](https://wiki.drone-hacks.com/en/windows_release_notes)
- [Custom Flight Controller commands](https://wiki.drone-hacks.com/en/dh2-cfc-commands)
- [Known issues and FCC restore procedure](https://wiki.drone-hacks.com/en/dh2-known-issues)
- [Custom-firmware release notes](https://wiki.drone-hacks.com/en/drone-hacks-v2/extras/fcfw-release-notes)
- [Ownership transfer notice](https://wiki.drone-hacks.com/new-era-for-DH)
- [Public model definitions](https://drone-hacks.com/api/v1/definitions/models)
- [Public model-catalogue application chunk](https://drone-hacks.com/_app/immutable/chunks/CXG_u84T.js)
- [Public compatible-license definitions](https://drone-hacks.com/api/v1/definitions/compatible-licenses)
- [Mini 5 Pro public product search](https://drone-hacks.com/api/v1/products/search?model=wa150)
- [Mini 3 Pro product-search positive control](https://drone-hacks.com/api/v1/products/search?model=wm162)
- [FCC ModBox compatibility configuration](https://drone-hacks.com/api/v1/configs/fccModBoxCompatibility)
- [Remote-controller compatibility boundary](https://wiki.drone-hacks.com/en/compatible-rc-dji-fly)

The API observations are an anonymous public snapshot from 2026-08-28. They may change. No
authenticated endpoint, account, license, device identifier, or private job payload was used.
