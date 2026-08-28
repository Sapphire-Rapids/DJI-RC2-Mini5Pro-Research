package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public final class DirectDiagnosticReportTest {
    @Test
    public void formatsStableUtf8TextEnvelopeWithoutDroppingResultLines() {
        String report = DirectDiagnosticReport.format(
                "0.7.1-test",
                "2026-08-29T08:00:00Z",
                "DIRECT_RESULT\r\nline two\rline three\u0000");

        assertEquals(
                "schema=finduas-rc2-rid-direct-diagnostic/v1\n"
                        + "version=0.7.1-test\n"
                        + "time=2026-08-29T08:00:00Z\n"
                        + "operation=active-readonly-flysafe-11-11\n"
                        + "result:\nDIRECT_RESULT\nline two\nline three?\n",
                report);
    }

    @Test
    public void headerFieldsCannotInjectAdditionalLines() {
        String report = DirectDiagnosticReport.format(
                "version\nforged=value",
                "time\rforged=value",
                "result");

        assertTrue(report.contains("version=version forged=value\n"));
        assertTrue(report.contains("time=time forged=value\n"));
        assertFalse(report.contains("\nforged=value\n"));
    }

    @Test
    public void rejectsMissingRequiredField() {
        assertThrows(IllegalArgumentException.class, () ->
                DirectDiagnosticReport.format("version", "time", null));
    }
}
