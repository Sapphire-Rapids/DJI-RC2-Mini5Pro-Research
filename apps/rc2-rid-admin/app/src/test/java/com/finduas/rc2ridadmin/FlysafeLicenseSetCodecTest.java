package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public final class FlysafeLicenseSetCodecTest {
    @Test
    public void buildsExactV3V4EnableAndDisablePayloads() {
        byte[] target = new byte[] {(byte) 0xcd, (byte) 0xab, 0x34, 0x12};
        assertArrayEquals(
                new byte[] {0, (byte) 0xcd, (byte) 0xab, 0x34, 0x12, 1, 0},
                FlysafeLicenseSetCodec.buildPayload(target, true));
        assertArrayEquals(
                new byte[] {0, (byte) 0xcd, (byte) 0xab, 0x34, 0x12, 2, 0},
                FlysafeLicenseSetCodec.buildPayload(target, false));
        assertArrayEquals(
                new byte[] {(byte) 0xcd, (byte) 0xab, 0x34, 0x12},
                target);
    }

    @Test
    public void rejectsMissingWrongWidthAndZeroTargetsWithoutRenderingThem() {
        for (byte[] target : new byte[][] {
                null,
                {},
                {1, 2, 3},
                {1, 2, 3, 4, 5},
                {0, 0, 0, 0}
        }) {
            IllegalArgumentException failure = assertThrows(
                    IllegalArgumentException.class,
                    () -> FlysafeLicenseSetCodec.buildPayload(target, true));
            assertFalse(failure.getMessage().contains("1234ABCD"));
            assertFalse(failure.getMessage().contains("CDAB3412"));
        }
    }

    @Test
    public void acceptsOnlyExactSuccessfulAckForRequestedState() {
        FlysafeLicenseSetCodec.Ack enabled = FlysafeLicenseSetCodec.decodeAck(
                true, 0, new byte[] {1, 0x7e}, true);
        FlysafeLicenseSetCodec.Ack disabled = FlysafeLicenseSetCodec.decodeAck(
                true, 0, new byte[] {1, 0x7d}, false);
        assertTrue(enabled.isEnabled());
        assertFalse(disabled.isEnabled());
    }

    @Test
    public void everyDocumentedNonzeroSetResultCodeIsAnError() {
        for (int ccode = 1; ccode <= 5; ccode++) {
            final int testedCcode = ccode;
            assertThrows(FlysafeLicenseSetCodec.ProtocolException.class,
                    () -> FlysafeLicenseSetCodec.decodeAck(
                            true, testedCcode, new byte[] {1, 2}, true));
        }
        assertThrows(FlysafeLicenseSetCodec.ProtocolException.class,
                () -> FlysafeLicenseSetCodec.decodeAck(
                        true, 255, new byte[] {1, 2}, true));
    }

    @Test
    public void rejectsCallbackShapeCountAndStateDrift() {
        assertThrows(FlysafeLicenseSetCodec.ProtocolException.class,
                () -> FlysafeLicenseSetCodec.decodeAck(
                        false, 0, new byte[] {1, 2}, true));
        for (byte[] data : new byte[][] {
                null,
                {},
                {1},
                {1, 2, 3},
                {0, 2},
                {2, 2}
        }) {
            assertThrows(FlysafeLicenseSetCodec.ProtocolException.class,
                    () -> FlysafeLicenseSetCodec.decodeAck(true, 0, data, true));
        }
        assertThrows(FlysafeLicenseSetCodec.ProtocolException.class,
                () -> FlysafeLicenseSetCodec.decodeAck(
                        true, 0, new byte[] {1, 0}, true));
        assertThrows(FlysafeLicenseSetCodec.ProtocolException.class,
                () -> FlysafeLicenseSetCodec.decodeAck(
                        true, 0, new byte[] {1, 2}, false));
    }

    @Test
    public void acknowledgementsAndErrorsNeverRenderTargetId() {
        FlysafeLicenseSetCodec.Ack ack = FlysafeLicenseSetCodec.decodeAck(
                true, 0, new byte[] {1, 2}, true);
        assertFalse(ack.toString().contains("1234ABCD"));
        RuntimeException failure = assertThrows(
                FlysafeLicenseSetCodec.ProtocolException.class,
                () -> FlysafeLicenseSetCodec.decodeAck(
                        true, 1, new byte[] {1, 2}, true));
        assertFalse(failure.toString().contains("1234ABCD"));
    }
}
