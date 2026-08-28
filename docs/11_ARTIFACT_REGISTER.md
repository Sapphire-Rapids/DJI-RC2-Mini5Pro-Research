# 研究工件登记

## 1. 登记规则

本文件是 `evidence/artifacts.csv` 的人类可读镜像。两者逐项使用相同的 ID、名称、类型、版本、SHA-256、大小、审计状态、设备使用状态、处置和隐私分类。

本表不是下载清单。公开 hash 只用于识别研究所依据的 exact bytes，不产生再分发厂商 APK、固件、分区、共享库、DEX 或研究工件的权利。未在规范 CSV 登记的大小或 hash 在本表中写“未登记”，不从其他临时文件推断补齐。

状态标签遵循 [AGENTS.md](../AGENTS.md)。V2.2 的规范状态是 `RETRACTED`，其处置明确标为 `REJECTED / DO NOT USE`。V2.3 的规范状态是 `NOT ADMITTED`；修复完成不等于独立 post-fix audit 或 live admission。

## 2. 规范工件表

| ID | 工件 / 类型 / 版本 | 大小 | SHA-256 | 状态 |
| --- | --- | ---: | --- | --- |
| A-001 | RC 2 admission probe；self-developed；v0.10 | `2,570,983` | `fdad29bfb1237bc224a805d6eb5a99358a044bd226610d9f0fc33975d94b606c` | `NOT ADMITTED`；从未复制、安装或运行；当前候选但未 staging；只公开 hash |
| A-002 | Route-only resolver；self-developed；V2.2 | `29,019` | `7aa794ff8611582fd7cf27808a9d9eb11c44e307889d615d0511c100522845fb` | `RETRACTED`；从未复制、安装或运行；**REJECTED / DO NOT USE**；只公开 hash |
| A-003 | Corrected route-only resolver；self-developed；V2.3 | `29,019` | `49d5d1d3b6e2dcb72b23f48b688effb2be3f320bec6997a9dcb15779904156c2` | `NOT ADMITTED`；从未复制、安装、附加或运行；只作索引、不分发；只公开 hash |
| A-004 | RC 2 adjacent Android OTA；input-sample；RC331 `10.00.0700/0205` | `985,959,104` | `f707cf3dc0be2894b111ce4973d0206e896a2c7e9c4ebe43de1040b528cf49ce` | `STATIC`；相邻样本；排除且不分发；只公开 metadata |
| A-005 | RC 2 protected platform package；input-sample；RC331 `10.00.0700/0200` | `454,223,680` | `d8a8fe5b418ee6461f6971d9dfad77bc4491d15160d47d5cf8f7481dc7113949` | `STATIC`；仅作输入分析；排除且不分发；只公开 metadata |
| A-006 | DJI Fly analyzed application sample；input-sample；`1.21.10` | `719,464,897` | `0312228ad536381509c09dbfdf1c7e3d4c825c5936199f444058b112985deb3a` | `STATIC`；仅作输入分析；排除且不分发；只公开 metadata |
| A-007 | DJI MSDK public analysis inputs；input-sample；`5.18.0` | 未登记 | 未登记 | `STATIC`；仅作输入分析；只保留公开 reference |
| A-008 | WA150 encrypted aircraft package sample；input-sample；product-139 family | 未登记 | 未登记 | `STATIC`；仅作输入分析；排除且不分发；只公开 metadata |
| A-009 | ARM64 JVMTI environment canary；self-developed；V0 | `8,528` | `4a3867251a745ce5db6c0513c23def5c97e53a57e17f4d611621895e4e323c73` | `NOT ADMITTED`；从未复制、安装或附加；只作索引、不分发；只公开 hash |
| A-010 | France EID semantic-anchor probe；self-developed；V1 | `8,531` | `ccdf198c83ecdd3d33a54192e2bffeb9ab89ce65289497643d16f5a00bff62b2` | `NOT ADMITTED`；从未复制、安装或附加；只作索引、不分发；只公开 hash |
| A-011 | Route-only resolver；self-developed；V2.1 | `16,731` | `7f0159619f89f7c6a9849b1028003a1070d97988838da7a6ef027e09626ada0d` | `NOT ADMITTED`；从未复制、安装或附加；只作索引、不分发；只公开 hash |
| A-012 | Historical RC-local observer family；self-developed；v0.1–v0.4 | 未登记 | 未登记 | `RETRACTED`；历史退役；禁止使用；只公开 metadata |
| A-013 | Rejected multi-capability Android input sample；input-sample；未版本化第三方样本 | 未登记 | 未登记 | `NEGATIVE`；从未安装；拒绝并排除；只公开 metadata |
| A-014 | Non-flashable integrity mutation sample；self-developed；offline-only | `679,295,296` | `dafe2c69e0ccf5ebeeaed2e9fd894f3ee3ac997453bc2b247c499aefe64a3fff` | `NOT ADMITTED`；从未传输或刷写；已销毁、不保留；只公开 hash |
| A-015 | WA150 encrypted cross-version input set；input-sample；`01.00.0600` 与 `01.00.0700` | 未登记 | 未登记 | `STATIC`；仅作输入分析；排除且不分发；只公开 metadata |
| A-016 | NLD FCC Smart RC distribution；input-sample；`2.0.0.6` bundle | `6,932,568` | `e75011e8190098aff12219d687c17b93495993890bf4a96212856174087a5100` | `STATIC`；本轮仅离线分析、无设备动作；排除且不分发；只公开 metadata |
| A-017 | NLD FCC Smart RC main APK；input-sample；`2.0.0.6` / code 46 | `7,278,464` | `1035f0aa22e158fd1703e14dd3bd2198845da4c2113454f9ac3a4569c41ee474` | `STATIC`；本轮仅离线分析、无设备动作；排除且不分发；只公开 metadata |
| A-018 | NLD bundled Package Installer helper；input-sample；Android 11 / code 30 | `3,274,224` | `523361acbe62587fa61e00a92369e87daa0d812232b8942deba67771ccf2633a` | `STATIC`；本轮仅离线分析、无设备动作；排除且不分发；只公开 metadata |
| A-019 | Drone-Hacks Windows MSI；input-sample；`2.0.29` | `16,289,792` | `a4c3867e34235a74b5df37ae81bc19f80a988e26e47b408947224e6c8247fd8d` | `STATIC`；与官网下载 MSI 相同且签名有效；从未安装或执行；排除且不分发 |
| A-020 | Drone-Hacks desktop application；input-sample；`2.0.29.0` | `24,011,848` | `9813d6a9d7ba137066712ecfebd2c397bfbe5516d546c6d5f95d23014e06f996` | `STATIC`；只从 MSI 静态提取；从未执行；排除且不分发 |
| A-021 | Drone-Hacks TypeScript binding generator；input-sample；`2.0.29.0` | `11,522,632` | `84eecdf2329635bf9856a9ea002c9696d4222cd56cafdc101c9f19bea809e652` | `STATIC`；只从 MSI 静态提取；从未执行；排除且不分发 |
| A-022 | SKYROVER official Android application；input-sample；`1.2.0` / code `102001130` | `405,543,495` | `8f5590f5f61194b186ac8e4a670e5b2182551a653eda2bb0c0ce23b696c554b8` | `STATIC`；只离线分析；从未安装或执行；排除且不分发 |
| A-023 | FindUAS RC 2 RID Admin；self-developed；`0.3.0-research` | `64,745` | `271ca3a415c7258919889a44983145671d6771be64803f6fe75289937bdc7c59` | `OBSERVED`；已安装并执行一次只读 Binder F7 probe；无 F9；已由 A-024 取代且从 removable storage 清理；不进入本 documentation repo |
| A-024 | FindUAS RC 2 RID Admin；self-developed；`0.4.1-research` | `92,569` | `68f9b0d42d42e1bcb674ddba88a3996229d06978e35e30a355f253678a8e2b95` | `OBSERVED`；已安装并执行只读双路 positive-control 与 30 秒 listener；target 未发送、无 F9；listener 经独立 RF 对照判为假阴性；由下一 inventory 版本取代；不进入本 documentation repo |
| A-025 | FindUAS RC 2 RID Admin；self-developed；`0.5.0-flysafe-readonly` / code 8 | `111,889` | `b137540f041cceb50a215bb95144c9f7ccf57fa4db4d2e7fc2108cb6ae68db80` | `OBSERVED`；exact final-artifact audit；MTP/readback 已闭合，用户随后明确报告安装完成；启动、执行与结果仍未知；由 A-026 取代；不进入本 documentation repo |
| A-026 | FindUAS RC 2 RID Admin；self-developed；`0.6.0-flysafe-gated` / code 9 | `135,525` | `3c2ae42ac9f19a9e3dfe669ed6357bb8d2f1c38568af6a0f8d8b8f677fcbfec4` | `OBSERVED`；exact final-artifact audit；MTP/readback/新会话唯一短名与 size 已闭合，用户随后明确报告安装完成；启动、执行与结果仍未知；current gate-aware FlySafe candidate；不进入本 documentation repo |

