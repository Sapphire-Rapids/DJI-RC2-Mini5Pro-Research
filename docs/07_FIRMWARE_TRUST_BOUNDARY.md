# 固件样本、完整性与信任边界

## 1. 适用范围

本文登记 RC331、WA150 和 DJI Fly 样本的身份、可验证边界、离线实验结果及不能由这些结果推出的结论。本文不包含厂商固件、APK、共享库、分区、解密输出、反编译代码或反汇编正文。

状态标签遵循 [AGENTS.md](../AGENTS.md)。后续记录与本文冲突时，较新的精确工件审计和带恢复读回的实机证据优先；相邻版本静态证据不能自动升级为当前设备事实。

最新进展见第16--22节（C-466--C-475）：Android upgrade限定负结果、位置producer语义、条件HostID/纯payload修复，以及
A-0661200复核/A-0921100新检查。没有STUE明文、实际控制面板或RF成功。第15节保留36+4项parser/payload主机验证。
RC331 固件支线见第 13 节（C-454--C-457）：0200 内层 TBIE/FLYA 仍加密；已从现有 0205 OTA 验证并提取三个 QSEE 组件，
静态链指向受保护 RPMB root/HUK 输入，尚未恢复 key。第 12 节的三个 v2 候选均未命中，STUE 仍未解密。

## 2026-10-17 审计更正与当前边界（C-442--C-449）

审计对象为 `DeepSeek-Harness` 提交 `5d761a1e31c65ab3cec4d1d8caa2bbe5ac23c76e`。
该轮没有飞机或遥控器，所有结果均为离线代码、文件或本机 helper 验证；未解开 WA150 STUE。

| 更正 | 已验证结果 | 不能据此推出 |
| --- | --- | --- |
| C-442 / F01 | vptr 比 vtable 符号多 16 字节；get 返回数据区。撤回 C-357/C-361/C-369 及其堆指针、栈尾、每轮 init 推论 | STUE key 依赖地址或未初始化数据 |
| C-443 / F02 | NFZ helper 的实际 IV 是 16 字节零；旧记录误读指针存储 | 所有直接 native 调用都使用了错误 IV |
| C-444 / F03 | MD5 仅供 before/after 日志；NFZ key 是确定的 32 字节常量变换结果，无内嵌 NUL | MD5(data) 是 KDF，或该常量就是 STUE key |
| C-445 / F04 | type 0/1/8 分别分派普通固件/NFZ/本地固件；修正 NFZ key+零 IV 直接试 2603 一次，checksum 不符 | NFZ 是普通固件必经路径，或 STUE 不可解 |
| C-446 / F05--F10 | 旧探针存在非整字 checksum、未使用 ck、ECB 方向、架构重启、argv 容量和依赖缺陷 | 旧公开版本已完成所声称的全枚举 |
| C-447 | v2 修复后 53 项测试通过；真实 2603 的十个 fixed-WAES 候选均未命中；本机 KAT/stdin/同长调用通过 | 旧枚举被追认、派生 key 已测试或 STUE 已解密 |
| C-448/C-449 | France EID、AirSense、地区策略与 app location 是不同表面；六个 CLI 仅生成离线 hex | global RID 开关、完整控制、实际发射或可用坐标编辑器 |

NFZ key 只登记长度 32 与 SHA-256 `7dc2f9655b6ccf792d92e6d241e8c8d612ccd327f285e238e99f35d93e300b71`。
精确 Assistant 库 SHA-256 为 `c55da41265f925f64c2d704deb68f65fcff44435c9681839cc8545cd07dd76a5`。
2603 样本 SHA-256 为 `4a573ab95316de69137deb71249ead09c23325a28acbf9ee305a36410775f274`，逻辑 chunk
435,382 B、填充范围 435,392 B；checksum 在裁剪逻辑长度前覆盖完整解密填充范围。一次直接尝试的 checksum 为 `0x6cbf5644`，期望为 `0xd2f782ff`。

审计来源保持仓外，不新增公开 artifact：`deepseek-audit.json` SHA-256
`35b24b6ff7556fa186ce61892e871cf8477f04e709da1d73624e3c015ba89516`；
`assistant-native-verification.json` SHA-256 `f65d8174a7dfcd5d28f4e4d748c020ae64fdd9972405d2332825efc5863a5f1c`；
`probe-verification.json` SHA-256 `93c0d150c39582989b4eb842d9a70ce3d58ae2b6201a27a92358e17782878827`。
原生证据引用包括 `ev_2fe1b77dee86b6359672e2d60a908dfd876793445bdc7a5248d5dcdf7ba6f7ca`、
`ev_081c76375d6dc9e91d0f091f920dc284b3e8ae9cab7099b7e485a6a45d18f842`、
`ev_7f3d7686035793dde67df56fc27f40c4860ea1a31e3ba444f3337397d95ff360`、
`ev_06ccdf81ac1df517edf2b5bec4db8aa8475155a214ceadb9b891a46723d2ff67` 与
`ev_2ceab34530c05ef4a306f832970b373e20bfef4929bac7efab25de35256584f2`。
不公开 key 字节、厂商反汇编或私有样本。

下文保留历史研究序列。较早的“唯一残差”“完整复现”“仅剩实机取值”均不能覆盖本节更正；修复后源码验证见 C-447
及[工件登记](11_ARTIFACT_REGISTER.md)，不自动追认旧枚举或提供设备控制能力。

## 2. 版本边界

| 对象 | 状态 | 已知事实 | 不成立的外推 | 公开处置 |
| --- | --- | --- | --- | --- |
| RC 2 操作界面版本 `07.00.0100` | `OBSERVED` | 版本由操作者界面报告；当前 USB 设备曾枚举为 RC331/RC 2 类设备 | C-174 的 signed-package 静态身份不等于 mounted live-file readback | 可公开版本；不公开设备标识 |
| RC331 `07.00.0100/0205` signed system chain | `STATIC` | target aggregate/signed config/`0205` 通过记录的签名与 checksum chain；exact APEX `adbd` 和 packaged `dpad_fuli` 已提取并固定 hash | 不证明当前实机 mounted/installed bytes、live properties、UID 或 SELinux | 只公开身份、hash 与独立描述；aggregate/module/image/APK/binary 不分发 |
| RC331 `10.00.0700/0205` | `STATIC` | 官方相邻 Android OTA 已按公开验证材料完成无强制外层验证，并用于平台静态审计 | 不证明当前 `07.00.0100` 实机具有相同 APK、属性、SELinux、Binder、ADBD 或 localhost 配置 | 只公开身份和独立描述；样本不分发 |
| RC331 `10.00.0700/0200` | `STATIC` | 官方相邻 `flyapp` 模块外层完整性已验证；内层 FLYA 仍受保护 | 不证明已取得可执行的 DJI Fly 镜像；不能用强制输出的密文字节代替明文 | 只公开身份和验证边界；样本不分发 |
| WA150 `01.00.0600` 与 `01.00.0700` | `STATIC` | 官方清单均有十个模块记录；主要变化集中在 `0802` 与 `2603` | 不证明变化必然由 Remote ID 引起；不证明 `2603` 是广播实现 | 只公开模块元数据和哈希；样本不分发 |
| DJI Fly `1.21.10` | `STATIC` | 官方公开下载样本用于定向静态分析；ARM64 native 样本身份固定 | 不证明 RC 2 内置 DJI Fly 与该 APK 相同；不证明静态 handler 在当前会话被选择 | 只公开版本、大小、哈希和独立结论；APK/SO 不分发 |

相关规范见 [范围与脱敏边界](00_SCOPE_AND_REDACTION.md)、[工件登记](11_ARTIFACT_REGISTER.md) 和后续的证据登记。

### 2.1 Exact target system chain（C-174--C-176）

`STATIC`：A-029 `07.00.0100` aggregate 是 `1,446,604,800` bytes，SHA-256
`296cfa63e3c6b011fd1ee8dd911c11f64dac9d34a8424a6fbb95b0c237ab1ae3`。Third-party archive
只提供获取与外层 metadata；内部 signed config 与 `0205` module 又用 `PRAK-2020-01` 完成 header
signature、stored/encrypted checksum 和 decrypted/plaintext checksum verification，全程无
force/skip/truncate。该内层 verification 才是 target bytes 的信任锚点。

Target `0205` 中 A-030 APEX `adbd` 是 `1,497,232` bytes，SHA-256
`b300d9bb90f5941fe2952bc9f6dacc30e639a498be4435f59a4ae95134bd5422`；A-031
`dpad_fuli.apk` 是 `8,849,471` bytes，SHA-256
`58b176eb1e17cacb7522914d282a69a677603ea9026993fc143c6a390211e44f`。二者与既有审计样本
逐字节相同，所以只有对应 binary/package 的静态结论可迁移到 exact target package。该 closure
不自动迁移 framework、Binder、ART、DJI Fly 或 live installed/mounted state。

## 3. RC331 `0205`：可读 Android 平台样本

### 3.1 样本身份

| 字段 | 值 |
| --- | --- |
| 产品/模块 | RC331 `10.00.0700/0205` |
| 模块大小 | `985,959,104` bytes |
| 官方 MD5 | `5c874f6e39819067caa31b67e0ad341b` |
| 本地 SHA-256 | `f707cf3dc0be2894b111ce4973d0206e896a2c7e9c4ebe43de1040b528cf49ce` |
| 证据状态 | `STATIC` |
| 分发状态 | 厂商样本，不进入本仓库 |

### 3.2 已验证的外层事实

- `STATIC`：公开 `PRAK-2020-01` 材料在不使用强制继续选项的情况下验证了 IMaH v2 头签名、加密 chunk 校验和以及明文 chunk 校验和。
- `STATIC`：内层对象是 Android SignApk OTA，包含 update-engine payload、属性和 OTA 元数据。
- `STATIC`：payload 元数据列出 29 个 A/B 分区。研究只定向提取了少量 system/vendor/product/odm/boot/vbmeta 内容；列出分区不表示全部分区已提取或审计。
- `STATIC`：基础 OTA 的 `/dji_apk` 目录为空。这将可读 Android 平台与受保护的 DJI Fly `0200` 模块区分开。

这些事实来自相邻样本的离线验证。它们不建立当前实机的包身份，也不授权安装、升级、恢复、刷写或平台修改。

### 3.3 相邻平台证据的允许用途

相邻 `0205` 样本可用于形成可证伪的版本门禁，例如：

- 对比 Android framework、services、Settings、PackageInstaller 和开发助手包的精确身份；
- 描述 `2ca3:1021` USB composition、ADBD 静态分支和 init 配置；
- 审计相邻 `dji.json` 与 `libduml_frwk.so` 的单活动连接行为；
- 审计相邻 `dpad_fuli` 的 UID、manifest、组件和 Parcelable 结构；
- 形成当前 live 探针应核验的文件哈希、ABI、签名和属性清单。

只有实机只读结果与对应的完整样本身份相等时，某一项相邻结论才可能迁移；单个版本字符串、Binder descriptor、Build ID 或 basename 均不足以迁移整套结论。

## 4. RC331 `0200`：外层闭合、内层受保护

### 4.1 样本身份

| 字段 | 值 |
| --- | --- |
| 产品/模块 | RC331 `10.00.0700/0200` |
| 模块版本 | `12.14.13.85` |
| 模块大小 | `454,223,680` bytes |
| 官方 MD5 | `cc219b04c4fcf34d8b14569a7e55eae1` |
| 本地 SHA-256 | `d8a8fe5b418ee6461f6971d9dfad77bc4491d15160d47d5cf8f7481dc7113949` |
| 证据状态 | `STATIC` |
| 分发状态 | 厂商样本，不进入本仓库 |

### 4.2 验证结果

- `STATIC`：无强制外层验证通过，产生一个 `454,223,200` bytes 的内层对象；其 SHA-256 为 `ea5e447b56823c6aa320eb90d4d883bc9f9223cd250a50b47689d23ffd04cb46`。
- `STATIC`：内层类型为 `flyapp`/`RAW`，包含一个 FLYA chunk，并声明 PRAK 认证与 TBIE 加密。
- `NEGATIVE`：固定公开 corpus 中的八个 PRAK 变体均未验证内层头；六个 TBIE 变体均未产生满足预期明文校验的结果。
- `RETRACTED`：早期限定缓存审计曾未找到当前 `07.00.0100` 的可独立验签 signed config/module
  set；A-029 后续从另一合法公开 archive 获得 target aggregate 并完成 signed system chain，故该
  “当前材料中没有 target signed system package”结论已被后续事实取代。完整 package set 与 live
  mounted identity 仍未闭合。

`NEGATIVE` 结果仅限定于记录的公开 key corpus 和本地审计范围。它不证明所需材料不存在于其他合法来源，也不允许把 `--force-continue` 产生的密文或校验失败输出标记为已解密固件。

## 5. WA150 模块差分

### 5.1 官方清单差异

两版清单各有十个模块。八个模块的版本、大小和 MD5 相同；发生变化的是：

| 模块 | `01.00.0600` | `01.00.0700` | 状态与边界 |
| --- | --- | --- | --- |
| `0802` | `10.00.12.83`，`679,368,672` B，anti `1` | `10.00.15.17`，`679,295,296` B，anti `2` | `STATIC`：IMaH type `E3`，主系统候选；不能据此认定 RID 因果 |
| `2603` | `01.00.00.01`，`436,000` B | `01.05.03.01`，`437,312` B | `STATIC`：IMaH type `GNSS`；可能提供位置/时间，但不是 Wi-Fi/BLE 广播实现证据 |

四个固定下载样本均匹配官方大小和 MD5，SHA-256 如下：

| 包/模块 | 大小 | SHA-256 | 状态 |
| --- | ---: | --- | --- |
| `01.00.0600/0802` | `679,368,672` B | `c36bcbd17f03f6f3aaed66a381c5823e510f72d19a74495b3a30780b2c560386` | `STATIC`，不分发 |
| `01.00.0600/2603` | `436,000` B | `4a573ab95316de69137deb71249ead09c23325a28acbf9ee305a36410775f274` | `STATIC`，不分发 |
| `01.00.0700/0802` | `679,295,296` B | `83978e131181977fee908641102ce8bd9b5c8fe6d34e0af8fd600a1aa5c307a9` | `STATIC`，不分发 |
| `01.00.0700/2603` | `437,312` B | `cb9b8f6c274e50551dbb683d9440eeeef60717775e3db5278c74d79de371aaba` | `STATIC`，不分发 |

`0806` 在两版清单中相同，大小 `12,251,264` B，SHA-256 为 `75bc1b74a0d46a43aa4099fc9f4570087e99c12298985528b5e961c712d1dfbc`。其 IMaH type 为 `DONG`，文件名包含 `4GG4CN`；这是可选通信 dongle 的静态线索，不是主 RID 广播服务证据。

### 5.2 加密边界

- `STATIC`：上述 WA150 样本均为 IMaH v2、PRAK 认证、STUE 加密、单 chunk、384-byte signature。
- `NEGATIVE`：固定公开 PRAK/STUE corpus 未能为这些 WA150 样本建立可验证明文。
- `INFERENCE`：若 `0600` 到 `0700` 的新增逻辑确实位于飞机固件，`0802` 因体量和版本变化是主要静态候选；运行时云控或未变化的无线模块仍可能消费该逻辑。

该推断不建立文件级因果，也不建立可安全修改的偏移。

### 5.3 公开的 `0802` 归属交叉证据（C-112--C-114）

`CORROBORATED`：两张公开 Mini 5 Pro 原始照片的元数据把相机型号标为 `FC9313`，并分别把
`Software` 标为 `10.00.12.83` 与 `10.00.15.17`；这两个值与上表 `01.00.0600`、
`01.00.0700` 的 `0802` 模块版本逐字一致。公开登记只保留页面、原始文件 SHA-256、产品/
软件版本，不复制照片内的坐标或其他私人元数据。该独立对应关系把 `0802` 从“仅凭体量猜测的主系统
候选”提升为产品主应用/相机栈的强候选，但不证明 RID 只由该模块实现。

