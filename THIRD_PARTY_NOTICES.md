# Third-party notices

The repository-root [MIT license](LICENSE) covers the independently written material unless a
file or directory carries a different notice. The following third-party source is included without
relicensing it under the repository MIT license.

## DJI-RC-Emulator DUML helper

`host-tools/device-read-probes/third-party/duml.py` and
`experiments/device-write/third-party/duml.py` are byte-identical copies from
[`deviverr/DJI-RC-Emulator`](https://github.com/deviverr/DJI-RC-Emulator) commit
`93eb7594770dc891c9c8495da1c57274e0d1d26c`.

The upstream MIT license and copyright notice are preserved beside each copy as
`LICENSE.DJI-RC-Emulator` and `NOTICE.md`.

## AOSP Android 11 JVMTI header

The JVMTI experiments include the Android 11 `jvmti.h` from AOSP `platform/art`, tag
`android-platform-11.0.0_r40`. It retains its original GPLv2 + Classpath Exception header and the
matching `LICENSE` and `NOTICE` files. See
[`experiments/jvmti/THIRD_PARTY_NOTICES.md`](experiments/jvmti/THIRD_PARTY_NOTICES.md) for the exact
location, identity and use boundary.

## Referenced but not vendored

Some tools are documented as external dependencies, including `o-gs/dji-firmware-tools`, Ghidra,
Android/Gradle build tools, and Python packages. Their source and licenses are not copied or
relicensed here. DJI firmware, applications, shared libraries and decompiled vendor source are also
not distributed by this repository.
