# Protocol probes and parsers

This directory preserves independently written Python codecs, bounded probes, passive listeners,
and their host tests. It contains no DJI binary, decompiled source, captured frame, account data,
or generated output.

## Status

- `STATIC`: the source is an independently written research implementation of the documented wire
  shapes and parsing rules.
- `OBSERVED`: all 68 self-contained host unit tests passed during the public-source import on
  2026-08-29.
- `NOT ADMITTED`: passing those tests does not establish that a Mini 5 Pro accepts a route, that a
  value is applied, or that Remote ID RF behavior changes.

The tools do not all have the same transport boundary:

| Files | Scope |
| --- | --- |
| `flysafe_license_protocol.py`, `flysafe_license_inventory_readonly.py` | Strict `0x11/0x11` inventory codec and a bounded active USB reader. The reader sends only the fixed read request; it is not a passive listener. |
| `flysafe_runtime_state_protocol.py`, `flysafe_runtime_state_listener.py` | Fail-closed `0x03/0x09` and `0x03/0x42` decoders plus a bounded USB-IN-only listener. |
| `rid_working_status_protocol.py`, `rid_working_status_listener.py` | Strict `0x11/0x1C` working-status parser plus a bounded USB-IN-only listener. |
| `rid_rc2_loopback_parser.py` | Offline parser for previously obtained loopback byte streams; it opens no socket and sends no data. |
| `flysafe_rid_product_eligibility_probe.py` | Anonymous public-endpoint checks and privacy-reduced parsing of response-body-only JSON. It has no credential/cookie option and never submits an unlock request. |
| `function_discovery_protocol.py` | Transport-free `0x00/0xB8` request-payload and page codec. Building bytes is not evidence that a target supports the command. |
| `rid_param_protocol.py` | Offline F7/F8 reply parsing, gated F9 write-body encoding and write-ACK parsing, and request-body SIMPLE-keystream transformation; it has no USB transport and performs no write. |
| `aircraft_bulk_capture.py` | USB-IN-only aircraft summary; emits aggregate routing metadata rather than payloads. |
| `rc2_bulk_capture.py` | USB-IN-only RC 2 capture helper. It emits complete frames and payloads to stdout, so its output can contain private telemetry and must never be committed. |
| `usb_duml_command_census.py` | USB-IN-only aggregate command-header census for the fixed aircraft and RC 2 interfaces. |

The five `test_*.py` files cover the protocol, listener-boundary, privacy-reduction, and loopback
parsing code. `function_discovery_protocol.py`, `rid_param_protocol.py`, and the two low-level bulk
capture helpers currently have no dedicated test module in this import.

## Dependencies

- Python 3.10 or newer.
- The host tests and pure codecs use the standard library only.
- USB tools require the PyPI package `libusb1` (import name `usb1`) and host permission to claim
  the indicated DJI vendor interface.
- `flysafe_rid_product_eligibility_probe.py` optionally uses `certifi`; without it, Python's system
  CA store is used.

Install optional runtime dependencies in an external virtual environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install libusb1 certifi
```

The repository ignores local environments; do not commit `.venv`, captures, JSON responses, or
redirected stdout.

## Tests

From this directory:

```sh
python3 -m unittest -v \
  test_flysafe_license_protocol.py \
  test_flysafe_runtime_state_protocol.py \
  test_rid_working_status_protocol.py \
  test_rid_rc2_loopback_parser.py \
  test_flysafe_rid_product_eligibility_probe.py
```

Expected result for this source snapshot: `Ran 68 tests ... OK`.

Before running any USB helper, use `--help` to confirm its fixed route and output behavior. Do not
commit live command output; only privacy-reduced, reviewed summaries belong in the evidence record.
