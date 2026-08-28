# IMaH analysis wrappers

These independently written offline wrappers inspect DJI IMaH containers and can create one
deliberately non-flashable integrity experiment. They do not include firmware, keys, a flasher, an
upgrader, or the upstream parser.

## External dependencies

Clone [`o-gs/dji-firmware-tools`](https://github.com/o-gs/dji-firmware-tools) separately and check
out commit `195692263c2684cf1ddc4995f2736be6c0fb135e`. That upstream project is GPL-3.0 licensed and
is intentionally not vendored here. Point this wrapper at the checkout with:

```sh
export DJI_FIRMWARE_TOOLS_DIR=/path/to/dji-firmware-tools
python3 -m pip install -r requirements.txt
```

The root repository's MIT license applies only to these original wrapper/test files. It does not
relicense `dji-firmware-tools`, DJI firmware, keys shipped by another project, or generated data.

## Tools

- `imah_patchability_audit.py` parses declared layout, checks public integrity fields, and tries
  authentication-key variants exposed by the pinned upstream parser. It does not extract, decrypt,
  modify, repack, sign, transfer, or flash an image.
- `imah_nonflashable_patch_probe.py` changes one selected byte in an encrypted payload copy and
  recomputes only public integrity fields. Its output must end in `.nonflashable.bin`; the original
  signature is preserved and therefore invalid for the changed signed region. Never flash it.

Example read-only audit:

```sh
python3 imah_patchability_audit.py /outside/the/repository/module.pro.fw.sig
```

The non-flashable probe requires `--confirm-nonflashable` and refuses to write inside this Git
repository. Firmware, generated reports, and non-flashable binaries remain outside version control.

Tests are self-contained in the sense that they pass without firmware; artifact-dependent cases are
reported as skipped. With local excluded fixtures present they exercise the full parser path:

```sh
python3 -m unittest discover -s . -p 'test_*.py'
```
