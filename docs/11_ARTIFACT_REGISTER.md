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

## 7. 输入样本与分发

A-004 至 A-008、A-013 和 A-015 是 input-sample 或 rejected third-party input。它们不属于本仓库实现，不能提交二进制或复制正文。允许保留的内容只有：

- 公开版本和产品族；
- 在规范 CSV 明确登记的 public hash；
- independently written 高层结论；
- 公开来源或固定 revision；
- “相邻”“受保护”“加密”“未安装”“不分发”等边界。

厂商输入的补充身份只在 [固件与信任边界](07_FIRMWARE_TRUST_BOUNDARY.md) 中作为样本 provenance 描述，不增加本规范 artifact CSV 的行，也不代表本仓库提供样本。

## 8. 更新与一致性检查

修改本表时必须同时更新 `evidence/artifacts.csv`，并运行：

```sh
ruby scripts/check_evidence_csv.rb
sh scripts/check_sensitive_patterns.sh
```

不得仅更新 Markdown 或仅更新 CSV。若当前任务无权修改 CSV，则新工件保持在候选审计记录中，等待拥有索引更新权限的维护者一次性加入两处。
