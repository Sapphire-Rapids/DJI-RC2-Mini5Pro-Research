# V1 live admission boundary

V1 is not eligible merely because it builds. Before any copy/install/attach, all of these must be
true on the actual RC 2 `07.00.0100`:

1. the complete v0.8 page proves the expected stock DJI Fly and helper identity, AArch64 ABI,
   `ro.debuggable`, SELinux and clear upgrade state;
2. the exact extracted library path, owner/mode/label and linker accessibility are known;
3. a separately audited caller can invoke `attach-agent` through the legitimate permission
   boundary without automatic root/ADB probes and while preserving argv, stderr and exit status;
4. V0 has attached successfully once with no DJI Fly instability and has then been removed by a
   normal DJI Fly restart;
5. aircraft motors are off and loss/restart of DJI Fly is acceptable;
6. the V1 APK hash and signer are rechecked immediately before staging.

The adjacent stock `dpad_fuli` shell page does not satisfy item 3: opening it automatically attempts
`adb shell su` and runs `adb version`, and its executor discards stderr and exit status. It must not
be opened as the attach launcher. A full exported-component audit also found no Intent, receiver,
service, PendingIntent or Binder route that can ask the stock package to run one fixed command and
return its exit status; see `../dpad_fuli_exported_caller_audit_20260828.md`.

V1 returns nonzero unless it sees exactly one `electronicIDBroadcastOn` semantic thunk, exactly one
`electronicIDBroadcastExisted` thunk and one shared loader. Missing or duplicate anchors, loader
ambiguity, any JNI exception, allocation/cleanup error or oversized class set is a stop condition.
JVMTI-environment disposal failure is also a stop condition.

Even success proves only that the two reviewed France-EID semantic-anchor classes are already
loaded by one ClassLoader. That topology is a prerequisite for, but does not prove, a later getter
design. It does not prove support, state, protocol success, broadcast behavior or a global RID
switch, and it never authorizes SET.
