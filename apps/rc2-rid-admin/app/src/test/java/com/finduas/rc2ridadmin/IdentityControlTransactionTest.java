package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import java.nio.charset.StandardCharsets;

import org.junit.Test;

public final class IdentityControlTransactionTest {
    private static final byte[] ORIGINAL = "TEST-OPID-000001".getBytes(StandardCharsets.US_ASCII);
    private static final byte[] CHANGED = "TEST-OPID-000002".getBytes(StandardCharsets.US_ASCII);

    @Test
    public void successfulReadCannotAdmitEitherWriteLane() {
        for (IdentityControlTransaction.Field field : IdentityControlTransaction.Field.values()) {
            IdentityControlTransaction transaction = new IdentityControlTransaction(field);
            transaction.captureBaseline(field == IdentityControlTransaction.Field.EID
                    ? new byte[] {1} : ORIGINAL);
            assertFalse(IdentityControlTransaction.writesAdmitted());
            assertThrows(IllegalStateException.class, IdentityControlTransaction::requireWriteAdmission);
        }
    }

    @Test
    public void nonRestorableStoredOpidBlocksBothSetAndDeleteBeforeIo() {
        for (int length : new int[] {1, 15, 17, 100}) {
            for (byte[] desired : new byte[][] {CHANGED, {}}) {
                IdentityControlTransaction transaction = opid();
                transaction.captureBaseline(new byte[length]);
                FakeDevice device = new FakeDevice(ORIGINAL);
                assertThrows(IllegalStateException.class, () -> transaction.transition(desired, device));
                assertEquals(0, device.reads);
                assertEquals(0, device.writes);
            }
        }
    }

    @Test
    public void freshNonRestorableValueBlocksWriteEvenWithOlderValidBaseline() {
        IdentityControlTransaction transaction = opid();
        transaction.captureBaseline(ORIGINAL);
        FakeDevice device = new FakeDevice(new byte[17]);
        assertThrows(IllegalStateException.class, () -> transaction.transition(CHANGED, device));
        assertEquals(1, device.reads);
        assertEquals(0, device.writes);
    }

    @Test
    public void emptyOpidCanBeSetAndRestoredWithoutLosingOriginalBaseline() throws Exception {
        IdentityControlTransaction transaction = opid();
        FakeDevice device = new FakeDevice(new byte[0]);
        assertTrue(transaction.transition(CHANGED, device).startsWith("APPLIED_READBACK"));
        assertArrayEquals(new byte[0], transaction.baseline());
        assertTrue(transaction.restore(device).startsWith("RESTORED_READBACK"));
        assertArrayEquals(new byte[0], device.state);
        assertEquals(2, device.writes);
    }

    @Test
    public void deleteRetainsExactOriginalForExplicitRestore() throws Exception {
        IdentityControlTransaction transaction = opid();
        FakeDevice device = new FakeDevice(ORIGINAL);
        assertTrue(transaction.transition(new byte[0], device).startsWith("APPLIED_READBACK"));
        assertTrue(transaction.restore(device).startsWith("RESTORED_READBACK"));
        assertArrayEquals(ORIGINAL, device.state);
    }

    @Test
    public void appliedWriteWithLostAckRequiresRestoreAndBlocksFurtherChanges() throws Exception {
        IdentityControlTransaction transaction = opid();
        FakeDevice device = new FakeDevice(ORIGINAL);
        device.ackFailure = new Exception("vendor echoed TEST-OPID-000002");
        String result = transaction.transition(CHANGED, device);
        assertTrue(result.startsWith("RESTORE_REQUIRED"));
        assertFalse(result.contains("TEST-OPID"));
        assertTrue(transaction.isRestoreRequired());
        assertArrayEquals(CHANGED, device.state);
        assertArrayEquals(ORIGINAL, transaction.baseline());
        assertThrows(IllegalStateException.class, () -> transaction.transition(new byte[0], device));
        assertEquals(1, device.writes);
        device.ackFailure = null;
        assertTrue(transaction.restore(device).startsWith("RESTORED_READBACK"));
        assertArrayEquals(ORIGINAL, device.state);
        assertFalse(transaction.isRestoreRequired());
    }

    @Test
    public void mismatchedReadbackNeverReportsAppliedOrSilentlyRetries() throws Exception {
        IdentityControlTransaction transaction = opid();
        FakeDevice device = new FakeDevice(ORIGINAL);
        device.ignoreWrite = true;
        assertTrue(transaction.transition(CHANGED, device).startsWith("RESTORE_REQUIRED"));
        assertEquals(1, device.writes);
        assertTrue(transaction.isRestoreRequired());
    }

    @Test
    public void readbackFailureRetainsBaselineAndRedactsException() throws Exception {
        IdentityControlTransaction transaction = opid();
        FakeDevice device = new FakeDevice(ORIGINAL);
        device.failReadAt = 2;
        String result = transaction.transition(CHANGED, device);
        assertTrue(result.startsWith("RESTORE_REQUIRED"));
        assertFalse(result.contains("TEST-OPID"));
        assertArrayEquals(ORIGINAL, transaction.baseline());
        assertEquals(1, device.writes);
    }

    @Test
    public void lostRestoreAckDoesNotClearRequiredStateEvenIfDeviceChanged() throws Exception {
        IdentityControlTransaction transaction = opid();
        FakeDevice device = new FakeDevice(ORIGINAL);
        transaction.transition(CHANGED, device);
        device.ackFailure = new Exception("unknown ACK");
        assertTrue(transaction.restore(device).startsWith("RESTORE_REQUIRED"));
        assertTrue(transaction.isRestoreRequired());
        assertArrayEquals(ORIGINAL, device.state);
        assertEquals(2, device.writes);
    }

