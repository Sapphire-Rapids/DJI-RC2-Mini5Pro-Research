# RID switch control and by-index probe (bounded USB DUML)

This directory contains two operator-run USB tools for the RID candidate parameters.
They are independently written research source, not DJI software, and neither is
**admitted** as a stable aircraft Remote ID switch: a write is only attempted after a
same-session baseline exists, the baseline is always restored immediately, and no
radio state is measured.

## Why this exists

The Android panel (`apps/rc2-rid-admin`) gates the same parameters over the Binder
route, but its generic attach routes failed their known-height positive controls on
the live controller (A-023/A-024). These tools reach the flight controller through the
independent USB DUML path already proven for read-only parameter access.

Two parameter families are covered:

- **by-hash** FLYC `0x03/0xF7` (metadata), `0x03/0xF8` (read), `0x03/0xF9` (write) —
  used by `rid_switch_control.py` for `rid_ctrl_enable_0` (`0x3CBD864F`).
- **by-index** FLYC `0x03/0xE0` (table), `0x03/0xE1` (get_info), `0x03/0xE2` (read),
  `0x03/0xE3` (write) — used by `rid_param_index_readonly.py` for the wa150 table's
  `EU_CE_enable_c0_rid` (index 1306) and neighbours, recovered from the public
  `lmdegreeds/djiparam` parameter table.

## Commands reachable

- `rid_switch_control.py`: F7/F8/F9 by hash, gated; only `rid_ctrl_enable_0`.
- `rid_param_index_readonly.py`: E0/E1/E2 by index, read-only; the E3 write encoder is
  present only in the offline codec and is not reachable from the probe.

Neither tool has a generic payload, route, command, or parameter interface. Neither
starts motors nor measures RF.

## Usage

```sh
# by-hash: probe only, then report the rid_ctrl_enable_0 baseline (no write)
python3 rid_switch_control.py --transport rc2 --wire-mode simple

# by-hash: A-B-A write OFF, read back, restore baseline, read back again
python3 rid_switch_control.py --transport aircraft --target off --wire-mode simple

# by-index: read the wa150 RID parameter names and values (read-only)
python3 rid_param_index_readonly.py --transport aircraft
```

Dependencies: Python 3.10+ and `libusb1`
(`pip install -r ../device-read-probes/requirements.txt`).

## Gate order (by-hash write)

1. Positive control `g_config.flying_limit.max_height` (`0x0371238A`) must round-trip
   F7/F8 on the chosen route. A failed positive control aborts before any RID request.
2. `rid_ctrl_enable_0` F7 metadata must match the fixed name, and F8 must return a
   strict Boolean baseline.
3. Only then may a single F9 write be sent; the F9 request and its acknowledgement use
   the same SIMPLE-keystream protection as reads.
4. Forward value is read back, then the baseline is written back and read back again.

The by-index probe never writes. It verifies the table identity through `0xE0`, then
re-checks each candidate's on-board name through `0xE1` before interpreting `0xE2`.

## Tests

```sh
python3 -m unittest -v test_rid_switch_control.py test_rid_param_index_readonly.py
```

Offline tests load the modules with a fake `usb1` and verify the value-width helpers,
the fixed candidate list, and the fail-closed dispatch gates without opening a device.
The by-hash F9 codec tests live in `../device-read-probes/test_rid_param_protocol.py`,
and the by-index codec tests in
`../../libraries/protocol-probes/test_rid_param_index_protocol.py`.

## Status

`STATIC` (offline source and synthetic tests) / `NOT ADMITTED` (no live write is
claimed). A green readback only records an onboard parameter value; it does not prove
Remote ID RF behaviour. Do not run a write path until the operator confirms the
physical route, motor-off state, and the external receiver for a motor-on A-B-A check
is ready.
