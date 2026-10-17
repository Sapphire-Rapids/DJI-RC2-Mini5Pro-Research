# RID 控制面总收口

状态：`STATIC`，代码侧穷尽。无设备，未实发，**全程无刷写**。

## 1. 结论

遥控器侧可从协议上完整控制 Remote ID 广播面：开关、标识、位置、高度、广播代理、ADS-B 量级。

- 广播代理总开关：SDK key `ADSBSwitch` → cmd55/sub17，1 字节
- RID/EID 开关：key `EIDSwitch` → cmd119/sub3，1 字节（0=关）
- 操作者注册号/删除：key `OperatorRegistrationNumber` → cmd120/sub3，字符串 ≤16
- 中国实名标签：`OIDIdentifier` → cmd0x11/0xD6，18 字节 pack（RID-005B 严格对齐）
- 位置：`UploadMobileDevicePosition` → cmd67/sub17，AES-256-CBC + HMAC
- 动态最大高度：GET cmd80/sub17
- ADS-B on/off：GET cmd12/sub17

## 2. 路径（全无条件成立）

App → 本地 socket + `logic` 协议 → `djilink` → bulk/USB → 飞机。
注册经 `BaseAbs::InsertCharacteristics`；传输 `SendSetPack → BaseAbstraction::SendPack(slot0x128) → UavCoreCancelation::SendData`。

receiver 统一取 `Characteristics+0x30`，sender 由 `GlobalPacketStatus::GetGlobalSenderIndex()` 自动。

## 3. 产物（发射器 + 自检）

| 对象 | artifact | 自检 |
| --- | --- | --- |
| EID 开关 | A-071 | ✅ |
| OIDIdentifier | A-072（RID-005B 对齐） | ✅ |
| OperatorRegistrationNumber | A-076 | ✅ |
| 位置（加密） | A-078 | ✅ |
| ADS-B 代理开关 | A-079 | ✅ |
| 动态最大高度 GET | A-080 | ✅ |

规格文档：`EID_SWITCH_MESSAGE.md`、`OID_IDENTIFIER_MESSAGE.md`；手册 `VERIFY_RUNBOOK.md`。

## 4. 验证通道

`RidWorkingStatusPush`（push-only，C-439/C-440）给出一读路径：先读它确认基线，再发 set，复读确认。

## 5. 明确不可写

- `ComplianceSerialNumber`：派生 listener，无 Get/Set（C-428/C-429）
- `SerialNumber`（底层 SN）：Get-only，164 处引用无 Set（C-430/C-431）
- 四 capability flag、RIDRegistedInfo(action)、RIDImportResult(getter)：非可写字段

## 6. 残差（含负结果）

- `CccBroadcastSignalQuality`：camera 族、计算指针到达、无命名 handler（C-413/C-438、N-90/N-98）
- `RidImportModule`：仅 opcode（C-409），载荷未解
- `dynamic_max_height`：handler 匿名（C-437、N-97）
- 全部 `STATIC`；live inventory/键存在性/ACK 待实机
- 飞机侧 STUE 后备在 `AIRCRAFT_STUE_CHECKPOINT.md`

## 7. 风险

- 值改了但广播不停 → 可能只是 RC 镜像，转飞机侧
- receiver/sender 是运行期值，勿照抄 0
- `0x02`/`0x03`/`0x05` 常量语义未证，照位置照抄
- OID 与 EID 勿混发；opid 空载荷=删除
