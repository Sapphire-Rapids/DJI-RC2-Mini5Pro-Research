# Historical device-write experiments

These two small programs preserve the exact bounded country/area round-trip experiments used on
the laboratory Mini 5 Pro / RC 2 pair. They are not a generic control interface.

## Status and observed history

- `OBSERVED`: the aircraft FC-area path completed `CN -> US -> CN` with readback after each step.
- `OBSERVED`: the Sky country path completed `CN -> US -> CN` with readback.
- `OBSERVED`: the Ground country attempt did not receive a matching setter acknowledgement and its
  readback remained `CN`; it did not establish a successful Ground transition.
- These state loops did not measure RID, channel, regulatory mode, signal power, or EIRP.

Changing country/area state can change radio-region or regulatory policy and can briefly disrupt a
link. These programs are operator-only laboratory records. They do not start motors, fly an
aircraft, schedule themselves, or provide automatic aircraft control. The one-shot country script
is checked in with its historical authorization marked consumed, so it refuses another run unless
source is deliberately reviewed and changed by an operator.

## Dependencies

Python 3.10 or later and `libusb1` are required:

```sh
python3 -m pip install -r requirements.txt
```

The two scripts load `third-party/duml.py`, copied without modification from
[`deviverr/DJI-RC-Emulator`](https://github.com/deviverr/DJI-RC-Emulator) commit
`93eb7594770dc891c9c8495da1c57274e0d1d26c`. Its MIT license and notice are preserved in
`third-party/`.

There are no device-independent unit tests in this directory. Import/compile validation does not
claim that a currently attached device matches the recorded routes or baseline.
