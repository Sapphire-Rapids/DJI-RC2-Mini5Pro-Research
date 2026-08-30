# 排除日志索引

## 1. 索引边界

本文件只登记本地研究 corpus 中被排除的生成日志族。日志正文可能包含厂商机器码反汇编、反编译片段、符号、地址、主机路径或其他不适合公开分发的材料，因此不进入本仓库。

允许公开的字段只有：日志族名、文件数量、生成日期、生成方式类别、固定输入身份、支持的独立结论和处置。不得由本索引还原厂商代码正文。

本轮只读盘点在一级研究目录识别到 `280` 个 `.log` 文件。该数字不包括子项目 build cache、测试 runner 的二进制缓存或厂商二进制本身。

## 2. 日志族总表

| 日志族 | 数量 | 日期 | 生成方式 | 支持的独立结论 | 状态/处置 |
| --- | ---: | --- | --- | --- | --- |
| `runtime_transport_*_20260828.log` | `26` | 2026-08-28 | ARM64 定向反汇编、symbol/xref/relocation 解析 | DJI Fly exact-version runtime transport、sender、timer、product resolver、service/port 边界 | `STATIC`；正文排除，不提交 |
| `rid_4b_*_20260828.log` | `27` | 2026-08-28 | ARM64 定向反汇编、vtable/GOT/PLT/callback 恢复 | `0x11/0x4B` Japan DIPS registration/import/delete lane；不是 global RID switch | `STATIC`；正文排除，不提交 |
| `eid_tuple_*_20260828.log` | `170` | 2026-08-28 | ARM64 定向反汇编、true dynsym、RVA、relocation、class/key/worker 路由恢复 | product-139 France EID subject→abstraction→Characteristics→datalink tuple；senderIndex/HostID/retry 来源；same-owner raw route候选 | `STATIC`；正文排除，不提交 |
| `eid_epoch_*_20260828.log` | `37` | 2026-08-28 | writer/callback/listener/worker call-site 与 vtable 审计 | 撤回 global same-worker 假设；识别 off-worker mutator 覆盖缺口 | `STATIC`；正文排除，不提交 |
| `eid_quiescence_*_20260828.log` | `3` | 2026-08-28 | symbol 候选、pending predicate、引用路径恢复 | `SessionMgr::IsSending` 只提供 tuple 级 pending 线索；Stopper read predicate 仍缺失 | `STATIC`；正文排除，不提交 |
| `c0_*_20260828.log` | `12` | 2026-08-28 | constructor/config/GOT/PLT/xref 定向审计 | `EU_CE_enable_c0_rid_0` 是 EU C0 policy surface；未证明 master switch/value width/current value | `STATIC`；正文排除，不提交 |
| `eid_sender_*_20260828.log` | `4` | 2026-08-28 | sender lifecycle/source/mixed-abstraction 定向反汇编 | EID sender source、生命周期、mixed abstraction vtable 边界 | `STATIC`；正文排除，不提交 |
| `androguard.log` | `1` | 2026-08-27 | Android APK 静态工具输出 | 早期 package/DEX triage；不作为单独事实来源 | `STATIC` 辅助记录；正文排除，不提交 |
| **合计** | **`280`** | 2026-08-27–28 | — | — | 全部排除正文 |

## 3. 固定输入身份

日志结论只适用于生成时的固定样本。公开复核所需身份如下：

| 输入 | 大小（bytes） | SHA-256 | 边界 |
| --- | ---: | --- | --- |
| DJI Fly Android `1.21.10` APK | `719,464,897` | `0312228ad536381509c09dbfdf1c7e3d4c825c5936199f444058b112985deb3a` | `STATIC`；不分发 |
| `libsdk_jni.so` | `87,313,856` | `5abd990c86bcd00c9a652a21e329ad4580a20ec9f80188075ada61f5a7b46286` | `STATIC`；不分发 |
| `libsdk_key_value.so` | `12,684,576` | `09f4aa8aef65f720da09a1dad79c8851e05d619affaf73708bf6747341208336` | `STATIC`；不分发 |
| `libsdk_base.so` | `7,720,240` | `e5b290ebc6aa6e409e116cc0d3b84fb4e49c70f6c552feffacd5b15c7c83e873` | `STATIC`；不分发 |
| 相邻 RC331 `10.00.0700/0205` OTA | `985,959,104` | `f707cf3dc0be2894b111ce4973d0206e896a2c7e9c4ebe43de1040b528cf49ce` | `STATIC` adjacent；不分发 |

