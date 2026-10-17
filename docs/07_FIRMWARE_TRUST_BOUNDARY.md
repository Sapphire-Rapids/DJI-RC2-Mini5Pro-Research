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
| RC 2 flyapp | `10.00.0700` | `0200` | `454,223,680` | `d8a8fe5b…8f7481dc7193949` | A-005 |
| Mini 5 Pro 主系统 | `01.00.0600` | `0802` | `679,368,672` | `c36bcbd1…b2c560386` | — |
| Mini 5 Pro GNSS | `01.00.0600` | `2603` | `436,000` | `4a573ab9…36410775f274` | — |
| 通信 dongle（两版同） | `01.00.0700` | `0806` | `12,251,264` | `75bc1b74…12d1dfbc` | — |

`STATIC`：先前已存在的 RC331 `07.00.0100` 全量聚合体（A-029，`1,446,604,800` B，`296cfa63…b0c237ab1ae3`）来自
第三方 archive，本轮 clone 进同一棵树并复核哈希一致（C-316）；它**不是**本次官方获取。

`STATIC`：`07.00.0100` 的操作界面版本对应 product_version `10.00.0700`，映射依据是既有的 A-004/A-005/A-029 登记串，
不凭旧线程或字面猜测。

### 11.2 RC331：可解且已解

`STATIC`：`wa150` 的 IMaH header 在 `header_version=2` 下仍使用 PKCS1-v1.5 签名，而 pinned 工具对 `pkgformat>=2018`
默认 PSS，故既存公开 PRAK 全部验签失败（C-321）。给本地工具副本加一条 PKCS1 回退后：

- RC331 `0205` **无 force 完整解密**：header 验签、encrypted-data checksum、decrypted plaintext checksum 三层全过（C-317）。
- 明文是 Android 11 A/B OTA（`CrAU`、`payload.bin`、`pre-device rc331`、post-build `V00.01.14.99`）；dump 出 29 个分区。
- 重新提取的两份 exact target 工件与登记逐字节一致：`adbd`（A-030，`/apex/com.android.adbd/bin/adbd`）与
  `dpad_fuli.apk`（A-031，`/vendor/app/dpad_fuli/`）（C-318）。
- RC331 `0200` 与 RC331 聚合体模块 `enc_key` 均为空，直接为明文（C-319）。

`STATIC`：跨产品看，RC331 全部明文、WA150 全部 STUE，因此**遥控器侧现在即可做静态逆向，飞机侧唯一卡点是 STUE**（C-322）。

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

`NEGATIVE`：以该原语撰写 [stue_plaintext_probe.py](../host-tools/firmware-acquisition/stue_plaintext_probe.py)，
先独立验证加密 checksum 字节范围（补码形式）MATCH，再枚举 crypt-key 方向 × stream 方向 × CTR 端序/位置 × CBC iv/ECB，
明文 checksum **NONE**（C-326）。字节范围已对，故只剩 key/mode 映射；未枚举模式、另一处 key 来源、或 WAES 与 STUE
无关均未否定。

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

### 11.9 CRijndael 真实路径与直接调用（C-331/C-332）

`OBSERVED`：`aesDecode2` 实例化 `CRijndael`，`MakeKey(key, sm_chain0, 0x20, 0x10)` 后 `Decrypt(len, mode1)` —— 即
AES-256 + CBC、IV `sm_chain0`（`a0898b00000000009236923600000000`），key 来自 `QString::toStdString`。唯一调用者是
`aesEncode2/aesDecode2/aesDecode2Ex/aesEncode2Ex`；`aesDecode/aesEncode` 的调用者含 `UpgradeNfzPack` lambda，其 key
参数即16字节字面量。`aesDecode2Ex`（QByteArray key）已可 ctypes 直调且 key 生效。

`NEGATIVE`：用真实 `aesDecode2Ex` 解2603 chunk（字面量 / 32字节池读 / 零 key）长度保持但 checksum 不中（C-332、N-65）。
framing 已证明，故下一步只查“模块 key 是谁”——即 NfzPack 字面量之外，模块是否另有 key 来源或派生。

### 11.10 NfzPack lambda 内部：XOR pad 与调用方 key（C-333/C-334）