`OBSERVED`：2026-08-30 操作者确认本机 Mini 5 Pro 飞机固件为 `01.00.0600`（C-220）。该版本
落在 CVE-2026-78306 与 CVE-2026-77812 声明的受影响窗口（`<=01.00.0600`）内，因此本机仍待
固件升级修复这两条 BLE/DUML 网络面；此事实不改变任何 Remote ID 开关结论。

`INFERENCE`：公开安全公告将 Mini 5 Pro `<=01.00.0600` 的 BLE DUML、QuickTransfer/Wi-Fi
配置与相关网络服务列为受影响表面，并把固件更新列为修复方式。官方 `0600 -> 0700` 清单只改变
`0802` 与明确标作 GNSS 的 `2603`。两项事实合并后，网络服务修复位于 `0802` 的解释具有较高
可信度；它仍不是文件级差分、RID handler 或广播开关证据。

`STATIC`：FCC 测试报告记录了实验室通过 USB-C 与厂商工程工具
`DjiSdrConsole-v2.2.8` 配置 BLE/Wi-Fi 测试模式。报告没有 Remote ID 命中，也没有公开该工具、
协议、签名链或恢复路径；工程测试能力不能外推成用户可用的 RID 控制面。

`NEGATIVE`：截至 2026-08-28 的固定公开检索仍未取得 WA150 `0802` 明文、符号、目标
PRAK/STUE、可替换信任根、恢复镜像、RID handler、0700 明文差分或可复现 PoC。该阴性不覆盖
私有、未索引或设备内已解密材料。

## 6. DJI Fly `1.21.10` 静态输入

| 工件 | 大小 | SHA-256 | 状态 |
| --- | ---: | --- | --- |
| 官方 Android APK | `719,464,897` B | `0312228ad536381509c09dbfdf1c7e3d4c825c5936199f444058b112985deb3a` | `STATIC`，厂商 APK 不分发 |
| ARM64 `libsdk_jni.so` | `87,313,856` B | `5abd990c86bcd00c9a652a21e329ad4580a20ec9f80188075ada61f5a7b46286` | `STATIC`，厂商 SO 不分发 |
| ARM64 `libsdk_key_value.so` | `12,684,576` B | `09f4aa8aef65f720da09a1dad79c8851e05d619affaf73708bf6747341208336` | `STATIC`，厂商 SO 不分发 |
| ARM64 `libsdk_base.so` | `7,720,240` B | `e5b290ebc6aa6e409e116cc0d3b84fb4e49c70f6c552feffacd5b15c7c83e873` | `STATIC`，厂商 SO 不分发 |
| ARM64 `libflightrestrictcore.so` | `5,490,392` B | `17da8363e1ddba47313a74801099e6fdf1e6c4b57ef749222b0cf6e3ceb018f3` | `STATIC`，current Fly FlySafe core；厂商 SO 不分发 |
| MSDK 5.18 ARM64 `libDJIFlySafeCore-CSDK.so` | `10,839,728` B | `1749d31c8ececb15b3da7c07a967ac9946ac05a0aaffd9e3d3840bd7db09e1ed` | `STATIC`，独立 public-SDK 对照；不进入仓库 |

这些输入支持精确版本的 key、handler、route、RVA、Build ID、调用边界和失败路径描述。它们不证明当前 RC 2 已加载相同文件，不证明静态 product-139 handler 已被当前会话选择，也不证明任何请求或写入已经执行。

### 6.1 Current Fly 与 MSDK 的 type-6 schema 边界（C-152）

`STATIC`：exact current Fly `libflightrestrictcore.so` 的 `LicenseData` parser 只 typed-decode
fields 1--5。field 7/tag `0x3a` 走 protobuf `SkipField`/`UnknownFieldSet`；exported symbol 也只覆盖
Area、Circle、Country、Height 与 Polygon。对 current Fly core、smali 和 protected bundle 的有界
exact-name inventory 没有找到 `RID_UNLOCK`、`LicenseDataRID` 或 `RidUnlockType`。

独立 MSDK 5.18 `libDJIFlySafeCore-CSDK.so` 则 typed-decode fields 1--8，并为 field 7 建立
`LicenseDataRID`/`level`。这两个 binary/schema 不能合并为一个“current DJI Fly 已识别 type-6”
结论。UnknownFieldSet 可能保留 raw field-7 bytes，因此 current Fly 的 typed-parser boundary 也不
证明 FC 不会返回 field 7 或 aircraft firmware 不会消费相应状态。

### 6.2 Generic set-enable 与 aircraft-side consumer 阴性（C-153）

`NEGATIVE`：exact current Fly V3 set-enable builder 只编码固定 zero、little-endian license ID、
enable/disable action 和结尾 zero；manager 只做 support/version gate。请求不包含 license type、RID
level、region、motor/armed、BLE/Wi-Fi 或 module ID。在 current app 静态范围内，没有找到 type 6、
field 7 或 `0x11/0x12` enabled state 到 WA150 `0802` broadcaster、motor transition 或 BLE/Wi-Fi
enable 的 consumer/xref。

该阴性不覆盖加密 WA150 plaintext，不能证明 aircraft firmware 中不存在 consumer。packed receiver
`0x92` 是协议 endpoint，不是 firmware module `0802` 身份；目前也没有可逆 Mini 5 Pro RID patch
offset。故这一结果收紧而不降低第 8 节的固件修改门禁。

## 7. 非刷写完整性实验

### 7.1 单字节变化

对 `01.00.0700/0802` 的隔离副本在 payload 零基偏移 `4096` 处执行一次 XOR-1。副本以不可刷写后缀保存，没有相邻 manifest，没有传输到设备。

| 项目 | 原样本 | 单字节变化副本 |
| --- | --- | --- |
| 大小 | `679,295,296` B | `679,295,296` B |
| MD5 | `998d1f1448e8f4cddc3269c2c7549f65` | `1332f1f1e6db26ad2c215fcc49599808` |
| SHA-256 | `83978e131181977fee908641102ce8bd9b5c8fe6d34e0af8fd600a1aa5c307a9` | `dafe2c69e0ccf5ebeeaed2e9fd894f3ee3ac997453bc2b247c499aefe64a3fff` |
| 计算所得 encrypted-payload SHA-256 | 与头部一致 | `030e351077962169afb6e377d2d6d8cd2513c8d7cd2892c0f9245503e459be60`，与原头部不一致 |
| encrypted-data checksum | 声明值 `0x81949d7d` | 计算值 `0x81949d7c` |

`OBSERVED`：实验只证明外部 MD5、内部 payload digest 和 encrypted-data checksum 会检测这次变化。它不是 RID patch，也不证明设备端具体拒绝阶段。没有匹配的 WA150 公钥可用于把结果表述为已实证 RSA 验签失败。

### 7.2 不成立的结论

以下结论均未由实验建立：

- 可以重签或生成设备接受的包；
- 可以绕过 anti-version、AVB、TEE、rollback index 或飞控校验；
- 可以安全恢复无法启动的飞机或遥控器；
- 修改某个静态字符串、参数名或 handler 即可改变空口 Remote ID；
- root 或 bootloader unlock 会提供缺失的 FLYA/STUE 密钥。

临时变异副本、重新计算的测试输出和厂商原件均属于排除材料，不进入本仓库。

## 8. 刷写与修改门禁

当前结论为 `NOT ADMITTED`。在以下事实全部由同一精确版本闭合前，不存在固件修改或刷写准入：

1. 精确目标模块和运行代码路径已验证，不是旧产品或相邻版本类比；
2. 原始签名、加密、anti-version、AVB 和 rollback 链已验证；
3. 修改后每一验证层的合法通过方式已知，不依赖私钥猜测或强制输出；
4. 存在与当前 rollback 状态兼容的官方恢复包；
5. 存在不依赖当前 Android、DJI Fly、飞控或主链路正常启动的恢复通道；
6. 使用可牺牲测试硬件，且主飞机、主遥控器和法定 RID 不在风险面；
7. 验证同时覆盖设备读回、重启后状态、机载自报和独立 RF 真值。

当前没有满足上述门禁的记录。Bootloader unlock、Magisk、Root、boot patch 和 firmware flash 均保持 `NOT ADMITTED`。

## 9. Drone-Hacks CFC 架构与 WA150 边界

`STATIC`：Drone-Hacks `2.0.29` 客户端包含通用固件/IMaH/upgrade/job 能力，公开文档说明其 V2
核心在已支持飞机固件中加入 CFC，再通过飞机 Name 字段提供窄运行时命令。该架构说明“host
安装器”和“飞行时控制入口”可以分层，但不公开每个 target 的完整 server job 或 patch。

`NEGATIVE/UNKNOWN`：公开 CFC 支持清单与命令均不含 Mini 5 Pro 或 RID。公开数据只建立
`wa150` 型号登记与独立 FCC ModBox 硬件兼容；没有 WA150 软件产品、CFC image、verified
plaintext、hook、签名接受或恢复链。故 CFC 只能作为架构假设，不能降低第 8 节刷写门禁。

完整证据见 [Drone-Hacks 2.0.29 静态分析](17_DRONE_HACKS_STATIC_ANALYSIS.md)。

## 10. 可复核来源与分发声明

