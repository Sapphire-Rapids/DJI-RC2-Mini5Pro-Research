package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotSame;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.junit.Test;

public final class FlysafeRidInventoryTest {
    @Test
    public void traversesV34GroupRecordsAndTerminatorWithExactSelectors() throws Exception {
        String secretSn = "sensitive-aircraft-serial";
        String secretDescription = "sensitive-license-description";
        long secretUserId = 9_876_543_210L;
        long secretLicenseId = 0xfedcba98L;

        byte[] group = group(2, secretSn, secretUserId, 123_456L);
        byte[] rid = page(
                0x06,
                license(
                        secretLicenseId,
                        bytesField(7, concat(
                                varintField(1, 2),
                                varintField(19, 44))),
                        secretDescription,
                        concat(
                                varintField(3, 1_725_000_000L),
                                varintField(4, 1_726_000_000L),
                                varintField(5, 1),
                                bytesField(7, new byte[] {1, 2, 3}),
                                varintField(91, 7))));
        byte[] nonRid = page(
                0x07,
                license(
                        4_242_424L,
                        bytesField(5, concat(
                                varintField(1, 99),
                                bytesField(2, new byte[] {7, 8}))),
                        "private-geometry-description",
                        new byte[0]));

        ScriptedTransport transport = new ScriptedTransport(
                response(0, group),
                response(0, rid),
                response(0, nonRid),
                response(1, null));
        FlysafeRidInventory.Result result = FlysafeRidInventory.query(transport);

        assertEquals(2, result.getDeclaredLicenseCount());
        assertEquals(2, result.getParsedLicenseCount());
        assertEquals(3, result.getPageCalls());
        assertEquals(1, result.getRidLicenses().size());
        FlysafeRidInventory.RidLicense item = result.getRidLicenses().get(0);
        assertEquals(FlysafeRidInventory.RID_UNLOCK_TYPE_CODE, item.getTypeCode());
        assertEquals(2L, item.getLevel());
        assertEquals("CHINA(2)", item.levelDisplay());
        assertTrue(item.isEnabled());
        assertTrue(item.isValid());
        assertFalse(item.isInvalid());
        assertEquals(0, item.getUninterpretedStatusBits());
        assertEquals(0x06, item.getRawStatus());

        assertEquals(4, transport.payloads.size());
        assertArrayEquals(new byte[] {0, 1}, transport.payloads.get(0));
        assertArrayEquals(new byte[] {0, 0}, transport.payloads.get(1));
        assertArrayEquals(new byte[] {0, 2}, transport.payloads.get(2));
        assertArrayEquals(new byte[] {0, 4}, transport.payloads.get(3));

        String printable = (result.display() + "|" + result).toLowerCase();
        for (String forbidden : new String[] {
                secretSn.toLowerCase(),
                secretDescription.toLowerCase(),
                Long.toString(secretUserId),
                Long.toString(secretLicenseId),
                Long.toHexString(secretLicenseId),
                "private-geometry-description",
                "4242424"
        }) {
            assertFalse("leaked: " + forbidden, printable.contains(forbidden));
        }
        assertTrue(printable.contains("rid_unlock #1"));
        assertTrue(printable.contains("enabled(bit1)=1"));
        assertTrue(printable.contains("valid(bit2)=1"));
        assertTrue(printable.contains("route=current-gate-session-bound"));
        assertFalse(printable.contains("02:04>12:04"));
        assertThrows(UnsupportedOperationException.class,
                () -> result.getRidLicenses().clear());
        result.close();
        assertTrue(result.isClosed());
    }

    @Test
    public void emptyInventoryRequiresAnExplicitDataLessTerminator() throws Exception {
        ScriptedTransport transport = new ScriptedTransport(
                response(0, concat(
                        varintField(1, 8),
                        bytesField(3, "sn".getBytes(StandardCharsets.UTF_8)))),
                response(1, new byte[0]));
        FlysafeRidInventory.Result result = FlysafeRidInventory.query(transport);
        assertEquals(0, result.getDeclaredLicenseCount());
        assertEquals(0, result.getParsedLicenseCount());
        assertEquals(1, result.getPageCalls());
        assertTrue(result.getRidLicenses().isEmpty());
        assertArrayEquals(new byte[] {0, 0}, transport.payloads.get(1));
        result.close();
    }

