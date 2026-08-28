# No-write / single-send contract

The V2 baseline phase is GET-only. Its body is exactly `[0x02]`; source and artifact audits reject
SET bodies `[0x00]` and `[0x01]`, `JNIKeyValue`, typed subject calls, raw observers, TCP-port sends,
socket APIs and any second send call site.

The guarded call is a laboratory single-shot with `retryTimes=0`. DJI Fly's product-139 request
constructor initializes retry to `3`; static EID Characteristics starts at `+0x30=0`, so initial
typed GET and typed SET both retain `3`, while a runtime Characteristics update can conditionally
clear typed GET only. V2's retry zero is therefore a deliberate safety deviation, not a claim of
official transport equivalence.

One terminal callback is accepted only if its handle matches the returned nonzero handle, the raw
payload length is exactly two, the protocol result byte is zero, no duplicate callback is observed,
and the 100 ms quarantine window stays quiet. A 2 s monotonic wrapper deadline permits one local
cancel for cleanup. Cancel, timeout and process interruption are never interpreted as proof of a
remote no-op.

The 100 ms window is not an unbounded exactly-once proof. A callback arriving after it can still
increment the process-static counters, including in the small interval between bridge success and
the final agent snapshot, without changing the already selected success error code. This is harmless
in the permanently unresolved carrier because no callback object or send is reachable, but it is a
live-admission blocker rather than an accepted production race.

The route epoch has the same lifetime requirement. The offline function is permanently false, but a
future resolver cannot treat the checks performed before helper-class construction as a pre-send and
post-response proof. It must recheck immediately before the sole JNI invocation and after the terminal
result/quiescence boundary; otherwise a link or aircraft change during helper setup or callback wait
can make an old-session baseline look current.

This directory contains no SET implementation. A future writer belongs in a separate version and
must add a durable baseline/target journal, one explicit transition, raw GET readback after every
ACK or timeout, explicit restoration to the baseline, final raw GET verification, aircraft/session
identity binding, a motor-stopped interlock and user-controlled independent RF A-B-A validation.
Software must never start the motors.