## 3. A-001：当前 v0.10 admission probe

`STATIC`：A-001 是当前 zero-permission admission-probe 候选，覆盖旧 v0.8 状态。其 schema 为 `finduas-rid-probe/v0.10-schema-1`。离线 final-artifact audit 记录：

- 43 tests 通过；
- 21/21 adversarial audit mutations 被拒绝；
- 两次 clean build byte-identical；
- 零 Android permission；
- 无 service、receiver、provider 或 packaged native library；
- 无 socket、localhost、DUML、application Binder transaction、process execution、file persistence、agent attach 或 library load path。

`NOT ADMITTED`：A-001 尚未复制、安装或运行在 RC 2。即使将来得到 `COMPLETE` report，也只建立报告声明的环境/身份事实，不建立 RID 状态、Binder transaction authorization、attach permission 或 setter admission。

旧 v0.8/v0.9 只作为本地 provenance 保留，不是当前 staging instruction。v0.1–v0.4 统一登记在 A-012，因 localhost second-client 架构而 `RETRACTED`。

## 4. A-002：V2.2 永久拒绝

V2.2 的规范登记是：

```text
audit_state:     RETRACTED
device_use:      never-copied-installed-or-run
disposition:     REJECTED / DO NOT USE
```

独立审计发现两个 P1 和一个 P2：

