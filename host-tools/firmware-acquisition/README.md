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
- matching `test_*.py` files: offline tests with synthetic HTTP responses and synthetic metadata.

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

## Distribution boundary

All generated JSON reports, firmware/module bodies, partial downloads, and output directories are
excluded by the local `.gitignore`. Do not commit them. The root MIT license covers these original
helpers and tests, not DJI Assistant, metadata responses, or downloaded DJI artifacts.

Run the self-contained tests with:

```sh
python3 -m unittest discover -s . -p 'test_*.py'
```