    @Test
    public void ccodeAndDataCombinationsFailClosed() {
        byte[] group = group(1, "sn", 7, 8);
        byte[] rid = page(0, ridLicense(7, 1));
        List<ScriptedTransport> bad = Arrays.asList(
                new ScriptedTransport(response(1, group)),
                new ScriptedTransport(response(0, null)),
                new ScriptedTransport(response(0, group), response(2, rid)),
                new ScriptedTransport(response(0, group), response(1, null)),
                new ScriptedTransport(
                        response(0, group), response(0, rid), response(1, new byte[] {9})),
                new ScriptedTransport(
                        response(0, group), response(0, rid), response(0, rid)));
        for (ScriptedTransport transport : bad) {
            assertThrows(FlysafeRidInventory.ProtocolException.class,
                    () -> FlysafeRidInventory.query(transport));
        }
    }

    @Test
    public void callbackFailureIsRejectedWithoutPropagatingSensitiveDiagnostics() {
        FlysafeRidInventory.ProtocolException error = assertThrows(
                FlysafeRidInventory.ProtocolException.class,
                () -> FlysafeRidInventory.query(payload ->
                        new FlysafeRidInventory.Response(false, -1,
                                "sensitive-license-id".getBytes(StandardCharsets.UTF_8))));
        assertFalse(error.getMessage().contains("sensitive"));
    }

    @Test
    public void duplicateLicenseIdsAcrossPagesAreRejectedViaRedactedFingerprints() {
        FlysafeRidInventory.Response first = response(0, page(0, ridLicense(987_654_321, 1)));
        FlysafeRidInventory.Response duplicate = response(
                0, page(0, ridLicense(987_654_321, 2)));
        FlysafeRidInventory.ProtocolException error = assertThrows(
                FlysafeRidInventory.ProtocolException.class,
                () -> FlysafeRidInventory.query(new ScriptedTransport(
                        response(0, group(2, "sn", 7, 8)),
                        first,
                        duplicate)));
        assertTrue(error.getMessage().contains("duplicate"));
        assertFalse(error.getMessage().contains("987654321"));
        assertTrue(allZero(first.data));
        assertTrue(allZero(duplicate.data));
    }

    @Test
    public void parsesStatusBitsAndUnknownRidLevelWithoutInventingSemantics() {
        FlysafeRidInventory.ParsedRecord record = FlysafeRidInventory.parsePageRecord(
                page(0xff, ridLicense(9, 0xffff_ffffL)));
        FlysafeRidInventory.RidLicense rid = record.ridLicense;
        assertEquals(0xffff_ffffL, rid.getLevel());
        assertEquals("UNKNOWN(4294967295)", rid.levelDisplay());
        assertTrue(rid.isEnabled());
        assertTrue(rid.isValid());
        assertTrue(rid.isInvalid());
        assertEquals(0xf8, rid.getUninterpretedStatusBits());
        assertEquals(0xff, rid.getRawStatus());
    }

    @Test
    public void onlyExactLicenseDataOneofFieldSevenIsRid() {
        for (int field = 1; field <= 8; field++) {
            if (field == 7) {
                continue;
            }
            FlysafeRidInventory.ParsedRecord record = FlysafeRidInventory.parsePageRecord(
                    page(0x06, license(100 + field,
                            bytesField(field, new byte[0]), "non-rid", new byte[0])));
            assertEquals(null, record.ridLicense);
        }

        byte[] conflict = license(7,
                concat(
                        bytesField(7, varintField(1, 1)),
                        bytesField(1, new byte[0])),
                "conflict",
                new byte[0]);
        assertThrows(FlysafeRidInventory.ProtocolException.class,
                () -> FlysafeRidInventory.parsePageRecord(page(0, conflict)));
    }