`OBSERVED`：`UpgradeNfzPack` lambda 内，字面量 `1ff6…13a0` 是逐字节 XOR pad（`xorb (%rsi,%rbx), %r12b` 带索引），
不是 CRijndael key。`aesDecode2` 的 key 实参是 r14 = rcx = lambda 的 `QByteArray const&` 形参（存于 -0x218，再按
QByteArray/QString 共用的 d-pointer 布局重解释给 `toStdString`），解密后接 `pkcs7UnPadding`。

`NEGATIVE`：按该真实管线（两序）配候选 key，明文 checksum 仍零命中（C-334、N-66）。缺的是调用方传入的模块
`QByteArray` key。下一步沿 lambda 调用方回溯该 key，或找到其它直接给模块解密的路径。

### 11.11 NfzPack key 的现场派生（C-335/C-336）

`OBSERVED`：lambda 内建 `std::ostringstream`（-0x878/-0x880），从 -0x160 的输入 QByteArray 副本按 `std::hex` 逐字节喂入，
`str()` 产出 std::string（-0x1d0），该指针作为 aesDecode2 的 key（rdx）并按 QString 重解释；MakeKey 只吃0x20 字节。
即 key 是**现场派生的 hex 串**，不是任何外带常量。

`NEGATIVE`：大小写 hex、前16字节 hex、前32字节 raw 作 key 均零命中（C-336、N-67）。下一步是把喂入流的精确缓冲
（XOR 前/后）与格式（大小写、宽度）对齐——0x68afc2 的 XOR 循环就在流构建之后，二者关系需精确判定。

### 11.12 key 的精确派生与 XOR pad 位移（C-337/C-338）

`OBSERVED`：key 构造链已完整：`MD5(data,len)` 建于 -0x160，`digest()` 的16字节逐字节以 int 写入 ostringstream
（`orl $0x8` 置 hex 基数、`movl $0x30` 置 fill `0`），`str()` 得32位小写补零 hex 串（-0x1d0），作为 aesDecode2 的 key。
同时 XOR 循环的 pad 基址按 `subq %rcx, %rsi` 位移，故字面量索引不是干净的0..15 循环。

`NEGATIVE`：按该派生（含自洽变体）仍零命中（C-339、N-68）。剩余是流前缀/格式与位移 pad 的精确对齐。

### 11.13 pad 位移的数学与位旋转（C-340/C-341）

`OBSERVED`：C-338 的位移不是随意的——索引乘 `0xF0F0F0F0F0F0F0F1`（除17魔数），取高半右移4再乘17，`subq` 后
有效索引即 `rbx mod 17`；16字节字面量加尾 NUL 构成周期17、index16 为0x00。同一循环还用 `rbx&7`/`r14&7` 的
`shrq`/`shl`+`orl` 跨相邻字节做位旋转，再与位移 pad 异或。

`NEGATIVE`：按该模型组合各 key/data 与 post-XOR（le/be）仍零命中（C-342、N-69）。
残差是旋转的精确配对与进入 aesDecode2 的实际缓冲。

### 11.14 旋转配对精确化（C-343/C-344）

`OBSERVED`：两个字节读取（r12/r13）其实是**同一**源字节——两次虚调用落在同一对象的同一 slot0x30、同一索引 rbx。
配合 `%cl=rbx&7` 与 `%cl=r14&7`（r14 自0递减）得 `b>>(i&7)` 与 `b<<((8-i%8)&7)`，合并即 `ror8(b,i&7)`，随后异或 mod17 pad。

`NEGATIVE`：按此精确变换、以及把 md5/hex-of-md5 施于多种输入当 key 套工具方案，仍零命中（C-344、N-70）。
残差只剩“哪个缓冲进 aesDecode2”，以及“NfzPack 是否就是模块本体的路径”。

### 11.15 key 实为变换缓冲的 C 字符串（C-345/C-346）

`OBSERVED`：transform 循环后，其 -0x208 对象数据被 memcpy 进 -0x42f 的 std::string，`strlen` 量长后经
`QString::fromAscii_helper` 存入 -0x1d0 —— 这里 **-0x1d0 被覆盖**，成为 aesDecode2 的 rdx key；rsi 是 -0x218 原始
QByteArray。此前 -0x1d0 的 MD5-hex 串只是 `nfz before decode md5: %1` 的日志值。key = 变换输出到首个 NUL，前0x20 字节生效。

