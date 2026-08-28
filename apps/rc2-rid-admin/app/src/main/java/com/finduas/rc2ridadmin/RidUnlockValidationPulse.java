package com.finduas.rc2ridadmin;

import java.util.Arrays;

/**
 * Executes one reversible, readback-authoritative RID_UNLOCK validation pulse.
 *
 * <p>The pulse is deliberately package-private and is not connected to the UI. It performs at
 * most one forward SET and, only after an exact target readback, at most one restore SET. A SET
 * ACK is diagnostic only. Complete inventory reads may be repeated up to three times after a
 * possible mutation, but SET is never retried.</p>
 *
 * <p>If the final baseline cannot be proved, the coordinator retains the baseline inventory and
 * opaque handle in memory and does not finish the DJI session. The caller must retain this
 * coordinator and must not terminate the process as though restoration had succeeded.
 * {@link #resumeRecovery()} is a strictly read-only continuation. Each invocation has a
 * three-inventory budget and may be repeated indefinitely while uncertainty remains. If it proves
 * the target, it stops at {@code TARGET_CONFIRMED_RESTORE_REQUIRED}; only the separate explicit
 * {@link #restoreConfirmedTargetOnce()} entry may attempt the one restore. A call rejected before
 * the session mutation gate remains in that state and is not counted as a transmitted SET.</p>
 */
final class RidUnlockValidationPulse {
    static final int MAX_READBACK_ATTEMPTS = 3;

    enum State {
        NOT_DISPATCHED,
        RESTORED_NO_CHANGE,
        RESTORED,
        TARGET_CONFIRMED_RESTORE_REQUIRED,
        UNCERTAIN_FORWARD_READBACK,
        UNCERTAIN_RESTORE_READBACK
    }

    enum Readback {
        BASELINE,
        TARGET
    }

    /** Sensitive baseline owner. Implementations must clear their opaque handle on close. */
    interface Baseline extends AutoCloseable {
        boolean wasEnabled();

        @Override
        void close();
    }

    /** Narrow seam used by the production DJI adapter and host-only state-machine tests. */
    interface Driver {
        Baseline readCanonicalBaseline() throws Exception;

        /** Returns true only for a strict ACK. It does not prove that state changed. */
        boolean attemptSet(Baseline baseline, boolean requestedEnabled) throws Exception;

        /** Performs one fresh, complete inventory and exact opaque-target reconciliation. */
        Readback readCanonicalReadback(Baseline baseline) throws Exception;

        /** Number of SET transitions admitted by the session write gate (0, 1 or 2). */
        int mutationAttempts();

        /** Consumes the DJI gate/session only after an exact baseline has been established. */
        void finishVerifiedSession();
    }

    static final class Outcome {
        private final State state;
        private final boolean baselineEnabled;
        private final boolean forwardAckAccepted;
        private final boolean restoreAckAccepted;
        private final long forwardReadbackAttempts;
        private final long restoreReadbackAttempts;
        private final long recoveryResumeCalls;
        private final boolean restoreSetAdmitted;
        private final long restoreAdmissionCalls;
        private final String forwardTransportFailure;
        private final String restoreTransportFailure;
        private final String lastReadbackFailure;
        private final boolean interruptObserved;

        private Outcome(
                State state,
                boolean baselineEnabled,
                boolean forwardAckAccepted,
                boolean restoreAckAccepted,
                long forwardReadbackAttempts,
                long restoreReadbackAttempts,
                long recoveryResumeCalls,
                boolean restoreSetAdmitted,
                long restoreAdmissionCalls,
                String forwardTransportFailure,
                String restoreTransportFailure,
                String lastReadbackFailure,
                boolean interruptObserved) {
            this.state = state;
            this.baselineEnabled = baselineEnabled;
            this.forwardAckAccepted = forwardAckAccepted;
            this.restoreAckAccepted = restoreAckAccepted;
            this.forwardReadbackAttempts = forwardReadbackAttempts;
            this.restoreReadbackAttempts = restoreReadbackAttempts;
            this.recoveryResumeCalls = recoveryResumeCalls;
            this.restoreSetAdmitted = restoreSetAdmitted;
            this.restoreAdmissionCalls = restoreAdmissionCalls;
            this.forwardTransportFailure = forwardTransportFailure;
            this.restoreTransportFailure = restoreTransportFailure;
            this.lastReadbackFailure = lastReadbackFailure;
            this.interruptObserved = interruptObserved;
        }

