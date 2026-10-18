# WA150 STUE 离线研究检查点

状态：`UNKNOWN`。WA150 STUE 尚未解密，RID broadcaster owner/enable 尚未定位。当前没有设备。
RC331 0205 平台有可读静态样本，0200 内层 TBIE/FLYA 仍受保护；这不代表遥控器侧 RID 控制已完成。

## 已确认的更正

- C-442：XsBuffer 的实际 vptr 为 vtable 符号加 16 字节。get 读取独立数据指针；变换不读取对象自身的 vptr/data/cap/len。
- C-443：`sm_chain0` 是指针变量，真正 IV 为 16 字节零。直接调用真实 helper 的旧实验不能一并判成错误 IV。
- C-444：NFZ callback 的 MD5 是输入/输出日志摘要。key 来自常量缓冲，33 字节已初始化、32 字节参与变换；
  输出为 32 个可打印字节且无内嵌 NUL。只公开 key SHA-256 `7dc2f9655b6ccf792d92e6d241e8c8d612ccd327f285e238e99f35d93e300b71`。
- C-445：`ProcessUpgradeFirmPack` 的 type 0/1/8 分别走普通固件、NFZ、本地固件。
  修正 NFZ key + 零 IV 对 2603 的一次直接尝试仍未匹配 plain checksum，只排除此直接应用。
- C-446：旧公开探针不能复现 C-326 的枚举；代码修复后的验证单独记为 C-447，不追认历史结果。

## 撤回的前提

C-331 的 IV 字节、C-333 的调用方 key、C-335/C-337 的 MD5 KDF、C-349 的 map 顺序、C-355 的普通固件路径归属、
C-357/C-361/C-369 的对象字节/strlen 模型均已撤回。C-363 的对象字段布局保留，撤回把布局当作变换输入的解释。
堆指针、12 字节未初始化栈尾、每轮 init 清零不再是待解决的 key 变量。不要继续随机 ptr/tail/cap/len 扫描。
相关历史尝试仍在[固件记录](../../docs/07_FIRMWARE_TRUST_BOUNDARY.md)和[负结果](../../docs/09_NEGATIVE_RESULTS.md)中。

## 当前结果（C-450--C-453）

- A-082 是公开 IMaH-v2 单候选校验器：KEK 解包 scram 得 content16，再做连续 AES-128-CTR；也可直接给 content16。
  raw key 只读 stdin；不导出 key/明文、不验证签名。6 项新增测试及 firmware-acquisition 59/59 通过。
- 真实 2603 的三个 v2 候选（NFZ32-as-KEK、WAES.decrypt/encrypt(scram)-as-content16）都未匹配 checksum。
  C-445 的直接 CBC、C-447 的 fixed-WAES、C-451 的三次 v2 试验是不同模型，不合并成“全部 key/mode 已排除”。
- C-452 只跟踪 Assistant method-4/register-upgrader；下载/cache 校验、tar copy 与 FTP 路径保持输入字节，
  已检查范围没有恢复出 STUE decoder。无证据表明当前 WA150 会选择该方法，也不能扩大为整个 Assistant 没有 decoder。
- C-453 筛选 517 fork 元数据，实际检查 25 份 IMaH 源码，均同上游且无 STUE；不是全网或全部 fork 检索。

## RC331 离线链已定位（C-454--C-457）

A-005 外层为空 enc_key 且完整性通过，offset 480 的第二层 TBIE/FLYA 仍加密，密文从 offset 960 开始。
C-319 只保留外层事实，C-322 的 RC 全明文推论撤回。六个公开 TBIE 版本仅做 prefix 试探，不是完整 checksum 排除。

