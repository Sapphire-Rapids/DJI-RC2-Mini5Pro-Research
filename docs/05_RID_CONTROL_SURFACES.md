# Remote ID、EID、OPID 与许可控制面

本文件把容易被统称为“Remote ID 开关”的多个独立表面分开记录。范围、版本和脱敏规则见
[范围与脱敏](00_SCOPE_AND_REDACTION.md)。本文件不提供设备控制程序、账号客户端、许可生成器或
可执行写入步骤。

机器索引中的核心对应关系为：generic switch negative `C-009`；France EID static route/semantics
`C-010` / `C-011`；人工 GET negative `C-012`；unavailable rule `C-013`；EASA OPID `C-014`；
Japan DIPS `C-015`；type-6 architecture/eligibility/inventory `C-016`--`C-018`；working-status
`C-019`--`C-023`、current owner/route `C-115`--`C-118`；localhost observer
`C-034` / `C-035`；v0.10 `C-036` / `C-037`；V2.2/V2.3
`C-038` / `C-039` / `C-055`；route epoch 与 quiescence `C-040`--`C-043`；typed EID retry
`C-044`--`C-046`；state model 与历史 corpus `C-056`--`C-059`；EU C0、cloud policy、legacy
inventory、type-6 query/enable、area strategy 与 broadcast-effect `C-071`--`C-078`；stable control
未闭合 `C-053`；中国 OID network-report gate 与 current exact setter re-audit `C-106`--`C-109`；
legacy DroneID Detection `C-119`--`C-122`；地区身份/位置 `C-123`--`C-128`；China UOM
reply/status/admission `C-130`--`C-132`；动态 RID bundle 与 namespace `C-133` / `C-134`；
AirSense 候选排除 `C-135`；独立 `RIDCtrlEnable` 特征与 FC 参数链 `C-136`--`C-138`；
同族配置全量盘点与公开先例阴性 `C-139` / `C-140`。
`rid_ctrl_enable_0` 两条 direct F7 实机结果为 `C-141`；exact current official owner、type-6
Java incompatibility 与 generic existing-ID switch 为 `C-183`--`C-187`。

## 总结矩阵

| Claim | 表面 | 证据状态 | 当前公共结论 |
| --- | --- | --- | --- |
| RID-001 | ordinary Broadcast Remote ID | `NEGATIVE` | 未发现当前跨地区 Boolean 总开关 |
| RID-002 | onboard working status | `STATIC` | product-139 RID module 监听 `0x11/0x1C`；无 GET/SET/action |
| RID-002A | dynamic RID characteristic bundle | `STATIC` | function-discovery ID `0x37` 准入九项 mixed-access inventory；live admission 未知 |
| RID-002B | AirSense/ADS-B lookalikes | `STATIC/NEGATIVE` | `0x11/0x0C`、`0x11/0x37`、`0x11/0x39` 均为非 RID 表面 |
| RID-002C | independent `RIDCtrlEnable` | `STATIC/NEGATIVE` | same-family mapping exists; C-230 closes positive-controlled absence on the tested Mini 5 Pro FLYC surface |
| RID-003 | France EID | `STATIC` | `0x03/0x77` 是法国专用 GET/SET schema |
| RID-004 | France EID live artificial routes | `NEGATIVE` | 两个固定 GET 路由均为 unavailable |
| RID-005 | EASA OPID | `STATIC` | `0x03/0x78` 是身份数据 GET/SET/DELETE |
| RID-005A | Japan DIPS | `STATIC` | `0x11/0x4B` 是三段受管理登记凭据，不是 Boolean |
| RID-005B | China UOM identifier | `STATIC` | `0x11/0xD6` tag route/reply 已闭合；live baseline/RF 未闭合 |
| RID-005B2 | China UOM real-name status | `STATIC/UNKNOWN` | 条件 `0x11/0xD1` getter + account/network Sync；无 setter，live admission 未知 |
| RID-006 | MSDK area strategy | `STATIC` | development delegate selector，不是实际地区/RF 证明 |
| RID-007 | FlySafe type-6 | `STATIC` | 签名、账号/FC 绑定的 managed license state；current Java UI 不能语义识别 type 6 |
| RID-008 | Mini 5 Pro type-6 entitlement | `UNKNOWN` | 资格、真实许可、FC 接受和 RF 效果均未闭合 |
| RID-009 | EU C0 policy | `NEGATIVE` | live F7 未返回 metadata，未执行 F8/F9 |
| RID-010 | broadcast-effect policy | `NEGATIVE` | live F7 未返回 metadata，bitmap 语义未知 |
| RID-011 | opaque cloud-control V2 | `STATIC` | set-only policy blob，不是稳定 Boolean |
| RID-011A | 中国 OID 云上报 gate | `STATIC/CORROBORATED` | 只控制 App 网络提交并可 direct-success，不控制飞机 RF 广播 |
| RID-012 | localhost observer | `NEGATIVE` | 历史路线已撤回，不得再连接第二 broker client |
| RID-013 | same-owner raw EID GET | `HYPOTHESIS` | 静态候选，当前不具备 live 准入条件 |
| RID-014 | route-only V2.2/V2.3 | `NEGATIVE` | V2.2 撤销；V2.3 修复但仍 zero-send、未准入 |
| RID-017 | legacy OcuSync DroneID mask | `STATIC/NEGATIVE` | `0x03/0xDA` 只提供旧协议字段 mask；不停止包且无 WA150 证据 |

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
- **对象/版本：** 精确 DJI Fly 1.21.10 `libsdk_jni.so` product-139 native route 与 MSDK
  working-state model。
- **owner 闭环：** product-139 主 abstraction 的 `PrepareModules` 构造并挂载
  `RidImportModule`；其 `Setup` 注册 `adsb_push_rid_working_status_pack`，绑定
  `OnRIDWorkingStatusPush`，并建立 `KeyRidWorkingStatusPush`。该 Characteristic 为
  listen/update-only：没有 getter、setter 或 action。
- **wire/route：** observer 注册值为 `0x4011001C`，其中命令组/命令为 `0x11/0x1C`，其余高位是
  observer flag。注册使用 runtime data-link/device identity；product-139 不启用额外 sender-sequence
  比较。因此静态证据没有给出一个可安全 hand-build 的固定 sender/receiver tuple。
- **payload：** handler 把七字节映射为 bit 0 `isRidSupport`、bit 1 `isEidSupport`、bit 8
  `isRidNormal`、bit 9 `isEidNormal`、`int32le(payload+2)` area code 和 `payload[6]` failure
  value。最后一项同时写入旧拼写 `failResion` 与修正后的 `failReason`。该 handler 只检查
  response/payload 非空，未见长度门禁；自写 parser 必须自行严格要求七字节最小长度，并保留
  trailing bytes。七字节是官方函数消费的最小前缀，不是 wire 永远恰好七字节的证明（C-147）。
- **地区支持派生：** product-139 注册 US=`bit0`、Cloud=`bit10`；EU/France/Japan 为向后兼容的
  default-true 解释：只有 bit10=1 且相应 bit11/13/12=0 时才为 false。五个 Java key 都是
  GET+LISTEN、无 SET，只由同一 push 更新。China 不在这组 support bit 中，属于独立
  OID/UOM/UTMISS 平面。bits 8/9 仅经完整状态模型暴露，其余未命名 bit 没有找到业务 consumer。
- **边界/不证明：** 它不是 setter；`isRidNormal` 或 `WORKING` 不证明独立 RF reception。live motors-off
  未见 push 也不证明 unsupported。由于没有 GET builder，它也不是可主动轮询的 read-only query。
- **live third-party Binder result：** A-024 的 transaction-2 listener 在 9 ms 内被 framework 接受，
  完整运行 30,000 ms，但 callback、有效帧与异常帧均为 0。操作者在窗口内正常起桨，同一实验的
  独立检测设备确认飞机确实播报 RID。因此该 listener 对本设置是**假阴性**，不能再作为控制面板
  readback oracle，也不能用“零回调”否定 RF。它不否定 DJI Fly 自己的 in-process observer 或
  其他 onboard health 源（C-146）。
