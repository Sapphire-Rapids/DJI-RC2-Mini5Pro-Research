# Current next-agent handoff

Continue the complete DJI RC 2 / Mini 5 Pro Remote ID research objective from the reviewed repository state.
This handoff is based on HEAD `e25c4aa` with committed claims through C-473; the working record now includes C-474/C-475 through 2026-10-18. Inspect current HEAD
and the working tree first; if newer work exists, preserve it and use the later evidence. Do not reset to this hash.

## Objective and current operating context

Implement and verify a Mini 5 Pro Remote ID switch and broadcast-parameter control panel. Its real-aircraft controls
cover the RID switch and, where an authoritative reversible path can be established, Basic/UAS ID, aircraft position
and operator position. UI completion does not replace per-control device/RF acceptance. Keep Operator ID
separate from Basic/UAS ID and operator position. The full objective remains active; offline findings are progress,
not completion. The lab's confidential authorization context and scope are recorded in
[CODEX_PROJECT_PROMPT.md](CODEX_PROJECT_PROMPT.md) and [AGENTS.md](AGENTS.md).

The user currently has no aircraft or controller available. Continue useful work with existing selected local
samples, reproducible offline tools, static analysis and bounded public sources. Do not issue a device-startup,
USB-reconnect, B5/B6, attach, capture or STOP instruction from historical session notes. A057/A060 captures and
prior loader experiments already have recorded outcomes; preserve their receipts and do not replay them.
If device-dependent evidence becomes necessary, leave that specific requirement explicit and continue independent
work instead of treating an old session or old mounted identity as current.

## Read first

1. [AGENTS.md](AGENTS.md), especially the current corrections and evidence/distribution rules.
2. The current opening and C-442--C-475 continuation sections of [docs/13_HANDOFF.md](docs/13_HANDOFF.md).
3. [AIRCRAFT_STUE_CHECKPOINT.md](host-tools/firmware-acquisition/AIRCRAFT_STUE_CHECKPOINT.md).
4. Claims C-442--C-475 in [evidence/claims.csv](evidence/claims.csv), mirrored in
   [docs/02_EVIDENCE_REGISTER.md](docs/02_EVIDENCE_REGISTER.md).
5. Sections 12--22 of [docs/07_FIRMWARE_TRUST_BOUNDARY.md](docs/07_FIRMWARE_TRUST_BOUNDARY.md), then the relevant
   [negative results](docs/09_NEGATIVE_RESULTS.md), [unknowns](docs/10_HYPOTHESES_AND_UNKNOWNS.md) and
   [current blockers](docs/12_CURRENT_BLOCKERS.md).
6. Verify each selected sample/tool in [evidence/artifacts.csv](evidence/artifacts.csv) and
   [docs/11_ARTIFACT_REGISTER.md](docs/11_ARTIFACT_REGISTER.md). Do not infer identity from a filename.

The older route-priority paragraphs and live-session instructions in project/topic documents are historical context.
The current unavailable-device condition and later retractions govern the next action. Use
[docs/03_TIMELINE.md](docs/03_TIMELINE.md) and [docs/23_RC2_LIVE_RUNTIME.md](docs/23_RC2_LIVE_RUNTIME.md) for history,
not as a queue of unfinished operator instructions.

## Latest continuation (2026-10-18, C-474/C-475)

C-474 uses new A-099 plus existing views to resolve selected Fly1.21.10 RID DeviceId input and exact caller18/4.
The inspected V1 supplier selects the first AIRCRAFT DeviceInfo.device_id; actual toggle/provider binding and numerical
DeviceId/ProductType equivalence remain unknown. Keep C-286/C-287 and live C-291 explicitly at Fly1.19.4; no selector bug
or retraction follows. No signed-body parser, device owner, readback or RF control was recovered.

C-475 traces a packaged RC331 sec_type2 condition through APS2 to the command name dji_verify and the packaged
same-name implementation. Its selected mode hashes/copies payload with fixed256-byte RSA length. The init service
names /system/etc/upgrade.json but the available config is vendor/etc/upgrade.json; the exact system member is absent
from the inspected image listing. Live config/mount/PATH binding is unknown. Do not merge this edge with C-456/C-457
or call variable header offsets WA150 signature/STUE support. A-100--A-103 remain excluded, never executed inputs.

## Prior continuation (2026-10-18, C-471--C-473)

