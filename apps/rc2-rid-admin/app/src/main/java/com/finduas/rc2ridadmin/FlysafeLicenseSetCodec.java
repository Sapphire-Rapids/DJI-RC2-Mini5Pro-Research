package com.finduas.rc2ridadmin;

/** Strict, privacy-preserving codec for the modern FlySafe 0x11/0x12 operation. */
final class FlysafeLicenseSetCodec {
    static final int PAYLOAD_LENGTH = 7;
    static final int ACK_DATA_LENGTH = 2;

    private static final int ENABLE_ACTION = 1;
    private static final int DISABLE_ACTION = 2;
    private static final int ENABLED_STATUS_BIT = 0x02;

    private FlysafeLicenseSetCodec() {
    }

    /**
     * Builds V3/V4 payload {@code [00][uint32 licenseId LE][01 enable|02 disable][00]}.
     * The caller owns and must clear both the input ID copy and returned payload.
     */
    static byte[] buildPayload(byte[] licenseIdLe, boolean enable) {
        if (licenseIdLe == null || licenseIdLe.length != 4) {
            throw new IllegalArgumentException("license target must be an exact uint32 handle");
        }
        boolean allZero = true;
        for (byte value : licenseIdLe) {
            allZero &= value == 0;
        }
        if (allZero) {
            throw new IllegalArgumentException("license target zero is not admitted");
        }

        byte[] payload = new byte[PAYLOAD_LENGTH];
        System.arraycopy(licenseIdLe, 0, payload, 1, licenseIdLe.length);
        payload[5] = (byte) (enable ? ENABLE_ACTION : DISABLE_ACTION);
        return payload;
    }

    /**
     * Accepts only a successful callback, result code zero, one returned item, and a status whose
     * bit 1 exactly matches the requested state. Other status bits are deliberately uninterpreted.
     */
    static Ack decodeAck(
            boolean callbackSuccess,
            int ccode,
            byte[] data,
            boolean requestedEnabled) {
        if (!callbackSuccess) {
            throw new ProtocolException("11/12 callback did not produce a validated ACK");
        }
        if (ccode != 0) {
            // Current V3/V4 result codes 1..5 are all errors. Unknown nonzero values also fail
            // closed; never reinterpret one as a per-item status.
            throw new ProtocolException("11/12 result code is nonzero");
        }
        if (data == null || data.length != ACK_DATA_LENGTH) {
            throw new ProtocolException("11/12 ACK data must be exactly two bytes");
        }
        if ((data[0] & 0xff) != 1) {
            throw new ProtocolException("11/12 ACK item count must be one");
        }
        boolean acknowledgedEnabled = (data[1] & ENABLED_STATUS_BIT) != 0;
        if (acknowledgedEnabled != requestedEnabled) {
            throw new ProtocolException("11/12 ACK state does not match the request");
        }
        return new Ack(requestedEnabled);
    }

    static final class Ack {
        private final boolean enabled;

        private Ack(boolean enabled) {
            this.enabled = enabled;
        }

        boolean isEnabled() {
            return enabled;
        }

        @Override
        public String toString() {
            return "FlysafeLicenseSetAck{state=" + (enabled ? "enabled" : "disabled") + "}";
        }
    }

    static final class ProtocolException extends IllegalArgumentException {
        ProtocolException(String message) {
            super(message);
        }
    }
}
