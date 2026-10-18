package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import java.util.Arrays;
import org.junit.Test;

public final class RidWorkingStatusTest {
    @Test
    public void parsesSupportNormalAreaFailureAndFullFlags() {
        RidWorkingStatus status = RidWorkingStatus.parse(new byte[] {
                0x03, 0x03,
                0x78, 0x56, 0x34, 0x12,
                0x00
        });

        assertEquals(0x0303, status.getFlags());
        assertTrue(status.isEidSupported());
        assertTrue(status.isRidSupported());
        assertTrue(status.isEidNormal());
        assertTrue(status.isRidNormal());
        assertEquals(0x12345678, status.getAreaCode());
        assertEquals(0, status.getFailureCode());
        assertEquals("WORKING", status.compatibilityState());
        assertArrayEquals(new byte[0], status.getTrailingBytes());
    }

    @Test
    public void areaCodeIsSignedLittleEndian() {
        RidWorkingStatus status = RidWorkingStatus.parse(new byte[] {
                0x01, 0x01,
                (byte) 0xFE, (byte) 0xFF, (byte) 0xFF, (byte) 0xFF,
                0x00
        });

        assertEquals(-2, status.getAreaCode());
        assertTrue(status.isRidSupported());
        assertTrue(status.isRidNormal());
        assertFalse(status.isEidSupported());
        assertFalse(status.isEidNormal());
    }

    @Test
    public void compatibilityStatesStayExplicit() {
        assertEquals("NOT_SUPPORTED", status(0x0000, 0).compatibilityState());
        assertEquals("IDLE", status(0x0001, 0).compatibilityState());
        assertEquals("OPERATOR_LOCATION_LOST_ERROR",
                status(0x0001, 1).compatibilityState());
        assertEquals("FIRMWARE_ERROR", status(0x0001, 2).compatibilityState());
        assertEquals("UNKNOWN_ERROR", status(0x0001, 255).compatibilityState());
    }

    @Test
    public void preservesUnknownFlagBitsWithoutGuessingTheirMeaning() {
        RidWorkingStatus status = status(0x8405, 0);
        assertEquals(0x8405, status.getFlags());
        assertTrue(status.isRidSupported());
        assertFalse(status.isEidSupported());
        assertFalse(status.isRidNormal());
        assertFalse(status.isEidNormal());
    }

    @Test
    public void rejectsNullAndEveryShortPayload() {
        assertThrows(RidWorkingStatus.ProtocolException.class,
                () -> RidWorkingStatus.parse(null));
        for (int length = 0; length < 7; length++) {
            byte[] payload = new byte[length];
            assertThrows(RidWorkingStatus.ProtocolException.class,
                    () -> RidWorkingStatus.parse(payload));
        }
    }

    @Test
    public void acceptsExtendedPrefixesWithoutInterpretingOrDisplayingTail() {
        byte[] prefix = {0x03, 0x03, 0x78, 0x56, 0x34, 0x12, 0x02};
        RidWorkingStatus base = RidWorkingStatus.parse(prefix);
        for (byte[] tail : new byte[][] {{(byte) 0xff}, {0x00, (byte) 0x80, 0x55}}) {
            byte[] payload = Arrays.copyOf(prefix, prefix.length + tail.length);
            System.arraycopy(tail, 0, payload, prefix.length, tail.length);
            RidWorkingStatus extended = RidWorkingStatus.parse(payload);

            assertArrayEquals(tail, extended.getTrailingBytes());
            assertEquals(base.getFlags(), extended.getFlags());
            assertEquals(base.getAreaCode(), extended.getAreaCode());
            assertEquals(base.getFailureCode(), extended.getFailureCode());
            assertEquals(base.display(), extended.display());
        }
    }

    @Test
    public void trailingBytesAreCopiedOnInputAndOutput() {
        byte[] payload = {0x01, 0x01, 0, 0, 0, 0, 0, 0x55};
        RidWorkingStatus status = RidWorkingStatus.parse(payload);
        payload[7] = 0;
        assertArrayEquals(new byte[] {0x55}, status.getTrailingBytes());

        byte[] exposed = status.getTrailingBytes();
        exposed[0] = 0;
        assertArrayEquals(new byte[] {0x55}, status.getTrailingBytes());
    }

    private static RidWorkingStatus status(int flags, int failure) {
        return RidWorkingStatus.parse(new byte[] {
                (byte) flags,
                (byte) (flags >>> 8),
                0, 0, 0, 0,
                (byte) failure
        });
    }
}
