# rid-protocol — 离线协议结构研究

状态：`STATIC`，当前无设备。六个报文 CLI 只生成 hex，没有 USB、socket 或其他设备传输实现；新增 SDK 探针只进行隔离 CPU 函数模拟。
C-448/C-449 撤回此前“RID 关闭路径”“全条件成立”和“完整控制”的表述。静态结构与自检不构成实机能力。

| 文件 | 当前用途 |
| --- | --- |
| `eid_switch_message.py` / `EID_SWITCH_MESSAGE.md` | A-071；France GET02/SET00或01 payload，不是 global RID 开关 |
| `oid_identifier_message.py` / `OID_IDENTIFIER_MESSAGE.md` | A-072；UOM18 B payload、截前8 B；本地零 GET tail，不等于 Basic/UAS ID |
| `opid_message.py` | A-076；OPID GET02/DELETE01/SET0010+exact16，完整20字符验证由 caller 负责 |
| `position_message.py` | A-078 v3；显式 plaintext22/key32/IV16 输入，生成 84 B 离线 payload，不提供typed坐标API或transport frame |
| `sdk_keychain_probe.py` | A-087；固定 SDK Get(0x37) 的隔离模拟与重封装检查，只输出长度/哈希 |
| `adsb_switch_message.py` | A-079；AirSense Boolean1 B payload，不是 RID 总开关 |
| `height_message.py` | A-080；动态最大高度 GET empty payload，输出空hex行，不是 RID 高度编辑器 |
| `test_*_message.py` | 合成结构/确定性自检，不能替代官方输出或设备对照 |
| `VERIFY_RUNBOOK.md` | 离线验证范围与尚缺证据，A-073 |
| `RC_RID_BREAKTHROUGH.md` / `RID_CONTROL_CONSOLIDATION.md` | 更正后的静态研究范围，A-074/A-081 |
| `RID_FIELD_MAP.md` | 业务面和验证缺口，A-077 |

离线示例：

```sh
python3 eid_switch_message.py --value 0
python3 test_eid_switch_message.py
python3 test_oid_identifier_message.py
```

这些命令只打印 payload 或测试结果。C-469 已删除五个旧 CLI 的伪32 B对象头及 sender/receiver 参数；
内部 request 内存布局不是 wire frame。C-468 的条件 HostID prefix/helper 检查也没有验证 live route、owner 或 transport。`EU_CE_enable_c0_rid_0` 在既有 direct USB 正对照会话中未暴露，不作为可用替代开关。
`RidWorkingStatusPush` 没有主动 GET，也不能单独证明 EID/ADS-B SET 已应用或 RID RF 改变。

SDK probe 复现（只使用本地固定 hash 的 libsdk_base.so）：

```sh
python3 -m pip install -r requirements.txt
python3 sdk_keychain_probe.py path/to/libsdk_base.so
```

预期报告包含 Get 返回 32 B、三个 block roundtrip PASS 和 48 B rewrap 一致；不输出 key/ciphertext 字节，不启动 Android
loader/OS、不连接设备。它只验证 keychain；C-464/C-465 另行检查 JNI 原始片段和 crypto helpers，并修复 A-078 v3。

业务语义与历史实机边界以[RID 控制面](../../docs/05_RID_CONTROL_SURFACES.md)的 RID-002B、RID-003、RID-005C、
RID-009 和 RID-011C 为准。A-078 v3 已修复旧 key/布局错误，但仅是离线 payload encoder，不能当作可用坐标编辑器。

位置 payload 复现（依赖固定为 `pycryptodome==4.0.1`、`unicorn==2.1.4`）：

```sh
python3 position_message.py --plaintext-file path/to/plain22.bin --key-file path/to/decoded-key32.bin --iv-file path/to/iv16.bin
python3 -m unittest -v test_position_message
```

输出为 `LE32(80) + AES-256-CBC ct32 + IV16 + HMAC-SHA256(ct+IV)32`。输入必须已序列化；上游lat/lon×1e6和alt×100见C-126/C-467，高度原单位/基准与Java来源仍未知，
不内置厂商 key/IV，也不加内部 request/DUML header。4 项主机测试含独立 OpenSSL synthetic fixture。
C-465 的 helper/片段对照不是完整官方 handler 输出、设备发送或 RF 验证；本批 36 项状态 parser 测试另行登记为 C-463。

OPID 用法选择 `--get`、`--delete` 或 `--payload-file path/to/validated16.bin`；SET 文件必须恰为16 B，
不接收或验证完整20字符登记输入/country/checksum。八个 schema 测试、九个有效 CLI case 和五个废弃路由参数拒绝
是 C-469 的独立主机结果，不代表厂商完整 handler 或实际设备发送。

C-467区分40 B SDK MobileDevicePositionMsg、handler22 B和encrypted84 B。producer时间是构造时epoch秒；
有限越界/近零坐标会清flag仍排队，不等于设备接受/拒绝或GPS fix。当前编码器保持显式22 B输入，不新增typed位置编辑器。
