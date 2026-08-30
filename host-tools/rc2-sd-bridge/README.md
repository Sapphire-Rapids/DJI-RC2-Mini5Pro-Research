# RC 2 SD bridge transport

Status: **OBSERVED** for B1 diagnostics and the B2 baseline/load/cleanup/STOP sequence.
A-048 successfully ran in Fly; the test file was removed and B2 is closed (C-273--C-275).
See [the runtime record](../../docs/23_RC2_LIVE_RUNTIME.md) for the changing job results and live
state. Compilation and synthetic tests remain separate evidence.
The libmtp helper transports bounded B1 diagnostic-mailbox files and does not itself execute
device code, install an application, attach an agent or change permissions. The Python client
submits fixed jobs: B1 supports `PING`, `SNAPSHOT` and `STOP`; B2 adds the three canary operations
below. It accepts no arbitrary Shell command. No aircraft protocol request is provided by this
transport/client.
The repository [MIT license](../../LICENSE) applies; generated binaries and all live output stay
excluded. See [the current runtime record](../../docs/23_RC2_LIVE_RUNTIME.md) for device evidence.

## Build

Requires a C11 compiler, `pkg-config` and libmtp (host build checked with 1.1.23).

```sh
sh build.sh
```

The result is ignored `build/mtp_bridge`. The build runs `--self-test`, which checks path and
operation restrictions, duplicate/parent/storage selection, payload limits and close-record
validation without initializing libmtp or accessing USB. `CC` and `PKG_CONFIG` may select tools.

## Interface and boundaries

```text
mtp_bridge mkdir <relative-directory>
mtp_bridge put <relative-file> <local-source>
mtp_bridge get <relative-file> <new-local-output>
mtp_bridge archive-active <sid>
```

Every device operation requires exactly one USB device with VID/PID `2ca3:1021` and exactly one
storage of type `4`. Lookups use that storage and the exact parent, reject duplicate names/case aliases and
use an uncached MTP connection. No device serial or local port topology is embedded.

| Path | Operations |
| --- | --- |
| `Download/B1.sh`, `Download/F4.sh`, `Download/B2.sh`, `Download/L1.sh`, `Download/FindUAS_ARTTI_V2.so` | put/get |
| `Download/FindUAS/Bridge/active.session` | put/get |
| `Download/FindUAS/Bridge/<sid>` and its `inbox`, `outbox` directories | mkdir |
| `…/<sid>/inbox/<seq>.job`, `<seq>.ready` | put/get |
| `…/<sid>/outbox/<seq>.accepted`, `<seq>.report`, `<seq>.done` | get only |
| `…/<sid>/worker.lock`, `worker.log`, `session.ready`, `session.closed`, `session.receiver`, archived `active.session` | get only |
| `Download/FindUAS/Probe/FindUAS_F4_*.txt`, `A048_copy.receipt`, `A048_attach.attempted` | get only |

`sid` is exactly 16 lowercase hex characters; `seq` is exactly four decimal digits. Only the
listed directory ancestors may also be created. Paths must be relative ASCII, at most 511 bytes,
with components at most 127 bytes; empty components, `.`, `..`, backslashes, whitespace and
unlisted names are rejected before USB initialization.

`mkdir` creates missing components and confirms a unique matching directory after each creation.
`put` first snapshots one regular, non-symlink local file of at most 32,768 bytes. An existing
remote file is accepted only after a full byte-for-byte readback match; different content is never
overwritten. A new upload also requires full readback and exact name/size/object checks. Payload
callbacks enforce the byte limit without confusing PTP overhead with file bytes. Uncertain or
failed uploads are not retried or deleted automatically; inspect their state before continuing.

`get` accepts at most 131,072 bytes, checks the complete payload and unchanged remote identity,
then exclusively creates the local output with mode `0600`. It never overwrites an existing local
file. A local write failure may leave that newly created partial file; a nonzero result must not
be treated as a valid report. The caller validates the report/ack schema, length, digest and end
marker. Byte receipt alone does not establish a diagnostic or execution result.

