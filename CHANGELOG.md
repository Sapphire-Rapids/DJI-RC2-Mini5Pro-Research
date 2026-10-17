# Changelog

## 0.4.61 - 2026-10-16

- Switched focus to the RC side; found DJI Fly libsdk_jni.so exposes the RID surface: EIDSwitch,
  IsEuCeEnableC0Rid, RidWorkingStatusPush, CccBroadcastSignalQuality, OIDIdentifier,
  ComplianceSerialNumber, EU_CE_enable_c0_rid_0 plus RIDRegistedInfoReq/ActionRIDRegistedInfo
  (C-373).
- Counted direct ADRP+ADD xrefs per symbol (C-374); focused on IsEuCeEnableC0Rid and
  RidWorkingStatusPush.
- NEGATIVE: EU_CE_enable_c0_rid_0 has no direct xref, so it is reached indirectly
  (C-375, N-86).

## 0.4.60 - 2026-10-16

- RC-side recon: rc331 partition `rid_enable`/`RID_ENABLE` hits are video-encoder properties and
  `RemoteId` hits are AOSP/Chromium classes, so neither is Remote ID; the DJI_FLY.apk bytes live in
  /data/app and are absent from the OTA (C-371, N-85).
- DJI Fly's package dji.go.v5 is referenced across five partitions, so native/config pieces do sit in
  the OTA (C-372).
- Correct route: use the external DJI Fly dump for the RID toggle and treat rc331 partitions as
  native/config corroboration.

## 0.4.59 - 2026-10-16

- NEGATIVE: 20000-iteration random struct-seed sweep (random pointer+tail, 3 cap/len, raw/transformed,
  120k attempts) still misses (C-370, N-84).
- Pointer/tail are thus densely covered; the likely remaining lever is the unjudged init-per-iteration
  question, which would zero the seed middle and change the search space.

## 0.4.58 - 2026-10-16

- NEGATIVE: tail/pointer/cap/len seed variants still miss (C-368, N-83).
- Realisation: the key comes from strlen on the transformed buffer, whose 0x00 vtable byte stays zero
  under ror8, so strlen stops ~index3 and MakeKey then reads past the NUL into the object; the
  effective key bytes are mostly the post-NUL object area (C-369).
- Next: rebuild so the key is taken from index3 onward across the struct fields rather than treating
  the struct as a strlen-truncated prefix.

## 0.4.57 - 2026-10-16

- Scanned all four wa150 modules: uniform header_version2 + STUE + attrib0x0 (C-366).
- NEGATIVE: raw payload checksum matches plain_cksum in none of them, so a clear attrib bit0 does not
  mean plaintext and decryption is genuinely required (C-367, N-82).

## 0.4.56 - 2026-10-16

- Dense in-process pointer brute (6144 combos) over the synthetic struct seed still misses (C-365,
  N-81).
- Key realisation: the loop bound is the length0x2c, i.e. 12 bytes beyond the32-byte struct, and
  -0x208+44 lands on the neighbouring -0x1d0 area - so the missing ingredient is those tail bytes.
- B-23 becomes 'include the 12 tail neighbour bytes' or an address-independent re-read.

## 0.4.55 - 2026-10-16

- Recorded the XsBuffer field layout: 0x0 vtable, 0x8 malloc data pointer, 0x10 capacity, 0x18 length;
  the live object is exactly 32 bytes and is the range the transform indexes (C-363).
- NEGATIVE: structure-mimicked seeds with a 64x16 heap-pointer sweep and fixed cap/len still miss
  (C-364, N-80).
- B-23 becomes a multi-dimension address sweep (pointer, cap/len, base prefix) or an
  address-independent re-read of the loop.

## 0.4.54 - 2026-10-16

- Key correction: cvPc tail-calls append and returns this, and append returns this, so the indexed seed
  is the XsBuffer struct bytes (vtable low bytes + pointer fields), while appended chars sit in the
  0x8(this) malloc block and do not enter the seed. The seed therefore embeds runtime address low
  bytes and a static replay must approximate or emulate allocation (C-361).
- NEGATIVE: coarse pointer seeds (vtable+zero/+buf/bare) still miss (C-362, N-79).
- B-23 now requires emulating the allocation addresses, then transforming to a key.

## 0.4.53 - 2026-10-16

- Confirmed the transform is an in-place, byte-local rewrite (read and write share the object and
  index rbx; both accumulator loads are the current byte before the write), excluding a streaming
  interpretation (C-360).
- NEGATIVE: rol/ror direction, mod17/mod16/reversed pad, forward/reversed seed all miss
  (C-359, N-78).
- B-23 is now a single action: include the object struct field low bytes with the appended chars to
  rebuild the seed.

## 0.4.52 - 2026-10-16

- Mapped the XsBuffer vtable (0x30=append(char) returns this, 0x38=cvPc data); the chain's *0x20 hits
  D0 and the transform loop indexes the object bytes at rbx, so the seed may include struct pointer
  bytes rather than only appended chars (C-357).
- NEGATIVE: all25 rotations x reversal x raw/transformed still miss (C-358, N-77).
- B-23 is now concretely 'include the struct field bytes in the seed rebuild'.

## 0.4.51 - 2026-10-16

- Confirmed the FirmPack path routes into the analysed scheme: ProcessUpgradeFirmPack calls
  UpgradeMgr::UpgradeNfzPack via a websocket writer, and the local .fw.sig is exactly such a pack
  artifact, so the earlier category-mismatch worry is lifted (C-355).
- NEGATIVE: neither NfzPack function decodes base64/hex, so pack bytes reach the crypto raw
  (C-356, N-76).
- B-23 returns to the byte-level residual: setter immediate role and seed rebuild.

## 0.4.50 - 2026-10-16

- Scoped the analysed scheme: UpgradeNfzPack reads JSON `version`/`code` and `url`, logs strUrl and a
  fetched size, so the md5/transform/xor key belongs to a remotely fetched nfz pack, not a local
  .fw.sig (C-353) - applying it to the local chunk is a possible category mismatch.
- NEGATIVE: UpgradeFirmPack carries no direct aes/WAES/CRijndael/Imah call (C-354, N-75).
- B-23 first asks whether the local .fw.sig routes through NfzPack at all; otherwise return to the
  tool IMaH scheme for the STUE key source.

## 0.4.49 - 2026-10-16

- Re-verified the aesDecode2 call ABI (rdi sret, rdx key, rsi data) and that -0x218 stays untouched by
  the field chain, so data=ciphertext and key=transformed seed string (C-352).
- NEGATIVE: ascending/descending key-sorted orderings with/without the 0x22 buffer prefix still miss
  (C-351, N-74).
- B-23 narrows to deciding whether the setter immediate is a map key or the emitted value.

## 0.4.48 - 2026-10-16

- Characterised the seed container shape: a mallocs0x22 fixed byte block with ASCII `74 59` (`tY`) at
  its head, plus further negative-key map fields; the25-byte constant list is recorded (C-349).
- Noted the fields are written as negative map keys, so emitted order is not list order - the residual.
- NEGATIVE: full/prefix-dropped/capped seed variants as key still miss (C-350, N-73).

## 0.4.47 - 2026-10-16

- Established that the transform source -0x208 is a built seed container (XsBuffer append plus ~20
  virtual immediate-byte field sets), not the ciphertext; the derived key is over the seed while
  aesDecode2's data stays the ciphertext (C-347).
- NEGATIVE: extracted constant seed raw/transformed as key with optional post-XOR still misses
  (C-348, N-72).
- B-23 narrows to the container's field serialization order/layout.

## 0.4.46 - 2026-10-16

- Corrected the key slot: -0x1d0 is overwritten by the transformed buffer wrapped as a C string
  (memcpy -> std::string -> strlen -> QString::fromAscii_helper), and it is the aesDecode2 key; the
  earlier MD5-hex is only the `nfz before decode md5` log value (C-345).
- NEGATIVE: the C-string transform key (and raw t-32) with optional post-XOR still misses
  (C-346, N-71).
- B-23 narrows to confirming whether the -0x208 XsBuffer object carries the ciphertext and the
  transform direction.

## 0.4.45 - 2026-10-16

- Pinned the rotate pairing exactly: both loads are the same source byte, and the shifts collapse to
  a single-byte self-rotate `ror8(b, i&7)` before the mod17 pad XOR (C-343).
- NEGATIVE: the exact transform plus md5/hex-of-md5 keys over enc/scram/header/sig against the tool
  ck/CTR/ECB and CBC scheme still miss (C-344, N-70).
- B-23 narrows to two choices: which buffer is fed, and whether NfzPack is the module path at all.

## 0.4.44 - 2026-10-16

- Resolved the XOR pad shift arithmetic: the index is `rbx mod 17` via a divide-by-17 magic
  (0xF0F0F0F0F0F0F0F1), giving a16+NUL byte period with index16 =0x00 (C-340).
- Identified the same loop as a bit-packed rotate across adjacent bytes (shrq/shl with 7-bit masks)
  before the pad XOR (C-341).
- NEGATIVE: md5hex(enc)/md5hex(rotated) keys, enc/rotated data and full-length post-XOR in le/be
  still miss (C-342, N-69). B-23 narrows to the exact rotate pairing and fed buffer.

