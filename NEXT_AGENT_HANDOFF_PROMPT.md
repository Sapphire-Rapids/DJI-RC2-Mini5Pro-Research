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
- claims C-235--C-295 for the latest progress, plus C-207 and C-227--C-230

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
  with `system_data_root_file` and `apk_data_file` labels respectively. That early baseline preceded
  the later successful A048/A051/A054 experiments below.
- C-248 statically identifies package scanning/reconciliation that can delete unregistered
  subdirectories; both examined rules skip ordinary non-APK files. The resulting ordinary `.so`
  path directly under `/data/app` was later exercised by A048/A051/A054. C-249 now records the complete listing: seven subdirectories
  (DJI_FLY at 0777, six randomized installation roots at 0775), all system:system with
  apk_data_file labels; `finduas_A040_canary.so` was absent.
- A-040 is the historical ARMv7 ART TI-only canary, already SD-staged but unexecuted. A-042 is the
  ARMv7 query build with the additional `-1` guard. The separate RID-state chain is mapped in
  C-240; unlock registration and the deferred certificate-page screenshot are not prerequisites.

Historical F1/A-043 was staged as `Download/F1.sh` with full readback matching 7,196 bytes and
SHA-256 `636a57319d6b53e874324adb67c6eab4b79fd73d703588e7a52e51bc1a381ece` (C-250/C-251).
C-252 records the photographed wrapper reaching `sh`, which tried the literal
`/storage/????-????/Download/F1.sh` path and reported `No such file or directory`. The input
matched the instruction; no F1 marker appeared and the script did not start. C-253 then
photographed `ls: /storage: Permission denied`. This is a directory-enumeration refusal,
not a result for reading an exact known child file.

C-254 closes the metadata/API check: `/storage` is mode 0710, shell:everybody, with
`mnt_user_file`; Fuli belongs to the everybody group and has search but not directory-read
permission. The API returned exactly one mounted public volume. Its identifier is retained
privately and must not be copied into public instructions.

Historical F2/A-044 removes global `/storage` traversal and uses that private exact entry. It
passed independent diff review, `sh -n` and eight host fixtures, including an actual mode-0111
parent that cannot be enumerated but permits an exact-path launch (C-255). `Download/F2.sh`
was created on SD and fully read back: 6,845 bytes, SHA-256
`808998e211f6af204f42df7fdce4257532dcccefd3f61420c8cfbccba08be02c` (C-256). The old F1 was
moved to `Download/FindUAS/Archive/F1.sh`, with matching full readbacks before/after and no deletion.

C-257 closes F2 execution, SD report saving and full MTP receipt: the 2,553-byte report passed
schema, terminal-marker and parser validation. Its status is INCOMPLETE solely because
`pidof dji.go.v5` returned rc=1 with empty output. System/system_app identity, SELinux Permissive,
ro.debuggable=1, wifi_on=0 and the 4,340-byte A-040 source hash all passed. No internal canary
copy or attach occurred. Keep the report name, volume identity and any process identifiers private.

C-258 now records the AMS LRU result: a `dji.go.v5` HOME main-process entry with a nonzero
PID. Its PID/UID are retained privately. This differs from the earlier empty pidof observation
and does not call for reopening Fly.

C-259 records a separate target-context path error without a mount-options line; it does not
resolve the process/view difference. Historical F3/A-045 collects AMS before/after and proc data
in one report. It passed 18 full shell fixtures and 14 independent parser/capture vectors
(C-260). `Download/F3.sh` is now staged with complete matching readback: 10,611 bytes, SHA-256
`1e87258dd013c00e720f20b4bc6981463197cef0d49a503a1bc1a577c6b1b5c0` (C-261). F2 was moved
to `Download/FindUAS/Archive/F2.sh`, with matching full readbacks before/after and no deletion.

C-262 closes F3 execution/report receipt. Both raw AMS entries use the same main PID; proc
mount options include gid=3009,hidepid=2, while the caller lacks group 3009. Android mksh
failed to create the heredoc temporary file twice, so the strict parser rejects the raw report.
The original file is preserved unchanged. F4 replaces that heredoc with a pipe. F4/B1 passed host checks and SD readback. One operator startup then enabled the
verified PING/SNAPSHOT/PING round trip (C-266/C-267). The F4 report is strictly valid, with
stable AMS PID and target-proc reads still hidden; preserve the active host session state. Do not repeat F3 or the manual proc commands.

Loading result (C-273--C-276): A-048 loaded successfully in the existing Fly process after the
live baseline passed. Canonical native identity, ART TI and disposal results all succeeded;
PID/UID/APK remained stable. The verified ordinary file was removed, independent cleanup found
it absent and B2 closed by STOP. A-040 remains untouched. Preserve the permanent A-048 attempt
marker and do not replay the canary. C-277--C-282 subsequently close the synchronous cache route
and A-051 live read: RID1/1, EID0/0, failReason0, one cache call, successful parse/disposal, stable
PID/UID/APK, file removed and independently absent; B3 STOP/CLOSED STOP completed. Preserve the
A-051 receipt too. C-283--C-292 then close the retained-cache semantics, exact cloud source and
A054 comparison: ProductType139,41 rows/36 distinct candidates, receiver18/4, match1/default0.
One MMKV decode and two SDK cache reads succeeded; file recovery/receipt readbacks and B4
STOP/CLOSED STOP are complete. Preserve A054 receipts. Next inspect the matched hex payload's
structure and receiving owner. No payload or actual App area was exported by A054.

Priority:

1. Recover provenance for existing FLYC and receiver records where available; account for the
   1558 reported table slots versus 915 named rows without exposing private data.
2. The post-install report, actual Shell identity and parent-directory observations are closed by
   C-245--C-247; the complete `/data/app` contents/basename check is received in C-249. C-254
   supplies the storage entry privately. C-257 closes F2 execution/report receipt and C-258
   supplies the AMS main-process identity privately. F3 validation/staging and execution are recorded in
   C-260--C-262. Its raw report supplies the live hidepid option and a shell compatibility defect;
   F4 then passed strict parsing with stable AMS PID and unavailable target proc reads (C-267).
   The B1 diagnostic round trip works (C-266); preserve its current host state rather than
   repeating F4 or the individual proc reads.
3. A-048/A-051 and A054 are complete, recovered and stopped. Use C-283--C-292 for retained
   cache behavior and RID policy/shared-cache content correlation. Next needs matched-row count,
   DEFAULT presence/nonempty and matched hex payload structure/version summaries; current
   reports lack that raw content. Do not repeat the basic cache read or add an unexplained SET.
   Timed RF correlation and listener lifecycle remain separate.
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

Latest prepared action (C-293--C-295): exact hex decode feeds the whole00/DD payload without
a new RID inner header. A057/L4/B5 and the offline structure analyzer are built and tested; all
three SD readbacks match. The current session awaits one B5 startup. Next collect one
STRUCTURE_BASELINE/STRUCTURE_READ, fetch only the session-named two-payload private JSON,
parse matched/DEFAULT structures and differences, then independent CLEANUP/STOP. No A057
attach has been submitted. Use original private SD client history and keep raw payload excluded.
