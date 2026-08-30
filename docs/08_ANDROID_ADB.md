# RC 2 Android、ADB 与无 Root 入口边界

## 1. 当前结论

- `OBSERVED`：RC 2 操作界面报告版本 `07.00.0100`。USB 调试已由操作者在 Android 设置中开启；一次关闭再开启和一次线缆重新枚举后，主机侧状态仍为 `offline`。
- `OBSERVED`：限定握手中，主机成功发送 ADB `CNXN`，控制器在约 15 秒的 bulk-IN 窗口内没有返回 `AUTH TOKEN`、`CNXN` 或其他 ADB packet。
- `NEGATIVE`：没有 shell、`OPEN`、APK 安装命令、Android 命令、重启、fastboot、root、remount、agent attach 或 DJI 协议请求经 ADB 执行。
- `STATIC`：已取得并验证 RC331 `07.00.0100` signed system chain。其 APEX `adbd` 与先前审计样本逐字节相同，target-version `handle_packet(CNXN)` 确含 DJI production/debug-count 的 pre-AUTH return。
- `UNKNOWN`：当前实机的 `ro.boot.mp_state`、`ro.boot.dbg_cnt`、mounted `adbd` hash 与分支 log 尚未读取；signed target package 静态事实不能改写成 live branch trace。
- `STATIC`：exact v07 `dpad_fuli.apk` 与已审计开发助手逐字节相同，因而“shell命令测试”页的 `Runtime.exec` 与 stdout-only 边界是 target-version 静态事实。
- `STATIC/NOT ADMITTED`：只改一条 gate-value instruction 的 userspace copy 已生成并审计；MTP staging/readback 已闭合，但它尚未复制到内部存储、chmod 或执行。
- `HYPOTHESIS`：第一包直接 public-key 可能进入 exact daemon 的独立 AUTH branch；该动作未执行，会触发授权提示或持久授权状态，因而不是只读结果，也不是默认下一步。

本文不包含设备序列、USB location、主机 transport ID、ADB key、授权记录、绝对路径、原始 USB packet dump 或厂商代码正文。

## 2. Live USB descriptor

`OBSERVED`：当前设备以 `VID:PID 2ca3:1021` 枚举。脱敏后的接口如下：

| Interface | class/subclass/protocol | endpoint | 观察边界 |
| --- | --- | --- | --- |
| 0 | `ff/43/01` | bulk OUT `0x01`，bulk IN `0x81`，MaxPacket 512 | DJI vendor/DUML 路径；与 ADB 分开 |
| 1 | `06/01/01` | bulk OUT `0x02`，bulk IN `0x82`，interrupt IN `0x83` | MTP/PTP 类路径 |
| 2 | `ff/42/01` | bulk OUT `0x03`，bulk IN `0x84`，MaxPacket 512 | ADB-shaped FunctionFS 路径 |

每次自定义 claim Interface 2 前，系统 ADB server 已停止。该 precondition 避免两个主机客户端同时占用接口；它不改变控制器状态，也不证明 daemon 完成协议握手。

## 3. 2026-08-28 限定握手记录

### 3.1 路由与正向控制

| 字段 | 记录 |
| --- | --- |
| 主题 | RC 2，UI version `07.00.0100` |
| 时间 | 2026-08-28 15:03–15:15，Asia/Shanghai |
| 物理路由 | USB Interface 2，固定 bulk OUT/IN endpoint |
| 主机正向控制 | OUT transfer 成功；descriptor 与 endpoint 在本次连接重新枚举 |
| 请求上限 | 每个 profile 只发送一个 ADB `CNXN` header 与 payload |
| 接收窗口 | 约 15 秒 bulk-IN timeout |
| 匹配规则 | ADB magic、checksum、length 和 short transfer 全部严格验证 |
| 结果 | 未收到任何 ADB packet |
| 恢复 | 无控制器设置或文件写入；释放接口 |
| 独立 RF | 不适用；未进行飞行/RID 请求 |

### 3.2 已复现的主机 profile

平台工具 `37.0.1` 的 macOS legacy USB backend 与 libusb backend 均得到同一 `offline` 结果。一个限定握手 client 复现了公开旧固件 profile：

