# eid_switch（RID/EID 开关）报文规格 — 静态重建

状态：`STATIC`。无设备，未实发。来源是 DJI Fly `libsdk_jni.so` 的反编译，不涉及刷写。

## 1. 依据

`EIDSwitchSet`（0x04e12f80）与 `UAV77FlightControllerAbstraction::SetEIDSwitch`（0x02d9afa0）实例化

```
uav_cmd_base_req<(uchar)1, (uchar)3, (uchar)119, uav_fc_handle_eid_switch, uav_fc_eid_switch_status>
```

`uav_cmd_base_req` 构造函数（见 topic 11.33）给出头部布局；包装层调 `SendSetPack<uav::core::eid_switch_pack>`，
最终经 `BaseAbstraction::SendPack`（虚槽0x128）→ `UavCoreCancelation::SendData` 发送。

## 2. 报文布局（0x20 头 + 1 字节载荷 = 33 字节）

| 偏移 | 值 | 含义 |
| --- | --- | --- |
| 0x00 | 01 | 模板参数1 |
| 0x01 | 03 | 子命令 sub |
| 0x02 | 77 | cmd 119 |
| 0x03 | 02 | 构造常量 |
| 0x04..05 | 00 00 | — |
| 0x06 | sender | `GlobalPacketStatus::GetGlobalSenderIndex()`，进程内自动 |
| 0x07 | 00 | — |
| 0x08 | 03 | — |
| 0x0c..0d | 00 00 49 57 | ASCII `'I','W'` 魔数 |
| 0x10..11 | 00 00 | — |
| 0x14..17 | f4 01 00 00 | 超时 500 |
| 0x18..19 | 00 00 | — |
| 0x20 | 载荷 | 1 字节启用值；**0 = 关**，1 = 开 |

receiver index 由调用方给（`Characteristics+0x30`），不在此字节流内。

## 3. 取值

- 关 RID：`--value 0`
- 开 RID：`--value 1`

## 4. 生成

```
python3 eid_switch_message.py --value 0
```

输出 `receiver` 提示行 + hex 字节流。

## 5. 边界与未闭合

- `sender` 在真实进程里自动填；此处默认0，真实发送前需替换。
- receiver 具体取值未定（属环境/会话项）。
- `0x03` 与 `0x02` 常量语义未证；按其出现位置照抄。
- 兄弟参数 `OIDIdentifier` 用另一对 opcode（cmd214/sub17，C-388），不在本规格内。