已从既有 A-004/0205 OTA 完整性链提取 A-083 bw_secure、A-084 libtee_util.so、A-085 dji_decrypt，并定位静态调用链：
480 B 固定 header 的 client → QSEE 命令 0x17/0x18 → payload-key init/持久 cipher context。
TBIE CMAC 派生使用受保护 RPMB root；存储 root 的解封/认证依赖 HUK-backed qsee_kdf。无设备 RPMB 数据或 HUK 输出，
未恢复 root/key，QSEE mode 常数 1/2 的名称未独立核对。所有厂商 ELF 均未运行。

## 独立 SDK/位置支线（C-458--C-462）

C-458/C-459 已恢复固定 SDK 的真实动态符号，并以 A-087 完整 Get(0x37) 隔离模拟得到 32 B 返回值；
roundtrip/重封装一致只验证 keychain。A-078 v2 的错误已由 C-464/C-465 后续修为 v3：22 B 显式输入生成 84 B payload，
原始片段/helper与4项测试支持模型；C-467 后续确认预缩放与 epoch 秒，C-473 接通选定 Java/default-provider 链。
高度契约以该来源且 altitude 有效为条件；实际 provider/有效性、完整 handler/transport/RF 未闭合。C-460 的 TEE 位置 envelope 是另一静态路径，算法 enum 与 SDK/TEE key 对应未确认。
A-088 GPS updater 的已检查 transfer 路径和独立公开调查没有新增 STUE consumer，不覆盖所有输入 producer 或全网。
这些结果服务于 Remote ID 开关及广播参数控制面板目标，不代表 STUE 解密或设备控制成功。

## 下一步与判据

当前具体缺口是 RC331 TBIE 的 root input，以及 STUE 自己的 owner/derivation；不再把“找到 bw_secure”列为下一步。
沿新的明确调用边或可用离线样本继续，不推断 RC331/WA150 共享 key/scheme，不把缺少 RPMB/HUK 输入扩大为所有离线方法不可能。
现成 client 固定 480 B 起点不适用于 WA150 608 B 布局；不直接执行。未出现新 key/路径证据时，不重复三个已失败候选，
不重启已撤回的 ptr/tail 扫描。

2603 逻辑 chunk 长度 435,382 B、stored payload 435,392 B；public-v2 对加密 chunk 按 32 B 对齐，CTR 仅跨加密
chunk 连续，明文 chunk 与 gap 不推进 counter。plain checksum 包括解密 padding；加密 checksum 使用完整 header
（对应字段清零）加 payload，不含 RSA signature。先核 payload SHA-256/encrypted checksum；命中后仍需独立结构佐证。

只公开候选来源、长度、哈希和校验结果，不公开 key、私有样本或厂商反汇编；当前不连接或修改设备。

## 本批完成项与范围（C-466--C-470）

Android upgrade配置/签名/transfer所检查函数未给出STUE consumer；不扩大到整个SDK。
C-467保留C-126既有缩放并补齐类型、40 B SDK序列化、Java byte[]边界和epoch秒；invalid有限坐标仅flag0仍排队。
C-468/C-469已纠正receiver/重载和五个CLI，只有离线片段/payload证据，没有设备/RF。

小模块当前是A-0661200重新获取复核及新A-092最小wa140bat1100，两者STUE完整性通过但未试key/解密/验RSA；
余五个1100未检查。STUE owner/derivation和TBIE root input缺口不变，不因为下载更多密文称解密进展完成。

## Java 位置来源的独立进展（C-471--C-473）

固定 Fly carrier 的 22 条目录/map 和四个分析视图已核对；只重建 header/string index，保留后续字节。
这不等于原始 DEX/header 解密；五个受保护 type 表段未恢复，也未提供 STUE key 或固件明文。
选定 Java 链连上两层缓存和 native 三标量接口。Android/default 的米/WGS84 椭球契约以 altitude 有效为条件；
所查方法不检查 hasAltitude，还可混合较新 network 坐标/时间和较旧 GPS 高度，新消息不证明 fresh fix。
实际 provider、owner、读回/恢复和 RF 仍未验证，STUE/TBIE 缺口不变。