## 0.4.43 - 2026-10-16

- Pinned the exact NfzPack key derivation: `MD5(data,len)`, digest()'s16 bytes written as ints to an
  ostringstream with hex base and `0` fill, `str()` giving32 lowercase zero-padded hex chars passed
  as aesDecode2's key (C-337).
- Found the XOR pad pointer is shifted (`subq %rcx, %rsi`), so literal indexing is not a clean16-byte
  cycle (C-338).
- NEGATIVE: md5hex/uppercase/raw/truncated/hex-of-hex keys plus self-consistent XOR-then-md5 variants
  still miss (C-339, N-68). B-23 narrows to stream prefix/zero-padding and the pad shift source.

## 0.4.42 - 2026-10-16

- Found the NfzPack key derivation: a `std::ostringstream` fed from a local input-buffer copy with
  `std::hex`, `str()` into a `std::string`, passed as aesDecode2's key and reinterpreted as QString;
  MakeKey consumes the first0x20 bytes (C-335). The key is therefore derived on the fly, not external.
- NEGATIVE: lowercase/uppercase hex, first16-byte hex and raw first32 bytes as keys, with the real
  aesDecode2Ex in both AES/XOR orders, still miss (C-336, N-67).
- B-23 narrows to the exact fed buffer (pre/post XOR) and format details.

## 0.4.41 - 2026-10-16

- Established the NfzPack lambda interior: the16-byte literal is a streaming XOR pad (`xorb`), while
  the `aesDecode2` key is the lambda's `QByteArray const&` parameter, reinterpreted as QString for
  `toStdString`; decrypt is followed by `pkcs7UnPadding` (C-333).
- NEGATIVE: the real aesDecode2Ex composed with the literal XOR in both orders, for literal /32-byte
  pool / zero keys, still misses the plaintext checksum (C-334, N-66).
- H-36 and B-23 now target backtracking the caller-supplied QByteArray key; framing, XOR pad and
  padding are settled.

## 0.4.40 - 2026-10-16

- Reversed the firmware crypto framing: `aesDecode2` builds `CRijndael`, `MakeKey(key, sm_chain0,32,16)`
  then `Decrypt(len,1)` — AES-256 CBC with a fixed IV, key via `QString::toStdString` (C-331). Callers
  include the `UpgradeNfzPack` lambdas where the key is the16-byte literal.
- Made `aesDecode2Ex` ctypes-callable and confirmed keys change output.
- NEGATIVE: the real helper on the2603 chunk with literal /32-byte pool / zero key stays length-
  preserving but does not match the plaintext checksum (C-332, N-65). Framing is proven; only the
  module-key question remains.

## 0.4.39 - 2026-10-16

- Corrected the WAES scope: its only callers are `GetPublicValue`/`GetPrivateValue`, so the recovered
  whitebox key is that value crypto, not necessarily the IMaH STUE key (C-329).
- Located the firmware path: firmware classes call `aesDecode2`/`aesEncode2` with QString keys, and a
  single16-byte key literal `1ff6b8ca503b47ad8d04d8686dcb13a0` sits at three call sites (C-329).
- NEGATIVE: the literal as raw plus MD5/SHA256/UTF-16/base64 derivations across tool scheme, CTR/CBC/
  CFB/OFB and several IVs still misses (C-330, N-64). `aesDecode2` inner framing is not yet reversed.
- H-35 and B-23 now redirect to disassembling `aesDecode2` first.

## 0.4.38 - 2026-10-16

- Decomposed every `t_box_dec` table: each is affine in128`InvSbox(x^k)` with coeff1 plus a constant
  encoding, giving exactly one key byte per table; candidate key
  `5ac8ed5cf0fa5e5d77b5c89599bb87d5`, reproducible via `wb_aes_key_recover.py` (C-327, A-069).
- Confirmed the whitebox interior is only InvSubBytes + AddRoundKey + constant encoding; MixColumns
  lives in `shift_mix`.
- NEGATIVE: the constant encoding means plain AES is not the whitebox, so the key stays a hypothesis;
  plain AES across modes/IVs and an OFB/CFB extension all miss, and a hand-built emulation is not yet
  byte-equal to the WAES oracle (C-328, N-63). B-23 narrows to encoding cancellation and round order.

## 0.4.37 - 2026-10-16

- Recovered DJI Assistant's baked whitebox AES-128 as a callable primitive: all six service dylibs
  embed the same `t_box_enc`/`t_box_dec` tables; a mirrored framework tree plus an ad-hoc re-signed
  interpreter loads the x86_64 dylib under Rosetta and roundtrips (C-325). Reproduced as
  `wb_aes_bridge.py` with three passing tests (A-067).
- Added `stue_plaintext_probe.py` (A-068): it first validates the encrypted-checksum byte ranges
  (negated additive form) MATCH, then enumerates crypt-key/stream direction, CTR counter order and
  position, CBC iv and ECB. The plaintext checksum still misses (C-326, N-62).
- Byte ranges are confirmed, so only the key/mode mapping is open; an unenumerated mode, another key
  source, or WAES being unrelated to STUE all remain possible.

## 0.4.36 - 2026-10-16

- Fetched the smallest WA150 `1200` module as a cheap STUE brute oracle by manual LockedTarget
  injection (C-323); official MD5/size matched.
- Parsed the Assistant dylibs: each embeds four plain2048-bit PRAK structs (two byte-identical to
  public PRAK-2017-12/-08) but none3072-bit and no plain16-byte enc/STUE constant (C-324).
- Full brute of Uav dylib, Fly libsdk_jni non-exec segments, and libuav_keys.so, zero plaintext
  hits; simple brute exhausted, next is whitebox or public release (N-61).

## 0.4.35 - 2026-10-16

- Fetched six current same-version firmware modules over the official Assistant metadata/CDN path;
  every file matched official size/MD5 and registered SHA-256 (C-316). Cloned the pre-existing local
  third-party A-029 aggregate for locality only and clarified `07.00.0100` ↔ product_version
  `10.00.0700` via the existing register.
- Added a local PKCS1-v1.5 fallback to the out-of-repo pinned tool (wa150 signs PKCS1 despite
  header_version2). RC331 `0205` then decrypted with no force, all three layers passed, plaintext is
  an Android11 A/B OTA with29 dumped partitions (C-317); recovered `adbd` (A-030) and
  `dpad_fuli.apk` (A-031) are byte-identical to their identities (C-318).
- Recorded that RC331 `0200` and all RC331 aggregate modules are plaintext, while every WA150 module
  is `enc_key=STUE` (C-319/C-322). `STUE` is absent from the public corpus and its forks; a brute over
  all16-byte keys with derived variants/3 modes/3 IVs/v1-v2 semantics gave zero plaintext-checksum
  hits on2603/0802 (C-320). The3072-bit wa150 PRAK is also absent (C-321).
- New artifacts A-063 (decrypted0205), A-064 (OTA payload) and A-065 (0802 STUE ciphertext);
  new negatives N-59/N-60, hypothesis H-34, blocker B-23; correction50 in AGENTS.md. Results and
  derived inputs stay local and excluded.

## 0.4.34 - 2026-08-31

- Completed the B6 baseline and one A060 capture:41 rows/10907 private JSON bytes,
  stable target, successful file recovery and matched permanent receipts (C-310--C-312).
- Verified all36 signature envelopes; independent comparison finds25 signed messages,
  six whole-body patterns and one26-byte/two-segment candidate body (C-313).
- Added offline repeated13-byte segment and split-byte interpretations with52 passing
  public tests (C-314). Related local enums did not match the candidate discriminator (C-315).
  Field names remain under H-33; results stay local.

## 0.4.33 - 2026-08-31

- Narrowed the firmware and adjacent SDK receiver leads (C-306/C-307).
- Added A060 complete stored RID policy export, L5/B6 fixed jobs and passing native,
  differential,13 integration and74 host tests (C-308).
- Verified all three SD readbacks, closed B5 normally and prepared a new B6 session;
  one operator startup is pending (C-309). Changes remain local.

## 0.4.32 - 2026-08-31

- Captured the actual matched/first-DEFAULT policies with A057:97 bytes each,826-byte private
  report, successful lifecycle/file recovery and retained receiver (C-301/C-302).
- Parsed the20+13+64 envelope and recorded the first body byte as an unnamed1/0 candidate
  under H-33 (C-303).
- Independently verified both existing P-256/SHA-256 signatures and added47 tested offline
  structure/verification checks (C-304). Bounded plaintext owner searches are recorded in C-305.
- Results are synchronized locally; no new GitHub push was made.

## 0.4.31 - 2026-08-31

- Closed the exact hex-to00/DD inner-byte boundary (C-293).
- Added a bounded matched/first-DEFAULT private SD export and offline structural comparison;
  native, storage, parser and bridge tests pass (C-294).
- Staged A057/L4/B5 with matching readbacks and prepared the next session (C-295).
  B5 startup and all23 baseline checks then succeeded (C-296); MTP failed before READ allocation.
  G HUB and ADB were stopped after the operator reported repeated connection interruptions;
  the operator then confirmed stability (C-297).
