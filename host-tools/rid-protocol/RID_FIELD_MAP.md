# RID 相关字段与证据边界

状态：`STATIC`。本表区分业务面和未知项，不是已具备的字段编辑功能清单（C-448/C-449）。
依据：[RID 控制面](../../docs/05_RID_CONTROL_SURFACES.md)与本目录源码。

| 对象 | 命令/结构线索 | 当前证据与缺口 |
| --- | --- | --- |
| France EID | `0x03/0x77`，A-071 | 法国专用；静态 request/ACK schema，不是 global RID |
| 中国 UOM 标签 | `0x11/0xD6`，A-072 | product-139 为 18 字节 pack、最多复制 8 字节；不是旧 C-389 的 0x70 字符串上限 |
| EASA OPID | `0x03/0x78`，A-076 | operator registration 身份面；不等于位置或 Basic/UAS ID |
| Japan DIPS | `0x11/0x4B` | 注册凭据 action；与 EID/UOM/OPID 分开 |
| App location | `0x11/0x43`，A-078 v3 | 84 B 离线 payload；C-473 接通选定 Java/cache 链与条件 default 高度单位；实际 provider/有效高度/fix age、完整 handler/transport/RF 未验证 |
| AirSense/ADS-B | `0x11/0x0C`、`0x11/0x37`，A-079 | 接收/配置业务，不是 RID 总开关 |
| 动态最大高度 | GET `0x11/0x50`，A-080 | 查询结构候选；不提供 RID 高度写入 |
| `EU_CE_enable_c0_rid_0` | 静态地区策略映射 | 所测 direct USB 正对照会话未暴露，不作为可用开关 |
| `CccBroadcastSignalQuality` | 静态注册/参数线索 | 位语义、live metadata 与 RF 对应仍未闭合 |
| `ComplianceSerialNumber` | 从 `SerialNumber` 派生的 listener | 没有恢复出已准入 SET；不能推断所有上下文绝不可写 |
| `RidWorkingStatusPush` | push/cache observer | 没有主动 GET；不能单独证实 SET applied 或 RF 状态 |

六个 CLI 均只输出离线 hex，不建立实际路由。内部 request 布局不能直接充当最终 wire framing。
A-078 v2 的错误由 C-459/C-464 撤回；v3 接受显式 22 B 字段、32 B decoded key、16 B IV，输出 84 B payload。
C-465 的原始 JNI 片段和 helper 对照支持此模型，未执行完整 handler/SendSetPack/transport；A-087 仍只验证 keychain。
当前没有设备可验证 owner、baseline/readback/restore、持久性或独立 RF 效果。

历史 claim 地址与调用点继续保留；C-448/C-449 和 docs/05 的较早实机正对照优先于后来“完整控制”的汇总措辞。

C-468 更正 receiver 来源：Characteristics+0x30 是 callback capture；实际覆盖取决于 single/multiple HostID 条件。
free EID/position 用 virtual+0x10，BaseAbstraction EID 重载才用+0x128。六个受控 prefix/helper cases 未执行完整 route。
C-469 将五个旧 CLI 改为纯 payload；OPID GET02/DELETE01/SET0010+exact16，UOM的零GETtail仍是本地选择。

C-471/C-472 的四份视图是限定结构分析输入，不恢复原始 DEX 身份。C-473 的 Android/default 分支直接复制
last-known altitude，米/WGS84 椭球契约以高度有效为条件，所查方法没有 hasAltitude 检查。它可混用 newer network
坐标/时间和 older GPS 高度；两层按需缓存与消息 epoch 秒不证明 fresh fix 或 1 Hz producer。AMap 的基准/runtime
选择、独立 altitude provider 和真实设备/RF 保持分开。A-078 的显式 22 B 接口不变。