```text
version  = 0x01000000
MAXDATA  = 262144
banner   = host::pydevice\0
framing  = 24-byte header 与 payload 分开的 USB transfer
```

从该 profile 出发，每次只改变一个变量：

| 单变量 | 结果 | 不能推出 |
| --- | --- | --- |
| version `0x01000001` | `NEGATIVE`：无回复，timeout | 不能证明版本字段被解析或拒绝 |
| MAXDATA `1 MiB` | `NEGATIVE`：无回复，timeout | 不能证明 buffer 大小是根因 |
| 短 `host::\0` banner | `NEGATIVE`：无回复，timeout | 不能证明 banner 文本是根因 |
| stock feature banner | `NEGATIVE`：无回复，timeout | 不能证明 feature list 是根因 |
| legacy payload checksum 置零 | `NEGATIVE`：无回复，timeout | 不能证明 checksum 分支被执行 |

将 header 和 payload 合并为一次 USB transfer 会快速返回 I/O failure。当前 ADB/WebADB 实现仍使用分离 transfer，因此该现象只是一条无效 framing 线索，不是认证绕过。

### 3.3 认证边界

握手 client 只允许：

1. 发送 `CNXN`；
2. 仅在收到真实 `AUTH TOKEN` 后，才允许发送 `AUTH RSAPUBLICKEY`；
3. 永远不发送 `OPEN` 或 shell service。

本次没有收到 token，所以没有发送 public key、signature 或任何 authorization packet。删除主机 key、修改 signature、切换 WebADB 的 post-token 行为均不能解释更早的 `CNXN` silence。

## 4. Exact v07 signed package 与 `adbd`

### 4.1 Provenance chain

| 字段 | 值 |
| --- | --- |
| target aggregate | RC331 `07.00.0100`，`1,446,604,800` bytes，SHA-256 `296cfa63e3c6b011fd1ee8dd911c11f64dac9d34a8424a6fbb95b0c237ab1ae3` |
| signed module | `0205` module SHA-256 `69988bff127293e4c512642df0b335aad2b8196105df050c573b591648a0e33a` |
| verification | `PRAK-2020-01` header signature、stored/encrypted checksum、decrypted/plaintext checksum 全部通过；无 force/skip/truncate |
| `adbd` 大小 | `1,497,232` bytes |
| `adbd` SHA-256 | `b300d9bb90f5941fe2952bc9f6dacc30e639a498be4435f59a4ae95134bd5422` |
| GNU Build ID | `c30245f84b2d2ddcecbcd9f640a84192` |
| 状态 | exact target-package `STATIC`；厂商 aggregate、module、image、APK 和 binary 均不分发 |

aggregate 来自 third-party Dank Drone Downloader archive；archive 本身不是 DJI。证据锚点是
内部 signed config/module 又经 public DJI release-key/checksum chain 独立验证。该 target `adbd`
与先前 RC331 sample 的 `cmp` 结果相等，故早先的 adjacent-only C-032 已 `RETRACTED`；这不等于
已从当前开机实机读取 mounted file。

### 4.2 USB composition

`STATIC`：exact v07 APEX init 的 service executable 是：

```text
/apex/com.android.adbd/bin/adbd
```

离线 extracted filesystem backing path 是 `/system/apex/com.android.adbd/bin/adbd`。target image
没有 `/system/bin/adbd`；后者不得再出现在操作指令中。Exact vendor init 将 `2ca3:1021` 绑定为
`mtp,bulk,adb` composition，依次链接 vendor bulk、MTP 和 FunctionFS ADB，再启动 APEX daemon。
因此 live `offline` 是 transport 已枚举但 ADB state machine 未完成，不是 USB 上没有 ADB function。

### 4.3 Production-state gate

`STATIC`：exact v07 `adbd` 在一般认证决策之外，还在 `CNXN` 分支检查：

```text
ro.boot.mp_state == production && ro.boot.dbg_cnt < 1
```

条件成立时进入 DJI early-return/log path，不调用普通 `send_auth_request()` 或 `send_connect()`；
normal branch 仍进入原 TLS/authentication state machine。该 exact target code 与 live 的“OUT 成功、
IN 沉默”一致。

