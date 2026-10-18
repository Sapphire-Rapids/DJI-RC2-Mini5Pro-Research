# Firmware acquisition helpers

These independently written Python tools reproduce the narrow metadata and target-locked download
steps used during RC 2 / Mini 5 Pro research. They do not contain DJI binaries, firmware, extracted
DJI application material, credentials, live tokens, or opaque CDN request paths.

## Requirements

- macOS with Python 3.10 or later;
- a DJI Assistant 2 installation that the operator obtained and installed lawfully;
- `/usr/bin/otool`, used to inspect the operator's local Assistant installation;
- network access for `--fetch-metadata` and actual downloads.

There are no third-party Python package requirements. `requirements.txt` documents that fact.
Request material is reconstructed in memory from the operator's local Assistant installation. The
tools are written so it is neither printed nor saved.

## Contents

- `dji_official_metadata.py`: metadata-only WA150 client; its module-body route is blocked.
- `dji_rc331_official_metadata.py`: metadata-only RC331 client.
- `dji_target_locked_module_download.py`: target-locked WA150 module downloader.
- `dji_rc331_0700_0200_download.py`: one-target RC331 `0200` downloader.
- `dji_rc331_0700_0205_download.py`: one-target RC331 `0205` downloader.
- `stue_plaintext_probe.py`: bounded fixed-WAES hypotheses checked against IMaH checksums.
- `wb_aes_bridge.py`: local Assistant whitebox block functions through Rosetta/ctypes.
- `aes_decode_bridge.py`: local Assistant AES-256 CBC utility with a required 32-byte key.
- matching `test_dji_*.py` files: offline tests with synthetic HTTP responses and metadata.

Metadata reports must be created locally before a downloader can validate its compiled lock:

```sh
python3 dji_official_metadata.py --fetch-metadata --output wa150_metadata_summary.json
python3 dji_rc331_official_metadata.py --fetch-metadata --output rc331_metadata_summary.json
```

Start with an offline lock check:

```sh
python3 dji_target_locked_module_download.py --version 01.00.0700 --module 0802 --dry-run
python3 dji_rc331_0700_0200_download.py --dry-run
python3 dji_rc331_0700_0205_download.py --dry-run
```

For the WA150 helper, omitting `--dry-run` performs the locked network download. The RC331 helpers
require the explicit `--download` flag. Downloads are written below this directory's excluded
`firmware/` tree and are never transferred to a device by these programs.

## Local crypto probes

The native bridges additionally require Rosetta on Apple silicon, `codesign`, and a universal
Python framework installation with `Resources/Python.app/Contents/MacOS/Python`. They copy and
ad-hoc sign the interpreter and service library in a local mirror; the installed app is unchanged.
Choose a dedicated mirror path with `FIND_UAS_WB_MIRROR`. A completed mirror is reused; an existing
incomplete directory raises an error and is never deleted.

```sh
export FIND_UAS_WB_MIRROR="$PWD/firmware/crypto-mirror"
python3 stue_plaintext_probe.py path/to/module.fw.sig
```

The probe tests ten arrangements of the fixed WAES primitive: four CTR, four CBC and two ECB.
Both primitive directions are tested; CTR counters span padded chunks and CBC resets its IV per
chunk. All plaintext checksums include the decrypted padding. The checksum helper zero-pads a
partial final word, following the [pinned IMaH tool](https://github.com/o-gs/dji-firmware-tools/blob/195692263c2684cf1ddc4995f2736be6c0fb135e/dji_imah_fwsig.py).
It does not test AES under a key derived from `scram`, and a miss only excludes these fixed-WAES
arrangements for that sample. A checksum hit still requires independent plaintext verification.

`aes_decode_bridge.decode2ex(data, key)` requires a 32-byte key and complete 16-byte ciphertext
blocks. Its binary stdin/stdout transport keeps the data and key out of argv. The CLI requires
`--key-file` pointing to a local 32-byte binary file and reports the decoded length of the first
padded IMaH chunk. No default or proven STUE key is supplied.

The separate `imah_v2_key_probe.py` (A-082) tests the pinned public IMaH v2 model with one explicit
candidate on macOS CommonCrypto, with no new dependency. `--key-kind kek` accepts a 16/24/32-byte
KEK and AES-ECB-decrypts `scram` to obtain content16; `--key-kind content` accepts content16 directly.
The raw key is read from stdin. Payload SHA-256 and encrypted checksum must pass first. Its JSON
report contains hashes, ranges, checksums and match status, without key or plaintext bytes.
It does not verify signatures, and this model's applicability to STUE remains unproven.

```sh
python3 imah_v2_key_probe.py path/to/module.fw.sig --key-kind kek < path/to/local-key.bin
```

## Distribution boundary

All generated JSON reports, firmware/module bodies, partial downloads, and output directories are
excluded by the local `.gitignore`. Do not commit them. The root MIT license covers these original
helpers and tests, not DJI Assistant, metadata responses, or downloaded DJI artifacts.

Run the full suite with the native prerequisites above and a dedicated mirror path:

```sh
python3 -m unittest discover -s . -p 'test_*.py'
```

The native tests check WAES roundtrips, a standard AES-256 known-answer vector, and binary transfer
larger than the old argv limit. Metadata/downloader tests and `test_stue_plaintext_probe.py` use
synthetic fixtures and need no Assistant installation. The six `test_imah_v2_key_probe.py` cases
include a frozen independent OpenSSL fixture for mixed encrypted/plain chunks, storage gaps and
nonzero decrypted padding; they use macOS CommonCrypto without Assistant. The recorded suite run
passed 59/59 (C-450), which validates implementation behavior, not STUE keys or device capability.
