# RedFly build-245 静态检查

2026-10-18，C-476--C-479。用户提供的安装包包含可直接分析的改版 Fly Java 代码，以及具体的 RID 云控拦截、GPS 和日志导出实现。这些是有用的新线索；本次没有安装、启动软件或连接设备，没有验证 Mini 5 Pro 的标准 Remote ID 广播效果。

## 样本与分析范围（C-476）

| 对象 | 固定身份 | 用途与边界 |
| --- | --- | --- |
| A-104 | RedFly Test Installer build-245；487,007,201 B；`app.redfly.installer` | 用户提供的第三方安装包，原件未修改 |
| A-105 | 内嵌 `redfly-v6.apk`；467,603,237 B；`dji.go.v6`；code 3116079 | versionName 自述基于 1.21.10、build-236；该标签不证明官方来源或功能有效 |
| A-031 | 内嵌 `utilities.apk`；8,849,471 B | 与已登记的 DJI Fuli APK SHA-256 完全相同，不是新的提权载荷 |

A-104/A-105 的签名校验通过，签名证书 SHA-256 均为 `4e1971daed82fe2025dd7f3e3bd5a493c9d79c00c1fb70845d623ee63a17e781`。三个辅助 APK 的证书摘要为 `a4aa1cdd2ea580cbbe67486b5f6f3cfea83f488889995afa70793daa516687da`。签名匹配不证明当前设备允许安装或授予权限。

A-105 包含 32 个普通 DEX，共 176,976 个 class_def。32 个文件的长度、SHA-1 与 Adler-32 均匹配。格式化指令引用扫描遍历 1,063,288 个方法体；随后只反编译相关类。它提供了这份改版的可读实现，不能替代原版 A-006 的精确版本证据，也不构成全应用审计或 ART 运行验证。

A-105 仅含 ARMv7 native 库，现有官方 A-006 对照仅含 ARM64 库，因此没有用两者的二进制差异归因 native 补丁。完整包身份、DEX 摘要和方法位置见 [独立证据索引](../evidence/redfly-build245-static.json)。

## RID 选项实际做什么（C-477）

`flysettings.S.ridKill()` 从 SharedPreferences 读取开关，缺省为 **true**。已定位的路径如下：

| 入口 | 静态行为 | 对现有研究的意义 |
| --- | --- | --- |
| `UAVRidCloudControlLogic.E/M` | 开关为 true 时提前返回，跳过连接时订阅及 `CloudControlData(18,4,string)` 写入 | 找到了拦截既有云控发送者的具体位置；没有生成替代策略或解析签名正文 |
| `UAVRidBroadcastEffectCloudControlLogic.N` | 开关为 true 时调用 `Rid.onConnect()` 并跳过广播质量云控订阅；断开时调用 `Rid.onDisconnect()` | 显示改版接入连接生命周期的位置；原质量分支通向 `CccBroadcastSignalQuality` |
| `ridkill.Rid.droneIdCycle()` | 将八个布尔项全部置 false，发送两次 SetSwitch；首轮前后各 GetSwitch 并打印结果 | 当前包的 `DataFlycDetection` 明确落到 `0x03/0xDA`、子命令 5/6，是既有 legacy DroneID mask 路线 |
| `ridkill.Rid.eidOff()` | 通过 SDK `EIDSwitch` 键设置 false，等待 SET 回调 | 同包 native EID setter 仍使用 `0x03/0x77` 与 `eid_switch_pack`，对应已知 France EID 平面 |

连接后延后 1 秒开始；每轮完成后再延后 12 秒调度。GET 结果仅打印，未校验目标 mask，也未保存原值；发送失败/超时可记录后继续。EID 成功依据是 SET 回调，没有 EID GET 或 RF 读回。

关闭选项或断开连接会移除待执行的周期任务；没有恢复原 mask/EID 值、恢复读回或等待在途请求结束的逻辑。`firstCycle` 在所查类中没有随重连重置。界面也要求改动后重连，不能把这个 UI 开关当成已完成的可逆设备控制。

广播质量的 guard 位于连接入口；切换选项本身不会重建被跳过的订阅或销毁已有质量订阅。普通 RID 云控写入 `M` 则再次检查当前开关值。这两个 guard 的生效时机应分别记录。

这些静态事实不证明 Mini 5 Pro 接受相关命令，也不证明屏蔽云控写入会改变已应用策略或标准 BLE/Wi-Fi RID。C-203 的 legacy DroneID 边界、France EID 与全局 RID 的区别，以及本项目逐项 owner/基线/读回/恢复/RF 要求均保留。