1. whole-file/maps/linker gate 完成前过早读取 runtime program headers；
2. 对原始 non-writable segment 接受 writable runtime coverage；
3. 未拒绝 `st_dev == 0`。

V2.2 的 passing built-in audit 没有覆盖这些问题。A-002 永久 `REJECTED`，不得安装、附加、复活或因 V2.3 存在而改变处置。

## 5. A-003：V2.3 修复后封存

`STATIC`：V2.3 是 distinct corrected artifact，记录的 project audit 修复 V2.2 三项 finding，并维持：

- immutable/fixed-zero exception gate；
- zero-send；
- 无 DEX/component/permission/shared UID；
- 无 DUML、JNI GET/SET/listen/send、socket、Binder、process execution 或 filesystem write；
- 从未复制、安装、附加或执行于 RC 2。

`UNKNOWN`：没有新的 independent post-fix audit report。项目自身 packaged audit、host tests 和可复现构建不能被改写成独立审计结论。

因此 A-003 保持 `NOT ADMITTED`。即使未来独立审计通过，fixed-zero/zero-send 设计也只支持离线 route evidence，不自动授权上机或执行 DJI-owned call。

## 6. A-009 至 A-011：V0、V1、V2.1

- A-009 V0 只检查 loader/JVMTI environment reachability；不枚举 DJI class，不读或写 EID/RID。
- A-010 V1 只计数 already-loaded France-EID semantic anchors 及 shared ClassLoader；不调用 Java、不 GET/SET/listen/send。
- A-011 V2.1 是 route-only resolver；fixed-zero gate 使 dormant target-owned route 不可执行。

