# rid-protocol — 离线协议结构研究

状态：`STATIC`，当前无设备。本目录六个 CLI 只生成 hex，没有 USB、socket 或其他设备传输实现。
C-448/C-449 撤回此前“RID 关闭路径”“全条件成立”和“完整控制”的表述。静态结构与自检不构成实机能力。

| 文件 | 当前用途 |
| --- | --- |
| `eid_switch_message.py` / `EID_SWITCH_MESSAGE.md` | France EID 请求结构候选，A-071；不是 global RID 开关 |
| `oid_identifier_message.py` / `OID_IDENTIFIER_MESSAGE.md` | 中国 UOM 标签的离线结构，A-072；不等于 Basic/UAS ID |
| `opid_message.py` | EASA operator registration 候选结构，A-076 |
| `position_message.py` | app-location 编码近似，A-078；prefix、字段与最终字节流未验证 |
| `adsb_switch_message.py` | AirSense/ADS-B 配置候选，A-079；不是 RID 总开关 |
| `height_message.py` | 动态最大高度 GET 结构候选，A-080；不是 RID 高度编辑器 |
| `test_*_message.py` | 合成结构/确定性自检，不能替代官方输出或设备对照 |
| `VERIFY_RUNBOOK.md` | 离线验证范围与尚缺证据，A-073 |
| `RC_RID_BREAKTHROUGH.md` / `RID_CONTROL_CONSOLIDATION.md` | 更正后的静态研究范围，A-074/A-081 |
| `RID_FIELD_MAP.md` | 业务面和验证缺口，A-077 |

离线示例：

```sh
python3 eid_switch_message.py --value 0
python3 test_eid_switch_message.py
python3 test_oid_identifier_message.py
```

这些命令只打印候选字节或测试结果。内部 request 对象布局不等于最终线包，sender/receiver、传输 framing 与当前 owner
尚未由这些生成器验证。`EU_CE_enable_c0_rid_0` 在既有 direct USB 正对照会话中未暴露，不作为可用替代开关。
`RidWorkingStatusPush` 没有主动 GET，也不能单独证明 EID/ADS-B SET 已应用或 RID RF 改变。

业务语义与历史实机边界以[RID 控制面](../../docs/05_RID_CONTROL_SURFACES.md)的 RID-002B、RID-003、RID-005C、
RID-009 和 RID-011C 为准。位置源码仍含近似，不能当作可用坐标编辑器。
