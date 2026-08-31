# RC 2 实机环境与加载进展

更新日期：2026-08-31。研究对象为 RC 2（界面固件 `07.00.0100`）与 Mini 5 Pro
（操作者确认固件 `01.00.0600`）。本页汇总 C-235--C-309；行动顺序见
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
| 同进程加载 | 新 A-048 已在原 Fly 进程成功运行；身份/API/释放均正常，文件已回收 | C-274、C-275 |
| 目录内容 | 七个子目录；拟用 `finduas_A040_canary.so` 文件名未出现 | C-249 |
| Shell 报告回传 | F2 已运行，报告完整读回；源文件校验通过，只有 pidof 未取到进程 | C-257 |
| Fly 进程 | AMS 已返回名称精确为 dji.go.v5、PID 非零的 HOME 主进程记录 | C-258 |
| 自动诊断 | B1/B2 均完成任务并正常停止；B2 预检、加载和独立回收报告已核验 | C-266--C-275 |
| 全组策略读取准备 | A060/L5/B6已构建、测试及SD完整回读；B5正常关闭，等待B6启动 | C-308、C-309 |

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

## 最小身份加载测试准备

`STATIC`：匹配的 v07 系统服务保留 system UID 与全局调试开关分支；固定进程名查询可
选择 Fly，数字 PID 查询则不再校验包名。因此本轮选择固定 `dji.go.v5` 名称，并独立核对
前后 AMS PID/UID 和原生结果。ARM32 ART TI 每次成功 GetEnv 建立独立环境，Dispose 可
释放本次环境；它不卸载 agent 或 JVMTI plugin（C-268）。

`STATIC`：A-048 新探针记录自身 PID/UID/GID、SELinux 域和 starttime，以及 ART TI
申请、版本读取与释放结果。有效入口始终返回 JNI_OK，结果由 ready 字段判读，避免框架
再次初始化。32 项主机测试、sanitizer、6 个故障变体和两次相同构建通过（C-269）。

`OBSERVED`：8,372-byte A-048 已以 `Download/FindUAS_ARTTI_V2.so` 放到 SD 并完整读回。
B1 的 STOP 任务和 CLOSED STOP 均已核验（C-270）。内部测试文件仍未创建；新的 L1/B2
加载任务已完成预检和回收场景测试（C-271）。

`STATIC`：L1/A-049 在加载前重新检查固定应用、网络和日志基线；独占创建普通 SO、
记录 FD 实际身份，再核 hash/label。永久 attempted 标记写完读回后，只向固定进程名
派发一次。原生日志必须有绑定 PID/UID/SID 的完整 enter/result，才进入正常文件回收。
13 个真实 mksh 测试覆盖 39 场景；B2/A-050 的两项 Java/mksh 分派和 29 项 host client
测试通过（C-271）。不完整复制或未见原生完成时保留文件；不会把延时当成完成信号。

`OBSERVED`：L1/B2 和 A-048 均已 SD 完整回读核对。旧 active 记录已在 CLOSED STOP
之后归档并核验，新会话已准备、active 最后发布；该准备阶段等待操作者启动 B2（C-272）。

## 实机加载成功与回收

`OBSERVED`：B2 预检报告完整收到，23 个检查均为 true（C-273）：Wi-Fi 设置和服务均关闭，
没有默认网络或已登记当前网络，四项升级触发值处于非活动状态；应用哈希、AMS PID/UID、
目录标签、源文件和日志通路检查通过。加载任务随后重新进行了这些检查。

`OBSERVED`：L1 独占创建普通测试 SO，核对实际 FD 身份、8,372-byte 大小、0644 模式、
system 所有者、apk_data_file 标签和 A-048 哈希。永久 attempt 标记写完读回后，发起一次
固定 `dji.go.v5` 名称的系统服务加载请求（C-274）。较后的日志快照中出现一组完整的
enter/result，绑定本轮 SID、预期 PID/UID 和 32-bit ABI：

