# AGENTS.md

This file applies to `apps/rc2-flysafe-agent-staging-payload/`.

This source-only project packages the adjacent independently written AArch64 ART TI query agent as
an uncompressed, page-aligned APK entry. It has no application component, permission, network path
or setter. AGP emits one synthetic `R` class DEX even though `android:hasCode="false"`; do not call
the final APK DEX-free. It exists only to preserve the completed temporary PackageInstaller
staging-directory experiment.

Never commit the generated APK, native library, signing material, Gradle output or local SDK paths.
Never commit or add a type-6 setter until a genuine existing-ID baseline, exact restore and external
RF closure have been observed. A successful agent callback is inventory transport evidence only.

The emulator staging path was labelled `apk_tmp_file`, and DJI Fly was denied directory search
before the agent loaded. The session was abandoned and the directory disappeared. Do not repeat or
propose this same route on RC 2 without new policy evidence. Do not commit the payload as an
installed package. Do not unlock the bootloader or modify boot, vendor_boot, vbmeta, TEE, QFPROM or
eFuse.