        State getState() {
            return state;
        }

        boolean wasBaselineEnabled() {
            return baselineEnabled;
        }

        boolean wasForwardAckAccepted() {
            return forwardAckAccepted;
        }

        boolean wasRestoreAckAccepted() {
            return restoreAckAccepted;
        }

        long getForwardReadbackAttempts() {
            return forwardReadbackAttempts;
        }

        long getRestoreReadbackAttempts() {
            return restoreReadbackAttempts;
        }

        long getRecoveryResumeCalls() {
            return recoveryResumeCalls;
        }

        boolean wasRestoreSetAdmitted() {
            return restoreSetAdmitted;
        }

        long getRestoreAdmissionCalls() {
            return restoreAdmissionCalls;
        }

        boolean isSafelyAtBaseline() {
            return state == State.NOT_DISPATCHED
                    || state == State.RESTORED_NO_CHANGE
                    || state == State.RESTORED;
        }

        boolean isUncertain() {
            return state == State.UNCERTAIN_FORWARD_READBACK
                    || state == State.UNCERTAIN_RESTORE_READBACK;
        }

        boolean requiresExplicitRestore() {
            return state == State.TARGET_CONFIRMED_RESTORE_REQUIRED;
        }

        boolean wasInterruptObserved() {
            return interruptObserved;
        }

        /** Redacted, class-name-only diagnostics; no exception message or license data. */
        String diagnostic() {
            return "state=" + state
                    + "; baseline=" + (baselineEnabled ? "enabled" : "disabled")
                    + "; forwardAck=" + (forwardAckAccepted ? 1 : 0)
                    + "; restoreAck=" + (restoreAckAccepted ? 1 : 0)
                    + "; forwardReads=" + forwardReadbackAttempts
                    + "; restoreReads=" + restoreReadbackAttempts
                    + "; resumeCalls=" + recoveryResumeCalls
                    + "; restoreSetAdmitted=" + (restoreSetAdmitted ? 1 : 0)
                    + "; restoreAdmissionCalls=" + restoreAdmissionCalls
                    + "; forwardTransport=" + safeLabel(forwardTransportFailure)
                    + "; restoreTransport=" + safeLabel(restoreTransportFailure)
                    + "; lastReadback=" + safeLabel(lastReadbackFailure)
                    + "; interruptObserved=" + (interruptObserved ? 1 : 0);
        }

        @Override
        public String toString() {
            return "RidUnlockValidationPulse.Outcome{" + diagnostic() + "}";
        }
    }

    private final Driver driver;
    private Baseline retainedBaseline;
    private RidUnlockControlFlow flow;
    private State state;
    private boolean executed;
    private boolean baselineEnabled;
    private boolean forwardAckAccepted;
    private boolean restoreAckAccepted;
    private boolean restoreSetAdmitted;
    private long restoreAdmissionCalls;
    private long forwardReadbackAttempts;
    private long restoreReadbackAttempts;
    private long recoveryResumeCalls;
    private String forwardTransportFailure;
    private String restoreTransportFailure;
    private String lastReadbackFailure;
    private boolean interruptObserved;

    RidUnlockValidationPulse(
            DjiProtocolClient client,
            DjiProtocolClient.FlysafeGateObservation gateObservation) {
        this(new DjiDriver(client, gateObservation));
    }

    RidUnlockValidationPulse(Driver driver) {
        if (driver == null) {
            throw new IllegalArgumentException("validation-pulse driver is required");
        }
        this.driver = driver;
    }