- Disabled libmtp's automatic whole-device USB resets with an enforced static-link guard;
  host tests and a live blocked-reset observation passed (C-298). Controller reboot recovery
  recovered file access; old baseline history was preserved and a fresh B5 session activated
  through explicit reboot recovery (C-299/C-300). Updates remain local.

## 0.4.30 - 2026-08-31

- Resolved RID cache expiry/deduplication and exact-version UI/adapter ownership (C-283--C-285).
- Closed the app cloud selector, product-type exclusions, service gate and shared last-SET cache
  source; recovered an existing-instance MMKV read path (C-286).
- Added sanitized offline/C candidate comparison and A054/L3/B4, with native/JNI/receiver/client
  and differential tests (C-287/C-288).
- Staged all three files with matching full SD readbacks and prepared the B4 session (C-289).
  B4 then completed baseline/read/cleanup/STOP: ProductType139,41 rows,36 distinct candidates,
  candidate match1 and DEFAULT match0; JNI/guard/parser/disposal succeeded. File absence,
  permanent receipts and CLOSED STOP were independently checked (C-290--C-292).
  This progress remains local.

## 0.4.29 - 2026-08-31

- Closed the exact Fly 1.19.4 synchronous RID cache entry and serialized value format (C-277).
- Added A-051 with one initialized-owner cache read, nullable results and bounded status-only
  parsing; 25 native cases, nine loader tests, three receiver tests and 36 client tests pass (C-278).
- Added L2/B3 staging and session handling. USB reconnection restored MTP; all three payloads
  have matching full SD readbacks and the startup command was supplied (C-279).
- The preceding six commits through `2f31394` were pushed on the operator's one-time request.
  This new work remains local.
- B3 then completed baseline/read/cleanup/STOP: one official cache call returned RID1/1, EID0/0
  and failReason0; parsing/disposal succeeded, the file was removed, and independent cleanup plus
  receipt readbacks and CLOSED STOP completed (C-280--C-282).

## 0.4.28 - 2026-08-31

- Mapped the exact system-mediated loader and ART TI environment lifecycle (C-268).
- Added independent A-048 self-identity canary source, tests and reproducible ARMv7 builds; the
  SD readback matches, and the preceding B1 session closed normally (C-269/C-270).
- Added L1/B2 fixed baseline/load/cleanup tasks with 13 mksh tests (39 scenarios), two dispatch
  tests and 29 client tests. All three SD files read back correctly and the new session was
  prepared (C-271/C-272).
- B2 subsequently passed its live baseline and loaded A-048 once inside the unchanged Fly
  process; identity/API/disposal succeeded and independent cleanup confirmed file removal.
  STOP/CLOSED STOP completed (C-273--C-275). The RID getter/cache review is recorded in C-276.
  Changes remain local; no GitHub push.

## 0.4.27 - 2026-08-31

- Fixed F3's Android mksh heredoc failure in F4 by feeding AMS text through a pipe. Eighteen
  complete mksh fixtures and twelve temp-policy comparisons passed (C-263).
- Added the finite B1 receiver, MTP transport and host client. Receiver integration checks pass
  (C-264); F4/B1 SD readback and session preparation completed (C-265).
- After one operator startup, PING/SNAPSHOT/PING completed with verified reports (C-266). F4
  strict parsing succeeds; AMS PID is stable and target-proc access remains unavailable (C-267).
- Reconciled takeover and blocker summaries with the received F3 report, including the observed
  proc policy and preserved raw parsing errors. GitHub synchronization remains paused.

## 0.4.26 - 2026-08-31

- Added F3's paired AMS/proc diagnostics with strict main-process parsing, before/after AMS
  checks, separate stability fields and complete proc-mount output. Fourteen parser/capture
  vectors and eighteen host shell fixtures passed (C-260).
- Staged A-045 with full matching readback and archived F2 with verified before/after reads;
  operator execution and report receipt are next (C-261). Changes remain local.
- F3's raw report records live proc gid=3009/hidepid=2 and matching raw AMS PIDs, but Android
  mksh rejected its heredoc temporary files, leaving two unframed errors (C-262). Fixing that
  compatibility issue now accompanies the requested SD task automation.

## 0.4.25 - 2026-08-31

- Read `/storage` mode 0710 and one mounted public volume through the system API, establishing
  search permission without directory enumeration for the Fuli caller (C-254).
- F2 removes the global storage glob while preserving the fixed read/report operations. Eight
  host fixtures passed, including a parent permitting search but denying listing (C-255).
- Staged A-044 with full matching readback and archived F1 with matching before/after readbacks;
  the exact-path F2 launch and report are next (C-256). GitHub synchronization remains paused.
- Received F2's complete SD report: only pidof returned rc1/empty; the other eleven commands and
  A-040 source checks passed. The next read uses AMS's package-filtered process record (C-257).
- AMS returned the exact Fly main-process name and a nonzero PID. The next read uses that private
  PID for target context and proc mount diagnostics, without restarting Fly (C-258).
- The separate target-context read returned a missing path; a combined AMS/proc report is being
  prepared to pair process identity and file reads in one run (C-259).

## 0.4.24 - 2026-08-31

- Received the full two-photo `/data/app` listing; the proposed standalone canary basename is
  absent. Existing Fly package/library path records avoid another manual directory check (C-249).
- Added A-043 F1 to collect fixed process/source-file reads into one SD report. Source review,
  syntax, three Java launcher cases and seven host shell fixtures passed (C-250). SD staging and
  full readback matched; operator execution/report receipt are next (C-251).
- The first launcher attempt returned an unmatched wildcard path before entering F1; the next
  read is the storage layout visible to Fuli (C-252).
- The stderr-capturing follow-up identifies `/storage` enumeration as permission-denied;
  directory metadata and the system volume API are the next diagnostics (C-253).

## 0.4.23 - 2026-08-31

- Received the post-install A-039 COMPLETE report: Fuli is updated-system with the original
  package identity and all three checked entries enabled (C-245).
- Recorded direct Developer Assistant Shell output: UID/GID 1000, system_app domain, and
  system-owned mode-771 `/data` and `/data/app` with their actual SELinux labels (C-246/C-247).
  The canary remains SD-staged; no internal test file or attach has run.
- Checked exact PackageManager scanning/boot reconciliation rules and dropped the proposed test
  subdirectory; ordinary non-APK files are skipped by both examined candidate filters (C-248).
- Paused GitHub synchronization at the operator's request; subsequent progress stays local.

## 0.4.22 - 2026-08-31

- Closed SD report receipt and identified the installed Fly as `1.19.4` / code `3113157`, ARMv7.
  Probe v0.12 (A-039) fixes ELF32 and enabled-state handling and exports fixed installed samples;
  94 JVM tests, 8 auditor tests, 37 rejected mutations and reproducible builds passed.
- Verified the live APK and three SDK libraries, mapped the exact FlySafe and independent RID
  working-status chains, fixed the query's `-1` device-ID guard and added ARMv7 builds (A-042).
- Added a pure ARMv7 ART TI canary (A-040), its build helper and 10-case fake-VM test; four fault
  variants were rejected. Added the host test to CI. The canary is SD-staged and unexecuted.
- Located the normal original-package reinstall path for Fuli. The operator installed the
  verified original and can open DevActivity; the post-install probe and Shell baseline are next.
- Archived eight superseded SD installers without deletion. Added claims C-235--C-244,
  artifacts A-039--A-042 and the current runtime topic; linked the timeline from the home page
  and made per-result GitHub synchronization part of the update workflow.

## 0.4.21 - 2026-08-30

- Added the explicitly requested SD report export in probe v0.11/code11 (A-038): one new fixed-
  directory MediaStore report per terminal inspection; failure-only save retry; no new permissions,
  device-control, network or attach behavior.
- Preserved the v0.10 core schema and completion proof, added app-version/final-file markers, and
  fixed the UI completion race by rendering/scheduling from one atomic display snapshot.
- Reviewed the new narrow write boundary; 69 JVM tests, 8 audit tests and 30 rejected mutations
  passed. Two clean builds matched the reviewed APK; the historical v0.10 profile still passes.
- Staged the new APK and verified full RC 2 SD readback (C-233/C-234). Installation/run and actual
  report receipt remain pending. Raw reports and MTP logs stay private.

## 0.4.20 - 2026-08-30

### Fixed

- Reconciled current handoff entrypoints with C-227--C-230; the two rejected FC candidates are no
  longer the next live task. The research scope now includes the aircraft's actual Basic/UAS ID,
  aircraft position and operator position, with Operator ID kept separate and synthetic work offline.
- Fixed bounded host recovery after uncertain write ACKs, JSON reporting on early/error exits,
  one-byte Boolean encoding, by-index response/table checks, bridge handling, and extended RID
  status parsing. Added fake-transport failure coverage rather than reopening a device route.
- Added the distinct A-037 Admin identity safety lock: EID/OPID writes locked at UI and sender,
  OPID diagnostics masked, recoverable baselines checked and stale-session restoration rejected.
- Added missing device-read, control-flow, synthetic-codec and Android Admin checks to CI.
- Local validation: 270 Python tests and 170 Admin JVM tests passed; the same-process inventory
  parser/build also passed. These are offline results; the new remote CI workflow has not run yet.

### Evidence

