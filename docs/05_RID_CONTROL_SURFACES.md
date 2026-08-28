# Remote ID、EID、OPID 与许可控制面

本文件把容易被统称为“Remote ID 开关”的多个独立表面分开记录。范围、版本和脱敏规则见
[范围与脱敏](00_SCOPE_AND_REDACTION.md)。本文件不提供设备控制程序、账号客户端、许可生成器或
可执行写入步骤。

机器索引中的核心对应关系为：generic switch negative `C-009`；France EID static route/semantics
`C-010` / `C-011`；人工 GET negative `C-012`；unavailable rule `C-013`；EASA OPID `C-014`；
Japan DIPS `C-015`；type-6 architecture/eligibility/inventory `C-016`--`C-018`；working-status
`C-019`--`C-023`；localhost observer `C-034` / `C-035`；v0.10 `C-036` / `C-037`；V2.2/V2.3
`C-038` / `C-039` / `C-055`；route epoch 与 quiescence `C-040`--`C-043`；typed EID retry
`C-044`--`C-046`；state model 与历史 corpus `C-056`--`C-059`；EU C0、cloud policy、legacy
inventory、type-6 query/enable、area strategy 与 broadcast-effect `C-071`--`C-078`；stable control
未闭合 `C-053`；中国 OID network-report gate 与 current exact setter re-audit `C-106`--`C-109`。

## 总结矩阵

| Claim | 表面 | 证据状态 | 当前公共结论 |
| --- | --- | --- | --- |
| RID-001 | ordinary Broadcast Remote ID | `NEGATIVE` | 未发现当前跨地区 Boolean 总开关 |
| RID-002 | onboard working status | `STATIC` | `0x11/0x1C` 是 status/push，不是 setter |
| RID-003 | France EID | `STATIC` | `0x03/0x77` 是法国专用 GET/SET schema |
| RID-004 | France EID live artificial routes | `NEGATIVE` | 两个固定 GET 路由均为 unavailable |
| RID-005 | EASA OPID | `STATIC` | `0x03/0x78` 是身份数据 GET/SET/DELETE |
| RID-006 | MSDK area strategy | `STATIC` | development delegate selector，不是实际地区/RF 证明 |
| RID-007 | FlySafe type-6 | `STATIC` | 签名、账号/FC 绑定的 managed license state |
| RID-008 | Mini 5 Pro type-6 entitlement | `UNKNOWN` | 资格、真实许可、FC 接受和 RF 效果均未闭合 |
| RID-009 | EU C0 policy | `NEGATIVE` | live F7 未返回 metadata，未执行 F8/F9 |
| RID-010 | broadcast-effect policy | `NEGATIVE` | live F7 未返回 metadata，bitmap 语义未知 |
| RID-011 | opaque cloud-control V2 | `STATIC` | set-only policy blob，不是稳定 Boolean |
| RID-011A | 中国 OID 云上报 gate | `STATIC/CORROBORATED` | 只控制 App 网络提交并可 direct-success，不控制飞机 RF 广播 |
| RID-012 | localhost observer | `NEGATIVE` | 历史路线已撤回，不得再连接第二 broker client |
| RID-013 | same-owner raw EID GET | `HYPOTHESIS` | 静态候选，当前不具备 live 准入条件 |
| RID-014 | route-only V2.2/V2.3 | `NEGATIVE` | V2.2 撤销；V2.3 修复但仍 zero-send、未准入 |

## 普通 Broadcast Remote ID

### RID-001：未发现跨地区普通 Boolean 总开关

- **证据状态：NEGATIVE**
- **对象/版本：** 当前官方 DJI Fly 1.21.10 native 样本、可读的 DJI Fly 1.21.4 业务层、MSDK
  5.18.0 公开与 retained 路径。
- **前提与路线：** 对 France EID、EASA OPID/C0、Japan DIPS、FAA/US、China OID/UTMISS、
  FlySafe exception 和 legacy/generated key 名进行分面静态检索与 handler/caller/registration 核对。
- **事实：** 找到了多个地区专用 status、identity、policy 和 managed exception 表面，但没有一个
  具有当前 handler、产品注册和 caller 的普通 Boolean master switch 跨越所有这些平面。
- **边界/不证明：** scoped static negative 不证明所有 DJI 产品、未来版本或私有服务端配置永远不存在
  某种控制。它足以否定把现有任一窄表面公开标成 global RID switch。
