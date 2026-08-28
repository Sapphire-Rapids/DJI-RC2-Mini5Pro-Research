package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.fail;

import org.junit.Test;

public final class RidUnlockControlFlowTest {
    @Test
    public void strictAckStillRequiresForwardAndRestoreReadback() {
        RidUnlockControlFlow flow = new RidUnlockControlFlow(false);
        assertFalse(flow.getBaselineEnabled());
        assertTrue(flow.getTargetEnabled());

        flow.beginForward();
        flow.finishForwardTransport(true);
        assertTrue(flow.wasForwardAckAccepted());
        assertEquals(RidUnlockControlFlow.State.FORWARD_READBACK_REQUIRED, flow.getState());
        assertFalse(flow.isSafelyAtBaseline());

        flow.reconcileForward(RidUnlockControlFlow.Readback.TARGET);
        assertTrue(flow.needsImmediateRestore());
        flow.beginRestore();
        flow.finishRestoreTransport(true);
        assertEquals(RidUnlockControlFlow.State.RESTORE_READBACK_REQUIRED, flow.getState());
        flow.reconcileRestore(RidUnlockControlFlow.Readback.BASELINE);
        assertTrue(flow.isSafelyAtBaseline());
        flow.close();
        assertEquals(RidUnlockControlFlow.State.CLOSED, flow.getState());
    }

    @Test
    public void failedAckCanStillBeReconciledAndRestored() {
        RidUnlockControlFlow flow = new RidUnlockControlFlow(true);
        flow.beginForward();
        flow.finishForwardTransport(false);
        assertFalse(flow.wasForwardAckAccepted());
        flow.reconcileForward(RidUnlockControlFlow.Readback.TARGET);

        flow.beginRestore();
        flow.finishRestoreTransport(false);
        flow.reconcileRestore(RidUnlockControlFlow.Readback.BASELINE);
        assertEquals(RidUnlockControlFlow.State.RESTORED, flow.getState());
    }

    @Test
    public void baselineReadbackAfterForwardNeverRetriesSet() {
        RidUnlockControlFlow flow = new RidUnlockControlFlow(false);
        flow.beginForward();
        flow.finishForwardTransport(false);
        flow.reconcileForward(RidUnlockControlFlow.Readback.BASELINE);
        assertEquals(RidUnlockControlFlow.State.RESTORED_NO_CHANGE, flow.getState());
        assertTrue(flow.isSafelyAtBaseline());
        expectIllegal(flow::beginForward);
        expectIllegal(flow::beginRestore);
    }

    @Test
    public void provenPreTransportCancellationReturnsToClosableBaseline() {
        RidUnlockControlFlow flow = new RidUnlockControlFlow(false);
        flow.beginForward();
        flow.cancelForwardBeforeTransport();
        assertEquals(RidUnlockControlFlow.State.RESTORED_NO_CHANGE, flow.getState());
        assertTrue(flow.isSafelyAtBaseline());
        flow.close();
        assertEquals(RidUnlockControlFlow.State.CLOSED, flow.getState());
    }

    @Test
    public void unusableForwardReadbackLocksWritesAndClose() {
        RidUnlockControlFlow flow = new RidUnlockControlFlow(false);
        flow.beginForward();
        flow.finishForwardTransport(true);
        flow.reconcileForward(RidUnlockControlFlow.Readback.UNUSABLE);
        assertTrue(flow.isTerminalUncertain());
        expectIllegal(flow::beginForward);
        expectIllegal(flow::beginRestore);
        expectIllegal(flow::close);
    }

    @Test
    public void targetStillPresentAfterRestoreLocksWithoutRetry() {
        RidUnlockControlFlow flow = new RidUnlockControlFlow(false);
        flow.beginForward();
        flow.finishForwardTransport(true);
        flow.reconcileForward(RidUnlockControlFlow.Readback.TARGET);
        flow.beginRestore();
        flow.finishRestoreTransport(true);
        flow.reconcileRestore(RidUnlockControlFlow.Readback.TARGET);
        assertEquals(RidUnlockControlFlow.State.UNCERTAIN, flow.getState());
        expectIllegal(flow::beginRestore);
    }

