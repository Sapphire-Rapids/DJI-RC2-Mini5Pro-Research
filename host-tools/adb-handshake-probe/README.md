# RC 2 ADB handshake probe

Status: **OBSERVED host-side probe**. On RC 2 firmware `07.00.0100`, the host sent `CNXN` over
the descriptor-discovered ADB bulk interface and received no ADB packet before the 15-second read
timeout. The probe did not reach `AUTH`, open a shell, or change the controller.

The program is a narrow reproduction of the first-packet profile in
[`Dr-Muh/dji-adb`](https://github.com/Dr-Muh/dji-adb):

- discover the ADB interface and endpoints from USB descriptors;
- send one `CNXN` packet;
- if and only if the device returns `AUTH TOKEN`, send the existing host ADB public key directly
  as `AUTH RSAPUBLICKEY`;
- stop after `CNXN`/authentication and never send `OPEN`.

It does not generate, delete, or replace an ADB key. Stop the normal ADB server before the probe so
that it does not own the same USB interface.

## Run

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
adb kill-server
.venv/bin/python rc2_adb_handshake_probe.py --label one-shot --wait-seconds 20
```

Unit tests do not touch USB:

```sh
.venv/bin/python -m unittest -v test_handshake_probe.py
```

The complete redacted result and the exact-v07 daemon explanation are maintained in
[`docs/08_ANDROID_ADB.md`](../../docs/08_ANDROID_ADB.md). `UPSTREAM_STATIC_AUDIT.md` records the
pinned upstream behavior and why the original interactive client was not used for the live trace.
No device serial, bus/address tuple, public-key fingerprint, or raw private capture is published.