    /** Executes the initial one-shot pulse. Only uncertain readback may later be resumed. */
    synchronized Outcome execute() throws Exception {
        if (executed) {
            throw new IllegalStateException("RID_UNLOCK_VALIDATION_PULSE_ALREADY_EXECUTED");
        }
        executed = true;

        boolean mutationPossible = false;
        InterruptMemory callInterrupt = new InterruptMemory();
        try {
            retainedBaseline = driver.readCanonicalBaseline();
            if (retainedBaseline == null) {
                throw new IllegalStateException("RID_UNLOCK_BASELINE_MISSING");
            }
            baselineEnabled = retainedBaseline.wasEnabled();
            boolean targetEnabled = !baselineEnabled;
            flow = new RidUnlockControlFlow(baselineEnabled);

            flow.beginForward();
            int forwardMutationsBefore = driver.mutationAttempts();
            if (forwardMutationsBefore != 0) {
                throw new IllegalStateException("RID_UNLOCK_FORWARD_MUTATION_COUNT_NOT_ZERO");
            }
            try {
                forwardAckAccepted = driver.attemptSet(retainedBaseline, targetEnabled);
            } catch (Exception exception) {
                forwardTransportFailure = exceptionClass(exception);
            }
            int forwardMutationsAfter = driver.mutationAttempts();
            mutationPossible = forwardMutationsAfter == 1;
            if (forwardMutationsAfter != 0 && forwardMutationsAfter != 1) {
                throw new IllegalStateException("RID_UNLOCK_FORWARD_MUTATION_COUNT_INVALID");
            }
            if (!mutationPossible) {
                flow.cancelForwardBeforeTransport();
                finishSafe(State.NOT_DISPATCHED);
                return outcome();
            }
            flow.finishForwardTransport(forwardAckAccepted);

            // The initial pulse retains the original policy of up to three forward reads and, if
            // target is proved, a fresh budget of up to three immediate restore reads.
            processForwardBatch(
                    new ReadbackBudget(MAX_READBACK_ATTEMPTS),
                    callInterrupt,
                    false,
                    true);
            return outcome();
        } catch (Exception exception) {
            mutationPossible |= driver.mutationAttempts() > 0;
            if (!mutationPossible) {
                try {
                    driver.finishVerifiedSession();
                } finally {
                    closeBaseline(retainedBaseline);
                    retainedBaseline = null;
                }
            } else if (retainedBaseline != null) {
                // Never clear the only exact-ID handle or consume the session after a possible
                // mutation whose baseline has not been proved.
                makeUnexpectedFailureResumable();
            }
            throw exception;
        } finally {
            restoreInterrupt(callInterrupt);
        }
    }

    /**
     * Runs one manually requested recovery batch with one shared three-inventory budget.
     *
     * <p>This method never issues or retries a SET. From forward uncertainty an exact target
     * readback stops at {@link State#TARGET_CONFIRMED_RESTORE_REQUIRED}; only the separate explicit
     * restore entry can cross the write gate. Restore uncertainty is permanently read-only.</p>
     */
    synchronized Outcome resumeRecovery() {
        if (!executed) {
            throw new IllegalStateException("RID_UNLOCK_VALIDATION_PULSE_NOT_EXECUTED");
        }
        if (retainedBaseline == null
                || (state != State.UNCERTAIN_FORWARD_READBACK
                && state != State.UNCERTAIN_RESTORE_READBACK)) {
            throw new IllegalStateException("RID_UNLOCK_RECOVERY_NOT_AVAILABLE");
        }

        recoveryResumeCalls = incrementSaturated(recoveryResumeCalls);
        InterruptMemory callInterrupt = new InterruptMemory();
        try {
            ReadbackBudget budget = new ReadbackBudget(MAX_READBACK_ATTEMPTS);
            if (state == State.UNCERTAIN_FORWARD_READBACK) {
                processForwardBatch(budget, callInterrupt, true, false);
            } else if (state == State.UNCERTAIN_RESTORE_READBACK) {
                processRestoreBatch(budget, callInterrupt, true);
            }
            return outcome();
        } catch (RuntimeException exception) {
            rememberReadbackFailure(exceptionClass(exception));
            normalizeRecoveryRuntimeFailure();
            return outcome();
        } finally {
            restoreInterrupt(callInterrupt);
        }
    }