边界：exact system `prop.default` 中的 `ro.debuggable=1`、`ro.adb.secure=0` 等值不能替代 live
readback，boot/vendor overlay 与持久属性可能改变结果。必须从实机读取两个 gate property 或看到
`[lsx_dbg]handle_new_connection return`，才可把本次 silence 记成 live gate branch。

## 5. 隐藏 Android 设置入口

### 5.1 静态路由

`STATIC`：相邻 RC331 Settings APK 删除了顶层菜单中的“关于设备”入口，但保留了标准 Android `DEVICE_INFO_SETTINGS` activity、版本号 preference 和七次点击开发者模式 controller。`APPLICATION_DEVELOPMENT_SETTINGS` 在门禁未打开时进入 warning-only fallback，门禁打开后才进入实际开发者选项页面。

这条路径不绕过 Android gate，不授予系统 UID/root，不改变 `adbd` production branch，也不证明主机可以完成认证。

### 5.2 Settings Launcher 1.0.0

`STATIC`：独立 launcher 只有两个固定 Android Settings action、零权限、一个前台 Activity、零后台组件、零 native library、零网络/文件/shell/ADB/Binder/DJI/DUML surface。封存 APK 身份见 [工件登记](11_ARTIFACT_REGISTER.md)。

`OBSERVED`：一份副本复制到可移动存储后重哈希与封存 APK 一致。该事实只证明复制完整性；安装状态不由这条记录建立。所有页面点击、七次版本号点击和 USB 调试切换均由操作者手动完成。

## 6. 历史 localhost observer 撤回

`RETRACTED`：observer v0.1–v0.4 曾把连接 `127.0.0.1:40007/40009` 后不写 payload 视为 input-only。相邻 `0205` 的 `dji.json` 与 `libduml_frwk.so` 显示，默认 server 只有一个活动 accepted fd；新 TCP connection 可关闭并替换旧 fd。`connect()` 本身因此可能中断 DJI Fly，即使调用者从未取得 output stream 或发送字节。

后果：

- v0.1–v0.4 永久停止 live 使用；其离线 parser/test 仍可作为静态材料；
- reconnect/backoff 会反复竞争同一 fd，不能修复架构；
- 当前 exact v07 行为仍是 `UNKNOWN`，但风险不对称使第二客户端方案维持 `RETRACTED`；
- 未来只允许复用官方 transport owner，不能恢复第二 localhost client。

当前替代候选是 v0.10，而不是旧 v0.8。v0.10 的精确状态见第 8 节。

## 7. Stock `dpad_fuli` 与 UID1000 边界

### 7.1 Exact v07 package 静态事实

Exact v07 signed system package 中的 `dpad_fuli.apk` 是 `8,849,471` bytes，SHA-256
`58b176eb1e17cacb7522914d282a69a677603ea9026993fc143c6a390211e44f`。它与此前完成 manifest/DEX
审计的样本逐字节相等。其 manifest 请求 Android system shared UID、标记 debuggable；
`DevActivity` 中的“shell命令测试”打开 `ShellCommandActivity`，后者把 operator text 交给
`Runtime.getRuntime().exec()` 并显示 stdout。

边界：static shared-UID/signer request 不是 live `id`；`Runtime.exec()` 不自动变成 UID 0；该页面
没有可靠保留 stderr 与 exit status。当前 controller installed APK 是否被 update 替换，也需要 live
package hash 才能闭合。

完整 manifest 审计覆盖 30 个 Activity、2 个 Receiver 和 1 个 Service；6 个 externally reachable
component 中仍没有一个提供“固定 argv、side-effect-free、可返回 stdout/stderr/exit status”的外部
自动化命令面：

- `STATIC`：`DevActivity` 忽略调用者 command extras。
- `STATIC`：exported share service 不提供可用 Binder command API。
- `STATIC`：update receiver/action 进入 update/recovery 域，不是 shell carrier。
- `STATIC`：private Shell page 可由操作者直接使用，但会执行任意输入，且丢失 stderr 和 exit status；它适合短命令人工取证，不是自动化 RPC。
- `STATIC`：private Protocol page 没有 selector/retry 控件，Parcelable 省略 retry 字段；其 push-listen 路径还会写外部日志。