Exit `0` means the requested operation verified; `2` is invalid input; **`3` is a missing remote
file or parent for get**, suitable for polling; other failures return `4`. Stdout contains one
short result. libmtp diagnostics are redirected to stderr and must be kept private. The caller
must apply a subprocess deadline: libmtp can block during device open, transfer or release.

Use one host writer and serialize mailbox operations. MTP does not expose a portable exclusive
create transaction; pre/post checks detect conflicts but do not provide a lock against another
writer racing the device. Upload the immutable job and verify it before uploading its ready
record. The receiver must validate the ready record and job digest; an upload return alone is
not the commit boundary. Do not publish raw reports, runtime identifiers or transport logs.

## Closed-session rotation

`archive-active <sid>` permits only a same-storage move of the root `active.session` into that
SID's existing directory. It requires exact source content `B1 SESSION <sid> END\n` and exact
`session.closed` content `B1 CLOSED <sid> <reason> END\n`, where reason is `STOP`, `TTL`, `LIMIT`
or `ERROR`. The destination must not exist. The helper verifies the moved file in full and confirms
that the old location is absent. It never deletes or overwrites a session record. A failed or
uncertain move needs readback before a new session is created; it does not prove the receiver
stopped beyond the supplied close record.

## Python protocol client

`bridge.py` requires Python 3.10+ and only the standard library. An explicit private `--state-dir`
is mandatory: use the repository's ignored `private/` tree or a directory outside the repository.
The directory must belong to the caller with mode `0700`. Keep and reuse this state; it contains
immutable jobs, received reports and raw transport logs. A nonblocking `flock` prevents concurrent
clients sharing it; a second invocation reports `STATE_BUSY` without issuing a device operation.

Run from this tool directory, substituting private local paths:

```sh
python3 bridge.py --state-dir /path/to/private-state stage --b1 /path/to/B1.sh --f4 /path/to/F4.sh
python3 bridge.py --state-dir /path/to/private-state prepare
python3 bridge.py --state-dir /path/to/private-state status
python3 bridge.py --state-dir /path/to/private-state submit PING
python3 bridge.py --state-dir /path/to/private-state collect 0001
```

`prepare` persists a new SID locally, creates its inbox/outbox and publishes `active.session`
last. An already active session is reused only with its original local history. Unknown active
history is not silently imported and sequence `0001` is never blindly reused. Closed sessions
can be archived only after pending local tasks have been collected or classified as unavailable.
The operator starts B1 once separately; neither `stage` nor `prepare` launches device code.

`status` reads canonical active/ready/closed records. A ready record is a past startup observation,
not proof that the worker is still alive. `submit` checks all five possible remote files for a
new sequence, then durably stores the canonical job and ready records before sending the job.
The ready record is uploaded only after the C helper verifies the job upload. On any uncertain failure, repeat
the same `submit` operation using the same state: it retains the SID, sequence and bytes.
A different operation is refused while that task is pending. No new task is allocated until
collection establishes the preceding task's terminal result; each session has at most 64 tasks.

`collect` performs one bounded pass and returns `TASK_PENDING` when no result is available; there
is no polling loop or automatic MTP retry. Accepted records must match the immutable job's size
and SHA-256. Done records must match SID, sequence, handler return code and the complete report's
size/SHA-256 and envelope. A valid `REJECTED` envelope is a terminal failure,
not a retry request; hashes do not authenticate an SD writer's identity.

For `SNAPSHOT`, return code `10` is a saved `INCOMPLETE` F4 report and is collected as well as
code `0`. Only an exact removable-SD `Probe/FindUAS_F4_<timestamp>_<pid>.txt` path from the expected
handler output is accepted. The client checks its v4 schema and end marker and keeps it private,
marked `envelope_received_only`; detailed diagnostic interpretation remains a separate step.
If the session is canonically closed and a second done lookup is still missing, collection records
`TASK_UNAVAILABLE … outcome=UNKNOWN`. It does not infer whether the task ran or replay it; explicit
`prepare` can then rotate the closed session. A racing valid done record follows normal collection.

