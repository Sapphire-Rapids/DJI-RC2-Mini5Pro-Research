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

public final class RidControlParameterTest {
    @Test
    public void hashRequestIsFixedLittleEndianAndDefensive() {
        byte[] first = RidControlParameter.buildHashRequestPayload();
        byte[] second = RidControlParameter.buildHashRequestPayload();

        assertArrayEquals(new byte[] {0x4F, (byte) 0x86, (byte) 0xBD, 0x3C}, first);
        assertNotSame(first, second);
        first[0] = 0;
        assertEquals(0x4F, second[0]);
    }

    @Test
    public void f7ParsesEveryFieldAndFixedIdentity() {
        byte[] minimum = bytes(0x10, 0x11, 0x12, 0x13);
        byte[] maximum = bytes(0x20, 0x21, 0x22, 0x23);
        byte[] defaultValue = bytes(0x30, 0x31, 0x32, 0x33);
        RidControlParameter.Metadata metadata = RidControlParameter.parseF7Metadata(
                f7(0, 0, 1, 0x1234, minimum, maximum, defaultValue,
                        RidControlParameter.NAME, new byte[] {0, 0}));

        assertEquals(0, metadata.getStatus());
        assertEquals(0, metadata.getType());
        assertEquals(1, metadata.getSize());
        assertEquals(0x1234, metadata.getAttribute());
        assertArrayEquals(minimum, metadata.getMinimumRaw());
        assertArrayEquals(maximum, metadata.getMaximumRaw());
        assertArrayEquals(defaultValue, metadata.getDefaultRaw());
        assertEquals(RidControlParameter.NAME, metadata.getName());
        assertEquals(RidControlParameter.HASH, metadata.getHash());
    }

