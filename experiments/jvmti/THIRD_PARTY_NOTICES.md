# Third-party notices

## AOSP Android 11 `jvmti.h`

The following unmodified third-party file is vendored so every experiment uses the Android 11
JVMTI ABI instead of a host JDK's potentially newer layout:

```text
jvmti_attach_canary/app/src/main/cpp/third_party/aosp_android_11_jvmti/jvmti.h
```

Provenance:

- AOSP repository: `platform/art`
- tag: `android-platform-11.0.0_r40`
- peeled tag commit recorded by the original audit: `4e6cbddac8c7a49209b6a9381b62c8c60a73307b`
- upstream path: `openjdkjvmti/include/jvmti.h`
- upstream source: <https://android.googlesource.com/platform/art/+/refs/tags/android-platform-11.0.0_r40/openjdkjvmti/include/jvmti.h>
- local and upstream SHA-256: `229d8607d191a3d7815a887ca32d79da11ffa85b4cb16a43b6a01dbb0929d08d`

The header's original Oracle copyright and license block is preserved. It is licensed under the
GNU General Public License, version 2 only, with Oracle's Classpath Exception. It is **not** covered
by this repository's MIT license.

The adjacent vendored files preserve the corresponding upstream terms:

- `LICENSE`: full GPLv2 text and Classpath Exception from AOSP Android 11 `platform/libcore`;
- `NOTICE`: AOSP ART `openjdkjvmti/NOTICE` describing the same license boundary;
- `README.md`: exact provenance note.

Official sources:

- <https://android.googlesource.com/platform/libcore/+/refs/tags/android-platform-11.0.0_r40/LICENSE>
- <https://android.googlesource.com/platform/art/+/refs/tags/android-platform-11.0.0_r40/openjdkjvmti/NOTICE>

All other source in this directory is independently written unless a file states otherwise.
