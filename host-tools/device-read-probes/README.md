# Device read probes

This directory contains narrowly scoped USB probes used to read selected RC 2 / Mini 5 Pro state.
They are independently written research tools, not DJI software.

## Boundaries

- Most probes send one of a fixed set of GET/read requests and apply route, command, sequence,
  framing, and checksum checks before interpreting a response.
- `usb_rid_passive_snapshot.py` is input-only and never obtains an output endpoint.
  It accepts the seven-byte minimum RID status prefix and retains extension bytes
  in memory; reports show their length, never their uninterpreted contents.
- No file exposes a generic packet sender, flight command, motor command, firmware write, country
  setter, RID setter, bootloader action, or updater.
- A GET reply is onboard state only. It does not by itself prove over-the-air RID, radio power, or
  regulatory compliance.

`aircraft_readonly_params.py` and `aircraft_readonly_uid_status.py` are transport wrappers around
the matching RC2 probes. `rid_param_protocol.py` is the strict F7/F8 decoder plus the gated F9
write-body/ACK codec shared by the RID-policy, EID, and RID-switch tools; its synthetic tests are
included. The bounded F9 write path itself lives in
[`../rid-switch-tool/rid_switch_control.py`](../rid-switch-tool/rid_switch_control.py) and is not
reachable from any probe in this directory.
The write-body codec rejects anything except a single `00`/`01` byte. Wider
integer/float Boolean read support does not establish a safe write encoding.

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
