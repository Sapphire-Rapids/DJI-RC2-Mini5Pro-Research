# 研究工件登记

## 1. 登记规则

本文件是 `evidence/artifacts.csv` 的人类可读镜像。两者逐项使用相同的 ID、名称、类型、版本、SHA-256、大小、审计状态、设备使用状态、处置和隐私分类。

本表不是下载清单。公开 hash 只用于识别研究所依据的 exact bytes，不产生再分发厂商 APK、固件、分区、共享库、DEX 或研究工件的权利。未在规范 CSV 登记的大小或 hash 在本表中写“未登记”，不从其他临时文件推断补齐。

状态标签遵循 [AGENTS.md](../AGENTS.md)。V2.2 的规范状态是 `RETRACTED`，其处置明确标为 `REJECTED / DO NOT USE`。V2.3 的规范状态是 `NOT ADMITTED`；修复完成不等于独立 post-fix audit 或 live admission。

## 2. 规范工件表

| ID | 工件 / 类型 / 版本 | 大小 | SHA-256 | 状态 |
| --- | --- | ---: | --- | --- |
| A-001 | RC 2 admission probe；self-developed；v0.10 | `2,570,983` | `fdad29bfb1237bc224a805d6eb5a99358a044bd226610d9f0fc33975d94b606c` | `NOT ADMITTED`；MTP staging/完整读回匹配；本版本安装/运行未确认；历史 APK 已移入 SD Archive，报告探针由 A-039 接续；只公开 hash |
| A-002 | Route-only resolver；self-developed；V2.2 | `29,019` | `7aa794ff8611582fd7cf27808a9d9eb11c44e307889d615d0511c100522845fb` | `RETRACTED`；从未复制、安装或运行；**REJECTED / DO NOT USE**；只公开 hash |
| A-003 | Corrected route-only resolver；self-developed；V2.3 | `29,019` | `49d5d1d3b6e2dcb72b23f48b688effb2be3f320bec6997a9dcb15779904156c2` | `NOT ADMITTED`；从未复制、安装、附加或运行；只作索引、不分发；只公开 hash |
| A-004 | RC 2 adjacent Android OTA；input-sample；RC331 `10.00.0700/0205` | `985,959,104` | `f707cf3dc0be2894b111ce4973d0206e896a2c7e9c4ebe43de1040b528cf49ce` | `STATIC`；相邻样本；排除且不分发；只公开 metadata |
| A-005 | RC 2 protected platform package；input-sample；RC331 `10.00.0700/0200` | `454,223,680` | `d8a8fe5b418ee6461f6971d9dfad77bc4491d15160d47d5cf8f7481dc7113949` | `STATIC`；仅作输入分析；排除且不分发；只公开 metadata |
| A-006 | DJI Fly analyzed application sample；input-sample；`1.21.10` | `719,464,897` | `0312228ad536381509c09dbfdf1c7e3d4c825c5936199f444058b112985deb3a` | `OBSERVED`；仅在 disposable emulator 安装/运行并作 runtime 分析；排除且不分发；只公开 metadata |
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
| A-026 | FindUAS RC 2 RID Admin；self-developed；`0.6.0-flysafe-gated` / code 9 | `135,525` | `3c2ae42ac9f19a9e3dfe669ed6357bb8d2f1c38568af6a0f8d8b8f677fcbfec4` | `OBSERVED`；exact final-artifact audit；`installed-and-run-gate-unobserved-zero-query`；首次 60,003 ms gate 窗口无任何 callback、无 permit、无 `11/11`；已由 direct-readonly branch 取代；不进入本 documentation repo |
| A-027 | FindUAS RC 2 RID Admin；self-developed；`0.7.0-flysafe-direct-readonly` / code 10 | `196,569` | `aa4bcd9c8aa96870cfbae1ba326d366cb8854a50ef4aff223f7bce4290ddcd81` | `OBSERVED`；exact audit/MTP/install/run；active result 为 `ProtocolException`-class ambiguous，`11/12 count=0`；无 canonical inventory/write；已由 A-028 取代；不进入本 documentation repo |
| A-028 | FindUAS RC 2 RID Admin；self-developed；`0.7.1-flysafe-direct-diagnostic` / code 11 | `197,061` | `d7c32636e19d1bce1b8b8994206355f42d0278b2f15048b14a948a8bbda1d540` | `OBSERVED`；exact audit/MTP/install/run；current direct-readonly transport diagnostic result；group transport callback failed，`11/12 count=0`；无 protobuf/page/terminator/write；不进入本 documentation repo |
| A-029 | RC331 v07 system aggregate；input-sample；`07.00.0100` | `1,446,604,800` | `296cfa63e3c6b011fd1ee8dd911c11f64dac9d34a8424a6fbb95b0c237ab1ae3` | `STATIC`；signed-chain verification 与离线提取；排除且不分发；只公开 metadata/hash |
| A-030 | RC331 v07 APEX `adbd`；input-sample；`07.00.0100` | `1,497,232` | `b300d9bb90f5941fe2952bc9f6dacc30e639a498be4435f59a4ae95134bd5422` | `STATIC`；从 exact signed package 离线提取并审计；排除且不分发；只公开 hash |
| A-031 | RC331 v07 DJI development assistant；input-sample；`07.00.0100` `dpad_fuli` | `8,849,471` | `58b176eb1e17cacb7522914d282a69a677603ea9026993fc143c6a390211e44f` | `OBSERVED`；原实机 APK/hash 匹配；原包 MTP/readback 匹配，用户已安装并打开 DevActivity；Shell/复测待完成；排除且不分发；只公开 hash |
| A-032 | RC331 v07 APEX `adbd` CNXN-gate derivative；input-sample；userspace copy | `1,497,232` | `3fceaa1724a77a153c17f725a2e3f3001b0543e31e0830aca0c77d785df9225f` | `NOT ADMITTED`；MTP staging/readback 闭合；未复制到内部存储、未 chmod、未执行；vendor derivative 排除且不分发 |
| A-033 | FindUAS RC 2 RID Admin；self-developed；`0.8.0-flysafe-diagnostic-export` / code 12 | `204,449` | `8ce8e0c13ecfcf69517a64e809a475b79bbc750124225744b6b35f281d3d7177` | `STATIC`；exact audit；MTP staged/readback matched；未安装或运行；sealed APK 排除，源码公开 |
| A-034 | DJI Fly runtime private mapping；runtime-derived input；`1.21.10` disposable emulator | `205,443,072` | `2926709cc6896c7315d003c4e61208d5a9fa53ae73cda897d820a581c5c8325c` | `OBSERVED`；authorized read-only emulator process-memory copy；仅本地分析；排除且不分发；只公开 hash |
| A-035 | FindUAS FlySafe agent carrier；self-developed；`0.1.0-emulator-observed` | `23,032` | `16a59c1996e817891dfb84208202cb942456095d4ee98dfa7d8eb17c4c10f289` | `NEGATIVE`；disposable emulator normal installed path 在首个 `=` 被截断；未在 RC 2 使用；generated APK 排除、源码公开 |
| A-036 | FindUAS FlySafe ART TI staging payload；self-developed；`0.1.0-emulator-observed` | `38,998` | `20a96fdd834e921b546105fd0b2314393a33d242690f731a776c867f70e47069` | `NEGATIVE`；disposable emulator uncommitted `apk_tmp_file` search denied，session 已 abandon；未在 RC 2 使用；generated APK 排除、源码公开 |
| A-037 | FindUAS RC 2 RID Admin identity safety lock；self-developed；`0.8.1-identity-safety-locked` / code 14 | `225,937` | `8ee7a4edd36c7f97c631fabf3186ac3df79e6611869ebf05b11e83ccba4e84ba` | `NOT ADMITTED`；仅离线构建/测试，未 staged、安装或运行；generated APK 排除、源码公开 |
| A-038 | RC 2 probe with SD report export；self-developed；`0.11.0-report-export` / code 11 | `2,601,935` | `aaa6f8bf22002c907d8de89fff58c04755bbfdd08feed4ec0f8771d6eb8044aa` | `OBSERVED`；已安装运行并收到报告，ART build-ID 检查 INCOMPLETE；历史 APK 已移入 SD Archive，由 A-039 接续；generated APK 排除、源码公开；只公开 artifact hash |
| A-039 | RC 2 ARM32 probe and installed Fly sample exporter；self-developed；`0.12.0-live32-samples` / code 12 | `2,651,903` | `46eb6ef19971256a02514fc51a94b21522c488d82294c8853a7beb52fbab3ce4` | `OBSERVED`；MTP/readback 匹配、已安装运行；COMPLETE 报告与样本收到；当前版本，generated APK 排除、源码公开；只公开 hash/source |
| A-040 | FindUAS pure ARMv7 ART TI canary；self-developed；`art-ti-canary-v1-armeabi-v7a` | `4,340` | `9b02f2b3a7e5a8e2afb200bd7d1fae2e75d2753eaa9c7ea86071dd47cccf086a` | `NOT ADMITTED`；MTP staged/完整读回匹配；未复制到内部、未 attach/运行；generated SO 排除、源码公开；只公开 hash/source |
| A-041 | DJI Fly exact live ARM32 application sample；input-sample；`1.19.4` / code `3113157` / armeabi-v7a | `426,180,752` | `fb695817a885bd9d4084643d8cae07285a8ac560b6e94edd5c87af4a70b8528c` | `OBSERVED`；从既有实机安装导出，收到后独立完整验证；排除且不分发；只公开 hash |
| A-042 | FindUAS ARMv7 FlySafe read-only query agent；self-developed；`device-id-minus-one-guard-armeabi-v7a` | `15,464` | `88d88ba10396a790d5d6675e70b44a21c01a71bbb92b4c80978998837ae75e25` | `NOT ADMITTED`；离线构建与 host 检查通过；未 staged、未在 RC 2 attach/运行；generated SO 排除、源码公开；只公开 hash/source |