    /**
     * Explicitly attempts the one restore after an exact target was confirmed.
     *
     * <p>A pre-admission failure leaves the same state and permits another explicit call because
     * no SET crossed the session mutation gate. Once admitted, the restore is permanently spent;
     * this method immediately uses a fresh three-inventory restore-readback budget and can never
     * dispatch a third SET.</p>
     */
    synchronized Outcome restoreConfirmedTargetOnce() {
        if (!executed || retainedBaseline == null
                || state != State.TARGET_CONFIRMED_RESTORE_REQUIRED) {
            throw new IllegalStateException("RID_UNLOCK_EXPLICIT_RESTORE_NOT_AVAILABLE");
        }

        InterruptMemory callInterrupt = new InterruptMemory();
        try {
            if (attemptUniqueRestore(callInterrupt)) {
                processRestoreBatch(
                        new ReadbackBudget(MAX_READBACK_ATTEMPTS),
                        callInterrupt,
                        false);
            }
            return outcome();
        } catch (RuntimeException exception) {
            restoreTransportFailure = exceptionClass(exception);
            normalizeRecoveryRuntimeFailure();
            return outcome();
        } finally {
            restoreInterrupt(callInterrupt);
        }
    }

    synchronized boolean hasRetainedRecoveryContext() {
        return retainedBaseline != null;
    }

    private void processForwardBatch(
            ReadbackBudget budget,
            InterruptMemory interruptMemory,
            boolean resumed,
            boolean freshRestoreBudget) {
        ReadbackAttempts forward = readBack(
                retainedBaseline, interruptMemory, budget, true);
        forwardReadbackAttempts = addSaturated(
                forwardReadbackAttempts, forward.attempts);
        rememberReadbackFailure(forward.lastFailure);

        RidUnlockControlFlow.Readback reconciled = toFlowReadback(forward.value);
        if (resumed) {
            flow.resumeForwardReadback(reconciled);
        } else {
            flow.reconcileForward(reconciled);
        }

        if (forward.value == null) {
            state = State.UNCERTAIN_FORWARD_READBACK;
            return;
        }
        if (forward.value == Readback.BASELINE) {
            finishSafe(State.RESTORED_NO_CHANGE);
            return;
        }

        if (resumed) {
            // resumeRecovery is strictly read-only. Exact target confirmation is handed to a
            // separate, explicit restore entry rather than crossing into SET from this method.
            state = State.TARGET_CONFIRMED_RESTORE_REQUIRED;
            return;
        }

        if (!attemptUniqueRestore(interruptMemory)) {
            return;
        }
        ReadbackBudget restoreBudget = freshRestoreBudget
                ? new ReadbackBudget(MAX_READBACK_ATTEMPTS) : budget;
        processRestoreBatch(restoreBudget, interruptMemory, false);
    }

    /** Returns true only when the unique restore crossed the session mutation gate. */
    private boolean attemptUniqueRestore(InterruptMemory interruptMemory) {
        if (restoreSetAdmitted) {
            throw new IllegalStateException("RID_UNLOCK_RESTORE_SET_ALREADY_ATTEMPTED");
        }
        flow.beginRestore();
        restoreAdmissionCalls = incrementSaturated(restoreAdmissionCalls);
        int mutationsBefore = driver.mutationAttempts();
        if (mutationsBefore != 1) {
            throw new IllegalStateException("RID_UNLOCK_RESTORE_MUTATION_COUNT_NOT_ONE");
        }
        clearAndRememberInterrupt(interruptMemory);
        try {
            restoreAckAccepted = driver.attemptSet(retainedBaseline, baselineEnabled);
        } catch (Exception exception) {
            restoreTransportFailure = exceptionClass(exception);
        }
        int mutationsAfter = driver.mutationAttempts();
        if (mutationsAfter == 1) {
            // The call failed before the session write gate. This was not a SET retry and did not
            // consume the one permitted restore; a later manual recovery may try admission again.
            flow.cancelRestoreBeforeTransport();
            state = State.TARGET_CONFIRMED_RESTORE_REQUIRED;
            return false;
        }
        if (mutationsAfter != 2) {
            throw new IllegalStateException("RID_UNLOCK_RESTORE_MUTATION_COUNT_INVALID");
        }
        restoreSetAdmitted = true;
        flow.finishRestoreTransport(restoreAckAccepted);
        return true;
    }

