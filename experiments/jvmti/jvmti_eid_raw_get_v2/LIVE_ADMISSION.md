# V2 live-admission gates

This file describes future prerequisites; none are satisfied by the offline carrier.

All gates must be obtained read-only from the same current DJI Fly process/session and must remain
stable between resolution and the single JNI call:

1. v0.8 reports `COMPLETE` for the exact DJI Fly package, APK/SO hashes, AArch64 loader,
   debuggability, SELinux and helper boundary.
2. A separately reviewed, side-effect-free attach caller passes V0, DJI Fly is restarted normally,
   and V1 resolves exactly one `electronicIDBroadcastOn` and one
   `electronicIDBroadcastExisted` anchor in the same ClassLoader.
3. `JNIRawData` is already initialized; `SendInterface`, both semantic anchors and the raw class
   all belong to that same loader. V2 must not trigger DJI class initialization.
4. Current product identity is product 139, France EID capability/gating is present, and the exact
   live `productId` and `deviceId` resolve to one existing ProductMgr datalink. The Java key's
   default `productId=0` is not a wildcard or permission to guess; however, `0` may itself be the
   exact first live product key. Read the value from the uniquely resolved live EID
   `BaseAbstraction` and cross-check its route instead of rejecting or accepting zero by value alone.
5. The current global sender index, live Characteristics HostID override, receiver type/index and a
   connection epoch are read from the same route snapshot. Static `18/4` is not enough. The epoch is
   rechecked immediately before `CallStaticLongMethodA` and again after the accepted terminal/quiescent
   result; the current offline bridge checks it only before helper construction, which is not a live
   implementation of this requirement.
6. No concurrent typed EID GET is running. V2 makes exactly one raw GET; it never calls
   `getOrNull()`, registers an observer or opens `40007`/`40009`.
7. Any unknown, duplicate candidate, epoch change, zero handle, callback mismatch, malformed ACK,
   nonzero protocol result, timeout, duplicate callback or cleanup uncertainty stops without retry.
8. The callback owner/release lifecycle and a terminal quiescence boundary are proven. The current
   100 ms duplicate quarantine is rejected: ACK delivery occurs before pending-node erase, timeout
   delivery occurs before copied-owner destruction, and explicit cancel is asynchronous. A future
   build must prove registration completion, callback return with in-flight count zero, and a
   post-terminal worker-tail fence at which the exact pending handle and `CallbackStopper` ID are both
   absent. A timer, sleep, cancel return, or first callback is not a completion boundary. See
   `../eid_callback_lifetime_audit_20260828.md`.
9. Once native callbacks have been registered or a send might have been accepted, the agent library
   has an explicit process-lifetime retention rule on the exact target ART. Android 11 AOSP leaves the
   mapping open even when `Agent_OnAttach` returns nonzero, but a safer live design must not depend on
   an unverified vendor implementation doing the same; operation failure and agent-retention return
   status should be represented separately.

Only after these gates are independently implemented and audited may the permanent unresolved
resolver be replaced. That later build requires a new version, new hashes and a separate review; it
must not overwrite the offline artifact in place.