因此 exported-caller path 维持 `NEGATIVE`，但 operator-visible Shell page 是当前最短的 live
property/identity collection surface。Package bytes 已对 exact v07 signed package 闭合；当前实机
installed-file identity 仍需单独 readback。

### 7.2 Android permission boundary

`STATIC`：Android 11 `attach-agent` shell command 要求 signature permission `SET_ACTIVITY_WATCHER`。普通 app 启动 `/system/bin/cmd` 时仍保持原 UID；`exec()` 不会把它变成 UID1000。目标 app 可调试性、ART `IsJdwpAllowed` 和 agent 路径可加载性是另外三个独立门禁。

系统 UID 也不是 root UID 0。不存在“debuggable + cmd = privilege bridge”的已验证路径。

## 8. 当前只读 admission probe：v0.10

v0.10 取代 v0.8/v0.9，保留同一 package/signer 只用于覆盖历史 observer。其身份如下：

| 字段 | 值 |
| --- | --- |
| 版本 | `0.10.0-research`，versionCode `10` |
| 大小 | `2,570,983` bytes |
| SHA-256 | `fdad29bfb1237bc224a805d6eb5a99358a044bd226610d9f0fc33975d94b606c` |
| schema | `finduas-rid-probe/v0.10-schema-1` |
| 审计 | 43 tests；21/21 adversarial audit mutations rejected；两次 clean build byte-identical |
| 状态 | `NOT ADMITTED`：已离线独立审计；C-231 MTP staging/完整读回匹配，安装与运行待确认 |

2026-08-30 接手复核（C-231）：原始精确 APK 再次通过源码/final-DEX 审计和 21/21 mutation 检查，已放到 removable SD 的 `Download/FindUAS_A001_V010.apk`。fresh listing 的唯一文件名与大小、随后同一只读会话的完整文件读回 hash 均匹配。独立 `mtp-getfile` 跨会话尝试失败，没有重传；同会话精确枚举后读回成功。该动作没有安装/启动 probe、启动 ADB、attach、DUML、飞机设置或电机操作。

v0.10 请求零 Android permission，只有一个 launcher Activity，没有 service/receiver/provider/native library。应用自身无 socket、localhost port、DUML、Parcel、DJI application transaction、process execution、file persistence、network send、agent attach 或 library load。

手动 snapshot 只读取：

- `protocol` Binder name 的 lookup、ping 和 descriptor 元数据；
- 固定 package/UID/version/signer/ABI/component/path/hash 分类；
- build/debug/SELinux 等固定环境事实；
- 本进程 `/proc/self/maps` 中 exact-basename `libart.so` 的严格双 snapshot、descriptor identity、whole-file SHA-256、GNU Build ID 和固定 range hash；
- 两个固定 Android Settings action 的本地打开结果。

`COMPLETE` 只表示该次只读报告按 schema 完成。Binder descriptor 匹配不证明 transaction authorization；ART identity 匹配不证明 target DJI Fly mapping；package match 不授权 attach；任何结果都不是 RID 状态或写入许可。

v0.8 是历史封存工件，不再是当前 staging instruction。v0.9 的独立审计发现 mapping geometry、timestamp/maps drift 和 auditor coverage 缺陷；这些已在 v0.10 修复并重新测试。

### 8.1 v0.11：SD 报告导出

当前候选是 A-038 `0.11.0-report-export` / code 11，上述 v0.10 是前一封存版本。用户明确要求
把报告写入 SD 卡供主机读取；新版本只增加固定 `Download/FindUAS/Probe/` 的新报告文件，不加
权限、DJI 命令、目标代码写入或 attach。检查终态不论 COMPLETE/INCOMPLETE 都保存，导出状态
独立；失败可重试保存而不重新检查。完整规则和审核见
[v0.11 报告导出](../apps/rid-admission-probe/REPORT_EXPORT_V11.md)。

C-233/C-234：69 JVM tests、30 mutations、两次一致构建及签名/对齐检查已完成；精确 APK 已作为
`Download/FindUAS_A038_V011.apk` staged，完整 MTP 读回匹配。安装、运行及报告文件读回仍未确认。
旧 A-001 文件未覆盖；原始报告和 MTP 日志保留于私有排除区。