## 3. A-001：历史 v0.10 admission probe

`STATIC`：A-001 是历史 zero-permission admission-probe 候选，曾覆盖旧 v0.8 状态；当前版本为 A-039。其 schema 为 `finduas-rid-probe/v0.10-schema-1`。离线 final-artifact audit 记录：

- 43 tests 通过；
- 21/21 adversarial audit mutations 被拒绝；
- 两次 clean build byte-identical；
- 零 Android permission；
- 无 service、receiver、provider 或 packaged native library；
- 无 socket、localhost、DUML、application Binder transaction、process execution、file persistence、agent attach 或 library load path。

`OBSERVED`（C-231，2026-08-30）：保存的精确 APK 再次通过源码/final-DEX 审计及 21/21 mutation 检查；已作为单个新文件 `Download/FindUAS_A001_V010.apk` 放入 RC 2 removable SD。fresh 唯一文件名/大小检查及同会话完整读回 SHA-256 均匹配，没有重传或覆盖旧文件。

`NOT ADMITTED`：安装与运行仍待操作者确认。即使将来得到 `COMPLETE` report，也只建立报告声明的环境/身份事实，不建立 RID 状态、Binder transaction authorization、attach permission 或 setter admission。

C-244：A-001 的 SD APK 已移入 `Download/FindUAS/Archive`，没有删除；这不补充本版本的安装/运行记录。

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
结果。A-025 已由 A-026 取代；sealed APK 和精确历史源码快照不入库。后续持续演化的 clean-room
源码现发布于 `apps/rc2-rid-admin`，不能反向当作 A-025 的逐字节源码身份（C-154/C-163）。

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
`OBSERVED`（C-164）。其后按既定流程完成首次 60,003 ms gate run：`03/09`、`03/42` 和所有 callback
分类计数均为 0，结果 `GATE_UNOBSERVED`，所以 fail-closed sender 的 `11/11 request count=0`
（C-165）。artifact device-use state 因此为 `installed-and-run-gate-unobserved-zero-query`。这只证明
本次 third-party passive listener 没形成观察面；不证明 aircraft unsupported、无 entitlement、empty
inventory、RID off/no RF 或 official in-process observer 缺失。没有记录 package-manager telemetry、
private device identifier、raw frame 或 license material；也没有 write、motor action 或 independent RF
observation。