- **公开依据：** [状态、账号与限飞层](04_STATE_ACCOUNT_LIMITS.md#remote-id-工作状态)。
- **隐私/分发：** 不保存 raw status payload。

### RID-002A：`RidCaptureV1` 是动态准入的九项 mixed-access bundle

- **证据状态：STATIC**（C-133、C-134）
- **对象/版本：** 精确 DJI Fly 1.21.10 `libsdk_jni.so` 的 `RidCaptureV1` registration 与
  `CommonFcAbs` function-discovery callback。
- **准入事实：** callback 原始 function ID `0x37` 构造并绑定 `RidCaptureV1`；相邻 ID `0x38`
  构造的是 `UnofficialBatteryAuthenticationV1`。SDK 的 `0x00/0xB8` 是通用 function-discovery
  transport，不是 RID 专属 GET。它们又都不同于 `0x11/0x37` ADSB command 与 FlySafe
  `PackType 0x38`。
- **九项 inventory：** 四个 listen-only capability 是 `IsCloudRIDSupported`、
  `IsEURidSupported`、`IsFREidSupported`、`IsJapaneseRidSupported`；Japan 平面包含
  `RIDRegistedInfo` action 与 `RIDImportResult` getter；`OperatorRegistrationNumber` 和
  `EIDSwitch` 为 GET+SET；`UploadMobileDevicePosition` 为 SET-only。
- **边界/不证明：** 这是四项只监听、一个 action、一个 getter、两个 GET+SET 与一个单向上传的
  混合包，不是九个可写设置，也没有提供 US/global Broadcast RID Boolean。静态 product-139
  身份不证明 live Mini 5 Pro inventory 已报告 ID `0x37`，缓存 replay 也不能替代当前会话准入。
- **UI 处置：** 在读取 official same-owner runtime inventory/key-existence 前，九项均保持
  `STATIC LOCKED`。任何静态可写项仍需 baseline、规范 ACK、独立 readback、restore、persistence
  与起桨后独立 RF A-B-A；位置流没有设备侧 baseline/readback，必须单独作为隐私敏感遥测输入。
- **隐私/分发：** 只发布名称、access type 与边界；不发布 identity、credential、coordinate、
  raw inventory 或 decompilation output。

### RID-002B：三个 current ADSB/AirSense tuple 不是 RID 配置

- **证据状态：STATIC**；对 RID attribution 为有界 `NEGATIVE`（C-135）。
- **`0x11/0x0C`：** product-139 当前注册的 AirSense/ADS-B traffic receive enable，具备 GET、
  SET 与读回；它控制接收侧告警业务，不是飞机 Broadcast RID transmitter。
- **`0x11/0x37`：** 从 UAV77 混入 product-139 的 `ADSBSwitch`，具备 GET、SET 与读回，但当前
  业务层没有 RID、DIPS 或 EID caller。此处 `0x37` 是 command ID，绝不能与 RID function ID
  `0x37` 混为一谈。
- **`0x11/0x39`：** AirSense synthetic-target test action，写入位置、速度与角度测试数据，无
  配置 GET/readback；它向接收告警链注入合成交通目标，不向外广播 RID。
- **其他词典候选：** current exact typed/key/UI surface 对 `0x11/0x05`、`0x06`、`0x0F`、
  `0x1A`、`0x35` 均未找到完整 ctor、handler、registration、caller 与 product-139 admission。
- **边界/不证明：** current application attribution 不证明 WA150 firmware 必然拒绝所有 raw
  request，也没有闭合 `0x11/0x37` 的 live RF 副作用。它足以把这三项永久排除出 RID 配置 UI；
  后续只允许被动 trace 或在单独 AirSense 研究中重新建证据。
- **隐私/分发：** 未执行上述 command；不保留 flight ID、测试坐标或 raw packet。

### RID-002C：独立 `RIDCtrlEnable` 已闭合到固定 FC 参数

- **证据状态：STATIC/OBSERVED/NEGATIVE**（C-136--C-145、C-227/C-230）
- **对象/版本：** 官网当前 SKYROVER `1.2.0`，package `com.sky.dronemaster`。输入 APK
  SHA-256 为 `8f5590f5f61194b186ac8e4a670e5b2182551a653eda2bb0c0ce23b696c554b8`；
  只在排除工作区静态分析，不在本仓库分发。
- **高层特征事实：** `RIDCtrlEnable` 是 Boolean，支持 GET、SET、Listen，且与
  `EIDSwitch`、`OperatorRegistrationNumber` 分开注册。应用在飞机连接后执行新的 GET：成功才
  显示开关，参数 GET 错误则隐藏，其他错误会重试。因此这是运行时能力探测，不是硬编码机型或
  地区清单。
- **native/transport 事实：** KeyValue `RIDCtrlEnable` 映射到 FC 参数
  `rid_ctrl_enable_0`。其 DJI hash 为 `0x3CBD864F`，wire little-endian 为
  `4F 86 BD 3C`。命令族是 FLYC metadata `0x03/0xF7`、read `0x03/0xF8`、write
  `0x03/0xF9`；静态 default route 为 app type/index `2/4` (`0x82`) 到 FC type/index
  `18/4` (`0x92`)。F7 回包是 value type/width 的实机权威来源。
- **与 France EID 的区别：** 该链不是 `0x03/0x77` France `EIDSwitch`，也不是
  `0x11/0x1C` listen-only RID health push。它是目前找到的第一个名称、Boolean 高层语义、底层
  固定参数、GET/SET 和应用 UI 行为能够连成一条链的独立 RID control candidate。
- **Mini 5 Pro 当前边界：** 精确 DJI Fly `1.21.10` native 未出现同名 KeyValue/FC parameter；
  单凭静态缺名不能证明飞控无参数。后续 C-230 已在正对照成功的 `01.00.0600` direct-USB
  FLYC 表面闭合 absence，不再把相同 F7/F8 当作待执行判别；其他 owner/表面仍须新证据。
- **live positive-controlled absence（2026-08-30，C-230）：** 本次 aircraft-direct `0x0A -> 0x03`
  同 session 正对照 `max_height_0` 成功；`rid_ctrl_enable_0`(`0x3CBD864F`) F7 返回单字节
  `0x03`，且 by-index 全表 915 个具名参数无 `rid_ctrl_enable` 行。因此该参数在实机 FC 上
  为 positive-controlled absence（direct-USB FLYC route），不是 route 失败。
- **direct live result：** 2026-08-28，同一当前会话中，RC 2 routed `0xAA -> 0x03` 与
  aircraft-direct `0x0A -> 0x03` 对该 hash 的 F7 都返回 canonical one-byte `03`；RC 2
  height/distance/distance-enable 与 aircraft height 正对照均成功返回 F7 metadata 和 F8
  value。直接把 static modern `0x82 -> 0x92` 用到 USB 时，目标和已知 height control 都无
  response，因此该 timeout 只否定 direct-USB route，不回答 Binder route。未发送 F8/F9。
- **Binder live result：** A-023 首次证明第三方 APK 可完成 service lookup、manager
  transaction 与 callback exception layer，但 target F7 约 3.1 秒后返回 `ECode 1`。A-024
  随后先发送 known maximum-height F7：legacy `0A:05 -> 03:00` 与 modern
  `02:04 -> 12:04` 两条 Binder route 都在约 3.1 秒后返回同一 `ECode 1` 且无 data。精确代码
  因两个正对照失败而停止，target F7、F8、F9 均未发送，按钮保持锁定。adjacent RC331
  `ActQueue` 将 `ECode 1` 映射为重试耗尽。电机未启动不是该配置路由实验的解释变量。
- **同族全量盘点：** RID 命名的 FCConfig `_0` 参数只发现 `rid_ctrl_enable_0`。其他真实
  writable 面均属于专用协议：France EID `03/77`、OPID `03/78`、Japan registration
  `11/4B`，以及无 GET/readback、schema 不公开的 `odm_rid_cloud_control -> 00/DD` opaque
  policy。`RidWorkingStatusPush`、地区 support、import result 与 compliance identity 都是只读；
  catalog-only `EidOpen`/`EidClose`/`EIDBroadcastEnable` 没有 current caller/native handler。
- **公开实现检索：** fixed-revision GitHub 项目及 exact-string indexes 未找到第二份
  `RIDCtrlEnable`/`rid_ctrl_enable_0` 的 Mini 5 Pro/RC 2 实现；2026-08-30 的社区调查
  （FreeFCC/djiparam/GlassFalcon/O4 研究）同样未找到第二份 global-RID Boolean 实现，且
  public wa150 参数表没有 `rid_ctrl_enable_0` 行（C-221/C-222）。FreeFCC 只独立支持 modern
  `0x82` transport、`0x92` destination 和 `03/F9` 形式；其 feature/hash 不同，不能当 RID
  接受证据。公开 MSDK V5 有区域 strategy 与 status getter，但普通 RID 没有 enable setter，
  只有 France EID 暴露 setter。
- **实现状态：** clean-room Android A-024 `0.4.1-research` 串行执行、正对照门禁和写入门禁均
  已在实机按预期工作；没有 target request 或 write 泄漏。它的完整 30 秒本地 `0x11/0x1C`
  listener 已由独立 RF 对照判定为假阴性，不再列为核心 readback 路径。
- **当前结论：** current direct legacy routes 对 target 已是 positive-controlled negative；raw
  modern USB route 与两条第三方 Binder route 均无法通过 known-height positive control。因此
  不再重复 generic F7/F8 attach 或仅改变 sender/receiver 的盲试。只有发现 official in-process
  owner、已验证的新 route，或取得 WA150 plaintext handler 后才重开该 exact parameter。
- **下一步：** 先闭合可信只读 RC 2 identity、caller/target policy 和合法 loader/descriptor，
  再作一次 official query-only inventory；只有真实 canonical type-6 基线才可追踪其 enable
  state 到 `NO_BROADCAST`/0802 policy owner 的因果链。不要重复
  protocol-Binder `0x11/0x1C` listener。任何未来控制点仍须 baseline/readback/restore 和独立
  RF A-B-A。
- **隐私/分发：** 只公开固定参数事实、self-developed APK hash 和脱敏结果；不提交 SKYROVER
  APK、shared library、反编译输出、设备标识或 raw private capture。

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

- **证据状态：STATIC**（C-014、C-124）
- **对象/版本：** DJI Fly 1.21.10 product-139 `OperatorRegistrationNumber` registration。
- **前提与路线：** FLYC `0x03/0x78` 的 String GET/SET action。
- **事实：** product-139 注册完整 GET/SET/listen String characteristic。action 区分 GET `[02]`、
  DELETE `[01]` 和 SET `[00][0x10][16-byte data]`。SDK 在发送前要求 20 字符，校验前三位地区码
  与 mod-36 校验位，但 wire 只携带前 16 字节。GET ACK 为 `[result,len,data...]`，SET/DELETE
  ACK 为 `[result]`。
- **边界/不证明：** 这是 EASA OPID identity plane，不是发射 enable、France EID 或 global RID。
  receiver 使用 dynamic HostID，当前 tuple 仍为 `UNKNOWN`，不得硬编码。没有进行 live OPID
  事务，重启持久性和 RF 字段均未验证。
- **公开依据：** 前述 compatibility research。
- **隐私/分发：** 不发布示例真实 OPID、私有后缀、完整 payload 或校验输入。任何 fixture 必须使用
  明显合成值。

### RID-005A：Japan DIPS 是三段凭据，不是普通配置 Boolean

- **证据状态：STATIC**（C-125）
- **对象/版本：** exact DJI Fly 1.21.10 product-139 `RIDRegistedInfo` action / result listen。
- **事实：** command 为 `0x11/0x4B`。注册代码为 30 hex -> 15 bytes（20-byte slot），shared key
  为 32 hex -> 16 bytes，nonce 为 12 hex -> 6 bytes；SET 与 QUERY 均分三阶段，DELETE 实际是
  对三段执行全零 SET。QUERY ACK 为 `[status,len,data...]`。
- **边界：** 这是日本登记凭据导入/持久存储面。它非原子、含敏感 secret，且未闭合 Mini 5 Pro
  接受、重启持久性或 RF 效果。账号/H5 只辅助取得凭据，未找到以本地 login Boolean 作为 wire
  setter gate 的证据。
- **处置：** 公共 UI 只允许 masked present/absent/unknown；不得记录 key/nonce、开放编辑/删除或
  逐段尝试。

### RID-005B：中国 UOM/OIDIdentifier 是八位实名标签面

- **证据状态：STATIC**（C-123、C-130）
- **对象/版本：** exact DJI Fly 1.21.10 product-139 `OIDIdentifierGet/Set` String characteristic。
- **事实：** command 为 `0x11/0xD6` `china_uom_realname_tag`；`0x11/0xD5` 是 OID publish push，
  不是 setter。product-139 registration 没有 HostID ExtraParam，receiver 固定为 type/index 18/4
  (`0x92`)，timeout 500 ms、retry 3；只有缓存 ProductType 为 `0x70` 的其他产品分支才改为
  index 0。SET 为 18 bytes：`[01][03 if empty else 01][16-byte field]`，其中最多复制输入前
  8 bytes，field 其余位置补零。GET 同样分配 18 bytes，但 current builder 只明确写入前缀
  `[01,02]`，后 16 bytes 没有可见初始化；旧 UI 拓扑把输入约束为八位数字。
- **ACK/parser：** SET 与 GET 都从 response byte 1 取得 result；成功 GET 从 bytes 2--9 构造
  恰好八字节的值。byte 0 语义仍未知，vendor lambdas 没有长度门禁；独立 parser 至少要求
  SET ACK 2 bytes、GET ACK 10 bytes。不得把未知 GET tail 写成“官方固定零填充”。
- **边界：** baseline、live ACK、restore、persistence 和 RF 映射仍未闭合。它是中国 UOM 实名
  标签，不是 EASA OPID、普通 ASTM Basic ID 或 global RID switch。
- **处置：** exact static schema 足以设计严格、掩码的未来只读诊断，但当前应用仍没有 admitted
  live owner；不得实现编辑器。未来任何 GET builder 都必须确定性清零未定义 tail，而不是复制
  vendor 的未初始化行为。

### RID-005B2：中国 UOM 实名状态是条件加载的认证链，不是开关

- **证据状态：STATIC**（C-131、C-132）
- **direct getter：** `UOMRealNameStatusGet` 使用 `0x11/0xD1`、receiver type/index 2/0、request
  `[01,00]`、timeout 500 ms、retry 3，不读取 HostID override。成功解释至少要求 4 bytes：先由
  外部 helper 映射 byte 0，随后要求 bytes 1/2 为 `1/1`，再把 byte 3 映射为未认证、有效认证、
  已取消、认证后取消、不支持或未知。当前 library 不包含两个外部 mapping body。
- **runtime admission：** `UOMV1` 只在 common FC runtime function discovery 接纳 function ID
  `0x6C` 且相应 flag 为 1 后创建；这时才注册 `UOMRealNameStatus` getter 和
  `SyncUOMRealNameStatus` action。静态 product-139 身份不能证明 live Mini 5 Pro inventory 已接纳。
- **sync boundary：** exact helper chain 已闭合为服务端中介流程：先收集设备参数，经中国区
  DeviceCenter 账号/实名校验取得服务端结果，再通过同一 D1 aircraft lane 应用一段 opaque
  server-derived state；最终 device check response 才形成同步结果。官方 cancel action 同样先等
  服务端成功，再发起 D1 cancellation synchronization。
- **边界：** 这不是任意本地 setter。sync/cancel 都依赖 official account-server state；cancel
  也不是离线 restore。live `0x6C` admission、认证结果、最终 applied readback、重启持久性和
  Broadcast RID/RF 影响均未闭合；key 未加载必须与返回 `UNSUPPORTED` 分开显示。
- **处置：** 只允许在官方 runtime key 已存在时显示脱敏枚举状态；不得把 Sync 或 cancel
  包装成 RID 广播开关、离线配置或可逆事务。

### RID-005C：位置、UAS ID 与电话必须分面解释

- **证据状态：STATIC / NEGATIVE**（C-126--C-128）
- **操作手位置：** exact `AppLocationUploadLogic` 约每 500 ms 取 client location，拒绝越界和
  `(0,0)`，按 lat/lon × 1e6、alt × 100 和 timestamp 编码，经 `0x11/0x43`
  `app_update_pos_enc` 送往设备。它证明 app-location -> device 数据面，但尚不能证明字段最终进入
  WA150 Broadcast RID RF。
- **飞机/UAS ID：** current `ComplianceSerialNumber` 是 get/listen-only characteristic，未找到 SET；
  当普通 SerialNumber 恰为 14 字符时，exact 逻辑派生 `1581F + 14-char SN + 0` 的 20 字符
  compliance form，否则沿用原值。该格式高度符合 compliance Basic-ID candidate，但是否等同 WA150
  RF Basic ID 未闭合。`JNI_SetUASId -> SetUtmissUASId` 属中国 UTMISS/app reporting，不是
  product-139 飞机广播 key。
- **电话：** `LteUserPhoneNumberSet` 是 LTE HYBRID 业务的 set-only `0x03/0xDA` 子命令，无 GET/
  readback；caller 定期上报经绑定/加密的手机号。它与 RID 无关，不能解释或实现为 operator-phone
  RID 配置。普通标准 Broadcast RID 也没有登记电话 message element。
- **隐私/处置：** 只显示权限/fix age/accuracy 或 masked identity；不显示原始坐标、电话、完整序列号，
  不提供坐标/电话写入。

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
  upload success 后调用 enable。官方 Cloud API FlySafe 文档进一步给出设备侧启停方法
  `unlock_license_switch`（`license_id` + `enable` bool，reply 返回 `result` + `license_id`）与
  `unlock_license_list`（`common_fields.type` 值 6 为 “RID unlocking”，`rid_unlock.level` 1=EU
  RID unlocking、2=China RID unlocking）（C-204）。官方 MSDK 5.8.0 也定义 `RidUnlockType`
  （EUROPEAN/CHINA）与 `FlyZoneLicenseInfo.getRidUnlockType()`，并用通用
  `setFlyZoneLicensesEnabled(info, isEnabled, callback)` 启停一条已拉取的 license（C-205）。
- **控制语义：** MSDK 5.18 保留的 `DefaultUASDelegate` 实现只在 license type 为
  `RID_UNLOCK`、`enabled=true`、level 与当前 area strategy 匹配时派生
  `isRidLicenseOpened=true`：level 1 只匹配 European，level 2 只匹配 China。若产品构造 gate
  `isRidLicenseSupport` 也为 true，`updateRemoteIDStatus()` 直接输出
  `broadcastRemoteIdEnabled=false`、state `NO_BROADCAST`，跳过普通地区状态计算（C-148）。这使
  type-6 成为目前最直接的“许可启用 -> 免播报”设计证据；US/FAA 没有对应 level。该 supplied
  class 有 leading-return 保护布局，所以仍须 current Mini 5 Pro dynamic/RF 证明。
- **边界/不证明：** type-6 不是本地 Boolean，不能合成、修改、重放或伪造。静态架构不证明当前
  Mini 5 Pro 有资格、已有真实许可、FC 接受或 enable 后 RF 变化。
- **公开依据：** DJI 官方 FlySafe/Cloud API/MSDK；前述公开
  [state research](https://github.com/Sapphire-Rapids/FindUAS/blob/15f331cf68ce93ae444a8e6aff4c5dc1ed90b5cc/docs/DJI_RC2_STATE_RESEARCH.md#current-official-rid_unlock-account-to-fc-chain)；
  官方 Cloud API FlySafe 文档（`unlock_license_switch`/`unlock_license_list`，type 6 + `rid_unlock.level`）
  与 MSDK 5.8.0 `RidUnlockType`/`setFlyZoneLicensesEnabled` 详见
  [14_SOURCE_INDEX.md](14_SOURCE_INDEX.md)。
- **隐私/分发：** 不发布账号、token、Cookie、FC serial、license ID、signed blob、描述、时间、区域或
  server response 正文。

### RID-007A：申请入口在 FlySafe 网站，DJI Fly 没有已恢复的 type-6 专用申请页

- **证据状态：STATIC（C-155）**
- **对象/版本：** 2026-08-29 重新取得的 DJI FlySafe public web bundle；DJI Fly 1.21.10 visible
  resource/model inventory。
- **网页入口：** 当前官方页面同时保留 Mainland RID 与 Abroad RID。前者要求账号背景
  `Government(0)`、审核 `Passed(4)`、资格 `Participated(1)` 且国家为 China；后者要求
  `EuropeanFcc(3)`、`Passed(4)`、`Participated(1)`。两者分别形成 `type:"Rid"`、level 2 China
  与 level 1 Europe。
- **正式接口与 gate：** public bundle 直接闭合以下流程：

  ```text
  GET  /api/qep/background
  GET  /api/qep/unlock/device_type
  GET  /api/qep/device/list?page_size=1000&dtid=<product>
  POST /api/qep/unlock
  ```

  产品 row 的 `support_unlock_type` 必须精确包含 `Rid`；随后账号设备记录必须同时匹配该产品与
  FC serial。后台仍可重复检查这些条件。2026-08-29 bundle 与 2026-08-11 发布版本相同：
  `unlock-request.5439c983.js` SHA-256
  `a2b04cf9def3a06f741a55c4d8c0c8149a534e45946726171f51f8c612e6ca4b`，
  `app.e0d44da4.js` SHA-256
  `268d33eaee4afef6e52103efc05314bd223ac1758c710ffe37f938cd283a4371`。
- **DJI Fly 可见面：** current app 有普通 Safety/Remote ID 注册、状态与地区字段，也有通用
  Unlock-a-Zone 账号/飞机 license list；有界资源和模型盘点没有恢复 type-6 专用申请入口。它们不能
  与网页受审核的 RID application 合并成一个“隐藏开关”。
- **边界/不证明：** 公开 `/dji/drones` 目录包含 Mini 5 Pro 只证明地图目录识别；它不公开
  `support_unlock_type`。当前未登录取数、未发送申请、未取得 Mini 5 Pro capability row 或审批结果。
  改 Sky/Ground country、locale、app region 或 area strategy 都不会生成后台 entitlement。
- **合法最小判别：** 设备所有者可在官方 FlySafe 登录后仅人工记录两个布尔值：“RID 申请卡是否
  可见”“Mini 5 Pro 是否出现在 RID 产品选择器”。不得导出 token、Cookie、HAR、完整 URL、SN 或
  response body。若资格不存在，可向 `flysafe@dji.com` 申请研究/实验支持；也可用一台官方支持且
  genuinely issued type-6 的其他 aircraft 验证 parser/transaction，但该许可不得移到 Mini 5 Pro。
  独立 synthetic OpenDroneID source 可验证检测器字段/地区兼容性，却不能证明 Mini 5 Pro switch。
  任一路线都不能以本地构造、跨账号/跨 FC 搬运或重放许可代替官方签发。
- **公开依据：** [DJI FlySafe](https://fly-safe.dji.com/)、
  [current unlock-request bundle](https://flysafe-public.djicdn.com/js/unlock-request.5439c983.js)、
  [current app bundle](https://flysafe-public.djicdn.com/js/app.e0d44da4.js)。

### RID-007B：当前 official account -> server -> FC 同步链已静态闭合

- **证据状态：STATIC（C-156）**
- **对象/版本：** DJI Fly 1.21.10 exact `libflightrestrictcore.so`；官方 MSDK 5.18 FlySafe API
  作为独立交叉验证。
- **服务器 gate：** 当前 native 先要求 nonempty official login token，再 GET
  `/api/v4/mobile/user` 取得 user context，随后 GET
  `/api/v4/mobile/unlock_license_groups`。服务器刷新使用 `X-FS-*` signed headers；本档案不复制
  app secret、签名材料或真实 header 值。
- **许可组：** server group 带 `sn`、`user_id`、`group_id` 以及预签名的
  `onboard_license_v2/v3/v4`。客户端按当前 FC 的 support、unlock version 与 target index 选择已有
  blob，再原样导入；它不会由 JSON item 在本地生成或签名许可。
- **导入、pull 与 enable gate：** 账号页/server refresh 需要登录；导入前按当前 FC SN 匹配 group，
  native 还按 version/target 选择 blob。飞机页 pull inventory 的可见 app gate 是 connected/known
  product，而非登录本身。enable/disable 只能引用 FC 中已存在的 license ID；FC 仍可校验 signature、
  SN、user ID、validity、version 与飞行状态。
- **不能合并的状态：** `server approved/downloaded`、`FC imported`、`inventory visible`、
  `enabled`、`aircraft broadcaster consumed`、`motor-on RF effect` 是六个不同状态。服务器下载成功不
  等于 FC 接受，FC enabled 也不等于实际 RF 已停播。
- **产品边界：** DJI 官方 SDK compatibility 当前把 Mini 5 Pro 标为 No SDK，MSDK 5.18 public
  support list 也未列出它；这只否定“可直接用 public MSDK app 管理”的假设，不否定 DJI Fly 内部组件。
- **公开依据：** [MSDK FlyZone manager](https://developer.dji.com/api-reference-v5/android-api/Components/IFlyZoneManager/IFlyZoneManager.html)、
  [FlyZone license model](https://developer.dji.com/api-reference-v5/android-api/Components/IFlyZoneManager/IFlyZoneManager_FlyZoneLicenseInfo.html)、
  [DJI Cloud API FlySafe](https://github.com/dji-sdk/Cloud-API-Doc/blob/4ec6b0c7f9472aeb09a0a47949855d19c473ea07/docs/en/60.api-reference/20.dock-to-cloud/00.mqtt/20.dock/00.dock1/170.flysafe.md)。
- **隐私/分发：** 未登录、未发送 authenticated request、未获取 genuine license、未执行 import/push/
  pull/setter。任何合法许可只由所有者通过官方流程取得；本档案不生成、搬运或重放。

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
- **对象/版本：** MSDK 5.18.0 native FlySafe implementation，并与 DJI Fly 1.21.10 exact
  `libflightrestrictcore.so` 比较。
- **前提与路线：** FC serial -> JNI query -> module mediator -> support/version gate -> V2/V3/V4
  session -> PackProvider。
- **事实：** query `PackType 0x38` 映射到 `0x11/0x11`；set-enable `PackType 0x39` 映射到
  `0x11/0x12`。V2 使用单字节 index；V3/V4 使用 group info/paging 与 protobuf/status parser。
  product/version 可改变 receiver route；runtime product 139 的静态 product-tree fallback 最终选择
  `0x92`，前提是 live runtime product 确认等于 139。V3/V4 start body 为 `[00,01]`，page N 为
  `[00,(N<<1)&ff]`；ACK 第一字节是 protocol result，后续 group/record body 分别为 protobuf
  `LicenseGroupInfo` 与 `status_bitmap + License`。在独立 MSDK 5.18 schema 中，
  `License.data` oneof field 7 是 RID，其内部 level 是 field 1；domain type 6 与 protobuf field 7
  是两个命名空间（C-149）。
- **current DJI Fly model boundary：** current native transport 能传递 signed onboard blob 并
  执行 generic query/set-enable，但 exact recovered 1.21.10 `LicenseType` 只定义 0--4 加
  `UNKNOWN(255)`，`LicenseData` oneof 只定义 fields 1--5，`LicenseType.find` 没有 typed field 时
  返回 unknown。更关键的是，`WhiteListLicense.parseFromProtoBufData` 把所有非 0--3 类型（包括
  unknown）送进可容忍空 polygon 的 pentagon fallback。因此 current UI 不只是“不认识 field 7”，
  还可能把 type-6 record 误建模成普通多边形许可（C-185）。独立只读 parser 是
  MSDK-compatible exploration，不能依赖 Fly UI 命名 type 6，也不能说 current Fly 本身已理解
  field 7。
- **边界/不证明：** numeric command 已知不等于可安全 hand-build。support/version push、session owner、
  route、真实许可、readback/restore 和独立 RF 效果仍未实证。
- **公开依据：** 前述公开 state/firmware research。
- **隐私/分发：** 不提供 sender、license ID、signed payload 或可执行 sender。

### RID-008C：A-025 已离线实现现代只读 inventory

- **证据状态：STATIC（C-150/C-151）**
- **对象/版本：** self-developed A-025，versionCode 8、versionName
  `0.5.0-flysafe-readonly`。
- **固定请求：** 通过既有 system `protocol` Binder transaction 4 `sendWithListen`，固定 sender
  type/index `2/4`、receiver `18/4`、`0x11/0x11` 和每次 6,000 ms。V3/V4 start 固定
  `[00,01]`，page N 固定 `[00,(N<<1)&ff]`；group 与 record 只接受 ccode 0，终止只接受
  ccode 1 且 data 为空。声明 count 上限 127、page call 上限 128、总窗口上限 90 秒；parser 对
  独立实现的 MSDK-compatible candidate protobuf schema 做 wire type、长度、深度、字段预算、
  singular duplicate、oneof 和终止 count 一致性检查并 fail closed。它识别 field 7 是兼容性探索，
  不表示 current DJI Fly 自身理解该字段。
- **输出边界：** 只显示总数、已解析数、page call 数、type-6 数量、level、enabled、valid、invalid
  和未解释 status bits。license ID 只转换为本会话随机加盐的 SHA-256 判重值；salt、fingerprint 和
  response copy 在解析后清零。SN、user ID、description、date、geometry、signature、blob 与 raw
  protobuf 不输出或持久化。
- **命令边界：** FlySafe lane 没有获准的 `0x11/0x12` tuple，allow-list 单元测试明确拒绝它；旧
  `0x11/0x1C` UI 按钮也已移除。`flysafe-readonly` 只描述这条新增 lane；工件仍保留 A-024 已有且
  分别受门禁约束的 F7/F9、France EID 与 OPID 实验功能，不能把整个 APK 表述为全局无写能力。
- **工件审计：** 最终 `111,889` 字节 APK 的 SHA-256 为
  `b137540f041cceb50a215bb95144c9f7ccf57fa4db4d2e7fc2108cb6ae68db80`；clean
  `testDebugUnitTest lint assembleDebug` 成功，42 tests 全通过、lint 0 errors/9 warnings，第二次
  clean build byte-identical，v2 signature 与 zip alignment 通过。APK 声明零 Android permission、
  无 packaged native library，检查未发现 network/socket/shell path。二进制不进入本仓库。
- **设备状态：** 2026-08-29 已通过 RC 2 MTP 写入 removable SD `Download`，短名
  `FindUAS_A025_RID.apk`；同会话读回 SHA-256 与登记值一致，意外长名副本已删除（C-154）。这只证明
  staging byte identity。用户随后明确报告安装完成（C-163），但没有确认启动、执行或任何结果；因此
  仍不证明 live Binder 接受、inventory 可用、当前 FC 存在 genuine type 6 或任何 RF 行为。A-025 已
  由 gate-aware A-026 取代。
- **判别：** canonical inventory 中没有 genuine type 6，则这条 managed switch 路线在当前 FC
  停止；存在 type 6 才允许后续单独实现同一 ID 的 baseline -> transition -> readback -> restore。
  Binder failure 只能报告“modern query unavailable”，不能报告 inventory empty。
- **最终真值：** 即便 readback 显示 type-6 enabled，仍要由操作者起桨并让独立检测器做
  enabled/disabled/restored 的 RF A-B-A，才能证明 Mini 5 Pro 实际广播受它控制。

### RID-008E：`03/09` 与 `03/42` 是被动 session gate，不是可猜的 GET

- **证据状态：STATIC（C-157）；A-025 false-negative 结论为 INFERENCE（C-158）**
- **对象/版本：** exact DJI Fly 1.21.10 `libflightrestrictcore.so`；A-025
  `0.5.0-flysafe-readonly`。
- **官方生命周期：** 当前 `Device::Setup` / `PackManager::RegisterDevicePush` 只注册三类本地
  observer，其中 `03/09` Area Info 为 unlock version 来源，`03/42` WhiteList Info 为 support 来源。
  observer 注册链不发送 business GET，也不重放此前 push；没有恢复出安全的主动触发命令。
- **version：** current-token、payload 至少 8 bytes 的 Area Info 从 bytes 3--4 LE16 最高两位得到
  `0 -> V2`、`1 -> V3`、`2 -> V4`、`3 -> 255/unknown`。
- **support：** usable WhiteList Info 按 current parser 的新旧格式产生 Boolean support。Device 初始
  缓存是 `version=255`、`support=false`；若 push 没看到、太晚、长度不够或 token 不匹配，这两个默认值
  必须标为 unknown，不能标成真实 unsupported。
- **manager gate：** official `QueryFCLicenseInfo` 在 support=false 时以 417 停止；version 不在
  0/1/2 时以 203 停止。version 还决定 V2/V3/V4 codec，即使 product 139 的最终 receiver 三代都被
  override 为 `0x92`，也不能跳过 version。
- **A-025 边界：** A-025 直接用固定 V3/V4 selector 发 `11/11`，没有先证明当前连接的
  `03/09 + 03/42`。因此 timeout、zero callback、parser rejection 或任何未 canonical 完成的输出都只能
  叫 `query unavailable/ambiguous`，不能叫 unsupported、no entitlement 或 empty inventory。只有通过
  count/terminator 一致性校验的 canonical completion 才能描述返回清单，并仍不证明 RF effect。
- **第三方 observer 边界：** external Binder 看不到 DJI internal device token；既有 `11/1C` listener
  又已出现独立 RF 对照下的假阴性。故未来即使观察到两个 push，同 sender + 同 bounded window 也只是一
  个 session proxy；若没观察到，结论仍是 observer unavailable，而不是设备不支持。

### RID-008F：A-026 首次实机 gate 为 unobserved，query 保持零发送

- **证据状态：** 设计理由为 `INFERENCE`（C-159）；实现和 final artifact audit 为 `STATIC`
  （C-160/C-161）；MTP 交付和用户报告安装为 `OBSERVED`（C-162/C-164）；首次 bounded gate
  运行是窄范围 `NEGATIVE`（C-165）。
- **对象/版本：** self-developed A-026，versionCode 9、versionName
  `0.6.0-flysafe-gated`。
- **passive gate：** 同一 transaction-2 listener 同时接收 `03/09` version 与 `03/42` support。只有
  两条 callback 的完整实际 route 一致、payload usable、support=true 且 version 为 1/V3 或 2/V4，
  才签发一个仅在同进程消费、不可序列化/复用的 permit。malformed、failure callback、route/value
  conflict、deadline 或 cancellation 均不签 permit；因此 `unobserved`、`unusable`、`unsupported`、
  `unknown` 与 `V2` 都不会发 `11/11`。
- **query gate：** permit 只能进入固定 system-Binder transaction-4 `11/11` sender。group 成功后
  严格按 page 0..127 selector 前进，count/page/terminator 约束保持 fail closed。callback 等待窗口覆盖
  初发与 vendor 两次各 6 秒 retry，避免 request retry 尚活跃时提前 terminal；内部 sender allow-list
  仍没有 `11/12`。
- **privacy/lifecycle：** 结果只保留 count、RID level/status 与 gate result class；不保留 raw payload、
  sender identity、license material 或 device token。完成、失败或取消都进入 listener cleanup，并终止
  进程以触发 Binder-death 清理。
- **非全局 read-only：** 外部 DJI Developer Assistant launcher 不经过上述内部 sender allow-list；
  APK 还保留原有、分别受门禁约束的 F9、France EID 与 OPID write controls。因此该工件是
  `RID Admin`，`flysafe-gated` 只描述新 FlySafe lane，不能把整个 APK 称为 read-only。
- **工件审计：** exact `135,525`-byte APK SHA-256 为
  `3c2ae42ac9f19a9e3dfe669ed6357bb8d2f1c38568af6a0f8d8b8f677fcbfec4`。两次 clean
  `testDebugUnitTest lintDebug assembleDebug` 均成功且 APK byte-identical；63/63 tests、lint
  0 errors/13 warnings、v2 signature、zip alignment、零 `uses-permission`、无 packaged native
  library 及无 inspected network/socket/shell path 全部通过。
- **设备状态：** 已通过 MTP 写入 removable SD `Download` 为 `FindUAS_A026_GATE.apk`；同会话
  readback SHA 一致，重新建立 MTP 会话后确认只有一个该短名且 size 为 `135,525` bytes。没有记录
  object/storage/USB/device serial。用户随后明确报告 A-026 安装完成（C-164）并按既定 gate flow 运行。
- **live result：** 60,003 ms 完整窗口结束时为 `GATE_UNOBSERVED`；`03/09` 为
  `seen=0/usable=0/version=UNOBSERVED`，`03/42` 为
  `seen=0/usable=0/supported=UNOBSERVED`，valid/ignored/malformed/failure callback 均为 0。
  因 gate 未准入，`11/11 request count=0`；这也直接验证了本次 fail-closed 行为（C-165）。
- **边界：** 本次只证明 third-party Binder passive listener 未形成观察面；不能写成 aircraft
  unsupported、no entitlement、empty inventory、RID off/no RF，也不能否定 official in-process
  observer。full-route proxy 不等于 DJI internal device token。没有 query/write、motor action、独立 RF
  对照、raw frame、identifier 或 license material。即便未来 canonical inventory 成功，也只闭合返回清单，
  不闭合 official product eligibility、aircraft-side consumer 或 RF effect。

### RID-008G：A-027 把下一步收敛为一次主动只读 inventory

- **证据状态：** 实现与 final artifact audit 为 `STATIC`（C-166/C-167）；MTP 交付为
  `OBSERVED`（C-168）。
- **对象/版本：** self-developed A-027，versionCode 10、versionName
  `0.7.0-flysafe-direct-readonly`。
- **固定 query：** 一个不可复用的 active-read-only permit 只进入 system-Binder transaction 4，
  固定 `02:04 -> 12:04`、`11/11`、V3/V4 group/page selectors。该 lane 不扫描 sender/receiver route，
  不做应用层 retry，也不借 passive `03/09`/`03/42` gate 解释结果。
- **结果分类：** 只有 count、page、terminator 和 bounded schema 全部 canonical 才显示 inventory。
  timeout、callback failure、schema mismatch 或 noncanonical completion 一律是
  `query unavailable/ambiguous`，不是 unsupported/no entitlement/no license。canonical inventory
  也只是返回清单，不证明 type-6 已被 aircraft broadcaster 消费，更不证明 RF RID 状态。
- **公开证据边界：** pinned `fpv_live` 与 `dji-firmware-tools` 支持历史 DUML device/packet family；
  DJI Cloud API 与 MSDK 支持 FlySafe inventory/license 的通用模型。没有一个公开来源独立确认
  product 139 / RC331 的固定 `02:04 -> 12:04` query route；该 route 是本地 exact static analysis
  候选，A-027/A-028 的 noncanonical live result 没有确认它。
- **工件审计：** exact `196,569`-byte APK SHA-256 为
  `aa4bcd9c8aa96870cfbae1ba326d366cb8854a50ef4aff223f7bce4290ddcd81`。127 tests 为
  0 failures/errors/skips，lint 0 errors/15 warnings；两次 clean build byte-identical；v2 signature、
  zipalign、zero permissions、no native/network/socket/shell/external-process path 均通过。
- **设备状态：** 已通过 MTP staged 为 removable-SD `Download/FindUAS_A027_RO.apk`；fresh listing
  size 为 `196,569` bytes，readback SHA 与登记值一致。操作者随后安装并运行主动按钮；结果为
  `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`，stage `ProtocolException`，显示
  `11/12 request count=0`（C-169）。没有 canonical inventory 或 set-enable request。
- **live 边界：** UI 没显示 exception message，因此不能区分 callback、ccode、group、page 或
  terminator。该运行不证明 unsupported、empty inventory、no `RID_UNLOCK`、RID off 或 RF。结果图片
  不入库；无 raw reply、identifier、license ID、write、motor action 或 independent RF observation。

### RID-008H：A-028 只增加安全诊断，不改变协议行为

- **证据状态：** 实现与 final artifact audit 为 `STATIC`（C-170/C-171）；MTP 交付为
  `OBSERVED`（C-172）。
- **对象/版本：** self-developed A-028，versionCode 11、versionName
  `0.7.1-flysafe-direct-diagnostic`。
- **唯一变化：** `FlysafeRidInventory.ProtocolException` 显示静态安全 message；group/page 非预期
  ccode 显示数值和 page index；terminator mismatch 显示 data length。A-027 的 command、固定
  `02:04 -> 12:04` route、V3/V4 selectors 与 write boundary 完全不变。
- **工件审计：** exact `197,061`-byte APK SHA-256 为
  `d7c32636e19d1bce1b8b8994206355f42d0278b2f15048b14a948a8bbda1d540`。127 tests、
  lint 0 errors/15 warnings、两次 clean build byte-identical、v2 signature、zipalign、zero
  permissions 与 no packaged native library 通过。
- **设备状态：** 已通过 MTP staged 为 removable-SD `Download/FindUAS_A028_DIAG.apk`；fresh
  listing size 为 `197,061` bytes，readback SHA 与登记值一致。操作者随后安装并运行；结果为
  `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`、`ProtocolException`，细分
  `group transport callback failed`，`11/12 count=0`（C-173）。
- **live 边界：** 固定 `11/11` group selector 未获得成功 transport callback，因此尚未进入 group
  protobuf、page 或 terminator，也没有 set-enable request。当前 UI 未显示 Reply failure/ecode/
  callback diagnostic；不能解释为 unsupported、empty inventory、no `RID_UNLOCK`、RID off 或 RF。
  下一判别是显示该既有 Reply 诊断，不重复同一黑盒请求。

### RID-008I：exact official owner 与 generic existing-ID switch 已恢复

- **证据状态：** emulator Activity 为 `OBSERVED`（C-183）；owner、type model 与 action path 为
  `STATIC`（C-184--C-186）；direct Frida attach 为有界 `NEGATIVE`（C-187）。
- **对象/版本：** exact official DJI Fly `1.21.10`，在 disposable ARM64 Android 11 emulator
  完成普通 onboarding 并由 authorized root shell 打开 non-exported Activity。
- **UI 观察：** account/aircraft 两个 license tab 正常渲染；无 aircraft 时，aircraft tab 要求连接。
  这只是 emulator UI 观察，不是 RC 2 inventory 或 FC result。
- **owner chain：** current `LicenseManageComponent -> UnlockLicenseManagerActivity ->
  UnlockLicenseManageView -> ULUavLicenseVM -> FlightRestrictImpl -> JNIFSUnlockManager`，查询最终
  以 current device ID 进入 native FC-license query（C-184）。
- **generic action：** row adapter 从 `WhiteListLicense.isEnabled()` 取得 baseline，把 existing
  license ID + desired Boolean 交给 native current-device setter；success callback 返回 Boolean
  array 更新所有 row。此写入从未执行，也不能自己生成 entitlement（C-186）。
- **type-6 boundary：** exact current Java 只有 types 0--4/unknown 与 fields 1--5；unknown 又落到
  tolerant polygon fallback（C-185）。所以 official current UI 是 same-process transport truth，
  却不是 reliable type-6 semantic truth。显示一个 generic switch 不能叫 RID switch。
- **方法与分发：** direct Frida attach 未产出文件且使 app 退出；不在 RC 2 重复。read-only root
  process-memory copy 仅在 disposable emulator 使用，通用 boundary scanner 以独立源码公开；vendor
  dump、DEX、decompiled source 与 private data 不公开。

### RID-008J：ART TI 已闭合 exact private query/callback plumbing

- **证据状态：** standard JVMTI 1.2 为 emulator `NEGATIVE`（C-188）；ART TI owner/query 为
  emulator `OBSERVED`（C-189/C-190）；success parser 为 `STATIC`（C-191）。
- **标准版本阴性：** standard JVMTI 1.2 late attach 在 canary 日志前导致 exact non-debuggable
  DJI Fly emulator process native crash。Android 11 ART 的适用 late-load version 为
  `0x70010200`，所以不在 RC 2 重复 standard attach。
- **owner/query 正向：** ART TI agent 一次枚举 already-loaded classes，唯一命中 unlock/event
  owner，取得两个 singleton 与 nonzero current device ID；随后通过独立 callback DEX 调用 exact
  private current-device FC-license query。stage=0、dispatch=1、callback=`417`，前后 PID 相同。
- **解释边界：** emulator 无 aircraft，因此没有 success payload；`417` 只证明 exact owner、native
  invocation 与 callback plumbing，不证明 unsupported、no entitlement、empty inventory、RID off
  或 RF。
- **success parser：** source-only parser 解析 embedded `LicenseGroupModel` records、核对 declared /
  observed count、识别 MSDK-compatible field-7 RID candidate；exactly one 时 ID 只留在 process
  memory，公开日志仅 count/level/status。五个 synthetic host cases 与 helper DEX/AArch64 build
  通过。
- **loader 阴性：** ordinary `/data/app/...==/...so` 会在首个 `=` 被截断（C-208）；generic
  `trace_data_file` 在 canary 前结束 target，而同 bytes 从 delimiter-free `apk_data_file` 正常
  callback（C-209）；uncommitted `apk_tmp_file` 又被 target search deny（C-210）。三条均不在
  RC 2 重复。
- **下一依赖：** 先闭合 exact RC 2 caller/target domain 的合法 delimiter-free path/descriptor
  交集，或准入 userspace ADB/system-mediated loader，再做一次 query-only fresh callback/PID
  check；在 real success callback 唯一识别 type 6 前不加入 setter（C-211）。

### RID-008D：current Fly 未闭合 type-6 到 aircraft broadcaster

- **证据状态：** C-152 为 `STATIC`；C-153 为 `NEGATIVE`。
- **exact current Fly parser：** SHA-256
  `17da8363e1ddba47313a74801099e6fdf1e6c4b57ef749222b0cf6e3ceb018f3` 的
  `libflightrestrictcore.so` 中，`v3::LicenseData::MergePartialFromCodedStream` 位于 Ghidra
  `0x004f4af8` / ELF VA `0x003f4af8`。它只 typed-decode fields 1--5；field 7/tag `0x3a`
  调用 protobuf `SkipField(..., UnknownFieldSet)`。exported field symbol 只覆盖
  Area/Circle/Country/Height/Polygon；current Fly core、smali 与 protected bundle 的有界 exact-name
  inventory 对 `RID_UNLOCK`、`LicenseDataRID`、`RidUnlockType` 均为零命中。
- **独立 MSDK 对照：** SHA-256
  `1749d31c8ececb15b3da7c07a967ac9946ac05a0aaffd9e3d3840bd7db09e1ed` 的 MSDK 5.18
  `libDJIFlySafeCore-CSDK.so` parser 位于 Ghidra `0x008ff040` / ELF VA `0x007ff040`，处理
  fields 1--8，并为 field 7 分配 `LicenseDataRID`。这是 A-025 candidate decoder 的 compatibility
  依据，不是 current Fly runtime 证据。`DefaultUASDelegate` 保留逻辑的相关 method 又在 bytecode
  offset 0 立即 return/return false，后续 body 只能作为不可达 design evidence。
- **generic setter：** current Fly `SetLicenseStateV3Session::SetEnable` 位于 Ghidra
  `0x0053505c` / ELF VA `0x0043505c`，只构造
  `[00][license_id_u32le][01 enable | 02 disable][00]`。请求不携带 license type、RID level、region、
  motor/armed、BLE/Wi-Fi 或 module ID；`LicenseUnlockFCManager::SetEnable` 只检查 support/version。
- **有界阴性：** current app/static xref 没有把 type 6、field 7 或 `0x11/0x12 enabled` 连接到
  WA150 `0802` broadcaster、motor transition 或 BLE/Wi-Fi enable。`0x92` 是 packed protocol
  receiver，不能当作 firmware module `0802` 的身份证明。
- **边界/不证明：** `UnknownFieldSet` 可能保留 field-7 raw bytes；以上不证明 FC 不会返回 field 7、
  type 6 不可用或 encrypted WA150 内没有 consumer。当前仍没有 aircraft-side RID enable consumer
  或可逆 firmware patch offset。type-6/license enable、RID status/HMS、RID cloud policy 与真实
  motor-gated RF 是四条尚未闭合的链，不能互相代替。
- **隐私/分发：** 厂商 SO、反编译工程、raw protobuf、license data 与私有回复均不进入本仓库；只
  公开 exact hashes、addresses、高层独立结论和不成立的外推。

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

### RID-009：EU C0 policy 映射存在，当前 FLYC 表面已正对照否定

- **证据状态：NEGATIVE**
- **对象/版本：** DJI Fly 1.21.10 UAV139 registration；当前 Mini 5 Pro live FLYC route。
- **前提与路线：** static key `IsEuCeEnableC0Rid` -> FC parameter
  `EU_CE_enable_c0_rid_0` -> fixed hash -> F7 metadata GET；direct 和 RC-routed plaintext 均测试，
  同 route 的 height/distance 参数为 positive controls。
- **事实：** 两条 live route 都只返回单字节 F7 status `0x03`，未达到 metadata 最小布局；因此未发送
  F8 value GET、F9 write 或 FA reset。
- **早期结果边界：** 单独的一字节 `0x03` 不能区分 endpoint absence、product/runtime gate 或
  其他 refusal。后续 C-227--C-229 结合具名枚举和邻接正对照收窄为本次 FLYC 表面的 absence，
  不证明 DJI Fly、其他固件表面或加密 `0802` 无该机制。静态 business owner 是 cloud-country +
  C0 certification policy，不是已验证用户开关。
- **公开依据：** 先前公开
  [firmware research](https://github.com/Sapphire-Rapids/FindUAS/blob/15f331cf68ce93ae444a8e6aff4c5dc1ed90b5cc/docs/DJI_RID_FIRMWARE_RESEARCH.md#current-official-dji-fly-native-boundary)。
- **隐私/分发：** 可记录公开参数名/hash；不发布 raw responses 或 vendor library。
- **离线工具：** `host-tools/rid-switch-tool/rid_eu_by_hash_switch_control.py` 现提供 bounded
  by-hash A-B-A（F7/F8/F9）单目标 `EU_CE_enable_c0_rid_0`（`0xF80992FE`），带
  `--rid-ctrl-bridge` 只读探针；Android 面板侧 `RidEuC0Parameter` codec 镜像其 F7/F8/F9 语义
  （C-196/C-197）。两者均为 `STATIC` 离线源码，不改变本节的 live `NEGATIVE` 结论，也不提供
  官方功能描述或合规条文。
- **面板独立通路：** `MainActivity` 现为 `EU_CE_enable_c0_rid_0` 增加与 `rid_ctrl_enable_0`
  分离的只读探测/关闭/开启/恢复按钮；写按钮仅在 EU C0 F7/F8 基线与 live route 通过后解锁，
  每次 F9 前重新探测 F7/F8，读回两次，任何未确认状态立即恢复基线（C-199）。UI 文案明确
  单次 F8 读回不代表重连后保持。
- **live positive-controlled absence（2026-08-30，C-227--C-229）：** 本次 direct-USB FLYC route
  正对照成功：table 0 CRC `0x5F8B2AE1`、count 1558；by-hash `max_height_0`
  (`0x0371238A`) F7/F8 canonical（type 1/size 2/值 500）。但 `EU_CE_enable_c0_rid`
  在实机 FC 上不存在：by-index 全表枚举 915 个具名参数无此名（1306 返回 status-only
  `0x0E`），by-hash `EU_CE_enable_c0_rid_0`(`0xF80992FE`) F7 返回单字节 `0x03`。同 session
  邻接 EU C0 行 `EU_CE_Reg_RID_Enable_0`(`0xA2C325CE`) 与
  `eu_ce_support_remote_set_level_0`(`0xA8E96A09`) 均返回 canonical metadata。故这是
  正对照下的 absence，不是 timeout/route 失败。
- **实机索引 +1 漂移（C-229）：** 实机 `01.00.0600` 的 EU C0 注册块整体比公开 wa150 表
  后移一位（`EU_CE_Reg_Level`=1308 … `eu_ce_support_remote_set_level`=1316），采样值
  Level=0 / RID_Enable=0 / fscap_EU_CE_Support=1 / remote_set_level=0，全部 min 0 / max 0。
  公开表索引对当前固件不再权威，by-index 探针必须依赖 onboard 名字校验，不能按公开表硬编码。
- **重连覆盖边界：** pinned FreeFCC 公开文本记载 DJI Fly 以 C0 class runtime flag 在每次连接时
  覆盖飞控参数，`cmd_set=3`/`cmd_id=0xF9` 的 DUML 写入会在每次 reconnect 被覆盖（C-198）。该
  文本未指名 `EU_CE_enable_c0_rid_0` 的 owner，也未证明 RID 相关 C0 flag 与高度 C0 cap 同层；
  因此可靠开关必须包含断开/重连后的持久性负结果或假设，不能以单次 A-B-A 作为可靠性结论。

- **EU C0 参数块边界：** public `lmdegreeds/djiparam` wa150 表显示 `EU_CE_enable_c0_rid`
  是索引 1306-1315 连续 EU C0 class 块内的一行；其中 `EU_CE_Reg_RID_Enable` 与
  `eu_ce_support_remote_set_level` 在公开表中声明 min 0 / max 0（非可写 Boolean 范围），
  且 public GlassFalcon SDK 记载 by-index `0xE0`-`0xE3` 仅在 PC/assistant 源身份 `0x0a` 下
  被接受（C-213/C-214/C-215）。这进一步把该行族标为 EU C0 class/registration 标志，而非
  单一发射机总开关。C-227--C-229 已给出当前固件的 live 结果，不能继续按公开索引重复准入，
  也不能以邻接参数名外推 RID 控制或 RF 行为。

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
  表示 RID off。native writer 是 `set_cloud_control_data_pack`，命令为 `0x00/0xDD`。只有 transport
  result 为零且 response 首字节 ACK 为零时才报告成功，并以原请求值更新本地 cache；ACK 不回显
  飞机实际配置。该 key 没有 GET/listen readback，payload schema、signature rule、WA150 sample 和
  `0x11/0x1C` 状态 correlation 都未闭合。
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

### RID-011C：当前 app 层不存在可准入的主动 RID 状态查询

- **证据状态：STATIC / NEGATIVE**（C-115--C-118）
- **闭合事实：** product-139 `RidImportModule` 是当前 `0x11/0x1C` 状态 owner，但只注册 push
  observer；`dji_fly_rid_cloud_control_v2` 走另一个 `0x00/0xDD` set-only writer。
- **writer 路由：** `KeyCloudControlData` 为 SET-only、无 GET element，也没有 characteristic-level
  host override。writer 从 `CloudControlData` value 本身取 receiver type/index 与 hex payload；
  current native 没有固定 tuple。相邻业务 caller 使用的 `(18,4)` 是调用值，不是 key metadata。
- **阴性结果：** 没有找到 `KeyRidWorkingStatusPush` GET builder、CloudControlData GET/readback、
  Reset/Disable/Debug、SET ACK 与 working-status 的 correlation，或一个静态固定且可安全复用的
  receiver tuple。所谓 `ResetCloudControlSetting` 实际重置三种飞行模式的云控最大速度；
  `GNSSCloudControlDataAction` 与 `IsEuCeEnableC0Rid` 也是不同表面。
- **结论：** 当前唯一可准入的读取方式是被动观察官方 owner 已订阅后自然出现的
  `0x11/0x1C` push；它不是 query，不能为了“读一下”主动发送猜测包。`0x00/0xDD` 的 success
  也不是 RID applied/readback，更不能替代起桨后独立 BLE/Wi-Fi RF 验证。

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

- **证据状态：STATIC/OBSERVED**（C-231 的 `OBSERVED` 仅覆盖交付/readback，不覆盖运行）
- **对象/版本：** `com.finduas.ridobserver` v0.10，SHA-256
  `fdad29bfb1237bc224a805d6eb5a99358a044bd226610d9f0fc33975d94b606c`；完整 identity/disposition
  见[工件登记册](11_ARTIFACT_REGISTER.md)。
- **前提与路线：** offline manifest/DEX/signature/zipalign、测试、对抗变异和 deterministic-build 审计。
- **事实：** v0.10 请求零权限，无 service/receiver/provider/socket/DUML/应用 Binder transaction、
  process execution、persistence、network send、packaged native library 或 attach/load 路径；它只采集
  环境 inventory 和自身进程映射的 ART identity。
- **当前交付：** A-001 已 staged 为 removable-SD `Download/FindUAS_A001_V010.apk`；fresh 唯一
  listing 与同 session 全量 MTP readback 的 size/hash 匹配（C-231）。安装/运行仍待完成。
- **边界/不证明：** 交付不等于 live environment report；即使环境 match 也不证明 RID state、
  EID route、transaction authorization 或 RF behavior。
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
  ADSB RID/EID 标签，且 28 个 display-only 数值映射已经恢复（C-110/C-111）；该表存在
  current-version 语义碰撞，仍没有适用于 WA150 的 schema、caller、product gate、readback
  或 live job，因此不能用于发包。
- **边界/不证明：** server job engine 的能力、`wa150` 型号登记和独立 FCC ModBox 兼容均不
  等于 Mini 5 Pro 软件/CFC/RID 支持。
- **可借鉴：** 若未来闭合 WA150 authoritative owner，可采用“固件内窄 hook + 显式状态/readback
  + stock restore + 独立 RF A-B-A”的架构；当前没有 flash 准入。
- **公开依据：** [Drone-Hacks 静态分析](17_DRONE_HACKS_STATIC_ANALYSIS.md)。

### RID-017：旧式 FlyC `Detection` mask 不迁移到现代 Broadcast RID

- **证据状态：STATIC / INFERENCE / NEGATIVE / CORROBORATED**（C-119--C-122、C-200/C-201）
- **静态 schema：** DJI-derived midware 把 FlyC `Detection` 映射为 `0x03/0xDA`；
  `SetSwitch` 请求为 `05 <mask:u32le>`，`GetSwitch` 请求为 `06`，mask 命名八个旧式
  DroneID 字段。它与 NDSS 论文未公开数值的多字段控制具有高可信语义对应，但不是作者披露值。
- **RF 事实：** 论文报告该控制不会停发 proprietary OcuSync DroneID 包；被选字段会变成字面值
  `fake`。论文没有固定披露该开关实验的机型/固件或实际 host source route。
- **独立复现：** pinned `CIAJeepDoors.py`（`a9a8b4430e847f22c75d4f89b14fe17388c82602`）复现同一
  `fc_monitor` 家族 `01`–`06`（purpose/DroneID 名称/privacy mask 的 get/set），固定路由 PC 10/1
  -> FLYC 3/6，mask bit 3 为 DroneID；其作者明确警告该表面只发 NULL/`fakeSN`、部分固件仍随机发
  有效位置包、新版 DJI Fly/iOS 会复位 bits，且不是可靠方案（C-200/C-201）。
- **当前边界：** 没有公开 primary evidence 表明 WA150 注册 `0x03/0xDA` `0x05/0x06`，或把该
  mask 接到 ASTM/FAA/EU Broadcast RID。当前 DJI Fly 保留旧 generic class 只证明库库存。
- **处置：** 仅作 legacy firmware search signature；不得作为 Mini 5 Pro sender、可调配置或
  transmitter-off control。完整链见
  [Legacy DJI DroneID `Detection` command](18_LEGACY_DRONEID_DETECTION.md)。

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
