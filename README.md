# DJI RC 2 / Mini 5 Pro research archive

[![Validate research archive](https://github.com/Sapphire-Rapids/DJI-RC2-Mini5Pro-Research/actions/workflows/validate.yml/badge.svg)](https://github.com/Sapphire-Rapids/DJI-RC2-Mini5Pro-Research/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

这是一个独立、非官方的 DJI RC 2 / Mini 5 Pro 研究档案。记录截至 2026-08-29 的实机观察、
固定版本静态分析、公开资料交叉验证、阴性结果、被撤回的路线、明确假设和未解决问题。

档案中的产品名称只用于说明研究对象。项目与 DJI 无隶属、授权或背书关系。

## 研究对象快照

| 对象 | 记录值 | 证据边界 |
| --- | --- | --- |
| 遥控器 | DJI RC 2；界面固件 `07.00.0100` | 精确 live 系统包未取得；部分平台结论来自相邻 RC331 `10.00.0700/0205` |
| 飞机 | DJI Mini 5 Pro；静态候选 WA150 / product 139 | product/route 需在 live session 重新确认 |
| DJI Fly | 重点分析样本 1.21.10 | 静态样本，不自动等同于 RC 2 当前已加载 APK |
| MSDK | 重点交叉验证 5.18.0 | schema/handler 证据不等于消费级产品支持 |
| 主机 | macOS；飞机与 RC 2 分别枚举为 DJI USB 设备 | 序列号、端口位置和私人数据不公开 |

## 状态词

- `OBSERVED`：实机直接观察或有界实验结果。
- `STATIC`：固定 app/library/firmware 的静态证据，未在 live 设备执行该路径。
- `CORROBORATED`：同一窄事实由独立来源交叉支持。
- `NEGATIVE`：限定条件下未得到预期结果；只否定该条件。
- `INFERENCE`：由事实推导、尚未直接观察的解释。
- `HYPOTHESIS`：可验证但尚未执行或闭合的候选解释/路径。
- `UNKNOWN`：现有材料不能回答。
- `RETRACTED`：后续证据推翻了早先假设、工件或流程。
- `NOT ADMITTED`：静态上存在，但缺少运行前证据门禁。

`unavailable` 不等于 `off`、`unsupported`、`absent` 或 `empty`。

## 当前结论摘要

- Current same-family SKYROVER `1.2.0` 已出现一个独立 Boolean `RIDCtrlEnable`：native 映射
  为 FC 参数 `rid_ctrl_enable_0`、hash `0x3CBD864F`，使用 FLYC `03/F7-F9`。它与 France
  EID、OPID、DIPS 和 China OID 分开。DJI Fly `1.21.10` 没有同名 wrapper，因此 Mini 5 Pro
  是否支持仍由当前实机 F7/F8 决定，不能仅凭静态同族 SDK 宣称已实现。
- 同族 RID key/native-handler 全量盘点没有发现第二个可直接落地的 global Boolean；公开固定
  revision 与 exact-string 检索也没有独立 Mini 5 Pro 实现。FreeFCC 仅交叉支持 modern route
  和 F9 framing，其参数与功能不同。
- Product-139 的 France EID 静态路径已闭合到 `0x03/0x77`，但它是法国专用 EID，不是
  global RID。两个固定人工 USB GET 路由均未获得 canonical ACK；DJI Fly 私有 owner 路径未实测。
- FlySafe type-6 `RID_UNLOCK` 是账号/FC 绑定的签名许可类别。官方 MSDK 5.18 保留实现会在
  产品 gate 为真、license 已 enabled 且 EU/China level 匹配当前 area strategy 时，把状态直接
  置为 `broadcastRemoteIdEnabled=false` / `NO_BROADCAST`。current native inventory/set-enable
  wire 已闭合为 `0x11/0x11` / `0x11/0x12`，product-139 receiver 为 `0x92`。这证明了设计语义，
  但 Mini 5 Pro 是否有资格、是否存在真实许可、当前 runtime 是否执行该分支及 RF 是否变化仍为
  `UNKNOWN`。
- DJI Fly `1.21.10` 的中国 OID `setReportEnable` 已闭合为 App/RC 网络上报 gate：关闭时跳过
  云提交并 direct-success，但不写飞机 BLE/Wi-Fi 广播。当前 exact setter 复查仍只找到 France
  EID wrapper，没有 product-139 ODID/OpenDroneID/global RF setter。
- A-024 的 30 秒 `0x11/0x1C` Binder listener 已实测：framework 接受监听，但在操作者起桨且
  独立检测设备确认真实 RID RF 的同一实验中仍为零 callback。因此该第三方 Binder listener 是
  假阴性路径，不再作为 readback oracle，也不再重复；它不否定 DJI Fly 自身 observer。
- DJI Fly `1.21.10` 的 product-139 主 abstraction 确实挂载 `RidImportModule`；它把
  `0x11/0x1C` 注册成只监听的七字节 RID/EID 状态，没有 GET、SET 或 action。独立的
  `0x00/0xDD` cloud-control key 只有 SET，ACK 只确认请求并缓存原值，不是 applied-state readback。
- 配置读取显示高度 500 m、距离 5000 m、距离限制关闭；这不能解释或否定未登录状态可能存在的
  30/50 m effective runtime restriction。
- FC area 和 Sky country 已完成 `CN -> US -> CN` 的一次有界读回/恢复闭环；Ground country 的
  单次 US 请求无匹配 ACK，随后 GET 仍为 CN。没有由此获得 Remote ID、频道或 RF 功率证据。
- RC 2 标准 ADB 在 RSA 认证前停止：主机 `CNXN` 已发出，设备不返回 ADB 包。相邻 unstripped
  `adbd` 含 production `CNXN` drop gate，可解释现象但不等同于精确 live v07 二进制证明。
- 当前 Android admission probe v0.10 通过离线工件审计，但尚未复制、安装或运行于 RC 2。
- 固定 clean-room 管理客户端 `0.3.0-research` 已安装并执行：live `protocol` Binder lookup、
  manager transaction 和 callback exception layer 均成功，但 target F7 在约 3.1 秒后以
  `ECode 1` 结束，没有 F7 ACK，也没有发送 F9。相邻 RC331 `ActQueue` 将该错误映射为重试耗尽；
  因该版本没有同路由已知参数正对照，这不是 parameter-absence 结论。
- 替代客户端 `0.4.1-research`（SHA-256
  `68f9b0d42d42e1bcb674ddba88a3996229d06978e35e30a355f253678a8e2b95`）先要求每条 Binder
  route 的 maximum-height F7/F8 正对照，再解释 target；它还增加完整 30 秒只读
  `0x11/0x1C` 状态时间线。25 项测试、lint 0 errors、两次逐字节相同构建及 APK 审计通过，
  已安装运行。legacy `0A:05 -> 03:00` 与 modern `02:04 -> 12:04` 正对照均以 `ECode 1`
  timeout，故 target F7/F8/F9 未发送；passive timeline 后续已由独立 RF 对照判为假阴性。
- 2026-08-28 实机 direct F7 已完成：RC 2 routed 和 aircraft-direct 两路对
  `0x3CBD864F` 均返回 one-byte `03`，且同会话已知参数正对照正常。raw USB modern route
  连 height control 也 timeout；A-023 的 Binder target 同样 timeout，但没有同路由正对照。
  A-024 又证明两条 Binder route 连 height 正对照都失败，因此 current generic-parameter
  attach 路线已关闭；target 从未发送，未发送 F9。下一主线是通过 system Binder 只读查询现代
  FlySafe type-6 inventory，并追其 enable state 到 `NO_BROADCAST`/真实 RF 的因果链；并行继续
  WA150 `0802` broadcaster/policy owner。
- Route-only V2.2 已因两个 P1 与一个 P2 缺陷撤销。V2.3 修复三项缺陷，但仍固定零 exception
  gate、zero-send、未上机，且尚无新的独立 post-fix audit 结论。
- NLD FCC Smart RC `2.0.0.6` 的普通 FCC 路径使用 authenticated Base64 envelope、
  AES-256-CBC、签名 entitlement 与原子离线缓存，再把解密 JSON 转为 DUML 发送；APK/ZIP
  没有真实 payload，因此具体命令和 RF 效果仍未知。七个与 FreeFCC 完全相同的 JSON 未发现
  运行时引用。C0 是独立的
  在线 VPN 配置、WireGuard、重启 DJI Fly，并在隧道 UP 后安排 25 秒自动停止的流程；实际
  路由范围由服务端配置，只有 allowed IPs 为空时才使用目标主机 IPv4 `/32` fallback。
- 对 NLD `2.0.0.6` 的全 DEX、资源、profile 和两架构 native 可打印字符串搜索没有找到
  可识别的 Remote ID 开关。opaque payload 或外部 DJI Fly 的间接副作用仍为 `UNKNOWN`。
- Drone-Hacks `2.0.29` 的官方 MSI 与本地输入逐字节一致且签名有效。客户端是 Rust/Tauri
  通用 DUML/USB/ADB/固件/参数 job engine；直接 `dhfc_config` 只有 FCC、NFZ 和高度，未发现
  RID 命令。其公开 CFC 是值得借鉴的“固件内 hook + 窄运行时控制”架构，但当前公开支持中
  Mini 5 Pro 只有型号登记/独立 FCC 硬件兼容，没有软件产品、CFC 或 RID 控制证据。
- Drone-Hacks 的 Debug 字典已数值恢复：其中 `RID_INFO=0x11/0x1A`、
  `EID_INFO=0x11/0x35`。但它在 `0x11/0x0C`、`0x11/0x1C` 上与 DJI Fly `1.21.10` 当前含义
  冲突，因此只能用于被动分类/固件检索，不能作为 Mini 5 Pro 发包或开关协议。
- NDSS 2023 所述旧式 DroneID 多字段控制已高置信对应到 FlyC `0x03/0xDA` 的
  `0x05`/`0x06` mask。论文的 RF 实测并未停发包，只把选中字段替换成 `fake`；它针对私有
  OcuSync/AeroScope DroneID，不是 Mini 5 Pro 的 ASTM/FAA/EU Broadcast RID。
- 可调目标已扩展为 RID 实验控制面。current exact 路径新增闭合 EASA OPID `0x03/0x78`、
  Japan DIPS `0x11/0x4B`、China UOM tag `0x11/0xD6`、app location `0x11/0x43` 和只读
  compliance serial；它们是不同身份/地区数据面，当前均未达到 Mini 5 Pro 可写 UI 的完整门禁。
- China UOM tag 的 product-139 receiver、timeout/retry 与 reply value parser 已进一步闭合；其
  独立 `0x11/0xD1` 实名状态 key 只有在 runtime function ID `0x6C` admission 后出现，Sync 属
  账户/网络认证链且没有 setter。两者都不是 RID 广播开关，实机 admission/ACK/RF 仍未验证。
- 两份独立公开 Mini 5 Pro 照片元数据的软件版本与 WA150 `0802` 的 0600/0700 版本精确匹配；
  结合公开 BLE/网络公告，`0802` 是主应用及网络服务的强候选。公开检索仍没有 plaintext、
  target key、recovery image、RID handler 或 0700 可复现 PoC，故固件修改门禁未改变。
- 尚未证明一个稳定、可恢复、经状态读回和起桨后独立 RF 接收共同确认的 Mini 5 Pro RID 开关。

## 文档地图

- [AGENTS.md](AGENTS.md)：人类与 coding agent 的接手契约。
- [docs/00_SCOPE_AND_REDACTION.md](docs/00_SCOPE_AND_REDACTION.md)：范围、证据类型和脱敏边界。
- [docs/01_RESEARCH_PROCESS.md](docs/01_RESEARCH_PROCESS.md)：实际研究过程与方法。
- [docs/02_EVIDENCE_REGISTER.md](docs/02_EVIDENCE_REGISTER.md)：核心 claim 登记册。
- [docs/03_TIMELINE.md](docs/03_TIMELINE.md)：2026-08-27 至 2026-08-28 时间线。
- [docs/04_STATE_ACCOUNT_LIMITS.md](docs/04_STATE_ACCOUNT_LIMITS.md)：RID 状态、账号登录和限飞层。
- [docs/05_RID_CONTROL_SURFACES.md](docs/05_RID_CONTROL_SURFACES.md)：各 RID/EID/OPID/许可控制面。
- [docs/06_REGION_RF_POLICY.md](docs/06_REGION_RF_POLICY.md)：地区码、FCC/CE、SDR 与 RF 证据。
- [docs/07_FIRMWARE_TRUST_BOUNDARY.md](docs/07_FIRMWARE_TRUST_BOUNDARY.md)：Assistant、WA150、RC331 与固件信任边界。
- [docs/08_ANDROID_ADB.md](docs/08_ANDROID_ADB.md)：Android、MTP、隐藏设置、APK 与 ADB。
- [docs/09_NEGATIVE_RESULTS.md](docs/09_NEGATIVE_RESULTS.md)：阴性结果与其限定范围。
- [docs/10_HYPOTHESES_AND_UNKNOWNS.md](docs/10_HYPOTHESES_AND_UNKNOWNS.md)：猜测、未知与判别实验。
- [docs/11_ARTIFACT_REGISTER.md](docs/11_ARTIFACT_REGISTER.md)：工件版本、哈希、审计和处置。
- [docs/12_CURRENT_BLOCKERS.md](docs/12_CURRENT_BLOCKERS.md)：当前证据门禁。
- [docs/13_HANDOFF.md](docs/13_HANDOFF.md)：接手顺序、文件/符号入口和状态更新规则。
- [docs/14_SOURCE_INDEX.md](docs/14_SOURCE_INDEX.md)：公开来源与固定 revision。
- [docs/15_LOG_INDEX.md](docs/15_LOG_INDEX.md)：未公开工作日志族及其支持的结论。
- [docs/16_NLDFCC_STATIC_ANALYSIS.md](docs/16_NLDFCC_STATIC_ANALYSIS.md)：NLD FCC Smart RC
  `2.0.0.6` 的静态实现、FreeFCC 对照、RID 阴性边界和可借鉴设计。
- [docs/17_DRONE_HACKS_STATIC_ANALYSIS.md](docs/17_DRONE_HACKS_STATIC_ANALYSIS.md)：Drone-Hacks
  `2.0.29` 的官方来源、签名、客户端/job/CFC 架构、Mini 5 Pro 支持边界和 RID 阴性结果。
- [docs/18_LEGACY_DRONEID_DETECTION.md](docs/18_LEGACY_DRONEID_DETECTION.md)：旧式 FlyC
  `Detection` 多字段 mask、NDSS RF 结果，以及不能迁移到现代 Broadcast RID 的边界。
- [docs/19_RID_EXPERIMENT_CONTROL_MATRIX.md](docs/19_RID_EXPERIMENT_CONTROL_MATRIX.md)：RID
  状态、身份、地区、策略、managed/opaque/legacy 面的可读/可写/恢复/RF 与 UI 准入矩阵。
- [evidence/claims.csv](evidence/claims.csv)：机器可读 claim 索引。
- [evidence/artifacts.csv](evidence/artifacts.csv)：机器可读工件索引。

## 仓库内容边界

本仓库只发布独立撰写的 Markdown/CSV、公开链接、版本号、命令标识、聚合结果和文件哈希。
不发布 DJI APK、固件、提取分区、共享库、反编译源码、原始私人抓包、账号材料、ADB key、
设备序列号、UAS ID、电话或坐标。

## License

[MIT](LICENSE) © 2026 Sapphire-Rapids