## 12. A-027：active direct-readonly FlySafe result

A-027 package 仍为 `com.finduas.rc2ridadmin`，versionCode 10、versionName
`0.7.0-flysafe-direct-readonly`。其新按钮只允许一次 fixed system-Binder transaction-4
`02:04 -> 12:04`、`11/11` V3/V4 group/page query；不扫描 route，不做应用层 retry。只有严格
count/page/terminator/schema completion 才形成 inventory，其他结果保持 unavailable/ambiguous。

最终工件经两次独立 clean build，APK byte-identical；127 tests 为 0 failures/errors/skips，lint 为
0 errors/15 warnings。V2 signature 与 zipalign 验证通过；manifest 声明零 permission，final-artifact
检查未发现 packaged native library、network、socket、shell 或 external-process execution path。
最终大小 `196,569` bytes，SHA-256
`aa4bcd9c8aa96870cfbae1ba326d366cb8854a50ef4aff223f7bce4290ddcd81`（C-166/C-167）。

2026-08-29，A-027 已通过 MTP staged 到 removable SD `Download/FindUAS_A027_RO.apk`；fresh
listing size 与登记值一致，readback SHA-256 也匹配（C-168）。操作者随后安装并运行主动只读按钮。
进入 strict inventory parser 后，屏幕结果为 `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`，
阶段 `ProtocolException`，并显示 `11/12 request count=0`（C-169）。因此 device-use state 为
`installed-and-run-direct-v3-v4-query-unavailable-ambiguous-no-write`。