A-093 is the exact Fly1.21.10 carrier. Its22 directory entries match independent DEX maps and page-rounded storage.
A-094 generates one analysis-only view per explicit invocation; four checked views A-095--A-098 change only relative
header[0,0x70) and string_ids[0x70,0x20000). Later bytes are identical. DEX035/link fields/new checksums are synthetic
assumptions. Five protected-type-table segments remain unrecovered. Do not claim original DEX identity, decryption,
all-app unpacking or ART verification. Carrier, derived views and vendor listings stay excluded.

C-473 connects selected Java registration/cache/clientLocation bodies to native serialization. For valid Android/default
altitude only, the API's meters/WGS84-ellipsoid contract explains a centimeters-scale x100 value. The inspected method
has no hasAltitude check and can combine newer network coordinates/time with older GPS altitude. AMap's reference
contract/runtime choice and separate GPS/barometric IClientAltitudeProvider remain distinct. Two on-demand caches
and newly sampled message epoch seconds do not bound fix age or prove fresh fixes. A-078 remains explicit22-byte input;
no typed editor or actual device/RF control is admitted. Independent review checked30 selected method mappings/offsets;
no Android/vendor Java, full ART verifier or native message path was executed in this Java pass.

## Prior continuation (2026-10-18, C-466--C-470)

C-466 is a bounded Android upgrade negative over exact config/signature/transfer/image-helper bodies,not the whole
SDK. C-467 refines the already known C-126 scales: exact MobileDevicePositionMsg/sdk40→handler22,Java byte[] provider,
message-construction epoch seconds,and a validity-like flag cleared for invalid finite coordinates without dropping
the queued message. Latitude/longitude ranges and pre-scaling are known; C-473 later advances selected Java/default
provider semantics. Actual provider/altitude validity/reference and RF correspondence remain open. A-078 stays the
explicit22-byte payload codec; no typed coordinate editor is added.

C-468 retracts Characteristics+0x30 as receiver; actual HostID override is conditional. Free KeyHandlers EID/position
use virtual+0x10,while+0x128 remains only the BaseAbstraction EID overload. Six prefix/helper cases do not run a full
SendSetPack or runtime route. C-469 removes five fake object headers/route CLI arguments and corrects OPID actions;
eight schema tests,nine valid CLI cases and five obsolete-argument rejections are offline payload evidence only.

C-470 officially reacquires the existing A-0661200 bytes and adds only A-092,the smallest1100 wa140bat compatibility
container. Both remain STUE with outer integrity checks; no RSA/key/decrypt/device attempt. Five other1100 variants
remain uninspected; do not label wa140bat as native WA150 battery hardware or1200 as a first-ever new sample.

## Prior parser/position continuation (C-463--C-465)

Java and Python status parsers now accept a minimum7-byte prefix and preserve unknown trailing bytes privately;
known fields, summaries, routes and sender gates are unchanged. C-147 is the length evidence;36 host tests pass,
with no APK build or deployment. Do not treat C-148's license semantics as length evidence.

A-089's exact JNI bytes show22-byte typed marshalling and the84-byte success payload. AES0x100 is256 key bits,
not output bytes; HMAC algorithm0 maps to SHA256 in original initialization instructions. C-467 subsequently maps
the upstream pre-scaling and epoch seconds,with altitude/source limits stated above. A-078 v3 now accepts
explicit serialized22/key32/IV16 inputs and emits LE32(80)+ct32+IV16+HMAC32, with no guessed coordinate units,
internal request header or transport frame. Four position tests and isolated original-fragment/helper comparisons
pass. The controlled SHA256 map node did not execute the Android global constructor. No complete handler,
SendSetPack, transport, aircraft or RF path ran. Keep36+4 host tests separate from the earlier59 firmware run.

The prior C-458/C-459 keychain result remains valid; old A-078 v2 mistakes stay retracted. The TEE position path
uses a distinct random-IV design, not the SDK's constant-IV input. STUE and protected TBIE-root gaps remain open.

## Established current state

- WA150 STUE plaintext has not been recovered; its authoritative RID broadcaster/control owner is not established.
- C-442--C-446 correct the Assistant XsBuffer vtable address point, IV dereference, MD5 logging and NFZ dispatch.
  NFZ has a deterministic 32-byte key and zero IV, but no proven ordinary-firmware/STUE call edge. Runtime-pointer,
  stack-tail, per-iteration-init and MD5-KDF models are withdrawn. Do not resume those sweeps.
