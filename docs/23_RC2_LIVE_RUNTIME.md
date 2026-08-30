# RC 2 实机环境与加载进展

更新日期：2026-08-31。研究对象为 RC 2（界面固件 `07.00.0100`）与 Mini 5 Pro
（操作者确认固件 `01.00.0600`）。本页汇总 C-235--C-248；行动顺序见
[时间线](03_TIMELINE.md#2026-08-31)，工件身份见 [工件登记](11_ARTIFACT_REGISTER.md)。

## 当前进度

| 项目 | 结果 | 证据 |
| --- | --- | --- |
| 实机软件身份 | DJI Fly `1.19.4` / code `3113157`，APK ABI 为 `armeabi-v7a` | C-235、C-237、C-238 |
| SD 回传 | v0.11/v0.12 报告已收到；实机 APK 和三份 SDK 库已完整校验 | C-235--C-238 |
| Android/ART 检查 | v0.12 为 `COMPLETE`，32 位 GNU build ID 解析成功 | C-237 |
| 官方调用链 | FlySafe 查询与独立 RID 工作状态链均已在实机版本中定位 | C-239、C-240 |
| 开发助手 | 原包已安装；新报告确认 updated-system、原身份保持一致、三个入口启用 | C-241、C-242、C-245 |
| Shell 身份 | `id` 实测 UID/GID 1000（system），域为 `u:r:system_app:s0` | C-246 |
| 目录基线 | `/data`、`/data/app` 均为 system:system、771；后者标签为 `apk_data_file` | C-247 |
| 同进程加载 | ARMv7 ART TI canary 已构建、测试并放到 SD 卡；尚未执行 | C-243 |
| 当前操作 | Shell 执行 `ls -laZ /data/app` 并回传，核对测试文件名是否占用 | C-247、C-248 |

本轮尚未执行 RID 切换。操作者说明未办理解禁，证书页面的人工查看已暂缓；后续优先
观察独立 RID 工作状态，FlySafe 清单不作为继续研究的前提。

## 两次报告与版本纠正

`OBSERVED`：A-038 v0.11 的报告经 RC 2 可移除 SD 卡、USB MTP 回传，文件完整。
两个原有检查段完成，ART 段停在 `ELF_BUILD_ID_FAILED`。代码只接受 ELF64，而实际探针
进程与所读 ART 为 32 位；实机 Fly 也只有 ARMv7 APK 库（C-235）。

`STATIC`：A-039 v0.12 增加 ELF32 解析、组件运行时 enabled override 查询，以及固定样本
导出。94 项 JVM 测试、8 项审计器测试、37 个被拒绝的故障变体、两次相同的 clean build
及签名/对齐检查通过；详见 [v0.12 审查](../apps/rid-admission-probe/REPORT_EXPORT_V12.md)
（C-236）。

`OBSERVED`：v0.12 报告为 `COMPLETE`。两次报告中 ART 文件大小和 SHA-256 相同：

- 大小：`7,094,912` bytes。
- SHA-256：`d58073daf219b39c744c91297e0b1d05b4530fbb01b4778dee7fe3a2cfec4b76`。
- v0.12 读出的 GNU build ID：`fdb09b8d18c509b1c69a238d28f4c316`。

旧 64 位 profile 为 `DIFFERENT`，其固定范围检查保持 `NOT_APPLICABLE`。报告还读取到
Android SDK 30、`ro.debuggable=1`、SELinux enforcing=false、`mp_state=production`；
`dbg_cnt` 返回空字符串。Fuli 三个组件从旧版误报的 `ABSENT` 纠正为
`EXPORTED_DISABLED` / `PRIVATE_DISABLED` / `PRIVATE_DISABLED`（C-237）。

两次检查均未发送飞机协议请求。正向对照包括系统服务 descriptor 匹配、两次 ART 文件
身份一致，以及随后取得的 APK 内 JNI 库与安装目录文件一致。此次未进行 RF 实验或状态
恢复操作；完整报告与运行标识保留在本地。

## 实机样本

`OBSERVED`：A-039 按固定版本和文件名导出 APK 及三份库。主机校验 ZIP、manifest、
逐文件大小/SHA-256、APK 版本/ABI/签名，并比较 APK 内库与安装目录导出库（C-238）。

| 文件 | bytes | SHA-256 |
| --- | ---: | --- |
| DJI Fly 1.19.4 APK（A-041） | 426180752 | `fb695817a885bd9d4084643d8cae07285a8ac560b6e94edd5c87af4a70b8528c` |
| `libsdk_jni.so` | 66957340 | `e1857df480ad312b536289a848bcc545f38f70f36076c04f862720e646d982bd` |
| `libsdk_key_value.so` | 10041476 | `e36123b638baf18d15367f8962048e34e537c2c52da04a55078fcb707e6a5086` |
| `libsdk_base.so` | 6545956 | `6ff8fdd8f77f7f556d29665bb7671ded8358f8757b052ee2c064f7a778b3efcc` |

本地 MTP 读取器最初把含 16 字节协议开销的末次进度误判为超量，传输返回错误；已经落盘
的完整 payload 另取快照并通过上述全部校验。读取器已修正，13 个离线边界向量通过，未要求
操作者重新导出。计数依据为 [libmtp 1.1.23](https://github.com/libmtp/libmtp/blob/55fa074240b703adb48c78d31d156879cb9e4959/src/libmtp.c#L5423)。厂商 APK、库、ZIP 和工具原始输出不发布。

## 实机版本的两条读取链

`STATIC`：FlySafe 路径为 `FlightRestrictImpl.m` → `queryFCLicensesJni` →
`native_queryFCLicense` → `libuavfs_jni` → `libflysafecore::QueryFCLicenseInfo`。
Java owner、JNI descriptor、回调及成功 envelope 与现有独立解析器一致。当前设备 ID
初始化为 `-1`，ARM32 JNI 桥将其符号扩展；查询程序在保留零值检查的同时增加 `-1` 拒绝，
并提供 ARMv7 构建（A-042，C-239）。

`STATIC`：独立 RID 状态链为 `11/1C` → `RidImportModule` →
`KeyRidWorkingStatusPush` → `RemoteIDModelImpl.getWorkingStatus()`。实机版本由基础
`FlightControllerAbstraction::PrepareModules` 挂载，读取七字节状态前缀；该 handler 未见长度
检查，独立解析器仍需至少七字节并保留尾随内容。
模型存在全 false 初值和缓存重放；后续观测需要区分初值、缓存与新 push。`RxCSDK.U`
返回监听 handle 的静态入口已定位，其深层调度和取消行为仍需核对（C-240）。

`00/DD` cloud-control 是另一条写入链，不纳入当前状态观测。此前 1.21.10 的模拟器结果
继续保留其版本标签，实机后续以 A-041 为准。

## 开发助手入口与加载准备

`STATIC`：实机匹配的 services/framework 显示，生产模式启动策略把 Fuli 整包设为
`DISABLED=2`；普通设置页的平台签名限制又使主启用按钮不可用。标准安装器允许原平台
签名的同版本替换，安装成功收尾把 enabled override 设为 `DEFAULT=0`。
“卸载更新”可恢复 vendor 原包，重启后既有启动策略再应用禁用状态（C-241）。

`OBSERVED`：A-031 原始包以 `Download/RC2_FULI_ORIG.apk` 放入 SD 卡，完整 MTP 回读
哈希匹配。操作者当时确认安装后开发助手可正常打开，未点击内部按钮（C-242）。

`OBSERVED`：随后通过同一 RC 2 可移除 SD 卡 MTP 收到安装后的 A-039 报告，结果为
`COMPLETE`，报告时间换算至 Asia/Shanghai 为 2026-08-31。Fuli 的 updated-system 标志为 true；版本 code
155、APK SHA-256、平台签名与两份已检查 DEX 保持一致。三个固定组件分别为
`EXPORTED_ENABLED`、`PRIVATE_ENABLED`、`PRIVATE_ENABLED`。Fly 1.19.4/ARMv7 及
ART 文件身份不变。目录 `ABSENT` 是 Observer 进程所见，另以直接 Shell 读取补齐（C-245）。

`OBSERVED`：操作者进入“开发助手 → shell命令测试”，输入 `id` 并发送一次。
照片显示 `uid=1000(system) gid=1000(system)`、`context=u:r:system_app:s0`，附加组
包括 log、reserved_disk、external_storage、net_bt_admin、net_bt、inet、net_bw_acct
和 everybody（C-246）。该身份来自实际命令输出。

`OBSERVED`：随后同页发送一次 `ls -ldZ /data /data/app`，照片中的命令与两行输出
一致（C-247）：

| 目录 | 权限 | 所有者/组 | SELinux 标签 |
| --- | --- | --- | --- |
| `/data` | `drwxrwx--x`（771） | system:system | `u:object_r:system_data_root_file:s0` |
| `/data/app` | `drwxrwx--x`（771） | system:system | `u:object_r:apk_data_file:s0` |

两条命令各执行一次，均已返回；未测耗时和单独退出码。正向对照为命令文本、预期身份行与
两个明确目录行相符。此次只读取元数据，无需恢复；测试目录/文件尚未创建，目标进程域、
加载与新 RF 数据尚待取得。原始照片及目录时间等元数据仅保留本地。

`STATIC`：已匹配 services 中，PackageManager 的 `scanDirLI` 把目录或 APK 作为包候选；
非系统包扫描失败可进入删除路径。`systemReady` 调用的 `reconcileApps` 也会清理未登记的
目录。普通非 `.apk` 文件由这两处候选判断跳过（C-248）。输入 services.jar 的 SHA-256 为
`1372cd839fc8f495d4e166bd4f29e08a446ca7fcd4154bfa642174ca4e7352ed`，与实机报告匹配。
因此不采用新建子目录的方案；
直接放置独立 `.so` 普通文件的候选见 [H-32](10_HYPOTHESES_AND_UNKNOWNS.md#h-32--the-remaining-loader-problem-is-a-callertarget-path-policy-intersectionc-208--c-211)。

`STATIC`：A-040 是独立的 ARMv7 ART TI 加载测试，仅请求接口版本 `0x70010200`、
查询版本并输出一次结果，不枚举类或发起飞机查询。10 项 fake-VM 测试通过，4 个故障
变体被拒绝，ARMv7/ARM64 均构建成功。ARMv7 文件已在 SD 卡回读核对，未复制到内部路径
或执行（C-243）。源码与命令见 [实验目录](../experiments/jvmti/jvmti_flysafe_inprocess_query/README.md)。

`OBSERVED`：8 个已被替代的研究 APK 已移至 `Download/FindUAS/Archive/`，文件名和大小
清单前后一致，没有删除文件。A-039、原版 Fuli 和当前工具留在 Download（C-244）。

## 下一步

1. 安装后报告、Shell 身份与两个父目录的权限/标签已收到，不再重复这些检查。
2. 当前 Shell 输入 `ls -laZ /data/app`，点“发送”并回传照片，核对拟用文件名是否已占用。
   再完成独占创建/复制、实际文件校验及加载前目标进程身份检查。
3. 先验证纯 canary 的成功标记与 Fly PID 稳定，再推进独立 RID 状态观测。

按操作者最新要求，进度仅同步本地仓库，暂停 GitHub 推送。

未采集新的无线广播数据；起桨由操作者另行控制。私有材料的定位类别见
[排除日志索引](15_LOG_INDEX.md)。
