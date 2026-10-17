# 遥控器侧 RID 突破口 — 总收口

状态：`STATIC`，代码侧见底；唯一开放项是实机取值。**全程无刷写**。

## 1. 结论

Remote ID 的开关在遥控器侧可被定位并（协议上）关闭：

- SDK key 名：**`EIDSwitch`**
- 关闭动作：对该 key 执行 Set，值 0
- 报文：cmd119(0x77)/sub3/attr0x12/'IW' 魔数/timeout500/1 字节载荷
- 路径：App → 本地 socket + `logic` 协议 → djilink → bulk/USB → 飞机

## 2. 证据链（已入 claim）

| 环节 | 证据 |
| --- | --- |
| DJI Fly RID 名称面 | C-373 |
| 名称 xref 计数 | C-374 |
| EIDSwitchGet/Set 本体 | C-377 |
| 模板常量 cmd119/sub3/attr0x12 | C-380 |
| 载荷 1 字节（value+8） | C-381 |
| pack 类型 eid_switch_pack | C-382 |
| base_req 头部布局 + sender 自动 | C-383 |
| receiver 调用方给 | C-384 |
| receiver = Characteristics+0x30 | C-385 |
| 发送虚槽 0x128 | C-386 |
| 传输 SendPack → SendData | C-387 |
| 注册 InsertCharacteristics | C-390 |
| rc331 native 守护进程 | C-392/C-393 |
| local/logic 路由 | C-394 |
| dji_link 本地 socket | C-395 |
| unix socket 命名机制 | C-396 |

产物：A-071（EID 发射器）、A-072（OID 发射器）、A-073（验证手册）。
推断：H-37（socket 名≈`whoami`）。阻塞：B-24（实机 socket/取值）。

## 3. 唯一开放项

需实机取：socket 字面名（`ss -x` / `/proc/net/unix`）、sender、receiver。
取到后按 A-073 执行即可。

## 3b. 区域备选键

`EU_CE_enable_c0_rid_0`（EUCeCxV1 注册类）是与 EIDSwitch 并列的区域 RID enable 键（C-400/C-401）。
若目标区服走 CE 路径，优先用它。

## 4. 边界与风险

- 值改了但广播不停 → 可能只是 RC 镜像，需回飞机侧（后备在 `AIRCRAFT_STUE_CHECKPOINT.md`）。
- receiver/sender 是运行期值，勿照抄 0。
- `0x02`/`0x03` 常量语义未证，照位置照抄。
- 兄弟参数 OIDIdentifier（A-072, cmd214/sub17）与开关无关，勿混发。