- `ready=1`、`identity_ok=1`、`artti_ok=1`、`dispose_ok=1`。
- GetEnv、GetVersionNumber、DisposeEnvironment 返回码均为 0。
- 实测接口版本为 `0x70010200`；自身 SELinux 基础域为 `untrusted_app`。
- 前后 AMS PID/UID 和 Fly APK 哈希保持一致。

原始类别、PID/UID、starttime 和日志保留私有。starttime 是一次原生读取，同一日志被多次
回读不算第二次采样。测试文件删除前再次核对身份/哈希/标签，随后删除成功。

`OBSERVED`：另一个 CANARY_CLEANUP 任务返回 `cleanup_already_absent=true`，再次确认文件
已不存在，派发计数为 0。主机回读 copy 和永久 attempt 记录并与报告核对；最后 STOP 和
CLOSED STOP 也已核验（C-275）。B2 已结束，不需继续保持开发助手页面。
本次释放了申请的 ART TI 环境并回收磁盘文件，没有重启 Fly；agent/plugin 映射未执行卸载。

## RID 状态读取的后续入口

`STATIC`：当前字段链从已初始化的 FlyModel flight Lazy，经过 FlightModelImpl regulation
Lazy、RegulationModelImpl RemoteID Lazy，抵达 RemoteIDModelImpl working-status Lazy。
三种 Kotlin Lazy 均保留 `_value`；读取应先确认类已初始化，每跳验证实例类型并在 sentinel/
空值处退出，不调用 Lazy getter 或工厂（C-276）。

ToggleFlyObservable 没有直接的最新状态 DTO 字段；V1FlyObservable 的默认 DTO 也不是当前
RID 值。`getOrNull()` 会经过可变拦截器，默认处理最终进入 `JNIKeyValue.native_get_sync`；
其类初始化还会加载库。该原生同步入口的主体/缓存语义尚需核对，当前没有调用这些 getter、
创建监听或读取 RID 字段。

## 官方同步缓存入口闭合

`STATIC`：exact Fly 1.19.4 的 `native_get_sync` 已对到同步 SDK GetValue、
SDKFrameworkCore 和 CacheLayer 加锁查找，返回值经独立 Java byte array 序列化
（C-277）。该链不进入异步请求或监听注册；内部会维护首次 key 日志集合，并可能扩展
空缓存层级槽。官方 V1 tuple 选择 product index 0 的 FC `RidWorkingStatusPush`。

新读取探针使用已初始化 JNI/key 类及原有 key 字段，检查现存 mediator、initialized 位、
framework/cache 指针和匹配 vtable；不经过 Lazy 工厂或 Rx 拦截器。结果结构为四个
Boolean、带长度的 area 字符串及两个 32-bit failure 字段，总长严格为 `16+L`。
采集只取状态和 RID failure，跳过 area 内容；null 缓存单独记录。

## RID 单次缓存采集已准备

`STATIC`：A-051 经过 25 项 ASan/UBSan 宿主测试、两次相同 ARMv7 构建；L2 的九项真实
mksh 测试、B3 的三项 Java/mksh 测试，以及 36 项 host protocol 测试通过（C-278）。
exact v07 ARM32 app seccomp 过滤器允许自身读取所用的 `process_vm_readv`；read/pread64
正控和 swapon 负控也已核对。生成 SO 保留在排除目录。

L2 使用新的普通测试文件和 A-051 永久尝试记录，先核对原有应用/网络/目录/日志基线，
再执行一次缓存读取。完整原生终态后回收匹配文件，并提供独立 CLEANUP；已读到值与
null 缓存分别输出。旧 A-048 及其记录不变。

`OBSERVED`：USB 文件传输会话曾连续打开失败，操作者重新插拔后恢复。新会话已准备，
以下三份文件均通过完整 SD 读回（C-279）：

- `Download/FindUAS_RID_CACHE.so`：A-051，14,376 bytes。
- `Download/L2.sh`：A-052，22,121 bytes。
- `Download/B3.sh`：A-053，10,513 bytes。

## 实机 RID 缓存结果