    private void processRestoreBatch(
            ReadbackBudget budget,
            InterruptMemory interruptMemory,
            boolean resumed) {
        ReadbackAttempts restore = readBack(
                retainedBaseline, interruptMemory, budget, false);
        restoreReadbackAttempts = addSaturated(
                restoreReadbackAttempts, restore.attempts);
        rememberReadbackFailure(restore.lastFailure);

        RidUnlockControlFlow.Readback reconciled = restore.value == Readback.BASELINE
                ? RidUnlockControlFlow.Readback.BASELINE
                : (restore.value == Readback.TARGET
                ? RidUnlockControlFlow.Readback.TARGET
                : RidUnlockControlFlow.Readback.UNUSABLE);
        if (resumed) {
            flow.resumeRestoreReadback(reconciled);
        } else {
            flow.reconcileRestore(reconciled);
        }

        if (restore.value == Readback.BASELINE) {
            finishSafe(State.RESTORED);
        } else {
            state = State.UNCERTAIN_RESTORE_READBACK;
        }
    }

    private ReadbackAttempts readBack(
            Baseline baseline,
            InterruptMemory interruptMemory,
            ReadbackBudget budget,
            boolean acceptTarget) {
        String lastFailure = null;
        Readback lastValue = null;
        int attempts = 0;
        while (budget.takeOne()) {
            attempts++;
            clearAndRememberInterrupt(interruptMemory);
            try {
                lastValue = driver.readCanonicalReadback(baseline);
                if (lastValue == Readback.BASELINE
                        || (acceptTarget && lastValue == Readback.TARGET)) {
                    return new ReadbackAttempts(lastValue, attempts, lastFailure);
                }
                lastFailure = "NullReadback";
            } catch (Exception exception) {
                lastFailure = exceptionClass(exception);
            }
        }
        return new ReadbackAttempts(lastValue, attempts, lastFailure);
    }

    private Outcome outcome() {
        return new Outcome(
                state,
                baselineEnabled,
                forwardAckAccepted,
                restoreAckAccepted,
                forwardReadbackAttempts,
                restoreReadbackAttempts,
                recoveryResumeCalls,
                restoreSetAdmitted,
                restoreAdmissionCalls,
                forwardTransportFailure,
                restoreTransportFailure,
                lastReadbackFailure,
                interruptObserved);
    }

    private void finishSafe(State verifiedState) {
        flow.close();
        state = verifiedState;
        Baseline baseline = retainedBaseline;
        try {
            driver.finishVerifiedSession();
        } finally {
            closeBaseline(baseline);
            retainedBaseline = null;
        }
    }

    private static void closeBaseline(Baseline baseline) {
        if (baseline != null) {
            baseline.close();
        }
    }

    private void clearAndRememberInterrupt(InterruptMemory memory) {
        boolean observed = Thread.interrupted();
        memory.observed |= observed;
        interruptObserved |= observed;
    }

    private void restoreInterrupt(InterruptMemory memory) {
        interruptObserved |= memory.observed;
        if (memory.observed) {
            Thread.currentThread().interrupt();
        }
    }

    private void rememberReadbackFailure(String failure) {
        if (failure != null && !failure.isEmpty()) {
            lastReadbackFailure = failure;
        }
    }

    private void makeUnexpectedFailureResumable() {
        if (state != null) {
            return;
        }
        RidUnlockControlFlow.State flowState = flow == null ? null : flow.getState();
        if (flowState == RidUnlockControlFlow.State.TARGET_CONFIRMED) {
            state = State.TARGET_CONFIRMED_RESTORE_REQUIRED;
        } else if (flowState == RidUnlockControlFlow.State.RESTORE_DISPATCHED
                || flowState == RidUnlockControlFlow.State.RESTORE_READBACK_REQUIRED) {
            if (flowState == RidUnlockControlFlow.State.RESTORE_DISPATCHED) {
                if (driver.mutationAttempts() == 1) {
                    flow.cancelRestoreBeforeTransport();
                    state = State.TARGET_CONFIRMED_RESTORE_REQUIRED;
                    return;
                }
                flow.finishRestoreTransport(false);
            }
            flow.reconcileRestore(RidUnlockControlFlow.Readback.UNUSABLE);
            state = State.UNCERTAIN_RESTORE_READBACK;
        } else if (flowState == RidUnlockControlFlow.State.FORWARD_DISPATCHED
                || flowState == RidUnlockControlFlow.State.FORWARD_READBACK_REQUIRED) {
            if (flowState == RidUnlockControlFlow.State.FORWARD_DISPATCHED) {
                flow.finishForwardTransport(false);
            }
            flow.reconcileForward(RidUnlockControlFlow.Readback.UNUSABLE);
            state = State.UNCERTAIN_FORWARD_READBACK;
        }
    }

