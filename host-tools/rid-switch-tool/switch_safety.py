"""Small transport-independent helpers for the three bounded research CLIs."""


def validate_boolean_write_range(*, type_id, size, minimum_raw, maximum_raw):
    """Require canonical one-byte metadata permitting both Boolean values.

    F7/E1 bounds occupy four-byte integer slots. Signed i8 bounds must use
    signed 32-bit extension; out-of-domain or unknown representations stay locked.
    Reading a zero-range flag is allowed, but it never admits a write or restore.
    """
    if size != 1 or type_id not in (0, 4, 11):
        raise ValueError("only one-byte integer/Boolean writes are established")
    if len(minimum_raw) != 4 or len(maximum_raw) != 4:
        raise ValueError("Boolean metadata bounds must use four-byte slots")
    signed = type_id == 4
    minimum = int.from_bytes(minimum_raw, "little", signed=signed)
    maximum = int.from_bytes(maximum_raw, "little", signed=signed)
    lower, upper = (-128, 127) if signed else ((0, 1) if type_id == 11 else (0, 255))
    if not lower <= minimum <= 0 < 1 <= maximum <= upper:
        raise ValueError("metadata range does not canonically permit both Boolean values")


def run_transition(*, report, record, write, read, target_raw, baseline_raw):
    """Attempt one transition, then restore and reconcile even after a lost ACK.

    Callers validate both encoded values before entering. Each write is attempted
    once; the final read is still attempted if the restore ACK is unavailable.
    This is bounded best-effort recovery, not a promise that a device restores.
    """
    forward_ok = False
    restore_ok = False
    report["state"] = "mutation_unverified"
    try:
        try:
            write(target_raw)
            record("forward_write", "ack", {})
            observed = read()
            forward_ok = observed == target_raw
            record("forward_readback", "match" if forward_ok else "mismatch",
                   {"raw_hex": observed.hex()})
        except (Exception, KeyboardInterrupt) as exc:
            record("forward", "fail", {"error_type": type(exc).__name__})
    finally:
        # Entered even if dispatch raised after the device might have applied it.
        report["state"] = "restore_unverified"
        try:
            write(baseline_raw)
            record("restore_write", "ack", {})
        except (Exception, KeyboardInterrupt) as exc:
            record("restore_write", "fail", {"error_type": type(exc).__name__})
        try:
            observed = read()
            restore_ok = observed == baseline_raw
            record("restore_readback", "match" if restore_ok else "mismatch",
                   {"raw_hex": observed.hex()})
        except (Exception, KeyboardInterrupt) as exc:
            record("restore_readback", "fail", {"error_type": type(exc).__name__})
        if restore_ok:
            report["state"] = (
                "A_B_A_complete" if forward_ok else "restored_forward_unverified"
            )
    return forward_ok and restore_ok


def close_usb(*, context, handle, claimed, interface, report):
    """Try every cleanup independently, without hiding the operation's report."""
    actions = []
    if handle is not None:
        if claimed:
            actions.append(("release_interface", lambda: handle.releaseInterface(interface)))
        actions.append(("close_handle", handle.close))
    if context is not None:
        actions.append(("close_context", context.close))
    for stage, action in actions:
        try:
            action()
        except (Exception, KeyboardInterrupt) as exc:
            report.setdefault("cleanup_errors", []).append(
                {"stage": stage, "error_type": type(exc).__name__}
            )
    return not report.get("cleanup_errors")
