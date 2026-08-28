package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertThrows;

import java.nio.charset.StandardCharsets;

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
}