- Recovered the old local corpus without importing private/vendor material or uncommitted drafts.
- Re-audited exact A-001 and staged one APK on RC 2 removable SD; fresh listing and full readback
  matched its identity (C-231). Operator installation/run and the environment report remain pending.
- Registered A-037's 170 passing JVM tests, lint 0 errors/15 warnings and identical clean builds
  (C-232); the APK was not staged, installed or run. No aircraft write, attach, motor or RF action.

## 0.4.19 - 2026-08-30

### Added

- Recorded the first live Mini 5 Pro FLYC positive control (route CRC/count + max_height_0 value
  500) and the positive-controlled absence of `EU_CE_enable_c0_rid_0` and `rid_ctrl_enable_0` on
  firmware 01.00.0600, plus the +1 index shift of the EU C0 block (C-227--C-230).
- Fixed the F7 metadata name check to accept the canonical on-board name without the `_0` instance
  suffix (the FC answers with the plain name).

## 0.4.18 - 2026-08-30

### Fixed

- Registered `importlib`-loaded sibling modules in `sys.modules` across the host tools, libraries and
  experiments (16 files), fixing a `dataclasses`/`sys.modules` crash on Python 3.13+ when a
  by-index/by-hash probe loads a `@dataclass`-bearing protocol module; the read-only RID probes
  now execute on modern Python.

### Added

- Surveyed public DUML / Remote ID community repositories (FreeFCC, lmdegreeds/djiparam,
  GlassFalcon, dji-ocusync-droneid-research) and recorded the new public-reference facts as
  C-213 through C-217 plus a survey note (`docs/22_COMMUNITY_DUML_RID_SURVEY.md`).
- Recorded the by-index FLYC sender-identity gate (`0x0a` only), the wa150 EU C0 block layout
  including the zero-range `EU_CE_Reg_RID_Enable` / `eu_ce_support_remote_set_level` rows, the
  Neo 2 index-drift warning, the O4 private DroneID AA/87 cryptographic chain, and FreeFCC's
  explicit no-Remote-ID position.
- Cross-referenced the EU C0 block boundary into `docs/05_RID_CONTROL_SURFACES.md` (RID-009) and
  extended the evidence register, timeline, and source index.
- Recorded the operator-confirmed Mini 5 Pro aircraft firmware `01.00.0600` as C-220, noted it
  inside the CVE-2026-78306 / CVE-2026-77812 affected window, and reconciled the by-index sender
  gate as transport-specific with the RC 2 localhost `40008` path (C-213/C-218/C-219).
- Recorded the wa150 table absence of `rid_ctrl_enable_0` and the dated no-second-implementation
  survey result (C-221/C-222).
- Refined C-221 with the wa150 China-broadcast sibling rows and added third-source by-index
  corroboration from `o-gs/dji-firmware-tools` (C-224).
- Added a cross-model EU C0 / RID parameter inventory narrowing `EU_CE_enable_c0_rid` to the
  Mini 5 Pro / Lito X1 pair while the zero-range EU C0 registration block spans five models (C-225).
- Re-bridged the full wa150 RID/EU C0/China family to by-hash and matched `o-gs`
  `flyc_parameter_compute_hash` across 15 names (C-226).
- Added an independently written, byte-compatible standardized OpenDroneID synthetic wire codec
  (`libraries/opendroneid-synthetic-codec/`) with Core C reference vectors and 12 tests, confined
  to the separate synthetic source lane (C-223).

## 0.4.17 - 2026-08-30

### Changed

- Declared the controllable Mini 5 Pro Remote ID switch as the repository's sole objective.
- Recorded the lab's confidential DJI and low-altitude-economy authorization context and stated that
  authorization material is neither published nor registered on the physical test aircraft.
- Removed the account/license/credential category from the active repository publication rule while
  retaining privacy, vendor-material, and bricking boundaries.

## 0.4.16 - 2026-08-30

### Changed

- Rewrote the project and next-agent prompts around the single objective of a controllable Mini 5
  Pro Remote ID switch with readback, restoration, and independent RF A-B-A evidence.
- Removed repetitive defensive language and consolidated the remaining boundaries into operational
  rules: authorized lab scope, evidence closure, privacy/publication, and no unrecoverable
  startup/TEE/eFuse state changes.

## 0.4.15 - 2026-08-30

### Changed

- Refocused the project objective from a general RID test control/panel to a controllable, readable,
  restorable Mini 5 Pro Remote ID switch.
- Reclassified RID/FlySafe state-changing work as goal-directed but gated by route admission,
  same-item/policy baseline, readback, restoration, and independent RF A-B-A rather than being
  categorically forbidden.

### Added

- Registered the pinned public RC 2 TEE/eFuse tamper bricking report as C-212 and cited it as the
  reason TEE/eFuse/startup-trust-chain, bootloader, flashing, and uncontrolled DJI Fly update paths
  remain prohibited.

## 0.4.14 - 2026-08-30

### Added

- Added a fixed C-207 observation form for the standardized Remote ID motor-off → motor-on →
  motor-off A-B-A record, including exact bearer class, message presence, frame count, and motor
  transition timestamps.
- Linked the form from the RID experiment matrix, current blocker, and handoff instructions.
- Added a read-only FindUAS local-history transcript tool that outputs privacy-reduced counts,
  timestamps, RID-standard labels, field presence, and an optional opaque ID digest prefix. It does
  not access devices and excludes full identifiers, coordinates, receiver IDs, raw frames, and
  credentials.

### Boundary

- The form is a recording procedure only. It does not perform a write, admit a route, or establish
  RF behavior. It excludes full identifiers, coordinates, raw frames, captures, account/license
  material, and DJI-private DroneID telemetry.

## 0.4.13 - 2026-08-30

### Added

- Published the source-only normal-path carrier and uncommitted PackageInstaller staging projects,
  with A-035/A-036 artifact identities and explicit emulator-negative status. Generated APK/SO/DEX,
  vendor bytes, raw logs and identifiers remain excluded.
- Registered C-208--C-211 for installed-path delimiter truncation, the trace-label negative plus
  identical-byte `apk_data_file` positive control, the `apk_tmp_file` search denial/session abandon,
  and the remaining exact RC 2 caller/target policy-intersection hypothesis.
- Added `NEXT_AGENT_HANDOFF_PROMPT.md`, an outcome-first takeover prompt pointing to the authoritative
  claims, current RID-control candidates, retired routes, evidence standard and hard device boundary.

### Corrected

- Removed the staging README's incorrect query-success statement. The emulator created and streamed
  the session, but target search was denied before agent load and no callback occurred.
- Corrected the claim that the staging APK is DEX-free: it has no application classes or components,
  but AGP emits one 600-byte synthetic `R`-class DEX despite `android:hasCode="false"`.
- Reclassified both loader APKs as negative regression fixtures rather than RC 2 candidates.

## 0.4.12 - 2026-08-29

### Added

- Recorded the operator's field confirmation that the Mini 5 Pro broadcasts plaintext standardized
  Remote ID with a readable Basic ID when motors spin (C-207); the switch work now targets the
  standard ASTM F3411 / EN 4709 bearer, and the DJI-private DroneID family is parked.

### Boundary

- No official DJI RID feature or legal text was added. The confirmation is an operator field
  observation; the exact Basic ID value, BLE vs Wi-Fi bearer, field set, and written motor on/off
  A-B-A timing remain unpinned, and no toggle or write was performed.

## 0.4.11 - 2026-08-29

### Added

- Corrected the DroneID vs standardized Remote ID distinction: the DragonSDR encrypted-O4 boundary
  is limited to DJI's private OcuSync DroneID protocol, while standardized Broadcast Remote ID
  (ASTM F3411 / EN 4709 BLE/Wi-Fi) is plaintext and readable by a standard receiver with no
  DJI-licensed decoder (C-202 reworded, C-203 added).
- Recorded the official DJI Cloud API FlySafe device methods `unlock_license_switch` and
  `unlock_license_list` with type 6 "RID unlocking" and `rid_unlock.level` 1=EU / 2=China (C-204).
- Recorded the official MSDK 5.8.0 `RidUnlockType` (EUROPEAN/CHINA),
  `FlyZoneLicenseInfo.getRidUnlockType()`, and `setFlyZoneLicensesEnabled` enable/disable setter
  (C-205).
- Recorded the OpenDroneID receiver-android README plaintext ASTM F3411 / prEN 4709-002 receiver
  reference (C-206).

### Boundary

- No official DJI RID feature, legal text, or regulation text was added; new claims are pinned
  official API/MSDK documentation and standards-community receiver references only.
- The FlySafe type-6 enable/disable surface is now pinned at the Cloud API and MSDK 5.8 levels, but
  Mini 5 Pro entitlement, a genuine type-6 license, and a motor-on standardized-RID RF effect remain
  unproved. No live write or RF measurement was performed.

## 0.4.10 - 2026-08-29

### Added

- Recorded independent community corroboration of the legacy FLYC `0x03/0xDA` (cmd 218)
  `fc_monitor` privacy-mask family (purpose/DroneID-name/mask get-set subcommands `01`–`06`,
  sender PC 10/1 to receiver FLYC 3/6, DroneID at mask bit 3) from pinned `CIAJeepDoors.py` and
  `comm_mkdupc.py` (C-200).
