# Handoff rules for `minimal_rid_observer`

- Package only `app/src/safe`; the withdrawn socket-era `app/src/main` implementation is excluded
  from this public repository and must never be reintroduced.
- Generated APKs and the sealed v0.8/v0.9/v0.10 binaries are intentionally not committed. Any
  source change needs a new version/code/name/hash and a new static review.
- This probe requests no permission and packages no service, receiver, provider, or native library.
- Never add a localhost or network socket, DUML encoder/sender, DJI Binder application transaction,
  agent attach/load, root/process execution, another-process `/proc` path, or target file write.
  The user's explicit 2026-08-30 request authorizes only the v0.11 report-export exception below;
  it does not change any device-control or target-code boundary.
- The v0.10 ART section may read only `/proc/self/maps` and the exact mapped non-symlink regular
  `libart.so` file. It must retain strict page-aligned/overflow/coverage parsing, non-zero maps and
  fstat devices, positive start addresses, unsigned device/inode tokens, `lstat` + `O_NOFOLLOW`,
  nanosecond metadata, and two exactly equal normalized maps snapshots. Do not weaken
  whole-file/build-id/named-range checks.
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
  v0.11 permits only the independently reviewed MediaStore report sink described below. Do not update
  the invoke count/hash mechanically; any change requires a new version and manual safety review.
- Keep exact range names and machine keys: `Agent::Unload` / `art.agent_unload_range.*` at
  `0x5ccfa0 + 0x100`, and `Runtime::AttachAgent` / `art.runtime_attach_agent_range.*` at
  `0x56bfc4 + 0xebc`. Never restore the misleading attach/loader key names.
- Keep one process-lifetime probe coordinator. Activity recreation must neither start a duplicate
  worker nor lose the running/completed report. Keep Settings buttons in Device-info then
  Developer-options order and retain only the three fixed Android actions.
- Before sealing any new artifact, run both scripts under `scripts/`, audit every app DEX class,
  read `INDEPENDENT_AUDIT_V10.md`, and update the versioned documentation/hash without claiming a
  device runtime result unless one was actually obtained. The optional sealed-profile audit also
  requires separately held historical APKs and exact ART input; neither is distributed here.

## User-requested v0.11 report export

- A terminal `COMPLETE` or `INCOMPLETE` inspection automatically exports its immutable report once.
  Export status is separate and must never promote the inspection verdict. Rotation/resume must
  not create another export; a failed export may be retried explicitly without rerunning the probe.
- Only `ProbeReportStore` and its private Android backend may create/write/publish a report through
  MediaStore Downloads on the unique mounted, non-primary, non-emulated removable volume.
- The only output is a new UTF-8 text report under `Download/FindUAS/Probe/`, with a fixed versioned
  prefix and validated run metadata. No user/Intent-controlled URI or path, old-file replacement,
  internal-storage fallback, broad storage permission or automatic network transfer is allowed.
- Publish only after a successful complete stream write/close. On failure, delete at most the
  pending URI created by this attempt; report cleanup failure separately. Never scan/delete older
  reports or claim MTP delivery from a MediaStore success alone.
- Full diagnostic reports remain private. Keep the app open until the save result, and verify a
  fresh final-name MTP listing and full readback before claiming host receipt.
- Seal the new source/DEX write boundary and external-invoke changes only after manual review and
  adversarial audit tests. Keep the historical v0.10 audit and artifact identity unchanged.
