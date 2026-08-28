package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import java.util.ArrayDeque;
import java.util.Deque;

import org.junit.After;
import org.junit.Test;

public final class RidUnlockValidationPulseTest {
    @After
    public void clearInterruptFlag() {
        Thread.interrupted();
    }

    @Test
    public void targetReadbackCausesOneImmediateRestoreAndFinalBaselineProof() throws Exception {
        FakeDriver driver = new FakeDriver(false);
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.BASELINE));

        RidUnlockValidationPulse pulse = new RidUnlockValidationPulse(driver);
        RidUnlockValidationPulse.Outcome outcome = pulse.execute();

        assertEquals(RidUnlockValidationPulse.State.RESTORED, outcome.getState());
        assertTrue(outcome.isSafelyAtBaseline());
        assertEquals(2, driver.setCalls);
        assertEquals(1, driver.forwardSetCalls);
        assertEquals(1, driver.restoreSetCalls);
        assertEquals(2, driver.readbackCalls);
        assertTrue(driver.baseline.closed);
        assertEquals(1, driver.finishCalls);
        assertFalse(pulse.hasRetainedRecoveryContext());
    }

    @Test
    public void ackNeverOverridesFreshBaselineReadback() throws Exception {
        FakeDriver driver = new FakeDriver(true);
        driver.forwardAck = true;
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.BASELINE));

        RidUnlockValidationPulse.Outcome outcome =
                new RidUnlockValidationPulse(driver).execute();

        assertEquals(RidUnlockValidationPulse.State.RESTORED_NO_CHANGE, outcome.getState());
        assertTrue(outcome.wasForwardAckAccepted());
        assertEquals(1, driver.setCalls);
        assertEquals(0, driver.restoreSetCalls);
        assertEquals(1, driver.finishCalls);
    }

    @Test
    public void transportExceptionsAfterMutationStillReadBackAndRestoreWithoutSetRetry()
            throws Exception {
        FakeDriver driver = new FakeDriver(false);
        driver.forwardSetFailure = new CheckedFailure();
        driver.restoreSetFailure = new CheckedFailure();
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.BASELINE));

        RidUnlockValidationPulse.Outcome outcome =
                new RidUnlockValidationPulse(driver).execute();

        assertEquals(RidUnlockValidationPulse.State.RESTORED, outcome.getState());
        assertFalse(outcome.wasForwardAckAccepted());
        assertFalse(outcome.wasRestoreAckAccepted());
        assertEquals(2, driver.setCalls);
        assertTrue(outcome.diagnostic().contains("CheckedFailure"));
        assertFalse(outcome.diagnostic().contains("secret-message"));
    }

    @Test
    public void eachReadbackStageGetsAtMostThreeFullInventoryAttempts() throws Exception {
        FakeDriver driver = new FakeDriver(false);
        driver.readbacks.add(Event.failure());
        driver.readbacks.add(Event.failure());
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        driver.readbacks.add(Event.failure());
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.BASELINE));

        RidUnlockValidationPulse.Outcome outcome =
                new RidUnlockValidationPulse(driver).execute();

        assertEquals(RidUnlockValidationPulse.State.RESTORED, outcome.getState());
        assertEquals(3, outcome.getForwardReadbackAttempts());
        assertEquals(3, outcome.getRestoreReadbackAttempts());
        assertEquals(6, driver.readbackCalls);
        assertEquals(2, driver.setCalls);
    }

    @Test
    public void threeUnusableForwardReadsRetainHandleAndDoNotRestoreOrFinish() throws Exception {
        FakeDriver driver = new FakeDriver(false);
        driver.readbacks.add(Event.failure());
        driver.readbacks.add(Event.failure());
        driver.readbacks.add(Event.failure());

        RidUnlockValidationPulse pulse = new RidUnlockValidationPulse(driver);
        RidUnlockValidationPulse.Outcome outcome = pulse.execute();

        assertEquals(
                RidUnlockValidationPulse.State.UNCERTAIN_FORWARD_READBACK,
                outcome.getState());
        assertTrue(outcome.isUncertain());
        assertEquals(1, driver.setCalls);
        assertEquals(0, driver.restoreSetCalls);
        assertEquals(3, driver.readbackCalls);
        assertFalse(driver.baseline.closed);
        assertEquals(0, driver.finishCalls);
        assertTrue(pulse.hasRetainedRecoveryContext());
        assertThrows(IllegalStateException.class, pulse::execute);
    }

    @Test
    public void threeNonBaselineRestoreReadsNeverCauseAnAutomaticThirdSet() throws Exception {
        FakeDriver driver = new FakeDriver(false);
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        driver.readbacks.add(Event.failure());
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));

        RidUnlockValidationPulse pulse = new RidUnlockValidationPulse(driver);
        RidUnlockValidationPulse.Outcome outcome = pulse.execute();

        assertEquals(
                RidUnlockValidationPulse.State.UNCERTAIN_RESTORE_READBACK,
                outcome.getState());
        assertEquals(2, driver.setCalls);
        assertEquals(3, outcome.getRestoreReadbackAttempts());
        assertFalse(driver.baseline.closed);
        assertEquals(0, driver.finishCalls);
        assertTrue(pulse.hasRetainedRecoveryContext());
    }

    @Test
    public void cancellationStyleInterruptAfterMutationCannotAbortRecovery() throws Exception {
        FakeDriver driver = new FakeDriver(false);
        driver.interruptAndFailForwardSet = true;
        driver.requireClearInterruptDuringReadback = true;
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.BASELINE));

        RidUnlockValidationPulse.Outcome outcome =
                new RidUnlockValidationPulse(driver).execute();

        assertEquals(RidUnlockValidationPulse.State.RESTORED, outcome.getState());
        assertEquals(2, driver.setCalls);
        assertTrue(outcome.wasInterruptObserved());
        assertTrue(Thread.currentThread().isInterrupted());
    }

    @Test
    public void failureBeforeMutationDoesNotReadBackAndClearsSafeBaseline() throws Exception {
        FakeDriver driver = new FakeDriver(false);
        driver.failForwardBeforeRecovery = true;

        RidUnlockValidationPulse pulse = new RidUnlockValidationPulse(driver);
        RidUnlockValidationPulse.Outcome outcome = pulse.execute();

        assertEquals(RidUnlockValidationPulse.State.NOT_DISPATCHED, outcome.getState());
        assertEquals(1, driver.setCalls);
        assertEquals(0, driver.readbackCalls);
        assertEquals(1, driver.finishCalls);
        assertTrue(driver.baseline.closed);
        assertFalse(pulse.hasRetainedRecoveryContext());
    }

    @Test
    public void baselineFailureFinishesUnmutatedSessionAndPulseCannotBeReused() throws Exception {
        FakeDriver driver = new FakeDriver(false);
        driver.baselineFailure = new CheckedFailure();
        RidUnlockValidationPulse pulse = new RidUnlockValidationPulse(driver);

        assertThrows(CheckedFailure.class, pulse::execute);
        assertEquals(1, driver.finishCalls);
        assertFalse(pulse.hasRetainedRecoveryContext());
        assertThrows(IllegalStateException.class, pulse::execute);
    }

    @Test
    public void forwardUncertainCanResumeToBaselineAndCloseResources() throws Exception {
        FakeDriver driver = new FakeDriver(false);
        addFailures(driver, 3);
        RidUnlockValidationPulse pulse = new RidUnlockValidationPulse(driver);
        assertEquals(RidUnlockValidationPulse.State.UNCERTAIN_FORWARD_READBACK,
                pulse.execute().getState());

        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.BASELINE));
        RidUnlockValidationPulse.Outcome recovered = pulse.resumeRecovery();

        assertEquals(RidUnlockValidationPulse.State.RESTORED_NO_CHANGE,
                recovered.getState());
        assertEquals(4L, recovered.getForwardReadbackAttempts());
        assertEquals(1L, recovered.getRecoveryResumeCalls());
        assertEquals(1, driver.setCalls);
        assertEquals(1, driver.finishCalls);
        assertTrue(driver.baseline.closed);
        assertFalse(pulse.hasRetainedRecoveryContext());
        assertThrows(IllegalStateException.class, pulse::resumeRecovery);
    }

    @Test
    public void forwardResumeTargetIsStrictlyReadOnlyUntilExplicitRestore() throws Exception {
        FakeDriver driver = new FakeDriver(false);
        addFailures(driver, 3);
        RidUnlockValidationPulse pulse = new RidUnlockValidationPulse(driver);
        pulse.execute();

        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        RidUnlockValidationPulse.Outcome confirmed = pulse.resumeRecovery();

        assertEquals(RidUnlockValidationPulse.State.TARGET_CONFIRMED_RESTORE_REQUIRED,
                confirmed.getState());
        assertTrue(confirmed.requiresExplicitRestore());
        assertFalse(confirmed.wasRestoreSetAdmitted());
        assertEquals(0L, confirmed.getRestoreAdmissionCalls());
        assertEquals(1, driver.setCalls);
        assertEquals(1, driver.admittedMutations);
        assertThrows(IllegalStateException.class, pulse::resumeRecovery);

        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.BASELINE));
        RidUnlockValidationPulse.Outcome recovered =
                pulse.restoreConfirmedTargetOnce();
        assertEquals(RidUnlockValidationPulse.State.RESTORED, recovered.getState());
        assertTrue(recovered.wasRestoreSetAdmitted());
        assertEquals(1L, recovered.getRestoreAdmissionCalls());
        assertEquals(2, driver.setCalls);
        assertEquals(2, driver.admittedMutations);
        assertEquals(2, driver.readbackCalls - 3);
    }

    @Test
    public void readOnlyResumeAndExplicitRestoreHaveSeparateThreeInventoryBudgets()
            throws Exception {
        FakeDriver driver = new FakeDriver(false);
        addFailures(driver, 3);
        RidUnlockValidationPulse pulse = new RidUnlockValidationPulse(driver);
        pulse.execute();

        driver.readbacks.add(Event.failure());
        driver.readbacks.add(Event.failure());
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        RidUnlockValidationPulse.Outcome exhausted = pulse.resumeRecovery();

        assertEquals(RidUnlockValidationPulse.State.TARGET_CONFIRMED_RESTORE_REQUIRED,
                exhausted.getState());
        assertEquals(6L, exhausted.getForwardReadbackAttempts());
        assertEquals(0L, exhausted.getRestoreReadbackAttempts());
        assertEquals(6, driver.readbackCalls);
        assertEquals(1, driver.setCalls);

        driver.readbacks.add(Event.failure());
        driver.readbacks.add(Event.failure());
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.BASELINE));
        RidUnlockValidationPulse.Outcome recovered =
                pulse.restoreConfirmedTargetOnce();
        assertEquals(RidUnlockValidationPulse.State.RESTORED, recovered.getState());
        assertEquals(1L, recovered.getRecoveryResumeCalls());
        assertEquals(3L, recovered.getRestoreReadbackAttempts());
        assertEquals(2, driver.setCalls);
    }

    @Test
    public void restoreUncertainCanResumeIndefinitelyWithoutThirdSet() throws Exception {
        FakeDriver driver = new FakeDriver(false);
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        RidUnlockValidationPulse pulse = new RidUnlockValidationPulse(driver);
        assertEquals(RidUnlockValidationPulse.State.UNCERTAIN_RESTORE_READBACK,
                pulse.execute().getState());
        assertThrows(IllegalStateException.class, pulse::restoreConfirmedTargetOnce);

        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        assertEquals(RidUnlockValidationPulse.State.UNCERTAIN_RESTORE_READBACK,
                pulse.resumeRecovery().getState());
        assertEquals(2, driver.setCalls);

        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.BASELINE));
        RidUnlockValidationPulse.Outcome recovered = pulse.resumeRecovery();
        assertEquals(RidUnlockValidationPulse.State.RESTORED, recovered.getState());
        assertEquals(7L, recovered.getRestoreReadbackAttempts());
        assertEquals(2, driver.setCalls);
    }

    @Test
    public void preAdmissionRestoreFailureStaysPendingAndCanAdmitOnceLater()
            throws Exception {
        FakeDriver driver = new FakeDriver(false);
        driver.restoreFailuresBeforeAdmission = 1;
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.TARGET));
        RidUnlockValidationPulse pulse = new RidUnlockValidationPulse(driver);

        RidUnlockValidationPulse.Outcome pending = pulse.execute();
        assertEquals(
                RidUnlockValidationPulse.State.TARGET_CONFIRMED_RESTORE_REQUIRED,
                pending.getState());
        assertFalse(pending.wasRestoreSetAdmitted());
        assertEquals(1L, pending.getRestoreAdmissionCalls());
        assertEquals(1, driver.admittedMutations);
        assertTrue(pulse.hasRetainedRecoveryContext());

        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.BASELINE));
        RidUnlockValidationPulse.Outcome recovered =
                pulse.restoreConfirmedTargetOnce();
        assertEquals(RidUnlockValidationPulse.State.RESTORED, recovered.getState());
        assertTrue(recovered.wasRestoreSetAdmitted());
        assertEquals(2L, recovered.getRestoreAdmissionCalls());
        assertEquals(2, driver.admittedMutations);
        assertEquals(3, driver.setCalls);
    }

    @Test
    public void resumeClearsInterruptForRecoveryAndReassertsItAfterward() throws Exception {
        FakeDriver driver = new FakeDriver(false);
        addFailures(driver, 3);
        driver.requireClearInterruptDuringReadback = true;
        RidUnlockValidationPulse pulse = new RidUnlockValidationPulse(driver);
        pulse.execute();
        driver.readbacks.add(Event.value(RidUnlockValidationPulse.Readback.BASELINE));

        Thread.currentThread().interrupt();
        RidUnlockValidationPulse.Outcome recovered = pulse.resumeRecovery();

        assertEquals(RidUnlockValidationPulse.State.RESTORED_NO_CHANGE,
                recovered.getState());
        assertTrue(recovered.wasInterruptObserved());
        assertTrue(Thread.currentThread().isInterrupted());
    }

    @Test
    public void recoveryCannotStartBeforeInitialExecution() {
        RidUnlockValidationPulse pulse =
                new RidUnlockValidationPulse(new FakeDriver(false));
        assertThrows(IllegalStateException.class, pulse::resumeRecovery);
    }

    private static void addFailures(FakeDriver driver, int count) {
        for (int index = 0; index < count; index++) {
            driver.readbacks.add(Event.failure());
        }
    }

    private static final class FakeBaseline implements RidUnlockValidationPulse.Baseline {
        final boolean enabled;
        boolean closed;

        FakeBaseline(boolean enabled) {
            this.enabled = enabled;
        }

        @Override
        public boolean wasEnabled() {
            if (closed) {
                throw new IllegalStateException("closed");
            }
            return enabled;
        }

        @Override
        public void close() {
            closed = true;
        }
    }

    private static final class FakeDriver implements RidUnlockValidationPulse.Driver {
        final FakeBaseline baseline;
        final Deque<Event> readbacks = new ArrayDeque<>();
        boolean forwardAck = true;
        boolean restoreAck = true;
        Exception baselineFailure;
        Exception forwardSetFailure;
        Exception restoreSetFailure;
        boolean failForwardBeforeRecovery;
        int restoreFailuresBeforeAdmission;
        boolean interruptAndFailForwardSet;
        boolean requireClearInterruptDuringReadback;
        int admittedMutations;
        int setCalls;
        int forwardSetCalls;
        int restoreSetCalls;
        int readbackCalls;
        int finishCalls;

        FakeDriver(boolean baselineEnabled) {
            baseline = new FakeBaseline(baselineEnabled);
        }

        @Override
        public RidUnlockValidationPulse.Baseline readCanonicalBaseline() throws Exception {
            if (baselineFailure != null) {
                throw baselineFailure;
            }
            return baseline;
        }

        @Override
        public boolean attemptSet(
                RidUnlockValidationPulse.Baseline candidate,
                boolean requestedEnabled) throws Exception {
            if (candidate != baseline || baseline.closed) {
                throw new IllegalStateException("baseline mismatch");
            }
            setCalls++;
            if (requestedEnabled != baseline.enabled) {
                forwardSetCalls++;
                if (failForwardBeforeRecovery) {
                    throw new CheckedFailure();
                }
                admittedMutations = 1;
                if (interruptAndFailForwardSet) {
                    Thread.currentThread().interrupt();
                    throw new CheckedFailure();
                }
                if (forwardSetFailure != null) {
                    throw forwardSetFailure;
                }
                return forwardAck;
            }
            restoreSetCalls++;
            if (restoreFailuresBeforeAdmission > 0) {
                restoreFailuresBeforeAdmission--;
                throw new CheckedFailure();
            }
            admittedMutations = 2;
            if (restoreSetFailure != null) {
                throw restoreSetFailure;
            }
            return restoreAck;
        }

        @Override
        public RidUnlockValidationPulse.Readback readCanonicalReadback(
                RidUnlockValidationPulse.Baseline candidate) throws Exception {
            if (candidate != baseline || baseline.closed) {
                throw new IllegalStateException("baseline mismatch");
            }
            if (requireClearInterruptDuringReadback
                    && Thread.currentThread().isInterrupted()) {
                throw new AssertionError("interrupt was not cleared for recovery readback");
            }
            readbackCalls++;
            Event event = readbacks.removeFirst();
            if (event.failure != null) {
                throw event.failure;
            }
            return event.value;
        }

        @Override
        public int mutationAttempts() {
            return admittedMutations;
        }

        @Override
        public void finishVerifiedSession() {
            finishCalls++;
        }
    }

    private static final class Event {
        final RidUnlockValidationPulse.Readback value;
        final Exception failure;

        private Event(RidUnlockValidationPulse.Readback value, Exception failure) {
            this.value = value;
            this.failure = failure;
        }

        static Event value(RidUnlockValidationPulse.Readback value) {
            return new Event(value, null);
        }

        static Event failure() {
            return new Event(null, new CheckedFailure());
        }
    }

    private static final class CheckedFailure extends Exception {
        CheckedFailure() {
            super("secret-message-must-not-be-rendered");
        }
    }
}