该 UI 没有显示 exception message，故不能进一步区分 callback、ccode、group、page 或 terminator
阶段；它不证明 unsupported、empty inventory、no `RID_UNLOCK`、RID off 或 RF state。截图不入库，
且未记录 storage/USB/device identifier、raw reply、license ID 或 account material。sealed APK
不入库；后续源码 successor 发布于 `apps/rc2-rid-admin`，不声称是 A-027 的 exact snapshot。

## 13. A-028：direct-readonly diagnostic result

A-028 package 仍为 `com.finduas.rc2ridadmin`，versionCode 11、versionName
`0.7.1-flysafe-direct-diagnostic`。它仅扩展 A-027 的安全 UI 诊断：静态
`ProtocolException` message、unexpected group/page ccode 数值及 page index、terminator data
length。command、固定 `02:04 -> 12:04` route、V3/V4 selectors 和 write boundary 不变。

最终工件 127 tests 通过，lint 0 errors/15 warnings，两次 clean build byte-identical；v2 signature、
zipalign、zero permissions、no packaged native library 通过。最终大小 `197,061` bytes，SHA-256
`d7c32636e19d1bce1b8b8994206355f42d0278b2f15048b14a948a8bbda1d540`（C-170/C-171）。

2026-08-29，A-028 已通过 MTP staged 到 removable SD `Download/FindUAS_A028_DIAG.apk`；fresh
listing size 与登记值一致，readback SHA-256 匹配（C-172）。操作者随后安装并运行；结果为
`DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`、`ProtocolException`，细分
`group transport callback failed`，`11/12 count=0`（C-173）。当前 device-use state 为
`installed-and-run-group-transport-callback-failed-no-write`。固定 group selector 未得到成功 transport
callback，未进入 protobuf/pages/terminator。当前 UI 不显示 Reply failure/ecode/callback diagnostic；
不提交 APK、结果图片、device identifier、raw reply 或 license material。仓库公开的是加入诊断文件
持久化后的未发布源码 successor，并明确标记为未分配新版本、未安装、未运行。

