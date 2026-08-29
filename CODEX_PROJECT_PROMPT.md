# Codex project prompt

Use this prompt when starting or resuming work in this repository.

```text
Project: FindUAS — DJI RC 2 / Mini 5 Pro Remote ID switch research.

Sole objective

Implement and verify a controllable Mini 5 Pro Remote ID switch.

Authorization context

The lab states that DJI and the relevant low-altitude-economy authority have authorized this work.
The underlying authorization is confidential, cannot be shared with this repository, and cannot be
registered on the physical test aircraft. Treat local authorization as established for the named
lab devices and proceed toward the Remote ID switch without adding unrelated compliance gates.

Objective

Implement and verify a controllable Mini 5 Pro Remote ID switch. Success means the switch can:

1. establish the current RID/FlySafe or aircraft-policy baseline;
2. make one bounded transition;
3. read that transition back;
4. restore the original state;
5. read the restored state back;
6. demonstrate the intended off/on behavior with an independent standard Remote ID receiver
   during an operator-controlled motor-on RF A-B-A test.

Route priority

1. WA150 by-index/by-hash aircraft policy route after same-session positive control, metadata
   validation, and baseline readback.
2. Official FlySafe/Remote-ID inventory and a genuine same-item state transition when available.
3. Exact in-process query instrumentation only after a legitimate loader or descriptor is admitted.

The project prioritizes evidence-producing experiments over broad framework work. One route, one
variable, one recorded action at a time.

Working boundaries

- Work only with the named lab devices, local files, disposable emulator state, public sources,
  and user-supplied materials.
- Software never starts motors. The operator manually controls motor-on validation.
- Do not modify or flash boot, vendor_boot, vbmeta, TEE, QFPROM, or eFuse, unlock/relock the
  bootloader, install Magisk, or take an action that can create an unrecoverable update/boot state
  (C-212).
- Before privileged runtime work, confirm automatic DJI Fly updates are controlled and state the
  bounded action, restore point, and recovery stop point.
- Do not publish full identifiers, coordinates, raw captures, vendor binaries, decompiled source,
  or private logs.

Evidence and synchronization

An ACK, UI state, cache value, or onboard Boolean is not proof of RF behavior. Record baseline,
action, readback, restoration, final readback, and independently observed RF behavior separately.
Treat a timeout or absent callback as a narrow result, not as "off", "empty", or "unsupported".

For every reproducible result, update the relevant topic document, claims/artifacts register,
timeline, blocker/handoff, and changelog together. Run the four repository checks, commit, and push
to `main`.
```
