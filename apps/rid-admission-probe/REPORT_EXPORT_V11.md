# v0.11 SD report export — historical

Superseded by [v0.12 report/sample export](REPORT_EXPORT_V12.md). The v0.11 artifact and audit
profile below remain unchanged; they do not certify the additional v0.12 sample sink.

The user requested that the probe save its report on RC 2 removable SD so the host can read it
through MTP. This is a narrow output exception to the historical v0.10 file-write ban. Device
inspection remains read-only; no aircraft command, ADB start, agent attach or network upload is added.

## Behavior

- Package `com.finduas.ridobserver`, version `0.11.0-report-export`, code `11`; same signer as v0.10.
- One user-triggered inspection; both `COMPLETE` and `INCOMPLETE` terminal results automatically
  export. Inspection and export verdicts remain separate.
- Select exactly one mounted, removable, non-primary, non-emulated volume. Its actual MediaStore
  volume must be present in `getExternalVolumeNames`; Android 10's UUID mapping must match that set.
  Missing/ambiguous storage never falls back to primary/internal storage.
- Insert a new `text/plain` Downloads row under `Download/FindUAS/Probe/`, initially pending.
  Its name is `FindUAS_Probe_v011_<completed-time>_<run-id>_<attempt-id>.txt`; IDs are generated
  internally. Each attempt has a fresh suffix, including retries after failed cleanup.
- Write and close the complete UTF-8 report, at most 256 KiB, then require exactly one row to be
  published. A failed attempt may delete only its newly inserted owned URI; cleanup failure is
  reported. No existing report is overwritten, queried for replacement, or deleted.
- Keep the app open until the save result. **重新保存报告到 SD 卡（不重新检查）** retries only a
  failed export of the same retained terminal snapshot. Rotation/resume cannot schedule another
  export. Process death can lose an unfinished in-memory report or leave a pending row.

The content preserves `finduas-rid-probe/v0.10-schema-1` and `machine_section_end=true`, adds
`app_version=0.11.0-report-export`, and ends with `report_file_end=true`. It contains private local
diagnostic metadata. Do not commit, publish or upload the full report.

## Host receipt

The UI's saved state means local MediaStore publication only. It does not prove MTP visibility.
The host must freshly enumerate the final file name, check the size, read the full file and verify
the schema/version/completion marker. Ignore temporary pending names and truncated outputs. Keep
raw MTP output and report bodies in the local excluded research area.

## Audit boundary

Only the exact private `ProbeReportStore` Android backend may call the reviewed MediaStore write
APIs. Other app classes retain their write/network/process/attach prohibitions. The auditor pins
the reviewed report source and full report-family DEX in addition to the application-owned external
invoke set. It preserves the old inspection-completion CFG proof and tests adversarial mutations.
The historical v0.10 identity and audit remain available via `--profile v10`; they do not certify v0.11.

The main UI renders one atomic inspection/export snapshot. Refresh scheduling uses the busy state
that was actually displayed, so a worker finishing immediately after rendering still gets a final
screen refresh. Export failures cannot turn an incomplete inspection into `COMPLETE`.

## Platform references

- [StorageVolume mapping](https://developer.android.com/reference/android/os/storage/StorageVolume#getMediaStoreVolumeName())
- [MediaStore Downloads](https://developer.android.com/reference/android/provider/MediaStore.Downloads)
- [App-owned shared-storage permission rules](https://developer.android.com/training/data-storage/shared/media)
- [Pending MediaStore rows](https://developer.android.com/reference/android/provider/MediaStore.MediaColumns#IS_PENDING)
- [Android 11 MTP storage observation](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-11.0.0_r1/media/java/android/mtp/MtpStorageManager.java)

Artifact verification and device-use results are recorded separately in the repository evidence and
artifact registers; passing source tests alone is not a device export or host-readback observation.

## Reviewed artifact checkpoint — 2026-08-30

A-038: `2,601,935` bytes, SHA-256 `aaa6f8bf22002c907d8de89fff58c04755bbfdd08feed4ec0f8771d6eb8044aa`. 69 JVM tests and 8 auditor tests passed; lint reported no issues; 30/30 v11 mutations were rejected. Two clean builds were byte-identical to the reviewed APK. The signature verified with v2, zip alignment passed, and the signer matches preserved v0.10.

The report store source (`80bec1fca211e41d86097630cae954104b617af76fbcd21106a5030f00e9265d`) and its six-class DEX family (`96fa9e54a92e65ac31d3c8f26646c049ae08ec524a3680b9384f2bfddbe6b258`) were manually reviewed. The full app-owned external-invoke multiset is 2627 calls / `4cc4ecb553f9c45689c29f09f8e6292e4dbceb92b438af82085b173e6f8c0f5c`; the 266 additions were reviewed and the original ART/framework-read surface retained.

C-234 records staging/full readback as `Download/FindUAS_A038_V011.apk`. C-235 records the subsequent
private v0.11 report confirming installation, execution and report receipt: it was `INCOMPLETE` with
`art.state=ELF_BUILD_ID_FAILED` because the old reader accepted ELF64 only while the probe ran as
32-bit. C-237 records the later v0.12 `COMPLETE` result after ELF32 support was added. See the
[RC 2 live runtime record](../../docs/23_RC2_LIVE_RUNTIME.md). No full report or raw MTP log is
published here.