`OBSERVED`：操作者启动 B3 后，完整 RID_BASELINE 报告的 23 项检查全部通过（C-280）。
RID_READ 再次执行同样检查，然后独占创建、核对 A-051 的普通测试文件，完成一次
系统服务加载及一次同步缓存调用（C-281）。10,879-byte 完整报告、DONE 哈希及独立解析
一致；唯一原生 enter/result 对应本轮 SID、PID/UID 和 32-bit ABI。

| 缓存字段 | 结果 |
| --- | --- |
| `rid_support` | `1` |
| `rid_normal` | `1` |
| `eid_support` | `0` |
| `eid_normal` | `0` |
| `fail_reason` | `0` |

`ready=1`、`stage=0`、`exception=0`、`query_count=1`、`value_present=1`；JNI、ART TI、
解析和 Dispose 返回码均为 0。失败码取自正式 `failReason` 字段。多次日志快照包含同一对
原生记录；并非多次采样。此结果为 SDK 缓存快照，没有接收时间戳；本轮按不起桨要求进行，
未采集独立 RF。前后 AMS PID/UID 与 APK 哈希保持一致。

`OBSERVED`：读取后核对文件身份/哈希/标签并删除。独立 RID_CLEANUP 返回
`cleanup_already_absent=true`，没有再加载或读取。copy/attempt 记录也被主机独立回读匹配；
STOP 与 CLOSED STOP 均已确认（C-282）。环境已释放、磁盘测试文件已回收，未卸载运行时
映射或重启 Fly。A-048/A-051 的永久记录均保留。

## 状态新鲜性与启停入口追踪

`STATIC`：RID 的四个状态位来自飞机状态包，area 只作字符串映射。缓存记录1000ms有效期，
但同步 getter 不检查这个期限。每个同值新推送仍会更新时间戳，只有值变化才通知 listener；
缺包不会自动清空已有值（C-283）。因此 A-051 的记录继续保留为真实缓存快照。

现有 native listener 对这个 push-only key 不启动 GET、也不回放首值；取消则先移除回调ID，
再排队清理 worker 项。它适合后续研究状态变化，目前不把零回调当作新包到达记录。

`STATIC`：当前设置页开关对应 France EID，状态页对应 Japan 注册导入；working-status的
直接 UI 消费者使用 support 位决定序列号行显示。Native BLE start/stop 则通向本机
Android action handler（C-284）。三份 exact SDK 中的旧 CCC/global-RID/C0 固定名字未见，
这轮没有形成新的飞机 RID 普通开关读回/恢复链（C-285）。

`STATIC`：RID 云策略使用旧 namespace 存储家族，名称中的 V2 不表示 getter-V2 API。
`block_device` 是产品类型列表；选择器按首个 country/default 项、产品排除、空串过滤和
同连接去重决定下发字符串。业务区域谓词会在服务层阻断 RID namespace；当前没有读取
该谓词或实际 App area。Native sender 把该字符串从 hex 解码为00/DD载荷（C-286）。

发送成功后原 CloudControlData 会留在 SDK 缓存，同一 key 也供限速、电池逻辑使用。
下一只读比对将读取固定 RID namespace 的现存内存项、产品类型和共享缓存，按有效首项/
DEFAULT规则比较可能的 RID 候选。原文、区域和payload摘要不输出；本轮不读取App area，
因此匹配结果只记为候选内容关联。

## 云策略比对程序与SD准备

`STATIC`：独立 Python 选择器与 C 候选解析器完成（C-287）。它们保留首项、DEFAULT、
产品排除及空串规则；不读取实际 App area 时只报告可能候选集合。UTF-8/JSON转义与代理对
经过101项C检查、427组有效差分和5组限额拒绝对照，另有27项Python测试。

