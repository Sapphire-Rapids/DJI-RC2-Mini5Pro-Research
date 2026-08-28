# RC 2 Android、ADB 与无 Root 入口边界

## 1. 当前结论

- `OBSERVED`：RC 2 操作界面报告版本 `07.00.0100`。USB 调试已由操作者在 Android 设置中开启；一次关闭再开启和一次线缆重新枚举后，主机侧状态仍为 `offline`。
- `OBSERVED`：限定握手中，主机成功发送 ADB `CNXN`，控制器在约 15 秒的 bulk-IN 窗口内没有返回 `AUTH TOKEN`、`CNXN` 或其他 ADB packet。
- `NEGATIVE`：没有 shell、`OPEN`、APK 安装命令、Android 命令、重启、fastboot、root、remount、agent attach 或 DJI 协议请求经 ADB 执行。
- `STATIC`：相邻 RC331 `10.00.0700/0205` 的 ADB daemon 含 DJI production-state `CNXN` 丢弃分支，可解释 live 现象。
- `UNKNOWN`：相邻 daemon 与当前 live `07.00.0100` 是否逐字节相同，尚未通过 live 文件身份闭合。
- `HYPOTHESIS`：第一包直接 public-key 可能进入相邻 daemon 的另一分支；该动作未执行，会触发授权提示或持久授权状态，因而不是只读结果，也不是默认下一步。

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

## 4. 相邻 `adbd` 静态解释

### 4.1 样本身份

| 字段 | 值 |
| --- | --- |
| 相邻平台 | RC331 `10.00.0700/0205` |
| `adbd` 大小 | `1,497,232` bytes |
| `adbd` SHA-256 | `b300d9bb90f5941fe2952bc9f6dacc30e639a498be4435f59a4ae95134bd5422` |
| GNU Build ID | `c30245f84b2d2ddcecbcd9f640a84192` |
| 状态 | `STATIC`，厂商二进制不分发 |

### 4.2 USB composition

`STATIC`：相邻 vendor init 将 `2ca3:1021` 绑定为 `mtp,bulk,adb` composition，依次链接 vendor bulk、MTP 和 FunctionFS ADB，并启动 `adbd`。因此 live `offline` 可解释为主机枚举到 ADB transport、但 ADB 状态机未完成；它不是“USB 上不存在 ADB function”的证据。

### 4.3 Production-state gate

`STATIC`：相邻 `adbd` 在一般认证决策之外，还在 `CNXN` 分支重新检查 production state。满足 production 条件时，该分支释放输入 packet，而不调用普通 `send_auth_request()` 或 `send_connect()`。该控制流与 live 的“OUT 成功、IN 沉默”一致。

`CORROBORATED` 只表示现象与相邻分支一致；由于 live 文件哈希尚未获得，不得写成“已证明当前 v07 使用该 exact binary/branch”。相邻属性文件中的 `ro.debuggable=1`、`ro.adb.secure=0` 等值也不能替代 live readback，vendor overlay 和持久属性可能改变结果。

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

### 7.1 相邻包静态事实

相邻 `dpad_fuli` 是 DJI-platform-signed、Android system shared UID、debuggable 的开发助手。完整 manifest 审计覆盖 30 个 Activity、2 个 Receiver 和 1 个 Service；6 个 externally reachable component 中没有一个提供“固定 argv、side-effect-free、可返回 stdout/stderr/exit status”的命令执行面。

- `STATIC`：`DevActivity` 忽略调用者 command extras。
- `STATIC`：exported share service 不提供可用 Binder command API。
- `STATIC`：update receiver/action 进入 update/recovery 域，不是 shell carrier。
- `STATIC`：private Shell page 打开即尝试 root/ADB 检查，并丢失 stderr 和 exit status。
- `STATIC`：private Protocol page 没有 selector/retry 控件，Parcelable 省略 retry 字段；其 push-listen 路径还会写外部日志。

因此相邻包的 exported-caller 路径为 `NEGATIVE`。只有 live whole-APK/version/signer/split identity 全部匹配时，这个负面结论才可迁移到当前设备；身份不同必须重新静态审计，不能直接试运行组件。

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
| 状态 | `NOT ADMITTED`：已离线独立审计，未复制、安装或运行于 RC 2 |