    @Test
    public void strictParserRejectsMissingDuplicateWrongWireAndMalformedValues() {
        byte[] ridData = bytesField(7, varintField(1, 1));
        List<byte[]> badPages = Arrays.asList(
                page(0, bytesField(6, ridData)),
                page(0, concat(varintField(1, 7), varintField(1, 8), bytesField(6, ridData))),
                page(0, concat(varintField(1, 7), bytesField(6,
                        bytesField(7, concat(varintField(1, 1), varintField(1, 2)))))),
                page(0, concat(bytesField(1, new byte[0]), bytesField(6, ridData))),
                page(0, concat(varintField(1, 7), bytesField(6,
                        bytesField(7, new byte[0])))),
                page(0, concat(varintField(1, 7), varintField(5, 2), bytesField(6, ridData))),
                page(0, concat(varintField(1, 7), bytesField(2,
                        new byte[] {(byte) 0xc3, 0x28}), bytesField(6, ridData))),
                new byte[] {0},
                null);
        for (byte[] bad : badPages) {
            assertThrows(FlysafeRidInventory.ProtocolException.class,
                    () -> FlysafeRidInventory.parsePageRecord(bad));
        }
    }

    @Test
    public void groupParserRequiresOneBoundedCountAndNeverReturnsIdentityFields() {
        FlysafeRidInventory.GroupInfo parsed = FlysafeRidInventory.parseGroup(
                group(127, "do-not-return-sn", 7_777_777, 8_888_888));
        assertEquals(127, parsed.licensesCount);
        String printable = parsed.toString();
        assertFalse(printable.contains("do-not-return-sn"));
        assertFalse(printable.contains("7777777"));
        assertFalse(printable.contains("8888888"));

        assertThrows(FlysafeRidInventory.ProtocolException.class,
                () -> FlysafeRidInventory.parseGroup(group(128, "sn", 1, 2)));
        assertThrows(FlysafeRidInventory.ProtocolException.class,
                () -> FlysafeRidInventory.parseGroup(new byte[0]));
        assertEquals(0, FlysafeRidInventory.parseGroup(varintField(1, 9)).licensesCount);
        assertThrows(FlysafeRidInventory.ProtocolException.class,
                () -> FlysafeRidInventory.parseGroup(
                        concat(varintField(5, 1), varintField(5, 1))));
    }

    @Test
    public void payloadBuildersAreDefensiveAndBounded() {
        byte[] first = FlysafeRidInventory.startPayload();
        byte[] second = FlysafeRidInventory.startPayload();
        assertNotSame(first, second);
        first[1] = 9;
        assertArrayEquals(new byte[] {0, 1}, second);
        assertArrayEquals(new byte[] {0, 0}, FlysafeRidInventory.pagePayload(0));
        assertArrayEquals(new byte[] {0, (byte) 0xfe},
                FlysafeRidInventory.pagePayload(127));
        assertThrows(IllegalArgumentException.class,
                () -> FlysafeRidInventory.pagePayload(-1));
        assertThrows(IllegalArgumentException.class,
                () -> FlysafeRidInventory.pagePayload(128));
    }

    @Test
    public void responseCopiesTransportBytesDefensively() {
        byte[] raw = new byte[] {1, 2, 3};
        FlysafeRidInventory.Response response = response(0, raw);
        raw[0] = 9;
        assertArrayEquals(new byte[] {1, 2, 3}, response.data);
    }

    @Test
    public void queryClearsEverySensitiveResponseCopyAfterParsing() throws Exception {
        FlysafeRidInventory.Response group = response(0, group(1, "secret-sn", 77, 88));
        FlysafeRidInventory.Response record = response(0, page(6, ridLicense(999, 1)));
        FlysafeRidInventory.Response end = response(1, null);
        FlysafeRidInventory.Result result = FlysafeRidInventory.query(
                new ScriptedTransport(group, record, end));
        result.close();
        assertTrue(allZero(group.data));
        assertTrue(allZero(record.data));
    }

