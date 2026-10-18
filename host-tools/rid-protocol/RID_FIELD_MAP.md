# RID 相关字段与证据边界

状态：`STATIC`。本表区分业务面和未知项，不是已具备的字段编辑功能清单（C-448/C-449）。
依据：[RID 控制面](../../docs/05_RID_CONTROL_SURFACES.md)与本目录源码。

| 对象 | 命令/结构线索 | 当前证据与缺口 |
| --- | --- | --- |
| France EID | `0x03/0x77`，A-071 | 法国专用；静态 request/ACK schema，不是 global RID |
| 中国 UOM 标签 | `0x11/0xD6`，A-072 | product-139 为 18 字节 pack、最多复制 8 字节；不是旧 C-389 的 0x70 字符串上限 |
| EASA OPID | `0x03/0x78`，A-076 | operator registration 身份面；不等于位置或 Basic/UAS ID |
| Japan DIPS | `0x11/0x4B` | 注册凭据 action；与 EID/UOM/OPID 分开 |
| App location | `0x11/0x43`，A-078 | 发送到设备的数据面；编码器仍有近似，未证明进入 WA150 Broadcast RID 字段 |
| AirSense/ADS-B | `0x11/0x0C`、`0x11/0x37`，A-079 | 接收/配置业务，不是 RID 总开关 |
| 动态最大高度 | GET `0x11/0x50`，A-080 | 查询结构候选；不提供 RID 高度写入 |
| `EU_CE_enable_c0_rid_0` | 静态地区策略映射 | 所测 direct USB 正对照会话未暴露，不作为可用开关 |
| `CccBroadcastSignalQuality` | 静态注册/参数线索 | 位语义、live metadata 与 RF 对应仍未闭合 |
| `ComplianceSerialNumber` | 从 `SerialNumber` 派生的 listener | 没有恢复出已准入 SET；不能推断所有上下文绝不可写 |
| `RidWorkingStatusPush` | push/cache observer | 没有主动 GET；不能单独证实 SET applied 或 RF 状态 |

六个 CLI 均只输出离线 hex，不建立实际路由。内部 request 布局不能直接充当最终 wire framing。
A-078 保留 prefix/字段/密文缓冲近似；本机自检的长度和确定性断言不等于官方逐字节匹配。
当前没有设备可验证 owner、baseline/readback/restore、持久性或独立 RF 效果。

历史 claim 地址与调用点继续保留；C-448/C-449 和 docs/05 的较早实机正对照优先于后来“完整控制”的汇总措辞。
