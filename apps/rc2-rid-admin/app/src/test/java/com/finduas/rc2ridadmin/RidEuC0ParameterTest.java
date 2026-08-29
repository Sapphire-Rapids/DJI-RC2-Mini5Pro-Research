package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotSame;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

import org.junit.Test;

public final class RidEuC0ParameterTest {
    @Test
    public void pinnedIdentityMatchesRecomputedHash() {
        assertEquals(0xF80992FE, RidEuC0Parameter.HASH);
        assertEquals("EU_CE_enable_c0_rid_0", RidEuC0Parameter.NAME);
        assertEquals(RidEuC0Parameter.HASH, RidEuC0Parameter.computeFlycHash(RidEuC0Parameter.NAME));
        RidEuC0Parameter.assertIdentity();
    }

    @Test
    public void flycHashMatchesPinnedReferenceVectors() {
        assertEquals(0xF80992FE, RidEuC0Parameter.computeFlycHash("EU_CE_enable_c0_rid_0"));
        assertEquals(0xA3F6F806, RidEuC0Parameter.computeFlycHash("EU_CE_enable_c0_rid"));
        assertEquals(0x3CBD864F, RidEuC0Parameter.computeFlycHash("rid_ctrl_enable_0"));
        assertEquals(0x0371238A, RidEuC0Parameter.computeFlycHash("g_config.flying_limit.max_height_0"));
        assertEquals(0xF412036C, RidEuC0Parameter.computeFlycHash("g_config.flying_limit.max_height"));
        assertEquals(0xD7757AD2, RidEuC0Parameter.computeFlycHash("ccc_broadcast_signal_quality_0"));
    }

    @Test
    public void hashRejectsNullAndEmptyNames() {
        assertThrows(IllegalArgumentException.class, () -> RidEuC0Parameter.computeFlycHash(null));
        assertThrows(IllegalArgumentException.class, () -> RidEuC0Parameter.computeFlycHash(""));
    }

    @Test
    public void hashRequestIsFixedLittleEndianAndDefensive() {
        byte[] first = RidEuC0Parameter.buildHashRequestPayload();
        byte[] second = RidEuC0Parameter.buildHashRequestPayload();

        assertArrayEquals(new byte[] {(byte) 0xFE, (byte) 0x92, 0x09, (byte) 0xF8}, first);
        assertNotSame(first, second);
        first[0] = 0;
        assertEquals((byte) 0xFE, second[0]);
    }

    @Test
    public void f7ParsesEveryFieldAndFixedIdentity() {
        byte[] minimum = bytes(0x10, 0x11, 0x12, 0x13);
        byte[] maximum = bytes(0x20, 0x21, 0x22, 0x23);
        byte[] defaultValue = bytes(0x30, 0x31, 0x32, 0x33);
        RidEuC0Parameter.Metadata metadata = RidEuC0Parameter.parseF7Metadata(
                f7(0, 0, 1, 0x1234, minimum, maximum, defaultValue,
                        RidEuC0Parameter.NAME, new byte[] {0, 0}));

        assertEquals(0, metadata.getStatus());
        assertEquals(0, metadata.getType());
        assertEquals(1, metadata.getSize());
        assertEquals(0x1234, metadata.getAttribute());
        assertArrayEquals(minimum, metadata.getMinimumRaw());
        assertArrayEquals(maximum, metadata.getMaximumRaw());
        assertArrayEquals(defaultValue, metadata.getDefaultRaw());
        assertEquals(RidEuC0Parameter.NAME, metadata.getName());
        assertEquals(RidEuC0Parameter.HASH, metadata.getHash());
    }

