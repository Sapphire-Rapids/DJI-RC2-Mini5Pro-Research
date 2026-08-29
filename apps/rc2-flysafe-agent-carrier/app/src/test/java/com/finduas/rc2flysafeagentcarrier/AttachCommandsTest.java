package com.finduas.rc2flysafeagentcarrier;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public final class AttachCommandsTest {
    @Test
    public void targetAndDiagnosticCommandsAreFixed() {
        assertEquals("dji.go.v5", AttachCommands.TARGET_PACKAGE);
        assertEquals("/system/bin/pidof dji.go.v5", AttachCommands.PID_COMMAND);
        assertEquals(
                "/system/bin/logcat -d -s FindUAS-FlySafe-Raw:I",
                AttachCommands.LOG_COMMAND);
    }

    @Test
    public void exactExtractedLibraryPathIsUsedWithoutShellQuotes() {
        String directory = "/data/app/com.finduas.test-1/lib/arm64";
        assertEquals(
                directory + "/libfinduas_flysafe_query.so",
                AttachCommands.libraryPath(directory));
        assertEquals(
                "/system/bin/cmd activity attach-agent dji.go.v5 "
                        + directory
                        + "/libfinduas_flysafe_query.so",
                AttachCommands.attachCommand(directory));
    }

    @Test(expected = IllegalArgumentException.class)
    public void runtimeExecUnsafeSpaceIsRejected() {
        AttachCommands.attachCommand("/data/app/path with space/lib/arm64");
    }

    @Test(expected = IllegalArgumentException.class)
    public void emptyNativeLibraryDirectoryIsRejected() {
        AttachCommands.attachCommand("");
    }
}
