# Handoff rules for `minimal_rid_observer`

- Package only `app/src/safe`; the withdrawn socket-era `app/src/main` implementation is excluded
  from this public repository and must never be reintroduced.
- Generated APKs and the sealed v0.8/v0.9/v0.10 binaries are intentionally not committed. Any
  source change needs a new version/code/name/hash and a new static review.
- This probe requests no permission and packages no service, receiver, provider, or native library.
- Never add a localhost or network socket, DUML encoder/sender, DJI Binder application transaction,
  agent attach/load, root/process execution, another-process `/proc` path, or target file write.
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
  bans on native loading, file-output APIs, network sockets and send/write syscalls. Do not update
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
