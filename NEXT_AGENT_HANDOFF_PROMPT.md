# Next-agent prompt

Continue from current `main` on the user's DJI RC 2 `07.00.0100` / Mini 5 Pro lab setup. The goal is
a controllable Remote ID switch with readback and restoration, closed by independent standard-RID
receiver RF A-B-A evidence.

Read:

- `CODEX_PROJECT_PROMPT.md`
- `AGENTS.md`
- `docs/13_HANDOFF.md`
- `docs/12_CURRENT_BLOCKERS.md`
- `docs/19_RID_EXPERIMENT_CONTROL_MATRIX.md`
- `docs/20_OFFICIAL_FLYSAFE_UI_PATH.md`
- `host-tools/rid-switch-tool/README.md`
- claims C-188--C-212

Current facts:

- The aircraft transmits plaintext standardized Remote ID with readable Basic ID while motors spin,
  but exact bearer and motor-off/on/off timing still need one written A-B-A record (C-207).
- `EU_CE_enable_c0_rid` by-index and `EU_CE_enable_c0_rid_0` by-hash are the leading WA150 policy
  candidates. Host tools and Android codecs are tested offline, but no live read/write has occurred.
- Generic external Binder F7/F8/F9, the tested `0x11/0x1C` listener, and fixed `0x11/0x11` are
  closed negatives. Do not repeat them or guess route variants.
- The exact FlySafe owner/query path is emulator-observed. Ordinary installed-path,
  `trace_data_file`, and `apk_tmp_file` loader routes are closed; do not repeat them (C-208--C-211).

Priority:

1. Record C-207 motor-off → motor-on → motor-off receiver evidence without recording full IDs or
   coordinates.
2. Run a read-only WA150 positive-control session and decide whether the by-index or by-hash route
   is live.
3. Only after metadata and baseline readback, perform one transition, read back, restore, and read
   back again.
4. Close the result with operator-controlled motor-on RF A-B-A.
5. In parallel, determine the exact RC 2 DJI Fly and privileged-caller signer/SELinux domains and
   test only a legitimate delimiter-free loader or descriptor intersection.

Keep privileged runtime actions bounded and controlled. Do not repeat the public RC 2 TEE/eFuse
tamper/update bricking path (C-212). Do not publish vendor material, raw captures, full identifiers,
or coordinates. Keep scripts small, record every result, run the four repository checks, commit,
and push to `main`.
