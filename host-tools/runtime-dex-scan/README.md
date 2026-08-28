# Runtime DEX boundary scanner

Status: **host-tested analysis helper**. This independently written tool scans an already acquired,
authorized raw-memory file for bounded Android DEX images. It validates only the DEX magic, header
size, endian constant, file size and input bounds, then writes each candidate and reports its
SHA-256. It is not a process dumper, injector, root tool, decompiler or device-control client.

The tool was created after a disposable Android 11 emulator running exact DJI Fly `1.21.10`
demonstrated that ordinary root read access to a private read/write process mapping could recover
protected runtime DEX images. No vendor dump, extracted DEX, decompiled source, account data, device
identifier or local path is included here.

## Run

Use only memory you own or are authorized to inspect:

```sh
python3 extract_runtime_dex.py INPUT_MEMORY.bin OUTPUT_DIRECTORY
```

Run the synthetic unit tests without any vendor input:

```sh
python3 -m unittest -v test_extract_runtime_dex.py
```

Passing this scanner means only that the candidate has a self-consistent outer DEX boundary. It does
not authenticate its provenance, verify every internal DEX table, prove device execution, or grant
permission to redistribute the extracted bytes.
