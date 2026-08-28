# RID raw-GET quiescence model 独立审计

日期：2026-08-28（Asia/Shanghai）
审计完成时间：2026-08-28 14:02 CST
对象：`rid_raw_get_quiescence_model` host-only synthetic trace verifier
最终版本：`0.1.1`
结论：**修复后 PASS；仍然 NOT ADMITTED，不构成任何 live GET/SET/attach 授权**

## 1. 范围与方法

本次审计先保持源码不变，逐行检查 `README.md`、`TEST_REPORT.md`、五个打包 Python source、
测试和构建/打包审计脚本，再与 `../eid_raw_get_quiescence_design_20260828.md` 的 25 条 invariant、
51 个固定结果码、24 个 required interleaving、唯一 success 谓词和零 retry 合同逐项比较。

随后独立构造原测试没有覆盖的 adversarial traces。发现 material fail-open 后，先向主任务报告，
再用 `apply_patch` 修复并扩充固定测试、manifest schema 与 packaged audit。整个过程没有连接设备、
运行 ADB、读取 DJI 进程/动态库、安装或 attach APK、调用 Binder/socket/协议接口，也没有产生任何
DJI 或 RID 流量。

## 2. Findings（按原始严重程度排序）

### [High，已修复] F1：registration 前的 SDK callback admission 可被误接受

原 `0.1.0` 只在 `REG_COMPLETE` 检查 `callback_total == 0`，没有检查
`sdk_callback_admitted == 0`；`SDK_ADMIT_ENTER` 本身也没有要求
`registration_complete == true`。因此把最小接受 trace 的 `SDK_ADMIT_ENTER` 移到
`REG_COMPLETE` 之前，原模型仍返回：

```text
accepted=True
phase=QS_QUIESCENT_VALID_RESPONSE
invariant_failures={}
```

这直接违反设计中 RegistrationWitness 的“no callback admission/helper entry/terminal before this
point”以及 `I07_NO_EARLY_CALLBACK`。

同一入口也没有核对 handle、pending-node 和 callback-owner。保持 generation 不变、只把任一 tag
替换为错误值时，原模型仍可接受。

修复：

- `SDK_ADMIT_ENTER` 在 registration complete 前立即永久触发
  `Q_CALLBACK_BEFORE_REGISTRATION`；
- admission 入口核对 generation、handle、pending-node、callback-owner 与完整 token identity；
- `REG_COMPLETE` 同时要求 SDK admission/helper in-flight 均为 0、terminal 仍为 `NONE`；
- SDK admission、helper、terminal、helper exit、Stopper removal 与 admission exit 绑定到同一条已覆盖
  callback thread；错误或中途换线程返回 `Q_CALLBACK_THREAD_UNPROVEN`；
- 新增固定 regression tests。上述原始 traces 现在全部 `accepted=false`。

### [High，已修复] F2：JSON schema 会把伪装类型转换成有效 witness

原 `TraceEvent.from_dict()` 对整数使用 `int()`、对字符串使用 `str()`。因此把最小接受 trace 的
所有整数序列化成 JSON string，仍会得到有效接受；`seq: true` 也会因为 Python
`bool` 继承 `int` 而变成整数 `1`。

这不触及设备，但会破坏一个安全 verifier 的 fail-closed 输入合同：上游字段类型错误可以被悄悄
规范化成安全见证。

修复：

- 七个整数 event 字段 exact-type 为 `int`，明确拒绝 `bool`；
- 七个字符串 event 字段 exact-type 为 `str`；
- coverage latch 只能是无重复的字符串数组；
- `details` 收敛为 43 个固定字段及 `bool/int/str` exact-type 表，未知字段拒绝；
- 直接构造 `TraceEvent` 也在 `consume()` 入口重新验证，不能绕过 JSON loader；
- 顶层 JSON 只接受精确的 `schema` 与 `events` 两个字段；
- exact schema 表写入 artifact manifest，并由独立 literal-table audit 复核。

数字字符串、bool-as-int、非字符串 identity/latch、错误 details 类型、未知 details 和顶层额外字段
现在均抛出 `ValueError`/CLI input error，不能进入 reducer。