三者均为 `NOT ADMITTED` 且未上机。V0、V1、V2.1 之间存在依赖顺序，但 hash 或 static success 不替代 live v0.10、caller、SELinux、ABI、mapping、exception、epoch 和 quiescence 门禁。

## 7. NLD FCC Smart RC 输入样本

A-016 至 A-018 记录本次 NLD 静态分析的外层分发包、主 APK 和安装器 helper。外层包在
2026-08-28 与官网 Smart RC 下载 bytes 相同；主 APK manifest 为 `2.0.0.6`/code 46。三个工件
均只在排除的工作区中离线读取；本轮没有安装、执行、动态加载或传输到设备，也未调用 NLD API。
这不追溯判断用户在其他时间是否曾使用相同 hash 的 helper。

这些 hash 只支持 exact-input 复核。仓库不分发 APK、native library、DEX、反编译源码或安装
说明正文。Package Installer helper 的签名 subject 提及 DJI 且签名校验有效，但不能仅凭 subject
文字推断其来源或其在任一精确 RC 2 平台上的特权。

详细结论见 [NLD FCC Smart RC 静态分析](16_NLDFCC_STATIC_ANALYSIS.md)。

## 8. Drone-Hacks 输入样本

A-019 至 A-021 记录官方 Windows 分发包及其两个 PE payload。用户输入 MSI 与官方 release ZIP
内 MSI 的大小和 SHA-256 完全一致；三个 Windows 工件的 Authenticode 签名均验证为
Skymod Technologies LTD。签名只建立来源/完整性边界，不证明功能或安全性。

本轮没有安装 MSI、运行 PE、登录账号、请求受保护 job/license、提交设备标识或连接设备。
客户端静态结论和公开支持快照见
[Drone-Hacks 2.0.29 静态分析](17_DRONE_HACKS_STATIC_ANALYSIS.md)。

## 9. 输入样本与分发

A-004 至 A-008、A-013、A-015 至 A-022 是 input-sample 或 rejected third-party input。它们不属于本仓库实现，不能提交二进制或复制正文。允许保留的内容只有：

- 公开版本和产品族；
- 在规范 CSV 明确登记的 public hash；
- independently written 高层结论；
- 公开来源或固定 revision；
- “相邻”“受保护”“加密”“未安装”“不分发”等边界。

厂商输入的补充身份只在 [固件与信任边界](07_FIRMWARE_TRUST_BOUNDARY.md) 中作为样本 provenance 描述，不增加本规范 artifact CSV 的行，也不代表本仓库提供样本。

## 10. SKYROVER 与固定 RID 管理客户端

A-022 是从官网 direct download 冻结的 current SKYROVER `1.2.0` 输入。静态分析只用于恢复
`RIDCtrlEnable` 的高层 access flags、应用 capability-probe 行为、FC parameter mapping 和
F7/F8/F9 protocol facts。APK、native libraries、DEX 和反编译输出全部留在排除工作区；MIT
仓库只保留独立表述、exact hash 和公开 URL。

A-023 是 clean-room self-developed Android artifact，package
`com.finduas.rc2ridadmin`。最终 APK 经 11 项 unit tests、lint（0 errors）、两次 byte-identical
clean build、manifest/permission、zipalign、APK v2 signature 和 decompiled-final 检查；不包含
permission、native library、socket、shell 或 background service。固定 command allow-list 为
France EID `03/77`、OPID `03/78` 和 `rid_ctrl_enable_0` 的 `03/F7-F9`；RID route 固定为
`0x82 -> 0x92`，使用 RC 2 `protocol` Binder service。它随后已安装并执行一次固定只读 F7：
service lookup、Binder transaction 与 callback exception layer 均完成，目标以 `ECode 1`
结束，未取得 F7 ACK，也未发送 F9。因为该版本没有同路由已知参数正对照，结果不能提升为
parameter-absence 结论。A-023 已被替换并从 removable storage 清理；本地可重建工件不进入仓库。