A-054从已初始化枚举字段取得实际RID namespace，不猜测配置名。它先确认现存默认MMKV
实例，用两层递归mutex的trylock守住固定键读取；缺实例、需重新加载、multiprocess或ashmem
分支均以数字原因结束。普通Java包装对象允许，nativeHandle须匹配。拿到String后先释放
MMKV锁，再转UTF-8并各读一次ProductType/CloudControlData缓存。只输出数字、计数及候选
匹配结果，原文和payload摘要不输出（C-288）。

40项JNI/锁顺序sanitizer案例、两次相同ARMv7构建、10项L3和3项B4真实mksh/Java测试，
以及43项host protocol测试通过。独立检查确认两次SDK读在MMKV锁之外，失败路径逆序释放。

`OBSERVED`：前一B3会话已正常关闭并归档，新会话已准备，三份文件完整SD回读均匹配（C-289）：

- `Download/FindUAS_CLOUD_POLICY.so`：A-054，22,336 bytes。
- `Download/L3.sh`：A-055，22,348 bytes。
- `Download/B4.sh`：A-056，10,555 bytes。

## 实机云策略缓存比对结果

`OBSERVED`：操作者启动B4，完整基线的23项检查全部通过（C-290）。POLICY_READ重复基线，
核对A054并加载一次。11,229-byte报告、DONE回执及独立解析一致，只有一组对应本轮SID/
PID/UID的原生enter/result。一次MMKV解码、一次CloudControlData缓存读取、一次ProductType
缓存读取均完成；JNI、环境、guard、JSON及Dispose返回码均为0（C-291）。

| 输出 | 结果 |
| --- | --- |
| namespace/存储值/cloud缓存/product缓存 | 全部存在 |
| ProductType | `139` |
| 缓存接收者type/index | `18/4` |
| 策略项 / country重复数 | `41 / 0` |
| 去重后的非空可能候选内容 | `36` |
| 缓存内容命中候选集合 | `1` |
| DEFAULT候选匹配 | `0` |
| 产品139命中block列表的首项数 | `0` |

匹配数针对去重后的payload字符串集合，不代表唯一country行；41→36的差额可能包含空值和
重复payload。DEFAULT匹配0未区分DEFAULT缺失、空或其他内容。实际App area和服务谓词没有
读取，原文/区域/payload摘要没有输出；本轮建立的是现存RID候选与共享SDK缓存的内容关联。

`OBSERVED`：Fly PID/UID/APK保持一致，匹配文件已删除；独立POLICY_CLEANUP确认不存在。
copy/attempt回执与报告匹配，STOP/CLOSED STOP均已收到（C-292）。没有第二次attach或
Fly重启；永久回执和已加载运行时映射保留。

## 匹配策略结构采集准备

`STATIC`：确切发送端只做hex解码，解码字节完整进入`00/DD`正文；没有额外RID内部头或
版本字段（C-293）。因此后续直接分析现存payload，并与首个DEFAULT逐字段/逐字节比较。

A-057保留A054的现存MMKV和SDK guard，各读取一次策略、CloudControlData及ProductType。
仅在receiver18/4且缓存属于有效候选集合时导出匹配hex和首个DEFAULT；同时记录原始匹配
行数，区分DEFAULT缺失与空串。JSON最多32KiB，由Fly自己的Application context通过
MediaStore写入可移除SD的`Download/FindUAS/Probe/`新文件；普通日志只有状态和长度。

`STATIC`：42项JNI/主流程案例、22组提取测试及272次sanitizer调用、66项存储案例、
14项离线格式/差分测试、13项loader/receiver集成和50项host测试通过。两次ARMv7构建
相同（C-294）。离线工具检查JSON、protobuf wire、ASN.1 TLV及gzip/zlib，并输出结构差异。

`OBSERVED`：三份新文件SD完整回读匹配，新会话已准备（C-295）：

- `Download/FindUAS_POLICY_STRUCTURE.so`：A-057，27,072 bytes。
- `Download/L4.sh`：A-058，23,349 bytes。
- `Download/B5.sh`：A-059，10,591 bytes。

## B5基线与USB传输中断