`NEGATIVE`：按此仍零命中（C-346、N-71）。残差：-0x208 是否逐字节等于密文（它由 XsBuffer append 链构建）与变换方向。

### 11.16 变换源是构建的常量容器（C-347/C-348）

`OBSERVED`：-0x208 并非密文，而是由 `XsBuffer::append` 加约20 个虚字段写入（立即数字节 dd d3 6e 81 …）构建出的
seed 对象；变换循环随后经 vtable slot0x30/0x38 读它的 data/length。故派生 key 作用在 seed 上，而 aesDecode2 的
data（rsi）始终是 -0x218 密文。

`NEGATIVE`：seed raw / transform(seed) 作 key 仍零命中（C-348、N-72）。残差是容器的序列化顺序与 data() 布局。

### 11.17 seed 形状：0x22 固定块 + 可读前缀（C-349/C-350）

`OBSERVED`：builder 先 `malloc(0x22)` 并写 0x74/0x59（ASCII `tY`），随后以负偏移 map key 继续写字段；提取的25字节
常量表为 `22 74 59 2b dd d3 6e 81 ec d4 d2 ab e2 d3 d5 dd 7a 66 f8 3a 97 ab 95 3b e0` —— 一个固定0x22 字节块、
带可读头。注意字段是以负 key 写入的，**发射顺序**未必等于列表顺序，这是当前残差。

`NEGATIVE`：各形状变体作 key 仍零命中（C-350、N-73）。下一步是按负 key 排序还原真实发射顺序。

### 11.18 setter ABI 与调用点复核（C-351/C-352）

`OBSERVED`：复核 0x68b109 调用，rdi=-0x310(sret)、rdx=-0x1d0(key)、rsi=-0x218(data)；-0x218 未被字段链触碰（链写的是另一个
-0x208 对象）。故 data=输入密文、key=变换后的 seed 字符串这一分工成立。

`NEGATIVE`：把负 key 排序并加/去前缀作 seed 仍零命中（C-351、N-74）。残余是 setter 链的 ABI 语义
（`movl $IMM,%esi` 中 IMM 到底是 map key 还是 value）。

### 11.19 路径归属：NfzPack 是 URL 抓取包（C-353/C-354）

`OBSERVED`：`DJIFirmUpgrader1::UpgradeNfzPack` 上游读 JSON `version`/`code`、本地读 `url`，并记录 strUrl 与抓取数据大小。
因此之前分析的 md5/变换/xor key 方案属于一个**远程抓取的 nfz pack**，而非本地 `.fw.sig` —— 用它直接套本地模块 chunk
可能是**类别错配**。

`NEGATIVE`：`UpgradeFirmPack`（模块路径）本体没有直接 aes/WAES/CRijndael/Imah 调用（C-354、N-75）。
下一步应确认 FirmPack 是否经 std::function 间接路由到 NfzPack，或模块另有解密 helper。

### 11.20 FirmPack 确实路由到 nfz 方案（C-355/C-356）

`OBSERVED`：`DJIUpgradeView::ProcessUpgradeFirmPack` 读 JSON VALUE/type/PACKAGE_VERSION/version，并经
`DJIWebSocketHandler::GetSafeWriter` 调用 `DJIUpgradeMgr::UpgradeNfzPack` —— 模块路径**确实**走到 NfzPack 方案，
而本地 `.fw.sig` 正是这样一份 pack 产物。故此前的类别错配担忧解除，本地 chunk 可作抓取 pack 的代理。

`NEGATIVE`：两条 NfzPack 函数体内无 base64/hex 解码（C-356、N-76），pack 字节原样入 crypto。
故 B-23 回到 seed/setter 的字节级精确性。

### 11.21 XsBuffer 布局与对象字节读（C-357/C-358）

`OBSERVED`：`__ZTV8XsBufferIcE` 槽位为 0x10=aS 0x18=D1 0x20=D0 0x28=init 0x30=append(char) 0x38=cvPc 0x40=get。
`append(char)` 返回 `this`，故链上的 `callq *0x20` 落在 D0（实参在 esi），而变换循环的 `movzbl (%rax,%rbx)` 是在
**对象自身字节**上按 rbx 索引，而非 0x8(this) 的独立缓冲 —— 意味着发射的 seed 可能含结构体指针字节，不只是追加的字符。

