# RID switch control and by-index probe (bounded USB DUML)

This directory contains fixed USB tools for historical RID candidate parameters.
They are independently written research source, not DJI software, and neither is
**admitted** as a stable aircraft Remote ID switch. Offline repair and passing tests
do not reopen a closed device route. In particular, `rid_ctrl_enable_0` and
`EU_CE_enable_c0_rid_0` / `EU_CE_enable_c0_rid` remain `NOT ADMITTED` for the recorded
Mini 5 Pro `01.00.0600` state. Do not repeat their closed routes merely because these
source defects have been repaired; consult the current evidence and handoff first.

A write path requires a same-session baseline, attempts one immediate restore after
any possible forward write, and checks the final value even if a restore ACK is lost.
This is bounded best-effort recovery: disconnection, process termination, power loss,
or a failed final read can leave restoration unverified. No radio state is measured.

## Why this exists

The Android panel (`apps/rc2-rid-admin`) gates the same parameters over the Binder
route, but its generic attach routes failed their known-height positive controls on
the live controller (A-023/A-024). These tools reach the flight controller through the
independent USB DUML path already proven for read-only parameter access.

Two parameter families are covered:

- **by-hash** FLYC `0x03/0xF7` (metadata), `0x03/0xF8` (read), `0x03/0xF9` (write) —
  used by `rid_switch_control.py` for `rid_ctrl_enable_0` (`0x3CBD864F`) and by
  `rid_eu_by_hash_switch_control.py` for `EU_CE_enable_c0_rid_0` (`0xF80992FE`).
- **by-index** FLYC `0x03/0xE0` (table), `0x03/0xE1` (get_info), `0x03/0xE2` (read),
  `0x03/0xE3` (write) — used by `rid_param_index_readonly.py` and
  `rid_index_switch_control.py` for the wa150 table's `EU_CE_enable_c0_rid`
  (index 1306) and neighbours, recovered from the public `lmdegreeds/djiparam`
  parameter table.

The parameter-name hash that links the two families is implemented in
[`../../libraries/protocol-probes/dji_flyc_parameter_hash.py`](../../libraries/protocol-probes/dji_flyc_parameter_hash.py).
`EU_CE_enable_c0_rid` (by index) and `EU_CE_enable_c0_rid_0` (`0xF80992FE`, by hash)
name the same wa150 row, and both tools can read-only report that bridge.

## Commands reachable

- `rid_switch_control.py`: F7/F8/F9 by hash, gated; only `rid_ctrl_enable_0`.
- `rid_eu_by_hash_switch_control.py`: F7/F8/F9 by hash, gated; only
  `EU_CE_enable_c0_rid_0`. It keeps the same positive control and the same
  A-B-A/restore/fail-closed safety mode, and adds an optional `--rid-ctrl-bridge`
  read-only probe of `rid_ctrl_enable_0` in the same session.
- `rid_param_index_readonly.py`: E0/E1/E2 by index, read-only; the E3 write encoder is
  present only in the offline codec and is not reachable from the probe.
- `rid_index_switch_control.py`: E0/E1/E2/E3 by index, gated; only
  `EU_CE_enable_c0_rid`. It verifies the table CRC/count and on-board name in the same
  session before one forward `0xE3` write, then immediately restores the captured
  baseline.

Neither tool has a generic payload, route, command, or parameter interface. Neither
starts motors nor measures RF.

## Read-only baseline batch

The historical wrapper sequences two write-free probes:

```sh
# Two separate USB connections in one batch (no --target is ever passed)
./readonly_baseline_session.sh aircraft legacy
```

Each completed invocation emits a JSON report, including a read-only result or an
operational failure. The batch stops at the first failure and may therefore create
only the first report. Each Python process opens and closes its own USB connection;
the batch does not establish a shared connection or same-session baseline across
the two reports. The default output is the repository's ignored
`private/readonly_baseline_<timestamp>/` directory; `READONLY_BASELINE_OUT_DIR` may
select another private local directory. It never reaches a write or restore path.
These are historical interfaces, not instructions to repeat the current closed
routes. Review reports for unexpected identifiers before sharing them.

## Usage

```sh

# by-hash: probe only, then report the rid_ctrl_enable_0 baseline (no write)
python3 rid_switch_control.py --transport rc2 --wire-mode simple

# by-hash: also map the by-index wa150 row EU_CE_enable_c0_rid -> _0 hash (read-only)
python3 rid_switch_control.py --transport aircraft --index-bridge --wire-mode simple

# by-hash: A-B-A write OFF, read back, restore baseline, read back again
python3 rid_switch_control.py --transport aircraft --target off --wire-mode simple

# by-hash EU C0: probe the EU_CE_enable_c0_rid_0 baseline only (no write)
python3 rid_eu_by_hash_switch_control.py --transport aircraft --wire-mode simple

# by-hash EU C0: also probe rid_ctrl_enable_0 in the same session (read-only)
python3 rid_eu_by_hash_switch_control.py --transport aircraft --rid-ctrl-bridge --wire-mode simple

# by-hash EU C0: A-B-A write OFF, read back, restore baseline, read back again
python3 rid_eu_by_hash_switch_control.py --transport aircraft --target off --wire-mode simple

# by-index: read the wa150 RID parameter names and values (read-only)
python3 rid_param_index_readonly.py --transport aircraft

# by-index: probe EU_CE_enable_c0_rid only, then report the baseline (no write)
python3 rid_index_switch_control.py --transport aircraft

# by-index: also map the same row to its _0 by-hash name (read-only F7/F8)
python3 rid_index_switch_control.py --transport aircraft --hash-bridge

# by-index: A-B-A write OFF, read back, restore baseline, read back again
python3 rid_index_switch_control.py --transport aircraft --target off
```

