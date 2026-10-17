# RID 广播字段控制地图

目标：穷举 RID 可写面，逐项给状态。状态沿用仓库规范。

依据：`docs/05_RID_CONTROL_SURFACES.md`（RID-001…005B 等既有条目）+ 本目录线路解码。

## A. 已解出线路的（STATIC）

| 字段 | opcode | 载荷 | artifact | claim |
| --- | --- | --- | --- | --- |
| EID enable 开关 | cmd119/sub3 | 1 字节（0=关） | A-071 | C-377/C-380/C-381 |
| OIDIdentifier 实名标签 | cmd214/sub17 | 字符串 ≤0x70 | A-072 | C-388/C-389 |
| OperatorRegistrationNumber | cmd120/sub3 | 字符串 ≤16（空=删除） | A-076 | C-408 |

## B. 已解出 opcode、载荷未解（STATIC）

| 字段 | opcode | 备注 | claim |
| --- | --- | --- | --- |
| RidImportModule 注册/导入 | cmd75/sub17（子字段0x4b） | 日本注册通道 | C-409 |
| CccBroadcastSignalQuality | 待解（handler 未命名，C-413） | 广播质量/位图（C-077） | — |
| UploadMobileDevicePosition | cmd67/sub17（AES+HMAC，whitebox 0x37） | 载荷细节待解 | C-412 |

## C. 非 settable（需另寻路径）

| 字段 | 现状 | claim |
| --- | --- | --- |
| ComplianceSerialNumber（飞机/UAS ID） | get/listen-only，无 SET；由 SN 派生 | docs/05 |
| 四 capability flag（Cloud/EU/FR/JP） | listen-only | C-133 |
| RIDRegistedInfo | action | C-133 |
| RIDImportResult | getter | C-133 |

## D. 数据面（App 自发）

| 字段 | 路径 | claim |
| --- | --- | --- |
| 手机位置 | `0x11/0x43` `app_update_pos_enc`，每 500ms | docs/05 |

## E. 残差

- ~~OID 对齐 RID-005B~~ 已完成（C-411，A-072 v2）。
- UE/CE 区域键 `EU_CE_enable_c0_rid_0` 为 observer 绑定（C-405）。
- receiver 统一来自 Characteristics+0x30，运行期取值。
- 全部 STATIC；live inventory/键存在性证据待实机。
