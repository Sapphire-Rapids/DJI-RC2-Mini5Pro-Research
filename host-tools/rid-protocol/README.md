# rid-protocol — 遥控器侧 RID 关闭（无刷写）

从 DJI Fly 静态恢复的 Remote ID 关闭路径。全程只发协议，不刷写。

## 结论

- 主键：SDK characteristic 名 **`EIDSwitch`**；关闭 = Set 值 0
- 区域备选：`EU_CE_enable_c0_rid_0`（observer 绑定，非命名 handler）
- 报文：cmd119(0x77)/sub3/attr0x12/'IW' 魔数/timeout500/1 字节载荷
- 路径：App → 本地 socket + `logic` → djilink → bulk/USB → 飞机

## 文件

| 文件 | 作用 |
| --- | --- |
| `EID_SWITCH_MESSAGE.md` | EID 报文规格（布局表、依据、边界） |
| `eid_switch_message.py` | EID 发射器（A-071） |
| `test_eid_switch_message.py` | EID 自检：对反编译 ctor 逐字节断言 |
| `oid_identifier_message.py` | OIDIdentifier 发射器（A-072，RID-005B 对齐：18字节 pack、receiver 0x92） |
| `OID_IDENTIFIER_MESSAGE.md` | OID 规格（RID-005B 对齐） |
| `test_oid_identifier_message.py` | OID 自检 + 0x70 上限 |
| `opid_message.py` | 操作者注册号 set/delete 发射器（A-076） |
| `test_opid_message.py` | opid 自检 + 16 上限 |
| `position_message.py` | 位置加密发射器（A-078） |
| `test_position_message.py` | 位置自检 |
| `adsb_switch_message.py` | ADS-B 代理开关发射器（A-079） |
| `test_adsb_switch_message.py` | adsb switch 自检 |
| `height_message.py` | 动态最大高度 GET 发射器（A-080） |
| `test_height_message.py` | height 自检 |
| `VERIFY_RUNBOOK.md` | 上手验证手册（A-073） |
| `RC_RID_BREAKTHROUGH.md` | 总收口（A-074，含证据表） |

## 用法

```
python3 eid_switch_message.py --sender <s> --receiver <r> --value 0   # 关
python3 eid_switch_message.py --value 1                               # 回滚
```

自检：

```
python3 test_eid_switch_message.py && python3 test_oid_identifier_message.py
```

## 边界

- sender/receiver 是**运行期值**（sender 自动、receiver = Characteristics+0x30），静态默认 0。
- socket 字面名未取（H-37 推断为 `whoami`，实机用 `ss -x` / `/proc/net/unix` 核对）。
- 值改了但广播不停 → 可能只是 RC 镜像，回飞机侧后备 `AIRCRAFT_STUE_CHECKPOINT.md`。