## 14. A-029 至 A-032：exact v07 ADB 静态链与未执行 userspace copy

A-029 来自第三方 firmware archive，但其内部 signed configuration 与 `0205` module 已用
`PRAK-2020-01` 完成 header signature、stored/encrypted checksum 和 decrypted/plaintext
checksum 验证，过程中没有 `--force-continue`、skip 或 truncate。该链把 A-030 与 A-031 锚定
到 DJI-signed `07.00.0100` package；并不把第三方 archive 本身描述成 DJI 官方来源，也不证明
当前实机 mounted file 与 archive 逐字节一致。

A-030 是 exact APEX `adbd`。运行时 service path 是
`/apex/com.android.adbd/bin/adbd`；`/system/apex/com.android.adbd/bin/adbd` 是离线 filesystem
backing path，exact target image 没有 `/system/bin/adbd`。A-030 与此前审计的相邻样本
`cmp` 相等，因此 target-version gate 结论不再只是 adjacent inference。

A-031 是 exact package 中的 `dpad_fuli.apk`。它与已审计样本逐字节相等，所以 manifest、
`ShellCommandActivity` 和 `Runtime.exec` 行为是 target-package `STATIC` 事实。C-235/C-237 的实机报告后来核对了原安装 APK/hash、平台 signer 和 system-shared-UID 身份。C-242 又记录原包 MTP staging/readback 匹配及用户安装后打开 DevActivity；未进入 Shell 页。当前尚无安装后 probe、Shell output 或 loader 执行结果。

A-032 是 vendor-derived、不可分发的 userspace-copy 实验工件。语义 patcher 只将 exact A-030
的 `handle_packet(CNXN)` gate-value instruction 从 `cset w21, lt` 改为 `mov w21, wzr`，保持
普通 TLS/auth target。三处实际 byte difference 均位于同一四字节 instruction；embedded
Build ID 没有重写，所以 A-032 必须用 whole-file SHA-256 识别。

`OBSERVED`：A-032 已通过 MTP 写入 removable-SD `Download/RC2_ADBD_CNXN.bin`。fresh session
listing 得到一个同名 `1,497,232`-byte object，完整读回 SHA-256 与表中登记值一致。没有记录
MTP object、storage、USB 或 device identifier。

`NOT ADMITTED`：A-032 尚未复制到 controller internal executable location、未 chmod、未执行；
没有停止 init-managed daemon、没有得到 ADB packet、没有 shell。Git 仓库只保留 identity、
独立描述与准入边界，不包含 A-029/A-030/A-031/A-032 bytes、厂商反编译正文或 patched manifest
中的本机路径。

## 15. A-033：diagnostic export candidate

A-033 保持 A-028 的 fixed `02:04 -> 12:04`、`0x11/0x11`、V3/V4 selector 与 direct-button
zero-`0x11/0x12` 边界。新增功能只是把同一 privacy-reduced result 同时写入 app-private external
files 和 MediaStore `Download/FindUAS/FindUAS_RID_A033_latest.txt`，便于在无 ADB 条件下由文件
管理器回传。报告不包含 raw reply、license ID、账号、飞机序列号或坐标。

两次 clean build byte-identical；132 tests 通过；lint 0 errors/15 warnings；v2 signature、
zipalign、zero permissions、no native/network/socket/shell/external-process path 通过。最终工件为
`204,449` bytes，SHA-256
`8ce8e0c13ecfcf69517a64e809a475b79bbc750124225744b6b35f281d3d7177`（C-181）。

