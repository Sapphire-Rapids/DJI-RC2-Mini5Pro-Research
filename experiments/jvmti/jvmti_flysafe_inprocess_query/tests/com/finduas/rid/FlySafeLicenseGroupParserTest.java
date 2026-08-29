package com.finduas.rid;

import java.io.ByteArrayOutputStream;

public final class FlySafeLicenseGroupParserTest {
    public static void main(String[] args) {
        parsesOneRidRecord();
        acceptsCanonicalEmptyGroupWithDefaultCount();
        preservesUniqueSelectionAcrossMixedRecords();
        rejectsCountMismatch();
        doesNotSelectAmbiguousRidRecords();
        System.out.println("FlySafeLicenseGroupParserTest: PASS");
    }

    private static void parsesOneRidRecord() {
        byte[] body = group(1, model(
                license(0x13572468, bytesField(7, varintField(1, 2))),
                status(true, true, false)));
        FlySafeLicenseGroupParser.Result result = FlySafeLicenseGroupParser.parse(body);
        require(result.declaredCount == 1, "declared count");
        require(result.recordCount == 1, "record count");
        require(result.ridCount == 1, "RID count");
        require(result.ridLicenseId == 0x13572468, "RID ID");
        require(result.ridLevel == 2, "RID level");
        require(result.enabled, "enabled");
        require(result.inValidDate, "valid date");
        require(!result.invalid, "invalid");
    }

    private static void preservesUniqueSelectionAcrossMixedRecords() {
        byte[] nonRid = model(license(7, bytesField(5, new byte[0])), status(false, true, false));
        byte[] rid = model(license(8, bytesField(7, varintField(1, 1))), status(false, false, true));
        FlySafeLicenseGroupParser.Result result = FlySafeLicenseGroupParser.parse(group(2, nonRid, rid));
        require(result.recordCount == 2, "mixed record count");
        require(result.ridCount == 1 && result.ridLicenseId == 8, "mixed RID selection");
        require(result.ridLevel == 1 && !result.enabled && result.invalid, "mixed RID state");
    }

    private static void acceptsCanonicalEmptyGroupWithDefaultCount() {
        FlySafeLicenseGroupParser.Result result =
                FlySafeLicenseGroupParser.parse(bytesField(2, new byte[0]));
        require(result.declaredCount == 0, "empty declared count");
        require(result.recordCount == 0 && result.ridCount == 0, "empty records");
    }

    private static void rejectsCountMismatch() {
        try {
            FlySafeLicenseGroupParser.parse(group(
                    2,
                    model(license(9, bytesField(7, varintField(1, 2))), status(false, true, false))));
            throw new AssertionError("count mismatch was accepted");
        } catch (FlySafeLicenseGroupParser.ParseException expected) {
            require(expected.getMessage().contains("mismatch"), "count mismatch detail");
        }
    }

    private static void doesNotSelectAmbiguousRidRecords() {
        byte[] first = model(license(10, bytesField(7, varintField(1, 1))), status(true, true, false));
        byte[] second = model(license(11, bytesField(7, varintField(1, 2))), status(false, true, false));
        FlySafeLicenseGroupParser.Result result = FlySafeLicenseGroupParser.parse(group(2, first, second));
        require(result.ridCount == 2, "ambiguous RID count");
        require(result.ridLicenseId == 0, "ambiguous RID ID must not escape");
    }

    private static byte[] group(int count, byte[]... models) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        write(out, bytesField(2, varintField(5, count)));
        for (byte[] model : models) {
            write(out, bytesField(4, model));
        }
        return out.toByteArray();
    }

    private static byte[] model(byte[] license, byte[] status) {
        return concat(bytesField(1, license), bytesField(2, status));
    }

    private static byte[] license(int id, byte[] data) {
        return concat(varintField(1, id), bytesField(6, data));
    }

    private static byte[] status(boolean enabled, boolean valid, boolean invalid) {
        return concat(
                varintField(1, enabled ? 1 : 0),
                varintField(2, valid ? 1 : 0),
                varintField(3, invalid ? 1 : 0));
    }

    private static byte[] varintField(int number, int value) {
        return concat(varint(number << 3), varint(value));
    }

    private static byte[] bytesField(int number, byte[] value) {
        return concat(varint((number << 3) | 2), varint(value.length), value);
    }

    private static byte[] varint(int value) {
        long unsigned = value & 0xffffffffL;
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        do {
            int current = (int) (unsigned & 0x7f);
            unsigned >>>= 7;
            out.write(unsigned == 0 ? current : current | 0x80);
        } while (unsigned != 0);
        return out.toByteArray();
    }

    private static byte[] concat(byte[]... parts) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        for (byte[] part : parts) {
            write(out, part);
        }
        return out.toByteArray();
    }

    private static void write(ByteArrayOutputStream out, byte[] bytes) {
        out.write(bytes, 0, bytes.length);
    }

    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
