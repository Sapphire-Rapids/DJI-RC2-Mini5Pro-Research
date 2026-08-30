# DJI RC 2 / Mini 5 Pro research archive

最新进展（C-262）：F3 已收到，定位到 Android mksh 的 heredoc 临时文件失败。正在修正诊断，并按用户请求实现有限会话的 SD 任务收发，减少手工输入。


[![Validate research archive](https://github.com/Sapphire-Rapids/DJI-RC2-Mini5Pro-Research/actions/workflows/validate.yml/badge.svg)](https://github.com/Sapphire-Rapids/DJI-RC2-Mini5Pro-Research/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

这是一个独立、非官方的 DJI RC 2 / Mini 5 Pro 研究档案。记录截至 2026-08-31 的实机观察、
固定版本静态分析、公开资料交叉验证、阴性结果、被撤回的路线、明确假设和未解决问题，并逐步
纳入可复现的自研 APK 源码、host tools、tests 和合成 fixtures。

档案中的产品名称只用于说明研究对象。项目不是 DJI 官方产品，无隶属或背书关系；实验室的
授权声明与非官方产品身份分开记录。

**最新进展：[2026-08-31 时间线](docs/03_TIMELINE.md#2026-08-31)** ·
[实机环境与当前操作](docs/23_RC2_LIVE_RUNTIME.md)。每次取得新结果后同步更新。
按用户最新要求，目前在本地更新、验证并可提交；用户恢复授权前不再推送 GitHub，历史已推送记录保留。

新建或接续 Codex 任务时，请使用
[`CODEX_PROJECT_PROMPT.md`](CODEX_PROJECT_PROMPT.md) 中的精简提示词。它把本项目准确界定为
用户自有实验设备上的 Remote ID 控制研究，并一次写清允许动作、硬性禁区和实证完成标准。
当前目标包括真机 RID 开关、Basic/UAS ID、飞机位置和操作者位置；Operator ID 单独记录。
各字段须分别闭合 owner、基线、读回、恢复及独立 RF 证据，不能用合成 codec 代替真机结果。
已有研究的快速接手请直接复制
[`NEXT_AGENT_HANDOFF_PROMPT.md`](NEXT_AGENT_HANDOFF_PROMPT.md)。

## 研究对象快照

| 对象 | 记录值 | 证据边界 |
| --- | --- | --- |
| 遥控器 | DJI RC 2；界面固件 `07.00.0100` | 已读回 ART、Fuli、framework/services 与部分系统属性，Fuli 安装后复测、Shell 身份和父目录基线已完成；mounted adbd 身份仍待核对（C-245--C-247） |
| 飞机 | DJI Mini 5 Pro；固件 `01.00.0600`；静态候选 WA150 / product 139 | 固件为操作者确认（C-220）；product/route 仍需 live session 重新确认；`01.00.0600` 落在 CVE-2026-78306/77812 受影响窗口 |
| DJI Fly | 实机 `1.19.4` / code `3113157`，ARMv7；另保留 `1.21.10` 对照 | 实机 APK/库已回传并校验；1.21.10 的模拟器结果保留原版本标签（C-238/C-239） |
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

- **标准 RID 已观察（C-207）**：操作者用已验证的标准 Remote ID 检测装置 + FindUAS 上位机确认，
  Mini 5 Pro 起桨时广播明文标准 Remote ID，Basic ID 可读。确切 BLE/Wi-Fi bearer 与电机
  off/on/off 时序仍需一份完整书面记录；Mac 到接收机的 BLE 连接不证明飞机的 air bearer。
  DJI 私有 OcuSync DroneID（含 O4 加密边界）暂缓，不作为当前控制目标。

- **两项 FLYC 候选已否定（C-227--C-230）**：`01.00.0600` aircraft-direct 路由正对照成功，
  table count 为 1558、报告具名项 915；`EU_CE_enable_c0_rid(_0)` 和 `rid_ctrl_enable_0`
  在该表面为 positive-controlled absence。邻接 EU C0 块比公开表后移一位，采样行 min/max
  均为 0。不得重复旧参数/地址变体或把邻接标志当开关；结论不覆盖 App、其他表面或加密 `0802`。
- **接手材料已定位**：旧本地 corpus 中的核心 DJI Fly/RC331 样本及部分 A-032/A-033 输出已
  重新核验 hash，与登记一致；没有导入厂商材料。限定 sandbox 检索尚未找到最新枚举输出及
  C-207 完整时序原件，不能据此称其丢失，应先核对旧任务输出或既有应用历史。
- **实机回传已完成（C-235--C-238）**：A-039 v0.12 报告为 `COMPLETE`；实机 Fly
  `1.19.4` APK 与三份库的版本、签名、哈希核对通过。独立 RID 状态读取链已定位（C-240）。
- **当前实机进展（C-245--C-261）**：报告、Shell system 身份与目录基线已收到，canary 仍未内部复制或 attach。
  F2 报告的唯一失败为 pidof 未返回结果；AMS 随后给出 Fly HOME 主进程条目，但一次分离的
  proc 路径读取失败（C-257--C-259），因此改为同次报告收集 AMS 前后记录与 proc 信息。
  当前 F3/A-045 已通过 18 个完整 shell fixtures 和 14 个独立 parser/capture vectors，
  暂存为 `Download/F3.sh`，完整读回匹配（C-260/C-261）。F2 已移入 Archive，前后读回一致、无删除。
  当前等待已私下发送的精确路径命令返回 `F3_SAVED` 或错误，不重跑 F2 或继续手工 proc 查询；
  操作见 [实机主题](docs/23_RC2_LIVE_RUNTIME.md#下一步)。字段 owner 独立推进，合成 codec 保持离线。

- Current same-family SKYROVER `1.2.0` 已出现一个独立 Boolean `RIDCtrlEnable`：native 映射
  为 FC 参数 `rid_ctrl_enable_0`、hash `0x3CBD864F`，使用 FLYC `03/F7-F9`。它与 France
  EID、OPID、DIPS 和 China OID 分开。DJI Fly `1.21.10` 没有同名 wrapper，因此 Mini 5 Pro
  该 wrapper 不能静态迁移到 Mini 5 Pro；该型号当前 FLYC 表面的后续否定见 C-230。
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
- 当前官方申请入口在 FlySafe 网站，不是 DJI Fly 中已恢复的 type-6 专用设置页。Mainland/Abroad
  RID 分别要求对应账号背景审核，产品 row 的 `support_unlock_type` 精确含 `Rid`，并选择与产品和
  FC serial 匹配的账号设备记录。DJI Fly 1.21.10 随后以 nonempty login token 获取 user/signed
  license group，按 FC support/version/target 选择 server-supplied V2/V3/V4 blob 后导入、pull，再对
  existing license ID enable。Mini 5 Pro 的登录后 capability/审批、FC import 与 genuine record 均
  未知；改地区不会生成 entitlement，public MSDK 也未支持 Mini 5 Pro。
- Exact current DJI Fly 1.21.10 `LicenseData` typed parser 只处理 fields 1--5；field 7/tag `0x3a`
  进入 `UnknownFieldSet`。把 field 7 解成 `LicenseDataRID` 的是独立 MSDK 5.18 工件，A-025 因此是
  MSDK-compatible exploration，不是“current Fly 已理解 type 6”的证据。current Fly
  `11/12` 也只是 license-ID-plus-action generic setter；有界静态追踪没有找到它到 WA150 `0802`、
  motor/armed 或 BLE/Wi-Fi broadcaster 的 consumer。该阴性不覆盖 encrypted aircraft firmware，
  `0x92` 也不是 module `0802` 身份。
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
- RC 2 标准 ADB 在 RSA 认证前停止：主机 `CNXN` 已发出，设备不返回 ADB 包。Exact signed-v07
  APEX `adbd` 已固定 hash 并证明含 `mp_state=production && dbg_cnt<1` 的 pre-AUTH return；运行时
  path 是 `/apex/com.android.adbd/bin/adbd`。C-237 已读到 `mp_state=production` 与空的
  `dbg_cnt` 字符串；mounted adbd hash 和实际分支仍待获取。
- 只改该 gate-value instruction、保留 ordinary TLS/auth path 的 A-032 userspace copy 已生成；
  removable-SD MTP fresh size/full readback SHA 匹配。它尚未复制到 internal storage、chmod 或执行，
  没有通过 A-032 获得 ADB shell。开发助手 Shell 身份及父目录读取另由 C-246/C-247 闭合。
  A-032 保留为备选；当前 F3/A-045 已暂存并读回匹配，等待同次 AMS/proc 报告（C-261），
  操作入口统一见 [实机主题](docs/23_RC2_LIVE_RUNTIME.md#下一步)。
- 当前 Android probe 为 v0.12（A-039），文件名 `Download/FindUAS_A039_V012.apk`。
  首次 COMPLETE 报告及实机样本已回传并校验（C-237/C-238）；安装后复测也已收到 COMPLETE
  报告（C-245），Fuli 原版 hash/版本/signer 保持一致、updated-system=true。v0.11/A-038 已归档。
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
- 当前已审计并 staged 的 A-025 `0.5.0-flysafe-readonly` / code 8（SHA-256
  `b137540f041cceb50a215bb95144c9f7ccf57fa4db4d2e7fc2108cb6ae68db80`，`111,889` bytes）
  已实现固定 system-Binder `02:04 -> 12:04`、`11/11` 的现代 FlySafe V3/V4 有界清单查询。
  count/page/overall 上限为 127/128/90 秒，只输出 count、RID level 与 status bits；identity/raw
  data 不输出，`11/12` 无获准路径，旧 `11/1C` 按钮已移除。42 tests、lint 0 errors、clean
  assemble 与 byte-identical rebuild 通过，APK 零权限、无 native/network/socket/shell path。它已
  通过 MTP 写入 RC 2 removable SD `Download` 为 `FindUAS_A025_RID.apk`，同会话读回 hash 一致，
  意外长名副本已删除；用户随后报告安装完成，但启动/执行/结果仍未知。A-025 已由 A-026 取代。
  `flysafe-readonly` 只指新增 lane，同一 APK 仍保留旧的门禁式 F7/F9、France EID 与 OPID 实验功能。
- Exact current Fly 还表明 FlySafe query 的 version/support 分别由 passive `03/09` Area Info 与
  `03/42` WhiteList Info 填充；默认 `255/false` 或没看到 push 都是 unknown。A-025 在未观察这些
  current-connection gates 时直接假设 V3/V4，所以 failure/noncanonical completion 可能是假阴性，
  不能叫 unsupported 或 empty。A-026 `0.6.0-flysafe-gated` / code 9 已实现 bounded passive gate：
  malformed/failure/conflict/deadline/cancel 不签 permit，仅 support=true + V3/V4 时同进程进入 fixed
  `11/11`。exact `135,525`-byte SHA-256 为
  `3c2ae42ac9f19a9e3dfe669ed6357bb8d2f1c38568af6a0f8d8b8f677fcbfec4`；63 tests、两次
  byte-identical clean build、lint 0 errors/13 warnings、v2/zipalign、零权限及无
  native/network/socket/shell path 通过。它已 staged 为 `FindUAS_A026_GATE.apk` 并跨 MTP 会话确认
  readback hash/唯一短名/size；用户随后明确报告安装并按既定流程运行。60,003 ms 窗口内
  `03/09` 与 `03/42` 均 `seen=0/usable=0`，所有 callback 分类计数均为 0，gate 为
  `GATE_UNOBSERVED`，所以 fail-closed 路径正确保持 `11/11 request count=0`（C-165）。这只说明
  本次 third-party Binder passive listener 没形成观察面，不表示飞机 unsupported、无 entitlement、
  empty inventory、RID off 或无 RF。external Binder route/window 仍只是 token 代理；
  external Developer Assistant 也不受内部 allow-list，且 APK 保留 gated F9/EID/OPID writes，因此是
  Admin 而非全局 read-only。
- 历史 A-027 `0.7.0-flysafe-direct-readonly` / code 10 将当时的诊断收敛为一次主动只读 `11/11`：固定
  system-Binder `02:04 -> 12:04`，只使用 V3/V4 group/page selectors，不扫描 route，也不做应用层
  retry。`196,569`-byte APK 的 SHA-256 为
  `aa4bcd9c8aa96870cfbae1ba326d366cb8854a50ef4aff223f7bce4290ddcd81`；127 tests 全通过、
  lint 0 errors/15 warnings、两次 clean build byte-identical、v2/zipalign、零权限以及无
  native/network/socket/shell/external-process path 均通过。它已通过 MTP staged 为
  `Download/FindUAS_A027_RO.apk`，fresh listing size 与 readback SHA 均匹配。操作者随后安装并运行
  主动按钮；进入 strict inventory parser 后结果为 `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`，阶段
  `ProtocolException`，`11/12 request count=0`。UI 没显示 exception message，所以目前不能区分
  callback、ccode、group、page 或 terminator；这不是 unsupported、empty inventory、无
  `RID_UNLOCK`、RID off 或 RF 结论。
- A-028 `0.7.1-flysafe-direct-diagnostic` / code 11 是紧随其后的只读诊断版。它只让 UI 安全显示
  `ProtocolException` 静态说明、unexpected group/page ccode 数值与 page index、terminator data
  length；协议命令、固定 route、selectors 和写入边界不变。`197,061`-byte APK SHA-256 为
  `d7c32636e19d1bce1b8b8994206355f42d0278b2f15048b14a948a8bbda1d540`；127 tests、
  lint 0 errors/15 warnings、两次 clean build byte-identical、v2/zipalign、零权限、无 packaged
  native library 通过。已 staged 为 `Download/FindUAS_A028_DIAG.apk`，fresh size/readback SHA
  匹配。操作者随后安装并运行；结果为 `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`、
  `ProtocolException`，细分 `group transport callback failed`，`11/12 count=0`。因此固定
  `11/11` group selector 没有得到成功 transport callback，尚未进入 group protobuf、page 或
  terminator；这仍不是 unsupported、empty inventory、无 `RID_UNLOCK`、RID off 或 RF 结论。
- A-033 `0.8.0-flysafe-diagnostic-export` / code 12 保持 A-028 的固定 `11/11` 协议与零
  `11/12` 按钮边界，只把 privacy-reduced 诊断自动写到
  `Download/FindUAS/FindUAS_RID_A033_latest.txt`。其 `204,449`-byte APK SHA-256 为
  `8ce8e0c13ecfcf69517a64e809a475b79bbc750124225744b6b35f281d3d7177`；132 tests、lint
  0 errors/15 warnings、两次 byte-identical clean build、v2/zipalign、零权限及无
  native/network/socket/shell/external-process path 已通过。MTP fresh readback 匹配；尚未安装或
  运行，不能据此宣称 inventory、RID 状态或 RF 控制。
- Exact DJI Fly 1.21.10 的运行时 Java 已从一次性 ARM64 Android 11 emulator 中恢复并仅在本地
  分析：官方 `UnlockLicenseManagerActivity` 的飞机 tab 确实沿同进程 component/view-model、
  `FlightRestrictImpl`、`queryFCLicensesJni` 到 native current-device query；generic row switch
  沿 existing license ID + Boolean 到 `setLicenseEnableJni`，本研究未执行写入。该 Activity 也已在
  emulator 中真实渲染，证明 UI/owner 存在但不是 RC 2/飞机结果。
- Exact current Java 同时给出一个重要阴性：`LicenseType` 只有 0--4 + `UNKNOWN`，`LicenseData`
  只有 fields 1--5，未知记录会落入可容忍空 polygon 的普通兜底。也就是说 DJI Fly 1.21.10 UI
  不能语义识别 type-6 `RID_UNLOCK`，可能误分类；这不否定 native/FC/opaque server 支持。
- Disposable Android 11 emulator 已进一步闭合 official owner 的真实调用：标准 JVMTI 1.2
  late attach 会在 canary 日志前导致 exact DJI Fly 进程 native crash；改用 ART TI
  `0x70010200` 后，同一 PID 内精确取得 FlySafe owner/current device ID，并成功派发一次 private
  FC-license query。因 emulator 没有飞机，回调为 `417`，PID 保持不变（C-188--C-190）。
- 新增 source-only
  [same-process query experiment](experiments/jvmti/jvmti_flysafe_inprocess_query/README.md)：
  success callback 独立解析嵌入式 license group，核对 count，识别 MSDK-compatible field-7
  type-6 candidate，只输出 count/level/status，license ID 只保留在内存。五个 synthetic host cases
  与 helper DEX/AArch64 agent build 通过（C-191）。下一步是为 RC 2 准入 same-process loader，
  不再继续猜 external Binder route。
- Same-process loader 的三个捷径已在 disposable emulator 关闭：普通 `/data/app/...==/...so`
  会在首个 `=` 被 agent-spec parser 截断；delimiter-free `trace_data_file` 在 canary 前结束 target，
  但相同 bytes 从 delimiter-free `apk_data_file` 能稳定派发并回调；uncommitted PackageInstaller
  `apk_tmp_file` 又被 target search deny，session 已 abandon（C-208--C-210）。下一步是 exact RC 2
  caller/target domain 与合法共享可执行路径/descriptor 的交集，两个新 APK 源码仅作为阴性记录，
  不是上机候选（C-211）。
- 2026-08-28 实机 direct F7 已完成：RC 2 routed 和 aircraft-direct 两路对
  `0x3CBD864F` 均返回 one-byte `03`，且同会话已知参数正对照正常。raw USB modern route
  连 height control 也 timeout；A-023 的 Binder target 同样 timeout，但没有同路由正对照。
  A-024 又证明两条 Binder route 连 height 正对照都失败，因此 current generic-parameter
  attach 路线已关闭；target 从未发送，未发送 F9。Exact A-026 的首次 passive gate 运行也已闭合为
  `GATE_UNOBSERVED`/zero-query，不能重复解释为设备能力阴性。A-027 主动只读候选随后也已运行，
  但只收敛到 `ProtocolException` 级 ambiguous failure，尚未形成 canonical inventory。A-028 又把它
  定位为 group transport callback failure。A-033 的 Reply diagnostic 只保留历史对照用途；当前
  优先读取可信 RC 2 identity 并准入 official in-process owner 的合法 loader，不重复相同黑盒
  请求。网站 RID card/Mini 5 Pro selector 仍是独立 entitlement 问题。只有 canonical genuine type 6 才继续追
  enable state 到 `NO_BROADCAST`/真实 RF；并行继续 WA150 `0802` broadcaster/policy owner。
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
- 可调目标已扩展为真机开关、Basic/UAS ID、飞机位置和操作者位置；Operator ID 单列。
  current exact 路径闭合 EASA OPID `0x03/0x78`、
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
- [docs/03_TIMELINE.md](docs/03_TIMELINE.md)：研究动作时间线。
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
- [docs/20_OFFICIAL_FLYSAFE_UI_PATH.md](docs/20_OFFICIAL_FLYSAFE_UI_PATH.md)：DJI Fly 官方同进程
  FlySafe owner、generic existing-ID action、current type-6 Java incompatibility 与一次性只读实机步骤。
- [docs/21_C207_MOTOR_RID_ABA_OBSERVATION_FORM.md](docs/21_C207_MOTOR_RID_ABA_OBSERVATION_FORM.md)：C-207
  电机 off→on→off 标准 RID A-B-A 观察表。
- [docs/22_COMMUNITY_DUML_RID_SURVEY.md](docs/22_COMMUNITY_DUML_RID_SURVEY.md)：2026-08-30
  社区 DUML/Remote ID 仓库调查与交叉引用。
- [evidence/claims.csv](evidence/claims.csv)：机器可读 claim 索引。
- [evidence/artifacts.csv](evidence/artifacts.csv)：机器可读工件索引。
- [projects/README.md](projects/README.md)：完整源码目录、状态与发布边界。

## 源码地图

- Android 应用：[RC 2 RID Admin](apps/rc2-rid-admin/README.md)、
  [隐藏设置启动器](apps/rc2-settings-launcher/README.md)、
  [v0.10 admission probe](apps/rid-admission-probe/README.md)、
  [normal-path carrier negative](apps/rc2-flysafe-agent-carrier/README.md) 与
  [PackageInstaller staging negative](apps/rc2-flysafe-agent-staging-payload/README.md)。
- 协议与模型：[protocol probes](libraries/protocol-probes/README.md)、
  [RID switch wire codec](libraries/rid-switch-wire-codec/README.md)、
  [type-6 inventory parser](libraries/rid-type6-inventory-parser/README.md)、
  [bounded controller](libraries/rid-switch-controller/README.md)、
  [quiescence model](libraries/rid-quiescence-model/README.md)、
  [OpenDroneID synthetic codec](libraries/opendroneid-synthetic-codec/README.md)。
- 主机工具：[ADB handshake](host-tools/adb-handshake-probe/README.md)、
  [exact-v07 adbd patch generator](host-tools/adbd-userspace-patch/README.md)、
  [system-UID bridge probes](host-tools/system-uid-bridge-probe/README.md)、
  [device read probes](host-tools/device-read-probes/README.md)、
  [RID switch control](host-tools/rid-switch-tool/README.md)、
  [firmware acquisition](host-tools/firmware-acquisition/README.md)、
  [IMaH analysis](host-tools/imah-analysis/README.md)、
  [ELF analysis](host-tools/elf-analysis/README.md)、
  [Ghidra scripts](host-tools/ghidra-scripts/README.md)、
  [runtime DEX boundary scanner](host-tools/runtime-dex-scan/README.md)。
- 实验源码：[same-process FlySafe query](experiments/jvmti/jvmti_flysafe_inprocess_query/README.md)、
  [country/area round trips](experiments/device-write/README.md) 与
  [JVMTI experiment sequence](experiments/jvmti/README.md)。撤回或尚未准入的路线保留原状态，
  不因为源码公开而变成已验证功能。

## 仓库内容边界

本仓库发布独立撰写的 Markdown/CSV、公开链接、版本号、命令标识、聚合结果、文件哈希，以及
可审阅的自研 APK/host-tool 源码和测试。源码公开不代表相应路线已通过实机验证；每个项目必须
保留 `OBSERVED`、`NOT ADMITTED`、`RETRACTED` 或 `UNKNOWN` 状态边界。

本项目目标是实现并验证可控的 Mini 5 Pro Remote ID 开关，以及具有独立证据链的 Basic/UAS ID、
飞机位置、操作者位置实验控制；Operator ID 保持独立。合成 codec 仅供离线验证，不添加 RF
发射后端。实验室声明已获得 DJI 及低空经济相关部门授权；因保密要求，授权材料不进入仓库，
也不在实机上注册。

不发布 DJI APK、固件、提取分区、厂商共享库、厂商反编译源码、原始私人抓包、
ADB/signing key、已打包 APK/JAR/SO、patched vendor binary、设备序列号、UAS ID、电话或坐标。

## License

[MIT](LICENSE) © 2026 Sapphire-Rapids。少量纳入的第三方源码保留原许可，见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