### [Medium，已修复] F3：registration witness 未绑定 exact worker

原模型接受由 coordinator thread 提交的 `REG_HOOK` 或 `REG_COMPLETE`。它还允许 registration
hook 缺少 request fingerprint，pending presence 缺少 worker witness，Stopper presence 缺少同一
mutex 的 membership witness，以及 callback owner 缺少独立 owner witness。

修复：

- `INITIAL_ENTER`、`DISPATCH`、`REG_HOOK`、pending/Stopper/owner witness、`REG_COMPLETE`、
  pending absence 与 fence start 都核对 exact worker object/control/thread、session/connection epoch、
  route hash 和 owner/logical identity；
- `REG_HOOK` 只允许一次，并要求 exact registration、request fingerprint match、相同 operation
  generation 和三个非空 identity tag；
- pending presence 要求 worker-domain witness；Stopper presence 要求同一 mutex 下 positive
  membership；callback owner 要求 independent owner witness；
- off-worker、缺 fingerprint 和 presence-witness mutations 全部拒绝。

### [Medium，已修复] F4：`I24_NO_REENTRY` 过度依赖输入自报

原实现只有在 event 自带 `details.in_callback=true` 时才识别 callback 内 dispatch/cancel/wait/fence
post/route-change。修复后，除显式标记外，模型也根据 `helper_callback_inflight > 0` 与已绑定 callback
thread 自动识别 reentry；fence start 也增加完整 worker-token 校验。

### 修复后未发现未解决的代码级 acceptance bypass

复测没有再找到能够绕过唯一 success 谓词的 trace。这个结论仅限离线 reducer；它不证明未来 live
hook 产生的 witness 真实、完整或无竞态。

## 3. 设计一致性

| 检查项 | 结果 |
| --- | --- |
| fixed invariants | 25/25，名称及顺序与设计文档完全一致 |
| fixed result codes | 51/51（含唯一成功码 0），名称/数值/顺序完全一致 |
| states / declared transitions | 21 / 20，packaged literal table audit PASS |
| event reducer coverage | 49/49 event type 有显式 handler，无遗漏/额外 handler |
| required rejected interleavings | 24/24 rejected |
| minimal valid trace | 仅在 fence + native-unregistration + lease-release 后接受 |
| minimal witness deletion | 24/24 单 event 删除均不接受 |
| response drain permutations | 仅 1/24 精确安全顺序接受 |
| registration witness permutations | 6/6 顺序无关但 witness 必须齐全 |
| fixed trace prefixes | 428 个 prefix 全部落在封闭三值 vocabulary |
| EOF/silence | 重复读取 report 不改变状态，不合成 absence/quiescence |
| dispatch/retry/cancel | dispatch 最多一次、transport retry 固定 0、cancel 最多一次且永不成功 |

`accepted=true` 的 trace 按设计保留 `classification=ACTIVE`，因为 prefix classification vocabulary
只有三值；调用者必须同时读取 `accepted`、`phase`、`quiescence` 与 `retention`。README 已明确说明，
本次没有把它误当成 live activity。

## 4. 独立 mutation 结果

固定 regression suite 新增并拒绝 17 个 adversarial witness/schema mutations：

1. SDK admission 早于 registration complete；
2. admission handle 错误；
3. admission pending-node 错误；
4. admission callback-owner 错误；
5. callback path 未覆盖；
6. callback 执行中途换到另一线程；
7. `REG_HOOK` 离开 exact worker；
8. `REG_COMPLETE` 离开 exact worker；
9. request fingerprint mismatch；
10. integer serialized as string；
11. JSON bool 冒充 event integer；
12. 非字符串 thread identity；
13. 非字符串 coverage latch；
14. bool 冒充 `details.transport_retry` 整数；
15. 未登记 details 字段；
16. 直接 dataclass 构造 bool-as-int；
17. 顶层 JSON 额外字段。

此外手工复核了 registration generation 错误、pending worker witness 缺失、Stopper mutex witness
缺失、independent owner witness 缺失与重复 registration hook；全部 `accepted=false`。

