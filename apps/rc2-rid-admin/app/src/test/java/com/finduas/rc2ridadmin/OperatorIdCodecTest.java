package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertThrows;

import java.nio.charset.StandardCharsets;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

import org.junit.Test;

public final class OperatorIdCodecTest {
    @Test
    public void syntheticValidValueEncodesPublic16() {
        String value = "FRA0000000000000-000";
        assertNull(OperatorIdCodec.validationError(value));

        byte[] expected = new byte[18];
        expected[0] = 0;
        expected[1] = 16;
        System.arraycopy(value.substring(0, 16).getBytes(StandardCharsets.US_ASCII),
                0, expected, 2, 16);
        assertArrayEquals(expected, OperatorIdCodec.encodeSetPayload(value));
    }

    @Test
    public void invalidCheckDigitIsRejected() {
        assertThrows(IllegalArgumentException.class,
                () -> OperatorIdCodec.encodeSetPayload("FRA0000000000001-000"));
    }

    @Test
    public void displayAndCopySummaryNeverContainTheReturnedIdentity() {
        String value = "TEST-OPID-000001";
        String summary = OperatorIdCodec.maskedSummary(value.getBytes(StandardCharsets.US_ASCII));
        assertFalse(summary.contains(value));
        assertFalse(summary.contains("TEST"));
        assertEquals("已设置（值已隐藏；长度=16）", summary);
        assertEquals("未设置", OperatorIdCodec.maskedSummary(new byte[0]));
        assertEquals("未知", OperatorIdCodec.maskedSummary(null));
    }

    @Test
    public void malformedGetCannotBecomeAnEmptyOrRestorableBaseline() {
        for (byte[] data : new byte[][] {null, {}, {16, 1}, {(byte) 101}}) {
            assertThrows(IllegalStateException.class, () -> OperatorIdCodec.decodeGetData(data));
        }
        assertArrayEquals(new byte[0], OperatorIdCodec.decodeGetData(new byte[] {0}));
        assertThrows(IllegalStateException.class,
                () -> OperatorIdCodec.requireRestorableBaseline(
                        OperatorIdCodec.decodeGetData(new byte[] {1, 42})));
    }

    @Test
    public void activityGetParserClearsRawIdentityOnSuccessAndFailure() throws Exception {
        Method parser = MainActivity.class.getDeclaredMethod("parseOperatorId", DjiProtocolClient.Reply.class);
        parser.setAccessible(true);
        byte[] value = "TEST-OPID-000001".getBytes(StandardCharsets.US_ASCII);
        byte[] data = new byte[17];
        data[0] = 16;
        System.arraycopy(value, 0, data, 1, 16);
        DjiProtocolClient.Reply good = new DjiProtocolClient.Reply(true, null, 0x78, 0, data, null);
        assertArrayEquals(value, (byte[]) parser.invoke(null, good));
        assertArrayEquals(new byte[17], good.data);

        DjiProtocolClient.Reply failed = new DjiProtocolClient.Reply(
                false, "vendor echoed TEST-OPID-000001", 0x78, 1, data, "TEST-OPID-000001");
        InvocationTargetException failure = assertThrows(
                InvocationTargetException.class, () -> parser.invoke(null, failed));
        assertFalse(failure.getCause().getMessage().contains("TEST-OPID"));
        assertArrayEquals(new byte[17], failed.data);
    }

    @Test
    public void activityWriteAdapterRequiresCanonicalApplicationAck() throws Exception {
        Method check = MainActivity.class.getDeclaredMethod(
                "requireIdentityWriteAck", DjiProtocolClient.Reply.class);
        check.setAccessible(true);
        check.invoke(null, new DjiProtocolClient.Reply(true, null, 0x78, 0, new byte[0], null));
        for (DjiProtocolClient.Reply reply : new DjiProtocolClient.Reply[] {
                new DjiProtocolClient.Reply(false, "failure", 0x78, 0, null, null),
                new DjiProtocolClient.Reply(true, null, 0x78, 1, null, null),
                new DjiProtocolClient.Reply(true, null, 0x78, 0, new byte[] {0}, null)
        }) {
            assertThrows(InvocationTargetException.class, () -> check.invoke(null, reply));
        }
    }
}
