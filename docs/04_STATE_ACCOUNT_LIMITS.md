# DJI 状态、账号与运行时限飞层

本文件记录截至 2026-08-28 与 DJI Mini 5 Pro、DJI RC 2、DJI Fly 1.21.10 和 MSDK
5.18.0 有关的 Remote ID 状态、账号状态和飞行限制证据。研究对象和脱敏边界见
[范围与脱敏](00_SCOPE_AND_REDACTION.md)。状态标签只描述证据类型；它们不表示产品支持、法规结论
或写入授权。

## 版本与解释边界

- 实机遥控器界面版本为 `07.00.0100`；未取得与该版本精确匹配的完整 RC331 系统包。
- RC331 `10.00.0700/0205` 只作为相邻平台静态证据，不自动成为 live v07 的实现事实。
- DJI Fly 1.21.10 是当前静态分析样本；未证明 RC 2 正在运行字节相同的 APK 和 native library。
- MSDK 5.18.0 提供公开 API、枚举、schema 和相邻 native 行为；其支持列表未包含当前飞机/遥控器组合。
- `aircraft-reported normal` 不等于 `independent RF reception`；`unavailable` 不等于 `off`、
  `unsupported` 或 `absent`。

对应的规范化 claim 应同步登记到[证据登记册](02_EVIDENCE_REGISTER.md)；失败路径汇总到
[否定结果](09_NEGATIVE_RESULTS.md)，未决解释汇总到[假设与未知](10_HYPOTHESES_AND_UNKNOWNS.md)。

现有机器索引中的直接对应 claim 为：RID working-status static route `C-019`，motors-off observation
`C-020` / bounded negative `C-021`，motor-start external receiver observation `C-022`，缺少同步
onboard/RF 记录 `C-023`，configured limits `C-024`，effective unauthenticated limit `C-025`，
unavailable 解释规则 `C-013`，onboard status 与 RF 分离 `C-049`。飞机自报路径、七字节布局、公开
状态模型和历史语料分别为 `C-056`--`C-059`；账号本地、服务端、FC 同步、实机 Boolean、诊断与
三层解释分别为 `C-060`--`C-065`。

## Remote ID 工作状态

### STATE-001：DJI Fly 使用飞机自报状态

- **证据状态：STATIC**
- **对象/版本：** DJI Fly 已恢复业务层与 DJI Fly 1.21.10 / MSDK 5.18.0 相关模型。
- **前提与路线：** 飞机 RID/EID 子系统状态进入 `RidWorkingStatusPushMsg`，再由
  `KeyRidWorkingStatusPush`、Remote ID model 和 DJI Fly 状态界面消费。
- **事实：** 该路径读取飞机提供的 RID/EID 支持、正常状态、地区值和失败原因；路径本身不扫描
  Wi-Fi 或 BLE 空口。
- **边界/不证明：** DJI Fly 显示正常只构成 onboard/self-test 层证据，不证明外部接收器能收到
  Remote ID，也不证明消息内容、节奏、信道或 RF 功率符合任何地区要求。
