# Community DUML / Remote ID survey (2026-08-30)

This note records the public repositories and reports surveyed on 2026-08-30 for leads toward the
controllable Mini 5 Pro Remote ID switch, and what each does and does not establish. It is a survey
and cross-reference, not a device-control program. Public code provides names, command families,
sender gates and protocol precedent; it does not replace exact current product/version identity, a
live route, readback, restoration, or independent RF evidence.

## 1. Scope and method

Sources were located through GitHub repository and advisory search, then shallow-cloned and read.
Only independently written or explicitly licensed public material was inspected; no vendor APK,
firmware, partition, shared library, decompiled source, raw capture, serial, or credential was
copied into this repository. Every new claim below is pinned to a commit and marked `STATIC` or
`CORROBORATED` only.

## 2. Sources surveyed

- **FreeFCC** (`doesthings/FreeFCC`, commit `597157bd52120dfeb9677f79a8ad46b6027ce8dc`, AGPL-3.0).
  Already in the source index for its loopback frames and issue history. Newly reviewed: the
  published JSON profiles (`fcc.json`, `ce_restore.json`, `4g.json`, `led_on/off.json`) and the
  `NO_REMOTE_ID.md` position statement. None of the profiles carries a Remote ID parameter; the
  project states it will never ship Remote ID disabling (C-217).
- **lmdegreeds/djiparam** (commit `1b396b1a0adedfd81810d7ba535e0d1ff387a10d`, MIT). Already in the
  source index for the by-index FLYC family. Newly reviewed in depth: the `wa150` parameter table
  header and the contiguous EU C0 block at indices 1306-1315, plus the model-table README's
  Neo 2 index-drift warning (C-214, C-215).
- **GlassFalcon** (`sworrl/GlassFalcon`, commit `dadafaa7b8bb094c9db7c22dabba901c22b1ab62`,
  GPL-3.0). A vendor-independent DUML ground-control SDK for DJI aircraft. Reviewed: `Duml.kt`
  (DUML framing, CRC8/CRC16, source identities `MOBILE_APP=0x02` vs `PC=0x0a`, USB/AOA/TCP
  transports) and `DumlCommands.kt` (FlyC by-index `0xE0`-`0xE3` and by-hash `0xF7`-`0xF9`
  parameter commands with the explicit sender-identity gate). New fact: the by-index family is
  honored only under the PC/assistant identity `0x0a` (C-213).
- **luyii-code-1/dji-ocusync-droneid-research** (commit `2ca1a92cf90d3c764bf589a0f49499e56b145d6a`,
  GPL-3.0). Reproducible O2/O4 DroneID PHY and packet research based on HackRF captures from a
  Mini 5 Pro. Reviewed: `o4_packet_tool.py` and the README measurement record. Resolves the O4
  `AA`/`87` cryptographic envelope and the AES-128-CTR key/IV construction (C-216).

## 3. What each source adds to the RID switch question

### 3.1 The EU C0 block is not a transmitter kill switch

The wa150 table shows `EU_CE_enable_c0_rid` is one row inside a contiguous EU C0 class-compliance
block (indices 1307-1315). Two of the neighbours (`EU_CE_Reg_RID_Enable` and
`eu_ce_support_remote_set_level`) are declared with min 0 / max 0, i.e. not a writable Boolean
range in the public table. This strengthens the existing interpretation that the row family is an
EU C0 / registration flag cluster, and that a single C0 RID flag is not the same object as a
transmitter master switch that provably stops the standardized BLE/Wi-Fi broadcast. It does not
change the route-priority decision: a live by-index or by-hash baseline is still required before
any single transition, and RF truth still comes only from the independent receiver.

### 3.2 The by-index family has a sender-identity gate, and it is transport-specific

Two public projects disagree at first glance, and the difference is transport, not protocol.

- GlassFalcon records, confirmed live on its own wm240 bench, that `0x03/0xE0`-`0xE3` is only
  honored under the PC/assistant source identity `0x0a` and silently ignored under `0x02` over
  direct USB.
- djiparam records the same by-index family working end-to-end over the RC 2 localhost bus
  (`40008` inject, `40007` read) under `0x02` on the wa150/wa151 generation, including a
  `forearm_led_ctrl` index-23 write; it also records that `40009` only routes injects from a
  privileged uid.

