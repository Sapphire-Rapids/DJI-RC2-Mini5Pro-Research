# RID switch control (bounded USB DUML)

This directory contains one operator-run USB tool for the single RID candidate
parameter `rid_ctrl_enable_0` (`0x3CBD864F`). It is independently written research
source, not DJI software, and it is **not admitted** as a stable aircraft Remote ID
switch: a write is only attempted after a same-session F7/F8 baseline exists, the
baseline is always restored immediately after the forward write, and no radio state
is measured.

## Why this exists

The Android panel (`apps/rc2-rid-admin`) already gates the same parameter over the
Binder route, but its generic attach routes failed their known-height positive
controls on the live controller (A-023/A-024). This tool reaches the flight
controller through the independent USB DUML path already proven for read-only F7/F8,
and adds the previously refused F9 write only behind positive-control and
baseline/restore gates.

## Commands reachable

- FLYC `0x03/0xF7` parameter metadata by hash
- FLYC `0x03/0xF8` parameter value by hash
- FLYC `0x03/0xF9` parameter write by hash (gated; only `rid_ctrl_enable_0`)

The tool has no generic payload, route, command, or parameter interface. It never
starts motors and measures no RF.

## Usage

```sh
# Probe only: positive control, then report the RID parameter baseline (no write)
python3 rid_switch_control.py --transport rc2 --wire-mode simple

# A-B-A: write OFF, read back, restore the captured baseline, read back again
python3 rid_switch_control.py --transport aircraft --target off --wire-mode simple

# Modern aircraft routing (0x82 -> 0x92), read-only probe
python3 rid_switch_control.py --transport aircraft --route modern --wire-mode simple
```

Dependencies: Python 3.10+ and `libusb1` (`pip install -r ../device-read-probes/requirements.txt`).

## Gate order

1. Positive control `g_config.flying_limit.max_height` (`0x0371238A`) must round-trip
   F7/F8 on the chosen route. A failed positive control aborts before any RID request.
2. `rid_ctrl_enable_0` F7 metadata must match the fixed name, and F8 must return a
   strict Boolean baseline.
3. Only then may a single F9 write be sent; the F9 request and its acknowledgement use
   the same SIMPLE-keystream protection as reads.
4. Forward value is read back, then the baseline is written back and read back again.

A route that does not pass the positive control is reported as `route_not_verified`,
and the RID parameter is never touched.

## Tests

Offline tests load the module with a fake `usb1` and verify the value-width helper and
the fail-closed dispatch gate without opening a device:

```sh
python3 -m unittest -v test_rid_switch_control.py
```

The protocol-layer F9 codec and write-ack tests live in
`../device-read-probes/test_rid_param_protocol.py`.

## Status

`STATIC` (offline source and synthetic tests) / `NOT ADMITTED` (no live write is
claimed). A green F8 readback only records an onboard parameter value; it does not
prove Remote ID RF behaviour. Do not run the write path until the operator confirms
the physical route, motor-off state, and the external receiver for a motor-on A-B-A
check is ready.
