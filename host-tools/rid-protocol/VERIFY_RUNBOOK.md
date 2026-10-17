# RID(EID) 关闭 — 无刷写验证上手手册

状态：`STATIC`，尚未实机执行。全程只发协议，**不刷写固件**。

## 0. 结论对象

- 目标参数：SDK key 名 `EIDSwitch`（RID/EID 启用开关）
- 关闭动作：对该 key 执行 **Set，值 0**
- 报文规格：`EID_SWITCH_MESSAGE.md` + `eid_switch_message.py`（A-071）
- 依据链：EIDSwitchSet → SendSetPack → BaseAbstraction::SendPack(slot0x128) → UavCoreCancelation::SendData

## 1. 前置（必须满足）

1. 遥控器已开机，且与飞机/设备**已连接**（DJI Fly 能正常出图/可控即算）。
2. App 侧的 key map 已插入 —— 即 Fly 已 init 过该 characteristics 表（打开设置页/参数页即可触发，
   对应 `BaseAbs::InsertCharacteristics("EIDSwitch")`，C-390）。
3. sender / receiver 来自运行进程：
   - `sender` = `GlobalPacketStatus::GetGlobalSenderIndex()`
   - `receiver` = `Characteristics+0x30`
   两者都是**运行期值**，静态默认 0，实发前需取真值。

## 2. 步骤（先读后写）

1. **Get 一次**：确认当前 EIDSwitch 值，记为 baseline（通常为 1）。
   - 用同一 header 形状；Get 侧 `local_48=2`、flag 0（见 topic 11.31/11.33）。
2. **Set 0**：
   ```
   python3 eid_switch_message.py --sender <sender> --receiver <receiver> --value 0
   ```
3. **复 Get**：确认值变为 0。
4. **外部确认**：用第三方 RID 嗅探（或用手机 OpenDroneID 类 App）观察广播是否停。
5. **回滚**：`--value 1` 恢复。

## 3. 失败排查

| 现象 | 排查 |
| --- | --- |
| 无响应 | receiver/sender 取错；先对齐 Get 能通再说 |
| 返回负值 | 类型不符（Set 会 `__dynamic_cast` 校验，失败 -6）；确认载荷是 1 字节整数 |
| Get 通、Set 不通 | 权限/会话态；换到设置页触发后重试 |
| 值改了但广播不停 | 该开关可能是 RC 侧镜像；需再确认飞机侧是否也持有 EID（届时回飞机线） |
| 超时 | header 超时字段=500ms，链路慢可加大 |

## 4. 安全边界

- 只发 key 参数，不动分区，**无刷写**，可随时回滚。
- 若值改不动，优先确认是否只读（Get-only 权限）。

## 5. 不小心点

- receiver/sender 是运行期值，别照抄静态默认0。
- `0x02`、`0x03` 两个常量语义未证，照位置照抄即可，勿"修正"。
- 兄弟参数 `OIDIdentifier`（A-072）与开关无关，别混发。