    /** Converts an internal recovery exception into a state that remains safe to invoke later. */
    private void normalizeRecoveryRuntimeFailure() {
        if (retainedBaseline == null) {
            return;
        }
        int mutations = driver.mutationAttempts();
        RidUnlockControlFlow.State flowState = flow == null ? null : flow.getState();
        if (mutations <= 1) {
            if (flowState == RidUnlockControlFlow.State.RESTORE_DISPATCHED) {
                flow.cancelRestoreBeforeTransport();
                flowState = flow.getState();
            }
            if (flowState == RidUnlockControlFlow.State.TARGET_CONFIRMED) {
                state = State.TARGET_CONFIRMED_RESTORE_REQUIRED;
            } else if (state != State.UNCERTAIN_FORWARD_READBACK) {
                state = State.UNCERTAIN_FORWARD_READBACK;
            }
            return;
        }

        restoreSetAdmitted = true;
        if (flowState == RidUnlockControlFlow.State.RESTORE_DISPATCHED) {
            flow.finishRestoreTransport(false);
            flowState = flow.getState();
        }
        if (flowState == RidUnlockControlFlow.State.RESTORE_READBACK_REQUIRED) {
            flow.reconcileRestore(RidUnlockControlFlow.Readback.UNUSABLE);
        }
        state = State.UNCERTAIN_RESTORE_READBACK;
    }

    private static RidUnlockControlFlow.Readback toFlowReadback(Readback readback) {
        if (readback == Readback.BASELINE) {
            return RidUnlockControlFlow.Readback.BASELINE;
        }
        if (readback == Readback.TARGET) {
            return RidUnlockControlFlow.Readback.TARGET;
        }
        return RidUnlockControlFlow.Readback.UNUSABLE;
    }

    private static long incrementSaturated(long value) {
        return value == Long.MAX_VALUE ? value : value + 1L;
    }

    private static long addSaturated(long value, int increment) {
        if (increment < 0) {
            throw new IllegalArgumentException("counter increment must be nonnegative");
        }
        return Long.MAX_VALUE - value < increment ? Long.MAX_VALUE : value + increment;
    }

    private static String exceptionClass(Exception exception) {
        return exception == null ? null : exception.getClass().getSimpleName();
    }

    private static String safeLabel(String value) {
        return value == null || value.isEmpty() ? "none" : value;
    }

    private static final class InterruptMemory {
        boolean observed;
    }

    private static final class ReadbackBudget {
        private int remaining;

        ReadbackBudget(int remaining) {
            if (remaining < 0) {
                throw new IllegalArgumentException("readback budget must be nonnegative");
            }
            this.remaining = remaining;
        }

        boolean takeOne() {
            if (remaining == 0) {
                return false;
            }
            remaining--;
            return true;
        }
    }

    private static final class ReadbackAttempts {
        final Readback value;
        final int attempts;
        final String lastFailure;

        ReadbackAttempts(Readback value, int attempts, String lastFailure) {
            this.value = value;
            this.attempts = attempts;
            this.lastFailure = lastFailure;
        }
    }

    /** Production adapter. It never displays, logs or persists the opaque license identity. */
    private static final class DjiDriver implements Driver {
        private final DjiProtocolClient client;
        private final DjiProtocolClient.FlysafeGateObservation session;
        private final Object sessionMarker;

        DjiDriver(
                DjiProtocolClient client,
                DjiProtocolClient.FlysafeGateObservation session) {
            if (client == null || session == null || !session.allowsModernInventory()) {
                throw new IllegalArgumentException("an admitted FlySafe client/session is required");
            }
            this.client = client;
            this.session = session;
            this.sessionMarker = client.modernFlysafeSessionMarker(session);
        }