`NEGATIVE`：全旋转/逆序组合仍零命中（C-358、N-77）。下一步应把结构体字段字节（0x0/0x8/0x10/0x18 指针低字节）纳入 seed。

### 11.22 变换是原地、逐索引（C-359/C-360）

`OBSERVED`：`movzbl (%rax,%rbx)` 读与 `movb %r12b,(%rax,%rbx)` 写落在同一对象同一 rbx，说明是逐索引原地重写；两个
累加载入（r12/r13）都是当前字节且在写之前完成。故不存在跨迭代进位，公式确为字节局部 —— 排除了“流式链”解释。

`NEGATIVE`：方向（rol/ror）、pad（mod17/mod16/逆序）、正逆序 seed 组合仍零命中（C-359、N-78）。
下一步按 C-357 把对象结构字段字节纳入，而非继续改动公式。

### 11.23 seed 实为结构体字节（含运行时指针）（C-361/C-362）

`OBSERVED`：关键修正 —— `XsBuffer::cvPc` 是 `movq (%rdi),%rax; jmpq *0x30(%rax)`，即尾调 append 并返回 `this`；append 本身也
返回 `this`。所以读写索引的是 **XsBuffer 对象自身字节**（0x0 为 vtable 指针低字节，0x8/0x10/0x18 为指针字段），追加的字符
其实落在 0x8(this) 的 malloc 块，并未进入被索引的 seed。

即 seed 内嵌**运行时地址低字节**：静态复现需近似或模拟分配；只有前0x20 字节影响 MakeKey。

`NEGATIVE`：粗略指针近似仍零命中（C-362、N-79）。下一步改为模拟分配（固定地址/对齐）生成指针字节。

### 11.24 XsBuffer 字段布局与结构体仿造（C-363/C-364）

`OBSERVED`：XsBuffer::init 清零 0x8..0x20 与 0x18；append 从 0x18 读 len、0x10 读 cap、经 0x8 数据指针写入并自增 0x18。
故活对象恰为32 字节：vtable 指针 / malloc 数据指针 / capacity / length —— 正是变换索引的范围。

`NEGATIVE`：按该布局伪造 seed 并扫堆指针（0x7f 前缀，64×16）仍零命中（C-364、N-80）。
下一步扫更多维度（cap/len、基址前缀、栈对象而非堆），或直接以地址无关方式重读该循环。

### 11.25 指针密扫与尾字节残差（C-365）

`NEGATIVE`：把指针维度密扫（6144 组合，进程内 CDLL）仍零命中（C-365、N-81）。

关键认识：循环 `cmpq %rax,%rbx` 的上界是**长度0x2c（44）**，而结构体只有32 字节，故 seed 还含12 字节**相邻局部**；
`-0x208+44` 落到 `-0x1dc`，正好压到邻近的 `-0x1d0` 区域。所以缺的正是这12 字节的尾部成分。
下一步把邻近局部（-0x1d0 等）纳入，或改用地址无关重读。

### 11.26 attrib 位语义复核（C-366/C-367）

`OBSERVED`：四份本地 wa150 模块（0802/1200/2603/0806）一律 header_version2、enc_key STUE、chunk attrib0x0。
但 `NEGATIVE`：对四者的原始 payload 直接算 checksum，无一命中 plain_cksum（C-367、N-82）。

故 attrib 位0 在此**不能**读作明文 —— 它是工具侧的加密标志却为0，语义与工具不同；解密仍需执行。

### 11.27 strlen 截断与尾字节近似（C-368/C-369）

`OBSERVED`：key 是对变换缓冲做 `strlen` 得来；变换首字节是 vtable 低字节（40 ba 8f 00…），而 0x00 经 ror8 仍为 0，
故 strlen 约在 index3 即停。MakeKey 随后从该指针读0x20 字节 —— **越过 NUL 进入对象尾部**，即 key 的实义字节大部分来自
NUL 之后的属性存区域。

`NEGATIVE`：tail/指针/cap/len 组合仍零命中（C-368、N-83）。下一步按“NUL 后即对象字段”这一事实重排：key 应从 index3 之后
读取结构体剩余字段，而非把结构体字节当作被 strlen 截断的前缀。

