package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

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
    public void rejectsNullShortAndExtendedPayloads() {
        assertThrows(RidWorkingStatus.ProtocolException.class,
                () -> RidWorkingStatus.parse(null));
        assertThrows(RidWorkingStatus.ProtocolException.class,
                () -> RidWorkingStatus.parse(new byte[6]));
        assertThrows(RidWorkingStatus.ProtocolException.class,
                () -> RidWorkingStatus.parse(new byte[8]));
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