最终 packaged pyz 也直接通过 stdin 复测：early-admission trace 返回 exit 0 但
`accepted=false / primary=Q_CALLBACK_BEFORE_REGISTRATION`；把 `seq` 改成 JSON string 时返回
exit 2 与 `INPUT_OR_MODEL_ERROR`，说明修复不是只存在于未打包工作树。

## 5. 两次 clean test/build 与复现性

在最终源码上独立运行两次：

```sh
env PYTHONDONTWRITEBYTECODE=1 ./scripts/test.sh
```

两次结果相同：

```text
unittest 17/17 PASS
required interleavings 24/24 rejected
packaged audit PASS
每轮各自的两个 clean artifact byte-identical
```

四个临时 clean artifact 与最终 `dist` 产物哈希一致：

```text
dist/rid-quiescence-verifier.pyz
bytes 92576
SHA-256 86ad845afe57de4a693fe0183e6e1ebe507d95b4805d20bd3ef97a93f9205218
packaged source-set SHA-256 715358335a4203506725f6ad95ee917370eedb918184b8197d75c7c7bb209bd0
```

五个 packaged source 的独立 SHA-256：

| source | SHA-256 |
| --- | --- |
| `ridq/__init__.py` | `302bfdcf5971fb9bb832cdba55cdef588eb84638f3faafc6fc0faff711d4b1cd` |
| `ridq/__main__.py` | `92a141c2d363f80fd10fce6385f01a373854787dcdc45ebe9729d4cf292e1ed2` |
| `ridq/constants.py` | `5e4f1a05dbab21b8c04cc0f3bc62e9aa57b51dda6282cf6189f8f3664aed496e` |
| `ridq/fixtures.py` | `6928b972d4137136526d3a2d5f59140a239165ab9fb4df91ab57da29eb1b78ee` |
| `ridq/model.py` | `4d733a813a12637451988cdbc9636daec860d6b6302a20c6c17d613ba53685bb` |

独立从工作树按 `relative-name + NUL + bytes + NUL` 重算 source-set digest，与 manifest 完全一致；
逐项比较 archive source 与工作树 source，mismatch 为 0。

## 6. Artifact / surface audit

最终 pyz 只有七个固定 ZIP entry：top-level `__main__.py`、`model_manifest.json` 和五个 `ridq/*.py`。
全部 timestamp 固定为 `1980-01-01 00:00:00`，全部 `ZIP_STORED`。检查结果：

- 不是 ELF/DEX，entry 中没有 `.so`、`.dex`、`.class`、`.pyc`；
- 没有 `JNIRawData`、send/cancel native symbol、`dlopen`、`ctypes`、`cffi`、Binder descriptor、
  `/dev/` 或 localhost token；
- AST import 仅为 Python 标准库与本包模块；
- 没有 socket、network、subprocess、process execution、dynamic native load 或 transport call；
- CLI 唯一外部输入面是用户指定的 synthetic JSON 文件/stdin，唯一输出是 JSON stdout/stderr；
- packaged literal audit 复核 model version、state/transition/invariant/result-code 表、event/detail schema、
  source-set digest 与 ZIP metadata。

## 7. 残余边界

1. verifier 消费的是 synthetic/replayed attestation；它不能自行证明 live hook 没有撒谎、漏事件或
   发生未覆盖 race。
2. 设计文档第 10 节列出的 live registration/pending/Stopper/callback/epoch/fence/binding API blockers
   仍然存在；本模型不关闭其中任何一项。
3. `PREFLIGHT_PASS`、`LEASE_ACQUIRE` 等事件是上游可信 witness 的抽象，不是本程序实现的设备探针。
4. 本产物仍不应复制到 RC 2、安装、attach 或与任何 GET/SET carrier 合并。
5. 本次审计只证明 `0.1.1` 上述精确 source/artifact；任何源码变化都必须重新构建、复核并更新 hash。

最终判断：修复后的 host-only verifier 可以作为 future live-hook 设计的离线逻辑测试基线；它本身
既不是 Remote ID 开关，也不是实机 read-only GET admission。
