# 地区码、FCC/CE、SDR 与 RF 证据

本文件记录 DJI Fly / RC 2 / Mini 5 Pro 的地区状态与 O4 regulatory RF policy 证据。社区常用的
“FAA mode”在本文中称为 **FCC regulatory mode**：FAA 管理飞行运行，而 DJI 公开规格使用 FCC、CE、
SRRC、MIC 等射频限制名称。

本文件不提供 radio-power modification profile、keepalive、country writer 或设备控制程序。范围和
解释规则见[范围与脱敏](00_SCOPE_AND_REDACTION.md)。

机器索引中的核心对应 claim 为：FC loop `C-026`、Sky loop `C-027`、Ground negative `C-028`、
region/RF interpretation `C-029`、ACK/readback/persistence 分层 `C-048`、onboard/RF 分层 `C-049`、
state-change evidence minimum `C-052`。SDR snapshot、legacy PowerMode negative、policy pipeline 和
official EIRP ceiling 分别登记为 `C-066`--`C-070`；最终已知 region state 为 `C-079`。

## 当前表面与最终状态

| 表面 | 当前证据状态 | 最终公共记录 | 不证明 |
| --- | --- | --- | --- |
| FC area | `OBSERVED` | CN；曾完成一次 `CN -> US -> CN` 闭环 | RID、频道、RF power 改变 |
| Sky country | `OBSERVED` | CN；曾完成一次 `CN -> US -> CN` 闭环 | Ground/RC policy 同步 |
| Ground country | `NEGATIVE` | 单次 US 无匹配 ACK，随后及最终 GET 为 CN | 永久不支持 setter |
| RC / DJI Fly policy country | `UNKNOWN` | available route 未取得 | 可由 FC/Sky/Ground 推断 |
| SDR address `0xFFFF0048` | `OBSERVED` | Sky 与 Ground 当时均为 5 | 5 的 regulatory 含义 |
| SDR address `0xFFFF0063` | `OBSERVED` | Sky 与 Ground 当时均为 0 | 当前 UI 一定称为 auto |
| O4 channel / EIRP | `UNKNOWN` | 无独立 RF 仪器或 receiver 同步记录 | country/state readback 等于 RF change |

## DJI Fly policy pipeline

### REG-001：现代 policy 是多输入 area-code pipeline

- **证据状态：STATIC**
- **对象/版本：** 已恢复 DJI Fly area-code 业务层、MSDK 5.18.0 native mapping。
- **前提与路线：** aircraft/controller 或 phone GNSS、MCC、IP、nearby-city、data-change 与 cache
  等输入进入 area manager，再同步不同 surface。
- **事实：** 静态路径把选择结果发布到 Sky/Ground Airlink area keys，在适用产品上同步 Wi-Fi
  country，并同步 FC area。native key-value 和下游 radio firmware 再应用 regulatory policy。
- **边界/不证明：** 输入优先级的候选顺序可见，但最终 fusion、trust、cache 和 anti-drift 规则仍有
  native 未闭合部分。pipeline 存在不证明当前某个 country 值已在所有 surface 一致生效。