### 11.28 遥控器侧 RID 侦察（C-371/C-372）

`OBSERVED`：rc331 分区裸扫里，`rid_enable`/`RID_ENABLE` 其实是视频编码属性 `layer_wise_rc_enable`；`RemoteId` 是
AOSP/Chromium 类 —— 都不是 Remote ID。`DJI_FLY.apk` 仅以路径出现（附近4MB 无 `PK` 魔数），故 apk 本体在 /data/app、
不在 OTA。`NEGATIVE`：分区裸扫不足以拿开关（N-85）。

正解：改用仓外的 DJI Fly dump（同一 App 版本）找 RID 开关/参数，rc331 分区只作 native/config 佐证。

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

### 11.31 遥控器侧命中 RID 开关处理器（C-377/C-378/C-379）

`OBSERVED`：Ghidra headless 定位到真正的 RID/EID 开关访问器 —— 自由处理器 `EIDSwitchGet`（0x04e12d44）与
`EIDSwitchSet`（0x04e12f80），签名 (KeyHandlers*, Characteristics const&, shared_ptr<UavValue>, callback)；Set 会
`__dynamic_cast` 校验类型、不匹配返回 -6。

`OBSERVED`：两者及其 `UAV77FlightControllerAbstraction::GetEIDSwitch/SetEIDSwitch` 包装（0x02d9ad3c / 0x02d9afa0）
都构造 `uav_cmd_base_req`，置 local_76=0x77、local_74=3、local_71=3 再 local_71=0x12、local_7c=4，并调用
`uav_cmd_req_header::SetReceiverIndex`；Get 置 local_48=2、get/set 标志0，Set 由值头取 local_48、标志1。

`OBSERVED`：`OIDIdentifierGet/Set`（0x04eabadc / 0x04eac2fc）为同级处理器，`ComplianceSerialNumberInit` 在 0x02e36740，
即整套 RID 参数族都在遥控器侧（C-379）。

下一步：解出各常量语义与值字节布局，形成可下发的 set 报文。

### 11.32 eid_switch 请求语义解码（C-380/C-381/C-382）

`OBSERVED`：反编译出的模板实例直接给出常量 —— `uav_cmd_base_req<(unsigned_char)1,(unsigned_char)3,(unsigned_char)119,
uav_fc_handle_eid_switch, uav_fc_eid_switch_status>`，包装层调 `SendGetPack<uav::core::eid_switch_pack>` /
`SendSetPack<...>`。即请求 = cmd119、sub3、attr0x12，回复标签 `uav_fc_eid_switch_status`，载荷类型为
`uav::core::eid_switch_pack`（含 `RspType`）。

`OBSERVED`：EIDSwitchSet 的载荷是**单个启用字节** —— 它对 `shared_ptr<UavValue>` 做 `__dynamic_cast` 后读
`*(undefined1 *)(lVar6 + 8)`（C-381）。Get 侧则硬编码 local_48=2。

于是"关 RID"在报文层就是：对该 opcode 下发一个值为0 的 set。

### 11.33 base_req 布局与 receiver/sender 分工（C-383/C-384）

`OBSERVED`：eid_switch 的 `uav_cmd_base_req` 构造函数给出头部布局 —— `this[0..3] = 01 03 77 02`（模板1、模板3、cmd119、0x02），
`+1..8` 为 `00 00 00 00 02 00 00 03`，`+0xc` 为 `00 00 49 57`（ASCII `'I','W'` 魔数），`+0x14` 超时500，`+0x10/+0x18` 置0，
`this[6]` 取自 `GlobalPacketStatus::GetGlobalSenderIndex()`，`+0x20` 构造 payload Buffer。

即：**sender index 自动派生**；`SetReceiverIndex` 为外部 thunk（0x0515dc90，经 PTR 解析），由包装层在填好 local_48（Get 为2、
Set 为值字节）后调用 —— **receiver index 由调用方给**（C-384）。

于是报文 = 该头部 + 载荷字节；关 RID 即 Set、值0、receiver 按调用方取。

### 11.34 receiver 来源与发送出口（C-385/C-386）

`OBSERVED`：`SendSetPack` 从 Characteristics 参数读 `param_2[0x30]` 作为 receiver index（Get 用自己的槽），说明
receiver 是**特征属性**、不是自由常量。

