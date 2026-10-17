# OIDIdentifier（中国 UOM 实名标签）报文规格 — RID-005B 对齐

状态：`STATIC`。无设备，未实发。依据：`docs/05_RID_CONTROL_SURFACES.md` RID-005B + 本目录反编译。

## 1. 事实（对齐 RID-005B）

- command `0x11/0xD6` `china_uom_realname_tag`；`0x11/0xD5` 是 publish push，不是 setter
- product-139 无 HostID ExtraParam → **receiver 固定 type/index 18/4 (`0x92`)**（非调用方给）
- timeout 500 ms、retry 3
- SET pack = 18 bytes：`[01][03 if empty else 01][16-byte field]`；最多复制输入前 **8** bytes，field 余位补零
- GET 同样 18 bytes，只写前缀 `[01,02]`；本发射器**确定性清零**未定义 tail（不复制 vendor 的未初始化）

## 2. 用法

```
python3 oid_identifier_message.py --text 12345678     # SET
python3 oid_identifier_message.py --get               # GET
```

## 3. ACK

SET 与 GET 均从 response byte 1 取 result；成功 GET 从 bytes 2--9 构造八字节值。
独立 parser 至少要求 SET ACK 2 bytes、GET ACK 10 bytes。byte 0 语义未知。

## 4. 边界

- 0x70 上限是另一产品分支（缓存 ProductType 0x70）的 receiver index 0 情形；product-139 用 0x92。
- 旧 UI 约束输入为八位数字。
- 这是中国 UOM 实名标签，**不是** EASA OPID / 普通 Basic ID / global switch。
