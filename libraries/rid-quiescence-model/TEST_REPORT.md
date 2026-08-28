# Test report

日期：2026-08-28（Asia/Shanghai）

命令：

```sh
./scripts/test.sh
./scripts/build.sh
```

结果：

```text
unittest: 17/17 PASS
required rejected interleavings: 24/24 rejected
minimal accepted trace: PASS
witness-deletion mutations: 24/24 not accepted
fixed invariants exercised: 25/25
fixed-trace prefixes classified: 428
response drain permutations: 1/24 accepted (the exact safe order only)
independent adversarial mutations: 17/17 rejected
  - early SDK admission; wrong callback handle/node/owner
  - off-worker registration hook/completion; missing request fingerprint
  - uncovered/drifting callback thread
  - numeric-string, bool-as-int, wrong identity/latch/details types and unknown fields
clean builds: byte-identical
packaged audit: PASS
```

产物：

```text
dist/rid-quiescence-verifier.pyz
bytes: 92576
SHA-256: 86ad845afe57de4a693fe0183e6e1ebe507d95b4805d20bd3ef97a93f9205218
packaged source-set SHA-256: 715358335a4203506725f6ad95ee917370eedb918184b8197d75c7c7bb209bd0
```

安全说明：本次构建和测试只处理本目录 synthetic events；没有连接设备、运行 ADB、加载 DJI SO、
安装或 attach APK，也没有产生任何协议流量。
