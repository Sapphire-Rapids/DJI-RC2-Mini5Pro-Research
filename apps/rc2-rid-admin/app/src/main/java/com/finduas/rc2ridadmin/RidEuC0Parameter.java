package com.finduas.rc2ridadmin;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

/**
 * Strict wire codec for the single DJI flight-controller parameter
 * {@code EU_CE_enable_c0_rid_0} ({@code 0xF80992FE}).
 *
 * <p>This class does not perform I/O. It deliberately has no API for selecting
 * another parameter name or hash. It mirrors the by-hash F7/F8/F9 semantics of
 * the host tool {@code host-tools/rid-switch-tool/rid_eu_by_hash_switch_control.py}
 * so the Android panel and the USB DUML host path address the same EU C0 row.</p>
 */
public final class RidEuC0Parameter {
    public static final String NAME = "EU_CE_enable_c0_rid_0";
    public static final int HASH = 0xF80992FE;

    private static final byte[] NAME_BYTES = NAME.getBytes(StandardCharsets.US_ASCII);
    private static final int F7_FIXED_SIZE = 19;

    private static final int TYPE_U8 = 0;
    private static final int TYPE_U16 = 1;
    private static final int TYPE_U32 = 2;
    private static final int TYPE_U64 = 3;
    private static final int TYPE_I8 = 4;
    private static final int TYPE_I16 = 5;
    private static final int TYPE_I32 = 6;
    private static final int TYPE_I64 = 7;
    private static final int TYPE_FLOAT = 8;
    private static final int TYPE_DOUBLE = 9;

    private RidEuC0Parameter() {
    }

    /**
     * Recomputes the DJI flight-controller parameter-name hash for {@code name}.
     *
     * <p>Algorithm: encode as GBK, start at zero, then for each byte
     * {@code hash = (((hash &amp; 0xFFFFFFFF) &lt;&lt; 8) + byte) % 0xFFFFFFFB}.
     * Current parameter names are ASCII, so GBK and byte iteration coincide.</p>
     */
    public static int computeFlycHash(String name) {
        if (name == null || name.isEmpty()) {
            throw new IllegalArgumentException("parameter name must not be empty");
        }
        byte[] encoded = name.getBytes(Charset.forName("GBK"));
        long hash = 0L;
        for (byte value : encoded) {
            hash = (((hash & 0xFFFFFFFFL) << 8) + (value & 0xFFL)) % 0xFFFFFFFBL;
        }
        return (int) hash;
    }

    /** Fails closed if the pinned name does not hash to the pinned hash. */
    public static void assertIdentity() {
        if (computeFlycHash(NAME) != HASH) {
            throw new IllegalStateException(
                    "EU C0 parameter name/hash mismatch; refusing to use codec");
        }
    }

    /** Returns the exact four-byte little-endian payload used by F7 and F8 requests. */
    public static byte[] buildHashRequestPayload() {
        assertIdentity();
        return hashLittleEndian();
    }

    /**
     * Parses one successful F7 metadata response and verifies the fixed parameter identity.
     *
     * <p>Layout: {@code [status:u8][type:u16le][size:u16le][attr:u16le]
     * [min:4][max:4][default:4][name:NUL-terminated ASCII]}.</p>
     */
    public static Metadata parseF7Metadata(byte[] payload) {
        assertIdentity();
        requirePayload(payload, "F7");
        int status = unsignedByte(payload[0]);
        if (status != 0) {
            throw new StatusException("F7", status);
        }
        if (payload.length < F7_FIXED_SIZE + 1) {
            throw new ProtocolException("F7 metadata is shorter than 20 bytes");
        }

        int type = unsignedLittleEndian16(payload, 1);
        int size = unsignedLittleEndian16(payload, 3);
        int attribute = unsignedLittleEndian16(payload, 5);
        int expectedSize = widthForType(type);
        if (size != expectedSize) {
            throw new ProtocolException(
                    "F7 type/size mismatch: type " + type + ", size " + size);
        }

        int terminator = -1;
        for (int index = F7_FIXED_SIZE; index < payload.length; index++) {
            if (payload[index] == 0) {
                terminator = index;
                break;
            }
        }
        if (terminator < 0) {
            throw new ProtocolException("F7 parameter name is not NUL-terminated");
        }
        int nameLength = terminator - F7_FIXED_SIZE;
        if (nameLength != NAME_BYTES.length) {
            throw new ProtocolException("F7 parameter identity does not match " + NAME);
        }
        for (int index = 0; index < NAME_BYTES.length; index++) {
            if (payload[F7_FIXED_SIZE + index] != NAME_BYTES[index]) {
                throw new ProtocolException("F7 parameter identity does not match " + NAME);
            }
        }
        for (int index = terminator + 1; index < payload.length; index++) {
            if (payload[index] != 0) {
                throw new ProtocolException("F7 parameter name has nonzero trailing bytes");
            }
        }

        return new Metadata(
                status,
                type,
                size,
                attribute,
                Arrays.copyOfRange(payload, 7, 11),
                Arrays.copyOfRange(payload, 11, 15),
                Arrays.copyOfRange(payload, 15, 19));
    }