- 公开工具基线：[o-gs/dji-firmware-tools](https://github.com/o-gs/dji-firmware-tools/tree/195692263c2684cf1ddc4995f2736be6c0fb135e)
- 当前公共研究入口：[DJI Fly 官方下载页](https://www.dji.com/downloads/djiapp/dji-fly)
- 证据标签和脱敏规则：[AGENTS.md](../AGENTS.md)
- 失败路径应同步登记于 `docs/09_NEGATIVE_RESULTS.md`；未验证解释应只登记于 `docs/10_HYPOTHESES_AND_UNKNOWNS.md`。

本仓库只保留上表身份和独立文字结论。厂商样本、提取分区、共享库、反编译/反汇编正文、Assistant secret、临时修改件和校验失败输出不得提交。

## 11. 本轮固件获取与 RC 侧解密（C-316--C-322）

### 11.1 获取

`OBSERVED`：2026-10-16 通过官方 DJI Assistant 元数据/CDN 路径（`mydjiflight.dji.com/getfile/firmware`，一次 302 到
`terra-2-g-a.djicdn.com`）取得 6 份当前同版本模块。请求材料在内存中由本机合法安装的 Assistant dylib 重建，不打印不落盘。
逐份匹配官方 size/MD5，并独立复算 SHA-256 与既有工件登记一致（C-316）：

| 对象 | 版本 | 模块 | 大小 | SHA-256 | 既有 ID |
| --- | --- | --- | ---: | --- | --- |
| RC 2 Android OTA | `10.00.0700`（≡ UI `07.00.0100`） | `0205` | `985,959,104` | `f707cf3d…b528cf49ce` | A-004 |
| RC 2 flyapp | `10.00.0700` | `0200` | `454,223,680` | `d8a8fe5b418ee6461f6971d9dfad77bc4491d15160d47d5cf8f7481dc7113949` | A-005 |
| Mini 5 Pro 主系统 | `01.00.0600` | `0802` | `679,368,672` | `c36bcbd1…b2c560386` | — |
| Mini 5 Pro GNSS | `01.00.0600` | `2603` | `436,000` | `4a573ab9…36410775f274` | — |
| 通信 dongle（两版同） | `01.00.0700` | `0806` | `12,251,264` | `75bc1b74…12d1dfbc` | — |

`STATIC`：先前已存在的 RC331 `07.00.0100` 全量聚合体（A-029，`1,446,604,800` B，`296cfa63…b0c237ab1ae3`）来自
第三方 archive，本轮 clone 进同一棵树并复核哈希一致（C-316）；它**不是**本次官方获取。

`STATIC`：`07.00.0100` 的操作界面版本对应 product_version `10.00.0700`，映射依据是既有的 A-004/A-005/A-029 登记串，
不凭旧线程或字面猜测。

### 11.2 RC331：0205 可读，0200 内层仍受保护

`STATIC`：`wa150` 的 IMaH header 在 `header_version=2` 下仍使用 PKCS1-v1.5 签名，而 pinned 工具对 `pkgformat>=2018`
默认 PSS，故既存公开 PRAK 全部验签失败（C-321）。给本地工具副本加一条 PKCS1 回退后：

- RC331 `0205` **无 force 完整解密**：header 验签、encrypted-data checksum、decrypted plaintext checksum 三层全过（C-317）。
- 明文是 Android 11 A/B OTA（`CrAU`、`payload.bin`、`pre-device rc331`、post-build `V00.01.14.99`）；dump 出 29 个分区。
- 重新提取的两份 exact target 工件与登记逐字节一致：`adbd`（A-030，`/apex/com.android.adbd/bin/adbd`）与
  `dpad_fuli.apk`（A-031，`/vendor/app/dpad_fuli/`）（C-318）。
- C-319 仅记录所检查 RC331 外层 header 的空 `enc_key`；不代表嵌套内容已经解密。C-454 确认 A-005/0200
  的外层 payload 内还有 TBIE/FLYA 容器，内层密文从原文件 offset 960 开始，尚未得到明文。

`RETRACTED`：C-322 原称“RC331 全部明文、仅飞机侧受阻”，把外层与内层混为一谈。0205 平台样本可用于静态研究，
0200 的受保护内层仍未解开；不能把这两者或 TBIE 与 WA150 STUE 视作同一密钥边界。

### 11.3 WA150：STUE 卡点（阴性）

`NEGATIVE`：三份 WA150 模块 `enc_key=STUE`；pinned 公开 corpus 及其上游 fork 都没有 `STUE` 条目（C-320）。
以全部 16 字节公开 key 的派生变体（raw/SHA256/MD5/AES-ECB-unwrap）×3 mode（CTR/CBC/ECB）×3 IV 来源 ×v1/v2 语义
做 brute，对 `2603` 与 `0802` 的 plaintext checksum **零命中**。因此主体抽出来仍是密文（A-065）。

`NEGATIVE`：`0802` 的 `auth_alg=0x40003`、384-byte 3072-bit 签名，唯一公开 3072-bit PRAK 在 PSS/PKCS1、
SHA256/384/512、salt 0/32/48/64 及 reserved/alg 清零变体下均失败（C-321）。加密走 STUE、不走 PRAK，故验签失败
不影响 payload 抽取，但也说明公开 auth corpus 落后于本模块。

`UNKNOWN`：STUE key 是否可通过 whitebox（TEE/引导链内、非明文存放）或后续公开释放取得；飞行器升级环节在何处
解密。RC Android 侧、Assistant 应用、DJI Fly native 库均未发现可用的 `STUE` 常量或字符串。

### 11.4 边界

以上全部是 `STATIC`/离线派生。签名只对 RC 侧的 exact 模块成立，且不是 live mounted 事实，也不构成刷写准入。
第 8 节门禁不变；`0802` 明文仍未得，RID 因果仍未建立。

### 11.5 内嵌 key 搜索（C-323/C-324）

`OBSERVED`：额外取回最小模块 `1200`（`67,744` B，官方 MD5 `8fda0e65105ec628beee13108d175f60`）作廉价
STUE brute oracle（C-323）。取得方式是在同一官方 API 路径上手动注入 LockedTarget，工具编译锁不变。

`NEGATIVE`：官方 Assistant 六个 dylib 各内嵌四个明文 2048-bit PRAK RSA 结构（其中两个与公开
PRAK-2017-12/-08 逐字节一致），说明 Assistant 本地做 IMaH 解析/验签，但**没有 3072-bit PRAK，也没有明文
16 字节 enc/STUE 常量**。进一步对 Uav dylib 全量、libsdk_jni 非执行段、libuav_keys.so 全量 brute，零命中（C-324）。

限定：只覆盖明文内嵌常量；白盒/混淆存储、运行时派生、TEE/引导链提取仍未被否定。简单 brute 到此告一段落，
下一步是 whitebox 或公开释放。

### 11.6 白盒 AES 原语与 STUE 探针（C-325/C-326）

`OBSERVED`：六个 Assistant 服务 dylib 各内嵌一套白盒 AES-128（`t_box_enc`/`t_box_dec`，表字节六份逐字节一致，
即一个全局 key），由 `WAES_encrypt`/`WAES_decrypt` 使用。搭镜像框架树 + ad-hoc 重签解释器，在 Rosetta 下 ctypes
加载 x86_64 dylib，encrypt/decrypt roundtrip 通过；已固化为 [wb_aes_bridge.py](../host-tools/firmware-acquisition/wb_aes_bridge.py)
（进程内 `load()` + 三测）。这给了 STUE 一个可调用的候选原语。

`RETRACTED`：C-326 的“公开探针完成方向/模式枚举且零命中”不能由审计提交复现（C-446）。真实 2603 逻辑长度为
435,382，旧 NumPy checksum 在首个裁剪候选上报错；派生 `ck` 未用于候选明文，ECB 又漏掉 encrypt 方向。
加密 checksum MATCH 与白盒 primitive roundtrip 的观察保留，但不证明枚举完整或“只剩 key/mode”。
仓外是否另有修订脚本未被本次审计判定。

### 11.7 白盒表分解与候选 key（C-327/C-328）

`OBSERVED`：逐表对 `t_box_dec` 做仿射判定，每表在 `InvSbox(x ^ k_i)` 上仿射（系数恒为1 + 一个常量编码），
每表唯一解出一个 `k`，拼出候选 key `5ac8ed5cf0fa5e5d77b5c89599bb87d5`；固化为
[wb_aes_key_recover.py](../host-tools/firmware-acquisition/wb_aes_key_recover.py)（A-069），可确定性复现。
该模型同时确认白盒内部只是 `InvSubBytes + AddRoundKey + 常量编码`，MixColumns 在 `shift_mix` 内。

`NEGATIVE`：常量编码使普通 AES 不等于白盒，故该 key 目前只到 HYPOTHESIS。把 key 走普通 AES（多 mode/IV）
以及把 WAES 扩到 OFB/CFB 均零命中；手搭仿真也未与 WAES 逐字节相等（C-328、N-63）。下一步是抵消常量编码并
对齐轮结构，或先证明 `shift_mix` 等价形态。

### 11.8 WAES 作用域修正与固件路径 key 字面量（C-329/C-330）

`OBSERVED`：`WAES_encrypt`/`WAES_decrypt` 的**唯一**调用者是 `GetPublicValue`/`GetPrivateValue`。因此 11.7 恢复的
白盒 key 属于该 QByteArray 值加密，**不必然是 IMaH STUE 的 key**。固件类（`DJIFirmwareUpgrader` /
`DJIUpgradeMgr` 等）改调 `aesDecode2`/`aesEncode2`/`aesDecode`，key 是 QString；在其中三个调用点附近出现唯一一个
16 字节 key 型字面量 `1ff6b8ca503b47ad8d04d8686dcb13a0`。

`NEGATIVE`：该字面量当 raw key 及多种派生、多种 mode/IV 试，明文 checksum 零命中（C-330、N-64）。`aesDecode`
的内层 framing 未反汇编，故未否定。

下一步：反汇编 `aesDecode2` 本体，确认它是否 base64/固定 IV/自定义 KDF，再把字面量放回正确位置。

### 11.9 CRijndael 路径与 IV 解引用更正（C-331/C-332/C-443）

`RETRACTED`：C-331 将 `sm_chain0` 指针变量及相邻存储误记为 16 字节 IV，并把 NFZ helper 直接称为固件解密路径。
精确样本中，`sm_chain0` 位于 `0x93a0e8`，存放指向 `0x8b89a0` 的指针；`MakeKey` 使用指针所指的 16 字节全零数据。
AES-256-CBC helper 的存在和 `aesDecode2Ex` 可调用这一事实保留，不构成 WA150 STUE 路径归属证明。

`NEGATIVE`：C-332/N-65 的真实 helper 调用与候选 key 未命中记录保留。直接调用厂商函数会使用真实 IV，不能把文档的
解引用错误推广为每次 native 调用都使用错误 IV。它只否定当时所试输入组合，不能推出“只剩模块 key 未知”。

### 11.10 NfzPack 输入与 key 的历史误判（C-333/C-334/C-444）

`RETRACTED`：C-333 将输入 `QByteArray` 当成调用方供应的 key。该 callback 的输入数据与独立常量 `XsBuffer` key
构造链应分开；已恢复的 NFZ key 不依赖模块 id、文件名或设备地址。

`NEGATIVE`：C-334/N-66 所记候选 key 与 AES/XOR 两序未命中，仅保留为历史试算；这些结果不能支持已撤回的 key 来源。

### 11.11 ostringstream 是摘要日志（C-335/C-336/C-444）

`RETRACTED`：C-335 的“现场 hex 派生 key”结论错误。输入摘要进入解码前 MD5 日志，输出摘要进入解码后日志；
两者都没有成为该 callback 的 AES key。key 来自独立的常量容器变换链。

`NEGATIVE`：C-336/N-67 的大小写 hex、前缀 hex/raw 尝试保留为历史负结果，不再称为已确认 KDF 的格式枚举。

### 11.12 MD5 KDF 结论撤回（C-337/C-338/C-339/C-444）

`RETRACTED`：C-337 将 `MD5(data)` 的日志格式化链误认成 AES key 派生；该错误也影响原检查点与旧 B-23 收敛结论。
C-338 的 pad 寻址观察是另一件事，不能为 MD5 KDF 提供支持。

`NEGATIVE`：C-339/N-68 的 MD5 格式变体未命中记录保留；不再据此寻找日志前缀、大小写或补零细节。

### 11.13 pad 周期与旋转的范围（C-340/C-341/C-342）

`STATIC`：C-340 记录的周期 17 pad 用于 NFZ 常量缓冲变换。C-341 的跨字节配对猜测已由 C-343 的逐字节解释替代。
`NEGATIVE`：C-342/N-69 的 MD5/旋转组合未命中只覆盖历史猜测；MD5 key 模型已由 C-444 撤回。

### 11.14 逐字节变换不建立 STUE 归属（C-343/C-344）

`STATIC`：C-343 的 `ror8(b, i&7)` 与周期 17 pad 描述 NFZ 缓冲的逐字节变换。
`NEGATIVE`：C-344/N-70 的历史 MD5/输入变体未命中；它不能证明 WA150 chunk 经过这个 callback。

### 11.15 key 字符串与 MD5 日志分开（C-345/C-346/C-444）

`STATIC`：C-345 后来已识别 MD5 字符串只用于日志，AES key 来自变换输出。现进一步确认该输出固定为 32 字节、
全部可打印且没有内嵌 NUL；C-345 边界中的密文来源猜测与数据相关截断已更正。

`NEGATIVE`：C-346/N-71 把密文变换后截断作 key 的尝试保留为历史负结果；它不代表真实 NFZ key 构造。

### 11.16 常量容器的正确读取（C-347/C-348/C-442）

`STATIC`：key 的来源是独立构造的 `XsBuffer` 数据区，输入密文另作 AES data。
构造写入 33 个已初始化字节，其中 32 字节参与变换；本轮只公开长度、性质与哈希，不公开常量 key 或厂商代码。
`NEGATIVE`：C-348/N-72 使用不完整 seed 的试算保留，不再把提取顺序当作待扫描的自由变量。

### 11.17 旧常量列表解释撤回（C-349/C-350）

`RETRACTED`：C-349 把分配大小、追加字节和虚调用混成固定块/负 map key 模型；它未正确恢复容器内容。
正确结果见 C-442/C-444。C-350/N-73 的列表变体未命中保留为历史记录，不证明还缺随机字节。

### 11.18 调用分工与旧排序试算（C-351/C-352）

`STATIC`：C-352 的数据与 key 分工可保留：密文是输入数据，key 来自独立变换后的常量缓冲。
`NEGATIVE`：C-351/N-74 的负 key 排序尝试依赖错误容器模型，不能再作为恢复 key 的方向。

### 11.19 NfzPack 与普通固件路径的区别（C-353/C-354）

`STATIC`：C-353 识别的是远程 NFZ pack 的 URL 获取/回调路径。
`NEGATIVE`：C-354/N-75 的普通 `UpgradeFirmPack` 函数范围内未发现直接 crypto 调用，是有界静态搜索；
它既不证明 NFZ 路径适用，也不排除其他 helper 或设备侧处理。

### 11.20 ProcessUpgradeFirmPack 的 type 分派（C-355/C-356/C-445）

`RETRACTED`：C-355 的“普通固件必经 NFZ，本地 chunk 可作代理”结论错误。
`ProcessUpgradeFirmPack` 按 type 分派：case 0 为 `UpgradeFirmPack`，case 1 为 `UpgradeNfzPack`，
case 8 为 `UpgradeFirmPackFromLocalFile`。存在 NFZ 分支不证明 WA150 IMaH STUE chunk 进入它。
C-356/N-76 的 NFZ 函数范围内解码函数未命中，也不能把这条路径推广到普通固件。

### 11.21 vtable address point 更正（C-357/C-358/C-442）

`RETRACTED`：C-357 漏掉 Itanium C++ ABI vtable 头部 16 字节。表符号为 `0x8fba40`，对象实际 vptr 为 `0x8fba50`。
相对实际 vptr，`+0x20` 是 append，`+0x28` 是字符指针转换，`+0x30` 是 get，`+0x38` 是 size。
get 返回 `this+8` 保存的数据指针，循环没有把对象本身的 vptr/data/cap/len 当作 seed。

`NEGATIVE`：C-358/N-77 的列表旋转未命中保留；它不能推出需要加入结构体指针。

### 11.22 原地变换发生在数据区（C-359/C-360）

`STATIC`：C-360 的逐索引原地变换仍成立，索引对象应明确为 `XsBuffer` 的数据区。
`NEGATIVE`：C-359/N-78 的公式变体未命中保留，但“下一步加入对象字段”的旧结论撤回。

### 11.23 运行时指针 key 模型撤回（C-361/C-362/C-442）

`RETRACTED`：C-361 的字符指针转换尾调 append、返回对象本身的解释来自错位 vtable。
真实 get 返回独立数据区；key 不含运行时堆指针或栈地址。
`NEGATIVE`：C-362/N-79 的合成指针试算保留，不能作为真实 key 复杂性或地址依赖的证据。

### 11.24 对象布局与变换输入不能混同（C-363/C-364）

`STATIC`：C-363 的 32 字节对象布局仍为 vptr/data/capacity/length；撤回的是“这个对象范围就是变换输入”。
`NEGATIVE`：C-364/N-80 的对象仿造与指针扫描只测试了错误模型，不再指向更多 cap/len 或地址枚举。

### 11.25 指针扫描与栈尾推论分开（C-365）

`NEGATIVE`：C-365/N-81 所记 6,144 组指针组合未命中保留为历史运行记录，本轮没有重新执行。
`RETRACTED`：把循环读入解释为 32 字节对象再加 12 字节未初始化栈尾，依赖同一 ABI 错误，不能作为剩余解密问题。

### 11.26 attrib 位与 raw payload checksum（C-366/C-367）

`STATIC`：四份本地 WA150 模块（0802/1200/2603/0806）均记录 header_version 2、`enc_key=STUE`、chunk attrib 0。
`NEGATIVE`：历史 raw payload checksum 没有匹配各自 plain_cksum（C-367/N-82），不支持直接把 attrib 0 读作已解密明文。
该结果不定位 key、cipher 路径或其他 attrib 位的含义。

### 11.27 strlen、栈尾和每轮 init 猜测撤回（C-368/C-369/C-370/C-442）

`RETRACTED`：C-369 的 vtable NUL 截断与 MakeKey 读入对象尾部结论错误；真实变换输出有 32 个可打印字节且无内嵌 NUL。
“每轮 init 清零”也来自错位虚槽，不是当前未知项。
`NEGATIVE`：C-368/N-83 的 tail 变体和 C-370/N-84 的 120,000 次合成尝试仅保留为历史负结果；
不再支持随机指针/栈尾模型，本轮不重复这些扫描。

### 11.28 遥控器侧 RID 侦察（C-371/C-372）

`OBSERVED`：rc331 分区裸扫里，`rid_enable`/`RID_ENABLE` 其实是视频编码属性 `layer_wise_rc_enable`；`RemoteId` 是
AOSP/Chromium 类 —— 都不是 Remote ID。`DJI_FLY.apk` 仅以路径出现（附近4MB 无 `PK` 魔数），故 apk 本体在 /data/app、
不在 OTA。`NEGATIVE`：分区裸扫不足以拿开关（N-85）。

正解：改用仓外的 DJI Fly dump（同一 App 版本）找 RID 开关/参数，rc331 分区只作 native/config 佐证。

### 11.28b 与既有记载的关系（C-407）

先前的仓库记载已在**名称/键层**覆盖 RID：`EIDSwitch` 特性（C-133 `RidCaptureV1` 清单）、`EU_CE_enable_c0_rid_0`
映射（C-071 STATIC → `IsEuCeEnableC0Rid`）、`CccBroadcastSignalQuality`（C-077），并有针对性的负结果 C-072/C-078
与 setter 搜索负结果 C-109。

本轮补充了 handler 地址、注册和传输线索；但不能推翻 C-109 的 global RF Boolean 搜索边界。France EID setter 早已由 RID-003 单独记录。故下述 C-373 之后的内容应读作既有 C-071/C-133 之下的展开，而非首次发现。

### 11.29 遥控器侧：DJI Fly 的 RID 面（C-373/C-374/C-375）

`OBSERVED`：DJI Fly `libsdk_jni.so` 的字符串面直接给出 RID 专用名 —— `IsEuCeEnableC0Rid`、`EIDSwitch`、
`RidWorkingStatusPush`、`CccBroadcastSignalQuality`、`OIDIdentifier`、`ComplianceSerialNumber`、`EU_CE_enable_c0_rid_0`，
以及 `RIDRegistedInfoReq`/`ActionRIDRegistedInfo` 与 `rid_len=`/`rid_data_packet` 日志文本。前人工具已列同一批名。

`OBSERVED`：直接 ADRP+ADD 引用计数已量出（EIDSwitch68、ComplianceSerialNumber64、CccBroadcastSignalQuality51、
OIDIdentifier37、IsEuCeEnableC0Rid18、RidWorkingStatusPush2、EU_CE_enable_c0_rid_0 0）。聚焦点取
`IsEuCeEnableC0Rid` 与 `RidWorkingStatusPush`。

`NEGATIVE`：`EU_CE_enable_c0_rid_0` 无直接 xref（C-375、N-86），属间接到达。

### 11.30 本机反编译工具链（C-376）

`OBSERVED`：Ghidra 12.1.2 位于 `/opt/homebrew/Cellar/ghidra/12.1.2`，运行根在 `libexec/`（`support/analyzeHeadless` 在 `libexec/support`），openjdk@21 位于
`/opt/homebrew/opt/openjdk@21`。以 `JAVA_HOME=... GHIDRA_INSTALL_DIR=...libexec libexec/support/analyzeHeadless ...` 可跑 headless。
注意 `~/Library/ghidra/ghidra_12.1.2_PUBLIC` 只是用户配置目录（log/osgi/preferences），不是安装本体。

### 11.31 遥控器侧 France EID 处理器（C-377/C-378/C-379）

`OBSERVED`：Ghidra headless 定位到France EID 访问器 —— 自由处理器 `EIDSwitchGet`（0x04e12d44）与
`EIDSwitchSet`（0x04e12f80），签名 (KeyHandlers*, Characteristics const&, shared_ptr<UavValue>, callback)；Set 会
`__dynamic_cast` 校验类型、不匹配返回 -6。

`OBSERVED`：两者及其 `UAV77FlightControllerAbstraction::GetEIDSwitch/SetEIDSwitch` 包装（0x02d9ad3c / 0x02d9afa0）
都构造 `uav_cmd_base_req`，置 local_76=0x77、local_74=3、local_71=3 再 local_71=0x12、local_7c=4，并调用
`uav_cmd_req_header::SetReceiverIndex`；Get 置 local_48=2、get/set 标志0，Set 由值头取 local_48、标志1。

`OBSERVED`：`OIDIdentifierGet/Set`（0x04eabadc / 0x04eac2fc）为同级处理器，`ComplianceSerialNumberInit` 在 0x02e36740，
这些是不同业务面的 SDK 处理器，不能合并成全球 RID 控制面（C-379/C-448）。

这些静态线索尚未建立设备路由、读回、恢复或 RF 对应关系；目录工具只生成离线 hex。

### 11.32 eid_switch 请求语义解码（C-380/C-381/C-382）

`OBSERVED`：反编译出的模板实例直接给出常量 —— `uav_cmd_base_req<(unsigned_char)1,(unsigned_char)3,(unsigned_char)119,
uav_fc_handle_eid_switch, uav_fc_eid_switch_status>`，包装层调 `SendGetPack<uav::core::eid_switch_pack>` /
`SendSetPack<...>`。即请求 = cmd119、sub3、attr0x12，回复标签 `uav_fc_eid_switch_status`，载荷类型为
`uav::core::eid_switch_pack`（含 `RspType`）。

`OBSERVED`：EIDSwitchSet 的载荷是**单个启用字节** —— 它对 `shared_ptr<UavValue>` 做 `__dynamic_cast` 后读
`*(undefined1 *)(lVar6 + 8)`（C-381）。Get 侧则硬编码 local_48=2。

值 0 属于 France EID 的候选 SET 语义；它不是 FAA/global RID 关闭命令（RID-003、C-448）。

### 11.33 base_req 是内存对象，不是 wire header（C-383/C-384/C-468）

`STATIC`：C-383 的 constructor 写入描述进程内 request 对象及其 Buffer，不能序列化照抄为 32 B wire header。
C-384 的外部 helper 缺口已在 A-086 闭合：SetReceiverIndex 把 index byte 写入 req+0x19，并对 req+0x0a OR 2。
free EID/position templates 是否覆盖 receiver 取决于 single/multiple HostID descriptor 条件，见 C-468。

### 11.34 receiver 来源与发送出口更正（C-385/C-386/C-468）

`RETRACTED`：C-385 的 Characteristics+0x30=receiver 推论错误；该字段在所检查函数中复制进 callback capture。
只有 multiple-host list 为空且 single descriptor 非空时，descriptor[0] 写 req+7，descriptor[1] 调 SetReceiverIndex。

`STATIC`：C-386 的 virtual+0x128 保留，但仅限 BaseAbstraction EID Set 重载；free KeyHandlers EID 和 app-position
SendSetPack 使用 first-pointee virtual+0x10。六个原始 prefix/helper 受控 case 通过，不等于完整 send 或设备路径已执行。

### 11.35 传输名称不能合并不同重载（C-387）

C-387 的 SendPack/SendData 名称清单保留为 `STATIC` 库存；不能把所有 SendSetPack 自动接成同一个 virtual+0x128 链。
C-468 已分别记录 free KeyHandlers 与 BaseAbstraction EID 重载，实际 owner、runtime HostID、完整 callback/transport 仍未验证。

### 11.36 EIDSwitch 注册与连接前置（C-390）

`OBSERVED`：`FUN_032ba30c` 构造名为 `"EIDSwitch"` 的 `CharacteristicsElement`，装入 `PTR_EIDSwitchGet_0532e518` /
`PTR_EIDSwitchSet_0532e520` 的 get/set 函数对，再调 `uav::sdk::key::BaseAbs::InsertCharacteristics(param_1,
"EIDSwitch", element)`。

即：App 是**按 SDK key 名**访问该开关（不是直接发 opcode）；characteristics 与 receiver 管线由这条 key 路径填充。
key 注册不等于当前 product/session 准入；receiver、重试及 product-139 的精确边界以 RID-003 为准。

### 11.37 rc331 侧 native 佐证（C-392/C-393）

`OBSERVED`：vendor.img 的名称池列出 `dji.go.v4`、`dji.go.v5`、`dji.prof.mg2`、`dji_logs`、`dji_v1_protocol`、`djilink`；
system.img 日志串显示 `hdvt_lte: inform djilink ...` / `failed to inform djilink`，并有 `dji_link` 的 stream_conf 条目 ——
即 RC 上存在 **native 链路守护进程**，App 的协议路径有其对端。

`OBSERVED`：system.img 的 launcher JSON 里有 `start dji_link` 与 `pkill -9 dji.go.v5`（在 download pretender 下），
说明开机先起 djilink、再拉起 DJI Fly（C-393）。

这些镜像中的名称和配置支持链路组件存在，不证明当前实例的端到端路由可用。

### 11.38 dji_link 本地通道与路由表（C-394/C-395）

`OBSERVED`：vendor.img 内嵌 `dji_link_services` → `mb_route_table` JSON。其中 `"dji_link"` 下的 `"00"` 项 status1、
target `whoami`、channel **`local`**、protocol **`logic`**，并有 `local.direct_host=whoami`；同级还有 `dummy`（bulk/UEvent）
与 `"10"`（camera, bulk, protocol v1）。表头 host 为 `mobile`、index5。

`OBSERVED`：dji_link 串包含 `dji_link_init_localsocket_to_app`、`dji_link_send_stream_via_localsocket`，日志
`app socket thread start ---- localsock_fd = %d, accept_fd = %d` —— 即 djilink **监听并 accept 来自 App 的本地 socket**。

配置支持 App/local/logic 与 bulk 路由的静态线索；`SendData` 到某一 WA150 请求的完整运行期路径尚未验证。

### 11.39 unix socket 命名与 whoami 语义（C-396）

`OBSERVED`：dji_link 串含 `dji_link unix_socket_listen create socket = %s` —— 监听 socket 名由配置/源码提供，不是写死字面量。
本地路由的 `direct_host` 为 `whoami`，同树源文件为 `hardware/dji/service/dji_link/src/dji_whoami.c`（即"本机自身"）；
`vt_gnd` 是另一虚拟地面主机、用于其它本地路由。

将 `whoami` 当作 socket 字面名仍只是 H-37，未取得实际地址，不能作为连接或发送依据。

### 11.40 EU/CE 区域法规族与扫描器修正（C-398/C-399）

`OBSERVED`：EU/CE 区域族含 `EU_CE_enable_c0_rid_0`、`EU_CE_Reg_120Height_Enable_0`、`EU_CE_Reg_Level_0`。
扩展扫描器到 ADRP+LDR（imm）形式后，`EU_CE_enable_c0_rid_0` 命中 **50 处**、`EU_CE_Reg_Level_0` 2 处；这些站点都在
构造键值结构（伴随 movk 常量）。

`RETRACTED`：C-375 的"0 xref → 间接到达"读法收回（C-399、N-87）—— 真相是活 key，只是重定位形态不同。
该静态键名不能覆盖 RID-009 的历史正对照负结果：所测 direct USB FLYC 表面未暴露该参数。

### 11.41 EUCeCxV1 注册类与区域 RID 键（C-400/C-401）

`OBSERVED`：`uav::sdk::key::EUCeCxV1::CreateCharacteristics`（0x04b20670）与 `BindKey`（0x04b25038）经
`FunImplBase::InsertCharacteristics` 插入一整套 EU/CE 法规键：`IsSupportEUCeCx`、`CeInfoEnable`、
`CeRegulatoryRestrictionEnable`、`IsCEC0/1/2Support`、`SyncC0HeightLimitState`、`DroneC0HeightLimitState`、
`HeightLimitRange`、`HeightLimit`、`StaticDBVersion` 等；BindKey 另用 `EU_CE_Reg_120Height_Enable_0` 字面量。

`OBSERVED`：`EU_CE_enable_c0_rid_0` 的50 处站点散布在大量不同函数中、均构造键值结构 —— 属**已注册的绑定键**，
而非一次性局部。这支持静态注册/绑定线索，不证明它与 France EID 构成两个可用 RID 开关（C-401/C-448）。

`RETRACTED`：不能据此建议以该键替代 EIDSwitch。RID-009/C-227--C-229 已记录所测 direct USB 的参数缺失与成功正对照；当前仍没有可用 RID 控制路径（C-448）。

### 11.42 旧 constructor 镜像自检的边界（C-402/C-403/C-469）

`OBSERVED`：C-402 记录旧 EID 自检通过；它只镜像进程内 constructor 写入，不能证明 wire frame 或发送能力。
C-403 曾修正其 'IW' 内存偏移。`RETRACTED`：这些自检支持有效 wire header 的解释撤回；C-469 删除整个伪对象头，
改用 payload-only schema tests。旧通过记录不追认当前 codec 或设备行为。

### 11.43 OID 自检与 EU_CE 无命名 handler（C-404/C-405）

`OBSERVED`：C-404 的旧对象头/0x70 cap 自检通过记录保留；它既不是产品139的正确 cap 证明，也不是 wire 验证。
C-123/C-389/C-411 已分清 18 B payload 与 8 B copy，C-469 删除 fake header；GET 零 tail 仍只是本地确定性选择。

`NEGATIVE`：C-405 的 EU_CE 命名 handler 搜索范围不变；C-469 不把该参数或 France EID 变成可用 global RID switch。

### 11.44 位置 setter 与 Ccc 未命名 handler（C-412/C-413）

`OBSERVED`：`UploadMobileDevicePositionSet`（0x04e23260）是 AES 加密的 set：模板 `<1,17,67,uav_adsb_set_app_update_pos_enc_req,...>`
（cmd 0x43 / sub 0x11，与 docs/05 的 `app_update_pos_enc` 一致），经 `SendSetPack<app_geography_info_upload_pack>`；密钥由
`uav::whitebox::GetWhiteBoxKeyChainString(local_c8, 0x37)` 派生，随后 `AES256Encrypt`(0x100) + `HmacEncode`。

`NEGATIVE`：`CccBroadcastSignalQuality` 无专属 handler 符号（C-413、N-90），其字面量落在通用 FC 注册与静态字符串表中，
线宽仍不闭合。

### 11.45 旧位置布局解释已更正（C-414/C-415/C-464）

`RETRACTED`：C-414 将第三个 double 当作 int、把 AES 参数 `0x100` 当作输出长度，并猜测 plaintext prefix 与更长 ciphertext 字段。
C-464 的精确 JNI bytes 确认：两个 u32 的低字节、三个 double→整数及 timestamp 序列化成 22 B；`0x100` 是 256 key bits。
成功 payload 为 LE32(80)+ciphertext32+原始 constant IV16+HMAC32，共 84 B，没有额外内部 request header。

C-415 的同一 key 字符串供 AES/HMAC 使用的事实保留。此处不解释坐标单位，也不声称完整 handler、SendSetPack、transport 或 RF 执行。

### 11.46 白盒库清单的旧负结论撤回（C-416/C-417/C-458）

原库清单未恢复 `GetWhiteBoxKeyChainString` 的定义；C-417 的“208 库均无 provider”结论已撤回。
C-458 证明 `libsdk_base.so` 有真实动态符号定义，不能把 section/nm 缺失推广为库中无实现。

### 11.47 sectionless ELF 仍有完整动态符号（C-418/C-419/C-458）

`RETRACTED`：C-418/C-419 将名字解释为 stripped 库中的嵌入字符串表，证据不足。
精确 ELF 的 PT_DYNAMIC 文件偏移指向短表，但虚拟地址经 PT_LOAD 映射后给出完整动态表及 14,944 个符号。
provider 的事实保留；动态符号和函数已定位，不再以“需要寻找白盒 body”作为待办。

### 11.48 表项长度是密文长度（C-420/C-421/C-422/C-459）

`STATIC`：C-420 的三字段表结构与 0x37 槽定位保留，原始指针需重定位。
`RETRACTED`：C-421 将 `0x30` 当作返回 key 长度；它实际是 stored ciphertext 长度 48 B。
完整 Get(0x37) 经固定 WAES CBC 解封和 padding 去除后返回 32 B，见 C-459。

### 11.49 存储块不是可直接使用的位置 key（C-423/C-424/C-425/C-459）

`STATIC`：C-423 的存储位置观察保留，第一指针是 48 B 密文，第三指针的前 16 B 是解封 IV。
C-424 的分段地址映射边界仍成立；不能用单一 base 相减替代 PT_LOAD 映射。

`OBSERVED`：C-459 的完整 Get 模拟返回 32 B，与密文前 32 B 不同，且重封装逐字节还原 stored ciphertext。
`RETRACTED`：C-425/A-078 v2 直接使用 `ciphertext[:32]` 的 key 选择已证伪。C-464/C-465 后续恢复 22 B 输入/84 B payload，
并将 Python 修为 A-078 v3 离线 payload encoder；旧模型不追认。完整 handler、最终传输 frame 和 RF 仍未验证。

### 11.50 ComplianceSerialNumber 是派生 listener（C-428/C-429）

`OBSERVED`：`ComplianceSerialNumberInit` 只做注册 —— 组装字面量 `SerialNumber`、经 handler 读取，再堆分配 0x48 lambda 捕获
KeyHandlers+Characteristics 并交回调派发。即合规值是对普通 SN 的**派生 listener**，没有自己的 opcode。

`NEGATIVE`：无 `ComplianceSerialNumberGet/Set` 符号（C-429、N-95）。故 UAS ID 不直接可写；改它等于改底层 SerialNumber。
这也解释了 docs/05 的"未找到 SET"。

### 11.51 SerialNumber 是 Get-only 身份键（C-430/C-431）

`OBSERVED`：`SerialNumber` 字面量（0x11d6059）有164 处引用；跨抽象（ActivateMgr/GlassAbstraction/CameraAbstraction/
RemoteControllerAbstraction/OPR38/56RCAbstraction 等）的具名访问器清一色 `GetSerialNumber` / `InternalGetSerialNumber`。

`NEGATIVE`：无任何 `SetSerialNumber`（C-431、N-96）。故序列号是身份而非可写字段，派生的 ComplianceSerialNumber
（C-428、C-128）默认也不可写。UAS ID 若要改，除非存在上下文级 set。

### 11.52 AirSense/ADS-B 与高度 opcode（C-432/C-433/C-434）

在 pack 模板标签层面另找到三个此前未记的 opcode：

- `uav_adsb_get_adsb_on_off_req/rsp` → cmd **12 (0x0C)** / sub17（ctor 0x02d6f14c）—— AirSense/ADS-B traffic receive 查询
- `uav_adsb_set_set_adsb_agent_switch_req/rsp` → cmd **55 (0x37)** / sub17（ctor 0x02da5140）—— AirSense/ADS-B 配置 SET，非 RID 总开关
- `uav_adsb_get_drone_dynamic_max_height_req/rsp` → cmd **80 (0x50)** / sub17（ctor 0x02cb9980）—— 动态最大高度，独立于位置 set

这些 opcode 属不同功能面；RID-002B 已将 `0x11/0x0C` 与 `0x11/0x37` 排除为 global RID 配置（C-135/C-448）。

### 11.53 动态最大高度 ctor 与匿名 handler（C-436/C-437）

`OBSERVED`：反编译 `uav_adsb_get_drone_dynamic_max_height` ctor（0x02cb9980）—— 标准形状：`*this=0x2501101`（字节
01 11 50 02）、+1 qword、`0x57490000` 魔数、500 超时、0x10/0x18 置零，无额外局部常量。即纯 GET、空载荷。

`NEGATIVE`：无 Get/Set 命名包装 handler（C-437、N-97），调用点匿名。

### 11.54 ccc 的归属与规模（C-438）

`OBSERVED`：把 EU_CE 用过的 ADRP+LDR 修正同样施于 ccc 字面量 —— `ccc_broadcast_signal_quality_0` 命中133 处、
`CccBroadcastSignalQuality` 29 处。其所在函数是大到巨型的 camera 注册 `FUN_03bfbfe8`，且经计算指针到达
（无 `s_` 符号出现）。

即 ccc 属 **camera 族语义**，非独立 RID 命名 handler（C-438、N-98）；线宽仍不闭合。与既有 C-077/C-078 一致。

### 11.55 RidWorkingStatusPush 载荷解析（C-439/C-440）

`OBSERVED`：`RidImportModule::OnRIDWorkingStatusPush`（0x02cec558）取 response 载荷 `param_1+0x28`，读 byte0 的 bit0/bit1/bit9
三标志（写入 +0x20/+0x21/+0x22）、byte1 的 bit0（+0x23）、+2 的 int 经 `GetAreaCodeStrByValue`、byte6 写 +0x40/+0x44，
再以名称 `RidWorkingStatusPush` 与 pack `adsb_push_rid_working_status_pack` 经 `UpdateParamValueProxy` 发布。

`RETRACTED`：C-440 把 push-only observer 提升为 EID/ADS-B SET 的可靠 applied readback。该关联未建立，也没有主动 GET builder；历史外部 Binder listener 曾在真实 RID RF 存在时零回调。push/cache/ACK 均不能替代当前接收时间与独立 RF 观察（C-448/C-449、RID-002/RID-011C）。

## 12. 修正后的 public-v2 试验与普通固件路径（C-450--C-453）

`OBSERVED`：独立单候选工具 [imah_v2_key_probe.py](../host-tools/firmware-acquisition/imah_v2_key_probe.py)（A-082）
与六项测试已完成；包含独立 OpenSSL 的混合加密/明文 chunk、gap、非零 padding 固定样例，整个目录 59/59 测试通过。
它只校验候选，不导出 key 或明文，不提供刷写/设备路径。以下进展未解开 STUE。

### 12.1 public IMaH-v2 模型与校验范围（C-450）

该实现依据 [pinned dji_imah_fwsig.py](https://github.com/o-gs/dji-firmware-tools/blob/195692263c2684cf1ddc4995f2736be6c0fb135e/dji_imah_fwsig.py)。模型用 16/24/32 字节 KEK 对 16 字节 scram 做 AES-ECB decrypt，
得到 16 字节 content key；也可直接输入 16 字节 content key。随后 AES-128-CTR 使用 12 字节零前缀与从 0 开始的
32-bit big-endian counter，跨加密 chunk 连续。加密 chunk 的 stored size 向上对齐 32 字节；`attrib&1` 为真或
`enc_key` 为空时按明文复制，不推进 counter，文件 gap 也不推进 counter。

checksum 为 little-endian uint32 模 2^32 求和，末尾不足四字节补零。plain checksum 覆盖解密后的完整 chunk padding；
加密 checksum 覆盖清零 checksum 字段的完整 header/chunk table 加完整 stored payload，取负，不包括 RSA signature。
工具先验证 stored payload SHA-256 和加密 checksum，再测试候选。以上是公开模型的实现语义，STUE 的适用性仍未知；
即使 checksum 命中，也还需要独立结构佐证和另行处理签名。

### 12.2 三个有来源的候选均未命中（C-451）

输入为 WA150 `01.00.0600/2603`，436,000 B，SHA-256
`4a573ab95316de69137deb71249ead09c23325a28acbf9ee305a36410775f274`。
header/signature/payload 分别为 224/384/435,392 B，逻辑 chunk 435,382 B；三次都通过 payload SHA-256 和加密 checksum。

| 候选解释 | 求得的 plain checksum | 期望 | 结果 |
| --- | --- | --- | --- |
| 恢复的 32 字节 NFZ 常量作为 v2 KEK | `0x5fb4802c` | `0xd2f782ff` | 不匹配 |
| WAES.decrypt(scram) 作为 content16 | `0x13169336` | `0xd2f782ff` | 不匹配 |
| WAES.encrypt(scram) 作为 content16 | `0x6bd174f9` | `0xd2f782ff` | 不匹配 |

`NEGATIVE` 仅覆盖这三个确定候选，不是任意 brute，也不否定所有 key 或整个模型。
C-445 的 NFZ key+零 IV 直接 CBC 试验、C-447 的十个 fixed-WAES 组合与本组三个 v2 试验分开登记。

### 12.3 Assistant method-4/register-upgrader 的静态数据流（C-452）

对象仍为 x86_64 `libDJIUavService.dylib`，SHA-256
`c55da41265f925f64c2d704deb68f65fcff44435c9681839cc8545cd07dd76a5`。本次只跟踪 method 4 所选的 register upgrader：

| 环节 | 已检查的静态行为 |
| --- | --- |
| 方法选择 | `SetUpgradeMethod` (`0x4c01c0`) 的 method 4 构造 `DJIFirmRegisterUpgrader`；`UpgradeFirmPack` (`0x4cff10`) 的对应分支经过 `0x4d0a40`、`0x5c72d0` |
| 下载 | `DownloadPack` (`0x5ae540`) 经 `GetProductFirmwareData` (`0x555fc0`)、`GetSingleFirmData` (`0x556690`)、`GetFirmwareFile` (`0x558730`)、`ApiGetfileFirmware` (`0x4660a0`) 到 `wGetBigFileUseCache` (`0x49db50`) |
| 缓存与校验 | progress (`0x49e880`) 把 readAll buffer 原样写 cache 并更新 MD5；finish (`0x49cee0`) 处理 redirect/callback。callback (`0x562b30`) 检查 size/MD5；single callback (`0x561d30`) 写 buffer 或 rename cache |
| 打包与发送 | `GenerateTarPack` (`0x59a130`) 经 `Tar::putFile` (`0x799e50`) 以 8,192 B 读取/写入同一缓冲并补 tar 的 512 B 对齐；`TransFirmDataByFtp` (`0x5afc70`) 将 QFile/MD5 交给 PutFile |

这些已检查的边复制/缓存/包装输入字节；输入若是密文，所观察到的这条路径不会在这些边把它变为明文。
未在这一范围恢复出 STUE decoder。该静态结果不覆盖整个 Assistant，不证明当前 WA150 在运行时选择 method 4，
也不定位下游解密 owner、设备 key 或 TEE。当前没有设备，未执行下载升级链。

### 12.4 有限公开源码检索（C-453）

上游仍为 `195692263c2684cf1ddc4995f2736be6c0fb135e`，没有 STUE 条目。本轮列出 517 个 fork 的元数据，
按 push 时间筛选 17 个默认分支并检查 8 个非默认分支；25 份 `dji_imah_fwsig.py` 都与固定上游逐字节相同，
SHA-256 `534680d1fb0ced5f6425b276fcd421456a45a513cf625d73566b2150c2ed6760`。
筛选条件是 push 时间晚于 2026-01-01，并排除三组已识别的上游同步时间；17 个默认分支并不全是实质 ahead。

`NEGATIVE`：这批源码没有新增 STUE key/mapping/实现。没有检查全部 517 个 fork 的源码、所有非默认分支、
删除或私有分支、独立仓库或整个网络，不能把这个结果写成全网 key 不存在。

### 12.5 证据保留与处置

只公开独立描述、原始源码和哈希。仓外 `correct-v2-candidate-results.json` SHA-256
`f7837283f00b328fcb9cc989ab56dbc3bd4fa54ca442facb13d1e910bc3723ff`；59 项测试日志 SHA-256
`601e287be6552a47111051bb4cb156817dd23589c353f7459a03d2f9484797ad`；有界检索 `report.json` SHA-256
`7064dd1c31bfa72c17fe069f17011f7911cd97d08b1848a1c24ee0e874617ac8`。
29 条原生证据的 `assistant-progress-evidence.json` 为 1,502,115 B，SHA-256
`2a26f99f275e33d1a9783ce1bdc126bf242a6419c59ba4248b23ed679a96edb3`，快照和原始厂商分析内容不入仓。
关键 Evidence IDs：

- method selection：`ev_524f2d5da8d7c5400ccb30f67ffda1b55620e0bb4dfd87719c9f748739755816`
- download：`ev_51170e9352a920d0e734635f468669e18ddbee09f50c499e4a0cfb2c6ae88b69`
- callback：`ev_2db680254b9ec83cbbbdfe086d02631af2087fecdba12e2d08c7412572c24b2b`
- cache progress：`ev_8e0b9a20dd256f63943179abdb9882c39f01e66f73092f9decd57d10c8548afa`
- tar copy：`ev_85e7dd0923d9d305f989c33d53d5c32a911cc21557bb43e72fca9cb0a1d266f9`
- FTP：`ev_c413b30b051b5043992ba68a86ec42c9ec751e93e21acf7828c7c518c4bb7a09`

## 13. RC331 内层与 QSEE 静态派生链（C-454--C-457）

本轮复用了已有固件，没有新下载或设备。0200 内层仍未解密；0205 OTA 提供了可验证的静态 QSEE 组件。
具体进展是找到了 RC331 TBIE 的派生依赖，不是恢复 root key，也不是 WA150 STUE 明文。

### 13.1 A-005 的两层 IMaH 必须分开（C-454）

A-005 为 454,223,680 B，SHA-256 `d8a8fe5b418ee6461f6971d9dfad77bc4491d15160d47d5cf8f7481dc7113949`，
MD5 `cc219b04c4fcf34d8b14569a7e55eae1`。外层 header/signature/payload 为 224/256/454,223,200 B，`enc_key` 为空；
外层 plain checksum、encrypted checksum 和 payload SHA-256 均匹配。

原文件 offset 480 开始第二层 IMaH v2：`enc_key=TBIE`、chunk `FLYA`，header/signature/payload 为
224/256/454,222,720 B；逻辑 chunk 454,222,705 B，padding 15 B，实际密文 offset 960。
内层 payload SHA-256 `5ec5414885733a276cfe28f429bd94298ce22ee3f2a9a772dd1b7ec8c4a07898` 与 encrypted checksum 均匹配。
这还没有得到 FLYA 明文。C-319 收窄为外层观察，C-322 的“RC 全部明文”整体推论撤回。

六个公开 TBIE 版本只做了 32 字节 prefix/magic 试探，未执行完整候选 checksum 验证；不能登记成六个已排除的 key。
本轮完整性检查不冒充新的 RSA 验签。

### 13.2 已有 OTA 与组件的完整性复核（C-455）

A-004/0205 为 985,959,104 B，SHA-256 `f707cf3dc0be2894b111ce4973d0206e896a2c7e9c4ebe43de1040b528cf49ce`。
ZIP 中 payload.bin SHA-256 `6579ebf096b01be4b03b12a1551052fee68625cf13c67847d8aa11db1eb27f9d` 与 FILE_HASH 匹配，
metadata SHA-256 `bad6254d2a780bff5303ca5bbea3e0d7de0ddba677dc7b8cdc4c25d0867e220c` 与 METADATA_HASH 匹配。
OTA 清单有 29 分区，以下缓存镜像的完整哈希与 `new_partition_info` 相同：

| 分区 | 大小 | SHA-256 |
| --- | --- | --- |
| system | 867,598,336 B | `89c3721a58198e14872a67de1f078192d58b9961b695181c8b365ed96a013783` |
| vendor | 1,293,729,792 B | `a6bba2d27e343df8ac2d9b1e7b9a5a7980d9f965843543ffbe3d59880f5fbf50` |

system 提取出 `libtee_util.so`（A-084）与 `dji_decrypt`（A-085）。独立 `bw_secure` 分区（A-083）只需一个
REPLACE_XZ operation：58,300 B 压缩 blob SHA-256 `70a579f9f1b32df61d7b0c51716e6f8b38cad69c51461bb041555b0f53705094`，
172,032 B 最终分区 SHA-256 `ddae8ddd83efbc63480807e014a53fe1e660f8fb6eb49b5ed8d898f3ecbb7201`，二者均与清单匹配。
三个 ELF64/AArch64 样本只作本地静态输入，从未运行；完整身份见[工件登记](11_ARTIFACT_REGISTER.md)。
这一轮复算哈希/完整性，没有重跑旧 C-317 的 RSA 验证，也没有验证 live mounted bytes。

### 13.3 固定 header 的 client→QSEE 链（C-456）

`dji_decrypt` main（分析地址 `0x101048`）固定读取 `0x1e0`/480 B header，把 `header+0x30` 的 16 B scram 交给
`qsee_data_dec_set_key`，随后分块调用 `qsee_data_dec`。`libtee_util` 中 set-key（`0x102470`）与 decrypt（`0x1024dc`）
分别进入 `qsee_cmd_req`（`0x10213c`）的命令 `0x17` / `0x18`；它通过 QSEECom 启动 `bw_secure`，再发送请求。
这两个命令的包数据中没有传递加密 FourCC。

`bw_secure` dispatcher（`0x100470`）把 `0x17` 分派到 `init_payload_dec_key`（`0x104570`），把 `0x18` 分派到
持有 cipher context 的 `firmware_dec`。这是静态调用链，不是已经执行的设备解密。
客户端固定的 480 B 数据起点与 WA150 的 224 B header + 384 B signature = 608 B 不同，不能直接把现成二进制
当成通用 STUE 解密器运行。

### 13.4 TBIE 派生依赖 RPMB root 与 HUK（C-457）

`init_payload_dec_key` 调 `rpmb_stor_derive_key(type=0x0c)`。该分支以 RPMB root 为输入，使用 CMAC KDF，
label 为 `IMAGE ENC KEY`（13 B）、context 为 `TBIE`（4 B），派生 128-bit key；context 通过立即数 `0x45494254`
组合构造，因而字面字符串搜索没有 TBIE 命中不代表此路径没有 TBIE。派生 key 再处理 16 B scram 并建立持久 payload
cipher context。观察到 cipher mode 常数先 1 后 2、key 长度 16、zero IV；QSEE enum 名称尚未独立核对，不写死模式名。

`read_root_key`（`0x10a128`）读取 protected partition `0xa001` 的 sector 0，检查 provisioning/encflag，再调用
`decrypt_rootkey_with_HUK`。后者经 `qsee_kdf(NULL,0,label,context)` 获得用于存储块解封/认证的 key，解密并校验后
返回 root。只有这份固件代码，尚无设备 RPMB 数据或 HUK 派生输出；静态依赖不是根密钥恢复。

当前最具体缺口是 RC331 TBIE 的 root input，以及 STUE 自己的 owner/derivation。没有证据表明两者共享 key 或 scheme，
也不能把本路缺失输入写成所有离线方法都不可能。

### 13.5 证据引用与处置

仓外 `handoff.json`（31,672 B）SHA-256 `3add0859cde61baa7e3a346967b83d1019d6d098001fc969f5d0adae44e9069b`
保留完整性和提取元数据；其主机路径、厂商 strings/反编译、二进制与原生快照不复制入仓。关键 Evidence IDs：

- client main：`ev_cbe5b97e992d853558d3d21c2d2303d8b70a2ab616e5bfa4933db9f99c52ab13`
- set-key：`ev_ea1c5706d29589fc1a927c08cd1a528ebcbe709e2f6d5485f594642bc23b7237`
- QSEE request：`ev_8784fedbfb866f6d5f336b97df8c41887533ba730d9f4a673ee994bf74f7ebea`
- dispatcher：`ev_74ec7bce1c58954bf7a77c5414ca25b7434619d5123f92fd5b1bc650437e5d93`
- payload init：`ev_8a55e89bbaaff31bc0e45964d0bac4f8c02f224e0c3d25c51ec82401ed16bd1c`
- derivation：`ev_9bbc4b83ecc897a306815f04f155c5d16661adf6decf2c8a776aae03aebacd13`
- assembled context：`ev_582a032c3ab48c4d4cfed09cfea523e4add043e2d48aa4261be53b8b70d19fd7`
- root read：`ev_5d517d9b5eee1338532b37adef576bd3ce0fd6a42b3f734669e442a313361f76`
- root/HUK：`ev_762ba19eeada4a181d17da9597c6406b90b6ada7a58bc7584efb402cb1efc19a`

## 14. SDK keychain 与位置路径分支（C-458--C-462）

SDK keychain0x37 的返回值已在隔离 ARM64 内存中得到并通过重封装对照，但完整位置消息/设备/RF 尚未验证。
STUE 仍未解密。新的结果必须与 RC331 TBIE、SDK app-location 和 TEE 位置封装分开解释。

### 14.1 正确动态表映射与样本身份（C-458）

A-086 `libsdk_base.so` 为 7,720,240 B，SHA-256
`e5b290ebc6aa6e409e116cc0d3b84fb4e49c70f6c552feffacd5b15c7c83e873`，与已有官方 DJI Fly 1.21.10 APK 中
`lib/arm64-v8a/libsdk_base.so` 成员逐字节哈希一致。该 ELF 没有 section 表；PT_DYNAMIC.p_offset=`0x75cae0` 指向
仅含 NEEDED/SONAME 的短表，而 p_vaddr=`0x718500` 经 PT_LOAD 映射到 file `0x717500`，得到完整 SYMTAB/STRTAB/
GNU_HASH/RELA。正确读取后有 14,944 个动态符号，whitebox/crypto Get 与 WAES 确有定义。

分析地址：whitebox Get `0x44d640`、crypto Get `0x3ebacc`、WAES decrypt/encrypt real `0x44e0f8` / `0x44ddfc`。
C-418/C-419 的嵌入名字/strip-only 解释撤回；provider 的事实保留，C-417 的无定义结论不恢复。

### 14.2 完整 Get(0x37) 的受控模拟（C-459）

A-087 用 Unicorn 2.1.4 在隔离 ARM64 内存执行完整 whitebox Get。它经 `uav_white_box_decrypt` (`0x44d4c8`) 用
第一表指针的 48 B ciphertext、第三指针前 16 B IV，执行固定 WAES CBC 解封并去 padding，返回 std::string。
实际外部替代只有 malloc 2 次、memcpy 1 次、free 1 次；没有 Android loader/OS 或设备执行。

结果为 32 B，SHA-256 `6deb71ae64dd7f305c107c2f6986d35a591025778c3791516a58215f1154f6ac`。
padding 为 16 个 `0x10`，结果不同于 ciphertext 前 32 B。三组 synthetic block 加/解 roundtrip 通过；
将返回值和 padding 按同一 WAES CBC 重封装，与原 48 B ciphertext 逐字节相同。

只公布长度、哈希与 PASS/比较结果，不发布 key、cipher blob 或厂商代码。该批发现 A-078 v2 错误地取 ciphertext 前 32 B；
C-421 的 48 B key、C-423/C-425 的直接可用 key 解释已更正。后续 C-464/C-465 单独闭合静态 22 B 输入/84 B payload 并修复
A-078 v3；这不把本次 keychain 模拟扩展为完整 handler、transport 或 RF 结果。

### 14.3 bw_secure 的独立 key/position 分支（C-460）

A-083 的命令 `0x16` 进入 `dji_handle_uav_key` (`0x104ac8`)，使用 derive type `0x0b` 作为 16 B AES key。
命令 `0x14` 进入 `dji_handle_pos` (`0x104d0c`)；`distinguish_rootkey` (`0x104bec`) 用 type `0x0f` 派生 key，
对 16 个 `0x09` 求 CMAC 并匹配三项指纹，选择对应 32 B 密文并解出 32 B 位置 key。

被检查的输入长度小于 128，做 PKCS7 padding；每次产生 16 B random IV，ciphertext 后附 IV，再由 HMAC routine
（算法数值 2、输出 32 B）覆盖 ciphertext+IV；外层 LE32 length 再加 4。TA 没有执行，QSEE cipher/hash enum
没有独立映射，因此此处不写成 CBC/SHA256。不能据此归为 STUE，不能假定 SDK 与 TEE key 相同，也不能推断 RF 位置可控。

### 14.4 GPS updater 只闭合本条 transfer 路径（C-461）

A-088 `dji_gps_update` 从已 hash 匹配的 system 镜像提取，32,800 B，SHA-256
`2bf9cd3e24b32256134213d047f33106e03009cebc6d58a246bd13cf3b1d7aa9`，ELF64/AArch64，未运行。
main (`0x1057f4`) 读取 `persist.dji.gps_update.loader`、`firmware`、`latestVer`；check_file (`0x103eb0`)
验证 32 B header CRC16 与 data 的 LE-word checksum。upgrade 将两个文件交给 xmodem_send (`0x1043ac`)，
后者以 1,024 B fread、复制数据、添加 XMODEM 头/CRC，末帧用 `0x1a` 填充后写 UART。

已检查的边没有恢复出 IMaH/STUE 解密，不覆盖其他 firmware producer 或 WA150 GNSS 是否采用此路径；无硬件写入。

### 14.5 有限独立公开调查（C-462）

- [fvantienen/dji_rev 固定提交](https://github.com/fvantienen/dji_rev/tree/64d3551e3087c56268506674b7f56fdd51189bdf)：
  检查 `tools/derive_key.py`、`tools/image.py`、`symbols/headers.h`，是旧 v1/CBC 与需要调用方 key 的派生逻辑，未提供目标 STUE 解密。
- [WA341 battery tester 固定提交](https://github.com/danusha2345/dji-mavic4-battery-tester/tree/eb5429aed4ec11b2f89073b8371f0b95abcaa749)：
  检查 `PROTOCOL.md` / `duml.py`，是电池 DUML/UART，不是 IMaH/STUE consumer。
- Unicore 的 [UC6580 产品页](https://en.unicore.com/products/dual-band-gps-chip-uc6580/)与
  [datasheet](https://en.unicore.com/uploads/file/uc6580-datasheet-en-r1-1.pdf)提供 GNSS 芯片和 loader 接口背景，
  [PRODUCTINFO](https://en.unicore.com/uploads/file/UFB2%20Protocol/UFBII%20Protocol%20Specification%20EN/Unicore%20Messages/General%20Messages/03-2-2%20PRODUCTINFO.html)与
  [CFGFWCHECK](https://en.unicore.com/uploads/file/UFB2%20Protocol/UFBII%20Protocol%20Specification%20EN/Unicore%20Messages/Configuration%20Messages/03-3-21%20CFGFWCHECK.html)
  说明身份/校验接口；这些只引出 A-088 候选，不提供 DJI STUE key 或确切 board placement。
- [DJI 白皮书入口](https://www.dji.com/trust-center/resource/white-paper)、
  [独立评估摘要](https://terra-1-g.djicdn.com/851d20f7b9f64838a34cd02351370894/OnDefend/DJI%20Technology%20Inc.%20-%20Security%20Assessment%20-%20Executive%20Report.pdf)与
  [Payload SDK 页面](https://developer.dji.com/payload-sdk/documentation/quickstart/porting.html)在实际打开范围内没有给出目标 key/PRAK/decoder。
  白皮书 PDF 获取失败，GitHub 部分 repository-search API 返回 403；这些访问失败不算源码阴性。

没有重查全部 fork、全 SDK 或整个网络；这里只记录列出的固定文件与已打开材料。未发现新 STUE key、匹配 PRAK 或目标 consumer。

### 14.6 证据处置

仓外 keychain-result.json SHA-256 `a0382eb8e110e31a9cff56faf34e91682ec32618330a679f28f5dc0b6d126cff`；
17 条 SDK native 证据包 SHA-256 `6552fd8bb0bdb0b89ecaca22a024b2588059a8d89ed6629fcf5b278e7514d488`；
bw_secure 位置分支 snapshot（23 条）SHA-256 `9564757668bbe13d87cb387a906e3a3d7e554aca20b6f4405cf11a1151d4cc82`；
GPS snapshot（5 条）SHA-256 `b14dd7502d18cbe63890cb6a2f41932c95b047846bf760e5023243cca08d1a00`；
本轮独立公开调查 report.json SHA-256 `85d622f0d281138530f4fd2784f094579efdaac529f3107495fa523b96231b1c`。
这些原始证据和厂商内容不入仓；公开探针只读取本地固定 hash 输入并输出哈希/结果。

关键 Evidence IDs：ELF/provider `ev_305d8336d0b5463071629ab2ad1dc049ff172b02c2944645ef17134561f380be`；
Get `ev_161f95c5798725c113434870497698014ccbe24c5d9c9fe59077f65dc3b83585`；
Get ABI `ev_e1728f728a564d2eaca6343b49a3187548a8b57ac07d2cf6141e879154f8ff36`；
unwrap `ev_0ec1bf7c63ed57e9a41969f0674aa81a8d4897e6160468a14bca3ed1771afd77`；
TEE key `ev_19a3629dec329e9c2c4ba4df690da25fbd1078c2d86dfa014c58e85e0982b2ef`；
TEE position `ev_da4d441af369ff63b11ae7a54af0079a0c877e66a04643c5f0d7d44048b8d516`；
root selection `ev_420e68697b4ad269e0e1677968b7e233e440e4479966509e244aefb52d1ffd3a`；
GPS main `ev_a0387210e1fb5ed6933dc166cb99181652ec48d85451975549914aab65a64fcb`；
GPS file check `ev_efddf15c06b89499b51c4ae5d9f26b62ce68a1b31504bbfeb9f9353c76df97fc`；
XMODEM `ev_f5f2bb9261f2027d9324786a2d0304a87fe4f562248db15ccb11e97be117ac7e`；
upgrade `ev_b80e0781b9e298e05a05d9f7150fd2bf9d244c1cc2b27e5dfb7672df4726174c`。

## 15. 2026-10-18 状态 parser 与位置 payload 验证（C-463--C-465）

本批修正两处可复现实现问题：状态 parser 接受至少 7 B，位置 encoder 生成 84 B 离线 payload。
共 36 项 parser 主机测试和 4 项 position 主机测试通过。原 C-450 的 59 项 firmware 测试是另一批已有记录，本批没有重跑或合并。
仍未解密 STUE，没有完整 JNI handler/SendSetPack、设备传输或 RF 验收。

### 15.1 双端状态 parser 的最小长度（C-463）

依据 C-147 和 RID-002 的官方 parser 前缀，Java/Python 同时拒绝 null/少于 7 B，接受 7/8/10 B。
Java 将尾部复制保存，getter 返回 clone；Python 使用 immutable `bytes trailing_bytes`，`repr=False, compare=False`。
未知尾部既不解释也不输出。已知 flags/area/failure、display/脱敏摘要、DUML CRC/route/type/command 和 sender gates 均不变。
C-148 是 license 消费证据，不能当作长度来源。

Java parser 与未改的 timeline 共 15 项 JVM 测试通过，Python direct-module 共 21 项通过；未构建/安装 APK、未部署设备。
同范围引用检查没有发现其他 Java `PAYLOAD_LENGTH` consumer。四份源文件身份见对应仓外验证报告；没有生成新的 APK artifact。

### 15.2 精确 JNI caller 的静态布局（C-464）

A-089 为 87,313,856 B，SHA-256 `5abd990c86bcd00c9a652a21e329ad4580a20ec9f80188075ada61f5a7b46286`，
与已有官方 Fly 1.21.10 APK 的 `lib/arm64-v8a/libsdk_jni.so` 成员流式 hash 一致。`UploadMobileDevicePositionSet`
的 ELF VA 为 `0x4d23260`，2,356 B，原始函数 bytes SHA-256
`afa49f1b9c7c050bac1a065336be9b30d686e75604a7469756e7205d1e9656b9`。
整库 REA 未返回可用证据后已关闭；这里用 Capstone 解码精确原始 bytes，并按真实动态符号/PLT relocation 标定调用，不猜测失败原因。

| 输入/操作 | 已核对的含义 |
| --- | --- |
| typed object `+8` / `+0xc` | 两个 u32 各取低 byte |
| `+0x10` / `+0x18` / `+0x20` | 三个 double 各转整数，连同前两 byte 与 `+0x28` timestamp 组成 22 B |
| output Buffer resize | `0x4d23344` 附近将 ciphertext buffer resize 到 `0x20`/32 B |
| AES call 参数 | `0x4d23384` 的 `w1=0x100` 表示 key bits 256，不是 256 B output |
| HMAC algorithm | SDK base ELF `0x32254c` 起的 map 初始化把 0 绑定 EVP_sha256，后续 1/2/3 分别 sha512/sha1/md5 |
| success payload | resize `macLen+0x34`=84 B；写 LE32(`macLen+0x30`)=80，ct32 在 +4，原始 IV16 在 +36，digest32 在 +52 |

没有额外 plaintext16 prefix、伪 SDK request32 header 或补到 256 B 的 ciphertext 字段。
C-467后续确认 raw typed 值已在上游预缩放：lat/lon×1e6、alt×100，不能把handler输入当作未缩放degrees。
C-473 后续推进选定 Java/default-provider 的条件高度语义，实际 provider/有效性/RF 参考仍未知。SDK使用原始constant IV，不能与C-460的QSEE random-IV路径混同。

### 15.3 分段模拟与原生 helper 对照（C-465）

原始 JNI instruction fragments 在受控寄存器、synthetic buffer 和 memcpy hook 下得到 22 B marshalling 与 84 B packing。
执行范围为 ELF `0x4d232e0`--`0x4d23324`、`0x4d23694`--`0x4d236c8`，不是完整 handler 或 SendSetPack。

另在隔离 SDK CPU 模拟中使用 keychain 实际返回的 32 B key（仍只公布既有 hash）与 synthetic 22 B 数据：
`AES256Encrypt`（分析地址 `0x422154`）输出 32 B，与 CommonCrypto CBC 逐字节一致；`HmacEncode`（`0x421d74`）
输出 32 B，与 stdlib SHA256 HMAC 一致。其 SHA256 lookup node 是受控输入，没有执行 Android 全局 constructor；
algorithm 0 映射由第 15.2 节原始初始化指令另行支持。只补了实际遇到的 realloc 内存 hook，其余 crypto 函数按原指令运行。

### 15.4 A-078 v3 的实现范围

`build(plaintext22, key32, iv16)` 输出 `LE32(80) + AES-256-CBC ct32 + IV16 + HMAC-SHA256(ct+IV)32`。
caller 显式提供已序列化字段、已解封 key 与 IV；CLI 从三个明确文件读取。移除旧 `KEY48[:32]`、伪内部请求头、
猜测的 lat/lon 转换和 256 B ciphertext 填充。工具不生成 DUML/设备 transport frame，也不建立坐标单位。

4 项主机测试包括独立 OpenSSL 固定 synthetic fixture、长度/解密/HMAC 范围、拒绝旧 48 B key 和不同 IV 对照。
依赖固定为 `pycryptodome==4.0.1` 与 `unicorn==2.1.4`。当前状态只到 offline payload model / native components checked，
不称完整官方输出、完整 handler 或实机可用。A-078 v2 的错误与失败历史保持撤回。

### 15.5 验证记录与公开边界

仓外 `rid-status-parser-check.json` SHA-256 `71cd9bb0968599ba8f307e433b08176f47d69a7234e439b8f313a6a68b8f05e6`，
Java 测试日志 SHA-256 `b9259c995adfae127fac5cda5e2b16cd83b7f70560ec282a38e13ba647ad3617`；
`jni-apk-member-identity.json` SHA-256 `7e1a1a89fde7b75c991a0f9416f55eafaa230ef2577c62e8682ec83fe580906f`；
`position-packing-result.json` SHA-256 `13433f0c68b3ea6f808d6aa737572d9fbdcc8b5d671b2c4446599fd98e4b6642`；
`position-native-result.json` SHA-256 `4290f1f6cb1a9686880b047616d2ed70f583367bb129db2d9cd9858253cfd165`。
私有 helper/packing 实验脚本 SHA-256 分别为 `0cd2185a45424e32c97236cbf88590b8365414a7f260f06d343d423240a78266`、
`3e0132129e8bb0b601362e7f059105ee84878e709cc32a708573c9858be11b3e`。
厂商 listing、输入样本、key bytes 和这些原生实验脚本保持仓外；仓库只保留自写 encoder/tests 和高层证据。

## 16. Android upgrade 的限定静态负结果（C-466）

本轮选定官方 Fly 1.21.10 的 A-090 `libupgrade_core.so` 与直接调用的 A-086 image helpers；没有运行厂商代码或设备。
A-090 为 6,557,136 B，SHA-256 `9b2c0cc2a95b3de94dd74dbc6781cbc780590b1439b4ffca56aeb68243b6f629`，
已与原 APK 的 arm64 成员逐字节比对一致。该 sectionless ELF 的正确 mapped dynamic table 有 7,343 个符号。

| 已检查入口（ELF VA） | 静态结果与边界 |
| --- | --- |
| VerifySignCfgData `0x5933cc` → get_chunk_by_index `0x31b2c8` | 前者取得 index0 chunk.size 和 payload 指针并复制到输出 string；后者仅计算 header/signature/chunk 偏移。这一 extraction pair 未做签名验证或解密，不外推所有配置路由跳过认证 |
| DatabaseServerCfgRequest::GetRequestBody `0x363c08` | 选 whitebox slot `0x0b`，组合 version/timestamp 后调用 CreateSignatureWithSHA256，写 request signature/timestamp；所见流不连接固件 payload decode。直接 B/BL 扫描仅覆盖具名 defined-symbol ranges |
| OfflineUpgradeManager::DeCrypt `0x383154` | 8 B 函数恒返回 1、没有 callee；名称不能证明解密实现 |
| CheckFirmwareFile `0x4f23f0` / SendPackForIndex `0x4f4478` | 检查 supplied path/name/size、打开文件，seek/fread、更新 MD5、复制原缓冲到 transfer packet 并派发；所检查 body 未出现 payload 解密或 key selection。caller 的文件和动态目的端未确定 |
| base image-header verifier `0x31afbc` | 只从 auth_key 选择 RRAK/PRAK，对 header_size 求 SHA256，UAV_RSA_verify 的签名长度写死为 `0x100`/256 B、digest 32 B；init 拷贝两个 public-key structures，verify/update/final 处理摘要，未选择 STUE 或解密 content |

`NEGATIVE`：这些 selected bodies 中没有闭合 file-read→IMaH/FourCC→STUE key-selection→decrypt 的具体调用链。
256 B 签名 helper 不提供当前 WA150 384 B signature 的匹配 PRAK，也不能据此断言 SDK 的所有 crypto 只支持 256 B。
未知的 indirect/unnamed caller、其他库/方法/版本/设备路径不在结论范围；没有建立 WA150 runtime/product gate。
slot `0x0b` 的 request signing 也不能当作新的 STUE key 来源。

### 16.1 证据身份

仓外 `android-upgrade/report.json` 为 17,872 B，SHA-256
`7c845b5adcd97ff6661d370b55238700bf91299ca153abc4ac4e812107bbd623`。
core evidence（8 records）SHA-256 `13a21d53e4b561cf55b3399749d80bcd21b2fad266767aa8fb811c6c19dd2ef9`；
base evidence（18 records，含 17 条先前 SDK 记录）SHA-256 `0215e5e95a17f92416a7e4c12d0373959960944244b1889a33ae8a6e4b4e55ea`。
快照及厂商 listing 不入仓；只公开身份、偏移、高层结果和以下 Evidence IDs：

- DeCrypt：`ev_dcc5b26af6894527dd646cd0611dc79887b4c105fb3df1a32543c839b54a2312`
- config extraction：`ev_fdacd61961c63efa5d5b37178a3fcf77d959dc6a876ecc96e8e617d6112dad1d`
- chunk pointer helper：`ev_b605faffd49dd9c938b707d4a1753f5cd6bb6ae9ac5b8c533588a3975e89a045`
- request signing：`ev_8e1d18a9719941f4ba702fa7852e19014caa8472cca052773c1a9284af8aa528`
- file buffer helper：`ev_039ad137d26f7bf6553ed498af4a374016af837630f2af7cfd186b1669f11f69`
- file check：`ev_93f7435ba5877093e17aa7468346232386bb6b5bf591c8fb4d91110000ba0c5c`
- transfer copy：`ev_52495294244449e0935f47fddda1a10ba073ad03cf517a40d16f63742f2dc5f3`

base verifier 的有界原始函数范围 372 B，SHA-256
`62aa8ccab375e2dc7c7d8c9be21a7a60525c1a84cc83abf477f65e8f35c1f1e3`，其余 raw-function identity 由上述私有报告保存。
这一范围有静态 bytes 证据，不捏造不存在的 REA function Evidence ID。

## 17. 精确 HostID 条件与 payload-only CLI（C-468/C-469）

### 17.1 路由原始片段与 helper（C-468）

输入为 A-089 JNI、A-086 base，以及固定 libsdk_key_value.so SHA-256
`09f4aa8aef65f720da09a1dad79c8851e05d619affaf73708bf6747341208336`。
free KeyHandlers 的 EID 与 position templates 都读取 single HostID 和 multiple HostIDs。仅当后者为空且前者非空，
才以 descriptor[0] 写 req+7、descriptor[1] 调用 SetReceiverIndex。实际 helper 写 req+0x19，OR req+0x0a bit1。
Characteristics+0x30 只是进入 callback capture，C-385 的 receiver 解释撤回。

| 函数/ELF VA | 长度 | 原始函数 SHA-256 |
| --- | --- | --- |
| free position SendSetPack `0x4d23c08` | 912 B | `d11e77ee74eb1227707822d506a0e0f3a920c7eae74ebf47c4024b366e2585f4` |
| position callback `0x4d24778` | 1,092 B | `b7a5dcc5d266bb356753d871bb400c94472977cb86fd4683624952611b13c403` |
| free EID SendSetPack `0x4d139d8` | 912 B | `8a0dd89c22bc914b6e5935710879c8b2563817ba1a77953edec893ef6740c1a5` |
| BaseAbstraction EID Set `0x2ca4c2c` | 836 B | `fe0605a6df1f634b7ce154cbfb606256b7a7000fd8a1e5aa1f841cf8e2b1f4c6` |
| base SetReceiverIndex `0x2ec25c` | 24 B | `db3b39de95ce3302b757dfdf9539dad662a3e08c55f15be1ca9d374579bb555e` |

free templates 发送用 first-pointee virtual+0x10；只有上表 BaseAbstraction EID 重载证明 virtual+0x128。
原始 prefix 与实际 SetReceiverIndex/GetSendPackHostID(s) helper 在六个受控 case 下通过：EID/position 各检查
single-only、no-single、multiple-present 三种状态。GetExtraParam hook 返回 synthetic descriptor container。
没有执行完整 SendSetPack、callback、Android initializer、transport 或设备/RF，runtime Characteristics/HostID 与 owner 未知。

### 17.2 五个 CLI 只编码 payload（C-469）

五个旧 CLI 删除伪 32 B SDK 对象头、无效 sender/receiver 参数和 receiver 提示；内存对象布局不再混作 wire framing。

| Codec | 当前 payload 范围 |
| --- | --- |
| France EID | GET `[02]`；SET `[00]`/`[01]`，非法启用值拒绝；法国专用 |
| 中国 UOM | 18 B，SET 最多复制前 8 B；GET `[01,02]` 后本地零 tail，不复制 vendor undefined tail |
| EASA OPID | GET `[02]`、DELETE `[01]`、SET `[00,10]+exact16`；CLI 显式 payload-file/delete/get，不校验完整20字符登记输入/country/checksum |
| AirSense | Boolean-normalized 1 B；不是 RID broadcast switch |
| 动态最大高度 GET | empty payload，CLI 输出空 hex 行；不是高度写入 |

8 项 host schema tests 与 9 个有效 CLI case 通过，5 个旧 sender/receiver 参数调用被拒绝。它们只验证 synthetic offline
payload 和 CLI 行为，没有 whole-handler 对照、真实路由、UI 设备写入或 RF。旧 constructor 镜像测试的历史不构成 wire 证据。

### 17.3 证据处置

仓外 routing report.json（4,549 B）SHA-256 `ecbe67708bcc1b0abab8e47ec3c9afb805b0007f99e5e5767b2ab64aeadd0ee6`；
payload-codec-check.json（1,064 B）SHA-256 `35f3477300367b79d0eb07aff86dac734ea01a4308005eda1e0c90c3044e5923`。
原始 listing/受控模拟留仓外；这里只发布函数身份、条件和自写 payload sources。测试结果不扩大到设备控制面板可用性。

## 18. 精确 MobileDevicePositionMsg 上游语义（C-467）

C-126 已记录 lat/lon×1e6 和 alt×100，本节不将它们作为首次发现。新结果闭合 exact type、40 B SDK serialization、
Java byte[] provider 边界与 epoch-second timestamp，并纠正“无效坐标直接丢弃”的解读。没有执行 Android、设备或再次运行 crypto。

A-091 `libsdk_key_value.so` 为 12,684,576 B，SHA-256
`09f4aa8aef65f720da09a1dad79c8851e05d619affaf73708bf6747341208336`，已与相同官方 APK arm64 member hash 核对。
其 RTTI/vtable 定义 `MobileDevicePositionMsg`，constructor `0xaa56cc`（36 B）签名为
`(int,int,double,double,double,long)`，写入 object+8/+0xc/+0x10/+0x18/+0x20/+0x28，不自行缩放。
serialization `0xaa5840`（68 B）/deserialization `0xaa5884`（252 B）对应 40 B；它不同于 handler22 B 和 encrypted payload84 B。

JNI producer `SendEncryptAppGeographyInfoToDevice` 位于 `0x209e6b0`（3,296 B）。首字段在这条路径恒为 0；
第二字段默认 1。有限纬度超出 [-90,90]、经度超出 [-180,180]，或两者 abs 都小于 1e-6 时，它把第二字段置 0，
仍继续预缩放、赋 timestamp、捕获对象并排队。这里仅称 validity-like field，不把它绑定为已验证 GPS-quality/receiver enum；
NaN/nonfinite 规则不扩成验证契约。lat/lon 上游各×1e6，alt×100，handler 收到 pre-scaled doubles 后再转整数。

location 经 ClientStateMgr 的 GetClientLocation（`0x2099db8`）取得；其 native provider（`0x1c5cf24`）调用同版本
`uav.sdk.provider.jni.JNIProviderManagerForCPP.clientLocation():byte[]` 并反序列化为 LocationCoordinate3D。
相关 provider-valid/foreground/location-service checks 是静态门禁，不是 live GPS fix/permission 观察。
本节分析当时未恢复精确 Java body；同版本后续选定方法体与 provider 结果见第20节 C-473，不借另一版本补齐。

`GetCurTimestamp` 在 A-086 ELF `0x2ec618`（36 B）调用 libc `time()`，是消息构造时 Unix epoch 秒，不是毫秒、
monotonic、GPS fix timestamp 或 RF receive time。仅凭 ×100 不能确定高度单位；C-473 后续在有效 Android/default-provider
条件下建立米/WGS84 椭球契约，实际 provider/有效性/设备 RF 参考仍未知。A-078 保持显式22 B序列化输入，没有新增 typed坐标编辑API。

仓外 position_semantics_findings.json（14,606 B）SHA-256
`72238bf86728ea49087f88219ef5763c280a1ba31ac4a8bd722d3f358f8f4781`。
输入身份、RTTI/relocation、constructor/serializer/producer/provider/time 范围由该报告及私有原始 listing 支持；
此轮没有 REA Evidence ID，不复制厂商 listing。以上不是 Broadcast RID、飞机导航位置、应用读回/恢复或 RF 控制证明。

## 19. 小模块范围更新：复核 A-066 与新增 A-092（C-470）

官方 `mydjiflight.dji.com/getfile/firmware` 经一次受约束 CDN 跳转取得两份当前清单条目，大小/MD5 及独立 SHA-256 匹配。
其中 1200 与历史 A-066/C-323 完全同字节，只登记重新获取/复核，不创建重复 artifact。新增独立容器仅为最小 1100 wa140bat 变体。

| Artifact | 清单条目 | 文件大小 / MD5 | SHA-256 |
| --- | --- | --- | --- |
| A-066（复核） | 1200 / 01.52.00.61 / mc01 | 67,744 B / `8fda0e65105ec628beee13108d175f60` | `fb802d4d8ca04d0c14b4c6f9be9cada9b18cceef915a1658279a954ba5ab5feb` |
| A-092（新增） | 1100 / 22.75.00.17 / wa140bat | 94,336 B / `be3245b4373fdee82470dd2fe6d66882` | `82bb350a2b229c03cf282322a7463047082b5135780dab510c9e3307882f6dc5` |

两者在 `01.00.0600`/`01.00.0700` 清单中相同，均为 IMaH v2、STUE/PRAK、384 B signature、单 chunk offset608，
attrib0/compression0。1200 stored/logical payload 为 67,136/67,129 B，1100 为 93,728/93,704 B；payload SHA-256 与 encrypted
checksum 均匹配。原始 payload checksum 不匹配 plain field，不是明文；arch_field0 也不能识别指令集或内层格式。

没有 RSA 签名验证、key trial、解密、升级或设备访问。wa140bat 是该 manifest 的兼容变体，不是 WA150 原装电池型号判据。
C-306 的七个小条目无本地原件是历史状态：C-323 已取得过 1200，本轮重新取得同字节并补查一个 1100；其余五个 1100 变体未检查。

仓外 wa150-small-modules/report.json（8,470 B）SHA-256
`166305a7c3a72161c95af58cff6f8199d883b281e9e707dc45c2983eaf183515`。
请求密钥、签名查询与不透明 CDN 路径只在内存中使用，报告保留有限身份/校验结果；样本只读保存在仓外。

## 20. 固定 carrier 分析视图与 Java location 来源（C-471--C-473）

本批从已有官方 Fly 1.21.10 的 A-093 `libdatajar.so` 继续，未运行 Android 或厂商 Java。
A-094 是独立编写的离线工具，为静态分析器构造受约束的视图；它未恢复原始 header 或证明解密。
carrier、四个视图、含原始 header 的 manifest 和全部厂商代码/listing 保持仓外。A-078 的显式 22 B 接口不变。

### 20.1 目录与 map 的双重约束（C-471）

A-093 为 205,458,768 B，SHA-256 `5a62603110efe22bbaed35ed34bdc8a292bf0fc657b4790fb0df086e497d1b22`。
blob 是文件半开区间 `[0x4008,0xc3ef00c)`；首个 BE u32 为 payload size `0xc3eb000`，payload 从 `0x400c` 开始。
第一个 segment 位于 `0x500c`；前方 0x1000 B metadata 页的最后 352 B，即 `[0x4eac,0x500c)`，包含 22 条各 16 B 的目录。
每条由 BE u32 的相对首段 offset、logical size 和两个观察值为零的 u32 组成。

22 条目录的 base/size 均与独立定位的 DEX map 对应；storage length 是 logical size 向上对齐 4096，最后一段 storage end
等于 blob end。独立复核反过来从目录推导 base/size，再找 terminal map，结论一致。`[0x400c,0x4eac)` metadata 和两个
零字段没有进一步解释；没有据此命名保护算法、推断 loader 行为或声称恢复密钥。

### 20.2 四个限定的分析视图（C-472）

A-094 固定输入 digest，要求显式 carrier 路径和新的私有输出目录。每次只生成选定的一份 view 与 manifest；默认 base 为
`0x689f00c`。它不修改 carrier、尝试 key 或连接设备；所用 Python 模块均为标准库。

| View / 内容 | Carrier base | Bytes | Strings / 原始明文 string_id 尾项 |
| --- | --- | ---: | ---: |
| A-095 JNI/provider | `0x689f00c` | 9,135,872 | 34,033 / 1,293 |
| A-096 value/cache | `0x5eea00c` | 10,174,556 | 39,624 / 6,884 |
| A-097 app provider | `0xa3cf00c` | 10,817,208 | 54,798 / 22,058 |
| A-098 mapkit | `0xd0100c` | 10,595,776 | 48,519 / 15,779 |

四份视图只替换相对 header `[0,0x70)` 和 string_ids `[0x70,0x20000)`；从 `0x20000` 到 logical end 的字节全部原样保留，
包括所选 code_items 和 exception data。严格 MUTF-8、声明 UTF-16 长度、唯一 UTF-16 排序、padding 和重建索引检查均通过，
全部原始明文 index 尾项吻合。type/proto shorty/field/method/class 引用约束也通过。默认段为 10,934 type_ids、10,637 protos、
24,434 field_ids、61,119 method_ids、8,155 class_defs；不要把 method_ids 数与 defined-method inventory 混用。

`dex035` magic、header_size `0x70`、little-endian marker 和零 link_size/link_off 是分析假设；新 SHA-1/Adler-32 只描述视图。
原始版本、link 字段、checksum 和 DEX 身份均未恢复。公开工具复现默认 view digest，并成功生成非默认 mapkit view；另两份
选定视图由此前私有原型生成。现有 JADX 1.5.6 只做单类静态解码/只读 API inventory，默认段得到 8,155 classes、58,041 methods、
1,047,528 instructions；没有执行这些指令或全包反编译。所有 view 的完整身份见 [artifact register](11_ARTIFACT_REGISTER.md)。

独立复核重建四份 string index，并额外核对 proto/field/method key 的有序唯一性；22 条目录/map、各 view 的完整 post-prefix
字节和公开默认输出均吻合。30 个目标及直接支持方法的 class_data、method IDs、prototypes、code_item offsets 独立匹配
JADX API。没有发现阻塞这四个固定输入视图的 ID mapping 或 code-preservation 缺陷；工具不因此成为通用 malformed-DEX verifier。

五个 base `0xcba00c`、`0x221f00c`、`0x571300c`、`0x7b3e00c`、`0xc12a00c` 的受保护前缀覆盖 type 表，未恢复；
实际 `0xcba00c` 调用明确拒绝。不能说 22 段均已解码、原始 DEX 还原、全包解壳、ART verifier 通过或 STUE/固件解密。
结构依据为 [Android DEX format](https://source.android.com/docs/core/runtime/dex-format)。

### 20.3 选定 Java provider 与高度语义（C-473）

`LocationProviderLogic.s` 的 lifecycle-start 注册将 `Caches.a(k,w3(this))` 包入 `IClientLocationProvider x3`。
`x3.a` 经 `LocationProviderLogic.f/u` 读 cache；supplier `w3` 经 `j/t/n` 调 `UAVAppLocationUtils.c`，实际 manager 在 callback
时读取。`t` 对 null 来源使用全零坐标对象，再从 latitude/longitude/altitude 三个 getter 构造 `LocationCoordinate3D`。
`JNIProviderManagerForCPP.clientLocation` 读取 manager 中的 provider，null 则返回 null，否则取接口结果并 `toBytes()`。
这接上 C-467 的 native 边界；后续 ×1e6/×100 仍是 C-126 已有结果，不代表生命周期已运行或设备实际选择 x3。

Android/default 分支由 `UAVAppLocationManager.d` 经具体 LocationProvider、dispatcher/default 实现到 helper，读取 Android
`LocationManager.getLastKnownLocation(network/gps)`。所查返回链直接复制 `Location.getAltitude()`，没有单位转换。
只有 altitude 有效时，Android 的米/WGS84 椭球契约才支持后续 ×100 的厘米量级数值；该契约不是 AGL/RID height，也不能
推广为实机或 RF 的高度语义。来源：[Android Location.getAltitude](https://developer.android.com/reference/android/location/Location#getAltitude())。

原始 bytecode 确认：两个对象都存在时，GPS 的 `elapsedRealtimeNanos` 严格更大才替换 network；相等时保留 network。
若所选高度绝对值 ≤1e-6，则可复制 GPS 高度，却保留所选对象的 `time/elapsedRealtimeNanos`。因而较新的 network 经纬度/时间
可以搭配较旧 GPS 高度，三个标量不一定来自同一 fix。carrier `0x13cea3c` 的比较是 `cmpg-double`，NaN 不进入此补值分支。
所查 `DefaultLocationProvider.o` 没有 `hasAltitude()` 调用；全零来源或非零高度都不证明 altitude 有效。

AMap 分支复制 `AMapLocation.getAltitude()`，其转换 helper 在条件经纬度转换时保留 altitude；AMap 的高度基准契约与真实运行期
选择未在本批建立。另行注册的 `IClientAltitudeProvider` 构造 GPS/barometric 字段，是另一数据面，不补齐这条 scalar 链。

| Selected method | Carrier code_item start |
| --- | --- |
| `JNIProviderManagerForCPP.clientLocation` | `0x6f42d60` |
| `LocationProviderLogic.s` | `0xaba4604` |
| `LocationProviderLogic.t` | `0xaba443c` |
| `LocationProviderLogic.u` | `0xaba44ac` |
| `DefaultLocationProvider.o` | `0x13ce96c` |
| `UAVAppLocationUtils.c` | `0x13cc6cc` |

表内为 code_item 起点，首指令另加 16 B。JADX 高层 Default.o 的异常重建出现看似未初始化局部，不能当可编译源码；FALLBACK
核对明确 network-fetch exception 将 network 置 null，GPS-fetch exception 保留 network。结论依据原始分支/寄存器，未替换常量。

### 20.4 缓存、新鲜度和剩余缺口

`isDpadRcDevice` 在类初始化时为真才取 cache duration 1000 ms，否则 -1；`Caches.a` 只有正时长选 TimerCache，否则选
InstantValue。TimerCache 在调用时以 uptime delta 大于 duration 触发刷新。`UAVAppLocationUtils.c` 另有 1000 ms 缓存：manager
存在，且（缓存为 null 或 elapsed 大于 1000）才读取来源，先记 cache time 再调用 manager，null 结果允许下次重试。
这两处都不是 1 Hz producer，也不能限制 last-known sensor fix 的年龄。default 选择方法本身没有 age cutoff。

`LocationCoordinate3D` 构造/序列化只遍历三标量，未携带来源 time/accuracy；C-467 已证明 native 在消息构造时重新采样 epoch 秒。
本批独立 Java review 未重跑 native/helper wire 实现，字节数和 timestamp 来源仍引用 C-467。新消息不能证明 fresh fix，1 秒缓存
不意味着 fix 至多 1 秒旧。实际权限、provider/altitude 有效性、owner/transport、应用读回/恢复、持久性及独立 RF 仍未验证。
没有新增 typed 位置编辑器，也没有降低控制面板逐项实机/RF 验收要求。

复现入口见 [rid-protocol](../host-tools/rid-protocol/README.md)。REA Android 工具缺少其 JADX MCP JAR，未提供本批证据；
已用现有 JADX CLI 完成限定解码，没有新 dependency install。Native AppGuard 分析未用于上述结论。

仓外证据身份（只登记摘要；原始 header/code/local paths 不入仓）：

- `container_layout_summary.json`：1,055 B；SHA-256 `18e7b28036653a913d2878b1961a34345f677695fca4a601cdf6ca02098eede2`。
- `dex_map_candidates.json`：54,083 B；SHA-256 `c9f83ca33b232f0cfc7a3635328ababd602a19406b9aa7c1a2f7eafb234527d4`。
- `target_segment_reconstruction.json`：6,882 B；SHA-256 `1cb4720b2fcc26566923f9350e2686b8a77b5491eb12b71119dba6f61be87533`。
- `report.txt`：8,448 B；SHA-256 `82c7808c7b007f68c3c73a439dac107cc47c884ddddc7602696772326a7e5f6c`。
- `findings.json`：7,533 B；SHA-256 `c9ba314da61b934dd616a95fdfe95c78ec66e1b4b1a342738c5e21ca7a10010f`。

## 21. Fly 1.21.10 RID selector 的 DeviceId 输入（C-474）

选定同版本 Java 方法体将 RID policy selector 的第三输入收窄为 `AircraftDeviceInfo.getDeviceId()`，不能继续直接称为
ProductType139。C-286/C-287 明确属于 Fly1.19.4 源码证据/离线模型，C-291 的实机 ProductType139 与 cache receiver18/4
观察照旧；本节不撤回这些历史结果，也没有证明 DeviceId 与 ProductType 的数值相等或不同。

新输入只有 A-099：carrier base `0xb79a00c`，10,024,504 B，SHA-256
`9480d22214c12c7d3e48ee4616ed427be87a88b72c47ab248e504193a0d583ac`。未改动的 A-094 公开工具完成生成：40,790 strings
通过结构/编码约束检查，8,050 个未改动的 string-ID 尾项与重建 offset 匹配，相对 `0x20000` 后字节全部原样保留。它与既有
A-096/A-097 支撑本节；仍含第20节的 synthetic-header 假设，不是原始 DEX 或解密成果。独立 class_data 解码定位 13 个方法，
其 code offsets 与 JADX API 自动比对一致；IDs/prototypes 保留作定位，未逐项独立比对全部 ID/原型。关键 FALLBACK 分支已人工核对；
method hash 范围仅为原始 code_item header + instructions，不含 exception tables。

`UAVRidCloudControlLogic.v` 读取模型 `getDeviceId()`，缺失默认 0L。所查 generated getter 解引用 lazy ToggleFlyObservable；
其 V1 supplier 读取 compiled `KeyConnectedDevice` 标签，从列表中第一个 type 为 AIRCRAFT 的 DeviceInfo 取 `device_id`，
把 Integer widening 为 Long，缺项/null 时返回 0。实际 1.21.10 toggle/provider 绑定和连接设备列表没有运行期观察；名称匹配的
native GetConnectedDevice 未建立该 key 的绑定，不用它解释 device_id 的含义。

selector 将此 Long 与所选行 `block_device` 比较；保留第一个 exact-area 行、第一个 DEFAULT 行及缺失/blocked 时 DEFAULT 回退，
然后过滤空字符串、distinct 去重。lifecycle-start 组合 cloud rows/area/deviceId，断开时清理 CompositeDisposable。
`M` 原样把字符串放入 `CloudControlData(18,4,string)` 并通过 compiled `KeyCloudControlData` 标签调用；18/4 是这个 exact
caller 的字面量，不是 generic key 的固定 metadata、已证实的 live route 或飞机 policy owner。

| Selected method | Carrier code_item start |
| --- | --- |
| RID combiner `a` | `0xabab154` |
| `UAVRidCloudControlLogic.M` | `0xabab5a0` |
| `UAVRidCloudControlLogic.v` | `0xabab85c` |
| `AircraftDeviceInfoModelImpl.getDeviceId` | `0xbe510f8` |
| V1 supplier `j` / mapper `k` | `0xbf309fc` / `0xbf30a6c` |

所查 selector 传递 opaque string，未在这些方法恢复 signed inner 13/26 B policy body parser、新控制字段、飞机 consumer 或
STUE key。RidInnerManager 名称候选在所查 body 只是两字段 holder，不能升格为全包阴性或新控制成果。没有 Android/lifecycle
执行、实际 policy 选择/写入、readback/restore/persistence 或 RF；generic KeyCloudControlData 仍 value-routed、SET-only、无 GET。

## 22. RC331 包内 sec_type2 到 dji_verify 的限定静态边（C-475）

A-100--A-103 来自 C-455 同一已核验 RC331 `10.00.0700/0205` system image。system 为 867,598,336 B，SHA-256
`89c3721a58198e14872a67de1f078192d58b9961b695181c8b365ed96a013783`；本次证据记录再次匹配该镜像身份。
A-100/A-101 复用已提取的 libupgrade_upgrade.so/dji_verify，A-102/A-103 是同镜像的 libupgrade_product.so/libupgrade_init.so；
各输入大小/hash 见 [artifact register](11_ARTIFACT_REGISTER.md)。全部只作静态分析，未执行厂商或 Android 代码。

包内 `vendor/etc/upgrade.json` 的 SHA-256 为 `9f1e5d60b350c6a22e10ddb074f5ab5751b113231d5d0d977f14dd29719d7b73`，
其中 sec_type 为字符串 2。其 vendor image 在 C-455 已核验为 1,293,729,792 B / SHA-256
`a6bba2d27e343df8ac2d9b1e7b9a5a7980d9f965843543ffbe3d59880f5fbf50`。关键路径缺口是：init service 指向
`/system/etc/upgrade.json`，而当前 system image 该精确成员 listing 无条目。未追 boot 生成、重定向或挂载，不能声称 live
设备读取了这份 vendor 配置或实际选择 type2。以下调用链只在该包内配置条件下成立。

| Static edge | Exact ELF location / observation |
| --- | --- |
| init JSON parser → setter | A-103 `0x95a4` 以十进制 strtoul 解析；A-100 setter `0x32974` 存入参数低8位 |
| manager → sec-op table | A-100 `0x2ffa0` → `0x46900`，按 type×0x40 选择表项并复制七个函数槽 |
| type2 verify binding | table `0x4e2d8`，relocation `0x4e360` → `rk3399_up_sec_verify` `0x48004` |
| selected ordinary nonstream branch | verify-image `0x2f350` → unsign wrapper `0x2d6d4` → sec_op+8 |
| CLI verifier | A-101 main `0x2c0c` → update `0x22a8` → image update `0x2434` → crypto_update `0x204c` |

函数表依据完整 APS2 解析：VA `0x8350` 的 988 B stream 全部消费，共 144 条 relocation；Ghidra 缺少 packed-relocation xref
不是 absence。type2 的其他六槽只登记绑定，未展开成研究分支。`rk3399` 是符号名，不据此推断实际 CPU。
所选普通/非stream 路径传入 signed input、unsigned output 和 module/index；secure-module 或 stream 分支跳过此普通 unsign。
verify wrapper 构造命令名 dji_verify，未写绝对路径；失败重试仍构造该命令，日志里的 dji_fw_verify 文字不证明换了程序。
本节只检查包内同名 dji_verify 的实现，实际 PATH 解析/绑定未知；所选 wrapper 分支没有调用 dji_decrypt。

所查包内同名 dji_verify 的 main 固定 flags `0x601`，crypto 初始化模式固定 `0x11000000`。首次 update 至少需要 480 B，检查单 chunk、调用方
指定 chunk id、声明总长和 image name 等条件；实际 payload 起点按 `header_size + signature_size` 计算，不能称它固定在 480。
认证从 auth_key 字段查公钥，所查 RSA 调用 signature length 固定 256 B、digest length 32 B。该模式的 crypto_update 仅摘要
更新并 memmove 输入到输出，没有按 STUE/enc-key/scram 选择 decoder，也没有接到 libtee_util/QSEE。能按字段跳过 608 B
不等于支持 WA150 384 B 签名或 STUE 解密；未执行验证器、RSA 验签、key trial 或导出明文。

A-102 的 selected pre_init `0x13604`、misc_pre_init `0x1b038`、post_init `0x13d0c` 与直接符号检查未恢复 sec-op/type/verify
覆写边。它只限定这几个入口，不是完整 writer 清单、全调用图或运行期无覆写证明；secure-access callback 也不能当作固件 decoder。
C-456/C-457 的 dji_decrypt→QSEE/TBIE 是独立入口，其 root/HUK 缺口及既有结论保留；本节不合并两链，也不改变 WA150 owner/derivation
未知、没有设备/实际控制面板/RF 结果的状态。

本批保存 25 条 REA evidence 和四份 snapshots，全部 session 已关闭。原始 ELF、反编译/listing、本地路径只留仓外。
选定证据 ID：init parser `ev_c916b3496a7abffe9cad73fa2da269ddc2e99d009060ec9e0920bac4f6eee95b`；
verify wrapper `ev_0a73de58970e87ab26d83e7d7e47a2c33ac245ddc3c2bb65e4e043a7bb1a3383`；
crypto_update `ev_4b52e5276cc2c2666503a6cf24ba79d55d1e148c071a1c80c1dd52b37b9be757`。

仓外摘要身份（只公开长度/hash）：

- `rid-java/findings.json`：12,880 B；SHA-256 `991d073e63656c9ff396788ee9934a36ee7fa3c21554b29065214f55f8bd7982`。
- `rid-java/selected-methods.json`：8,376 B；SHA-256 `1f8c9b8690076bec5c31b02c7c3d332466e1694fc3370f32f6110191e1b83596`。
- `offline-next-edge/report.json`：15,166 B；SHA-256 `e4b05486cbab3b7350eba4b6d87e9290cdf7ee7bd6da60d01c6e38593c82af80`。