- **公开依据：** 先前公开研究
  [Remote ID compatibility testing](https://github.com/Sapphire-Rapids/FindUAS/blob/15f331cf68ce93ae444a8e6aff4c5dc1ed90b5cc/docs/REMOTE_ID_COMPATIBILITY_TESTING.md#remote-id-switch-is-not-one-control)，
  DJI 官方 MSDK Remote ID API。
- **隐私/分发：** 只保留符号和高层控制面；不发布 vendor code 或 decompilation output。

### RID-002：`RidWorkingStatusPush` 是状态源

- **证据状态：STATIC**
- **对象/版本：** DJI Fly 1.21.10 native handler 与 MSDK working-state model。
- **前提与路线：** `KeyRidWorkingStatusPush` 映射到 `0x11/0x1C`。
- **事实：** 该命令由飞机 push/status handler 消费；当前恢复到七字节 flags/area/failure 布局。
- **边界/不证明：** 它不是 setter；`isRidNormal` 或 `WORKING` 不证明独立 RF reception。live motors-off
  未见 push 也不证明 unsupported。
- **公开依据：** [状态、账号与限飞层](04_STATE_ACCOUNT_LIMITS.md#remote-id-工作状态)。
- **隐私/分发：** 不保存 raw status payload。

## France Electronic ID

### RID-003：Product-139 France EID 的静态 request/ACK schema

- **证据状态：STATIC**
- **对象/版本：** DJI Fly 1.21.10 product-139/UAV139 native registration 与 MSDK 5.18.0 对照。
- **前提与路线：** FLYC command set `0x03`、command `0x77`；静态 receiver type/index 为
  18/4，即 `0x92`；runtime single-HostID Characteristics 仍可能覆盖 receiver。
- **事实：** GET body 为 `[02]`，SET off/on 分别为 `[00]` / `[01]`。GET canonical ACK 为
  `[protocol_result,state]`，成功后读取 `state & 1`；SET ACK 只含 result。timeout 为 500 ms。
  request layout 中 `uav_cmd_req+0x08` 是 retry，receiver index 位于 `+0x19`。constructor retry
  为 3；静态 product-139 EID Characteristics `+0x30` 初值为 0，因此初始 typed GET 保留 3；
  runtime update 可能使 typed GET 条件式清为 0。typed SET 保留 3。
- **边界/不证明：** 静态 schema 不证明 live route、capability 或 current Characteristics 值。France
  EID 不是 FAA/global RID、EASA OPID、日本 DIPS 或中国 OID 开关。ACK 也不替代后续 GET readback。
- **公开依据：** 前述 compatibility research、DJI 官方 France strategy API；版本纠正由本仓库
  [AGENTS.md](../AGENTS.md)固定。
- **隐私/分发：** 只发布 command/schema；不发布 raw frame、device route identity 或厂商代码正文。

### RID-004：两个固定人工 France EID GET 路由均未得到 canonical ACK

- **证据状态：NEGATIVE**
- **对象/版本：** 当前 Mini 5 Pro / RC 2 实机组合，2026-08-28。
- **前提与路线：** 更正静态 receiver 为 `0x92` 后，对飞机 direct USB 和 RC 2 USB 各发送恰好一次
  clear GET `[02]`；严格匹配 CRC、sequence、reverse route、command 和 canonical payload；无 SET、
  无 retry、无 address scan。
- **事实：** 两条人工路由都没有 canonical `0x03/0x77` ACK，因此公共结果为 `unavailable`。
- **边界/不证明：** 不证明 EID off、不证明 unsupported，也不证明 DJI Fly 私有 in-process owner route
  不可用。没有取得 baseline，任何 SET 仍无依据。
- **公开依据：** 前述 compatibility research；应同时列入
  [否定结果](09_NEGATIVE_RESULTS.md)和[时间线](03_TIMELINE.md)。
- **隐私/分发：** 不保留 raw request/reply、序列号或端口拓扑。

## EASA operator registration / OPID

### RID-005：`0x03/0x78` 是身份数据面，不是广播 Boolean

- **证据状态：STATIC**
- **对象/版本：** DJI Fly 1.21.10 product-139 `OperatorRegistrationNumber` registration。
- **前提与路线：** FLYC `0x03/0x78` 的 String GET/SET action。
- **事实：** action 区分 GET `[02]`、DELETE `[01]` 和经格式校验后的 SET。应用在 SET 前校验完整
  operator registration 格式；GET 返回 result、length 和 data，SET/DELETE 返回 result。
- **边界/不证明：** 这是 EASA OPID identity plane，不是发射 enable、France EID 或 global RID。
  static destination 仍可能被 runtime Characteristics 覆盖；没有进行 live OPID 事务。
- **公开依据：** 前述 compatibility research。
- **隐私/分发：** 不发布示例真实 OPID、私有后缀、完整 payload 或校验输入。任何 fixture 必须使用
  明显合成值。

## MSDK area strategy 与 DJI Fly 内部地区注入

### RID-006：MSDK area strategy 是 development policy selector

- **证据状态：STATIC**
- **对象/版本：** DJI MSDK 5.18.0 `setUASRemoteIDAreaStrategy` 和官方 sample。
- **前提与路线：** supported MSDK 应用选择地区 delegate。
- **事实：** 不同 delegate 分别处理 US status、EU registration/C-class、Singapore/UAE
  registration、Japan registration、China real-name/UOM 和 France EID。retained 逻辑还比较 real
  area，并对 China transition 有额外限制。
- **边界/不证明：** 选择 SDK delegate 不证明飞机 authoritative country、RF transport、packet format、
  O4 regulatory mode 或 power 已改变，也不证明 RC 2 内置 DJI Fly 接受同一 override。
- **公开依据：** DJI 官方 MSDK 文档/sample、前述 compatibility research；实际 region state 见
  [地区与 RF policy](06_REGION_RF_POLICY.md)。
- **隐私/分发：** 无私人数据。

### RID-006A：内部 real-area injection 会跨多个 policy 表面

- **证据状态：STATIC**
- **对象/版本：** 已恢复 DJI Fly 内部 build area-code 逻辑。
- **前提与路线：** internal-only mock country preference 输入 native area manager，再由后台同步至 FC、
  Sky/Ground 及部分 Wi-Fi surface。
- **事实：** 另一个 debug switch 只控制部分同步，并不是 country selector。内部路径可能同时影响
  FlySafe、RID 地区行为、Sky/Ground regulatory policy 和缓存重试。
- **边界/不证明：** 没有 public production UI；未完整恢复 native precedence/update rules。实机 FC/Sky
  闭环没有启用该内部 preference，也没有形成同步 region transaction 或 RF 证据。
- **公开依据：** 前述 compatibility research、
  [地区与 RF policy](06_REGION_RF_POLICY.md#dji-fly-policy-pipeline)。
- **隐私/分发：** 不提供注入或写入步骤。

## FlySafe `RID_UNLOCK`

### RID-007：type-6 是签名、账号/FC 绑定的 managed license

- **证据状态：STATIC**
- **对象/版本：** DJI Cloud API、MSDK 5.18.0、DJI Fly 1.21.10 account-to-FC architecture。
- **前提与路线：** 官方账号资格与 server product capability -> 下载 signed onboard data -> FC serial
  / product / unlock-version 匹配 -> 上传到 FC -> pull inventory -> enable/disable 现有 license。
- **事实：** 官方 schema 定义 `RID_UNLOCK == 6`；level 1 为 European，level 2 为 China。V2、V3、
  V4 选择不同的 signed onboard data 和 wire session。DJI Fly 的 upload-then-enable callback 只在
  upload success 后调用 enable。
- **边界/不证明：** type-6 不是本地 Boolean，不能合成、修改、重放或伪造。静态架构不证明当前
  Mini 5 Pro 有资格、已有真实许可、FC 接受或 enable 后 RF 变化。
- **公开依据：** DJI 官方 FlySafe/Cloud API/MSDK；前述公开
  [state research](https://github.com/Sapphire-Rapids/FindUAS/blob/15f331cf68ce93ae444a8e6aff4c5dc1ed90b5cc/docs/DJI_RC2_STATE_RESEARCH.md#current-official-rid_unlock-account-to-fc-chain)。
- **隐私/分发：** 不发布账号、token、Cookie、FC serial、license ID、signed blob、描述、时间、区域或
  server response 正文。

### RID-008：Mini 5 Pro 的官方 type-6 entitlement 仍未知

- **证据状态：UNKNOWN**
- **对象/版本：** Mini 5 Pro / WA150、当前 FlySafe service 和 live FC session。
- **前提与路线：** 需要官方已登录上下文的 product capability yes/no，以及当前 session 的
  support/version、type-6 inventory、level/valid/enabled baseline。
- **事实：** 公开申请表要求 server row 的 `support_unlock_type` 含 `Rid` 并绑定产品与 FC serial；
  当前没有可公开、可复现的 Mini 5 Pro 资格或真实 type-6 被 FC 接受记录。
- **边界/不证明：** 公开表单存在不等于当前产品有资格。任何 missing/unknown 都必须停止在 no setter。
- **公开依据：** DJI FlySafe current site、RID terms、前述公开 state/firmware research。
- **隐私/分发：** 公共输出仅允许 product row exists yes/no、Rid capability yes/no、version enum 和
  type/level/valid/enabled；license ID 只能在获批实验的进程内短暂存在。

### RID-008A：现代 query / set-enable schema 已静态闭合

- **证据状态：STATIC**
- **对象/版本：** MSDK 5.18.0 native FlySafe implementation。
- **前提与路线：** FC serial -> JNI query -> module mediator -> support/version gate -> V2/V3/V4
  session -> PackProvider。
- **事实：** query `PackType 0x38` 映射到 `0x11/0x11`；set-enable `PackType 0x39` 映射到
  `0x11/0x12`。V2 使用单字节 index；V3/V4 使用 group info/paging 与 protobuf/status parser。
  product/version 可改变 receiver route；runtime product 139 的静态 product-tree fallback 最终选择
  `0x92`，前提是 live runtime product 确认等于 139。
- **边界/不证明：** numeric command 已知不等于可安全 hand-build。support/version push、session owner、
  route、真实许可、readback/restore 和独立 RF 效果仍未实证。
- **公开依据：** 前述公开 state/firmware research。
- **隐私/分发：** 不提供 sender、license ID、signed payload 或可执行 sender。

### RID-008B：旧式固定 inventory request 超时

- **证据状态：NEGATIVE**
- **对象/版本：** 当前 Mini 5 Pro / RC 2 实机组合。
- **前提与路线：** 旧式 hand-built `0x11/0x11` 单 index 请求分别走飞机 direct 和 RC proxy；紧接着
  FC area 与 Sky/Ground country positive controls 成功。
- **事实：** 两条 inventory 请求均无匹配 response。
- **边界/不证明：** 不证明 inventory empty、V2 unsupported 或 link disconnected。可能变量包括
  support/version、session、route、payload 细节或 endpoint；现有材料不能选择其中一个解释。
- **公开依据：** 前述公开 state/firmware research；列入
  [否定结果](09_NEGATIVE_RESULTS.md)和[假设与未知](10_HYPOTHESES_AND_UNKNOWNS.md)。
- **隐私/分发：** 不发布 raw frame 或 license data。

## FC policy 参数与 cloud policy

### RID-009：EU C0 policy 映射存在，但 live metadata 不可用

- **证据状态：NEGATIVE**
- **对象/版本：** DJI Fly 1.21.10 UAV139 registration；当前 Mini 5 Pro live FLYC route。
- **前提与路线：** static key `IsEuCeEnableC0Rid` -> FC parameter
  `EU_CE_enable_c0_rid_0` -> fixed hash -> F7 metadata GET；direct 和 RC-routed plaintext 均测试，
  同 route 的 height/distance 参数为 positive controls。
- **事实：** 两条 live route 都只返回单字节 F7 status `0x03`，未达到 metadata 最小布局；因此未发送
  F8 value GET、F9 write 或 FA reset。
- **边界/不证明：** 不证明 key 不存在于 DJI Fly，也不确定 `0x03` 是 endpoint absence、product/runtime
  gate 或其他 refusal。该字段的 business owner 是 cloud-country + C0 certification policy，不是用户开关。
- **公开依据：** 先前公开
  [firmware research](https://github.com/Sapphire-Rapids/FindUAS/blob/15f331cf68ce93ae444a8e6aff4c5dc1ed90b5cc/docs/DJI_RID_FIRMWARE_RESEARCH.md#current-official-dji-fly-native-boundary)。
- **隐私/分发：** 可记录公开参数名/hash；不发布 raw responses 或 vendor library。

### RID-010：broadcast-effect policy 映射存在，但 bit 语义和 live metadata 未闭合

- **证据状态：NEGATIVE**
- **对象/版本：** DJI Fly 1.21.10 UAV139 registration、当前 Mini 5 Pro live route。
- **前提与路线：** `CccBroadcastSignalQuality` ->
  `ccc_broadcast_signal_quality_0` -> fixed hash -> F7；与 RID-009 相同的 positive-control 设计。
- **事实：** live F7 同样只返回 `0x03`，所以没有 F8/F9。静态业务逻辑把 product-specific bitmap
  与 0--18 signal-quality 值打包，但 bitmap 各 bit 的物理语义未恢复。
- **边界/不证明：** converter 类型不确定 wire width；`0`/`1` 不能被猜成 off/on。静态 mapping 不证明
  live FC 暴露该参数，也不证明它控制普通 RID enable。
- **公开依据：** 前述公开 firmware/state research。
- **隐私/分发：** 不提供写值或 setter。

### RID-011：`dji_fly_rid_cloud_control_v2` 是 opaque set-only policy

- **证据状态：STATIC**
- **对象/版本：** DJI Fly 1.21.10 app/native path。
- **前提与路线：** area/product selector 选择 opaque hex data 或 `DEFAULT`，再封装为 generic
  `CloudControlData` 并通过 command `0xDD` 的 set-only handler 发送。
- **事实：** product 139 以 numeric product value 参与选择；`block_device` 命中会选择 DEFAULT，而不是
  表示 RID off。该 key 没有 GET/listen readback，payload schema、signature rule、WA150 sample 和
  RID status correlation 都未闭合。
- **边界/不证明：** generic `0xDD` 和 receiver tuple 不能识别成 RID switch。不得猜测、重放、持久化
  或公开 opaque blob。
- **公开依据：** 前述公开 state/firmware research。
- **隐私/分发：** 不保存或发布 cloud response、installation identity 或 blob。

### RID-011A：中国 OID report gate 是网络提交开关，不是 RF 开关

- **证据状态：STATIC / CORROBORATED**（C-106--C-108）
- **对象/版本：** 当前精确 DJI Fly `1.21.10` `libsdk_jni.so`；相邻旧 Java 方法体只作
  cloud-policy corroboration。
- **当前 native 入口：** `uav/sdk/oidmgr/UAVOIDManager` 注册
  `native_SetOIDReportEnable(Z)V`、`native_SetSimulatorEnable(Z)V`、
  `native_MockOIDReportStatus(ZZ)V` 及 init/uninit/observer 方法。
- **对象状态：** constructor 将 report gate 默认置 true、simulator/mock gates 默认 false，
  mock result 默认 true。`SetReportEnable`、`SetSimulatorEnable` 和 `MockReportStatus` 只更新
  对象 Boolean；没有找到 gate-state getter。
- **消费语义：** `ShouldReport` 优先处理 mock，其次 simulator，正常状态只读 report gate。
  OID push 解析后，true 进入网络 `Submit`；false 进入 `DirectSuccess`，即跳过网络提交但向
  上层给出直接成功结果。
- **cloud namespace：** 相邻 Java flow 将该 gate 绑定到 `CN_OPERATE_ID_EFFECT`；值精确为
  `"0"` 才关闭，缺失/异常默认开启。它与 `dji_fly_rid_cloud_control_v2` 是不同链路。
- **关键边界：** 这条路径处理中国 OID/UOM 数据的 RC/App 云上报。它不写飞机广播参数，
  不控制 BLE/Wi-Fi RID transmitter，也没有 RF/readback/persistence 证据。因此名字中出现
  OID、report、enable 仍不能把它加入管理员面板的 RF 开关候选。
- **静态入口：** `OIDMgr` constructor `0x25e33f8`、`SetReportEnable` `0x25e57b0`、
  `SetSimulatorEnable` `0x25e5a20`、`MockReportStatus` `0x25e5c90`、`OnOIDPushReceived`
  `0x25e73e8`、`ShouldReport` `0x25e7df0`。RVA 只适用于已登记的 `1.21.10` native 样本。

### RID-011B：当前 exact setter 复查仍没有 global RF Boolean

- **证据状态：NEGATIVE**（C-109）
- **范围：** 当前 `1.21.10` native function/name/registration paths 中的
  EID broadcast/open/close、Remote ID、ODID、OpenDroneID 和 switch/setter 组合，以及 MSDK
  `setBroadcastRemoteIdEnabled`、generic cloud-reset 和既有 product-139 policy 路线。
- **结果：** 当前 native 只有已知 France `EIDSwitchGet/Set` wrapper 与 RemoteIDHelper 输入校验；
  没有可识别的 product-139 `EIDBroadcastEnable`、EID open/close、ODID/OpenDroneID 或 global RF
  setter handler。MSDK America `setBroadcastRemoteIdEnabled` 只改状态 DTO，不发设备 SET；
  `ResetCloudControlSetting` 的已知业务 caller 属于云端速度限制恢复，不是 RID reset。
- **边界：** 该阴性只覆盖当前可读 app/native surfaces。WA150 现有输入仍是加密 `.fw.sig`，
  因此不能据此断言固件内不存在隐藏 owner 或 setter。

## 观察路线、撤回与未准入设计

### RID-012：历史 localhost observer 路线已撤回

- **证据状态：NEGATIVE**
- **对象/版本：** 历史 observer v0.1--v0.4；相邻 RC331 `10.00.0700/0205` framework。
- **前提与路线：** observer 作为第二 TCP client 连接 RC-local `40007`/`40009`，即使没有 output
  stream 或 payload write。
- **事实：** 相邻官方 `dji.json` / framework 表明这两个 endpoint 默认只有一个 active accepted fd；
  newcomer 可以关闭并替换旧 fd。连接本身可能中断 DJI Fly，因此 v0.1--v0.4 的 live 使用已撤回。
- **边界/不证明：** exact live v07 framework 尚未取得；由于风险非对称，未知不能用来承担飞控链路
  中断风险。历史 parser/tests 只保留 offline value。
- **公开依据：** 前述 compatibility/state research；当前 correction 见本仓库
  [AGENTS.md](../AGENTS.md)。
- **隐私/分发：** 不发布历史 raw broker traffic；不得安装、启动或恢复该 observer 流程。

### RID-012A：v0.10 只是一项环境准入探针

- **证据状态：STATIC**
- **对象/版本：** `com.finduas.ridobserver` v0.10，SHA-256
  `fdad29bfb1237bc224a805d6eb5a99358a044bd226610d9f0fc33975d94b606c`；完整 identity/disposition
  见[工件登记册](11_ARTIFACT_REGISTER.md)。
- **前提与路线：** offline manifest/DEX/signature/zipalign、测试、对抗变异和 deterministic-build 审计。
- **事实：** v0.10 请求零权限，无 service/receiver/provider/socket/DUML/应用 Binder transaction、
  process execution、persistence、network send、packaged native library 或 attach/load 路径；它只采集
  环境 inventory 和自身进程映射的 ART identity。
- **边界/不证明：** 尚未复制、安装或运行于 RC 2；即使环境 match 也不证明 RID state、EID route、
  transaction authorization 或 RF behavior。
- **公开依据：** 本仓库 AGENTS correction、前述 compatibility research。
- **隐私/分发：** 仓库只登记 hash/size/audit/disposition，不分发 APK，不记录 live inode/path/maps。

### RID-013：same-owner raw France-EID GET 是未执行候选

- **证据状态：HYPOTHESIS**
- **对象/版本：** DJI Fly 1.21.10 `JNIRawData.native_SendData` 静态 path。
- **前提与路线：** 复用已初始化的 ProductMgr/RawMgr/SessionMgr 和 callback，在同 owner 内构造
  France EID GET；候选实验 profile 为 selector 3、retry 0、timeout 500、body `[02]`。
- **事实：** 静态 path 能返回 raw ACK application payload，因此理论上可保留
  `[protocol_result,state]`，不需要第二 broker socket 或 observer-map mutation。
- **边界/不证明：** 尚未 live-admitted 或发送。retry 0 是有意的单发实验 profile，不是 typed GET
  当前 runtime retry policy。live productId/deviceId/senderIndex/HostID、product139/France/EID identity、
  ClassLoader、whole-file identity、route epoch、callback quiescence 均未闭合；不得与 typed GET 并行。
- **公开依据：** 前述 compatibility/state research；阻断项见
  [当前阻断点](12_CURRENT_BLOCKERS.md)。
- **隐私/分发：** 不发布 live identifiers、raw callbacks 或可执行 sender。

### RID-014：route-only V2.2 已撤销，V2.3 仍未准入

- **证据状态：NEGATIVE**
- **对象/版本：** work-only route resolver V2.2，SHA-256
  `7aa794ff8611582fd7cf27808a9d9eb11c44e307889d615d0511c100522845fb`；V2.3，SHA-256
  `49d5d1d3b6e2dcb72b23f48b688effb2be3f320bec6997a9dcb15779904156c2`；artifact identity 由
  [工件登记册](11_ARTIFACT_REGISTER.md)规范化。
- **前提与路线：** exact final-artifact static review；两个版本均为 zero-send route-only 设计。
- **事实：** V2.2 因两个 P1 与一个 P2 缺陷永久拒绝。V2.3 修复已记录的三项缺陷，但仍固定零
  exception gate、zero-send、未执行，且没有新的独立 post-fix audit 报告。
- **边界/不证明：** 修复已知缺陷不等于 whole-file live identity、exception safety、route atomicity、
  callback lifetime 或 GET capability 已闭合；不得安装、attach 或据此发送。
- **公开依据：** 本仓库 [AGENTS.md](../AGENTS.md) 的 current corrections；详细 disposition 见
  [工件登记册](11_ARTIFACT_REGISTER.md)和[当前阻断点](12_CURRENT_BLOCKERS.md)。
- **隐私/分发：** 只发布 hash、审计状态和处置；不分发工件或 vendor target material。

### RID-015：固定延迟和 callback return 不能证明 request quiescence

- **证据状态：STATIC**
- **对象/版本：** DJI Fly 1.21.10 raw-send callback/pending/cancel lifecycle。
- **前提与路线：** 静态审计 ACK、timer、pending erase、callback-owner destruction、Stopper removal 和
  asynchronous cleanup 顺序。
- **事实：** ACK callback 可发生在 pending-node erase 前；timer callback 可发生在 copied owner
  destruction 前；cancel return 不证明 core cleanup 已结束。固定 100 ms quiet window 已被否定。
- **边界/不证明：** 当前没有 exact pending/Stopper membership、in-flight zero、stable lifecycle/epoch
  与 worker-tail fence 的完整证明，因此任何 raw GET 仍不能进入 live execution。
- **公开依据：** 前述 compatibility/state research、本仓库 AGENTS correction。
- **隐私/分发：** 只记录状态机关系，不发布 vendor disassembly。

### RID-016：Drone-Hacks CFC 是架构先例，不是 Mini 5 Pro RID 实现

- **证据状态：STATIC / NEGATIVE / UNKNOWN**
- **对象/版本：** Drone-Hacks `2.0.29` 客户端、2026-08-28 公开兼容性快照与 CFC 文档。
- **事实：** 客户端直接 `dhfc_config` 只有 FCC、NFZ、高度；公开 CFC 命令覆盖 FCC、LED、
  ATTI、NFZ、高度，支持清单不含 Mini 5 Pro，且未文档化 RID。通用 DUSS 名称表虽出现
  ADSB RID/EID 标签，但没有数值、schema、caller、product gate、readback 或 live job。
- **边界/不证明：** server job engine 的能力、`wa150` 型号登记和独立 FCC ModBox 兼容均不
  等于 Mini 5 Pro 软件/CFC/RID 支持。
- **可借鉴：** 若未来闭合 WA150 authoritative owner，可采用“固件内窄 hook + 显式状态/readback
  + stock restore + 独立 RF A-B-A”的架构；当前没有 flash 准入。
- **公开依据：** [Drone-Hacks 静态分析](17_DRONE_HACKS_STATIC_ANALYSIS.md)。

## 当前判定规则

1. 不得把 France EID、OPID、MSDK area strategy、C0 policy、broadcast-effect policy、cloud blob 或
   FlySafe license 中任一项命名为“通用 Remote ID 开关”。
2. `unavailable`、timeout、missing push 和 converter `false` 不得改写成 off/unsupported/empty。
3. 许可类证据必须保持 account/server entitlement、signed blob、FC import、inventory、enable state、
   restore 和独立 motor-on RF observation 的链式边界。
4. 任何未来 GET 必须复用官方 owner 或证明不会替换 DJI Fly active fd；不得重新连接
   `40007`/`40009`。
5. 任何未来 SET 都必须有 baseline、单次 forward、严格 GET readback、bounded restore、final readback
   和独立 RF 验证；本文没有给出任何已准入 SET。
6. 新假设先进入[假设与未知](10_HYPOTHESES_AND_UNKNOWNS.md)，新失败进入
   [否定结果](09_NEGATIVE_RESULTS.md)，完成门禁状态同步到[交接](13_HANDOFF.md)。