The two are reconciled as a transport/generation-specific sender gate, not a universal one. The
practical consequence is unchanged for this archive: neither project is a Mini 5 Pro live result
here, the Android panel must not be assumed to reach the by-index family through the Binder route
without a positive control, and the repository's USB DUML host-tools remain the preferred read-only
entry point. The djiparam path additionally requires an unlocked RC (system shell plus permissive
SELinux), which is outside this repository's boundary and adjacent to the C-212 bricking precedent.

### 3.3 The private DroneID lane stays parked

The O4 chain (C-216) strengthens C-202's encrypted O4 boundary with a concrete AA/87 and
AES-128-CTR construction and the measured GNSS-valid / takeoff trigger granularity. It is private
OcuSync DroneID, distinct from the standardized ASTM F3411 / EN 4709 bearer that C-207 confirmed in
plaintext. It therefore changes nothing about the standardized-bearer switch objective; it only
reconfirms that the private lane is not an unencrypted short cut.

### 3.4 No second global-RID Boolean surfaced

(Preceded by a related table detail: the wa150 table does carry the China-broadcast sibling rows
`ccc_unsupport_control_type` (index 250) and `ccc_poor_position_accuracy_on` (251), while
`ccc_broadcast_signal_quality` itself appears only in the wa020 Neo 2 table; this is folded into
C-221 and changes no conclusion.)

### 3.4 No second global-RID Boolean surfaced

Beyond the SKYROVER `rid_ctrl_enable_0` chain already in the archive, the 2026-08-30 survey found
no second independent Mini 5 Pro global-RID Boolean implementation (C-222): FreeFCC profiles carry
no RID parameter and the project refuses RID disabling; the djiparam wa150 table has no
`rid_ctrl_enable_0` row (C-221); GlassFalcon exposes only non-RID FlyC commands; and the O4
repository targets the encrypted private DroneID lane (C-216). This is a bounded, dated negative
that extends the existing "no second implementation" note in RID-002C without proving absence in
unindexed or private material.

### 3.5A Cross-model parameter inventory narrows EU_CE_enable_c0_rid to Mini 5 Pro / Lito X1

The public djiparam model tables give a cross-model view of the EU C0 / China / RID-family rows
(C-225):

- `EU_CE_enable_c0_rid` (u8 0..1 default 0) exists **only** in wa150 (Mini 5 Pro) and wa151
  (Lito X1), both at index 1306.
- `EU_CE_Reg_RID_Enable`, `EU_CE_Reg_Level`, `fscap_EU_CE_Support`, and
  `eu_ce_support_remote_set_level` (all declared min 0 / max 0) exist across wa020 (Neo 2),
  wa150, wa151, wa234 (Air 3S), and wa341 (Mavic 4).
- `ccc_broadcast_signal_quality` exists only in wa020 (Neo 2); `ccc_unsupport_control_type` /
  `ccc_poor_position_accuracy_on` / `oid_link_disconnected` / `support_china_oid` exist in
  wa020/wa150/wa151/wa234.

The practical consequence: the zero-range `EU_CE_Reg_RID_Enable` is a widely shared, read-only
EU C0 registration marker, while `EU_CE_enable_c0_rid` is a generation-specific flag present on
exactly the Mini 5 Pro / Lito X1 pair. That strengthens its interest as a candidate row worth a
same-session, read-only by-index/by-hash baseline, but it still does not prove standardized Remote
ID RF control, and no live result is claimed.

### 3.5 o-gs/dji-firmware-tools independently pins the by-index family

The public `o-gs/dji-firmware-tools` tooling (pinned in the source index) sends parameter
requests with sender `COMM_DEV_TYPE.PC` (0x0a) to `FLYCONTROLLER` (0x03) and its `comm_mkdupc`
schema matches this repository's independently written `rid_param_index_protocol.py` get_info
reply layout (status/table/index/type_id/size/def/min/max/NUL-name). This is a third independent
pin of the by-index command family and of the direct-USB PC (0x0a) sender identity (C-224), and
again is protocol corroboration rather than a Mini 5 Pro live result.

## 4. Source-handling boundary

None of these repositories was vendored. Their facts are recorded by name, commit, and high-level
finding only. Their licenses (GPL-3.0, MIT, AGPL-3.0) are their own; no third-party source file is
copied here. See [14_SOURCE_INDEX.md](14_SOURCE_INDEX.md) for the pinned entries and
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) for the repository-wide third-party policy.
