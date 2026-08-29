# OpenDroneID synthetic wire codec

Independently written Python codec for the standardized Remote ID message set
(ASTM F3411 / ASD-STAN prEN 4709-002). It re-implements the 25-byte message
encodings and the 0xF Message Pack container from the public OpenDroneID Core C
model ([opendroneid-core-c](https://github.com/opendroneid/opendroneid-core-c),
Apache-2.0, Intel) from its published semantics. No DJI software is bundled,
derived from, or redistributed here.

## Status

- `STATIC`: source-only codec for the **separate synthetic laboratory source**
  lane. It encodes/decodes standardized messages with fully synthetic identity
  and coordinates for detector compatibility tests.
- `OBSERVED`: all self-contained tests pass; the encode reference vectors were
  produced by compiling the public Core C library and running its official
  encoders on identical `TEST*` inputs.
- `NOT ADMITTED`: passing these tests does not transmit RF, does not establish a
  macOS/ESP32/nRF transmit adapter, and does not change Mini 5 Pro behavior. The
  real-aircraft Remote ID switch remains a separate, evidence-gated lane.

## Scope

| Function | Coverage |
| --- | --- |
| `encode_basic_id` / `decode_basic_id` | Basic ID (UAS type, ID type, UAS ID) |
| `encode_location` / `decode_location` | Location/Vector (status, speed, lat/lon, altitude, height, accuracies, timestamp) |
| `encode_auth` / `decode_auth` | Authentication (page 0 + page N layouts) |
| `encode_self_id` / `decode_self_id` | Self ID |
| `encode_system` / `decode_system` | System / operator-location (EU category/class) |
| `encode_operator_id` / `decode_operator_id` | Operator ID |
| `encode_pack` / `decode_pack` | Message Pack container (type 0xF, up to 9 messages) |

Field quantisation matches the public reference: lat/lon `x10^7` int32, altitude
`(m+1000)/0.5` uint16, horizontal speed 0.25/0.75 m/s two-scale, vertical speed
`/0.5` int8, direction 0-179 + E/W bit, timestamp tenths since the hour, area
radius `/10` uint8.

## Safety boundary

This module has no RF, no socket, no USB, no DUML, and no aircraft-control path.
Any future source adapter must additionally require: no real identity; controlled
test area and authorization; a bounded lease with manual/timeout stop and
fail-closed lockout; readback from the source; independent receiver confirmation;
no auto-resume; and redacted audit logs. See
[`docs/19_RID_EXPERIMENT_CONTROL_MATRIX.md`](../../docs/19_RID_EXPERIMENT_CONTROL_MATRIX.md)
for the full contract.

## Tests

```sh
cd libraries/opendroneid-synthetic-codec
python3 -m unittest -v test_odid_wire_codec.py
```

Expected result: `Ran 12 tests ... OK`.

## License

Original content here is MIT-licensed like the repository root. The upstream
OpenDroneID Core C library is Apache-2.0 and is referenced only; it is not
vendored, and its `TEST*` reference vectors were regenerated locally for
cross-checking.