    /**
     * Parses exactly one F8 response, preserving which published response layout matched.
     *
     * <p>Accepted layouts are current {@code [status][hash][value]} and legacy
     * {@code [hash][value]}. The echoed hash and F7-derived value width must match exactly.</p>
     */
    public static Value parseF8Value(byte[] payload, Metadata metadata) {
        assertIdentity();
        requirePayload(payload, "F8");
        requireMetadata(metadata);

        if (payload.length == 1) {
            int status = unsignedByte(payload[0]);
            if (status != 0) {
                throw new StatusException("F8", status);
            }
            throw new ProtocolException("F8 success status has no hash or value");
        }

        final Layout layout;
        final int valueOffset;
        if (payload.length == 5 + metadata.size) {
            requireHash(payload, 1, "F8 current");
            int status = unsignedByte(payload[0]);
            if (status != 0) {
                throw new StatusException("F8", status);
            }
            layout = Layout.STATUS_HASH_VALUE;
            valueOffset = 5;
        } else if (payload.length == 4 + metadata.size) {
            requireHash(payload, 0, "F8 legacy");
            layout = Layout.HASH_VALUE_LEGACY;
            valueOffset = 4;
        } else {
            throw new ProtocolException("F8 response length does not match F7 metadata");
        }

        byte[] raw = Arrays.copyOfRange(payload, valueOffset, payload.length);
        boolean enabled = decodeBoolean(raw, metadata);
        return new Value(layout, raw, enabled);
    }

    /** Encodes only the Boolean value bytes using the type and width admitted by F7. */
    public static byte[] encodeSetRaw(boolean enabled, Metadata metadata) {
        requireMetadata(metadata);
        requireWritableBooleanMetadata(metadata);
        byte[] raw = new byte[metadata.size];
        switch (metadata.type) {
            case TYPE_U8:
            case TYPE_U16:
            case TYPE_U32:
            case TYPE_U64:
            case TYPE_I8:
            case TYPE_I16:
            case TYPE_I32:
            case TYPE_I64:
                raw[0] = (byte) (enabled ? 1 : 0);
                return raw;
            case TYPE_FLOAT:
                return ByteBuffer.allocate(4)
                        .order(ByteOrder.LITTLE_ENDIAN)
                        .putFloat(enabled ? 1.0f : 0.0f)
                        .array();
            case TYPE_DOUBLE:
                return ByteBuffer.allocate(8)
                        .order(ByteOrder.LITTLE_ENDIAN)
                        .putDouble(enabled ? 1.0d : 0.0d)
                        .array();
            default:
                throw new ProtocolException("unsupported Boolean wire type " + metadata.type);
        }
    }

    /** Returns the complete F9 application payload {@code [hash:u32le][value:F7 size]}. */
    public static byte[] buildSetPayload(boolean enabled, Metadata metadata) {
        assertIdentity();
        byte[] raw = encodeSetRaw(enabled, metadata);
        byte[] result = new byte[4 + raw.length];
        byte[] hash = hashLittleEndian();
        System.arraycopy(hash, 0, result, 0, hash.length);
        System.arraycopy(raw, 0, result, hash.length, raw.length);
        return result;
    }

    private static boolean decodeBoolean(byte[] raw, Metadata metadata) {
        switch (metadata.type) {
            case TYPE_U8:
            case TYPE_U16:
            case TYPE_U32:
            case TYPE_U64:
            case TYPE_I8:
            case TYPE_I16:
            case TYPE_I32:
            case TYPE_I64:
                boolean zero = true;
                boolean one = raw[0] == 1;
                for (int index = 0; index < raw.length; index++) {
                    if (raw[index] != 0) {
                        zero = false;
                    }
                    if (index > 0 && raw[index] != 0) {
                        one = false;
                    }
                }
                if (zero) {
                    return false;
                }
                if (one) {
                    return true;
                }
                break;
            case TYPE_FLOAT:
                float floatValue = ByteBuffer.wrap(raw)
                        .order(ByteOrder.LITTLE_ENDIAN)
                        .getFloat();
                if (Float.isFinite(floatValue) && floatValue == 0.0f) {
                    return false;
                }
                if (Float.isFinite(floatValue) && floatValue == 1.0f) {
                    return true;
                }
                break;
            case TYPE_DOUBLE:
                double doubleValue = ByteBuffer.wrap(raw)
                        .order(ByteOrder.LITTLE_ENDIAN)
                        .getDouble();
                if (Double.isFinite(doubleValue) && doubleValue == 0.0d) {
                    return false;
                }
                if (Double.isFinite(doubleValue) && doubleValue == 1.0d) {
                    return true;
                }
                break;
            default:
                break;
        }
        throw new ProtocolException("RID EU C0 value is not exactly Boolean 0 or 1");
    }

