# ELF analysis helpers

Small host-only tools used to inspect AArch64 ELF64 files and preserve one exact DJI Fly 1.21.10
runtime-route admission manifest. No ELF, APK, firmware, disassembly output, or generated binary is
included here.

## Status

- `STATIC`: the Python tools and committed JSON/Markdown manifest are independently maintained
  analysis material.
- `NOT ADMITTED`: symbol/RVA/signature matches are an exact-build software admission check, not a
  live RC 2 route, protocol success, or Remote ID RF result.

| File | Purpose | Dependency |
| --- | --- | --- |
| `disasm_aarch64_elf_range.py` | Disassemble a file-backed virtual-address range from one ELF64 `PT_LOAD`. | Python 3.10+, `capstone` |
| `scan_aarch64_string_xrefs.py` | Scan executable segments for direct AArch64 ADR/ADRP references. | Python 3.10+, `capstone` |
| `elf64_va_read.py` | Translate an ELF64 virtual address through `PT_LOAD` and print bytes. | Python standard library |
| `elf64_reloc_inspect.py` | Inspect section-backed ELF64 RELA entries by target/range. | Python standard library |
| `runtime_route_manifest_20260828.py` | Rebuild, verify, or inventory the pinned loader-style runtime-route manifest. | Python standard library plus the exact external input ELF files |
| `runtime_route_manifest_20260828.json` | Committed exact-build identity, loader, dynsym, RVA, and short entry-signature records. | Data only |
| `runtime_route_manifest_20260828.md` | Human-readable rendering of that manifest and its runtime-consumer boundary. | Documentation |

Install Capstone in an external virtual environment when using the two instruction tools:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install 'capstone>=5,<6'
```

## Exact-input boundary

The runtime manifest intentionally names three exact DJI Fly shared libraries by relative path,
size, SHA-256, GNU build ID, and symbol signatures. Those vendor files are excluded from this
repository. To run `--verify`, `--self-test`, `--write`, or `--inventory`, a researcher must supply
lawfully obtained exact files under the relative paths encoded in `MODULE_SPECS`; a missing or
different file fails closed. Never commit those inputs or the output of disassembly/inventory runs.

## Checks

The self-contained checks are:

```sh
python3 -m py_compile *.py
python3 disasm_aarch64_elf_range.py --help
python3 elf64_reloc_inspect.py --help
python3 elf64_va_read.py --help
python3 scan_aarch64_string_xrefs.py --help
python3 runtime_route_manifest_20260828.py --help
```

There is no bundled vendor fixture, so the manifest's `--verify` and corruption `--self-test` modes
are deliberately not self-contained. With the exact external files present, run them from this
directory as documented in `runtime_route_manifest_20260828.md`.