`OBSERVED`：APK 已通过 MTP staged 为 removable-SD
`Download/FindUAS_A033_DIAG_EXPORT.apk`；fresh persistent-object readback 的 size/hash 与登记一致
（C-182）。`UNKNOWN`：没有安装、启动、Binder 结果、inventory、状态改变或 RF 观察。sealed APK
和 signing material 不入库；独立源码与测试发布在 `apps/rc2-rid-admin`。

## 16. A-006 与 A-034：exact 1.21.10 disposable-emulator runtime inputs

A-006 是此前已登记的 exact DJI Fly `1.21.10` APK。本轮只在 disposable ARM64 Android 11
emulator 安装并运行：普通 onboarding 到达主 Activity，authorized emulator shell 又打开了
non-exported license-manager Activity。该观察改变的只是 A-006 的 device-use state；它不产生 RC 2、
飞机、账号、inventory 或 RF 结论。

A-034 是同一 emulator app process 的一个 private read/write mapping，由 authorized root
`/proc/PID/mem` 只读复制取得。独立 boundary scanner 从中恢复 22 个 structurally valid DEX image
用于本地 exact-current Java 分析。A-034、extracted DEX、decompiled source 与 raw process logs 均不
入库；GitHub 只保留 whole-file identity、方法、事实、边界和独立 scanner 源码。direct Frida attach
未产出工件并使 app 退出，单独记录为 C-187。

## 17. A-035 与 A-036：source-only loader negatives

A-035 packages the exact independently written query SO with legacy extraction and displays the
normal installed filesystem path. Its manifest has zero permissions; the built APK contains the
exact `17,344`-byte SO whose SHA-256 is
`15813976fbbdd842f91f90f76628c01200711f3bb6669a7944e6f7706c1ea891`. Emulator installation
confirmed extraction, but the path's first `=` was treated as agent options, so no load occurred
(C-208). This artifact is a negative regression fixture, not an RC 2 candidate.

A-036 stores the same SO uncompressed in an APK with no Android component or permission. AGP emitted
one synthetic 600-byte `R`-class DEX despite `android:hasCode="false"`; the record therefore does
not call it DEX-free. A system-UID emulator process created and streamed an uncommitted session, but
target search of its `apk_tmp_file` directory was denied. Abandon removed the directory (C-210).

Both generated APKs and the generated SO remain excluded. Only original Gradle/manifest/source/test
and build instructions are published.

## 18. 更新与一致性检查

修改本表时必须同时更新 `evidence/artifacts.csv`，并运行：

```sh
ruby scripts/check_evidence_csv.rb
sh scripts/check_sensitive_patterns.sh
```

不得仅更新 Markdown 或仅更新 CSV。若当前任务无权修改 CSV，则新工件保持在候选审计记录中，等待拥有索引更新权限的维护者一次性加入两处。

## A-037：身份控制锁定修复版

C-232 固定的是新版本 `0.8.1-identity-safety-locked` / code 14，不能冒用 A-033 的 hash 或运行状态。170 JVM tests 通过；lint 0 errors / 15 warnings；两次 clean 构建相同；v2 签名和 zipalign 通过；零权限、无 packaged native library。

EID/OPID 写入由 UI/入口/sender 共同锁定，完整 OPID 不进入可复制诊断。保留事务逻辑只以 fake device 验证可恢复基线、ACK/读回不确定、成功变更后仍需恢复、会话漂移时拒绝覆盖旧基线。其他实验写入面仍保留自身边界，所以整个 APK 不是全局只读。新安装包没有 staged、安装或运行，也不证明任何 RID/RF 控制能力。

## A-038：SD 卡报告导出探针

C-233 固定新版本 `0.11.0-report-export` / code 11。69 JVM tests、8 auditor tests 通过，lint 无问题；30/30 v11 mutation 被拒绝；两次 clean build 与登记 APK 完全一致。零权限、v2 签名、zipalign 通过；signer 与旧 v0.10 相同。旧 v0.10 artifact-only profile 与 21 mutations 另行重跑通过。

