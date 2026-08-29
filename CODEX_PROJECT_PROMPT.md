# Codex project prompt

Use this prompt when starting or resuming a Codex task for this repository.

```text
Project: FindUAS — authorized DJI RC 2 / Mini 5 Pro interoperability and Remote ID compliance
testing.

Authorization and environment

- The user owns and controls the RC 2, aircraft, removable storage and detection receiver used in
  this lab. Work is limited to those named devices, local files, a disposable Android emulator and
  public documentation/prior art.
- The purpose is to build a repeatable test panel for Remote ID broadcast behavior and regional
  protocol compatibility, then verify behavior with exact readback and an independent receiver.
- This is not a request to access third-party systems, evade account controls, forge credentials or
  licenses, conceal aircraft identity in operation, or deploy a capability outside the lab.

Current objective

Implement and verify a controllable Mini 5 Pro Remote ID switch. The switch must change a genuine
same-item baseline or a readback-closed aircraft policy candidate, read the changed state back,
restore the baseline and read it back again, and finally survive an operator-controlled external RF
A-B-A test. Canonical FlySafe/Remote-ID inventory remains the preferred official route; a bounded
aircraft policy candidate may be used only after same-session route admission, metadata validation,
and baseline readback. Keep region configuration as a separate, reversible compatibility-test
surface.

Allowed autonomous work

- Inspect repository files, public standards and public source; analyze user-supplied binaries
  offline without publishing them.
- Edit original source and documentation in this repository; build and test original host tools,
  APKs and synthetic fixtures.
- Run read-only diagnostics and same-process query instrumentation on the disposable emulator.
- On the named lab devices, run read-only queries and previously authorized reversible configuration
  experiments. Record baseline, exact action count, readback, restore and final readback.
- Keep GitHub current after each reproducible result: source, objective evidence, negative result,
  limitations and next step belong in the same commit.

Hard boundaries

- Do not unlock the bootloader, enable OEM unlock, reboot to bootloader, patch or flash boot,
  vendor_boot or vbmeta, install Magisk, modify TEE/QFPROM/eFuse, or weaken the startup trust chain.
- Do not fabricate, transfer, replay or publish FlySafe/RID license IDs, signed blobs, account tokens,
  credentials, device identifiers, coordinates or private captures.
- RID/FlySafe state-changing work is not categorically forbidden, but it is gated: obtain a genuine
  same-item baseline or a readback-closed policy candidate, prove the exact route, preserve an
  immediate restore path, and require independent RF A-B-A evidence. Do not reinterpret an ACK, UI
  state or onboard Boolean as RF proof.
- Software must never start motors. Motor-on validation is performed manually by the operator with
  the aircraft secured and the external receiver online.
- Do not redistribute DJI APKs, firmware, decompiled vendor source, runtime dumps or proprietary
  binaries. Publish only independently written source, tests, hashes, redacted facts and citations.

Research method

Observe -> change one variable -> record the exact result -> restore if state changed -> update the
evidence register. Prefer a small experiment with visible protocol/log output over a general
framework. Treat timeouts, absent callbacks and ambiguous errors as narrow negative results, not as
"unsupported", "off" or "empty".

Success criteria

The project is complete only when the current aircraft yields a canonical existing-state baseline,
the same genuine item can be changed and read back, the original state is restored and read back,
and an independent Remote ID receiver confirms the intended A-B-A RF behavior. Until then, continue
the strongest evidence-producing next step and keep the repository handoff current.

Communication

Use plain Chinese with the user. Lead with the concrete result, material limitation and next action.
Ask for operator help only when a physical action is actually ready, and provide one consolidated
checklist rather than repeated prompts.
```

This wording describes the real authorized scope; it must not be altered to hide a materially
different action. A task that expands beyond these devices, data or reversible lab validation needs
fresh user direction and a corresponding repository-boundary review.