A-024 是已完成实机实验的历史替代工件，package 与 signer 不变。它先在每个候选 Binder route 上执行
maximum-height F7/F8 正对照，只有正对照成功才解释 `rid_ctrl_enable_0`；所有操作串行，F9 只有在
target metadata、attribute、range 和 Boolean baseline 均闭合后才解锁，写后使用重复 F8 readback，
歧义时恢复操作前值。它还通过 transaction 2 注册一次只读 `0x11/0x1C` listener，完整记录
30 秒有界状态时间线，并在保存结果后终止自身进程以触发 Binder-death 清理。最终 APK 经 25 项
unit tests、lint（0 errors，12 warnings）、两次 byte-identical clean build、manifest/permission、
zipalign、APK v2 signature 和 native-library 检查；无声明 permission 或 native library。它已以
短文件名 `RID-Admin.apk` 复制到 RC 2 removable storage，随后已确认安装并运行一次参数 probe。
legacy `0A:05 -> 03:00` 与 modern `02:04 -> 12:04` 两路 maximum-height F7 正对照均在约
3.1 秒后以 `ECode 1` 结束且无 data；代码按门禁没有发送 target F7/F8/F9。随后 transaction-2
listener 在 9 ms 内被接受并运行完整 30 秒，但 callback/valid/malformed/state count 全为 0；
操作者在窗口内起桨，独立检测器确认飞机实际播报 RID。故该 listener 被归类为假阴性，不再作为
readback oracle。应用按设计在保存后关闭；未观察到由此造成的 DJI Fly/link 异常。

A-025 是已审计并由用户报告安装完成、但没有启动/执行/结果记录的旧 modern FlySafe inventory baseline，package 保持
`com.finduas.rc2ridadmin`，versionCode 8、versionName `0.5.0-flysafe-readonly`。新增主流程只通过
system `protocol` Binder transaction 4 固定发送 `02:04 -> 12:04`、`11/11`、6,000 ms 的 V3/V4
group/page 请求；selector、ccode、空 terminator、count/page/overall deadline 与 protobuf parser
均严格有界。该 FlySafe lane 没有获准的 `11/12` tuple，单元测试明确拒绝 setter；已证假阴性的
旧 `11/1C` listener 按钮从 UI 移除。其 field-7 decoder 是独立 MSDK-compatible candidate；exact
current Fly typed parser 只处理 fields 1--5，不能据 A-025 声称 current Fly 自身理解 type 6。

隐私审计确认清单结果只保留 count、RID level 与 status bits。license ID 只生成本会话随机加盐的
判重 fingerprint，连同 salt 和 response copy 在使用后清零；SN、user ID、description、date、
geometry、signed data 和 raw protobuf 不进入显示或持久化。`flysafe-readonly` 是新增清单 lane 的
边界，不是整个 APK 的全局描述：A-024 已有、各自受门禁约束的 F7/F9、France EID 与 OPID 实验功能
仍在工件内。

最终 A-025 经 clean `testDebugUnitTest lint assembleDebug`，42 tests 全通过、lint 0 errors/9
warnings，第二次 clean build byte-identical，v2 signature 与 zip alignment 验证通过；manifest
声明零 Android permission，APK 无 packaged native library，检查未发现 network/socket/shell path。
最终工件为 `111,889` 字节，SHA-256
`b137540f041cceb50a215bb95144c9f7ccf57fa4db4d2e7fc2108cb6ae68db80`。2026-08-29，工件已
通过 RC 2 MTP 写入 removable SD 的 `Download`，短文件名为 `FindUAS_A025_RID.apk`；同一传输会话
读回所得 SHA-256 与登记值一致。一个意外产生的长文件名副本已删除，仅保留短名副本。该观察只证明
staging byte identity 与 duplicate cleanup，不包含 storage、USB 或 device serial。MTP 交付时尚无
用户确认安装或运行结果；用户随后明确报告“A-025 APK 安装完成”，因此 artifact device-use state 与 C-163 记录为
`OBSERVED`；该事实不证明应用被打开、发送 Binder 请求、返回 inventory、改变设备状态或产生 RF
结果。A-025 已由 A-026 取代；二进制和源码均不进入本 documentation-only repository（C-154/C-163）。