- A-067/A-068/A-070 v2 fixes are verified separately from the old flawed probe. A-082 is a single-candidate implementation
  of the pinned public IMaH-v2 model, not a proven STUE algorithm or plaintext exporter. The recorded full firmware suite
  passed 59/59. C-451's three source-backed candidates on real 2603 all miss; C-445 direct CBC and C-447 fixed-WAES
  results remain separate experiments. Do not repeat them without new input or treat them as exhaustive exclusions.
- C-452 traces only Assistant method 4 / DJIFirmRegisterUpgrader: inspected download/cache, size/MD5, tar-copy and FTP
  edges preserve input bytes. No STUE decoder was recovered in that path; neither live WA150 method selection nor
  all-Assistant decoder absence is established. C-453 inspected 25 selected public IMaH source copies after screening
  517 fork metadata rows, not all fork sources or the entire web.
- C-454 confirms A-005/RC331 0200 has a clear outer layer and encrypted inner TBIE/FLYA. C-319 is outer-only and C-322's
  all-RC-plaintext conclusion is retracted. Six public-TBIE prefix probes were not full-checksum key exclusions.
- C-455--C-457 identify A-083 `bw_secure`, A-084 `libtee_util.so` and A-085 `dji_decrypt` from the existing verified OTA.
  They remain local and have never been executed. The static QSEE command chain reaches TBIE CMAC derivation using
  protected RPMB-root/HUK-backed input. Finding these components is complete; root input/HUK output and usable keys
  were not recovered. QSEE mode constants 1/2 are not independently named. The client assumes a 480-byte header,
  unlike WA150's 608-byte header/signature layout, and is not a ready-to-run STUE decoder.
- The specific open questions are RC331 TBIE's root input and STUE's own owner/derivation. Do not assume the two
  products share a key or scheme, and do not infer that every offline route is impossible.

Choose the next bounded investigation from a concrete available input or call edge that can answer one of those
questions or advance the full RID objective. Verify the resulting claim with the appropriate independent check;
keep structural observations, model hypotheses, candidate failures and actual plaintext success distinct.

## RID semantics and completion evidence

The six `rid-protocol` CLIs are offline hex generators without device transport. The current position tool validates an offline payload model only. The producer pre-scales coordinates as C-126/C-467
describe; C-473 adds selected Java/default-provider semantics without proving actual altitude validity, runtime provider or full device/RF behavior. France EID is France-specific, ADSBSwitch/AirSense is not a global RID switch, and the tested direct-USB
FLYC surface has positive-controlled absence for the two known RID parameter candidates (C-227--C-230).
Do not reopen those variants without materially new owner/handler/version evidence. WorkingStatusPush has no active
GET or established SET-to-applied/RF correspondence; ACK, UI, cache and an absent callback are not RF proof.
Use [docs/05_RID_CONTROL_SURFACES.md](docs/05_RID_CONTROL_SURFACES.md) and the
[control matrix](docs/19_RID_EXPERIMENT_CONTROL_MATRIX.md) for each separate business plane.

No real-aircraft field editor is admitted. For the switch and every requested field independently, completion requires:

1. an exact authoritative owner and a valid current baseline;
2. one bounded transition and strict independent readback;
3. restoration to the original value and final readback;
4. reconnect/reboot persistence and automatic-writer classification;
5. independent standard-RID receiver confirmation of the intended off/on or field behavior in an operator-controlled
   motor-on RF A-B-A experiment.

C-207's historical standard-RID observation does not replace the missing complete bearer/motor-timing record or a new
control transition. Software never starts motors. Synthetic OpenDroneID encode/decode, hashes or successful offline
tests do not satisfy real-aircraft RF acceptance.

## Work and record boundaries

Follow the existing authorized scope. Do not modify/flash boot, vendor_boot, vbmeta, TEE, QFPROM or eFuse, change the
bootloader lock state, install Magisk or repeat the recorded irreversible boot/update path. No such action follows
from finding the static QSEE chain. Do not publish vendor binaries, vendor disassembly/decompiled source, private
captures, full identifiers/coordinates, credentials or key bytes; retain only permitted hashes and high-level evidence.

For material results, synchronize the relevant topic, claim/artifact CSV and Markdown mirrors, timeline, blockers,
handoff and changelog. Preserve prior retractions and precise tested scope. Keep entrypoints concise rather than
appending superseded startup procedures. Run the four repository checks in AGENTS.md and the smallest relevant code
verification. GitHub pushes remain paused unless the user explicitly resumes them; continue authorized local work,
validation and commits. The absence of devices does not change the objective or the evidence required to finish it.