    @Test
    public void f7RejectsStatusShortTypeWidthNameAndTrailingGarbage() {
        RidControlParameter.StatusException status = assertThrows(
                RidControlParameter.StatusException.class,
                () -> RidControlParameter.parseF7Metadata(new byte[] {3}));
        assertEquals(3, status.getStatus());

        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.parseF7Metadata(new byte[] {0}));
        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.parseF7Metadata(
                        f7(0, 10, 1, 0, zeros4(), zeros4(), zeros4(),
                                RidControlParameter.NAME, new byte[0])));
        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.parseF7Metadata(
                        f7(0, 11, 1, 0, zeros4(), zeros4(), zeros4(),
                                RidControlParameter.NAME, new byte[0])));
        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.parseF7Metadata(
                        f7(0, 2, 1, 0, zeros4(), zeros4(), zeros4(),
                                RidControlParameter.NAME, new byte[0])));
        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.parseF7Metadata(
                        f7(0, 0, 1, 0, zeros4(), zeros4(), zeros4(),
                                "another_parameter", new byte[0])));

        byte[] missingTerminator = f7(0, 0, 1, 0, zeros4(), zeros4(), zeros4(),
                RidControlParameter.NAME, new byte[0]);
        missingTerminator = Arrays.copyOf(missingTerminator, missingTerminator.length - 1);
        final byte[] finalMissingTerminator = missingTerminator;
        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.parseF7Metadata(finalMissingTerminator));

        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.parseF7Metadata(
                        f7(0, 0, 1, 0, zeros4(), zeros4(), zeros4(),
                                RidControlParameter.NAME, new byte[] {1})));
    }

    @Test
    public void f7RawFieldsAreDefensiveCopies() {
        RidControlParameter.Metadata metadata = RidControlParameter.parseF7Metadata(
                f7(0, 0, 1, 0, bytes(1, 2, 3, 4), zeros4(), zeros4(),
                        RidControlParameter.NAME, new byte[0]));
        byte[] first = metadata.getMinimumRaw();
        first[0] = 99;
        assertArrayEquals(bytes(1, 2, 3, 4), metadata.getMinimumRaw());
    }

    @Test
    public void f8CurrentAndLegacyLayoutsRemainDistinct() {
        RidControlParameter.Metadata metadata = metadata(0, 1);
        byte[] hash = RidControlParameter.buildHashRequestPayload();

        RidControlParameter.Value current = RidControlParameter.parseF8Value(
                concat(new byte[] {0}, hash, new byte[] {1}), metadata);
        assertEquals(RidControlParameter.Layout.STATUS_HASH_VALUE, current.getLayout());
        assertTrue(current.isEnabled());
        assertArrayEquals(new byte[] {1}, current.getRaw());

        RidControlParameter.Value legacy = RidControlParameter.parseF8Value(
                concat(hash, new byte[] {0}), metadata);
        assertEquals(RidControlParameter.Layout.HASH_VALUE_LEGACY, legacy.getLayout());
        assertFalse(legacy.isEnabled());
    }

    @Test
    public void f8RejectsErrorsWrongHashWrongWidthAndNonBooleanValues() {
        RidControlParameter.Metadata metadata = metadata(0, 1);
        RidControlParameter.StatusException status = assertThrows(
                RidControlParameter.StatusException.class,
                () -> RidControlParameter.parseF8Value(new byte[] {4}, metadata));
        assertEquals(4, status.getStatus());

        byte[] wrongHash = RidControlParameter.buildHashRequestPayload();
        wrongHash[3] ^= 1;
        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.parseF8Value(
                        concat(new byte[] {0}, wrongHash, new byte[] {1}), metadata));
        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.parseF8Value(
                        concat(RidControlParameter.buildHashRequestPayload(),
                                new byte[] {1, 0}), metadata));
        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.parseF8Value(
                        concat(RidControlParameter.buildHashRequestPayload(),
                                new byte[] {2}), metadata));
    }

    @Test
    public void integerWireWidthsEncodeCanonicalZeroAndOne() {
        int[][] typesAndWidths = {
                {0, 1}, {1, 2}, {2, 4},
                {4, 1}, {5, 2}, {6, 4}
        };
        for (int[] typeAndWidth : typesAndWidths) {
            RidControlParameter.Metadata metadata = metadata(
                    typeAndWidth[0], typeAndWidth[1]);
            byte[] disabled = new byte[typeAndWidth[1]];
            byte[] enabled = new byte[typeAndWidth[1]];
            enabled[0] = 1;
            assertArrayEquals(disabled,
                    RidControlParameter.encodeSetRaw(false, metadata));
            assertArrayEquals(enabled,
                    RidControlParameter.encodeSetRaw(true, metadata));

            RidControlParameter.Value decoded = RidControlParameter.parseF8Value(
                    concat(RidControlParameter.buildHashRequestPayload(), enabled), metadata);
            assertTrue(decoded.isEnabled());
        }
    }

    @Test
    public void floatAndDoubleTypesUseLittleEndianZeroAndOne() {
        RidControlParameter.Metadata floatMetadata = RidControlParameter.parseF7Metadata(
                f7(0, 8, 4, 1, zeros4(),
                        ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN)
                                .putFloat(1.0f).array(),
                        zeros4(), RidControlParameter.NAME, new byte[0]));
        RidControlParameter.Metadata doubleMetadata = metadata(9, 8);

        assertArrayEquals(ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN)
                        .putFloat(1.0f).array(),
                RidControlParameter.encodeSetRaw(true, floatMetadata));
        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.encodeSetRaw(false, doubleMetadata));

        assertTrue(RidControlParameter.parseF8Value(
                concat(RidControlParameter.buildHashRequestPayload(),
                        ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN)
                                .putFloat(1.0f).array()),
                floatMetadata).isEnabled());
        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.parseF8Value(
                        concat(RidControlParameter.buildHashRequestPayload(),
                                ByteBuffer.allocate(8).order(ByteOrder.LITTLE_ENDIAN)
                                        .putDouble(Double.NaN).array()),
                        doubleMetadata));
    }

    @Test
    public void completeSetPayloadIsFixedHashFollowedByF7SizedRawValue() {
        RidControlParameter.Metadata metadata = metadata(2, 4);
        assertArrayEquals(
                bytes(0x4F, 0x86, 0xBD, 0x3C, 1, 0, 0, 0),
                RidControlParameter.buildSetPayload(true, metadata));
        assertArrayEquals(
                bytes(0x4F, 0x86, 0xBD, 0x3C, 0, 0, 0, 0),
                RidControlParameter.buildSetPayload(false, metadata));
    }

    @Test
    public void writeRequiresWritableAttributeAndRangeContainingZeroAndOne() {
        RidControlParameter.Metadata readOnly = RidControlParameter.parseF7Metadata(
                f7(0, 0, 1, 0, zeros4(), bytes(1, 0, 0, 0), zeros4(),
                        RidControlParameter.NAME, new byte[0]));
        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.buildSetPayload(true, readOnly));

        RidControlParameter.Metadata excludesOne = RidControlParameter.parseF7Metadata(
                f7(0, 0, 1, 1, zeros4(), zeros4(), zeros4(),
                        RidControlParameter.NAME, new byte[0]));
        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.buildSetPayload(true, excludesOne));

        RidControlParameter.Metadata wide = metadata(3, 8);
        assertThrows(RidControlParameter.ProtocolException.class,
                () -> RidControlParameter.buildSetPayload(true, wide));
    }

    private static RidControlParameter.Metadata metadata(int type, int size) {
        return RidControlParameter.parseF7Metadata(
                f7(0, type, size, 1, zeros4(), bytes(1, 0, 0, 0), zeros4(),
                        RidControlParameter.NAME, new byte[0]));
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