v0.10 请求零 Android permission，只有一个 launcher Activity，没有 service/receiver/provider/native library。应用自身无 socket、localhost port、DUML、Parcel、DJI application transaction、process execution、file persistence、network send、agent attach 或 library load。

手动 snapshot 只读取：

- `protocol` Binder name 的 lookup、ping 和 descriptor 元数据；
- 固定 package/UID/version/signer/ABI/component/path/hash 分类；
- build/debug/SELinux 等固定环境事实；
- 本进程 `/proc/self/maps` 中 exact-basename `libart.so` 的严格双 snapshot、descriptor identity、whole-file SHA-256、GNU Build ID 和固定 range hash；
- 两个固定 Android Settings action 的本地打开结果。

`COMPLETE` 只表示该次只读报告按 schema 完成。Binder descriptor 匹配不证明 transaction authorization；ART identity 匹配不证明 target DJI Fly mapping；package match 不授权 attach；任何结果都不是 RID 状态或写入许可。

v0.8 是历史封存工件，不再是当前 staging instruction。v0.9 的独立审计发现 mapping geometry、timestamp/maps drift 和 auditor coverage 缺陷；这些已在 v0.10 修复并重新测试。

## 9. 未执行的第一包 public-key 假设

相邻 `adbd` switch 中存在独立处理 `AUTH/RSAPUBLICKEY` 的分支，因此“第一包直接 public-key 是否进入授权 UI”是 `HYPOTHESIS`。目前：

- 未向控制器发送该 packet；
- 未生成或复用设备授权 key；
- 未显示授权 prompt；
- 未改变授权数据库；
- 未证明该分支在 live v07 存在或可达。

该动作可能创建持久授权记录，属于 state-changing experiment。若将来单独审批，仍必须使用临时、隔离、不可复用的测试 key，只允许一个 packet，不得组合 `OPEN`、shell、wireless ADB、`tcpip`、bootloader、fastboot、root 或 firmware 操作。测试材料和授权记录不得进入本仓库。

## 10. 下一步门禁

1. `NOT ADMITTED`：如获得单独设备测试授权，只允许 exact v0.10 覆盖安装，要求 schema 正确且 `run_state=COMPLETE`；不先卸载历史 package。
2. `NOT ADMITTED`：建立独立审计的 side-effect-free UID1000 caller，固定 argv，并保留 stdout、stderr、exit status 和时间边界。当前 stock `dpad_fuli` 不满足。
3. `NOT ADMITTED`：v0.10 的 live package、ABI、debuggable、SELinux、ART、target load path 门禁全部匹配后，才可重新审阅 V0 attach canary。V0 成功只证明 loader/JVMTI reachability。
4. `NOT ADMITTED`：不再重复 USB 调试切换、删除 ADB key、offline reconnect、wireless debugging 或 `tcpip 5555`；这些动作不能修复 pre-auth `CNXN` silence。
5. `UNKNOWN`：若通过其他安全入口获得当前 live `adbd`/property/process/log 的只读身份，再比较 adjacent production gate；未匹配前保持 adjacent-version 标签。

Bootloader unlock、OEM unlock、fastboot、Magisk、boot patch、root、remount 和 firmware flash 不属于当前准入路径。

## 11. 公开来源与分发声明

- [AOSP ADB](https://android.googlesource.com/platform/packages/modules/adb/)
- [`Dr-Muh/dji-adb` 固定 revision](https://github.com/Dr-Muh/dji-adb/tree/027c7815568c89e55fff22bfeede9dd294404660)
- [`ya-webadb` 固定 revision](https://github.com/yume-chan/ya-webadb/tree/340d3fe0f0f6a44830ac41965106a2aea41bc484)
- [固件与信任边界](07_FIRMWARE_TRUST_BOUNDARY.md)
- [工件登记](11_ARTIFACT_REGISTER.md)

原始 ADB/USB 抓包、device authorization key、vendor `adbd`、APK/DEX、init/SELinux 文件和反汇编日志均不进入本仓库。
