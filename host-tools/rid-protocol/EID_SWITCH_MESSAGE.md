# France EID 离线请求结构

状态：`STATIC`，当前无设备、未发送。A-071 只生成候选 hex，未实现最终 wire framing 或 USB/socket transport。
`0x03/0x77` 属 France EID；不能称为 FAA/global RID 开关（C-448/C-449）。

历史静态分析记录了 `EIDSwitchGet/Set`、`SendGetPack/SendSetPack` 和 `SendPack/SendData` 的调用线索。
源码按内部 request 构造写入 0x20 字节头部与 1 字节候选载荷。内部对象与最终线包不能直接等同。

| 生成器偏移 | 当前写入 | 证据边界 |
| --- | --- | --- |
| 0x00..0x03 | `01 03 77 02` | 内部构造常量，非完整 wire header 验证 |
| 0x05 | `02` | 内部构造常量 |
| 0x06 | sender | CLI 值，未证明当前会话合法 |
| 0x08 | `03` | 既有 schema 中此处是 retry，不是 receiver |
| 0x0e..0x0f | `49 57` | 内部结构魔数 |
| 0x14..0x17 | 500 | 超时字段 |
| 0x20 | 0 或 1 | France EID 候选启用值，不证明当前机型或 RF 效果 |

product-139 静态 receiver type/index 为 18/4（`0x92`）；精确 route/retry/ACK 以
[RID-003](../../docs/05_RID_CONTROL_SURFACES.md) 为准。
源码打印的 receiver 提示不等于发送或路由验证。

```sh
python3 eid_switch_message.py --value 0
```

该命令只打印离线候选，不关闭设备广播。历史人工 France EID GET 未得到 canonical ACK（RID-004），没有可据此执行的
baseline/SET/restore 链。有关“取到 sender/receiver 即可下发”的旧成熟度结论已撤回。