- **公开依据：** 先前公开研究
  [DJI RC 2 / DJI Fly state research](https://github.com/Sapphire-Rapids/FindUAS/blob/15f331cf68ce93ae444a8e6aff4c5dc1ed90b5cc/docs/DJI_RC2_STATE_RESEARCH.md#remote-id-what-working-means-inside-dji-software)，
  DJI 官方 `IUASRemoteIDManager` 文档；相关控制面见
  [RID 控制面](05_RID_CONTROL_SURFACES.md)。
- **隐私/分发：** 只保留符号、状态语义和聚合结论；不保留原始 push、飞行器身份或位置。

### STATE-002：当前静态样本的七字节 RID working-status 布局

- **证据状态：STATIC**
- **对象/版本：** 当前官方 DJI Fly 1.21.10 native 样本。
- **前提与路线：** ADS-B/RID command set `0x11`、command `0x1C` 的 native handler；本结论
  来自 handler 的固定读取行为，不来自 live Mini 5 Pro 抓包。
- **事实：** handler 消费恰好七字节：前两字节是 little-endian flags，其中 bit 1/0 分别表示
  EID/RID support，bit 9/8 分别表示 EID/RID normal；字节 2--5 被作为有符号 32 位地区值；
  字节 6 同时供两个上层失败字段使用。
- **边界/不证明：** 上层对象序列化格式不是 raw DUML 布局；地区整数到国家代码的精确表尚未闭合。
  静态布局也不证明当前 live 产品会发送该 push，或 sender/receiver/cmd type 与相邻样本完全一致。
- **公开依据：** 前述公开 state research；固定命令证据另见
  [RID 控制面](05_RID_CONTROL_SURFACES.md)。
- **隐私/分发：** 可公开字段布局；不公开任何原始帧或设备相关 payload。

### STATE-003：公开工作状态枚举与诊断语义

- **证据状态：STATIC**
- **对象/版本：** MSDK 5.18.0 Remote ID API 与已恢复 DJI Fly 诊断映射。
- **前提与路线：** 公开 `RemoteIdWorkingState` 与 DJI Fly 状态界面。
- **事实：** 公开状态包括 `IDLE`、`WORKING`、`OPERATOR_LOCATION_LOST_ERROR`、
  `FIRMWARE_ERROR`、`NO_BROADCAST`、`NOT_SUPPORTED` 和 `UNKNOWN_ERROR`。已恢复 DJI Fly
  诊断包括 30331（RID 正常）、30332/30334（操作者位置问题）和 30333（RID link/firmware
  问题）；部分位置告警有约两秒稳定过滤。
- **边界/不证明：** 只有 `WORKING` 明示软件认为广播正在工作，但仍不是独立 RF 观测。
  `NO_BROADCAST` 在某个地区/许可 delegate 中的语义不构成普通用户总开关。
- **公开依据：** DJI 官方 MSDK 文档和前述公开 state research。
- **隐私/分发：** 只记录公开枚举和诊断号。

### STATE-004：起桨前严格被动窗口没有 `0x11/0x1C`

- **证据状态：NEGATIVE**
- **对象/版本：** 当前 Mini 5 Pro 与 RC 2 实机组合，2026-08-27；飞机未起桨。
- **前提与路线：** Assistant 释放 USB 后，分别进行飞机侧 15 秒基线和飞机/RC 2 双路 20 秒
  同时被动监听；解析器执行严格 framing、CRC 和 command 匹配，未发送订阅或设备写入。
- **事实：** 双路窗口均验证了普通 DJI traffic，但没有 `0x11/0x1C` 候选；没有保留原始
  payload、UAS ID、位置或序列号。
- **边界/不证明：** 该结果只描述 motors-off、无官方订阅/状态变化的有限窗口。它不证明飞机不支持
  RID，不证明起桨后仍无 push，也不证明没有空口广播。
- **公开依据：** 前述公开 state research；时间线应登记于[研究时间线](03_TIMELINE.md)。
- **隐私/分发：** 只发布窗口长度和聚合结果；原始 traffic 不进入仓库。

### STATE-005：历史 broker 语料证明该 command family 曾实际出现

- **证据状态：OBSERVED**
- **对象/版本：** 固定的历史 RC 2 / 另一飞机型号会话语料，不是当前 Mini 5 Pro live session。
- **前提与路线：** 已脱敏历史 `40007` 语料经严格 CRC 和 inner DUML 解析。
- **事实：** 语料中存在严格有效的 `0x11/0x1C`、FlySafe area/version push 和 whitelist/support
  push，证明普通 RC 2 app 在至少一个真实产品/会话上能从 broker 收到这些类型。
- **边界/不证明：** 不证明当前 Mini 5 Pro 会话转发相同 push，也不证明第二个 localhost 客户端能
  与 DJI Fly 安全共存。后续单活动 fd 证据已经使第二客户端 observer 路线撤回。
- **公开依据：** 前述公开 state research；撤回原因见
  [RID 控制面](05_RID_CONTROL_SURFACES.md#rid-012历史-localhost-observer-路线已撤回)。
- **隐私/分发：** 不公开历史原始语料和其私人遥测，只公开命令计数级结论。

### STATE-006：广播验证需要两个独立层级

- **证据状态：INFERENCE**
- **对象/版本：** 当前研究档案的一致解释规则。
- **前提与路线：** 结合 DJI onboard status 语义、官方 Remote ID 说明和外部 receiver 的功能边界。
- **事实：** 可重复的判定应分为：（1）飞机自报 RID support/working 且无 blocking diagnostic；
  （2）在操作者自行起桨后，由独立接收器观察并解码新鲜的飞机与控制站数据。
- **边界/不证明：** 任一层单独通过都不替代另一层；普通 macOS 蓝牙设备列表也不是第二层，因为
  Broadcast Remote ID 不必表现为可连接 peripheral。
- **公开依据：** DJI 官方 Remote ID FAQ、前述公开 state research；RF 证据层级见
  [地区与 RF policy](06_REGION_RF_POLICY.md#rf-006证据阶梯)。
- **隐私/分发：** 独立接收结果只允许保存脱敏字段和聚合判定。

## DJI 账号状态

### ACCOUNT-001：本地登录状态只证明缓存层

- **证据状态：STATIC**
- **对象/版本：** 已恢复 DJI Fly 账号业务路径。
- **前提与路线：** `UAVAccountCenterService.isLogin()` 与登录回调的本地状态路径。
- **事实：** 本地 `isLogin` 主要依据缓存会话材料是否非空；登录回调可以先设置本地 Boolean，且该
  判断本身不访问服务器、不要求飞机已接收当前账号身份。
- **边界/不证明：** 绿色/已登录 UI 不证明服务端仍接受当前会话，也不证明 FC 持有当前账号身份。
- **公开依据：** 前述公开 state research 的 “DJI account” 章节。
- **隐私/分发：** 只记录状态机行为；不记录账号、UID、token、Cookie 或缓存内容。

### ACCOUNT-002：服务端 token 验证是独立第二层

- **证据状态：STATIC**
- **对象/版本：** 已恢复 DJI Fly 网络账号逻辑及 DJI 官方离线限制说明。
- **前提与路线：** 网络可用时，官方 app 将现有会话交给其 token validation endpoint。
- **事实：** 业务成功码会接受会话并刷新本地到期时间；业务失败会清除账号状态；transport/parse
  失败只在本地期限已过时清除。成功登录或成功验证写入约 90 天的本地有效期。
- **边界/不证明：** 本地未到期不等于服务器刚刚接受；服务端接受也不证明 UID 已同步到 FC。
- **公开依据：** DJI 官方超过 90 天无网络限制说明、前述公开 state research。
- **隐私/分发：** 不记录请求 header、账号值、token、Cookie、响应正文或用户标识。

### ACCOUNT-003：账号身份向飞行系统同步是独立第三层

- **证据状态：STATIC**
- **对象/版本：** 已恢复 DJI Fly `WriteUuidLogicV1` / flight-limit component 路径。
- **前提与路线：** 飞控连接和账号状态变化触发 app identity 与 account identity 写入逻辑。
- **事实：** 飞控连接后，app 会设置 app 身份；只有当前账号 UID 非空时才尝试向 flight-limit
  subsystem 写入 UID。失败路径会以固定间隔继续尝试。恢复的普通路径没有在成功写入后读取 FC 值并
  与当前 UID 做等值比较。
- **边界/不证明：** 本地 login Boolean、发起写入或日志成功均不能证明当前 FC 持有正确账号身份。
  本档案不实现或建议 UID 写入。
- **公开依据：** 前述公开 state research。
- **隐私/分发：** 不公开 UID、账号、写入 payload 或真实设备身份。

### ACCOUNT-004：两个 transport 的 FC 身份状态读数一致

- **证据状态：OBSERVED**
- **对象/版本：** 当前 Mini 5 Pro / RC 2 实机组合，2026-08-27。
- **前提与路线：** 只发送两个 allow-listed `FLYC Detection` `0x03/0xDA` status GET；分别通过
  RC 2 bridge 和飞机 direct USB，响应必须匹配 subcommand 和 success code。
- **事实：** `GetIsSetUUID=9` 在两路均返回 false；legacy `GetUAVAppFlag=12` 在两路也均返回
  false。隐私敏感的 UUID content/history GET 未发送。
- **边界/不证明：** 结果不证明 RC 2 本地账号已退出，也不证明服务端 token 无效。legacy app flag
  是否与现代 `KeyAppFlag` 使用同一 backing state 仍未知。
- **公开依据：** 前述公开 state research；实验最低字段应同步到
  [时间线](03_TIMELINE.md)和[证据登记册](02_EVIDENCE_REGISTER.md)。
- **隐私/分发：** 只发布 Boolean 与 route 一致性；不查询或保存真实 UID。

### ACCOUNT-005：诊断 3000003 不能覆盖三层登录状态

- **证据状态：STATIC**
- **对象/版本：** 已恢复 DJI Fly top-bar diagnostic 逻辑。
- **前提与路线：** 飞控连接且 app 本地认为未登录时，由 app 自行构造 3000003。
- **事实：** 该诊断不是飞机 push，也不是 FC UUID 写入失败 ACK；它主要覆盖本地 login Boolean。
- **边界/不证明：** 没有 3000003 不证明 token 最新有效，不证明 UID 非空，不证明 UID 已到达 FC。
  `FCHasWrittenUUID=true` 也可能只表示历史身份存在，不能证明与当前账号相等。
- **公开依据：** 前述公开 state research。
- **隐私/分发：** 只记录诊断控制流；不记录账号状态原值。

### ACCOUNT-006：三层账号判定

- **证据状态：INFERENCE**
- **对象/版本：** 当前研究档案对“正确登录”的操作性分层。
- **前提与路线：** ACCOUNT-001 至 ACCOUNT-005 的静态和实机事实。
- **事实：** 三层分别是：（1）本地 session 可用且 UID 非空；（2）最近一次服务端验证成功且本地
  期限未过；（3）当前 FC identity 与当前账号 UID 在内存中严格相等。
- **边界/不证明：** 这是证据分层，不是 DJI 公开合规 API，也不授权查询或导出私人 UID。当前资料
  没有完成第三层的 current-account 等值验证。
- **公开依据：** 前述公开 state research。
- **隐私/分发：** 最终公共记录只允许 yes/no/unknown，不允许保存实际身份值。

## 配置限值与有效运行时限制

### LIMIT-001：普通配置值在两个读取路线一致

- **证据状态：OBSERVED**
- **对象/版本：** 当前 Mini 5 Pro / RC 2 实机组合，2026-08-27。
- **前提与路线：** 通过 RC 2 bridge 与飞机 direct USB 对三个已知 hash 参数执行严格只读 metadata
  和 value GET；两路均有有效响应。
- **事实：** 高度配置为 500 m；距离配置为 5000 m；distance-limit enabled 为 false。两路返回
  的值与类型/范围 metadata 一致。
- **边界/不证明：** 这些是配置层数值，不证明飞行时的 effective limit，也不证明当时存在或不存在
  未登录账号引发的 30 m / 50 m runtime restriction。
- **公开依据：** 前述公开 state research。
- **隐私/分发：** 参数值不含私人身份；不发布完整 raw response。

### LIMIT-002：配置层不能解释潜在 30/50 m 运行时层

- **证据状态：INFERENCE**
- **对象/版本：** 当前 Mini 5 Pro 的已观察配置和 DJI 官方未登录限制说明。
- **前提与路线：** LIMIT-001 的配置值与 ACCOUNT-004 的 FC identity status 同时存在。
- **事实：** 如果测试状态下实际存在 30 m 高度 / 50 m 距离限制，它不由已读取的高度、距离和
  distance-enabled 三个配置值直接表达，应位于独立的 effective-limit/reason/status 层。
- **边界/不证明：** 本次观察没有飞行，也没有读取完整 effective status，因此不能确认 30/50 m
  cap 当时实际生效。
- **公开依据：** DJI 官方未登录限制说明、前述公开 state research。
- **隐私/分发：** 无私人数据。

### LIMIT-003：可判别 effective limit 的状态面仍未取得

- **证据状态：UNKNOWN**
- **对象/版本：** 当前 Mini 5 Pro / DJI Fly runtime。
- **前提与路线：** 已恢复的长 `DataOsdGetPushHome` `0x03/0x44` 布局和
  `DistanceLimitedReason` key；需要在操作者观察实际限制时进行只读关联。
- **事实：** 静态资料指出 long home push 含 height-limit status、effective height value 和 reached
  bits，并有 `REAL_NAME_LIMIT` reason 值。当前 motors-off 被动窗口只见普通 flight-controller
  push，没有足够长的 `0x03/0x44`。
- **边界/不证明：** absent push 不证明不存在 effective limit；本研究软件不得代表操作者启动电机。
- **公开依据：** 前述公开 state research；待办和门禁见
  [当前阻断点](12_CURRENT_BLOCKERS.md)与[交接](13_HANDOFF.md)。
- **隐私/分发：** 未来只保留状态枚举和数值，不保留位置、身份或完整 flight log。

## 当前可复用判定表

| 问题 | 当前状态 | 可公开结论 | 不可推出 |
| --- | --- | --- | --- |
| DJI Fly 是否认为 RID 正常 | `UNKNOWN` | 有静态 status 路径和严格 decoder | 当前飞机 live `WORKING` |
| 起桨前是否见 `0x11/0x1C` | `NEGATIVE` | 有限 motors-off 窗口未见 | 不支持 RID、起桨后仍无 push |
| 是否完成独立 RF 验证 | `UNKNOWN` | 当前保留记录没有同步 onboard + RF 证据 | 广播 off/on、法规符合性 |
| 本地账号是否可见为登录 | `UNKNOWN` | 已知本地 Boolean 的实现边界 | 服务端有效或 FC 已同步 |
| FC 是否报告已有 UUID | `OBSERVED` | 两路均报告 false | RC 2 本地已退出、服务器 token 无效 |
| 普通高度/距离配置 | `OBSERVED` | 500 m / 5000 m / distance disabled | effective 30/50 cap 不存在 |
| effective real-name limit | `UNKNOWN` | 已恢复候选 read-only status 面 | 当前是否正在生效 |

## 接手条件

1. 新证据先更新[机器可读 claim 索引](../evidence/claims.csv)和
   [证据登记册](02_EVIDENCE_REGISTER.md)，再更新本文。
2. RID status 的下一条有效记录必须复用官方 owner 或其他不创建第二 broker fd 的观察路径；保存
   脱敏字段，不保存 raw frame。
3. 独立 RF 记录必须与操作者自行起桨后的 onboard status 对时；禁止把 self-report 当成 RF proof。
4. 账号研究只允许 yes/no/unknown 与 enum 输出；不得导出 token、Cookie、UID、账号或 license。
5. effective limit 研究保持 read-only；不更改高度、距离、账号或 app identity。
6. 任何 timeout、缺失 push 或 Boolean false 都必须保留 route、窗口、正控和“不证明什么”。
