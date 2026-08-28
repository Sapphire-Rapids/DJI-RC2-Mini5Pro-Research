package com.finduas.rc2ridadmin;

/**
 * Pure state machine for one reversible RID_UNLOCK license experiment.
 *
 * <p>The state machine deliberately knows no license identifier or transport details. A SET ACK is
 * never accepted as state proof: every attempted transition must be reconciled by a fresh, complete
 * inventory of the exact same opaque record before the next write is admitted.</p>
 */
final class RidUnlockControlFlow {
    enum State {
        BASELINE_READY,
        FORWARD_DISPATCHED,
        FORWARD_READBACK_REQUIRED,
        TARGET_CONFIRMED,
        RESTORE_DISPATCHED,
        RESTORE_READBACK_REQUIRED,
        RESTORED_NO_CHANGE,
        RESTORED,
        UNCERTAIN,
        CLOSED
    }

    enum Readback {
        BASELINE,
        TARGET,
        UNUSABLE
    }

    private final boolean baselineEnabled;
    private final boolean targetEnabled;
    private State state = State.BASELINE_READY;
    private State uncertainOrigin;
    private boolean forwardAckAccepted;
    private boolean restoreAckAccepted;

    RidUnlockControlFlow(boolean baselineEnabled) {
        this.baselineEnabled = baselineEnabled;
        this.targetEnabled = !baselineEnabled;
    }

    synchronized boolean getBaselineEnabled() {
        return baselineEnabled;
    }

    synchronized boolean getTargetEnabled() {
        return targetEnabled;
    }

    synchronized State getState() {
        return state;
    }

    synchronized boolean wasForwardAckAccepted() {
        return forwardAckAccepted;
    }

    synchronized boolean wasRestoreAckAccepted() {
        return restoreAckAccepted;
    }

    synchronized void beginForward() {
        requireState(State.BASELINE_READY, "forward SET");
        state = State.FORWARD_DISPATCHED;
    }

    /** Records transport completion only; even a strict ACK still requires inventory readback. */
    synchronized void finishForwardTransport(boolean strictAckAccepted) {
        requireState(State.FORWARD_DISPATCHED, "forward transport completion");
        forwardAckAccepted = strictAckAccepted;
        state = State.FORWARD_READBACK_REQUIRED;
    }

    /** Closes an attempted forward phase only when the transport gate proves no mutation began. */
    synchronized void cancelForwardBeforeTransport() {
        requireState(State.FORWARD_DISPATCHED, "forward pre-transport cancellation");
        state = State.RESTORED_NO_CHANGE;
    }

    synchronized void reconcileForward(Readback readback) {
        requireState(State.FORWARD_READBACK_REQUIRED, "forward readback");
        if (readback == null || readback == Readback.UNUSABLE) {
            uncertainOrigin = State.FORWARD_READBACK_REQUIRED;
            state = State.UNCERTAIN;
        } else if (readback == Readback.TARGET) {
            uncertainOrigin = null;
            state = State.TARGET_CONFIRMED;
        } else {
            // The write either did not apply or was already rolled back elsewhere. No second SET.
            uncertainOrigin = null;
            state = State.RESTORED_NO_CHANGE;
        }
    }

    /** Reconciles another manually requested read-only batch after forward uncertainty. */
    synchronized void resumeForwardReadback(Readback readback) {
        requireUncertainOrigin(State.FORWARD_READBACK_REQUIRED, "forward recovery readback");
        state = State.FORWARD_READBACK_REQUIRED;
        reconcileForward(readback);
    }

    synchronized void beginRestore() {
        requireState(State.TARGET_CONFIRMED, "restore SET");
        state = State.RESTORE_DISPATCHED;
    }

    /** Records transport completion only; even a strict ACK still requires inventory readback. */
    synchronized void finishRestoreTransport(boolean strictAckAccepted) {
        requireState(State.RESTORE_DISPATCHED, "restore transport completion");
        restoreAckAccepted = strictAckAccepted;
        state = State.RESTORE_READBACK_REQUIRED;
    }

    /** Returns to the confirmed target when the restore transport gate admitted no mutation. */
    synchronized void cancelRestoreBeforeTransport() {
        requireState(State.RESTORE_DISPATCHED, "restore pre-transport cancellation");
        state = State.TARGET_CONFIRMED;
    }

    synchronized void reconcileRestore(Readback readback) {
        requireState(State.RESTORE_READBACK_REQUIRED, "restore readback");
        if (readback == Readback.BASELINE) {
            uncertainOrigin = null;
            state = State.RESTORED;
        } else {
            // A second restore write would be an application-level retry and is never automatic.
            uncertainOrigin = State.RESTORE_READBACK_REQUIRED;
            state = State.UNCERTAIN;
        }
    }

    /** Reconciles another manually requested read-only batch after restore uncertainty. */
    synchronized void resumeRestoreReadback(Readback readback) {
        requireUncertainOrigin(State.RESTORE_READBACK_REQUIRED, "restore recovery readback");
        state = State.RESTORE_READBACK_REQUIRED;
        reconcileRestore(readback);
    }

    synchronized boolean needsImmediateRestore() {
        return state == State.TARGET_CONFIRMED;
    }

    synchronized boolean needsReadbackBeforeAnyWrite() {
        return state == State.FORWARD_DISPATCHED
                || state == State.FORWARD_READBACK_REQUIRED
                || state == State.RESTORE_DISPATCHED
                || state == State.RESTORE_READBACK_REQUIRED
                || state == State.UNCERTAIN;
    }

    synchronized boolean isSafelyAtBaseline() {
        return state == State.BASELINE_READY
                || state == State.RESTORED_NO_CHANGE
                || state == State.RESTORED;
    }

    synchronized boolean isTerminalUncertain() {
        return state == State.UNCERTAIN;
    }

    synchronized void close() {
        if (!isSafelyAtBaseline()) {
            throw new IllegalStateException(
                    "RID_UNLOCK_SESSION_CANNOT_CLOSE_BEFORE_CONFIRMED_BASELINE");
        }
        state = State.CLOSED;
    }

    private void requireState(State expected, String operation) {
        if (state != expected) {
            throw new IllegalStateException(
                    operation + " requires " + expected + " but state is " + state);
        }
    }

    private void requireUncertainOrigin(State expected, String operation) {
        if (state != State.UNCERTAIN || uncertainOrigin != expected) {
            throw new IllegalStateException(
                    operation + " requires UNCERTAIN from " + expected
                            + " but state is " + state + " origin=" + uncertainOrigin);
        }
    }

    @Override
    public synchronized String toString() {
        return "RidUnlockControlFlow{state=" + state
                + ", baselineEnabled=" + baselineEnabled
                + ", targetEnabled=" + targetEnabled
                + ", forwardAckAccepted=" + forwardAckAccepted
                + ", restoreAckAccepted=" + restoreAckAccepted + "}";
    }
}
