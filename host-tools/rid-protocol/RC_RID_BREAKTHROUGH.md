# 遥控器侧协议研究范围

状态：`STATIC`。本轮无设备、未发送、未取得新的 ACK/readback/RF 证据。
旧标题中的“突破口/总收口”不代表已能关闭 RID；C-397 的“只剩实机取值”结论已撤回（C-448/C-449）。

已记录的静态线索包括 EIDSwitchGet/Set、key 注册、请求结构、SendPack/SendData 名称及 rc331 的 local/logic/bulk
配置（C-373--C-396）。它们不能合成一条已经验证可用的 App→飞机控制路径。

| 对象 | 已有边界 |
| --- | --- |
| `EIDSwitch` / `0x03/0x77` | France EID 专用；不是 FAA/global RID。现有生成器没有传输实现 |
| `ADSBSwitch` / `0x11/0x37` | AirSense/ADS-B 业务；不是 RID 广播总开关 |
| `EU_CE_enable_c0_rid_0` | 静态映射存在；所测 direct USB 会话有成功正对照而目标未暴露 |
| local/logic/socket | 固件配置与名称线索；实际 socket、owner、路由和请求生命周期未由本目录验证 |
| `RidWorkingStatusPush` | push-only/cache 观察面；没有主动 GET 或已证明的 SET/RF 对应关系 |

历史静态产物 A-071/A-072 是离线 hex 生成器；A-073 是验证说明。不能通过补一个 sender/receiver 就认定可发送、
可逆或能关闭广播。恢复值必须来自真实 baseline，不能预设为 1。

后续仍需要分别证明业务语义、实际 owner/路由、baseline、严格 readback、恢复、持久性与独立 RF 对应关系。
当前工作保持离线；固件研究状态见[STUE 检查点](../firmware-acquisition/AIRCRAFT_STUE_CHECKPOINT.md)。
更高优先级边界见[RID 控制面](../../docs/05_RID_CONTROL_SURFACES.md) RID-002B、RID-003、RID-009、RID-011C。
