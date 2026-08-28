package com.finduas.rc2ridadmin;

/** Pure formatter for the privacy-reduced active 11/11 diagnostic file. */
final class DirectDiagnosticReport {
    static final String SCHEMA = "finduas-rc2-rid-direct-diagnostic/v1";
    static final String OPERATION = "active-readonly-flysafe-11-11";

    private DirectDiagnosticReport() {
    }

    static String format(String version, String time, String result) {
        if (version == null || time == null || result == null) {
            throw new IllegalArgumentException("diagnostic fields are required");
        }
        return "schema=" + cleanSingleLine(SCHEMA)
                + "\nversion=" + cleanSingleLine(version)
                + "\ntime=" + cleanSingleLine(time)
                + "\noperation=" + cleanSingleLine(OPERATION)
                + "\nresult:\n" + cleanMultiline(result)
                + "\n";
    }

    static String cleanSingleLine(String value) {
        return cleanMultiline(value).replace('\n', ' ');
    }

    static String cleanMultiline(String value) {
        StringBuilder clean = new StringBuilder(value.length());
        for (int index = 0; index < value.length(); index++) {
            char item = value.charAt(index);
            if (item == '\r') {
                if (index + 1 < value.length() && value.charAt(index + 1) == '\n') {
                    index++;
                }
                clean.append('\n');
            } else if (item == '\n') {
                clean.append('\n');
            } else if (Character.isISOControl(item)) {
                clean.append('?');
            } else {
                clean.append(item);
            }
        }
        return clean.toString();
    }
}