    @Test
    public void f7RejectsStatusShortTypeWidthNameAndTrailingGarbage() {
        RidEuC0Parameter.StatusException status = assertThrows(
                RidEuC0Parameter.StatusException.class,
                () -> RidEuC0Parameter.parseF7Metadata(new byte[] {3}));
        assertEquals(3, status.getStatus());

        assertThrows(RidEuC0Parameter.ProtocolException.class,
                () -> RidEuC0Parameter.parseF7Metadata(new byte[] {0}));
        assertThrows(RidEuC0Parameter.ProtocolException.class,
                () -> RidEuC0Parameter.parseF7Metadata(
                        f7(0, 10, 1, 0, zeros4(), zeros4(), zeros4(),
                                RidEuC0Parameter.NAME, new byte[0])));
        assertThrows(RidEuC0Parameter.ProtocolException.class,
                () -> RidEuC0Parameter.parseF7Metadata(
                        f7(0, 11, 1, 0, zeros4(), zeros4(), zeros4(),
                                RidEuC0Parameter.NAME, new byte[0])));
        assertThrows(RidEuC0Parameter.ProtocolException.class,
                () -> RidEuC0Parameter.parseF7Metadata(
                        f7(0, 2, 1, 0, zeros4(), zeros4(), zeros4(),
                                RidEuC0Parameter.NAME, new byte[0])));
        assertThrows(RidEuC0Parameter.ProtocolException.class,
                () -> RidEuC0Parameter.parseF7Metadata(
                        f7(0, 0, 1, 0, zeros4(), zeros4(), zeros4(),
                                "another_parameter", new byte[0])));

        byte[] missingTerminator = f7(0, 0, 1, 0, zeros4(), zeros4(), zeros4(),
                RidEuC0Parameter.NAME, new byte[0]);
        missingTerminator = Arrays.copyOf(missingTerminator, missingTerminator.length - 1);
        final byte[] finalMissingTerminator = missingTerminator;
        assertThrows(RidEuC0Parameter.ProtocolException.class,
                () -> RidEuC0Parameter.parseF7Metadata(finalMissingTerminator));

        assertThrows(RidEuC0Parameter.ProtocolException.class,
                () -> RidEuC0Parameter.parseF7Metadata(
                        f7(0, 0, 1, 0, zeros4(), zeros4(), zeros4(),
                                RidEuC0Parameter.NAME, new byte[] {1})));
    }

    @Test
    public void f7RawFieldsAreDefensiveCopies() {
        RidEuC0Parameter.Metadata metadata = RidEuC0Parameter.parseF7Metadata(
                f7(0, 0, 1, 0, bytes(1, 2, 3, 4), zeros4(), zeros4(),
                        RidEuC0Parameter.NAME, new byte[0]));
        byte[] first = metadata.getMinimumRaw();
        first[0] = 99;
        assertArrayEquals(bytes(1, 2, 3, 4), metadata.getMinimumRaw());
    }

    @Test
    public void f8CurrentAndLegacyLayoutsRemainDistinct() {
        RidEuC0Parameter.Metadata metadata = metadata(0, 1);
        byte[] hash = RidEuC0Parameter.buildHashRequestPayload();

        RidEuC0Parameter.Value current = RidEuC0Parameter.parseF8Value(
                concat(new byte[] {0}, hash, new byte[] {1}), metadata);
        assertEquals(RidEuC0Parameter.Layout.STATUS_HASH_VALUE, current.getLayout());
        assertTrue(current.isEnabled());
        assertEquals((byte) 0x01, current.getRaw()[0]);

        RidEuC0Parameter.Value legacy = RidEuC0Parameter.parseF8Value(
                concat(hash, new byte[] {0}), metadata);
        assertEquals(RidEuC0Parameter.Layout.HASH_VALUE_LEGACY, legacy.getLayout());
        assertFalse(legacy.isEnabled());
    }

    @Test
    public void integerWireWidthsEncodeCanonicalZeroAndOne() {
        int[][] typesAndWidths = {
                {0, 1}, {1, 2}, {2, 4},
                {4, 1}, {5, 2}, {6, 4}
        };
        for (int[] typeAndWidth : typesAndWidths) {
            RidEuC0Parameter.Metadata metadata = metadata(
                    typeAndWidth[0], typeAndWidth[1]);
            byte[] disabled = new byte[typeAndWidth[1]];
            byte[] enabled = new byte[typeAndWidth[1]];
            enabled[0] = 1;
            assertArrayEquals(disabled,
                    RidEuC0Parameter.encodeSetRaw(false, metadata));
            assertArrayEquals(enabled,
                    RidEuC0Parameter.encodeSetRaw(true, metadata));

            RidEuC0Parameter.Value decoded = RidEuC0Parameter.parseF8Value(
                    concat(RidEuC0Parameter.buildHashRequestPayload(), enabled), metadata);
            assertTrue(decoded.isEnabled());
        }
    }

    @Test
    public void floatAndDoubleTypesUseLittleEndianZeroAndOne() {
        RidEuC0Parameter.Metadata floatMetadata = RidEuC0Parameter.parseF7Metadata(
                f7(0, 8, 4, 1, zeros4(),
                        ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN)
                                .putFloat(1.0f).array(),
                        zeros4(), RidEuC0Parameter.NAME, new byte[0]));
        RidEuC0Parameter.Metadata doubleMetadata = metadata(9, 8);

