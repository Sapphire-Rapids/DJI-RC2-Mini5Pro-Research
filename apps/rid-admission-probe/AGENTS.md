# Handoff rules for `rid-admission-probe`

- Package only `app/src/safe`; the withdrawn socket-era `app/src/main` implementation is excluded
  from this public repository and must never be reintroduced.
- Generated APKs and historical sealed binaries are intentionally not committed. Changes to shipped
  code need a new version/code/name/hash and a new static review.
- This probe requests no permission and packages no service, receiver, provider, or native library.
- Never add a localhost or network socket, DUML encoder/sender, DJI Binder application transaction,
  agent attach/load, root/process execution, another-process `/proc` path, or target file write.
  The user authorized the two fixed v0.12 report/sample exports below. They do not change the
  device-control or target-code boundary; installed package/library inputs remain read-only.
- The v0.10 ART section may read only `/proc/self/maps` and the exact mapped non-symlink regular
  `libart.so` file. It must retain strict page-aligned/overflow/coverage parsing, non-zero maps and
  fstat devices, positive start addresses, unsigned device/inode tokens, `lstat` + `O_NOFOLLOW`,
  nanosecond metadata, and two exactly equal normalized maps snapshots. Do not weaken
  whole-file/build-id/named-range checks. Support both ELF32 and ELF64 headers/program tables;
  never apply a reference artifact's fixed ranges to a different identity or ELF class.
- Existing v0.8 Android-framework-only reflection is retained for its read-only checks. Do not add
  DJI/ART private-class reflection, class enumeration, or code loading.
- Activity launches are limited to explicit user clicks and the fixed Android Settings actions in
  `MainActivity`. Do not add packages, components, URIs, extras, or automatic launches.
- `ProbeRunState.COMPLETE` requires both v0.8 sections and the v0.10 ART identity section. Preserve
  the final-DEX semantic audit and its mutation suite; a marker/string check is not sufficient.
  The audit must prove false initialization/normal-return provenance for both completion flags,
  real-run/fail-closed provenance for the ART result, and unchanged persistence of the gate result
  into the retained snapshot's `runState`.
- Preserve the frozen application-owned external-invoke audit and the explicit final-DEX/source
  bans on native loading, arbitrary file-output APIs, network sockets and send/write syscalls.
  v0.12 permits only the independently reviewed report and fixed-sample sinks below. Do not update
  the invoke count/hash mechanically; any change requires a new version and manual safety review.
- Keep exact range names and machine keys: `Agent::Unload` / `art.agent_unload_range.*` at
  `0x5ccfa0 + 0x100`, and `Runtime::AttachAgent` / `art.runtime_attach_agent_range.*` at
  `0x56bfc4 + 0xebc`. Never restore the misleading attach/loader key names.
- Keep one process-lifetime probe coordinator. Activity recreation must neither start a duplicate
  worker nor lose the running/completed report. Keep Settings buttons in Device-info then
  Developer-options order and retain only the three fixed Android actions.
- Before sealing, run `scripts/build_and_audit.sh` and `scripts/reproducibility_check.sh`, audit every
  app DEX class and update versioned documentation. Keep the v10/v11 final-DEX profiles and history
  separate from the current v12 profile; do not replace their fingerprints with a new build's hash.
  The optional sealed-profile audit requires separately held historical APKs and exact ART input.
- Current v0.12 / A-039 has an observed `COMPLETE` report and validated four-file sample receipt
  (C-236–C-238). The operator can now open Developer Assistant; a fresh post-installation probe
  report is still pending. See [live runtime status](../../docs/23_RC2_LIVE_RUNTIME.md).

## User-requested report and sample exports

- A terminal `COMPLETE` or `INCOMPLETE` inspection automatically exports its immutable report once.
  Export status is separate and must never promote the inspection verdict. Rotation/resume must
  not create another export; a failed export may be retried explicitly without rerunning the probe.
- Only `ProbeReportStore` and its private Android backend may create/write/publish a report through
  MediaStore Downloads on the unique mounted, non-primary, non-emulated removable volume.
- The report store's only output is a new UTF-8 text file under `Download/FindUAS/Probe/`, with a
  fixed versioned prefix and validated run metadata. No user/Intent-controlled URI or path, old-file replacement,
  internal-storage fallback, broad storage permission or automatic network transfer is allowed.
- Publish only after a successful complete stream write/close. On failure, delete at most the
  pending URI created by this attempt; report cleanup failure separately. Never scan/delete older
  reports or claim MTP delivery from a MediaStore success alone.
- Full diagnostic reports remain private. Keep the app open until the save result, and verify a
  fresh final-name MTP listing and full readback before claiming host receipt.
- `InstalledFlySampleExporter` may separately read only PackageManager's `dji.go.v5` source APK
  and three fixed library basenames after matching version `1.19.4` / code `3113157`.
  `DJI_FLY.apk` and `libsdk_jni.so` are required; `libsdk_key_value.so` and `libsdk_base.so` are
  optional. Do not extend collection to app data, other packages, credentials or license files.
- Its only output is a new `FindUAS_Fly1194_<attempt-id>.zip` under `Download/FindUAS/Samples/`
  on the same unique removable-volume rule. Use the fixed four entry names and `manifest.json`,
  a 64 KiB copy buffer, 1 GiB per-file / 2 GiB aggregate input limits, and source identity/path and
  per-file metadata rechecks. Manifest hashes/sizes must describe the bytes actually copied.
- MediaStore sample writes belong only to the exporter's reviewed Android backend; ZIP writes stay
  in the reviewed exporter. Close the ZIP before publishing and delete at most this attempt's owned
  pending URI on failure. No arbitrary input/output path, old-row replacement or internal fallback.
- Sample export starts only on the explicit button. Keep its state across Activity recreation and
  serialize it with probe/report operations. Export result, missing optional files and cleanup
  status remain separate from the inspection's `COMPLETE` verdict.
- Both exported reports and vendor samples remain private. A saved UI result needs fresh MTP
  listing/full readback before host-receipt claims; sample entry sizes/hashes must also validate.
- Seal both source/DEX writer families and external-invoke changes only after manual review and
  adversarial tests. Preserve historical v0.10/v0.11 artifact identities and audit profiles.
  See [v0.12 export contract](REPORT_EXPORT_V12.md).
