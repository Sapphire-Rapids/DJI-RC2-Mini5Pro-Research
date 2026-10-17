# Status

- `STATIC`: the public tree contains independently written clients, compiled target locks, and
  synthetic tests only.
- `OBSERVED`: local research runs previously retrieved metadata and locked artifacts, but none of
  those responses or artifacts are redistributed here.
- Repository validation is offline. It does not contact DJI or require the Assistant application.
- The downloaders have no device transport, upgrade, flashing, or installation path.
- A downloaded filename/hash lock identifies an artifact; it does not establish patchability,
  flashability, RID ownership, or live-device behavior.

## 2026-10-16 firmware fetch + RC decrypt (C-316--C-322)

- `OBSERVED`: all six current modules fetched and independently re-hashed to the register.
- `STATIC`: RC331 `0205`/`0200` and the RC331 aggregate modules are plaintext; `0205` fully decrypts
  (no force, three layers) to an Android11 A/B OTA,29 partitions dumped, `adbd`/`dpad_fuli`
  byte-identical to A-030/A-031.
- `NEGATIVE`: WA150 `0802`/`2603`/`0806` are `enc_key=STUE`; no public `STUE`, brute zero-hit.
- `NEGATIVE`: wa150 3072-bit PRAK absent from the public auth corpus.

The pinned out-of-repo tool is unmodified upstream; a local copy carries one PKCS1-v1.5 fallback
because wa150 signs PKCS1 while header_version2 makes the tool assume PSS. The patch is outside this
repository. Downloaded firmware, decrypted output, partitions and reports are all gitignored here.
See `firmware/EXTRACTION_NOTES.md` for the local layout. Nothing is returned to a device.

## 飞机侧 STUE 续跑检查点

飞机侧（wa150）STUE 破解仍在进行，完整坐标/证据编号/下一步/勿重做清单见
[AIRCRAFT_STUE_CHECKPOINT.md](AIRCRAFT_STUE_CHECKPOINT.md)。

- 遥控器侧（rc331）enc_key 为空、已明文解出，无阻碍。
- 飞机侧四份模块（0802/1200/2603/0806）全部 STUE 加密，卡点即 STUE key 的 seed 运行时地址字节。
- 当前残留三项：结构体指针字节、12 字节未初始化尾、`init` 是否每轮清零（先判后者）。
