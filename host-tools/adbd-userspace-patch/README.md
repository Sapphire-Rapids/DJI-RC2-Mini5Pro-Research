# RC331 v07.00.0100 `adbd` CNXN gate — offline userspace-copy patch

This directory contains a narrow offline experiment. It creates a separate `adbd` file in which
one conditional branch is changed; it does not install, execute or flash anything.

The exact RC331 v07.00.0100 APEX `adbd` has this control flow in `handle_packet(CNXN)`:

```text
ro.boot.mp_state == "production" && ro.boot.dbg_cnt < 1
    -> gate flag = 1

cbz gate, normal_connection_path
    -> DJI early-return/log path

normal_connection_path
    -> TLS check / auth_required check / send_auth_request
```

The patch leaves those branches and all of their targets intact. It changes only the instruction
which materializes the gate value:

```text
vaddr/file offset 0x90460
before  f5 a7 9f 1a    cset w21, lt
after   f5 03 1f 2a    mov  w21, wzr
```

The gate therefore remains false. Its normal branch target remains `0x904d8`, which retains the
existing TLS and ADB authentication state machine. This also preserves the compiler's secondary
gate check after temporary-string cleanup instead of altering one of two control-flow checks.

## Exact-v07 identity and provenance

The exact v07.00.0100 firmware extraction is locally traceable through these immutable identities:

```text
outer download
  V07.00.0100_rc331_dji_system.bin
  SHA-256 296cfa63e3c6b011fd1ee8dd911c11f64dac9d34a8424a6fbb95b0c237ab1ae3

embedded signed package
  rc331_0205_v08.00.01.20_20250828.pro.fw.sig
  SHA-256 69988bff127293e4c512642df0b335aad2b8196105df050c573b591648a0e33a

extracted system image
  SHA-256 755554a902df526cbd37e1c22aeda8b3cea6122c66ec3e2aa0f56d720c10ebb3

APEX adbd payload
  bytes    1,497,232
  SHA-256 b300d9bb90f5941fe2952bc9f6dacc30e639a498be4435f59a4ae95134bd5422
  Build ID c30245f84b2d2ddcecbcd9f640a84192
```

The outer aggregate was downloaded through the third-party Dank Drone Downloader selector and
matched its published SHA-256. More importantly, `rc331.cfg.sig` and the `0205` module were then
verified with `dji_imah_fwsig.py`, DJI public-release key `PRAK-2020-01`, without
`--force-continue`; header signature, stored/encrypted-data checksum and decrypted/plaintext
checksum all passed. The Android update payload was extracted to `system.img`, and `adbd` was read
directly from `/system/apex/com.android.adbd/bin/adbd` with `debugfs`. The verification boundary,
hashes and extraction summary are recorded in
[`docs/08_ANDROID_ADB.md`](../../docs/08_ANDROID_ADB.md). Firmware, the original executable and
the generated derivative are intentionally not distributed in this repository.

The v07 `adbd` is byte-for-byte identical (`cmp` exit 0 and equal SHA-256) to the previously
inspected adjacent RC331 `10.00.0700/0205` APEX payload. The earlier disassembly is therefore exact
for this v07 payload rather than merely a cross-version inference.

The executable is supplied by the `com.android.adbd` APEX. The exact v07 init fragment states:

```text
service adbd /apex/com.android.adbd/bin/adbd --root_seclabel=u:r:su:s0
```

Therefore the target-package runtime path is `/apex/com.android.adbd/bin/adbd`, **not**
`/system/bin/adbd`. In the extracted system image the backing file is logically
`/system/apex/com.android.adbd/bin/adbd`.
The extracted target system image contains no `/system/bin/adbd` entry.

## Why the script does not use a fixed offset

Before producing a copy, `patch_cnxn_gate.py` requires all of the following in the input ELF:

- AArch64 and an unstripped, unique `handle_packet` symbol;
- unique `ro.boot.mp_state`, `production` and `ro.boot.dbg_cnt` strings;
- one ordered `ADRP+ADD` reference to each string inside `handle_packet`;
- one `cset ..., lt` for the `dbg_cnt < 1` result and one following `cbz` using that same register;
- the branch's normal target reaching the named `send_auth_request` function.

If any condition differs, it exits without an output. Even though the exact v07 sample is now
known, the script still recognizes it semantically rather than trusting a fixed offset alone.

## Exact-v07 procedure (offline only)

Use the extracted exact-v07 payload above, or copy `/apex/com.android.adbd/bin/adbd` from the RC 2.
First record its untouched hash, then run a dry analysis:

```bash
shasum -a 256 adbd-v07-original
python3 patch_cnxn_gate.py adbd-v07-original
```

Only if the reported strings, branch and `send_auth_request` path are coherent, create a new copy:

```bash
python3 patch_cnxn_gate.py adbd-v07-original \
  --output adbd-v07-cnxn-gate-bypass \
  --manifest adbd-v07-cnxn-gate-bypass.json
```

Static verification is included: the manifest records both SHA-256 values, virtual/file address,
branch target, before/after bytes and disassembly, and all changed byte offsets. The script requires
all changed bytes to remain inside that one four-byte instruction. It refuses in-place patching and
refuses to overwrite an output.

The ELF's embedded GNU Build ID is not recomputed by this byte patch and therefore still names the
original link output. Use the manifest's whole-file SHA-256, not the Build ID, as patched-copy identity.

No file produced here should be put on or run by the RC 2 until the exact-v07 analysis and a separate
execution plan have been reviewed.

## Tests

```bash
python3 -m unittest -v test_patch_cnxn_gate.py
```

The pure instruction-vector test always runs. Exact-sample tests are enabled only when the
researcher supplies the excluded input through `RC2_ADBD_V07`; `RC2_ADBD_ADJACENT` is optional:

```sh
RC2_ADBD_V07=/path/to/extracted/adbd \
RC2_ADBD_ADJACENT=/path/to/optional/adjacent/adbd \
python3 -m unittest -v test_patch_cnxn_gate.py
```