- Recorded the community author's reliability boundary for that legacy surface: it only sends
  NULL/`fakeSN`, some firmware still randomly sends valid location packets, later DJI Fly/iOS
  reset the bits, and it is not reliable (C-201).
- Recorded the public DragonSDR DroneID receiver O4 capability boundary, scoped to DJI's private
  OcuSync DroneID protocol: O4 (Mini 5) private DroneID is encrypted and receiver-alone yields
  session hash plus frequency/RSSI, with full telemetry requiring a licensed DragonScope config and
  private DroneID broadcast only while motors spin (C-202).
- Recorded the DroneID vs standardized Remote ID distinction: pinned RUB-SysSec DroneSecurity
  NDSS 2023 README FAQ states DJI's Drone-ID is not the same as standardized Bluetooth/Wi-Fi
  Remote ID (EN 4709 EU / ASTM F3411 US) and the standard bearer is readable by a plain smartphone
  app (C-203).

### Boundary

- No official DJI RID feature or legal text was added; the new claims are community prior-art
  documentation for the legacy OcuSync/AeroScope mask surface and for independent-receiver scope.
- The encrypted-O4 boundary is limited to DJI's private OcuSync DroneID telemetry. Standardized
  Broadcast Remote ID (ASTM F3411 / EN 4709 BLE/Wi-Fi) is plaintext and readable by a standard
  Remote ID receiver without any DJI-licensed decoder.
- No live write or RF measurement was performed; all new evidence is pinned public text
  (`CORROBORATED`/`NEGATIVE`) and does not establish a Mini 5 Pro transmitter-off switch.

## 0.4.9 - 2026-08-29

### Added

- Wired `RidEuC0Parameter` into `MainActivity` as a separate EU C0 surface for
  `EU_CE_enable_c0_rid_0` (`0xF80992FE`): read-only F7/F8 probe plus off/on/restore
  buttons with independent metadata/baseline/route state. Write buttons stay disabled
  until an F7/F8 baseline and live route pass, every F9 re-probes F7/F8, readback is
  sampled twice, and any unconfirmed state restores the baseline.
- Extended the `DjiProtocolClient` parameter allow-list to admit the EU C0 F7/F8/F9
  tuples separately from `rid_ctrl_enable_0`, plus a new allow-list test.

### Fixed

- Corrected the panel positive-control name `HEIGHT_LIMIT_NAME` to
  `g_config.flying_limit.max_height_0`, matching hash `0x0371238A`.

### Boundary

- Pinned public FreeFCC prior art (C-198) documents a C0 class runtime flag that
  overrides flight-controller parameters on every connection, so a single F8 readback
  is not a reconnect-persistence or reliability result. All panel wiring is offline
  source plus synthetic tests (C-199); no live EU C0 read/write is claimed and the
  Binder generic attach route has not been shown to carry the EU C0 parameter.

## 0.4.8 - 2026-08-29

### Added

- Added `host-tools/rid-switch-tool/rid_eu_by_hash_switch_control.py`, a bounded
  by-hash A-B-A switch for the single parameter `EU_CE_enable_c0_rid_0`
  (`0xF80992FE`). It keeps the same positive control, baseline, single F9 forward
  write, readback, immediate restore and fail-closed safety mode as
  `rid_switch_control.py`, and adds an optional `--rid-ctrl-bridge` read-only probe
  of `rid_ctrl_enable_0` in the same session.
- Added `host-tools/rid-switch-tool/test_rid_eu_by_hash_switch_control.py` (10 offline
  tests) pinning the single target, the name/hash identity, the positive control, the
  transport allow-list and the fail-closed command gate.
- Added `apps/rc2-rid-admin/.../RidEuC0Parameter.java`, a strict by-hash F7/F8/F9
  codec for `EU_CE_enable_c0_rid_0` that recomputes the FLYC parameter-name hash and
  fails closed on name/hash mismatch, mirroring the host-tool semantics.
- Added `apps/rc2-rid-admin/.../RidEuC0ParameterTest.java` (12 tests) pinning the
  name/hash identity, reference hash vectors, F7/F8 layouts, F9 payload and Boolean
  gate.

### Boundary

- All of this is `STATIC` offline source and synthetic tests. No live by-hash
  read/write is claimed, the bridge steps are read-only, and none of it proves Remote
  ID RF behaviour. `EU_CE_enable_c0_rid_0` is an EU C0 policy candidate, not a global
  RID master switch.

## 0.4.7 - 2026-08-29

### Added

- Added `libraries/protocol-probes/dji_flyc_parameter_hash.py`, an independent,
  source-only re-implementation of the public DJI flight-controller parameter-name
  hash (`GBK` encode, `hash = ((hash << 8) + byte) % 0xFFFFFFFB`) with pinned ASCII
  regression vectors covering the current RID policy parameters, the wa150 EU C0 rows,
  and the known-good positive controls. It performs no I/O.
- Added the by-hash/by-index bridge: `rid_param_index_readonly.py` reports the computed
  `_0`-form hash for each wa150 RID row, and `rid_switch_control.py` (`--index-bridge`)
  and `rid_index_switch_control.py` (`--hash-bridge`) each add a read-only F7/F8 probe of
  `EU_CE_enable_c0_rid_0` (`0xF80992FE`) to anchor the by-index row to its by-hash name.

### Fixed

- Corrected the by-hash positive-control name: `0x0371238A` is
  `g_config.flying_limit.max_height_0` (not `g_config.flying_limit.max_height`), and the
  read probe's three labels were corrected to `g_config.flying_limit.max_height_0`,
  `g_config.flying_limit.max_radius_0`, and
  `g_config.advanced_function.radius_limit_enabled_0`. The corrected names match the hash
  now that the algorithm is pinned.

### Boundary

- All of this is `STATIC` offline source and synthetic tests; no live by-hash or by-index
  read/write result is claimed, and none of it proves Remote ID RF behaviour. The bridge is
  read-only metadata only.

## 0.4.6 - 2026-08-29

### Added

- Added `host-tools/rid-switch-tool/rid_index_switch_control.py`, a bounded by-index
  A-B-A tool for the single wa150 table parameter `EU_CE_enable_c0_rid` (index 1306).
  It verifies the table CRC/count (`0xE0`) and the on-board name (`0xE1`) in the same
  session, reads a strict baseline (`0xE2`), performs one forward `0xE3` write, reads
  back, and immediately restores the captured baseline with a final readback. It has no
  generic payload/route/command/parameter interface and never starts motors.
- Added `host-tools/rid-switch-tool/test_rid_index_switch_control.py`, offline synthetic
  tests pinning the fixed target index/name, the wa150 table identity constants, the
  transport allow-list, and the fail-closed command gate.

### Boundary

- The tool is `STATIC` (offline source and synthetic tests) and `NOT ADMITTED` as a
  device write. `EU_CE_enable_c0_rid` is an EU C0 policy candidate from the public wa150
  table, not a global RID master switch, and a green `0xE2` readback does not prove
  Remote ID RF behaviour. No live by-index read or write has been performed.

## 0.4.5 - 2026-08-29

### Added

- Added `libraries/protocol-probes/rid_param_index_protocol.py`, an offline by-index FLYC codec for
  the `0xE0` (table attributes), `0xE1` (get_info), `0xE2` (read), and `0xE3` (write) parameter
  commands, with strict name/index/width validation and a gated write encoder.
- Added `host-tools/rid-switch-tool/rid_param_index_readonly.py`, a read-only USB DUML probe that
  verifies the wa150 parameter-table identity through `0xE0` and re-checks each candidate RID
  index's on-board name through `0xE1` before reading `0xE2`. It never reaches `0xE3`.
- Recorded the public `lmdegreeds/djiparam` by-index command family and wa150 parameter table as a
  pinned source; its EU C0 RID rows are policy candidates, not a global master switch.

### Boundary

- The by-index command family is a third, independent parameter-access path alongside by-hash
  `F7/F8/F9`. It is `STATIC` offline source only: no live by-index read or write is claimed, and a
  green `0xE2` readback still does not prove Remote ID RF behaviour.


### Added

- Added `host-tools/rid-switch-tool`, an operator-run USB DUML control for the single RID candidate
  parameter `rid_ctrl_enable_0` (`0x3CBD864F`) over the verified read-only FC path. It gates every
  write behind a same-session maximum-height positive control and a strict F7/F8 Boolean baseline,
  performs one forward F9 write, reads the value back, and immediately restores the captured
  baseline with a final F8 readback. It has no generic payload/route/command/parameter interface
  and never starts motors.
- Extended `rid_param_protocol.py` with a gated F9 request encoder (`encrypt_request_frame` with an
  explicit write allow-list), an F9 write-body builder, and an F9 write-ACK parser. Read-only paths
  remain unchanged and still refuse write commands by default.
- Added synthetic tests for the new codec and the switch tool gate/width helper.

### Boundary

- The tool is `STATIC` (offline source and synthetic tests) and `NOT ADMITTED` as a device write.
  A green F8 readback records only an onboard parameter value; it does not prove Remote ID RF
  behaviour. Live motor-on RF observation remains operator-initiated with an independent receiver.

## 0.4.3 - 2026-08-29

### Documentation

- Added `CODEX_PROJECT_PROMPT.md`, a concise reusable task prompt that accurately frames the work as
  authorized interoperability and Remote ID compliance testing on user-owned lab devices.