`OBSERVED`：两个 Send 都以 `(**(code **)(*(long *)this + 0x128))(this, req, cb, 1)` 收尾 —— 发送走 concrete 抽象的
虚槽 `0x128`；UAV77 类经 `FlightControllerAbstraction` 成员指针绑定。

故报文全要素已定：cmd119/sub3/attr0x12/'IW'/timeout500/sender 自动/receiver=Characteristics+0x30/载荷1字节。

### 11.35 传输出口命名（C-387）

`OBSERVED`：全函数清单把槽0x128对应到 `uav::sdk::BaseAbstraction::SendPack`（两个重载 0x02618fc4 / 0x02619118），
另有 `uav::sdk::key::BaseAbs::SendPack`（0x028bfee0）。更底层核心传输是
`uav::core::UavCoreCancelation::SendData(string const&, unsigned_short, uav_cmd_req const&, rsp cb, cancel cb, bool)`，
并经 `queue<pair<uav_cmd_req, function<void(int)>>>` 排队。

即：发送链 = SendSetPack → slot0x128 SendPack → UavCore SendData → 队列/链路。

### 11.36 EIDSwitch 注册与连接前置（C-390）

`OBSERVED`：`FUN_032ba30c` 构造名为 `"EIDSwitch"` 的 `CharacteristicsElement`，装入 `PTR_EIDSwitchGet_0532e518` /
`PTR_EIDSwitchSet_0532e520` 的 get/set 函数对，再调 `uav::sdk::key::BaseAbs::InsertCharacteristics(param_1,
"EIDSwitch", element)`。

即：App 是**按 SDK key 名**访问该开关（不是直接发 opcode）；characteristics 与 receiver 管线由这条 key 路径填充。
这解释了 receiver（Characteristics+0x30）来自会话环境，而非固定常量 —— 连接前置就是"设备已连、key map 已插入"。

### 11.37 rc331 侧 native 佐证（C-392/C-393）

`OBSERVED`：vendor.img 的名称池列出 `dji.go.v4`、`dji.go.v5`、`dji.prof.mg2`、`dji_logs`、`dji_v1_protocol`、`djilink`；
system.img 日志串显示 `hdvt_lte: inform djilink ...` / `failed to inform djilink`，并有 `dji_link` 的 stream_conf 条目 ——
即 RC 上存在 **native 链路守护进程**，App 的协议路径有其对端。

`OBSERVED`：system.img 的 launcher JSON 里有 `start dji_link` 与 `pkill -9 dji.go.v5`（在 download pretender 下），
说明开机先起 djilink、再拉起 DJI Fly（C-393）。

这坐实了连接前置的性质：报文最终经 App → djilink/dji_v1_protocol → 链路，而非直连飞机。

### 11.38 dji_link 本地通道与路由表（C-394/C-395）

`OBSERVED`：vendor.img 内嵌 `dji_link_services` → `mb_route_table` JSON。其中 `"dji_link"` 下的 `"00"` 项 status1、
target `whoami`、channel **`local`**、protocol **`logic`**，并有 `local.direct_host=whoami`；同级还有 `dummy`（bulk/UEvent）
与 `"10"`（camera, bulk, protocol v1）。表头 host 为 `mobile`、index5。

`OBSERVED`：dji_link 串包含 `dji_link_init_localsocket_to_app`、`dji_link_send_stream_via_localsocket`，日志
`app socket thread start ---- localsock_fd = %d, accept_fd = %d` —— 即 djilink **监听并 accept 来自 App 的本地 socket**。

于是连接前置具体化：App 经本地 socket + `logic` 协议进程内递送到 djilink，再由 djilink 走 bulk/USB 到飞机。
`SendData` 排入的就是这条链。

### 11.39 unix socket 命名与 whoami 语义（C-396）

`OBSERVED`：dji_link 串含 `dji_link unix_socket_listen create socket = %s` —— 监听 socket 名由配置/源码提供，不是写死字面量。
本地路由的 `direct_host` 为 `whoami`，同树源文件为 `hardware/dji/service/dji_link/src/dji_whoami.c`（即"本机自身"）；
`vt_gnd` 是另一虚拟地面主机、用于其它本地路由。

故 App 侧抽象 socket 名很可能就是 `direct_host` 值 `whoami`，而非新常量。