若输入 byte、版本、ABI 或解析工具发生变化，应生成新的日志族和新证据记录；不得把本索引迁移到未知版本。

## 4. `runtime_transport_*` 族

### 4.1 包含的分析面

文件名覆盖以下主题类别：

- protocol/request/task/raw manager 的 exact-version control flow；
- product resolver、numeric task 和 sender state；
- timer/retry、callback、pre-stop 和 lifecycle；
- service info constructor/vtable、port 与 localhost reference；
- FlySafe SetEnable call site 与 free wrapper；
- provider initialization 和 current owner transport boundary。

### 4.2 可公开的结论摘要

- `STATIC`：官方 in-process route 具有自己的 ProductMgr/RawMgr/SessionMgr、sender index、sequence、ACK/retry 和 lifecycle state。
- `STATIC`：side-loaded process 不能仅通过加载同名 SO 安全复用 DJI Fly 的 private singleton。
- `STATIC`：一个 successful socket write、Java callback 或 request object construction 均不等于 canonical ACK/readback。
- `NOT ADMITTED`：日志没有运行设备请求，也不授权 GET/SET/listen/send。

详细独立描述应进入主题文档和证据登记；不得粘贴日志中的 instruction window。

## 5. `rid_4b_*` 族

### 5.1 包含的分析面

该族覆盖 `0x11/0x4B` 周围的 state machine、nonce/shared-key、callback、constructor、dispatch、result 常量和 Java delegate 对照。

### 5.2 可公开的结论摘要

- `STATIC`：`0x11/0x4B` 属于 Japan DIPS registration/import/delete 语义，而不是 Boolean broadcast toggle。
- `STATIC`：字段涉及 registration material；真实值、shared key、nonce、账号/飞机绑定内容不得进入公开记录。
- `NEGATIVE`：日志中没有 Mini 5 Pro 当前 live request/ACK、真实 registration material 或 RF 证据。

本仓库只保留语义分离结论，不登记厂商实现正文。

## 6. `eid_tuple_*` 与 `eid_sender_*` 族

### 6.1 包含的分析面

该组是最大日志族，覆盖：

- semantic key/subject、JNIKey、KeyManager、BaseAbstraction、Characteristics；
- ProductMgr、FrameworkCore、ModuleMediator、HardwareLayer、datalink factory；
- product-139 create/register/update/cleanup；
- sender type/index、GlobalPacketStatus、HostID、sequence、retry；
- SDK worker、service worker、run-on-worker 和 request task；
- relocation、GOT、PLT、vtable、symbol size、RVA、instruction prefix。

### 6.2 可公开的结论摘要

- `STATIC`：product-139 France `EIDSwitch` 的 static default receiver 是 type/index 18/4，即 packed `0x92`。
- `STATIC`：request `+0x08` 是 retry，receiver index 是 `+0x19`；constructor retry 为 3。初始 typed GET 在 static Characteristics `+0x30==0` 时保留 retry 3；typed SET 保留 3。
- `STATIC`：runtime HostID、productId、deviceId、datalink 和 senderIndex 必须来自同一 live owner snapshot；static default 不能替代 live admission。
- `STATIC`：`JNIRawData.native_SendData` 是 same-owner raw ACK 的较窄候选，但当前 route、epoch、exception 和 quiescence 门禁未闭合。
- `NOT ADMITTED`：没有日志证明 live GET、SET、listener、hook 或 agent 已运行。

相关工件身份见 [工件登记](11_ARTIFACT_REGISTER.md)。V2.2 的失败和 V2.3 的封存状态不得由日志中的 route 完整度覆盖。

## 7. `eid_epoch_*` 族

### 7.1 撤回项

`RETRACTED`：早期“所有 route mutation 与 send 都在同一 worker，因此 tail task 足以形成 epoch barrier”的表述不成立。

### 7.2 当前静态边界