- The prompt states the current stable-control objective, allowed autonomous local work, reversible
  live-device boundary, boot/TEE/credential/license/privacy prohibitions, GitHub update rule and
  exact query/readback/restore/external-RF completion standard once rather than repeating ambiguous
  “bypass” language.
- Linked the prompt from the repository README and root `AGENTS.md`; detailed evidence rules remain
  in `AGENTS.md` and are not weakened by the shorter task prompt.

## 0.4.2 - 2026-08-29

### Added

- Registered C-188--C-191 for the disposable-emulator ART TI experiment: the standard JVMTI 1.2
  late-load negative, clean ART TI `0x70010200` owner reachability, one exact private FC-license
  query callback, and the independent success-side group/type-6 parser.
- Added source-only `experiments/jvmti/jvmti_flysafe_inprocess_query`, including the AArch64 agent,
  in-memory callback DEX source, exact compile-time callback stub, minimal protobuf parser, five
  synthetic host cases and direct build scripts. Generated DEX/SO output is ignored and excluded.
- The parser reconciles declared/observed record counts, identifies a unique MSDK-compatible
  field-7 RID candidate, keeps its existing ID in memory only, and exposes counts, level and status
  Booleans.

### Observed boundary

- On exact DJI Fly `1.21.10` in a disposable AArch64 Android 11 emulator, standard JVMTI 1.2 ended
  in a native process crash before the canary logged. ART TI attached cleanly, found exactly one
  loaded unlock/event owner pair, obtained a nonzero current device ID, dispatched the private
  query once and received callback `417`; the PID before and after was identical.
- No aircraft was connected, so no success payload, inventory or type-6 item was observed. The
  result does not establish RC 2 loading, entitlement, setter behavior, restore or RF effect.

### Verification

- Five synthetic parser cases passed. The helper DEX and Android 30/AArch64 agent built with JDK 21,
  build-tools 35 and NDK 27.2.12479018.
- Vendor APK/DEX/process-memory bytes, raw logs, license IDs and generated binaries remain excluded.

## 0.4.1 - 2026-08-29

### Added

- Registered C-183--C-187 and A-034 for the exact DJI Fly `1.21.10` disposable-emulator runtime
  study. The non-exported official license-manager Activity rendered, authorized read-only process
  memory recovery produced a local current-Java analysis set, and all vendor bytes remain excluded.
- Closed the exact current same-process aircraft-license owner through the component, Activity,
  view model, `FlightRestrictImpl`, `JNIFSUnlockManager` and native current-device query.
- Closed the exact generic existing-license action through the native current-device setter and
  Boolean-array row refresh. The action was not executed and is not represented as a proven RID
  switch.
- Added `host-tools/runtime-dex-scan`, an independently written bounded DEX-image scanner with
  synthetic tests. It operates only on an already acquired authorized memory file and contains no
  process-dumping, injection, device-control or vendor code.

### Corrected

- Replaced the stale statement that current protected Java/type-6 rendering was unrecovered. Exact
  current Java defines only license types 0--4 plus unknown and protobuf fields 1--5; unknown records
  fall through to a tolerant polygon model. DJI Fly `1.21.10` therefore cannot be treated as a
  semantic type-6 `RID_UNLOCK` reader even though its official query/action transport exists.
- Recorded direct Frida attach as a narrow emulator negative: it found candidates but destroyed the
  script/application before producing output. This injection path is not to be repeated on RC 2.

### Publication boundary

- The exact DJI Fly APK, runtime mapping, extracted DEX, decompiled source, raw process logs, local
  paths and any account/device data remain excluded. Public records contain only identities,
  independent source, high-level control flow, testable claims and explicit evidence boundaries.

### Verification

- The published RC 2 RID Admin source completed clean JVM tests (`132`, zero failures/errors), lint
  and debug assembly under Gradle `8.10.2` with JDK 21.
- Published host source compiled successfully; protocol, quiescence, firmware-target and runtime-DEX
  suites completed `123` synthetic/device-free tests with zero failures.
- Markdown-link, claims/artifacts CSV, sensitive-pattern and whitespace validation passed before
  publication.

## 0.4.0 - 2026-08-29

### Added

- Registered C-180--C-182 and A-033: exact DJI Fly official license-manager surface, the
  independently written `0.8.0-flysafe-diagnostic-export` source/artifact audit, and removable-SD
  MTP staging/readback.
- Added a file-manager-readable privacy-reduced report at
  `Download/FindUAS/FindUAS_RID_A033_latest.txt` using zero-permission MediaStore. The fixed direct
  button remains `0x11/0x11` only and never emits `0x11/0x12`.
- Added the one-time assisted sequence for manually inspecting DJI Fly's same-process aircraft
  license list before one A-033 run. The first pass contains no toggle, motor action, or RF test.

### Verification

- A-033 is `204,449` bytes with SHA-256
  `8ce8e0c13ecfcf69517a64e809a475b79bbc750124225744b6b35f281d3d7177`; 132 tests passed, lint
  reported zero errors and 15 warnings, two clean builds were byte-identical, and signature,
  alignment, zero-permission, native/network/socket/shell/external-process checks passed.
- MTP fresh readback matched the registered artifact. The APK is not committed and has not been
  installed or run; source and tests are published under `apps/rc2-rid-admin`.

## 0.3.9 - 2026-08-29

### Added

- Published the independently written RC 2 / Mini 5 Pro research source archive under `apps/`,
  `libraries/`, `host-tools/`, and `experiments/`, with project-local status, build, test, and
  evidence-boundary documentation.
- Added the current FindUAS RC 2 RID administration source, the hidden-settings launcher, and the
  v0.10 admission probe safe source set. Exact historical APKs remain identity records rather than
  redistributed binaries, and later source is not represented as a byte-for-byte reconstruction of
  every historical APK.
- Added host-testable RID codecs, inventory parsing, quiescence and bounded-control models; USB/ADB,
  firmware-acquisition, IMaH and ELF analysis helpers; Ghidra scripts; source-only system-UID bridge
  probes; and the preserved JVMTI experiment sequence.
- Preserved experimental outcomes in source: V2.2 is `RETRACTED`, V2.3 remains `NOT ADMITTED`, the
  ADB userspace-copy patch has not been executed, and build/test success is never promoted into a
  live Remote ID control result.
- Extended CI with 121 stable, device-free host tests for the protocol probes, quiescence model and
  firmware metadata/target-lock helpers, plus compilation of all published Python source.

### Publication boundary

- No DJI APK, firmware, partition, shared library, decompiled vendor source, patched vendor binary,
  raw private capture, device/account identifier, signing/ADB key, or generated APK/JAR/SO/DEX is
  published. A small third-party MIT transport helper and AOSP JVMTI header retain their original
  notices; GPL tooling is referenced externally rather than vendored.

## 0.3.8 - 2026-08-29

### Added

- Registered C-174--C-179 and A-029--A-032 for the exact `07.00.0100` ADB chain: verified signed
  system/`0205` provenance, exact APEX `adbd`, exact packaged `dpad_fuli`, the narrow userspace-copy
  gate patch, MTP staging/readback, and the still-unexecuted live session.
- Recorded the exact APEX path distinction: runtime `/apex/com.android.adbd/bin/adbd`, extracted
  backing `/system/apex/com.android.adbd/bin/adbd`, and no target `/system/bin/adbd` entry.
- Promoted the production/debug-count pre-AUTH return from adjacent-only inference to exact
  target-package `STATIC`; retracted C-032/H-14 only as the obsolete adjacent-parity inference while
  retaining live mounted-hash/property/branch-log unknowns.
- Registered A-032 at `1,497,232` bytes and SHA-256
  `3fceaa1724a77a153c17f725a2e3f3001b0543e31e0830aca0c77d785df9225f`. The patch changes only
  `cset w21, lt` to `mov w21, wzr` at the exact gate-value instruction and preserves the normal
  TLS/auth target.
- Recorded removable-SD `Download/RC2_ADBD_CNXN.bin` staging: a fresh MTP listing matched size and a
  full readback SHA matched. No internal copy, chmod, execution, daemon stop, new ADB response, or
  shell occurred.
- Added the operator handoff: first collect live UID/SELinux/gate/USB/init and exact stock/staged/Fuli
  hashes. Choose an internal executable path only from that output, then generate the second one-shot
  command segment in the same assisted session.

### Provenance

- At the time of this release, the outer aggregate came from a third-party archive, not DJI; the
  evidence anchor is the separately
  verified signed config/`0205` PRAK/checksum chain. No firmware, image, APK, original/patched vendor
  binary, raw disassembly, MTP identifier, device serial, ADB key, or host path is committed.

## 0.3.7 - 2026-08-29

### Added

- Registered A-027 and C-166--C-169 for the active read-only FlySafe inventory candidate:
  `0.7.0-flysafe-direct-readonly` / code 10, fixed `02:04 -> 12:04`, `11/11`, V3/V4 selectors,
  no route scan, and no application-level retry.