- **公开依据：** 先前公开
  [DJI RC 2 / O4 regulatory RF-power research](https://github.com/Sapphire-Rapids/FindUAS/blob/15f331cf68ce93ae444a8e6aff4c5dc1ed90b5cc/docs/DJI_RC2_RF_POWER_RESEARCH.md#normal-dji-fly-policy-path)，
  固定 public reverse-source snapshots、DJI MSDK 5.18.0。
- **隐私/分发：** 不记录真实 GNSS、MCC、IP、城市或 cache 内容。

### REG-002：FC area 的现代 GET/SET schema 已静态闭合

- **证据状态：STATIC**
- **对象/版本：** MSDK 5.18.0 arm64 native mapping。
- **前提与路线：** FLYC `0x03/0xAF`。
- **事实：** GET 为 subcommand `0x04` 加固定零填充；SET 为 subcommand `0x03` 加 ISO-3166-1
  numeric value 的 little-endian 表示。当前 native GET 从成功 response 的固定位置读取数值。
- **边界/不证明：** schema 存在不等于所有产品支持，也不等于 FC area 是最终 RF authority。SET ACK
  callback 不比较 applied value，因此 ACK-only 不能证明状态改变。
- **公开依据：** 前述 RF-power research、MSDK 5.18.0。
- **隐私/分发：** command/schema 可公开；不发布 raw frames 或 device identity。

### REG-003：内部 debug controls 不是 production FCC toggle

- **证据状态：STATIC**
- **对象/版本：** 已恢复 DJI Fly internal-build area controls。
- **前提与路线：** internal build preference 与 area synchronization logic。
- **事实：** `debug_area_code_switch` 只控制内部 app 是否向部分 device surface 同步地区；关闭它是
  抑制写入，不是选择 FCC。另一个 local-forever mock country 仅在 internal build 条件下进入 area
  manager。
- **边界/不证明：** 没有证据表明账号国家、resource overlay、证书替换或 production settings UI
  暴露等价控制。不得把 preference 名称转换成产品写入步骤。
- **公开依据：** 前述 RF-power research。
- **隐私/分发：** 只发布符号与作用边界，不发布 vendor code。

### REG-004：相邻 RC331 平台含 country persistence/application 链

- **证据状态：STATIC**
- **对象/版本：** no-force verified 相邻 RC331 `10.00.0700/0205` Android OTA。
- **前提与路线：** 对 selected platform service、init/SELinux 和 country-related string/xref 做离线
  静态检查。
- **事实：** 静态证据支持 authenticated DJI Fly / DUSS country input 经 `dji_link` 做 country
  conversion/event 并持久化，再由 `dji_sdrs_agent` 应用 wireless-country operation。相关 service
  配置为 DJI app authentication domain。
- **边界/不证明：** exact message ID、payload、precedence 和 permission check 未恢复；相邻 v10 证据
  不证明 live v07 byte-identical。不得据 log/string 猜测 writer。
- **公开依据：** 前述 RF-power research、
  [固件信任边界](07_FIRMWARE_TRUST_BOUNDARY.md)。
- **隐私/分发：** 不发布 filesystem image、binary、反编译正文或 live persistent file。

### REG-005：相邻平台有 power-level test anchor，但没有可用 public control

- **证据状态：NEGATIVE**
- **对象/版本：** 相邻 RC331 `10.00.0700/0205` 中的 `dji_wlm` 等平台组件。
- **前提与路线：** targeted static handler/string/xref audit。
- **事实：** 找到内部 SDR/Wi-Fi/LTE power-level test 相关 anchor，但没有恢复安全 public property、
  level enum、handler registration、message ID 或下游 SDR acceptance rule。
- **边界/不证明：** scoped negative 不证明内部实现不存在；它否定把附近 debug string 或 `setprop`
  猜成已验证 RF control。相邻平台也未在 live controller 上执行。
- **公开依据：** 前述 RF-power research。
- **隐私/分发：** 不发布 vendor binary/code 或 invocation recipe。

## Community DUML surface audit

### REG-006：country state 与 FC area 是可读回的独立表面

- **证据状态：STATIC**
- **对象/版本：** 固定 community RC 2 prior art、legacy DJI command model、MSDK 5.18.0。
- **前提与路线：** Airlink country family `0x07/0x30` SET / `0x07/0x19` GET；FC area
  `0x03/0xAF`。
- **事实：** community evidence 和当前静态 handler 均支持把 Airlink alpha-2 country 与 FC numeric
  area 视为不同表面。旧十字节 country request 中可能存在两个 band slot，但当前 RC 2 handler 的
  静态行为只消费 leading alpha-2 country 并保存一个 vendor country slot。
- **边界/不证明：** duplicate frames 不证明 per-band write；FC、Sky、Ground、RC policy 不能互相推断。
- **公开依据：** 固定 FreeFCC/SkylabFCCfree prior art、前述 RF-power research。
- **隐私/分发：** 不发布 private capture；只保留 command family 和独立表面结论。

### RF-001：legacy `setForceFcc()` 对应一个窄 Sky SDR selector

- **证据状态：STATIC**
- **对象/版本：** legacy DJI Java model 与一条固定 community frame。
- **前提与路线：** Sky / CP_A7，SDR assistant write address `0xFFFF0048`，literal value 2，
  OSD/OFDM `0x09/0x27`。
- **事实：** legacy model 明确把该组合命名为 `setForceFcc()`，一条 community frame 与组合一致。
- **边界/不证明：** 没找到当前 DJI Fly business caller；它是 legacy protocol surface，不是 current
  Mini 5 Pro/O4 safe writer。也不证明 value 2 的 current target effect 或 measured EIRP。
- **公开依据：** 固定 legacy source、前述 RF-power research。
- **隐私/分发：** 只记录静态映射，不提供 profile/keepalive 或执行程序。

### RF-002：若干社区帧不能合并称为“FCC protocol”

- **证据状态：NEGATIVE**
- **对象/版本：** 固定 FreeFCC / SkylabFCCfree profiles 与相关 command-label audit。
- **前提与路线：** 对完整 profile、restore frame 和 keepalive 中每条 command 做来源与语义核对。
- **事实：** `0xFFFF0063` 属于 frequency-band selector 家族而非已知 power register；RC
  `0x06/0x72` 在不同产品有不同含义；500 m height write 与 FCC 无关；activation、Care、perception、
  lost-link 等帧没有建立为 RF primitive；常见四帧 keepalive 不含 country update 或已知
  `setForceFcc` 组合。
- **边界/不证明：** public reports 中的 UI 变化可能是真实观察，但 local socket writes 不隔离是哪条
  frame 造成结果，也不提供 RF measurement。不能据此构造“最小 FCC 协议”。
- **公开依据：** 固定 community repositories/issues、前述 RF-power research。
- **隐私/分发：** 不收录完整可执行 profile 或 blind keepalive。

## 有界实机 state validation

### REG-007：FC area 完成一次 `CN -> US -> CN` 闭环

- **证据状态：OBSERVED**
- **对象/版本：** 当前 Mini 5 Pro 实机，2026-08-27。
- **前提与路线：** 明确的一次性 surface-specific 授权；FC GET baseline 为 CN/156；固定 SET；
  transport ACK 后必须 fresh GET；恢复到原值并 final independent GET。
- **事实：** forward 后 ACK 与 GET 均为 US/840；restore 后 ACK 与 GET 均为 CN/156；独立 final
  GET 仍为 CN/156。
- **边界/不证明：** 只证明当前 session 的 FC area field 可逆变化，不证明 complete region、RID、
  FlySafe、channel、SDR selector、persistence after reboot 或 RF power 变化。
- **公开依据：** 前述 RF-power research；行动记录应见[时间线](03_TIMELINE.md)。
- **隐私/分发：** 不保留 serial、账号、坐标或完整 raw frame。

### REG-008：Sky country 完成一次 `CN -> US -> CN` 闭环

- **证据状态：OBSERVED**
- **对象/版本：** 当前 Mini 5 Pro Sky route，2026-08-27。
- **前提与路线：** 两次连续 CN precondition GET；至多一次 forward 和一次 restore；每次 SET 需
  strict matching ACK + fresh GET。
- **事实：** forward SET 后 ACK 匹配且 GET=US；restore SET 后 ACK 匹配且 GET=CN；最终独立 probe
  保持 CN。
- **边界/不证明：** 只证明固定 route/session 的 Sky country surface，不证明 Ground/RC policy、FC
  同步、channel、country persistence、Remote ID format 或 EIRP。
- **公开依据：** 前述 RF-power research。
- **隐私/分发：** 不发布 raw frame 或设备身份。

### REG-009：Ground US 单次请求无匹配 ACK，readback 仍为 CN

- **证据状态：NEGATIVE**
- **对象/版本：** 当前 RC 2 Ground route，2026-08-27。
- **前提与路线：** 两次连续 CN precondition GET；仅一次 fixed US SET；strict ACK matcher；请求后
  立即 safe GET；无 retry。
- **事实：** 没有 matching ACK；fresh GET 仍为 CN，因此 harness 不发送 restore SET。之后两个独立
  final GET 仍为 CN。
- **边界/不证明：** 不是成功写入，也不证明 Ground 永久不支持 setter。可能的 exact modern
  route/context 未闭合；一次 timeout 不是重试授权。
- **公开依据：** 前述 RF-power research；同步登记到[否定结果](09_NEGATIVE_RESULTS.md)。
- **隐私/分发：** 不发布 raw traffic 或 USB topology。

### REG-010：最终已知 region surfaces

- **证据状态：OBSERVED**
- **对象/版本：** 当前实机组合，在有界事务恢复后。
- **前提与路线：** fixed read-only FC/Sky/Ground GET，两个独立 final probes。
- **事实：** FC=CN、Sky=CN、Ground=CN；RC/DJI Fly policy country 为 unavailable/unknown。
- **边界/不证明：** 三个可读值不构成稳定 aircraft/controller pair identity，也不能推出 unknown RC
  policy。最终 state readback 不证明 aircraft power-cycle persistence。
- **公开依据：** 前述 RF-power research、[状态与账号](04_STATE_ACCOUNT_LIMITS.md)。
- **隐私/分发：** 只发布非识别性 country state。

## SDR 与公开 RF 规格

### RF-003：DJI RC 2 公开规格给出 regulatory EIRP ceiling，而非恒定输出

- **证据状态：STATIC**
- **对象/版本：** DJI RC 2 官方 O4 video transmission specification。
- **前提与路线：** 官方规格中的不同 regulatory regime 表格。
- **事实：** 公开 ceiling 包括 2.4 GHz FCC `<33 dBm`、CE `<20 dBm`；5.8 GHz FCC `<33 dBm`、
  CE `<14 dBm`；CE 另列 5.1 GHz `<23 dBm`。
- **边界/不证明：** ceiling 不是当前设备恒定 output，也不是本次实机 measurement。DJI Fly channel
  graph、range、RSSI 或 distance line 不能证明 33 dBm。O4 与 RC 2 普通 Android Wi-Fi 也不是同一
  radio surface。
- **公开依据：** [DJI RC 2 specifications](https://www.dji.com/rc-2/specs?startPoint=0)。
- **隐私/分发：** 官方公开规格，无私人数据。

### RF-004：两个 endpoint 的 SDR read-only snapshot 一致

- **证据状态：OBSERVED**
- **对象/版本：** 当前飞机 Sky endpoint 与 RC 2 Ground endpoint，2026-08-27。
- **前提与路线：** fixed-address SDR Assistant Read `0x09/0x26`；hard allow-list 只包含
  `0xFFFF0048` 与 `0xFFFF0063`；无 write、country、commit 或 keepalive path。
- **事实：** 两端 `0xFFFF0048` 均为 5，`0xFFFF0063` 均为 0；每个匹配 response result code 为 0。
- **边界/不证明：** 只证明当时两个 endpoint 的两个 slot 一致。它不命名 value 5，也不证明 FCC/CE
  state、channel table 或 RF output。
- **公开依据：** 前述 RF-power research；应同步登记到
  [证据登记册](02_EVIDENCE_REGISTER.md)。
- **隐私/分发：** 只发布 address/value 聚合，不发布 raw reply。

### RF-005：两个 SDR value 的语义边界

- **证据状态：UNKNOWN**
- **对象/版本：** 当前 O4 / RC 2 radio policy。
- **前提与路线：** RF-001 legacy mapping 与 RF-004 live readback。
- **事实：** 唯一已恢复的窄 legacy 事实是 `setForceFcc()` 写 value 2 到 `0xFFFF0048`；当前 readback
  value 5 的确切名称、owner、fallback 与 reconnect/reboot behavior 未知。`0xFFFF0063=0` 在 legacy
  enum 中是 dual-band；当前 DJI Fly 是否显示为 auto 仍未直接观察。
- **边界/不证明：** 不得把 5 猜成 CE/FCC，或把 0 自动命名为 current auto mode。
- **公开依据：** 前述 RF-power research；未知项见
  [假设与未知](10_HYPOTHESES_AND_UNKNOWNS.md)。
- **隐私/分发：** 无私人数据。

### RF-005A：legacy RC PowerMode GET 在两个候选 route 均无响应

- **证据状态：NEGATIVE**
- **对象/版本：** 当前 RC 2 实机候选 route。
- **前提与路线：** legacy RC PowerMode GET `0x06/0x21`；两个固定候选 route。
- **事实：** 两路均未得到 response。
- **边界/不证明：** 只说明旧 query path 在这两个 route 不可用；不证明当前 regulatory state 是 CE、
  FCC 或其他模式。
- **公开依据：** 前述 RF-power research。
- **隐私/分发：** 不发布 raw timeout trace。

## RF-006：证据阶梯

- **证据状态：INFERENCE**
- **对象/版本：** 本研究档案对 state 与 RF claim 的统一解释规则。
- **前提与路线：** 综合 community socket behavior、实机 state readback 和公开 RF measurement 原理。
- **事实：** 至少应分为四层：
  1. transport：bytes 到达 local proxy/USB；
  2. protocol state：strict ACK + independent GET readback；
  3. regulatory surface：band/channel/bandwidth/frequency range 或 app graph 的 observable consequence；
  4. RF measurement：在 shielded 或 fixed-attenuation 条件下用 spectrum analyzer/power meter A/B。
- **边界/不证明：** 前一层不蕴含后一层。range、RSSI、UI distance line 含 path-loss、link、TX-power
  与显示 offset，不能替代 calibrated RF measurement。
- **公开依据：** 前述 RF-power research；onboard/RF 双层规则另见
  [状态与账号](04_STATE_ACCOUNT_LIMITS.md#state-006广播验证需要两个独立层级)。
- **隐私/分发：** 未来 RF 报告使用合成身份和脱敏 measurement，不发布私人飞行数据。

## RF-007：有界 area/country 实验没有 RF 结论

- **证据状态：NEGATIVE**
- **对象/版本：** 2026-08-27 FC/Sky/Ground 有界 state experiments。
- **前提与路线：** 外部 FindUAS receiver 当时离线；未使用 spectrum analyzer 或 power meter；未改变
  SDR selector、channel、account、flight limit、motor 或 RID setting。
- **事实：** 实验只得到 FC/Sky/Ground state-level 结果，没有 over-the-air Remote ID、channel、
  regional format 或 RF-power observation。
- **边界/不证明：** 成功恢复 state 不证明没有瞬时 RF effect，也不证明发生过 RF effect；两者都未测。
- **公开依据：** 前述 RF-power research；同步列入
  [否定结果](09_NEGATIVE_RESULTS.md)。
- **隐私/分发：** 不发布现场位置、身份或原始 capture。

## 当前未知与阻断点

### REG-011：最终 policy authority 与 persistence 未闭合

- **证据状态：UNKNOWN**
- **对象/版本：** 当前 Mini 5 Pro、RC 2、DJI Fly 和 O4 system。
- **前提与路线：** 需要在不争夺官方 owner 的条件下同时观察 app policy、FC、Sky、Ground、SDR 和
  power-cycle persistence。
- **事实：** 已知这些是独立 surface，且 DJI Fly 有同步/retry behavior；现有实验只对 FC 和 Sky
  分别完成一次 state loop，Ground 未形成 applied state，RC policy 不可读。
- **边界/不证明：** 不能指定谁是最终 authority，也不能假设单一 country write 会稳定覆盖全部 surface。
- **公开依据：** 前述 RF-power research；阻断项见
  [当前阻断点](12_CURRENT_BLOCKERS.md)。
- **隐私/分发：** 未来记录仍只保存去标识 state 和 aggregate timing。

### RF-008：实际 O4 channel/EIRP change 未测

- **证据状态：UNKNOWN**
- **对象/版本：** 当前 Mini 5 Pro / RC 2 O4 link。
- **前提与路线：** 需要授权的 shielded/conducted 或 fixed-attenuation A/B，calibrated analyzer/meter，
  同步 state snapshot 和独立 restore verification。
- **事实：** 当前档案没有该 measurement。
- **边界/不证明：** 任何 country、SDR state、UI graph、socket write、range 或 RSSI 都不能补足该缺口。
- **公开依据：** 前述 RF-power research；实验门禁见
  [交接](13_HANDOFF.md)。
- **隐私/分发：** 不在公共环境发射合成身份；公共记录不得含精确现场位置或私人 flight capture。

## coding agent 接手规则

1. topic claim 必须同步到[证据登记册](02_EVIDENCE_REGISTER.md)和机器可读 claims CSV。
2. region 模型必须保留 FC、Sky、Ground、RC/DJI Fly policy 四个独立字段和 unavailable 状态。
3. UI 或报告不得把 ACK-only、state readback、UI graph、socket completion 或 onboard status 标为 RF
   success。
4. 不实现 generic writer、opaque profile replay、blind keepalive、SDR power setter 或 country fight loop。
5. 如果未来出现第三值、route drift、policy overwrite 或 restore mismatch，状态机必须停止，不与 DJI Fly
   synchronizer 竞争。
6. 新实验必须满足 [AGENTS.md](../AGENTS.md) 的 baseline、request count、strict matcher、fresh readback、
   restore、final state 和 independent RF 字段要求。
7. 新的猜测先写入[假设与未知](10_HYPOTHESES_AND_UNKNOWNS.md)；失败路线进入
   [否定结果](09_NEGATIVE_RESULTS.md)，不要用新的 timeout 覆盖旧结论。
