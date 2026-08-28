# RID raw-GET quiescence model（host-side、zero-send）

状态：**离线模型已实现；仍然 NOT ADMITTED**
版本：`0.1.1`
许可：本目录的独立实现适用仓库根目录 [MIT license](../../LICENSE)。

这个目录只实现一个纯 Python 的 synthetic trace 状态机。它回答的问题是：如果未来 live hooks
能提供一组完整、可信的事件，这些事件是否足以证明一次只读操作已经完成、所有回调与 owner 都已
排空，而且结果可以安全提交。

它不会连接遥控器或飞机，不会加载或链接 DJI 动态库，不会注册 JNI，不会调用设备协议、网络、
Binder、进程控制或 ADB。打包产物只包含 Python 源码和一个常量 manifest，没有 ELF、DEX、class
或 native bytecode。

## 模型边界

- 输入只能是 `finduas-ridq-trace/v1` synthetic JSON/结构体事件。
- event 的整数/字符串字段、coverage latch 与 43 个允许的 `details` 字段都做 exact-type
  校验；Python `bool` 不可冒充整数，数字字符串不会被转换，未知字段永久拒绝。
- `transport_retry` 固定为 `0`，第二次 dispatch 或 retry event 永久拒绝。
- 状态表、51 个固定结果码（含唯一成功码）和 25 条 invariant 全部封闭在 manifest 中。
- 任意 trace prefix 的 `classification` 只能是 `ACTIVE`、`QUIESCENT_REJECTED` 或
  `UNKNOWN_RETAINED`。
- 成功使用独立布尔字段 `accepted=true` 表示。为保持上述三值 prefix vocabulary，成功 trace 的
  `classification` 仍是 `ACTIVE`；应同时读取 `accepted`、`phase`、`quiescence` 和 `retention`。
- EOF、固定等待时间或“后面没有看到事件”不会产生 absence、fence completion 或 quiescence。
- 唯一接受路线需要所有显式 witness，并在 fence 之后做安全 native-binding/mapping retention
  decision。删除最小接受 trace 中任一 event 都不能再接受。

因此，**模型全绿只证明离线状态机逻辑一致，不证明 RC 2 上存在对应 hooks/API，也不批准安装、
attach、GET、SET 或任何实机操作。** 当前 live admission blockers 仍以设计文档第 10 节为准。

## 目录

```text
ridq/constants.py       固定状态、transition、25 invariants、失败码和 event vocabulary
ridq/model.py           纯 reducer 与 JSON event schema
ridq/fixtures.py        最小接受 trace 与 24 个必须拒绝的 interleaving
ridq/__main__.py        JSON-only CLI
tests/test_model.py     unit/property/mutation tests
scripts/build.py        固定 ZIP metadata 的 reproducible Python zipapp 构建器
scripts/audit_artifact.py  独立 literal-table/source/import/artifact 审计
scripts/test.sh         全量测试、两次 clean build 比对及 packaged audit
dist/rid-quiescence-verifier.pyz  可复现 host-side verifier（构建生成，不提交）
```

## 运行

```sh
./scripts/test.sh
./scripts/build.sh
python3 dist/rid-quiescence-verifier.pyz --self-check
python3 dist/rid-quiescence-verifier.pyz --fixture minimal --all-prefixes
python3 dist/rid-quiescence-verifier.pyz --input synthetic-trace.json
```

输入 JSON 顶层必须是：

```json
{
  "schema": "finduas-ridq-trace/v1",
  "events": []
}
```

每个 event 都必须显式包含：

```text
seq, monotonic_ns, op_generation, phase,
thread_identity, worker_identity,
session_epoch, connection_epoch,
handle_tag, pending_node_tag, callback_owner_tag,
event_type, before_count, after_count, coverage_latches
```

`details` 是唯一可选字段。`phase` 表示消费该 event 后声称到达的 phase；reducer 会独立计算并
核对它，输入不能靠伪造 phase 获得接受。

## 测试覆盖

`tests/test_model.py` 固定覆盖：

- 设计第 8.1 节的全部 24 个拒绝 interleaving；
- 最小接受 trace；
- 删除最小接受 trace 每一项 witness 的 mutation tests；
- 25 条 invariant 各自至少一个触发样本，同时最小接受 trace 对全部 invariant 保持 clean；
- registration witness 的全部排列；
- SDK wrapper registration 前准入、错误 handle/node/owner、注册见证离开 exact worker、回调路径
  未覆盖/中途换线程与请求 fingerprint 不匹配的独立 adversarial mutations；
- JSON 数字字符串、bool-as-int、非字符串 identity/latch、错误 `details` 类型、未知字段和顶层额外
  字段的 fail-closed schema mutations；
- response drain 四个关键事件的全部 24 种排列，只有精确安全顺序可接受；
- 关键 witness 的一项/两项缺失组合；
- 所有固定 trace 的每一个 prefix 三值分类；
- EOF 不改变 state、phase 字段不受信任、handle 数值不能替代 generation/owner identity。

## 固定构建结果

```text
dist/rid-quiescence-verifier.pyz
bytes: 92576
SHA-256: 86ad845afe57de4a693fe0183e6e1ebe507d95b4805d20bd3ef97a93f9205218
packaged source-set SHA-256: 715358335a4203506725f6ad95ee917370eedb918184b8197d75c7c7bb209bd0
```

两次独立临时目录构建已由 `scripts/test.sh` 用 `cmp` 证明 byte-identical。若 runtime 源码有任何
变化，上述 hashes 必须重新构建、复核并更新，不能沿用。
