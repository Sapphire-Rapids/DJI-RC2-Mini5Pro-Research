package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public final class DiagnosticFileStoreTest {
    @Test
    public void publicDiagnosticUsesOneStableDedicatedDownloadPath() {
        assertEquals(
                "Download/FindUAS/FindUAS_RID_A033_latest.txt",
                DiagnosticFileStore.publicRelativeLocation());
    }
}
