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
- `STATIC`: the earlier 0205 extraction yields a readable Android11 A/B OTA with29 partitions and
  `adbd`/`dpad_fuli` matching A-030/A-031. C-319 is limited to clear outer headers: A-005/0200 has an encrypted
  TBIE/FLYA inner container (C-454). C-322's all-RC-plaintext conclusion is retracted.
- `NEGATIVE`: WA150 `0802`/`2603`/`0806` are `enc_key=STUE`; no public `STUE`, brute zero-hit.
- `NEGATIVE`: wa150 3072-bit PRAK absent from the public auth corpus.

The pinned out-of-repo tool is unmodified upstream; a local copy carries one PKCS1-v1.5 fallback
because wa150 signs PKCS1 while header_version2 makes the tool assume PSS. The patch is outside this
repository. Downloaded firmware, decrypted output, partitions and reports are all gitignored here.
See `firmware/EXTRACTION_NOTES.md` for the local layout. Nothing is returned to a device.

## 2026-10-17 audit correction (C-442--C-449)

The audited commit is `5d761a1e31c65ab3cec4d1d8caa2bbe5ac23c76e`. The original A-068 probe cannot reproduce its
claimed sweep: a real 435,382-byte logical chunk fails its NumPy checksum, the derived key is unused, and ECB misses
one direction. Architecture selection, command-line payload size and dependency documentation also required repair.
A-067's existing primitive checks remain distinct from STUE proof. Final corrected identities and validation are
recorded separately in C-447 and the artifact register. The corrected directory suite passed 53/53; a real 2603 run
launched from arm64 completed through Rosetta with encrypted checksum MATCH and ten fixed-WAES misses. The native
AES-256 zero-IV known-answer test, 600000-byte stdin transfer and 435392-byte real-chunk length check passed.
These checks neither test a derived-key model nor establish STUE plaintext.

The NFZ callback uses a constant 32-byte key and a zero IV. MD5 is logging. Its vtable must be addressed 16 bytes past
the symbol; data comes from the buffer, not runtime pointer/stack bytes. NFZ is one type-dispatch branch, not a proven
WA150 firmware decrypt path. One direct NFZ-key attempt on 2603 failed the plaintext checksum; STUE remains unresolved.

## 飞机侧 STUE 续跑检查点

飞机侧（wa150）STUE 破解仍在进行，完整坐标/证据编号/下一步/勿重做清单见
[AIRCRAFT_STUE_CHECKPOINT.md](AIRCRAFT_STUE_CHECKPOINT.md)。

- RC331 静态样本可研究；不能表述为 RID 控制已完成。
- WA150 STUE 尚未解开。普通固件的实际处理路径与 key/mode 映射仍需证据。
- 地址、栈尾和每轮 init 模型已撤回；当前无设备，全部工作保持离线。

## 2026-10-17 public-v2 and method-4 progress (C-450--C-453)

A-082 adds a macOS CommonCrypto single-candidate implementation of the pinned public IMaH-v2 model. Six new tests,
including a frozen independent OpenSSL mixed-chunk/gap/nonzero-padding fixture, passed within the 59-test suite.
The checker verifies payload SHA256 and encrypted checksum before candidate evaluation; it reads keys from stdin,
exports no key/plaintext, and does not verify signatures or establish STUE applicability.

On the exact real 2603 sample, NFZ32 as KEK and WAES-decrypt/encrypt(scram) as content keys all miss the expected
plaintext checksum. These are exactly three candidates, separate from direct-CBC and fixed-WAES experiments.
The inspected Assistant method-4/register-upgrader path preserves input/cache bytes through tar/FTP; no STUE decoder
was recovered within that bounded path. It is not proof of WA150 runtime method choice or all-Assistant absence.
The public refresh inspected 25 selected source files after screening 517 fork metadata rows; no new STUE mapping
was found. STUE plaintext, the actual consumer/key owner and all device/RID behavior remain unresolved.

## 2026-10-17 RC331 inner-container and QSEE findings (C-454--C-457)

A-005/0200 has a clear outer container but an encrypted TBIE/FLYA inner layer at offset480, ciphertext at960.
Outer and inner integrity checks pass; inner plaintext is not recovered. C-319 is outer-only and C-322 is retracted.
Six public-TBIE prefix probes are not six full-checksum negative results.

Existing A-004 OTA/property/partition hashes were rechecked and A-083 bw_secure, A-084 libtee_util.so and A-085
dji_decrypt extracted as local ELF64/AArch64 inputs. No new download, vendor execution, live identity or RSA
reverification occurred. The static client/QSEE chain reaches protected RPMB-root/HUK-backed TBIE CMAC derivation;
root input and STUE's own owner/derivation remain unknown. Cipher mode constants1/2 are not independently named.
The fixed480-byte client does not directly fit WA150's608-byte header/signature layout. This is no STUE decoder or
root-key recovery, and does not rule out all other offline approaches.

## Separate SDK/position work (C-458--C-462)

The pinned SDK Get(0x37) now runs in isolated ARM64 emulation and returns a32-byte value checked by roundtrips and
rewrap. This disproves A-078 v2's direct ciphertext-prefix key choice. C-464/C-465 later recover22-byte input/84-byte
payload composition and repair v3 with4 passing host tests plus controlled native components/fragments; no full handler,
transport or RF execution follows. It remains separate from the static bw_secure position-envelope branch.
The inspected GPS-update transfer path and bounded independent-source survey add no STUE consumer within their
scopes. The control-panel objective retains full per-control device/RF acceptance; no device is currently available.

The2026-10-18 status-parser validation is a separate36-host-test run (C-463); together with4 position tests this batch
has40 host tests. The earlier59 firmware tests (C-450) were not rerun or merged into a single larger run.

## Current bounded inputs after C-466--C-470

A-090 Android upgrade selected bodies do not expose a concreteSTUE consumer; this is not a whole-SDK conclusion.
Location producer/type/provider/epoch-second and conditionalHostID/payload fixes are independent offline work,not
STUE plaintext or real control-panel success. Existing C-126 scales remain valid; C-473 later advances selected
Java/default-provider semantics while actual provider/altitude validity/reference and device/RF correspondence remain open.

Official1200 reacquisition matches existing A-066/C-323 bytes. Only A-092 smallest1100 wa140bat is a new distinct
container. Both areSTUE with payload/encrypted integrity checks; neither was RSA-verified,key-tried or decrypted.
Five other1100 variants remain uninspected; wa140bat is a compatibility entry,not nativeWA150 hardware evidence.

## Separate carrier/Java continuation (C-471--C-473)

22 carrier directory/map records and four analysis-only views are checked. Selected Java provider/cache bodies
connect to the native position boundary; valid Android/default altitude has a conditional meters/WGS84 contract.
The inspected method has no hasAltitude check and can mix newer network coordinates/time with older GPS altitude.
New message timestamps do not prove fresh fixes. This is static app-location evidence, not original DEX/firmware
recovery, STUE decryption or actual device/RF control. Existing firmware/root-input blockers are unchanged.