        @Override
        public Baseline readCanonicalBaseline() throws Exception {
            FlysafeRidInventory.Result result = readCanonicalInventory();
            boolean retained = false;
            try {
                FlysafeRidInventory.OpaqueRidHandle handle =
                        result.openSingleEligibleHandle(sessionMarker);
                DjiBaseline baseline = new DjiBaseline(result, handle);
                retained = true;
                return baseline;
            } finally {
                if (!retained) {
                    result.close();
                }
            }
        }

        @Override
        public boolean attemptSet(Baseline baseline, boolean requestedEnabled) throws Exception {
            DjiBaseline target = requireBaseline(baseline);
            DjiProtocolClient.FlysafeWritePermit permit =
                    client.issueModernFlysafeWritePermit(
                            session, sessionMarker, target.handle, requestedEnabled);
            try {
                FlysafeLicenseSetCodec.Ack ack =
                        client.setModernFlysafeLicenseEnabled(permit);
                return ack != null && ack.isEnabled() == requestedEnabled;
            } finally {
                permit.close();
            }
        }

        @Override
        public Readback readCanonicalReadback(Baseline baseline) throws Exception {
            DjiBaseline target = requireBaseline(baseline);
            FlysafeRidInventory.Result fresh = readCanonicalInventory();
            try {
                DjiProtocolClient.ReadbackClassification classification =
                        client.classifyModernFlysafeReadback(
                                session, target.handle, fresh);
                return classification == DjiProtocolClient.ReadbackClassification.BASELINE
                        ? Readback.BASELINE : Readback.TARGET;
            } finally {
                fresh.close();
            }
        }

        @Override
        public int mutationAttempts() {
            return session.mutationAttempts();
        }

        @Override
        public void finishVerifiedSession() {
            client.finishModernFlysafeSession(session);
        }

        private FlysafeRidInventory.Result readCanonicalInventory() throws Exception {
            DjiProtocolClient.FlysafeInventoryPass pass =
                    client.beginModernFlysafeInventoryPass(session);
            FlysafeRidInventory.Result result = null;
            boolean completed = false;
            try {
                result = FlysafeRidInventory.query(payload -> {
                    DjiProtocolClient.Reply reply =
                            client.queryModernFlysafeLicense(pass, payload);
                    try {
                        return new FlysafeRidInventory.Response(
                                reply.callbackSuccess, reply.ccode, reply.data);
                    } finally {
                        if (reply.data != null) {
                            Arrays.fill(reply.data, (byte) 0);
                        }
                    }
                });
                client.finishModernFlysafeInventoryPass(pass, result);
                completed = true;
                return result;
            } finally {
                if (!completed) {
                    pass.close();
                    if (result != null) {
                        result.close();
                    }
                }
            }
        }

        private DjiBaseline requireBaseline(Baseline baseline) {
            if (!(baseline instanceof DjiBaseline)) {
                throw new IllegalArgumentException("baseline owner mismatch");
            }
            DjiBaseline target = (DjiBaseline) baseline;
            if (target.closed) {
                throw new IllegalStateException("baseline was cleared");
            }
            return target;
        }
    }

    private static final class DjiBaseline implements Baseline {
        private FlysafeRidInventory.Result result;
        private FlysafeRidInventory.OpaqueRidHandle handle;
        private boolean closed;

        DjiBaseline(
                FlysafeRidInventory.Result result,
                FlysafeRidInventory.OpaqueRidHandle handle) {
            this.result = result;
            this.handle = handle;
        }

        @Override
        public synchronized boolean wasEnabled() {
            requireOpen();
            return handle.wasEnabled();
        }

        @Override
        public synchronized void close() {
            if (closed) {
                return;
            }
            // Result owns and clears its issued child handle.
            result.close();
            result = null;
            handle = null;
            closed = true;
        }

        private void requireOpen() {
            if (closed || result == null || handle == null) {
                throw new IllegalStateException("baseline was cleared");
            }
        }

        @Override
        public synchronized String toString() {
            return "DjiBaseline{sensitive=<redacted>, closed=" + closed + "}";
        }
    }
}
