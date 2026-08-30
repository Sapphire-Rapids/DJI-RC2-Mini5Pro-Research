# RC 2 实机环境与加载进展

更新日期：2026-08-31。研究对象为 RC 2（界面固件 `07.00.0100`）与 Mini 5 Pro
（操作者确认固件 `01.00.0600`）。本页汇总 C-235--C-267；行动顺序见
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
| 目录内容 | 七个子目录；拟用 `finduas_A040_canary.so` 文件名未出现 | C-249 |
| Shell 报告回传 | F2 已运行，报告完整读回；源文件校验通过，只有 pidof 未取到进程 | C-257 |
| Fly 进程 | AMS 已返回名称精确为 dji.go.v5、PID 非零的 HOME 主进程记录 | C-258 |
| 自动诊断 | B1 已启动；PING → F4 → PING 三项自动往返成功，F4 报告已严格解析 | C-266、C-267 |

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

`OBSERVED`：操作者发送 `ls -laZ /data/app` 一次，两张相互重叠的照片覆盖列表首尾。
共有七个子目录：`DJI_FLY` 为 system:system、0777、apk_data_file；其余六个 Android
随机安装根为 system:system、0775、同一标签。拟用的 `finduas_A040_canary.so` 文件名未出现
（C-249）。既有报告已记录 Fly 的固定 APK 与 native-library 位置，不再重复检查这些路径。

`STATIC`：A-040 是独立的 ARMv7 ART TI 加载测试，仅请求接口版本 `0x70010200`、
查询版本并输出一次结果，不枚举类或发起飞机查询。10 项 fake-VM 测试通过，4 个故障
变体被拒绝，ARMv7/ARM64 均构建成功。ARMv7 文件已在 SD 卡回读核对，未复制到内部路径
或执行（C-243）。源码与命令见 [实验目录](../experiments/jvmti/jvmti_flysafe_inprocess_query/README.md)。

`OBSERVED`：8 个已被替代的研究 APK 已移至 `Download/FindUAS/Archive/`，文件名和大小
清单前后一致，没有删除文件。A-039、原版 Fuli 和当前工具留在 Download（C-244）。

## F1 一次性报告收集

`STATIC`：独立脚本 A-043 合并调用方身份、固定系统属性、已有 Fly 进程身份、PID/starttime
前后检查与 SD 上 A-040 的大小/哈希读取。仅在当前 SD 的 `Download/FindUAS/Probe/` 新建
报告，已有同名文件不覆盖；每条命令保留退出码和错误输出。独立源码审查、shell 语法、
三个实际 Java `Runtime.exec(String)` 启动用例及七个主机 shell 模拟场景通过（C-250）。

`OBSERVED`：`Download/F1.sh` 已经 RC 2 MTP 暂存，完整回读与源码逐字节一致：7,196 bytes，
SHA-256 `636a57319d6b53e874324adb67c6eab4b79fd73d703588e7a52e51bc1a381ece`（C-251）。
`OBSERVED`：操作者执行下方原定启动命令，照片确认输入一致。内层 `sh` 报告字面路径
`/storage/????-????/Download/F1.sh: No such file or directory`，没有出现 F1 标记；脚本尚未
进入采集。接下来读取调用方能看到的存储入口（C-252）。

原定命令保留作记录，当前不重复执行：

```text
sh -c (sh${IFS}/storage/????-????/Download/F1.sh)2>&1
```

`OBSERVED`：随后用合并 stderr 的命令列举 `/storage`，照片明确返回
`ls: /storage: Permission denied`（C-253）。因此先读取父目录的权限/标签与系统 volume
信息，再选择脚本入口；F1 源码与 SD 上的文件仍保持 C-251 的同一身份。

## F2 精确路径与报告回收

`OBSERVED`：随后读到 `/storage` 为 0710、shell:everybody、mnt_user_file，并通过系统
存储接口得到唯一 mounted public 卷。C-246 中的调用方组可穿过父目录，但无法列举它；
卷标识仅保留在私有记录（C-254）。

`STATIC`：F2/A-044 去掉全局 `/storage` 枚举，保留原有固定读取和报告写入范围。独立
差异检查及八个主机用例通过，包含不可列举、可穿过父目录的真实 host 权限场景（C-255）。
`OBSERVED`：6,845-byte 脚本暂存及完整回读一致；旧 F1 移入 Archive，移动前后读回一致（C-256）。

`OBSERVED`：操作者按精确路径运行 F2，报告保存后由主机经 MTP 完整读取，大小 2,553 bytes，
schema、各段退出码和结束标记通过验证。十二条命令中，只有 `pidof dji.go.v5` 返回 1 且无
输出，因此报告为 `INCOMPLETE`。其余十一项成功：system/system_app 身份保持一致，SELinux
为 Permissive，`ro.debuggable=1`、`wifi_on=0`；A-040 源文件大小前后均为 4,340、哈希匹配。
报告记录的协议请求、attach、内部复制次数均为零（C-257）。