## 安装器与辅助工具（C-478）

安装器使用本机 ADB。RC2 路线要求最终读到 UID 0：它先尝试已有连接，再以安装器自身进程调用属性工具；只在 `dbg_cnt` 为空时请求设置，保留所有非空值。外层没有提供新的 Binder 提权、adbd 补丁或 native 注入实现。属性写权限、SELinux 以及实际 root 结果仍未验证。

失败后的人工入口是原有 Fuli Shell。其页面启动时的 `adb shell su` 探测，与用户输入走的普通 `Runtime.exec(String)` 是不同调用；不能把后者自动视为 root。RC Pro 分支明确匹配 Enterprise/rm510/SDK29，不能泛化到所有 RC Pro。

原版 APK 备份、哈希核对和重新安装是真实代码，但未备份 app data，也未回滚 ADB、权限、共存设置及辅助包。另有 10 项 RC2 媒体资源种子，属于界面素材。外层检查不覆盖主 APK 的全部 OTA/保护行为。

## GPS 与飞行记录（C-479）

| 模块 | 已核实的行为 | 验证边界 |
| --- | --- | --- |
| 遥控器 GPS | `gpskill.G.setKilled` 写 Android `Settings.Secure.location_mode`；相关 UI 读该状态 | 是 RC 定位设置，不是飞机位置或 RID 操作者位置编辑器；实际权限与效果未知 |
| 飞机 GPS | `flyctl.F.writeGps` 使用 `FCGPSEnabled`；RC2 还进入 `Flyc.sendGps` 的参数发送路径 | RC2 分支先更新本地状态，重复发送但不读 ACK，并吞发送异常；true/UI 不能证明飞机接受。非 RC2 分支另有 SET 回调和读回尝试 |
| 飞行记录导出 | `frtool.Decryptor` 调用 `UavJNIFlightRecordUIMapConvertor`，经 `libuavfr` 及所依赖的 FR 库解析，再将 `MapDetailData` 写成 JSON | 导出地图/轨迹数据，不是全量原始日志，也不是 RC331 TBIE 或 WA150 STUE 固件解密器。未输入用户日志或执行 native 解密 |

文件扫描接收 `.txt/.DAT/.dat` 后缀，但都进入同一 UI-map parser；包内帮助明确写飞机 `.DAT` 尚不支持，不能由扩展名推断能力。导出字段可含飞机、home、用户位置，应继续作为私有材料保存。独立合成 protobuf 检查只验证所建模的导出形状，未验证真实解密。

## 可继续利用的部分与证据定位

优先利用这份改版的可读 Java 和已定位的云控入口，针对尚缺的原版方法做逐项对照；同时保留原版版本及 ABI 边界。安装器提供了清楚的访问前提和 APK 恢复流程参考。GPS 的本地状态与设备状态分离、RID 缺少原值恢复，也给后续面板设计提供了具体反例。

| 证据 | 位置（均为所属未压缩 DEX 内 code_item offset） |
| --- | --- |
| RID 云控 guard | `classes20.dex`：`E` `0x518950`、`M` `0x518548` |
| 广播质量连接/断开 hook | `classes20.dex`：`N` `0x517d34`、`U` `0x517e00` |
| 开关缺省/变更 | `classes27.dex`：`ridKill` `0x666c40`、`setRidKill` `0x667010` |
| mask/EID 周期 | `classes28.dex`：`droneIdCycle` `0x2ba28`、`eidOff` `0x2bb58`、`onSettingChanged` `0x2bf38` |
| Detection 构造/发送 | `classes12.dex`：`doPack` `0x462bb4`、`start` `0x463b98` |

19 个方法由独立 class_data 解码定位，其中 18 个外层方法的 offset 与 JADX API 一致；匿名 `run` 来自原始 class_data、指令引用及父类合并反编译，单独按 `$1` 查询未解析。Native 只检查同包 EID Get/Set 的固定符号范围，并通过 ARM PLT/GOT relocation 确认 request constructor 与 `SendSetPack<eid_switch_pack>`；没有将静态调用当作运行期绑定。

本次保留的原始 APK、DEX、SO、反编译代码和原始日志均在仓库外，不分发；仓库只记录独立文字、摘要和位置。REA archive evidence 为 `ev_90b311b344b353decd96a82ff08f075f4262ae62d5b6cba057281af8f0505ac7`，其完整导出仅供本地复查。未发现于所查模块的能力不外推为全包不存在。RC331 TBIE root input、WA150 STUE 与实机/RF 验收缺口不因本样本而关闭。