`OBSERVED`：B5已启动，receiver及完整STRUCTURE_BASELINE报告收到，23项检查全部通过、
返回0，attach计数0（C-296）。提交采集任务前，读取session.ready发生MTP超时；随后重连
返回RC2_OPEN_FAILED。原会话历史只有已完成的基线任务，尚未分配STRUCTURE_READ。

## USB恢复与断连排查

`OBSERVED`：重插后MTP仍打不开。USB调试记录显示，OpenSession的bulk OUT传输了0字节，
返回device-not-responding；原libmtp进入自动USB重置路径。操作者随后报告遥控器/飞机连接
短暂恢复后反复断连。暂停诊断、关闭G HUB，并停止仍连接遥控器的主机ADB服务后，操作者
确认连接稳定（C-297）。G HUB依操作者要求保持关闭。全程尚未分配STRUCTURE_READ。

`CORROBORATED`：发现libmtp的恢复行为作用于整个USB设备，并非只重置MTP接口。主机工具
现强制静态链接libmtp并用独立guard拦截两处reset；缺guard或混入动态libmtp会拒绝构建。
两项C自测、53项host测试通过。一次无reset状态读取实际拦截了两次调用，但MTP仍超时；
另外两次标准MTP状态查询也超时（C-298）。旧的自动重置构建不再使用。

## 重启后恢复

`OBSERVED`：操作者确认遥控器重启、图传连接稳定。三次MTP读取恢复成功；每次正常关闭
会话时，guard都拦截了一次USB重置，进一步确认正常关闭分支也需要阻断（C-300）。

`STATIC`：新增显式重启恢复命令（C-299）。它只处理已完整收齐且没有READ/LOAD的诊断
会话，保存原始记录及固定的旧/新SID映射；归档或发布回应丢失后可用原请求继续。
重启回执单独记录操作者确认，不伪造worker的CLOSED。67项host测试及两项C自测通过。

`OBSERVED`：旧基线会话已完整保留并归档，新的会话已激活（C-300）。A057/L4/B5文件保持
原先核验的版本，A057尚未执行。G HUB和ADB保持关闭。

## A057实机采集与内部结构

`OBSERVED`：新B5会话的23项基线全部通过；A057随后加载一次，读取现存MMKV一次及两项SDK
缓存各一次。ProductType139、receiver18/4、41项/36候选、match1/default0保持一致；所有
JNI/guard/解析/释放返回码为0，PID/UID/APK稳定，内部临时文件清除（C-301）。

`OBSERVED`：826-byte私有JSON已通过MTP取回。匹配内容对应唯一原始行；首个DEFAULT存在且
非空；两者各194个hex字符、97字节。独立清理确认文件不存在，copy/attempt回执与本轮
身份、boot及source匹配。没有发送STOP，接收端保留（C-302）。

两份数据均拆为`20-byte头部 + 13-byte正文 + 64-byte尾部`，头部offset18的LE16长度为13。
固定magic是`0x83677667`；头部只有offset8的四字节字段变化（C-303）。

正文按当前候选宽度划分如下；字段名称尚未在接收端匹配，解释集中在H-33：

| 正文相对偏移 | 候选宽度 | matched | DEFAULT |
| --- | --- | --- | --- |
|0|1|1|0|
|1|2|3|2|
|3|2|2|0|
|5|4|16|20|
|9|4|16|3|

`CORROBORATED`：尾部为两项32-byte大端ECDSA数值。离线恢复得到唯一共同P-256验证点，
OpenSSL对两份原始头部/正文的SHA-256签名均验证成功；SHA-384负对照均失败（C-304）。
签名覆盖整个33字节头部与正文。独立envelope与签名核验工具已加入源码，相关47项测试通过。
完整payload、公钥、原签名及私有报告不入库。

`NEGATIVE`：确切Fly APK/SDK及已有RC明文资料没有找到这一内层解析器或公钥owner；邻版
资料另行标注。AddCloudControlSign属于HTTP请求签名，未作为本包的验证器使用（C-305）。

## 固件输入与另一版本接口

