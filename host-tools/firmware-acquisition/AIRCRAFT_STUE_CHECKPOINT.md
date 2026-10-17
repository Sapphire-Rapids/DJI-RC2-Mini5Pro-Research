# 飞机侧 STUE 破解 — 续跑检查点

状态：`IN-PROGRESS`。遥控器侧（rc331）已完成且无阻碍；本文件只覆盖飞机侧（wa150）。
目标：解出 WA150 固件 STUE 明文 → 在 0802 定位 RID 广播 owner / enable 参数。

## 1. 已确认的事实（都已入 claim，勿重做）

| 事实 | 证据 |
| --- | --- |
| 四份本地 wa150 模块均 hdr_v2 / enc_key STUE / attrib0x0，但仍加密 | C-366、C-367、N-82 |
| 固件 crypto = `CRijndael` AES-256 CBC，IV `CRijndael::sm_chain0` = `a0898b00000000009236923600000000`；MakeKey(key, iv, 0x20, 0x10)，Decrypt(len,1) | C-331 |
| key 是现场派生，非外带常量 | C-335、C-337 |
| key = `MD5(data,len)` → `digest()` → ostringstream 以 hex 基数 + fill `0` → `str()` 得32位小写补零 hex | C-337 |
| 同一 lambda 另有 XOR 循环：pad 索引为 `rbx mod 17`，字节变换为 `ror8(b, i&7)`，原地、字节局部 | C-340、C-343、C-360 |
| FirmPack 经 websocket 路由到 NfzPack 方案；无 base64/hex 解码 | C-355、C-356 |
| 变换源 `-0x208` 是构建的 `XsBuffer` 容器；`append`/`cvPc` 都返回 `this`，故索引的是**结构体字节** | C-347、C-357、C-361 |
| XsBuffer 字段布局：0x0 vtable、0x8 数据指针、0x10 cap、0x18 len；活对象恰32字节 | C-363 |
| 调用 ABI 已复核：rdi=-0x310(sret)、rdx=-0x1d0(key)、rsi=-0x218(data=密文) | C-352 |
| key 经 `strlen` 截断；vtable 低字节含0x00 且 ror8(0)=0，故 strlen 约在 index3 停，`MakeKey` 随后越过 NUL 读入对象尾部 | C-369 |

## 2. 未闭合残差（就是当前要做的三件事）

1. **结构体指针字节**：0x8 数据指针的运行时低字节（堆地址）。
2. **12 字节尾邻**：循环上界是长度0x2c(44) > 32字节结构，`-0x208+44` 落到 `-0x1dd..-0x1d1`（未初始化栈）。
3. **`init` 疑点**：循环每轮还调 `*0x28`（vtable slot = `init`），而 `init` 清零 0x8..0x20 —— 若属实，seed 中段近似全零，扫描空间大幅压缩。**先判这个**。

## 3. 代码坐标（Assistant x86_64 dylib）

- dylib：`/Applications/DJI Assistant 2(Consumer Drones Series).app/Contents/MacOS/DJIServices/libDJIUavService.dylib`
- 变换循环：`0x68af70`–`0x68b002`（`mulq 0xF0F0F0F0F0F0F0F1` 除17魔数在 `0x68af73`）
- `-0x208` 构建链：`0x68ad48`–`0x68af50`
- MD5 构造：`0x68a5d5`；`digest`：`0x68a721`
- key 字符串组装：`0x68b0f1`（`strlen` 0x68b0e1、`fromAsciiHelper` 0x68b0ec）
- aesDecode2 调用：`0x68b109`；其后 `pkcs7UnPadding`：`0x68b11c`
- vtable `__ZTV8XsBufferIcE` = `0x8fba40`

## 4. 现成工具

- `wb_aes_bridge.py`（A-067，WAES 原语，3 测通过）
- `wb_aes_key_recover.py`（A-069，表仿射分解）
- `aes_decode_bridge.py`（A-070，真实 `aesDecode2Ex`，key 生效）
- `stue_plaintext_probe.py`（A-068，方案枚举）
- 镜像树构建自带（`build_mirror`），Rosetta 运行方式见各脚本 `_reexec_under_rosetta`
- 快速进程内扫描样例：`/tmp/big_sweep.py`（随机 ptr+tail+cap/len，raw/tf 两路）

## 5. 判据

只看 `plain_cksum`（加性、非补码）是否命中；`encr_cksum` 是补码形式，仅用于校验字节范围。
样本优先级：2603（小、单 chunk）先行，命中后套 0802。

## 6. 不要重做

- 不要再用普通 AES 直接套 STUE（白盒带常量编码，不等价）。
- 不要重复枚举 mode（CTR/CBC/ECB/OFB/CFB 已全试）。
- 不要重复 md5 派生（C-337 已定）。
- 不要重复 mod17/ror8（C-340/C-343 已定）。
- 不要重复 6144 指针密扫（C-365）与 tail 变体（C-368）。

## 7. 恢复动作

先判 `0x68afb1` 的 `*0x28` 是否确实执行 `init`（看是否只是预留、还是每轮清零），据此决定 seed 中段取值；
然后按 seed = `vt(8) + ptr(8) + cap(8) + len(8) + tail(12)` 重建并扫 ptr/tail，跑 `decode2ex` 验 `plain_cksum`。
