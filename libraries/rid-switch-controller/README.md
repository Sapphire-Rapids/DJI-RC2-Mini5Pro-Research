# RID_UNLOCK control safety core (research only)

This work-only Kotlin/JVM module models two deliberately different experiments for a future DJI
RC 2 `RID_UNLOCK` integration:

- `RidValidationPulseController.executeValidationPulse(...)` briefly applies one verified
  transition, proves it with an exact GET, and always restores the exact baseline before returning.
- `RidBoundedLeaseController.prepareBoundedLease(...)` can hold a proven target state for a finite
  lease after an explicit `commitBounded(...)`, then restores on early close or watchdog expiry.

The bounded-lease feature is disabled by default. Its explicit research policy has a non-bypassable
120-second ceiling; there is no permanent commit, renewal, or indefinite mode.

Status: **NOT ADMITTED.** This is **not a working aircraft switch**. The independently written
source is covered by the repository-root [MIT license](../../LICENSE). Production source contains
no Android integration, device/socket/cloud transport, DJI command encoder,
persistence, generic write API, or boolean setter.

The typed transport boundary contains only:

- a live, cache-bypassing exact RID state GET;
- enable one cryptographically/provenance-verified type-6 license;
- disable that same verified active license;
- restore an exact baseline using the same verified license capability used for mutation.

Every failure after a possible mutation triggers bounded, non-cancellable restoration and final
GET reconciliation. An uncertain result locks that controller instance. Raw license material is
zeroed when a validation pulse, abandoned preparation, failed commit, or lease terminates. RF
evidence remains external and can never be marked complete by this core.

## Test

Use JDK 21 to run Gradle; emitted bytecode targets JVM 17:

```sh
export JAVA_HOME=/path/to/jdk-21
gradle clean test
```

The repository-level control-surface and blocker records are in
[`../../docs/05_RID_CONTROL_SURFACES.md`](../../docs/05_RID_CONTROL_SURFACES.md) and
[`../../docs/12_CURRENT_BLOCKERS.md`](../../docs/12_CURRENT_BLOCKERS.md).