## 9. Exact-v07 userspace-copy patch

### 9.1 Design

`STATIC`（C-177）：semantic patcher 先要求 exact input 为 unstripped AArch64 ELF、唯一
`handle_packet` 与 `send_auth_request` symbol、三个 property/string anchor 的有序唯一 xref，随后
验证 `dbg_cnt < 1` 的 `cset`、使用同一 register 的后续 `cbz`，以及 normal target 到 named
`send_auth_request` 的路径。任一条件不同即退出且不生成 output。

唯一 instruction change 是：

```text
file/vaddr 0x90460
before: f5 a7 9f 1a    cset w21, lt
after:  f5 03 1f 2a    mov  w21, wzr
```

这只把 DJI gate flag 固定为 false；normal target `0x904d8`、TLS/authentication、RSA key 与 shell
service 实现均不被重写。Original A-030 SHA-256 为 `b300d9...422b`；A-032 output 是同样
`1,497,232` bytes，SHA-256
`3fceaa1724a77a153c17f725a2e3f3001b0543e31e0830aca0c77d785df9225f`。Embedded Build ID 没有
重算，不能用它识别 patched copy。Original/derivative binary 与含本机 path 的 raw manifest 均不
进入仓库。

### 9.2 MTP staging state

`OBSERVED`（C-178）：A-032 已写入 removable-SD `Download/RC2_ADBD_CNXN.bin`。Fresh MTP
session 看到一个同名 `1,497,232`-byte object，完整 readback 的 SHA-256 与登记 output 相等。

`NOT ADMITTED`：该文件没有复制到 internal executable location、没有 chmod、没有执行；本次
staging 没有停止 init daemon、没有发送新的 ADB packet、没有取得 shell，也没有变更 boot、APEX、
partition 或 firmware。Removable-SD file 不是安装或 runtime success。

## 10. 未执行的第一包 public-key 假设

Exact v07 `adbd` switch 中存在独立处理 `AUTH/RSAPUBLICKEY` 的分支，因此“第一包直接 public-key
是否进入 authorization UI”仍是 `HYPOTHESIS`。目前未发送该 packet、未生成或复用 device
authorization key、未显示 prompt、未改变 authorization database。

但 exact `CNXN` gate 已闭合，这条 first-packet path 不再是默认下一步。它绕开 ordinary
`CNXN -> AUTH TOKEN` order，可能留下持久 key，且不会回答 userspace-copy 是否恢复 normal auth。
只有 normal patched path 失败并形成一个新的精确 discriminator 后才重新评估；key 与原始 packet
不进入本仓库。

## 11. 操作者回来后的同一 session

本 session 分成两个短段；第二段必须根据第一段的 live UID、SELinux 与 filesystem 结果即时生成，
不得预写一个未经验证的 internal executable path。

### 11.1 第一段：只读 baseline

在 RC 2 打开“开发助手 -> shell命令测试”，依次输入以下三行，并保存完整结果：

```text
/system/bin/sh -c id;echo${IFS}selinux=$(getenforce);echo${IFS}mp_state=$(getprop${IFS}ro.boot.mp_state);echo${IFS}dbg_cnt=$(getprop${IFS}ro.boot.dbg_cnt);echo${IFS}adb_secure=$(getprop${IFS}ro.adb.secure);echo${IFS}secure=$(getprop${IFS}ro.secure);echo${IFS}debuggable=$(getprop${IFS}ro.debuggable);echo${IFS}init_adbd=$(getprop${IFS}init.svc.adbd);echo${IFS}usb_config=$(getprop${IFS}sys.usb.config);echo${IFS}usb_state=$(getprop${IFS}sys.usb.state);echo${IFS}ffs_ready=$(getprop${IFS}sys.usb.ffs.ready);echo${IFS}userlock=$(getprop${IFS}rc.userlock.state);echo${IFS}lockscreen=$(getprop${IFS}persist.rc.lockscreen.state)
```

```text
/system/bin/sh -c echo${IFS}stock_adbd;sha256sum${IFS}/apex/com.android.adbd/bin/adbd;echo${IFS}staged_copy;ls${IFS}-lZ${IFS}/sdcard/Download/RC2_ADBD_CNXN.bin;sha256sum${IFS}/sdcard/Download/RC2_ADBD_CNXN.bin
```

