# Next-agent prompt

你正在接手用户自有 DJI RC 2 `07.00.0100` / Mini 5 Pro 的 Remote ID 互操作性研究。最终目标是
实现并验证一个稳定、可读回、可恢复的 RID 测试开关和控制面板。直接在仓库当前 `main` 上继续，
先读 `CODEX_PROJECT_PROMPT.md`、`AGENTS.md`、`docs/13_HANDOFF.md`、
`docs/12_CURRENT_BLOCKERS.md`、`docs/19_RID_EXPERIMENT_CONTROL_MATRIX.md`、
`docs/20_OFFICIAL_FLYSAFE_UI_PATH.md`、`host-tools/rid-switch-tool/README.md` 及 C-188--C-211；
不要重做已有阴性实验。

当前最重要的事实：用户已用标准 RID 接收器确认 Mini 5 Pro 在起桨后发送可读 Basic ID 的明文
ASTM F3411 / EN 4709 Remote ID，但 exact bearer 和书面 motor on/off A-B-A 尚未记录（C-207）。
WA150 表中已找到 `EU_CE_enable_c0_rid` by-index 候选及 `_0` by-hash 路线，host A-B-A tools 和
Android panel codec 已完成静态/合成测试（C-192--C-199），尚无 live read/write；它们是 EU C0
policy candidates，不是已证明的 global switch。exact DJI Fly `1.21.10` 的 same-process FlySafe
query/现有-ID setter owner 也已闭合；ART TI query 在 emulator 的有效 `apk_data_file` 路径上收到
callback `417` 且 PID 不变，但当时没有飞机。普通安装路径、`trace_data_file`、uncommitted
`apk_tmp_file` 三条 loader 路线已退役（C-208--C-210）。外部 Binder F7/F8、`0x11/0x1C`
listener 和 fixed `0x11/0x11` 也已有窄阴性，不要换地址盲试。

下一步先补一份标准 RID receiver 的 motor-off -> motor-on -> motor-off 记录，固定 bearer、Basic-ID
存在性和时间；不要记录真实 ID。随后以 read-only positive control 判定 by-index/by-hash 哪条 WA150
route 可达，未取得同会话 metadata、baseline 和 readback 前不得写。并行确定 RC 2 上 DJI Fly 与
Developer Assistant 的真实 signer/SELinux domain，计算合法 delimiter-free path/descriptor 交集；
若不存在，转向 userspace-ADB 或已有 system-mediated loader。首次 ART TI 实机只 query，必须取得
fresh callback 且 attach 前后 PID 相同。只有 canonical genuine type-6 item 或经读回闭合的明确
aircraft policy candidate 才能进入 baseline -> change -> readback -> restore -> final readback，
最后由用户起桨、标准 RID 接收器做 RF A-B-A；不得伪造、导出或重放 license/账号材料。

禁止解锁 Bootloader、OEM Unlock、bootloader reboot、修改或刷写 boot/vendor_boot/vbmeta/TEE/
QFPROM/eFuse、Magisk。厂商 APK/固件/DEX/反编译源码、raw log/capture、设备/账号/license 标识不得
进 GitHub。保持实验脚本小：观察 -> 单变量实验 -> 记录。每个发现同步 Markdown、claims/artifacts
CSV、timeline/negative/blocker/handoff/changelog，运行仓库四项校验后提交并推送；需要实机、起桨
或外部接收器时，把所有人工步骤整理成一次请求再通知用户。