- Recorded exact final identity and audit: 196,569 bytes, SHA-256
  `aa4bcd9c8aa96870cfbae1ba326d366cb8854a50ef4aff223f7bce4290ddcd81`; 127 tests with
  zero failures/errors/skips, lint 0 errors/15 warnings, two byte-identical clean builds, v2
  signature, zipalign, zero permissions, and no native/network/socket/shell/external-process path.
- Recorded MTP staging as `Download/FindUAS_A027_RO.apk`; a fresh listing matched the registered size
  and readback SHA-256 matched.
- Recorded the first installed A-027 run: the active button returned
  `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS` at `ProtocolException`, and displayed
  `11/12 request count=0`. The UI did not expose the exception message or lower-level failure stage.
- Added the public-evidence boundary: pinned `fpv_live`, `dji-firmware-tools`, DJI Cloud API, and MSDK
  support generic transport/FlySafe context but do not independently confirm the product-139/RC331
  fixed route; A-027/A-028's noncanonical live results did not confirm it.
- Registered A-028 and C-170--C-173: `0.7.1-flysafe-direct-diagnostic` / code 11 changes only safe UI
  diagnosis while preserving command, route, selectors, and write boundary. Exact identity is
  197,061 bytes, SHA-256
  `d7c32636e19d1bce1b8b8994206355f42d0278b2f15048b14a948a8bbda1d540`; 127 tests,
  lint 0 errors/15 warnings, two byte-identical clean builds, v2 signature, zipalign, zero
  permissions, and no packaged native library passed.
- Recorded A-028 MTP staging as `Download/FindUAS_A028_DIAG.apk`; fresh listing size and readback SHA
  matched.
- Recorded the installed A-028 run: `DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS`,
  `ProtocolException`, detail `group transport callback failed`, `11/12 count=0`. The fixed group
  selector therefore did not reach a successful transport callback; protobuf/pages/terminator were
  not reached. The next discriminator is Reply failure/ecode/callback detail, not another identical
  black-box run.

### Provenance

- At the time of this release, no APK, implementation source, result image, device identifier, raw
  reply, license ID, or account material was committed. Source was published later in 0.3.9; sealed
  APK bytes and private/live material remain excluded. Failure remains ambiguous rather than
  unsupported/no-license, and canonical inventory would not establish RF RID.

## 0.3.6 - 2026-08-29

### Added

- Added C-165 from the first live A-026 gate run. The instructed 60,003 ms window ended
  `GATE_UNOBSERVED`: `03/09` and `03/42` were both unseen/unusable, every reported callback-class
  count was zero, and fail-closed admission kept `11/11` request count at zero.
- Updated A-026 device-use state to `installed-and-run-gate-unobserved-zero-query` and propagated the
  result through the evidence/artifact registers, timeline, RID surfaces, negative results,
  hypotheses, blockers, handoff, control matrix, README, and agent handoff rules.

### Provenance

- This is a narrow third-party Binder passive-listener negative. It is not evidence that the
  aircraft lacks RID support, a type-6 entitlement is absent, inventory is empty, RID/RF was off,
  or the official in-process observer cannot receive the pushes. No raw frame, identifier, license
  material, write, motor action, or independent RF observation is recorded.

## 0.3.5 - 2026-08-29

### Added

- Registered A-026 `0.6.0-flysafe-gated` and C-160/C-161: tx2 passive `03/09 + 03/42` gate,
  complete-route consistency, fail-closed same-process permit, fixed tx4 V3/V4 `11/11`, strict
  group/page 0..127 traversal, and an initial-plus-two-retry callback window.
- Recorded exact A-026 identity: code 9, 135,525 bytes, SHA-256
  `3c2ae42ac9f19a9e3dfe669ed6357bb8d2f1c38568af6a0f8d8b8f677fcbfec4`; two clean
  test/lint/assemble runs were byte-identical, 63/63 tests passed, lint was 0 errors/13 warnings,
  v2 signature/zipalign passed, and the APK has zero permissions and no native/network/socket/shell
  path.
- Added C-162 for MTP delivery as `FindUAS_A026_GATE.apk`: same-session readback SHA matched and a
  new session confirmed one unique short name with the registered size.
- Added C-163: the operator explicitly reported A-025 installation complete. This does not establish
  launch, execution, Binder requests, inventory, state change, or RF result.
- Added C-164: the operator explicitly reported A-026 installation complete. This establishes only
  installation; launch, execution, passive callbacks, permit, Binder requests/results, inventory,
  state change, and RF remain unknown.
- Updated C-159 from an unimplemented direction to the inference rationale now realized offline by
  A-026; runtime passive-push visibility remains unknown.
- Preserved the Admin boundary: external DJI Developer Assistant is outside A-026's internal
  allow-list, and gated F9/EID/OPID write controls remain, so the APK is not globally read-only.

### Provenance

- No object/storage/USB/device serial, local absolute path, account material, raw payload, or license
  material is recorded. A-026 implementation/audit is `STATIC`; delivery and user-reported
  installation are `OBSERVED`; execution and all live behavior remain `UNKNOWN`.

## 0.3.4 - 2026-08-29

### Added

- Added C-154 and updated A-025 disposition: the exact APK was written through RC 2 MTP to
  removable-SD `Download` as `FindUAS_A025_RID.apk`; same-session readback SHA-256 matched, and an
  unintended long-name duplicate was removed. Installation and execution remain unconfirmed.
- Added C-155/C-156 for the current official type-6 chain: FlySafe website background qualification,
  exact `Rid` product capability, product/FC-SN account record, reviewed application, nonempty-login
  signed group download, version/target-specific onboard blob selection, FC import, inventory, and
  existing-ID enable/disable.
- Recorded the visible-surface boundary: DJI Fly has ordinary Remote-ID registration/status and
  generic Unlock-a-Zone license lists, but no type-6-specific application page was recovered. Mini 5
  Pro capability/approval remains unknown, country/locale changes do not grant entitlement, and
  public MSDK support omits the product.
- Added C-157 for exact passive FlySafe admission: `03/09` Area Info populates unlock version and
  `03/42` WhiteList Info populates support; default `255/false`, missed pushes, and absent replay are
  unknown rather than unsupported.
- Added C-158 for A-025's false-negative boundary. Its fixed V3/V4 query lacks a current-connection
  passive gate, so failure or noncanonical completion cannot establish unsupported/no-license/empty
  inventory; only a canonical count-consistent completion describes returned inventory.
- Added C-159/H-28 for the A-026 direction: bounded passive observation first, one existing V3/V4
  query only after usable support=true and version 1/2, and fail-closed result classes otherwise.
  No final A-026 APK, version/hash, audit, installation, or live result exists.
- Updated the evidence/artifact registers, timeline, control surfaces, hypotheses, blockers,
  handoff, source index, README, and AGENTS correction. At this release the repository was
  documentation-only; source was added later in 0.3.9. Binaries and account/license material remain
  excluded.

### Provenance

- No local absolute path, storage/USB/device serial, account token/Cookie/HAR/SN, signed license,
  authenticated request, FC import, setter, or RF result is recorded.
- Public web and current-app evidence is static; A-025 staging is observed; A-025 execution,
  Mini 5 Pro entitlement, passive-gate visibility, and all A-026 behavior remain unobserved.

## 0.3.3 - 2026-08-29

### Added

- Added C-142/C-143 from the installed A-023 read-only Binder probe: service and callback ABI were
  reached, but target F7 ended in `ECode 1` after about 3.1 seconds; adjacent RC331 maps that class
  to retry exhaustion. No F8/F9 or RF effect occurred.
- Registered replacement artifact A-024 `0.4.1-research`, including serialized operation gates,
  per-route maximum-height F7/F8 positive control, validated Boolean metadata/readback/rollback,
  and one full-window passive `0x11/0x1C` state timeline.
- Added C-144 for the A-024 final-artifact audit: 25 unit tests, lint with zero errors, two
  byte-identical clean builds, no permissions/native libraries, v2 signature, and alignment checks.
- Added C-145 from the installed A-024 live result: legacy `0A:05 -> 03:00` and modern
  `02:04 -> 12:04` Binder routes both failed the known-height F7 positive control with `ECode 1` and
  no data after about 3.1 seconds. Target F7/F8/F9 were correctly not sent.
- Added C-146 from the motor-on experiment: the accepted 30-second Binder `0x11/0x1C` listener
  delivered zero callbacks while an independent detector confirmed real RID RF, closing that
  listener as a false-negative truth/readback path.
- Added C-147--C-149 for the official minimum status parser, the type-6 region-matched
  `NO_BROADCAST` design semantics, and the exact current product-139 inventory/set-enable wire.
- Registered A-025 `0.5.0-flysafe-readonly` and C-150/C-151: the fixed, bounded, privacy-reduced
  system-Binder `11/11` inventory lane and its exact final-artifact audit. The FlySafe lane admits no
  `11/12`, and the false-negative `11/1C` UI button is removed.
- Recorded the exact A-025 boundary: 42 passing tests, lint with zero errors, byte-identical clean
  rebuild, zero permissions, no packaged native library or inspected network/socket/shell path, and
  no copy to RC 2 removable storage, install, or execution. The version suffix is lane-specific;
  separately gated older F7/F9, EID, and OPID controls remain.
- Added C-152 to separate the exact current DJI Fly 1.21.10 fields-1--5 `LicenseData` parser from the
  independent MSDK 5.18 field-7 `LicenseDataRID` schema used by A-025's compatibility decoder.
