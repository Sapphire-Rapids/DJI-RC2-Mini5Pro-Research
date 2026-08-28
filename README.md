# DJI RC 2 / Mini 5 Pro research archive

这是一个独立、非官方的 DJI RC 2 / Mini 5 Pro 研究档案。记录截至 2026-08-28 的实机观察、
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

- 没有发现一个跨 FAA/US、法国 EID、EASA OPID、欧盟 C0、日本 DIPS、中国 OID 与普通
  Broadcast Remote ID 的当前普通 Boolean 总开关。
- Product-139 的 France EID 静态路径已闭合到 `0x03/0x77`，但它是法国专用 EID，不是
  global RID。两个固定人工 USB GET 路由均未获得 canonical ACK；DJI Fly 私有 owner 路径未实测。
- FlySafe type-6 `RID_UNLOCK` 是账号/FC 绑定的签名许可类别，具备 enable-state 语义；当前
  Mini 5 Pro 是否有资格、是否存在真实许可、FC 是否接受及 RF 是否变化均为 `UNKNOWN`。
- 起桨前的受限观察窗没有收到严格 `0x11/0x1C` RID working-status；已知现场观察表明该机型
  起桨后才开始实际 RID 播报。缺少同步 onboard status + 独立接收器 RF 记录。
- 配置读取显示高度 500 m、距离 5000 m、距离限制关闭；这不能解释或否定未登录状态可能存在的
  30/50 m effective runtime restriction。
- FC area 和 Sky country 已完成 `CN -> US -> CN` 的一次有界读回/恢复闭环；Ground country 的
  单次 US 请求无匹配 ACK，随后 GET 仍为 CN。没有由此获得 Remote ID、频道或 RF 功率证据。
- RC 2 标准 ADB 在 RSA 认证前停止：主机 `CNXN` 已发出，设备不返回 ADB 包。相邻 unstripped
  `adbd` 含 production `CNXN` drop gate，可解释现象但不等同于精确 live v07 二进制证明。
- 当前 Android admission probe v0.10 通过离线工件审计，但尚未复制、安装或运行于 RC 2。
- Route-only V2.2 已因两个 P1 与一个 P2 缺陷撤销。V2.3 修复三项缺陷，但仍固定零 exception
  gate、zero-send、未上机，且尚无新的独立 post-fix audit 结论。
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
- [evidence/claims.csv](evidence/claims.csv)：机器可读 claim 索引。
- [evidence/artifacts.csv](evidence/artifacts.csv)：机器可读工件索引。

## 仓库内容边界

本仓库只发布独立撰写的 Markdown/CSV、公开链接、版本号、命令标识、聚合结果和文件哈希。
不发布 DJI APK、固件、提取分区、共享库、反编译源码、原始私人抓包、账号材料、ADB key、
设备序列号、UAS ID、电话或坐标。

## License

[MIT](LICENSE) © 2026 Sapphire-Rapids
