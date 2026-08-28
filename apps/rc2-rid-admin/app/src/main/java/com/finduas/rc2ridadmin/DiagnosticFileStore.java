package com.finduas.rc2ridadmin;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;

/** Atomic latest-result replacement inside the app-specific external files directory. */
final class DiagnosticFileStore {
    private DiagnosticFileStore() {
    }

    static File writeLatest(File directory, String report) throws IOException {
        if (directory == null) {
            throw new IOException("external diagnostics directory is unavailable");
        }
        if (!directory.isDirectory() && !directory.mkdirs()) {
            throw new IOException("cannot create diagnostics directory");
        }

        File target = new File(directory, "latest.txt");
        File temporary = File.createTempFile("latest-", ".tmp", directory);
        boolean moved = false;
        try {
            try (FileOutputStream output = new FileOutputStream(temporary);
                    OutputStreamWriter writer = new OutputStreamWriter(
                            output, StandardCharsets.UTF_8)) {
                writer.write(report);
                writer.flush();
                output.getFD().sync();
            }
            Files.move(
                    temporary.toPath(),
                    target.toPath(),
                    StandardCopyOption.ATOMIC_MOVE,
                    StandardCopyOption.REPLACE_EXISTING);
            moved = true;
            return target;
        } finally {
            if (!moved) {
                // Best effort only; a failed atomic replace must never damage the previous result.
                temporary.delete();
            }
        }
    }
}