    @Test
    public void forwardUncertaintyCanResumeReadOnlyToEitherExactState() {
        RidUnlockControlFlow baseline = new RidUnlockControlFlow(false);
        baseline.beginForward();
        baseline.finishForwardTransport(false);
        baseline.reconcileForward(RidUnlockControlFlow.Readback.UNUSABLE);
        baseline.resumeForwardReadback(RidUnlockControlFlow.Readback.BASELINE);
        assertEquals(RidUnlockControlFlow.State.RESTORED_NO_CHANGE, baseline.getState());

        RidUnlockControlFlow target = new RidUnlockControlFlow(false);
        target.beginForward();
        target.finishForwardTransport(false);
        target.reconcileForward(RidUnlockControlFlow.Readback.UNUSABLE);
        target.resumeForwardReadback(RidUnlockControlFlow.Readback.TARGET);
        assertEquals(RidUnlockControlFlow.State.TARGET_CONFIRMED, target.getState());
        target.beginRestore();
    }

    @Test
    public void restoreUncertaintyCanResumeReadOnlyUntilBaseline() {
        RidUnlockControlFlow flow = new RidUnlockControlFlow(false);
        flow.beginForward();
        flow.finishForwardTransport(true);
        flow.reconcileForward(RidUnlockControlFlow.Readback.TARGET);
        flow.beginRestore();
        flow.finishRestoreTransport(false);
        flow.reconcileRestore(RidUnlockControlFlow.Readback.TARGET);
        flow.resumeRestoreReadback(RidUnlockControlFlow.Readback.UNUSABLE);
        flow.resumeRestoreReadback(RidUnlockControlFlow.Readback.BASELINE);
        assertEquals(RidUnlockControlFlow.State.RESTORED, flow.getState());
        flow.close();
    }

    @Test
    public void restoreRejectedBeforeTransportRemainsTheSameUniqueRestore() {
        RidUnlockControlFlow flow = new RidUnlockControlFlow(false);
        flow.beginForward();
        flow.finishForwardTransport(true);
        flow.reconcileForward(RidUnlockControlFlow.Readback.TARGET);
        flow.beginRestore();
        flow.cancelRestoreBeforeTransport();
        assertEquals(RidUnlockControlFlow.State.TARGET_CONFIRMED, flow.getState());
        flow.beginRestore();
        flow.finishRestoreTransport(true);
        assertEquals(RidUnlockControlFlow.State.RESTORE_READBACK_REQUIRED, flow.getState());
    }

    @Test
    public void cannotSkipTransportOrReadbackPhases() {
        RidUnlockControlFlow flow = new RidUnlockControlFlow(false);
        expectIllegal(() -> flow.reconcileForward(RidUnlockControlFlow.Readback.TARGET));
        flow.beginForward();
        expectIllegal(flow::beginRestore);
        expectIllegal(() -> flow.reconcileForward(RidUnlockControlFlow.Readback.TARGET));
        flow.finishForwardTransport(true);
        expectIllegal(flow::beginForward);
        expectIllegal(flow::beginRestore);
    }

    @Test
    public void closeOnlyFromVerifiedBaselineStates() {
        RidUnlockControlFlow untouched = new RidUnlockControlFlow(true);
        untouched.close();
        assertEquals(RidUnlockControlFlow.State.CLOSED, untouched.getState());
        expectIllegal(untouched::close);

        RidUnlockControlFlow active = new RidUnlockControlFlow(true);
        active.beginForward();
        expectIllegal(active::close);
    }

    private static void expectIllegal(Runnable runnable) {
        try {
            runnable.run();
            fail("expected IllegalStateException");
        } catch (IllegalStateException expected) {
            // Expected.
        }
    }
}