All C subprocess calls use argument arrays, a deadline no greater than 30 seconds, and at least
one second between the previous call's end and the next call; each CLI also cools down before its
first call. Timeout/failure details, stdout and stderr are retained under `logs/`, including uncertain
results. Every C download uses a fresh local filename. Console output contains only short status,
sequence and handler return code, not private PID/path/report contents. `--transport` selects the
built C helper and `--transport-timeout` may lower the deadline. No command automatically sends STOP.

Synthetic tests use a fake transport and never initialize USB:

```sh
python3 -m unittest discover -s . -p 'test_bridge.py' -v
```

They cover the five orphan-slot cases, uncertain job/ready commits, original-state recovery,
closed-session races, wrong bindings/hashes/return codes, F4 code-10 receipt, path escape rejection,
local locking and transport cooldown/timeout logging.

The separate receiver integration suite uses real host mksh and Java with synthetic filesystem
paths. Set `MKSH` to its executable and put `java`/`javac` on PATH, then run:

```sh
python3 -m unittest discover -s tests -p 'test_receiver.py' -v
```

Its eleven cases include Java stdout EOF, inherited FD3, input-read failure, partial/invalid jobs,
result collisions, helper snapshot integrity, expiry and the 64-job limit. Without `MKSH` these
tests skip; the receiver checks do not access USB or an Android device.

## B2 fixed canary lane

B2/A-050 preserves the B1 mailbox protocol and adds a canonical `session.receiver` record naming
B2. The client checks that marker before submitting `CANARY_BASELINE`, `CANARY_LOAD` or
`CANARY_CLEANUP`. These operations run only the SHA-pinned L1/A-049 text; L1 in turn pins
the 8,372-byte A-048 ARMv7 identity canary. Staging/readback and current execution state are in
[the runtime record](../../docs/23_RC2_LIVE_RUNTIME.md) (C-268--C-276).

```sh
python3 bridge.py --state-dir /path/to/private-state stage-canary --b2 /path/to/B2.sh --l1 /path/to/L1.sh --canary /path/to/identity.so
python3 bridge.py --state-dir /path/to/private-state prepare
# The operator starts B2 once, then the host checks its status and reads the baseline.
python3 bridge.py --state-dir /path/to/private-state submit CANARY_BASELINE
python3 bridge.py --state-dir /path/to/private-state collect 0001
```

Only the latest completely received baseline with return code zero and one section-external
`preflight_ready=true` permits a LOAD allocation. The client allocates at most one LOAD per
session; uncertain transfer retries keep that same sequence. A complete outer result with
truncated/invalid L1 content is retained as a terminal diagnostic failure, permitting explicit
cleanup without treating that content as a successful baseline.

LOAD repeats the baseline, exclusively creates the one ordinary internal SO, verifies its
FD-derived identity/hash/label, and permanently records the attempt before one fixed-name
Activity Manager dispatch. Its own strict native parser binds enter/result to the expected
PID/UID and session. The API return is recorded separately from the native `ready` outcome.

Normal cleanup removes only that verified file after a matched native terminal record. Later
`CANARY_CLEANUP` may collect a late result or recover after a different boot; it never repeats
the dispatch. A partial copy with a different hash remains for explicit recovery. Neither the
copy receipt nor the global attempt record is automatically deleted, and file/environment
cleanup does not unload the agent/JVMTI plugin from a running process.

The fixed helper budgets are 120 seconds for BASELINE, 210 for LOAD and 30 for CLEANUP, within
the receiver's one-hour lease. Reports, upgrade/network observations and native identity logs
remain private. The real-mksh loader tests cover 13 methods/39 scenarios; the B2 composition
suite covers the Java startup and pinned helper dispatch. Run them with the same MKSH/JDK
setup as the receiver suite:

```sh
python3 -m unittest discover -s tests -p 'test_canary_*.py' -v
```