Dependencies: Python 3.10+ and `libusb1`
(`pip install -r ../device-read-probes/requirements.txt`).

## Gate order (by-hash write)

1. Positive control `g_config.flying_limit.max_height_0` (`0x0371238A`) must round-trip
   F7/F8 on the chosen route. A failed positive control aborts before any RID request.
2. `rid_ctrl_enable_0` F7 metadata must match the fixed name, and F8 must return a
   strict Boolean baseline. Writes are restricted to a one-byte integer/Boolean
   type with raw value `00` or `01`; wider integer and floating-point values remain
   read-only. Canonical metadata bounds must permit both 0 and 1 within that type's
   domain; zero-range or malformed bounds stop before any forward or restore write.
3. Only then may a single F9 write be sent; the F9 request and its acknowledgement use
   the same SIMPLE-keystream protection as reads.
4. Forward value is read back, then the exact captured baseline bytes are written
   back and read back again. A forward ACK failure or interruption also enters the
   restore attempt. A failed restore ACK does not skip the final readback.

The by-index probe never writes. Both by-index tools compare the `0xE0` CRC/count
with the pinned table before any `0xE1`/`0xE2` request, and validate frame CRCs,
response type, reverse route, sequence and command before parsing. A table mismatch
stops the operation. The switch also requires a one-byte Boolean baseline.
Its metadata range must permit both Boolean states before a requested write or
no-op can be admitted. Read-only reports may still show a zero-range flag.

An explicitly requested bridge is required to complete successfully. Bridge failure
retains any successful baseline reads, reports `partial_bridge_unverified`, exits
nonzero and sends no write. The by-index tool also rejects disagreement between its
baseline and the same parameter's by-hash value. Unrequested bridges add no gate.

The EU C0 by-hash switch tool uses the same gate order as `rid_switch_control.py`,
applied to `EU_CE_enable_c0_rid_0` (`0xF80992FE`). The by-index switch tool uses the
same gate order as the by-hash tool, applied to
`EU_CE_enable_c0_rid` (index 1306): verify the wa150 table CRC/count through `0xE0`,
verify the on-board name and width through `0xE1`, read a strict baseline through
`0xE2`, then one forward `0xE3` write, a `0xE2` readback, and an immediate restore with
a final readback. `EU_CE_enable_c0_rid` is an EU C0 policy candidate from the public
wa150 table, not a global RID master switch.

## Tests

```sh
python3 -m unittest -v test_rid_switch_control.py test_rid_eu_by_hash_switch_control.py test_rid_index_switch_control.py test_rid_param_index_readonly.py
python3 -m unittest -v test_switch_session_failures.py
```

Offline tests load the modules with a fake `usb1` and verify the value-width helpers,
the fixed single-parameter target and table identity, the fixed candidate list, and the
fail-closed dispatch gates without opening a device. In-memory USB sessions exercise
the actual CLI and packet paths for read-only output, positive-control failure,
table mismatch, damaged replies, lost ACKs, interruption, exact restoration and
unverified restoration. Tests also cover zero-range and malformed metadata, the
live 1558 count against the pinned 1557 table, and requested bridge failure or value
disagreement before writes. The fixed hash bridge permits F7/F8 only for its pinned
hash; it does not add an F9 route.

Reports distinguish `route_target` from `requested_target`. Operational failure and
unverified transition/restore exit nonzero; successful read-only/no-op paths emit
JSON and exit zero. `A_B_A_complete` describes exact onboard byte readbacks only,
including a separately recorded missing ACK when a later read confirms the state.
The EU C0 by-hash codec is mirrored in the Android panel at
`apps/rc2-rid-admin/.../RidEuC0Parameter.java` with its own name/hash identity test.
The by-hash F9 codec tests live in `../device-read-probes/test_rid_param_protocol.py`,
and the by-index codec tests in
`../../libraries/protocol-probes/test_rid_param_index_protocol.py`.

## Status

`STATIC` (offline source and synthetic tests) / `NOT ADMITTED` (no live write is
claimed). A green readback only records an onboard parameter value; it does not prove
Remote ID RF behaviour. Do not run a write path until the operator confirms the
physical route, motor-off state, and the external receiver for a motor-on A-B-A check
is ready.

## Offline RID cloud-policy audit

`rid_cloud_policy_audit.py` reads a private JSON input and prints only sanitized selection or
possible-candidate statistics. It reproduces the exact1.19.4 first-row, product-block, DEFAULT,
empty-string and per-subscription distinct rules in C-286/C-287. An input `area` selects exact-area
mode; omitting it uses candidate comparison without assuming actual area. `A054_LIMITS` matches
the native probe's bounded UTF8 subset. Inputs include a decoded shared cache object with
`receiver_type`, `receiver_index` and `data`; payload strings, areas and hashes are never output.

```sh
python3 rid_cloud_policy_audit.py /path/to/private-input.json
python3 -m unittest test_rid_cloud_policy_audit
```

This tool has no device transport or write operation. Matching a candidate and receiver does not
identify the shared cache's writer. See [the runtime record](../../docs/23_RC2_LIVE_RUNTIME.md).

## Offline policy structure inspection

`rid_cloud_payload_structure.py PRIVATE_CAPTURE --output PRIVATE_ANALYSIS` consumes the two
captured hex strings (`matched_hex`, `default_hex`) and presence/count metadata. It validates
hex, checks bounded JSON/protobuf-wire/ASN.1-TLV/gzip/zlib syntax and compares byte ranges and
structural fields. Output omits opaque string/byte values; Boolean names remain candidates until
connected to the receiver's implementation. It has no device or network operations. Tests use
synthetic input only; actual A057 bytes are pending (C-293--C-295).
