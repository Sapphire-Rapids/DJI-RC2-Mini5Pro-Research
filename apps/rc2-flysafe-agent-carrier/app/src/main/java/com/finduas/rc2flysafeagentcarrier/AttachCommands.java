package com.finduas.rc2flysafeagentcarrier;

import java.io.File;

/** Fixed command strings shown to the operator; this class never executes them. */
final class AttachCommands {
    static final String TARGET_PACKAGE = "dji.go.v5";
    static final String AGENT_LIBRARY_NAME = "libfinduas_flysafe_query.so";
    static final String PID_COMMAND = "/system/bin/pidof " + TARGET_PACKAGE;
    static final String LOG_COMMAND =
            "/system/bin/logcat -d -s FindUAS-FlySafe-Raw:I";

    private AttachCommands() {
        throw new AssertionError("No instances");
    }

    static String libraryPath(String nativeLibraryDir) {
        if (nativeLibraryDir == null || nativeLibraryDir.isEmpty()) {
            throw new IllegalArgumentException("nativeLibraryDir is empty");
        }
        if (nativeLibraryDir.indexOf(' ') >= 0 || nativeLibraryDir.indexOf('\'') >= 0) {
            throw new IllegalArgumentException("nativeLibraryDir is not Runtime.exec-safe");
        }
        return new File(nativeLibraryDir, AGENT_LIBRARY_NAME).getAbsolutePath();
    }

    static String attachCommand(String nativeLibraryDir) {
        return "/system/bin/cmd activity attach-agent "
                + TARGET_PACKAGE
                + " "
                + libraryPath(nativeLibraryDir);
    }
}