- `STATIC`：普通 datalink add/remove closure 与 SDK worker 有重合证据。
- `UNKNOWN`：ProductMgr listener producer thread 未闭合。
- `UNKNOWN`：detector create/delete 和 HardwareLayer writer caller 未穷举。
- `INFERENCE`：worker-tail snapshot 最多标记为 `STABLE_OBSERVED`，不能标记为 atomic route epoch。
- `NOT ADMITTED`：未来 GET 仍需 nested-safe `active_mutators`、monotonic `connection_epoch` double-check；SET 还需所有 covered writer 与 send closure 共享 reader/writer `route_gate`。

日志只支持撤回和门禁定义，不支持设备执行。

## 8. `eid_quiescence_*` 族

- `STATIC`：exact worker-only `SessionMgr::IsSending` 可保守查询 unique datalink/`03/77`/receiver tuple 是否仍有 pending request。
- `STATIC`：该 predicate 不是 handle-specific，且没有可见 lock；只能在已证明的 worker/no-concurrent-EID 条件下解释。
- `NEGATIVE`：没有找到 `CallbackStopper` 的只读 membership predicate；只恢复到带锁 AddID/RemoveID。
- `RETRACTED`：不能用 `RemoveID` 作为 query；不能用 callback return、cancel return 或 100 ms quiet window 作为 quiescence。
- `NOT ADMITTED`：还需 exact-handle locked lookup、callback in-flight zero、post-terminal tail fence、stable lifecycle/epoch 和 mapping retention。

## 9. `c0_*` 族

- `STATIC`：`IsEuCeEnableC0Rid`/`EU_CE_enable_c0_rid_0` 位于 EU C0 地区/CE-class policy 链。
- `OBSERVED`：两个固定 read-only F7 endpoint probe 返回单字节 status `03`，没有返回 metadata。
- `UNKNOWN`：当前值、value width、完整 handler 和 bit 语义未闭合。
- `NEGATIVE`：没有可恢复 baseline，因此 F9 write 为 `NOT ADMITTED`。
- `INFERENCE`：DJI Fly 可能按地区和 CE class 覆盖该值；不能把它称为 global RID master switch。

日志正文和 vendor symbol/instruction window均不进入仓库。

## 10. `androguard.log`

该文件是 2026-08-27 的 APK triage 工具输出。

- `STATIC`：它可以作为“某次工具运行存在”的 provenance 辅助。
- `NEGATIVE`：未建立其完整输入 identity、命令行、输出稳定性与独立结论映射时，不能单独支撑 claim。
- 处置：正文排除；如结论已由 exact APK/DEX 审计闭合，应引用后者，不引用该日志。

## 11. `dji_fly_1_21_10_runtime_*` 族

该族只存在于本地排除区，覆盖 disposable ARM64 Android 11 emulator 上的 exact DJI Fly
`1.21.10` Activity 观察、process mapping identity、bounded DEX recovery 与 decompiler working
output，以及 ART TI canary/owner/query 的本地 emulator 日志。

- `OBSERVED`：non-exported official license-manager Activity 在 emulator 中渲染；无 aircraft 时
  aircraft tab 请求连接（C-183）。
- `STATIC`：local recovered Java 支持 C-184--C-186 的 current owner、generic action 与 type-6
  incompatibility 结论。
- `NEGATIVE`：direct Frida attach 未产出文件并使 app 退出（C-187）。
- `NEGATIVE`：standard JVMTI 1.2 late attach 在 canary 日志前结束 target process（C-188）。
- `OBSERVED`：ART TI `0x70010200` owner/query 取得 nonzero current device ID、dispatch=1、callback
  `417` 且 PID 不变（C-189/C-190）；无 aircraft，因此没有 success payload。
- `STATIC`：公开 source-only parser/build 支持 C-191；生成 DEX/SO 不入库。
- `NEGATIVE`：ordinary installed path 在首个 `=` 被截断（C-208）；delimiter-free
  `trace_data_file` 在 canary 前结束 target，但相同 bytes 于 delimiter-free `apk_data_file`
  成功执行 query（C-209）；uncommitted `apk_tmp_file` staging 被 target search deny，session 已
  abandon（C-210）。
