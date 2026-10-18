# RID 相关协议研究汇总

状态：`STATIC`。当前无设备，六个工具只生成离线 hex；没有设备发送实现。
C-448/C-449 撤回旧版“完整控制 Remote ID”“路径全无条件成立”和“代码侧穷尽”的结论。

| 表面 | 静态名称/命令 | 工具与当前边界 |
| --- | --- | --- |
| France EID | `EIDSwitch` / `0x03/0x77` | A-071；法国专用，不是 global RID |
| 中国 UOM 标签 | `OIDIdentifier` / `0x11/0xD6` | A-072；18 字节 pack，不等于 Basic/UAS ID |
| EASA registration | `OperatorRegistrationNumber` / `0x03/0x78` | A-076；身份面，不是 RF 开关 |
| App 位置 | `UploadMobileDevicePosition` / `0x11/0x43` | A-078 v3 为 84 B 离线 payload；选定 Java/cache 与条件 default 高度语义见 C-473；实际 provider/有效高度/fix age 和 transport/RF 未验证 |
| AirSense/ADS-B | `ADSBSwitch` / `0x11/0x37`，receive enable `0x11/0x0C` | A-079；不能作 RID 总开关 |
| 动态最大高度 | GET `0x11/0x50` | A-080；静态结构候选，不是 RID 高度写入 |

C-459/A-087 只验证 keychain；C-464/C-465 后续恢复 22 B 输入/84 B payload，并通过原始片段/helper 与独立 fixture 对照。
这没有执行完整 handler/SendSetPack/transport 或 RF，不能视作已验证位置编辑功能。

`EU_CE_enable_c0_rid_0` 的静态映射不能覆盖所测 direct USB 的正对照负结果；不能推荐为 EID 的可用替代。
`ComplianceSerialNumber`/`SerialNumber` 的命名访问器未恢复出可用写路径，不能由派生关系或名称缺失推断其他路径绝不存在。

App→local/logic→djilink→bulk/USB 是静态组件线索。注册成功、内部请求结构、候选 hex 与自检均不证明端到端路由、
设备 capability、baseline、readback、恢复或 RF 效果。源码自检验证的是合成结构和确定性，未与官方 wire 输出逐字节对照。

`RidWorkingStatusPush` 是 push-only 观察面，没有主动 GET；尚未证明其 flags 对应 EID/ADS-B SET 的 applied 状态。
历史外部 Binder listener 在真实 RID RF 存在时曾零回调，不能把无回调读作关闭。保留缓存也需要接收时间语义和独立 RF 对照。

依据：[RID 控制面](../../docs/05_RID_CONTROL_SURFACES.md) RID-002B、RID-003、RID-005B、RID-005C、RID-009、RID-011C；
[字段地图](RID_FIELD_MAP.md)；[离线验证说明](VERIFY_RUNBOOK.md)；[STUE 检查点](../firmware-acquisition/AIRCRAFT_STUE_CHECKPOINT.md)。

C-468/C-469 后，SDK request 内存头不再由任何 payload CLI 输出；旧 sender/receiver 参数均删除。
Characteristics+0x30=receiver 已撤回，free KeyHandlers+0x10 与 BaseAbstraction EID+0x128 分开。实际 runtime route 未验证。
五个修正 CLI 通过8项schema/9个有效调用并拒绝5个旧路由参数调用；OPID action按C-124、UOM GETtail保持本地选择，
这些结果不构成 full-handler/transport/RF 验证。

C-471/C-472 的四份视图是限定结构分析输入，不恢复原始 DEX 身份。C-473 的 Android/default 分支直接复制
last-known altitude，米/WGS84 椭球契约以高度有效为条件，所查方法没有 hasAltitude 检查。它可混用 newer network
坐标/时间和 older GPS 高度；两层按需缓存与消息 epoch 秒不证明 fresh fix 或 1 Hz producer。AMap 的基准/runtime
选择、独立 altitude provider 和真实设备/RF 保持分开。A-078 的显式 22 B 接口不变。