- Added C-153 for the bounded aircraft-consumer negative: current Fly `11/12` carries only license ID
  and action, with no recovered edge to WA150 `0802`, motor/armed state, or BLE/Wi-Fi enable. This
  does not cover encrypted aircraft firmware or establish a patch offset.
- Changed the active implementation path to a bounded read-only modern `0x11/0x11` inventory query;
  `0x11/0x12` remains absent and prohibited until a genuine type-6 baseline exists.
- Updated the blocker, handoff, experiment matrix, artifact state, hypothesis, timeline, README, and
  AGENTS contract to close generic parameter attach variants and promote passive status,
  diagnostics, type-6 inventory, and WA150 `0802/E3` ownership as the active dependency chain.

### Provenance

- The two user-supplied result photographs were used only to transcribe redacted protocol outcomes;
  PID, UID, device identity, and image files are not committed.
- At the time of this release, A-023/A-024/A-025 APKs and implementation source were outside the
  documentation-only repository. Later successor source was published in 0.3.9; the sealed APK
  bytes and exact historical snapshots remain excluded.
- No target F7, F8, F9, reset, account action, license action, firmware write, or RF claim is made.

## 0.3.2 - 2026-08-28

### Added

- Recovered the current same-family SKYROVER `1.2.0` independent Boolean `RIDCtrlEnable`, its
  GET/SET/Listen flags, connection-time capability probe, and separation from France `EIDSwitch`.
- Closed the native mapping `RIDCtrlEnable -> rid_ctrl_enable_0`, parameter hash `0x3CBD864F`,
  FLYC `03/F7-F9` family, and static modern `0x82 -> 0x92` route as C-136 and C-137.
- Added C-138/H-27/B-20 for the decisive Mini 5 Pro F7/F8 admission test and subsequent reversible
  F9/readback/restore plus motor-on independent RF A-B-A.
- Added C-139/C-140: a full same-family RID configuration inventory found no second closed global
  Boolean, and a fixed public search found no independent Mini 5 Pro implementation. Modern
  FreeFCC transport/framing is retained only as corroboration for a different hash/feature.
- Registered the exact official input as A-022 and the clean-room fixed RC 2 Binder client
  `0.3.0-research` as A-023. The client APK was copied to RC 2 removable storage; install/run/live
  reply remain pending.
- Added C-141 from a live read-only probe: both validated direct routes returned F7 status `0x03`
  for `0x3CBD864F` while same-session known-parameter controls succeeded. Direct USB modern routing
  failed its own height control, so only the RC 2 Binder modern route remains open; no F9 was sent.
- Updated the control matrix, handoff, source index, timeline, README, AGENTS contract, claim CSV,
  and artifact CSV so another researcher can continue at the single live F7/F8 step.

### Provenance

- SKYROVER proprietary APK, shared libraries, DEX, and decompilation output remain excluded.
- The MIT implementation is independently written from protocol facts; no vendor or AGPL source was
  copied.
- No live F7/F8/F9 reply or RF effect is claimed by this documentation update.

## 0.3.1 - 2026-08-28

### Added

- Recovered Drone-Hacks' complete 28-entry ADSB numerical Debug dictionary, including
  `RID_INFO=0x11/0x1A` and `EID_INFO=0x11/0x35`, as claims C-110 and C-111.
- Cross-checked the dictionary against exact DJI Fly `1.21.10` and recorded the mixed agreement and
  semantic collisions that prevent using it as a current Mini 5 Pro request schema.
- Updated README, AGENTS, handoff, blocker, timeline, and negative-result guidance so future work
  uses these IDs only for passive traffic classification or exact static xrefs until a current
  handler and payload are recovered.
- Closed the current product-139 RID state owner through `RidImportModule`, including the exact
  seven-byte status mapping and the absence of a status GET/SET/action surface (C-115/C-116).
- Closed `KeyCloudControlData` as value-routed SET-only `0x00/0xDD`; ACK/cache is the request rather
  than applied RID state, and no active read-only RID query was recovered (C-117/C-118).
- Added independent public identity evidence for both WA150 `0802` versions, the bounded
  network-service ownership inference, and the still-negative public plaintext/key/recovery search
  (C-112--C-114).
- Added a focused legacy DroneID report: FlyC `0x03/0xDA` subcommands `0x05`/`0x06` are the
  high-confidence match for the NDSS multi-field mask, whose reported RF effect retained packets
  and changed selected values to `fake`; no WA150/modern Broadcast RID transfer is established
  (C-119--C-122).
- Expanded the target into a RID experiment-control matrix with explicit live-read, passive-owner,
  static-locked, managed, opaque, legacy, and synthetic-source implementation levels.
- Closed exact current identity/data surfaces for EASA OPID, Japan DIPS, China UOM identifier,
  app-location upload, and compliance serial; excluded the LTE phone path from RID (C-123--C-128).
- Recorded a separate synthetic OpenDroneID source as a controlled-lab hypothesis, not as a current
  Mac or DJI-device capability (C-129).
- Closed the current China UOM identifier receiver/timeout/retry and reply parser, corrected its
  GET-tail bytes from assumed zeroes to undefined vendor initialization, and separated conditional
  `UOMV1` real-name status/sync from broadcast control (C-130--C-132).

### Safety and provenance

- The Drone-Hacks executables were not run, no guessed DUML request was sent, and no device state
  changed. Vendor binaries and disassembly output remain excluded.
- No active RID query or cloud-control write was sent. Public image coordinates and unrelated
  metadata were excluded; only product/software version and whole-file hashes were retained.
- No legacy `Detection` command was sent and no executable sender was added to the repository.
- No OPID, DIPS, UOM, location, telephone, compliance identity, cloud policy, or license data was
  read or written. Secret credentials and real identity fixtures remain excluded.
- No China UOM GET or Sync action was sent; the new result is exact static analysis only.

## 0.3.0 - 2026-08-28

### Added

- Added a bounded static analysis of the official Drone-Hacks `2.0.29` Windows distribution,
  including exact provenance, Authenticode identity, Rust/Tauri command surface, server-driven job
  architecture, parameter editor, one-time FCC path, and firmware-resident CFC precedent.
- Recorded the current public Mini 5 Pro boundary: `wa150` is recognized, but no software platform,
  compatible license, product, CFC image, or explicit RID control was found; separate FCC ModBox
  compatibility is not software/RID support.
- Added Drone-Hacks artifacts A-019 through A-021, claims C-093 through C-101, a fixed-scope RID
  negative result, one architecture hypothesis, one blocker, source links, and handoff guidance.
- Closed NLD's native FCC envelope, entitlement verification, offline-cache framing, decrypted
  command schema, and DUML write loop as claims C-102 through C-105 while retaining the absent-real-
  payload and absent-RF-evidence boundary.
- Closed DJI Fly's current China OID report-enable Boolean as an app-side network-submission gate,
  not an aircraft RF switch; added the distinct cloud-namespace boundary and current exact global-
  setter negative as C-106 through C-109.

### Safety and provenance

- The user-supplied MSI matched the MSI in the official release ZIP and its signature validated.
- The MSI and embedded PEs were never installed or executed. No account, authenticated endpoint,
  license, private job payload, device identifier, or device read/write operation was used.
- Vendor binaries, extracted strings, decompiled material, credentials, and device data remain
  excluded from this repository.
- The fixed NLD symmetric master and all license/cache material remain excluded; only algorithm and
  framing facts are recorded.

## 0.2.0 - 2026-08-28

### Added

- Added a bounded static analysis of NLD FCC Smart RC `2.0.0.6`, including exact input identities,
  normal FCC native/server flow, C0 server-routed WireGuard orchestration, device-keyed offline
  licensing, parameter-editor design, and Package Installer boundary.
- Recorded that seven packaged JSON profiles are byte-identical to pinned FreeFCC but have no found
  NLD runtime reference.
- Added a fixed-scope negative result for an explicit NLD Remote ID control and preserved opaque
  native/server and hosted-DJI-Fly side effects as unknown.
- Added NLD artifacts A-016 through A-018, claims C-080 through C-092, two hypotheses, three
  negative results, one blocker, source links, and handoff guidance.

### Safety and provenance

- No NLD APK was installed or executed, no NLD API was contacted, and no device state changed.
- Vendor binaries, decompiled code, native libraries, license material, and private traffic remain
  excluded. Files matching AGPL-3.0 FreeFCC profiles were not copied into this MIT repository.

## 0.1.0 - 2026-08-28

### Added

- Created an independent RC 2 / Mini 5 Pro research archive with an evidence vocabulary, claim
  ledger, experiment timeline, topic reports, negative-result register, artifact identities,
  blockers, source index, and coding-agent handoff.
- Added automated Markdown-link, evidence-index, privacy-boundary, and whitespace validation.
- Recorded v0.10 as the current offline admission-probe candidate.
- Recorded V2.2 as rejected and V2.3 as the corrected but still unadmitted, zero-send route-only
  artifact without a new independent post-fix audit conclusion.

### Privacy

- Excluded vendor binaries, decompiled vendor code, private captures, serials, accounts, tokens,
  keys, licenses, real identifiers, coordinates, telephone numbers, and host-specific paths.
