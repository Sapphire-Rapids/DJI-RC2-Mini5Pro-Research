# Next-agent prompt

Continue from the current reviewed checkout on the DJI RC 2 `07.00.0100` / Mini 5 Pro `01.00.0600`
lab setup. The objective covers a controllable Remote ID switch plus Basic/UAS ID, aircraft-position
and operator-position controls, each requiring its own authoritative owner, readback, restoration
and independent standard-RID RF A-B-A evidence. Operator ID is a separate identity plane. The lab
states that DJI and the relevant low-altitude-economy authority
have authorized the work; that authorization is confidential, cannot be shared here, and cannot be
registered on the physical test aircraft.

Read:

- `CODEX_PROJECT_PROMPT.md`
- `AGENTS.md`
- `docs/13_HANDOFF.md`
- `docs/12_CURRENT_BLOCKERS.md`
- `docs/19_RID_EXPERIMENT_CONTROL_MATRIX.md`
- `docs/20_OFFICIAL_FLYSAFE_UI_PATH.md`
- `host-tools/rid-switch-tool/README.md`
- claims C-188--C-231, especially C-207 and C-227--C-231

Current facts:

- The aircraft transmits plaintext standardized Remote ID with readable Basic ID while motors spin,
  but exact bearer and motor-off/on/off timing still need one written A-B-A record (C-207).
- The direct-USB FLYC positive control passed on `01.00.0600`, but
  `EU_CE_enable_c0_rid(_0)` and `rid_ctrl_enable_0` have positive-controlled absence on that
  surface (C-227--C-230). The EU C0 block shifts +1 from the public table and its sampled flags
  have min/max 0. Neither target nor the neighbouring flags admit a write. These results do not
  rule out an app-layer owner, another firmware surface or encrypted WA150 `0802`.
- Generic external Binder F7/F8/F9, the tested `0x11/0x1C` listener, and fixed `0x11/0x11` are
  closed negatives. Do not repeat them or guess route variants.
- The exact FlySafe owner/query path is emulator-observed. Ordinary installed-path,
  `trace_data_file`, and `apk_tmp_file` loader routes are closed; do not repeat them (C-208--C-211).
- The original local research corpus has been located. Selected core DJI Fly/RC331 samples and
  A-032/A-033 outputs were rehashed and match the registered identities; this does not establish
  current installed or mounted RC 2 identity or change artifact admission.
- The latest 1558-slot/915-name enumeration files and completed C-207 RF timeline were not found
  in the bounded sandbox search. They may remain in old task outputs or application history;
  do not call them lost or replace missing provenance with a new device request by default.
- No real-aircraft field editor is admitted. Synthetic OpenDroneID work stays offline and does
  not substitute for aircraft owner/readback/RF evidence.
- Exact A-001 v0.10 is staged as removable-SD `Download/FindUAS_A001_V010.apk`; fresh unique
  listing and same-session full MTP readback matched size/hash (C-231). Installation and run
  remain pending. Obtain its privacy-reduced environment report before promoting live identities;
  the probe does not itself admit an attach or aircraft request.

Priority:

1. Recover provenance for existing FLYC and receiver records where available; account for the
   1558 reported table slots versus 915 named rows without exposing private data.
2. The next device objective is a bounded read-only RC 2 identity baseline, including current
   DJI Fly and caller/target signer, ABI and SELinux facts. Do not preselect an executable path.
3. Admit a legitimate delimiter-free loader or mediated descriptor from that evidence, then run
   the official inventory query once with a fresh callback and unchanged DJI Fly PID. Do not
   start with a setter, repeat the closed loaders or assume an ordinary APK can attach.
4. Independently map Basic/UAS ID, aircraft position, operator position and Operator ID owners,
   read paths and RF fields. An app location update or compliance serial is not yet RF correspondence.
5. Complete C-207's motor-off → motor-on → motor-off standard-bearer record with the operator if
   existing records cannot close it. Do not record full IDs or coordinates.
6. Only a separately admitted surface with a real baseline may advance to one bounded transition,
   independent readback, exact restore, final readback, persistence classification and RF A-B-A.

Keep privileged runtime actions bounded and controlled. Do not repeat the public RC 2 TEE/eFuse
tamper/update bricking path (C-212). Do not publish vendor material, raw captures, full identifiers,
or coordinates. Keep scripts small, record every result, run the four repository checks, commit,
and push to `main`.