    @Test
    public void publicReadOnlyQueryKeepsPublicRidStateButCannotIssueControlHandle()
            throws Exception {
        long secretLicenseId = 0xfedcba98L;
        FlysafeRidInventory.Result result = FlysafeRidInventory.queryReadOnly(
                new ScriptedTransport(
                        response(0, group(1, "secret-sn", 77, 88)),
                        response(0, page(6, ridLicense(secretLicenseId, 2))),
                        response(1, null)));
        try {
            assertFalse(result.isControlHandleEligible());
            assertEquals(1, result.getRidLicenses().size());
            assertEquals(2L, result.getRidLicenses().get(0).getLevel());
            assertTrue(result.getRidLicenses().get(0).isEnabled());
            assertTrue(result.getRidLicenses().get(0).isValid());

            FlysafeRidInventory.ProtocolException rejected = assertThrows(
                    FlysafeRidInventory.ProtocolException.class,
                    () -> result.openSingleEligibleHandle(new Object()));
            assertTrue(rejected.getMessage().contains("public read-only"));

            String printable = (result.displayDirectReadonly() + "|" + result)
                    .toLowerCase();
            assertTrue(printable.contains("public-read-only"));
            assertTrue(printable.contains("不保留控制句柄"));
            assertFalse(printable.contains(Long.toString(secretLicenseId)));
            assertFalse(printable.contains(Long.toHexString(secretLicenseId)));
        } finally {
            result.close();
        }
    }

    @Test
    public void opaqueHandleKeepsExactUint32PrivateAndUsesTokenIdentity() throws Exception {
        long secretLicenseId = 0xfedcba98L;
        Object sessionMarker = new Object();
        Object equalLookingButDifferentToken = new Object();
        FlysafeRidInventory.Result result = singleRidInventory(
                secretLicenseId, 2, 0xa6);
        FlysafeRidInventory.OpaqueRidHandle handle =
                result.openSingleEligibleHandle(sessionMarker);
        try {
            assertEquals(FlysafeRidInventory.RID_UNLOCK_TYPE_CODE, handle.getTypeCode());
            assertEquals(2L, handle.getLevel());
            assertTrue(handle.wasEnabled());

            byte[] firstCopy = handle.copyLicenseIdLeForSet(sessionMarker);
            assertArrayEquals(new byte[] {
                    (byte) 0x98, (byte) 0xba, (byte) 0xdc, (byte) 0xfe
            }, firstCopy);
            firstCopy[0] = 0;
            byte[] secondCopy = handle.copyLicenseIdLeForSet(sessionMarker);
            assertArrayEquals(new byte[] {
                    (byte) 0x98, (byte) 0xba, (byte) 0xdc, (byte) 0xfe
            }, secondCopy);
            Arrays.fill(firstCopy, (byte) 0);
            Arrays.fill(secondCopy, (byte) 0);

            assertThrows(FlysafeRidInventory.ProtocolException.class,
                    () -> handle.copyLicenseIdLeForSet(equalLookingButDifferentToken));
            assertThrows(FlysafeRidInventory.ProtocolException.class,
                    () -> result.openSingleEligibleHandle(sessionMarker));

            String printable = (result.display() + "|" + result + "|" + handle)
                    .toLowerCase();
            assertFalse(printable.contains(Long.toString(secretLicenseId)));
            assertFalse(printable.contains(Long.toHexString(secretLicenseId)));
            assertTrue(printable.contains("redacted"));
        } finally {
            result.close();
        }

        assertTrue(result.isClosed());
        assertTrue(handle.isClosed());
        assertThrows(IllegalStateException.class,
                () -> handle.copyLicenseIdLeForSet(sessionMarker));
        assertThrows(IllegalStateException.class,
                () -> result.openSingleEligibleHandle(sessionMarker));
        result.clear();
        handle.clear();
    }

