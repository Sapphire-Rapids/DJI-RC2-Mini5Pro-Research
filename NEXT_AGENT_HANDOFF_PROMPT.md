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
- `docs/23_RC2_LIVE_RUNTIME.md`
- claims C-235--C-248 for the latest progress, plus C-207 and C-227--C-230

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
- The installed Fly is now verified as `1.19.4` / code `3113157`, ARMv7. A-039's COMPLETE
  report and the installed APK/three SDK samples were retrieved; Fuli/framework/services hashes
  and 32-bit ART identity are recorded. Earlier `1.21.10` results retain their original scope.
- The latest 1558-slot/915-name enumeration files and completed C-207 RF timeline were not found
  in the bounded sandbox search. They may remain in old task outputs or application history;
  do not call them lost or replace missing provenance with a new device request by default.
- No real-aircraft field editor is admitted. Synthetic OpenDroneID work stays offline and does
  not substitute for aircraft owner/readback/RF evidence.
- A-039 is the current probe: `Download/FindUAS_A039_V012.apk`. Old installers are in
  `Download/FindUAS/Archive/`. The original Fuli package has been reinstalled and the operator
  confirms DevActivity opens. The post-install A-039 COMPLETE report is now received (C-245):
  updated-system=true, the original code/hash/signer and two checked DEX entries are unchanged,
  and all three component entries are enabled. Earlier directory ABSENT results remain only the
  Observer app's view. C-246 now records the actual Shell `id` output: UID/GID 1000/system and
  domain `system_app:s0`. C-247 records `/data` and `/data/app` as mode 0771, system:system,
  with `system_data_root_file` and `apk_data_file` labels respectively. No test file has been
  created, copied or executed; canary execution remains pending.
- C-248 statically identifies package scanning/reconciliation that can delete unregistered
  subdirectories; both examined rules skip ordinary non-APK files. The candidate is a separate
  regular `.so` directly under `/data/app`, with no new subdirectory. This is not yet a tested
  file location or loader.
- A-040 is the new ARMv7 ART TI-only canary, already SD-staged but unexecuted. A-042 is the
  ARMv7 query build with the additional `-1` guard. The separate RID-state chain is mapped in
  C-240; unlock registration and the deferred certificate-page screenshot are not prerequisites.

Priority:

1. Recover provenance for existing FLYC and receiver records where available; account for the
   1558 reported table slots versus 915 named rows without exposing private data.
2. The post-install report, actual Shell identity and parent-directory observations are closed by
   C-245--C-247. The only current operator command is `ls -laZ /data/app`, to inspect its
   contents and check the proposed regular-file basename for a conflict (C-248). Do not create
   a subdirectory. File-level and target-process checks remain prerequisites before loading.
3. After the regular-file path checks and the target-process baseline are complete, validate A-040's
   explicit success marker and unchanged Fly PID, then advance the independent
   RID-state observation route. The deeper listener dispatcher/cancellation behavior remains to
   be checked before creating an observer. Keep old closed loaders and sender variants retired.
4. Independently map Basic/UAS ID, aircraft position, operator position and Operator ID owners,
   read paths and RF fields. An app location update or compliance serial is not yet RF correspondence.
5. Complete C-207's motor-off → motor-on → motor-off standard-bearer record with the operator if
   existing records cannot close it. Do not record full IDs or coordinates.
6. Only a separately admitted surface with a real baseline may advance to one bounded transition,
   independent readback, exact restore, final readback, persistence classification and RF A-B-A.

Keep privileged runtime actions bounded and controlled. Do not repeat the public RC 2 TEE/eFuse
tamper/update bricking path (C-212). Do not publish vendor material, raw captures, full identifiers,
or coordinates. Keep scripts small, record every result and run the four repository checks.
The latest user instruction pauses GitHub pushes only: keep local updates, validation and
commits, but do not resume pushes until the user restores authorization. Preserve historical
pushed results. Append completed actions to the existing timeline;
keep current operator instructions in the runtime topic and handoff, rather than creating competing logs.
