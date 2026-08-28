# Device read probes

This directory contains narrowly scoped USB probes used to read selected RC 2 / Mini 5 Pro state.
They are independently written research tools, not DJI software.

## Boundaries

- Most probes send one of a fixed set of GET/read requests and apply route, command, sequence,
  framing, and checksum checks before interpreting a response.
- `usb_rid_passive_snapshot.py` is input-only and never obtains an output endpoint.
- No file exposes a generic packet sender, flight command, motor command, firmware write, country
  setter, RID setter, bootloader action, or updater.
- A GET reply is onboard state only. It does not by itself prove over-the-air RID, radio power, or
  regulatory compliance.

`aircraft_readonly_params.py` and `aircraft_readonly_uid_status.py` are transport wrappers around
the matching RC2 probes. `rid_param_protocol.py` is the original strict F7/F8 decoder shared by the
RID-policy and EID probes; its synthetic tests are included.

## Dependencies and tests

Python 3.10 or later and `libusb1` are required for live USB access:

```sh
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s . -p 'test_*.py'
```

The tests are synthetic and do not access USB hardware. Live probes may need exclusive access to a
USB interface and can conflict with another application that has already claimed it.

The probes load `third-party/duml.py`, copied without modification from
[`deviverr/DJI-RC-Emulator`](https://github.com/deviverr/DJI-RC-Emulator) commit
`93eb7594770dc891c9c8495da1c57274e0d1d26c`. Its complete MIT license and notice are preserved in
`third-party/`.