唯一新增写入为用户要求的 SD 报告：固定 `Download/FindUAS/Probe/`，每次一个新文件，完整 UTF-8/close 后 publish，失败仅清理本次 pending URI。报告写入不能改变检查结果，也不授予 DJI 控制或 attach 能力。审阅边界见 [v0.11 说明](../apps/rid-admission-probe/REPORT_EXPORT_V11.md)。

C-234 记录 `Download/FindUAS_A038_V011.apk` staging/完整读回匹配且无覆盖。C-235 随后收到 10,698-byte 实机报告，确认本版本已安装运行；报告中的 Fly 1.19.4 / code 3113157、ARM32 和 JNI 身份可用，但其 ELF build-ID 检查为 INCOMPLETE。C-244 已把这一历史 APK 移入 SD Archive；当前探针为 A-039。


## A-039：ARM32 实机探针与固定样本导出

C-236 固定版本 `0.12.0-live32-samples` / code 12：94 JVM tests、8 auditor regressions、37/37 拒绝 mutation，lint 无问题；两次 clean build 完全一致，零权限、v2 签名与 zipalign 通过。新增 ELF32 ART build-ID 读取、禁用组件可见性，以及固定 DJI Fly 1.19.4 APK/库的 SD ZIP 导出；报告导出不改变原 COMPLETE 判定。详见 [v12 审计说明](../apps/rid-admission-probe/REPORT_EXPORT_V12.md)。

C-237 记录 APK staging/readback 匹配、安装运行和 10,794-byte COMPLETE 报告收到。C-238 记录随后导出的完整 APK 与三个 SDK 库收到并通过独立内容验证。A-039 留在当前 SD 入口，八个旧 APK 仅移入 Archive（C-244）。

## A-040 与 A-042：ARMv7 canary 和独立查询 agent

A-040 是只检查 ART TI 接口的纯 canary：请求 `0x70010200`、检查接口版本并记录结果，不枚举类或发起查询。10 host tests 与 4 拒绝 mutation 通过；C-243 的 SD staging/完整读回 hash 匹配。没有内部复制、attach 或执行记录，不能把 SD 文件存在写成 loader 成功。

A-042 是另一工件：它保留既有只读 FlySafe 查询机制，新增 `-1` 初始化 sentinel 拒绝和显式 ARMv7 构建选择，原 ARM64 默认不变。C-239 将其 Java descriptor、成功 envelope、JNI 注册和 core bridge 对到 exact 1.19.4；host checks 通过，但 A-042 仅离线构建，未 staged 或在 RC 2 运行。两者独立源码及构建边界见 [实验 README](../experiments/jvmti/jvmti_flysafe_inprocess_query/README.md)，生成 SO 均不入库。

## A-041：实机 DJI Fly 1.19.4 输入样本

A-041 来自原已安装的 DJI Fly，不是把旧 1.21.10 样本重新标记版本。固定样本 ZIP 内的 APK、`libsdk_jni.so`、`libsdk_key_value.so` 和 `libsdk_base.so` 全部通过 manifest、entry、大小和流式 SHA-256 独立验证；APK 的版本、ARMv7 ABI、signer 与报告相符，SDK JNI hash 也匹配（C-238）。

首次本地主机读取因进度检查漏算 libmtp 的 16-byte 请求开销而返回 error；原 payload 已完整落盘，只有独立验证全部通过后才作为分析样本接受。修正 reader 的进度范围并用 13 个本地向量验证，不将原 error 返回改写为传输成功。APK、库、反编译结果和原始报告均留在本地；此表只登记原 APK 的身份，不分发任何厂商材料。

C-235–C-244 的实机步骤及后续状态统一见 [RC 2 实机运行时进展](23_RC2_LIVE_RUNTIME.md)。