APK signer certificate SHA-256：
`37896e5a80772e39edad4bdf3ce7f19d2b6e1352a701c48c70edc10c97b2b224`。

## 11. A-026：gate-aware FlySafe Admin candidate

A-026 package 仍为 `com.finduas.rc2ridadmin`，versionCode 9、versionName
`0.6.0-flysafe-gated`。它把 C-159 的 gate-aware 方向实现为一个不可跨进程转移的 permit：同一 tx2
listener 被动接收 `03/09` version 与 `03/42` support，只有两者的完整实际 route 一致、payload
usable、support=true 且 version 为 V3/V4 时才在同一进程内允许后续 fixed `11/11` query。malformed、
failure callback、route/value conflict、deadline 与 cancellation 均不签发 permit；没有 permit 时不发
inventory 请求。

permit 后仍只使用固定 system-Binder transaction 4 FlySafe sender：group selector 后严格按 page
0..127 遍历，selector、page 次数、count 与 terminator 都 fail closed。tx4 callback 等待预算覆盖初发与
两次各 6 秒重试，避免在 vendor retry 仍可能到达时提前把本次 query 判死。内部 sender allow-list 不含
`11/12`。结果仍只保留 privacy-reduced count/level/status；完成、失败或取消后清理 listener，并以进程
termination 触发 Binder-death cleanup。

这不是整个 APK 的 global read-only 声明。外部 DJI Developer Assistant launcher 不由内部 sender
allow-list 约束；APK 也继续保留各自受原有门禁约束的 F9、France EID 与 OPID write controls。因此名称
和用途为 RID Admin，`flysafe-gated` 只描述新的 FlySafe gate/query lane。

最终工件经两次独立 clean `testDebugUnitTest lintDebug assembleDebug`；63/63 tests 通过，lint 为
0 errors/13 warnings，两次 APK byte-identical。V2 signature 与 zipalign 验证通过；manifest 为零
`uses-permission`，APK 无 packaged native library，检查未发现 network/socket/shell path。最终大小
`135,525` bytes，SHA-256
`3c2ae42ac9f19a9e3dfe669ed6357bb8d2f1c38568af6a0f8d8b8f677fcbfec4`（C-160/C-161）。

2026-08-29，A-026 已通过 RC 2 MTP 写入 removable SD `Download`，短名
`FindUAS_A026_GATE.apk`。同一会话读回 SHA-256 与登记值一致；重新建立 MTP 会话后的目录清单又确认
仅有一个该短名且 size 为 `135,525` bytes。此处不记录 object/storage/USB/device serial。该交付只证明
staged-file identity/uniqueness（C-162）。用户随后明确报告“A-026 APK 安装完成”，因此安装记为
`OBSERVED`（C-164）；这不证明启动、执行、passive callback、permit、Binder query/result、inventory、
state 或 RF，以上仍为 `UNKNOWN`，且不记录 package-manager telemetry 或 private device identifier。

## 12. 更新与一致性检查

修改本表时必须同时更新 `evidence/artifacts.csv`，并运行：

```sh
ruby scripts/check_evidence_csv.rb
sh scripts/check_sensitive_patterns.sh
```

不得仅更新 Markdown 或仅更新 CSV。若当前任务无权修改 CSV，则新工件保持在候选审计记录中，等待拥有索引更新权限的维护者一次性加入两处。