    @Test
    public void eidRestoreMismatchAlsoRequiresRecovery() throws Exception {
        IdentityControlTransaction transaction = new IdentityControlTransaction(
                IdentityControlTransaction.Field.EID);
        FakeDevice device = new FakeDevice(new byte[] {1});
        assertTrue(transaction.transition(new byte[] {0}, device).startsWith("APPLIED_READBACK"));
        device.ignoreWrite = true;
        assertTrue(transaction.restore(device).startsWith("RESTORE_REQUIRED"));
        assertTrue(transaction.isRestoreRequired());
    }

    @Test
    public void interruptedWriteDoesNotLoseRestoreObligationOrInterruptFlag() throws Exception {
        IdentityControlTransaction transaction = opid();
        FakeDevice device = new FakeDevice(ORIGINAL);
        device.ackFailure = new InterruptedException();
        try {
            assertTrue(transaction.transition(CHANGED, device).startsWith("RESTORE_REQUIRED"));
            assertTrue(Thread.currentThread().isInterrupted());
            assertTrue(transaction.isRestoreRequired());
        } finally {
            Thread.interrupted();
        }
    }

    @Test
    public void baselineCopiesCannotBeMutatedByCallerOrLaterObservations() {
        IdentityControlTransaction transaction = opid();
        byte[] input = ORIGINAL.clone();
        transaction.captureBaseline(input);
        input[0] = 0;
        transaction.baseline()[1] = 0;
        transaction.captureBaseline(CHANGED);
        assertArrayEquals(ORIGINAL, transaction.baseline());
    }

    @Test
    public void missingRestoreBaselineNeverSendsAWrite() {
        FakeDevice device = new FakeDevice(ORIGINAL);
        assertThrows(IllegalStateException.class, () -> opid().restore(device));
        assertEquals(0, device.writes);
    }

    @Test
    public void malformedEidBaselineBlocksTransition() {
        IdentityControlTransaction transaction = new IdentityControlTransaction(
                IdentityControlTransaction.Field.EID);
        FakeDevice device = new FakeDevice(new byte[] {2});
        assertThrows(IllegalStateException.class, () -> transaction.transition(new byte[] {0}, device));
        assertEquals(0, device.writes);
    }

    @Test
    public void alreadyMatchingValueRequiresNoWrite() throws Exception {
        FakeDevice device = new FakeDevice(ORIGINAL);
        assertTrue(opid().transition(ORIGINAL, device).startsWith("UNCHANGED_READBACK"));
        assertEquals(0, device.writes);
    }

    @Test
    public void successfulForwardWriteStillBlocksASecondTransitionUntilRestored() throws Exception {
        IdentityControlTransaction transaction = opid();
        FakeDevice device = new FakeDevice(ORIGINAL);
        transaction.transition(CHANGED, device);
        assertTrue(transaction.isRestoreRequired());
        assertThrows(IllegalStateException.class, () -> transaction.transition(new byte[0], device));
        assertEquals(1, device.writes);
        transaction.restore(device);
        assertFalse(transaction.isRestoreRequired());
        assertTrue(transaction.transition(new byte[0], device).startsWith("APPLIED_READBACK"));
    }

    @Test
    public void externalBaselineChangeBlocksBothTransitionAndStaleRestore() {
        IdentityControlTransaction transaction = opid();
        transaction.captureBaseline(ORIGINAL);
        FakeDevice device = new FakeDevice(CHANGED);
        assertThrows(IllegalStateException.class, () -> transaction.transition(new byte[0], device));
        assertThrows(IllegalStateException.class, () -> transaction.restore(device));
        assertEquals(0, device.writes);
    }

    @Test
    public void restoreDoesNotOverwriteAnUnrelatedExternalChange() throws Exception {
        IdentityControlTransaction transaction = opid();
        FakeDevice device = new FakeDevice(ORIGINAL);
        transaction.transition(CHANGED, device);
        device.state = "TEST-OPID-000003".getBytes(StandardCharsets.US_ASCII);
        assertThrows(IllegalStateException.class, () -> transaction.restore(device));
        assertEquals(1, device.writes);
    }

    @Test
    public void alreadyRestoredBaselineClearsObligationWithoutAnotherWrite() throws Exception {
        IdentityControlTransaction transaction = opid();
        FakeDevice device = new FakeDevice(ORIGINAL);
        transaction.transition(CHANGED, device);
        device.state = ORIGINAL.clone();
        assertTrue(transaction.restore(device).startsWith("BASELINE_READBACK_NO_WRITE"));
        assertFalse(transaction.isRestoreRequired());
        assertEquals(1, device.writes);
    }

    private static IdentityControlTransaction opid() {
        return new IdentityControlTransaction(IdentityControlTransaction.Field.OPERATOR_ID);
    }

    private static final class FakeDevice implements IdentityControlTransaction.DeviceState {
        byte[] state;
        int reads;
        int writes;
        int failReadAt = -1;
        boolean ignoreWrite;
        Exception ackFailure;

        FakeDevice(byte[] state) {
            this.state = state.clone();
        }

        @Override
        public byte[] read() throws Exception {
            reads++;
            if (reads == failReadAt) {
                throw new Exception("vendor echoed TEST-OPID-000001");
            }
            return state.clone();
        }

        @Override
        public void write(byte[] desired) throws Exception {
            writes++;
            if (!ignoreWrite) {
                state = desired.clone();
            }
            if (ackFailure != null) {
                throw ackFailure;
            }
        }
    }
}