脚本采集前读取的时间换算为 Asia/Shanghai 的 2026-08-31 03:12:47。目标 PID 分支未进入，
随后查看系统服务持有的单包进程记录，无需重跑 F2。

`OBSERVED`：三秒超时的 `dumpsys activity -p dji.go.v5 lru` 返回 AMS 标题与一条 HOME
主进程记录，进程名精确为 `dji.go.v5`，PID 非零（C-258）。具体 PID/UID 仅保留私有。
这提供了下一次直接进程路径读取的目标，不需要重新打开 Fly。

`OBSERVED`：下一张照片中，对先前 PID 的 `attr/current` 读取返回 `No such file or directory`。
画面没有挂载选项行，输入框仅显示水平滚动后的末尾（C-259）。接下来把前后 AMS 记录及
进程文件读取放进同次 F3 报告，补齐连续性与完整错误输出。

## F3 原始报告与兼容性修复

`OBSERVED`：操作者运行 F3 后，主机经 MTP 完整收到 3,677-byte 原始报告（C-262）。
两个原始 AMS 段包含同一个 Fly 主 PID。`/proc` 挂载参数为 `gid=3009,hidepid=2`，
调用方附加组不含 3009。AMS 解析函数中的 heredoc 两次尝试在 `/data/local` 创建临时
文件而被拒，目标 proc 分支因此跳过；这两行 shell 错误位于段框架外，严格解析器据此拒绝
原始格式。原始文件和错误均保留，派生诊断另存并注明处理步骤。

`STATIC`：F4 改用 `printf` 管道把 AMS 内容交给解析函数，去掉临时文件依赖。
Android mksh 的 18 个完整场景和 12 个临时存储对照通过（C-263）。F4 为 10,607 bytes，
已经经 MTP 放到 `Download/F4.sh` 并完整回读一致；后续 B1 执行结果见 C-267。

## B1：一次启动后的 SD 任务收发

`STATIC`：B1/A-047 从启动脚本所在 SD 读取会话，接收 `PING`、`SNAPSHOT` 和 `STOP`。
会话持续至多一小时、最多 64 个顺序任务；任务与完成记录绑定会话、序号、大小和 SHA-256。
`SNAPSHOT` 只执行哈希固定的 F4 内存快照，结果保存后由主机回读。Java `Runtime.exec`
实际启动模型验证了页面输出可快速结束、后台 worker 继续工作。十一个 mksh/Java 场景、十九个客户端测试
和主机传输器检查通过（C-264）。实现和可复现测试见
[主机工具](../host-tools/rc2-sd-bridge/README.md)。

`OBSERVED`：F4 和 B1 已经 MTP 暂存并完整回读，分别为 10,607 和 9,417 bytes，哈希与
A-046/A-047 一致。会话目录准备完成，active 记录最后发布；当时读取为等待启动（C-265）。
两次较早准备在只读路径查询时报 PTP I/O 错误，未发布新 active；保留同一会话标识并加入
一秒调用间隔后准备成功。此处尚无任务执行结果。

## 自动往返与 F4 实机结果

`OBSERVED`：操作者启动一次后，主机读到 B1 READY，随后顺序发出 PING、SNAPSHOT、
PING 三个任务。每项先校验上传的 job，再发布 ready；收回 accepted、完整 report、done
后核对会话、序号、长度、SHA-256 和返回码。三次 handler 返回码依次为 0、10、0；最后
PING 在 F4 收齐后新发出并得到正常响应（C-266）。会话继续使用原来的一小时/64 项上限，
此次没有发送 STOP。

`OBSERVED`：SNAPSHOT 保存的 F4 报告为 4,036 bytes，严格 schema、各段返回码和结束
标记校验全部通过（C-267）。前后 AMS 解析均为 0，主 PID 一致，`ams_pid_stable=true`；
没有再出现 heredoc 临时文件错误。两次 pidof 和六次目标 proc 读取均返回 1，
`proc_starttime_stable=unknown`；其余十五条命令成功。挂载仍为 `gid=3009,hidepid=2`，
调用方不含该读取组。A-040 SD 文件大小/哈希匹配，内部 canary 文件名仍未出现。
因此当前 INCOMPLETE 对应明确的进程文件可见性失败；数据回传与 AMS 解析已经完成。

## 下一步

当前不需要新的人工命令或截图；保持开发助手页面与 USB 连接即可继续使用当前诊断会话。
会话不会跨重启，并在启动一小时后结束。下次任务先检查原会话状态，保留原始 host state，
不要丢弃未完成的任务编号或重放已接受的任务。

研究下一步是解决目标进程自身信息的读取与合法加载路径；现有 F4 已完成其诊断任务，
不再重复相同的 pidof/proc 查询。内部 payload copy/attach 仍未进行。现有 B1 操作集为
PING/SNAPSHOT/STOP；增加后续研究操作时须单独审阅实现和对应基线。

按操作者最新要求，进度仅同步本地仓库，暂停 GitHub 推送。

私有材料的定位类别见 [排除日志索引](15_LOG_INDEX.md)。