`STATIC`：WA150两个版本的官方清单各有10项：0802、1200、六个1100变体、2603及0806。
1200/1100的编号定义及文件名分别对应ESC和电池控制器家族；七个小模块两版相同，当前
只有清单。现有五份原件为两版0802/E3、两版2603/GNSS及共用0806/DONG；完整size/MD5、
payload SHA-256均匹配。它们都是IMaH v2单chunk，payload从offset608开始，STUE加密、
attributes0、头部compression0，没有明文外层chunk（C-306）。缺失模块的实际封装尚未检查；
接收端主候选仍是与实机版本对应的0600/0802/E3。

`STATIC`：MSDK5.18的CloudControlVersion在WA345 setup注册，GET使用`0x50/0x20`，
receiver type/index为25/4、timeout500ms；响应包含ccode@2、version u32@8与32-byte nonce@12。
对应`libdjisdk_jni.so` SHA-256为
`27402f45c63bf6ea9e8d3a783fc1202b53631e0ee24cc18a938ba1e91629dbcf`，getter位于
`0x3414088`，注册段位于`0x2ee4be8..0x2ee4c3c`。确切Fly1.19.4未找到同名接口；这是与
`00/DD`不同的产品/版本接口，本轮未执行查询（C-307）。

## 全组策略读取准备

`STATIC`：A060保留现存MMKV及SDK owner guard，只解码一次固定RID namespace、读取一次
ProductType缓存；CloudControlData查询和SET均为0。最多32KiB的JSON保留全部全球策略行、
顺序和重复项，每行只含`country_code`、`data_hex`、`blocked_for_product`；不读取当前App area。
新报告使用`FindUAS_A060_policyset_<SID>.json`，原文保留在私有采集目录（C-308）。

43项native案例、提取器274次调用/1044项检查及存储66案例/9060项检查通过ASan/UBSan；
15项Python测试包含160组随机差分。两次ARMv7构建一致，另有13项L5/B6集成和74项host
bridge测试通过。

| 准备工件 | bytes | SHA-256 |
| --- | ---: | --- |
| A060 ARMv7 probe | 26624 | `3c0c5988996e79e4bc8010344b62c5dead48d07471e5d6dac282a6841939c04d` |
| L5 loader | 23055 | `a1e509cd10b55594151e3a5b9694247fab4a43b1850cf9602fccb23eac264060` |
| B6 receiver | 10557 | `594ac137a897c6ceaf889df54acb91af2f407cedf214bd3715bc2a1550587440` |

C-308记录程序准备；SD staging与新会话另记后续实机条目。A060尚未执行，未取得全组策略报告。

## 下一步

当前待操作者启动B6；通过新基线后采集一次全组全球策略，供离线跨地区比较，同时继续追飞机端
`00/DD`接收处理器。13字节正文的字段仍未命名，候选解释继续统一保留在H-33。

## 同步状态

按操作者的一次性要求，既有六个提交已推送至 GitHub main，终点为 `2f31394`。
本轮新采集准备继续在本地记录，未再次推送。
私有材料的定位类别见 [排除日志索引](15_LOG_INDEX.md)。


## A060部署与B6待启动（C-309）

`OBSERVED`：A060/L5/B6三个新固定文件的SD完整回读均与源字节/hash匹配。
旧B5的前三项结果和独立清理早已收齐；本轮STOP任务返回0，收到规范`CLOSED STOP`。
正常prepare保留并归档原会话记录，最后激活一个新会话。未使用重启恢复路径，
未更改A048/A051/A054/A057永久回执。G HUB和host ADB保持关闭，USB reset仍由主机工具拦截。

当前只需操作者在开发助手启动一次`Download/B6.sh`，准确含卷路径的命令已私下提供。
启动后主机自动收取`CATALOG_BASELINE`，通过后执行一次`CATALOG_READ`，读取固定A060 JSON，
比对导出计数、验证签名并统计逐字段值域，再独立`CATALOG_CLEANUP`。
B6尚未确认启动，A060尚未执行。飞机保持当前静止状态即可。