    private static int widthForType(int type) {
        switch (type) {
            case TYPE_U8:
            case TYPE_I8:
                return 1;
            case TYPE_U16:
            case TYPE_I16:
                return 2;
            case TYPE_U32:
            case TYPE_I32:
            case TYPE_FLOAT:
                return 4;
            case TYPE_U64:
            case TYPE_I64:
            case TYPE_DOUBLE:
                return 8;
            default:
                throw new ProtocolException("unsupported F7 data type " + type);
        }
    }

    private static void requirePayload(byte[] payload, String command) {
        if (payload == null || payload.length == 0) {
            throw new ProtocolException(command + " response is empty");
        }
    }

    private static void requireMetadata(Metadata metadata) {
        if (metadata == null) {
            throw new ProtocolException("validated F7 metadata is required");
        }
    }

    private static void requireWritableBooleanMetadata(Metadata metadata) {
        if ((metadata.attribute & 0x01) == 0) {
            throw new ProtocolException(String.format(
                    "F7 attribute 0x%04X is not read/write", metadata.attribute));
        }
        if (metadata.size > 4 || metadata.type == TYPE_U64 || metadata.type == TYPE_I64
                || metadata.type == TYPE_DOUBLE) {
            throw new ProtocolException(
                    "Boolean write is not admitted for F7 type " + metadata.type
                            + " width " + metadata.size);
        }
        double minimum = decodeRangeValue(metadata.minimumRaw, metadata.type);
        double maximum = decodeRangeValue(metadata.maximumRaw, metadata.type);
        if (!Double.isFinite(minimum) || !Double.isFinite(maximum)
                || minimum > 0.0d || maximum < 1.0d) {
            throw new ProtocolException(
                    "F7 range does not admit both Boolean values 0 and 1");
        }
    }

    private static double decodeRangeValue(byte[] raw, int type) {
        ByteBuffer buffer = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);
        switch (type) {
            case TYPE_U8:
                return raw[0] & 0xff;
            case TYPE_U16:
                return buffer.getShort() & 0xffff;
            case TYPE_U32:
                return buffer.getInt() & 0xffffffffL;
            case TYPE_I8:
                return raw[0];
            case TYPE_I16:
                return buffer.getShort();
            case TYPE_I32:
                return buffer.getInt();
            case TYPE_FLOAT:
                return buffer.getFloat();
            default:
                throw new ProtocolException("unsupported Boolean range type " + type);
        }
    }

    private static void requireHash(byte[] payload, int offset, String layout) {
        byte[] expected = hashLittleEndian();
        for (int index = 0; index < expected.length; index++) {
            if (payload[offset + index] != expected[index]) {
                throw new ProtocolException(layout + " echoed an unexpected parameter hash");
            }
        }
    }

    private static int unsignedLittleEndian16(byte[] payload, int offset) {
        return unsignedByte(payload[offset]) | (unsignedByte(payload[offset + 1]) << 8);
    }

    private static int unsignedByte(byte value) {
        return value & 0xFF;
    }

    private static byte[] hashLittleEndian() {
        return new byte[] {
                (byte) HASH,
                (byte) (HASH >>> 8),
                (byte) (HASH >>> 16),
                (byte) (HASH >>> 24)
        };
    }

    public enum Layout {
        STATUS_HASH_VALUE,
        HASH_VALUE_LEGACY
    }

    public static final class Metadata {
        private final int status;
        private final int type;
        private final int size;
        private final int attribute;
        private final byte[] minimumRaw;
        private final byte[] maximumRaw;
        private final byte[] defaultRaw;

        private Metadata(
                int status,
                int type,
                int size,
                int attribute,
                byte[] minimumRaw,
                byte[] maximumRaw,
                byte[] defaultRaw) {
            this.status = status;
            this.type = type;
            this.size = size;
            this.attribute = attribute;
            this.minimumRaw = minimumRaw;
            this.maximumRaw = maximumRaw;
            this.defaultRaw = defaultRaw;
        }

        public int getStatus() {
            return status;
        }

        public int getType() {
            return type;
        }

        public int getSize() {
            return size;
        }

        public int getAttribute() {
            return attribute;
        }

        public byte[] getMinimumRaw() {
            return minimumRaw.clone();
        }

        public byte[] getMaximumRaw() {
            return maximumRaw.clone();
        }

        public byte[] getDefaultRaw() {
            return defaultRaw.clone();
        }

        public String getName() {
            return NAME;
        }

        public int getHash() {
            return HASH;
        }
    }

    public static final class Value {
        private final Layout layout;
        private final byte[] raw;
        private final boolean enabled;

        private Value(Layout layout, byte[] raw, boolean enabled) {
            this.layout = layout;
            this.raw = raw;
            this.enabled = enabled;
        }

        public Layout getLayout() {
            return layout;
        }

        public byte[] getRaw() {
            return raw.clone();
        }

        public boolean isEnabled() {
            return enabled;
        }
    }

    public static class ProtocolException extends IllegalArgumentException {
        ProtocolException(String message) {
            super(message);
        }
    }

    public static final class StatusException extends ProtocolException {
        private final int status;

        private StatusException(String command, int status) {
            super(command + " returned status 0x" + String.format("%02X", status));
            this.status = status;
        }

        public int getStatus() {
            return status;
        }
    }
}
