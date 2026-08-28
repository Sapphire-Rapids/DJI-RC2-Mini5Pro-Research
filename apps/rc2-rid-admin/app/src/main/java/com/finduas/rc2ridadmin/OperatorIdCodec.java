package com.finduas.rc2ridadmin;

import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Locale;
import java.util.MissingResourceException;
import java.util.Set;

/** Exact DJI Fly 1.21.10 validation and wire encoding for EASA OPID 0x03/0x78. */
final class OperatorIdCodec {
    private static final Set<String> ISO3 = buildIso3Set();

    private OperatorIdCodec() {
    }

    static byte[] encodeSetPayload(String input) {
        String error = validationError(input);
        if (error != null) {
            throw new IllegalArgumentException(error);
        }
        byte[] complete = input.getBytes(StandardCharsets.US_ASCII);
        byte[] payload = new byte[18];
        payload[0] = 0x00;
        payload[1] = 0x10;
        System.arraycopy(complete, 0, payload, 2, 16);
        return payload;
    }

    static byte[] encodeRawPublic16(byte[] public16) {
        if (public16 == null || public16.length != 16) {
            throw new IllegalArgumentException("运营人编号公开部分必须是 16 字节");
        }
        byte[] payload = new byte[18];
        payload[0] = 0x00;
        payload[1] = 0x10;
        System.arraycopy(public16, 0, payload, 2, 16);
        return payload;
    }

    static String validationError(String input) {
        if (input == null || input.length() != 20) {
            return "请输入完整 20 字符 EASA 运营人编号";
        }
        String country = input.substring(0, 3);
        if (!ISO3.contains(country)) {
            return "前三位必须是 ISO 3166-1 三字母国家码";
        }

        String check = input.substring(3, 15)
                + input.substring(17, 20)
                + input.charAt(15);
        int factor = 1;
        int sum = 0;
        for (int index = check.length() - 1; index >= 0; index--) {
            int value = base36(check.charAt(index));
            if (value < 0) {
                return "编号主体、校验位和后三位只能使用 0-9 或小写 a-z";
            }
            int product = value * factor;
            sum += product / 36 + product % 36;
            factor = factor == 1 ? 2 : 1;
        }
        if (sum % 36 != 0) {
            return "Luhn mod-36 校验失败";
        }
        return null;
    }

    private static int base36(char value) {
        if (value >= '0' && value <= '9') {
            return value - '0';
        }
        if (value >= 'a' && value <= 'z') {
            return value - 'a' + 10;
        }
        return -1;
    }

    private static Set<String> buildIso3Set() {
        Set<String> result = new HashSet<>();
        for (String alpha2 : Locale.getISOCountries()) {
            try {
                result.add(new Locale("", alpha2).getISO3Country().toUpperCase(Locale.US));
            } catch (MissingResourceException ignored) {
                // Android's locale table can omit obsolete country entries.
            }
        }
        return result;
    }
}
