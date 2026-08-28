# Android 11 JVMTI header provenance

`jvmti.h` is the unmodified AOSP Android 11 header from:

- repository: `platform/art`
- tag: `android-platform-11.0.0_r40`
- peeled tag commit: `4e6cbddac8c7a49209b6a9381b62c8c60a73307b`
- path: `openjdkjvmti/include/jvmti.h`
- source: <https://android.googlesource.com/platform/art/+/refs/tags/android-platform-11.0.0_r40/openjdkjvmti/include/jvmti.h>

The upstream header carries the GPLv2 Classpath Exception notice in the file itself. It is vendored
so the Android NDK build does not accidentally use a host JDK's newer JVMTI layout. `LICENSE`
contains the complete GPLv2 text and Classpath Exception from the matching Android 11 AOSP
`platform/libcore` tag; `NOTICE` is the matching ART `openjdkjvmti/NOTICE`. This header is not MIT
licensed.
