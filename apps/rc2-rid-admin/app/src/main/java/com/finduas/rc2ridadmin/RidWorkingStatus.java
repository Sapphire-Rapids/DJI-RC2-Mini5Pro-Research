package com.finduas.rc2ridadmin;

import java.util.Arrays;
import java.util.Locale;

/** Parses the seven-byte {@code 0x11/0x1C} status prefix and retains unknown trailing bytes. */
final class RidWorkingStatus {
    static final int MIN_PAYLOAD_LENGTH = 7;

    private final int flags;
    private final boolean eidSupported;
    private final boolean ridSupported;
    private final boolean eidNormal;
    private final boolean ridNormal;
    private final int areaCode;
    private final int failureCode;
    private final byte[] trailingBytes;

    private RidWorkingStatus(
            int flags,
            boolean eidSupported,
            boolean ridSupported,
            boolean eidNormal,
            boolean ridNormal,
            int areaCode,
            int failureCode,
            byte[] trailingBytes) {
        this.flags = flags;
        this.eidSupported = eidSupported;
        this.ridSupported = ridSupported;
        this.eidNormal = eidNormal;
        this.ridNormal = ridNormal;
        this.areaCode = areaCode;
        this.failureCode = failureCode;
        this.trailingBytes = trailingBytes;
    }

    static RidWorkingStatus parse(byte[] payload) {
        if (payload == null) {
            throw new ProtocolException("RID working-status payload is null");
        }
        if (payload.length < MIN_PAYLOAD_LENGTH) {
            throw new ProtocolException(
                    "RID working-status payload length is " + payload.length + ", expected at least 7");
        }

        int flags = unsigned(payload[0]) | (unsigned(payload[1]) << 8);
        int areaCode = unsigned(payload[2])
                | (unsigned(payload[3]) << 8)
                | (unsigned(payload[4]) << 16)
                | (payload[5] << 24);
        return new RidWorkingStatus(
                flags,
                (flags & (1 << 1)) != 0,
                (flags & (1 << 0)) != 0,
                (flags & (1 << 9)) != 0,
                (flags & (1 << 8)) != 0,
                areaCode,
                unsigned(payload[6]),
                Arrays.copyOfRange(payload, MIN_PAYLOAD_LENGTH, payload.length));
    }

    int getFlags() {
        return flags;
    }

    boolean isEidSupported() {
        return eidSupported;
    }

    boolean isRidSupported() {
        return ridSupported;
    }

    boolean isEidNormal() {
        return eidNormal;
    }

    boolean isRidNormal() {
        return ridNormal;
    }

    int getAreaCode() {
        return areaCode;
    }

    int getFailureCode() {
        return failureCode;
    }

    /** Unknown extension data; not interpreted or included in display output. */
    byte[] getTrailingBytes() {
        return trailingBytes.clone();
    }

    String compatibilityState() {
        if (!ridSupported) {
            return "NOT_SUPPORTED";
        }
        if (failureCode == 0) {
            return ridNormal ? "WORKING" : "IDLE";
        }
        if (failureCode == 1) {
            return "OPERATOR_LOCATION_LOST_ERROR";
        }
        if (failureCode == 2) {
            return "FIRMWARE_ERROR";
        }
        return "UNKNOWN_ERROR";
    }

    String display() {
        return String.format(Locale.US,
                "RID support=%s normal=%s; EID support=%s normal=%s; "
                        + "area=%d; fail=%d; flags=0x%04X; state=%s",
                yesNo(ridSupported),
                yesNo(ridNormal),
                yesNo(eidSupported),
                yesNo(eidNormal),
                areaCode,
                failureCode,
                flags,
                compatibilityState());
    }

    private static int unsigned(byte value) {
        return value & 0xff;
    }

    private static String yesNo(boolean value) {
        return value ? "yes" : "no";
    }

    static final class ProtocolException extends IllegalArgumentException {
        ProtocolException(String message) {
            super(message);
        }
    }
}