    @Test
    public void selectionRequiresExactlyOneKnownLevelCurrentlyValidRecord() throws Exception {
        Object token = new Object();
        FlysafeRidInventory.Result none = ridInventory(
                new long[] {11, 12, 13},
                new long[] {1, 2, 3},
                new int[] {0x05, 0x00, 0x04});
        try {
            assertThrows(FlysafeRidInventory.ProtocolException.class,
                    () -> none.openSingleEligibleHandle(token));
        } finally {
            none.close();
        }

        FlysafeRidInventory.Result ambiguous = ridInventory(
                new long[] {21, 22},
                new long[] {1, 2},
                new int[] {0x04, 0xfe});
        try {
            FlysafeRidInventory.ProtocolException error = assertThrows(
                    FlysafeRidInventory.ProtocolException.class,
                    () -> ambiguous.openSingleEligibleHandle(token));
            assertTrue(error.getMessage().contains("multiple"));
            assertFalse(error.getMessage().contains("21"));
            assertFalse(error.getMessage().contains("22"));
        } finally {
            ambiguous.close();
        }
    }

    @Test
    public void exactReadbackAllowsOnlyTargetEnabledBitToDiffer() throws Exception {
        long licenseId = 0x89ab_cdefL;
        Object token = new Object();
        FlysafeRidInventory.Result baseline = singleRidInventory(licenseId, 2, 0xa4);
        FlysafeRidInventory.OpaqueRidHandle handle =
                baseline.openSingleEligibleHandle(token);
        try {
            FlysafeRidInventory.Result enabled = singleRidInventory(licenseId, 2, 0xa6);
            try {
                assertTrue(handle.verifyReadback(enabled, token, true));
            } finally {
                enabled.close();
            }

            FlysafeRidInventory.Result restored = singleRidInventory(licenseId, 2, 0xa4);
            try {
                assertTrue(handle.verifyReadback(restored, token, false));
            } finally {
                restored.close();
            }

            assertThrows(FlysafeRidInventory.ProtocolException.class,
                    () -> handle.verifyReadback(baseline, token, false));
            FlysafeRidInventory.Result wrongTokenFresh =
                    singleRidInventory(licenseId, 2, 0xa6);
            try {
                assertThrows(FlysafeRidInventory.ProtocolException.class,
                        () -> handle.verifyReadback(wrongTokenFresh, new Object(), true));
            } finally {
                wrongTokenFresh.close();
            }

            assertReadbackRejected(handle, token, licenseId + 1, 2, 0xa6, true);
            assertReadbackRejected(handle, token, licenseId, 1, 0xa6, true);
            assertReadbackRejected(handle, token, licenseId, 2, 0xa7, true);
            assertReadbackRejected(handle, token, licenseId, 2, 0xa2, true);
            assertReadbackRejected(handle, token, licenseId, 2, 0xb6, true);
            assertReadbackRejected(handle, token, licenseId, 2, 0xa4, true);

            FlysafeRidInventory.Result changedType = nonRidInventory(licenseId);
            try {
                assertThrows(FlysafeRidInventory.ProtocolException.class,
                        () -> handle.verifyReadback(changedType, token, true));
            } finally {
                changedType.close();
            }
        } finally {
            baseline.close();
        }
    }

    private static void assertReadbackRejected(
            FlysafeRidInventory.OpaqueRidHandle handle,
            Object token,
            long licenseId,
            long level,
            int status,
            boolean expectedEnabled) throws Exception {
        FlysafeRidInventory.Result fresh = singleRidInventory(licenseId, level, status);
        try {
            assertThrows(FlysafeRidInventory.ProtocolException.class,
                    () -> handle.verifyReadback(fresh, token, expectedEnabled));
        } finally {
            fresh.close();
        }
    }

    private static FlysafeRidInventory.Result singleRidInventory(
            long licenseId,
            long level,
            int status) throws Exception {
        return ridInventory(
                new long[] {licenseId},
                new long[] {level},
                new int[] {status});
    }