        assertArrayEquals(ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN)
                        .putFloat(1.0f).array(),
                RidEuC0Parameter.encodeSetRaw(true, floatMetadata));
        assertThrows(RidEuC0Parameter.ProtocolException.class,
                () -> RidEuC0Parameter.encodeSetRaw(false, doubleMetadata));

        assertTrue(RidEuC0Parameter.parseF8Value(
                concat(RidEuC0Parameter.buildHashRequestPayload(),
                        ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN)
                                .putFloat(1.0f).array()),
                floatMetadata).isEnabled());
        assertThrows(RidEuC0Parameter.ProtocolException.class,
                () -> RidEuC0Parameter.parseF8Value(
                        concat(RidEuC0Parameter.buildHashRequestPayload(),
                                ByteBuffer.allocate(8).order(ByteOrder.LITTLE_ENDIAN)
                                        .putDouble(Double.NaN).array()),
                        doubleMetadata));
    }

    @Test
    public void completeSetPayloadIsFixedHashFollowedByF7SizedRawValue() {
        RidEuC0Parameter.Metadata metadata = metadata(2, 4);
        assertArrayEquals(
                bytes(0xFE, 0x92, 0x09, 0xF8, 1, 0, 0, 0),
                RidEuC0Parameter.buildSetPayload(true, metadata));
        assertArrayEquals(
                bytes(0xFE, 0x92, 0x09, 0xF8, 0, 0, 0, 0),
                RidEuC0Parameter.buildSetPayload(false, metadata));
    }

    @Test
    public void writeRequiresWritableAttributeAndRangeContainingZeroAndOne() {
        RidEuC0Parameter.Metadata readOnly = RidEuC0Parameter.parseF7Metadata(
                f7(0, 0, 1, 0, zeros4(), bytes(1, 0, 0, 0), zeros4(),
                        RidEuC0Parameter.NAME, new byte[0]));
        assertThrows(RidEuC0Parameter.ProtocolException.class,
                () -> RidEuC0Parameter.buildSetPayload(true, readOnly));

        RidEuC0Parameter.Metadata excludesOne = RidEuC0Parameter.parseF7Metadata(
                f7(0, 0, 1, 1, zeros4(), zeros4(), zeros4(),
                        RidEuC0Parameter.NAME, new byte[0]));
        assertThrows(RidEuC0Parameter.ProtocolException.class,
                () -> RidEuC0Parameter.buildSetPayload(true, excludesOne));

        RidEuC0Parameter.Metadata wide = metadata(3, 8);
        assertThrows(RidEuC0Parameter.ProtocolException.class,
                () -> RidEuC0Parameter.buildSetPayload(true, wide));
    }

    private static RidEuC0Parameter.Metadata metadata(int type, int size) {
        return RidEuC0Parameter.parseF7Metadata(
                f7(0, type, size, 1, zeros4(), bytes(1, 0, 0, 0), zeros4(),
                        RidEuC0Parameter.NAME, new byte[0]));
    }

    private static byte[] f7(
            int status,
            int type,
            int size,
            int attribute,
            byte[] minimum,
            byte[] maximum,
            byte[] defaultValue,
            String name,
            byte[] trailing) {
        byte[] nameBytes = name.getBytes(StandardCharsets.US_ASCII);
        ByteBuffer buffer = ByteBuffer.allocate(19 + nameBytes.length + 1 + trailing.length)
                .order(ByteOrder.LITTLE_ENDIAN);
        buffer.put((byte) status);
        buffer.putShort((short) type);
        buffer.putShort((short) size);
        buffer.putShort((short) attribute);
        buffer.put(minimum);
        buffer.put(maximum);
        buffer.put(defaultValue);
        buffer.put(nameBytes);
        buffer.put((byte) 0);
        buffer.put(trailing);
        return buffer.array();
    }

    private static byte[] zeros4() {
        return new byte[4];
    }

    private static byte[] bytes(int... values) {
        byte[] result = new byte[values.length];
        for (int index = 0; index < values.length; index++) {
            result[index] = (byte) values[index];
        }
        return result;
    }

    private static byte[] concat(byte[]... parts) {
        int size = 0;
        for (byte[] part : parts) {
            size += part.length;
        }
        byte[] result = new byte[size];
        int offset = 0;
        for (byte[] part : parts) {
            System.arraycopy(part, 0, result, offset, part.length);
            offset += part.length;
        }
        return result;
    }
}