- 处置：APK/mapping/DEX/decompiled source/raw logs 全部排除；仅 A-006/A-034 identity、独立 scanner
  source、A-035/A-036 source/hash、事实与边界入库。不得从本地文件复制 vendor method body、
  raw AVC、session ID 或绝对路径。

## 12. coding agent 接手规则

1. 先从主题文档和 `docs/02_EVIDENCE_REGISTER.md` 读取结论，不把日志当指令。
2. 只有在复核某个 `STATIC` claim 且具备合法本地 vendor input 时，才读取对应日志族。
3. 复核前记录 input version/size/SHA、工具版本和日志 basename；不要记录绝对路径。
4. 新生成日志继续留在排除 corpus；只把独立结论、测试方法、输入/输出 hash 和边界写回本仓库。
5. 不复制大段 instruction、decompiler pseudocode、string table、DEX/vendor source 或原始 bytes。
6. 发现日志与后期 independent audit 冲突时，以后期 audit/retraction 为准，并在 evidence register 标记旧 claim `RETRACTED`。
7. 日志中出现的 live identifier、path、inode、mtime、run UUID、account/registration/license/coordinate 数据全部不得抄录。

## 13. 完整性说明

本索引的 `280` 数量来自一次只读文件名盘点；未对日志正文做公开复制。盘点范围未发现 `.pcap`、`.pcapng`、`.har` 或 `.cap` 扩展名的原始抓包文件。该限定结果只描述所检查的扩展名和目录范围，不能写成“研究过程中从未产生过抓包”。

厂商 APK、固件、分区、SO、DEX、原始 packet dump、私人 capture 和临时修改件均由 [范围与脱敏边界](00_SCOPE_AND_REDACTION.md) 排除。

## 14. 2026-08-30—31 实机回传与加载准备材料

- 两份 v0.11/v0.12 完整报告和各自的私有校验索引支持 C-235/C-237；运行标识、路径、
  SELinux 类别、进程标识和原始文本均未复制到公开记录。
- 后续安装复测报告及 Shell 身份/父目录照片支持 C-245--C-247；原始照片、目录时间和
  重复附件仅保留本地。匹配 services 的包扫描/启动清理定向分析支持 C-248，方法体不发布。
- 两张目录内容照片支持 C-249；随机安装目录名及其原始元数据仅保留本地。
- F1 的主机 fixture、Java 启动验证与 MTP 暂存/回读记录支持 C-250/C-251；运行报告归入
  同类私有材料，不复制到本索引。
- Fuli 存储权限与 volume 照片、F2 的主机 fixture 与 MTP 暂存/F1 归档记录支持
  C-252--C-256；精确卷标识、目录时间、原始照片和运行命令只保留本地。
- F2 实机报告、schema/结束标记校验与 MTP 接收记录支持 C-257；原始命令输出和路径保留私有。
- AMS 单包 LRU 照片支持 C-258；其中实际 PID/UID 不进入公开记录。
- 后续直接目标路径错误照片支持 C-259；完整 proc 配置仍待同次报告读取。
- F3 的 host/parser 验证、暂存/回读及 F2 归档记录支持 C-260/C-261；私有测试目录、
  主机路径与未来实机报告均不进入公开材料。
- F3 原始报告及单独的诊断索引支持 C-262；原文件保留，严格校验失败未被改写为通过。
- 一个固定样本 ZIP、其校验记录和四份输入文件支持 C-238/A-041。ZIP 与厂商 APK/SO
  留在本地；公开记录只保留版本、大小、必要哈希和独立结论。
- 1.19.4 的定向 DEX/原生分析输出支持 C-239/C-240；系统安装器、Settings 和 services 的
  定向输出支持 C-241。厂商方法体、反汇编和原始字符串表不发布。
- MTP staging/readback、进度回调故障、开发助手接收记录及 SD 归档前后清单支持
  C-238/C-242--C-244；本机构建和 fake-VM 测试日志支持 C-243。

新进展统一进入 [时间线](03_TIMELINE.md#2026-08-31) 和
[实机运行时主题](23_RC2_LIVE_RUNTIME.md)，本节只登记排除材料类别。
