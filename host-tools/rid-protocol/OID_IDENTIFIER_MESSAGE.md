# 中国 UOM OIDIdentifier 离线请求结构

状态：`STATIC`，当前无设备、未发送。A-072 只生成候选 hex；它不是实际发送器，也不是通用 Basic/UAS ID 编辑器。
依据：[RID 控制面](../../docs/05_RID_CONTROL_SURFACES.md) RID-005B。

- command `0x11/0xD6` 为 `china_uom_realname_tag`；`0x11/0xD5` 是 publish push。
- product-139 无 HostID ExtraParam，静态 receiver type/index 为 18/4（`0x92`），timeout 500 ms、retry 3。
- SET pack 为 18 字节，最多复制 8 字节，剩余字段补零；0x70 是另一产品分支条件，不是本对象的字符串长度上限。
- 官方 GET 只确认 18 字节请求的前两字节 `[01,02]`，尾部未见初始化。生成器的确定性零尾是本地测试选择，不能称为
  byte-exact 官方 GET，也不能据此准入发送。

SET/GET reply result 在 byte 1；成功 GET 的值位于 bytes 2--9，独立 parser 至少需 2/10 字节。
该业务面与 EASA OPID、FAA Basic/UAS ID、France EID、global RID switch 分开。真实标识保持私有。

```sh
python3 oid_identifier_message.py --get
```

输出只有候选 hex；当前没有 canonical live readback、restore 或 RF 对应证据。