```text
/system/bin/sh -c p=$(pm${IFS}path${IFS}com.dpad.fuli);echo${IFS}$p;sha256sum${IFS}${p#package:};echo${IFS}cwd=$(pwd);ls${IFS}-ldZ${IFS}.${IFS}/sdcard/Download
```

Expected package/archive hashes are only matchers: stock `adbd` must be `b300d9...422b`, staged copy
must be `3fceaa...225f`, and unmodified exact-v07 `dpad_fuli.apk` must be `58b176...e44f`。如果任何
hash 不匹配，或 `id`、SELinux state、file presence、current-directory label、USB/init state 不能
支持一个明确的后续方案，停止，不执行第二段。第一段只记录当前目录和 removable-SD label；它不
把任何 `/data` 目录预先认定为可写、可执行或可用于 A-032。

### 11.2 第二段：baseline-dependent one-shot

第二段尚未执行，也不在本文虚构固定 path。研究者收到第一段结果后，在同一 live assistance
session 中只选择一个已由实际 owner/mode/label 证明可写且可执行的 internal path，然后给出最短
命令序列：

1. 复制 A-032 到该 internal path；
2. 对 internal copy 做 exact size/SHA readback；
3. 证明它可执行后才停止 init-managed `adbd`；
4. 后台启动该 copy；
5. 主机只发一次 `CNXN`，记录 first returned packet；
6. 只有 transport 达到 `device` 才执行 `adb shell id` 与固定 `getprop` readback；
7. 失败即保留原错误并通过普通 RC reboot 恢复 init service，不改 APEX/partition。

成功只表示 normal ADB state machine 可达；必须报告实际 UID/GID/SELinux context，不能因 prompt
字符推断 root。禁止 bootloader/fastboot/OEM unlock、boot/vendor_boot/vbmeta/Magisk/TEE/QFPROM/
eFuse/firmware flash。`/system/bin/adbd` 是错误 path，禁止把它带回 procedure。

## 12. 当前门禁

1. `NOT ADMITTED`：A-032 的 internal path、mode、label 与 exec permission 必须由 11.1 live
   baseline 决定；MTP success 不替代这些条件。
2. `NOT ADMITTED`：不再重复 USB debugging toggle、删除 ADB key、offline reconnect、wireless
   debugging 或 `tcpip 5555`；它们不能修复 exact pre-AUTH `CNXN` gate。
3. `NOT ADMITTED`：不先发 first-packet public key；先测试恢复后的 normal ADB auth path。
4. `UNKNOWN`：即使 A-032 返回 `AUTH TOKEN`，authorization prompt、final `CNXN`、shell service、
   UID 与 SELinux context 仍要逐层观察。
5. v0.10/JVMTI/route-resolver 路线不是当前 ADB offline discriminator；在这条 one-shot 结束前不
   与其混合执行。

## 13. 公开来源与分发声明

- [AOSP ADB](https://android.googlesource.com/platform/packages/modules/adb/)
- [`Dr-Muh/dji-adb` 固定 revision](https://github.com/Dr-Muh/dji-adb/tree/027c7815568c89e55fff22bfeede9dd294404660)
- [`ya-webadb` 固定 revision](https://github.com/yume-chan/ya-webadb/tree/340d3fe0f0f6a44830ac41965106a2aea41bc484)
- [Dank Drone Downloader](https://github.com/cs2000/DankDroneDownloader)；仅作为 third-party
  archive/metadata 来源，不能替代 signed module verification，也不被描述为 DJI 官方来源。
- [`dji-firmware-tools` 固定 revision](https://github.com/o-gs/dji-firmware-tools/tree/195692263c2684cf1ddc4995f2736be6c0fb135e)；用于 `dji_imah_fwsig.py` 的公开签名/校验流程。
- [固件与信任边界](07_FIRMWARE_TRUST_BOUNDARY.md)
- [工件登记](11_ARTIFACT_REGISTER.md)

原始 ADB/USB 抓包、device authorization key、vendor `adbd`、patched binary、APK/DEX、
init/SELinux 文件和反汇编日志均不进入本仓库。
