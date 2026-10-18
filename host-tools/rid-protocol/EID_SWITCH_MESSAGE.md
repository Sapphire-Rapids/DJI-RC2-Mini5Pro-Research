# France EID 离线 payload

A-071 当前只输出 payload hex，没有 SDK request 对象头、sender/receiver 参数、DUML framing 或设备 transport。
`0x03/0x77` 属 France EID，不是 FAA/global RID（C-010、C-448、C-469）。

| 动作 | Payload |
| --- | --- |
| GET | `02` |
| SET off | `00` |
| SET on | `01` |

```sh
python3 eid_switch_message.py --get
python3 eid_switch_message.py --value 0
```

非法启用值拒绝。两个命令只打印 hex，不执行设备动作。旧 32 B 对象头与镜像偏移自检不构成 wire 证据，已由 C-469 移除。
C-468 的条件 HostID/helper 结果也没有建立当前 runtime route；Characteristics+0x30 不再解释为 receiver。
原有 product-139 schema、人工 GET 的 canonical ACK 缺失及 readback/restore 边界见
[RID-003/RID-004](../../docs/05_RID_CONTROL_SURFACES.md)。
