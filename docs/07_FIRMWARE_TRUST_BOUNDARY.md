# 固件样本、完整性与信任边界

## 1. 适用范围

本文登记 RC331、WA150 和 DJI Fly 样本的身份、可验证边界、离线实验结果及不能由这些结果推出的结论。本文不包含厂商固件、APK、共享库、分区、解密输出、反编译代码或反汇编正文。

状态标签遵循 [AGENTS.md](../AGENTS.md)。后续记录与本文冲突时，较新的精确工件审计和带恢复读回的实机证据优先；相邻版本静态证据不能自动升级为当前设备事实。

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