    private static FlysafeRidInventory.Result ridInventory(
            long[] licenseIds,
            long[] levels,
            int[] statuses) throws Exception {
        assertEquals(licenseIds.length, levels.length);
        assertEquals(licenseIds.length, statuses.length);
        FlysafeRidInventory.Response[] responses =
                new FlysafeRidInventory.Response[licenseIds.length + 2];
        responses[0] = response(0, group(licenseIds.length, "sn", 7, 8));
        for (int index = 0; index < licenseIds.length; index++) {
            responses[index + 1] = response(
                    0, page(statuses[index], ridLicense(licenseIds[index], levels[index])));
        }
        responses[responses.length - 1] = response(1, null);
        return FlysafeRidInventory.query(new ScriptedTransport(responses));
    }

    private static FlysafeRidInventory.Result nonRidInventory(long licenseId) throws Exception {
        return FlysafeRidInventory.query(new ScriptedTransport(
                response(0, group(1, "sn", 7, 8)),
                response(0, page(0xa6, license(
                        licenseId,
                        bytesField(5, new byte[0]),
                        "non-rid",
                        new byte[0]))),
                response(1, null)));
    }

    private static byte[] group(int count, String sn, long userId, long groupId) {
        return concat(
                varintField(1, groupId),
                varintField(2, 1_725_000_000L),
                bytesField(3, sn.getBytes(StandardCharsets.UTF_8)),
                varintField(4, userId),
                varintField(5, count),
                varintField(90, 9),
                fixed32Field(91, 0x11223344));
    }

    private static byte[] ridLicense(long id, long level) {
        return license(id, bytesField(7, varintField(1, level)), "rid", new byte[0]);
    }

    private static byte[] license(long id, byte[] data, String description, byte[] extras) {
        return concat(
                varintField(1, id),
                bytesField(2, description.getBytes(StandardCharsets.UTF_8)),
                bytesField(6, data),
                extras);
    }

    private static byte[] page(int status, byte[] license) {
        return concat(new byte[] {(byte) status}, license);
    }

    private static FlysafeRidInventory.Response response(int ccode, byte[] data) {
        return new FlysafeRidInventory.Response(true, ccode, data);
    }

    private static byte[] varintField(int number, long value) {
        return concat(varint(((long) number) << 3), varint(value));
    }

    private static byte[] bytesField(int number, byte[] value) {
        return concat(
                varint((((long) number) << 3) | 2L),
                varint(value.length),
                value);
    }

    private static byte[] fixed32Field(int number, int value) {
        return concat(
                varint((((long) number) << 3) | 5L),
                new byte[] {
                        (byte) value,
                        (byte) (value >>> 8),
                        (byte) (value >>> 16),
                        (byte) (value >>> 24)
                });
    }

    private static byte[] varint(long value) {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        long remaining = value;
        while ((remaining & ~0x7fL) != 0L) {
            output.write(((int) remaining & 0x7f) | 0x80);
            remaining >>>= 7;
        }
        output.write((int) remaining);
        return output.toByteArray();
    }

    private static byte[] concat(byte[]... values) {
        int length = 0;
        for (byte[] value : values) {
            length += value.length;
        }
        byte[] result = new byte[length];
        int offset = 0;
        for (byte[] value : values) {
            System.arraycopy(value, 0, result, offset, value.length);
            offset += value.length;
        }
        return result;
    }

    private static boolean allZero(byte[] value) {
        for (byte item : value) {
            if (item != 0) {
                return false;
            }
        }
        return true;
    }

    private static final class ScriptedTransport implements FlysafeRidInventory.Transport {
        private final List<FlysafeRidInventory.Response> responses;
        private int next;
        final List<byte[]> payloads = new ArrayList<>();

        ScriptedTransport(FlysafeRidInventory.Response... responses) {
            this.responses = Arrays.asList(responses);
        }

        @Override
        public FlysafeRidInventory.Response fetch(byte[] payload) {
            payloads.add(Arrays.copyOf(payload, payload.length));
            if (next >= responses.size()) {
                throw new AssertionError("unexpected fetch");
            }
            return responses.get(next++);
        }
    }
}
