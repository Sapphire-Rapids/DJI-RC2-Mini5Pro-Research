# v0.12 live ARM32 checks and fixed SD sample export

Status: **OBSERVED**. A-039 was installed and run on RC 2; its `COMPLETE` report was received
through MTP, followed by all four requested Fly sample files with validated sizes and hashes
(C-236–C-238). The current runtime record is [RC 2 live runtime](../../docs/23_RC2_LIVE_RUNTIME.md).
These observations supersede v0.11's pending status and ELF32 parsing failure; historical
[v0.11](REPORT_EXPORT_V11.md) and [v0.10](INDEPENDENT_AUDIT_V10.md) audits remain unchanged.

## Artifact and compatibility

| Item | Reviewed result |
| --- | --- |
| Package | `com.finduas.ridobserver` |
| Version / code | `0.12.0-live32-samples` / `12` |
| Artifact | A-039, `2,651,903` bytes |
| SHA-256 | `46eb6ef19971256a02514fc51a94b21522c488d82294c8853a7beb52fbab3ce4` |
| Android | Minimum API 29; observed on Android 11/API 30; compile/target SDK 35 |
| Validation | 94 JVM tests; 8 auditor tests; 37/37 rejected mutations; lint: no issues |
| Final artifact | Source/all app DEX reviewed; zero permissions; no packaged native library; v2 signature and zipalign verified |
| Reproduction | Two clean builds byte-identical to the reviewed APK |
| Staging | `Download/FindUAS_A039_V012.apk`, fresh listing and full readback matched |

The GNU build-id reader now handles ELF32 and ELF64 header/program-table layouts. The earlier
v0.11 reader failed on the observed 32-bit probe process; v0.12 completed the same self-process ART
identity inspection. Fixed reference ranges remain conditional on the exact whole-file/build-id
match; ARM32 does not reuse an unrelated ARM64 range profile.

Component inventory includes disabled components and reads application/component enabled-setting
overrides. Two additional fixed property reads report `ro.boot.mp_state` and `ro.boot.dbg_cnt`.
The probe still performs no agent attach, native load, class enumeration, process execution,
DJI protocol application transaction, DUML send or network connection.

## Two separate output stores

The user authorized reports and fixed installed-software samples. Both stores require exactly one
mounted, removable, non-primary, non-emulated volume with a valid MediaStore Downloads volume name.
API 30 uses the volume's MediaStore name; API 29 matches its UUID against available external names.
Missing or ambiguous SD storage fails without falling back to primary/internal storage.

| Output | Owner | Fixed directory / new name |
| --- | --- | --- |
| UTF-8 report | `ProbeReportStore` and its private Android backend | `Download/FindUAS/Probe/FindUAS_Probe_v012_<completed-time>_<run-id>_<attempt-id>.txt` |
| Sample ZIP | `InstalledFlySampleExporter` and its private Android backend | `Download/FindUAS/Samples/FindUAS_Fly1194_<attempt-id>.zip` |

Each store inserts a new pending Downloads row, writes and closes its stream, then publishes that
row. A failed attempt can remove only its own newly created URI; cleanup failure is reported.
Neither store replaces or deletes earlier outputs, accepts user-selected paths/URIs, requests broad
storage permissions or uploads data. Installed package/library inputs are never modified.

## Report operation

**执行只读能力检查** runs the retained inspection. Both terminal `COMPLETE` and `INCOMPLETE`
snapshots automatically save one report, limited to 256 KiB of UTF-8. Export success never changes
the inspection verdict. **重新保存报告到 SD 卡（不重新检查）** retries a failed export from the
same retained snapshot under a fresh attempt name, without rerunning the inspection.

The report retains `finduas-rid-probe/v0.10-schema-1` and `machine_section_end=true`, identifies
`app_version=0.12.0-live32-samples`, and ends with `report_file_end=true`. Rotation/resume does not
duplicate a worker/export. Keep the app open until its result; process death can lose unfinished
in-memory work or leave a pending row.

## Fixed sample operation

**导出 DJI Fly 1.19.4 分析样本到 SD 卡** is a separate explicit action. It requires PackageManager
to report exactly `dji.go.v5`, version `1.19.4`, code `3113157`, and reads only its source APK and
three fixed basenames under its reported native-library directory:

| ZIP entry | Requirement |
| --- | --- |
| `DJI_FLY.apk` | Required |
| `libsdk_jni.so` | Required |
| `libsdk_key_value.so` | Optional; absence is recorded |
| `libsdk_base.so` | Optional; absence is recorded |
| `manifest.json` | Generated package/version, copied sizes/SHA-256, missing optional entries and total bytes |

The exporter streams with a 64 KiB buffer, limits each input to 1 GiB and aggregate inputs to
2 GiB, compares file size/mtime around copying, and rechecks package identity and both source paths.
Changes abort the export. It does not collect app data, credentials, licenses, arbitrary ZIP entries
or other packages. The manifest contains no source paths. All four requested inputs were present
and validated in the C-238 receipt.

Copying runs in a retained background session with byte progress; other probe/export/navigation
actions are disabled while busy. Failures display the fixed entry name when known and cleanup
status; success lists missing optional libraries if any. Keep the app open until completion.

## Host receipt and current follow-up

Publication is not host delivery. For each new output, freshly enumerate its final MTP name and
size, read the complete file, and validate report markers or ZIP manifest/entry hashes and sizes.
Keep report bodies, sample ZIPs, extracted vendor files and transport logs in excluded private
storage. No vendor binary or full live report is distributed with this source tree.

C-237 closes the earlier v0.12 `COMPLETE` report and C-238 closes sample receipt. The operator has
since confirmed that Developer Assistant can be opened; its new post-installation probe report
is still pending. The next action is to reopen the already installed probe and tap
**执行只读能力检查**, then retrieve that new report. The older disabled-component observation must
not be silently relabeled as a new measurement.

## Audit continuity

C-236 covers manual review of the changed source, final app DEX, both restricted writer families
and external calls, followed by completion-CFG and mutation checks. Current source hashes are:

- `ProbeReportStore.kt`: `11fa59c20d9e8b1f4df4d0985880cf7f8729af529b78c84cad0b34eb17888a4d`.
- `InstalledFlySampleExporter.kt`: `c9bda403ac697255eca7df02f38202c1a4a9c778e6f91235fa7db52ced243f90`.

The v12 external-invoke multiset is 3067 calls /
`0e6b11a5891d2d7ac0cb84153f1c4e21ed277a24c2f1a6280418235ec421820e`.
The auditor separately pins the complete report/sample DEX families; it does not generally allow
file-output APIs. Mutations cover wrong package/version/source paths, ZIP entry names, output
directories and unreviewed writers as well as the preserved ART/completion proof.

`audit_artifact.py` defaults to `--profile v12`, checking current source and final DEX.
`--profile v10` and `--profile v11` check their respective historical artifacts without claiming
that current source built them; their 21/30 mutation histories remain separate from v12's 37.
Use `build_and_audit.sh` and `reproducibility_check.sh` for new builds rather than resealing
fingerprints from an unreviewed or incremental APK.
