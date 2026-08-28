package com.finduas.rc2ridadmin;

import android.content.ContentResolver;
import android.content.ContentUris;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.BaseColumns;
import android.provider.MediaStore;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;

/** Atomic latest-result replacement inside the app-specific external files directory. */
final class DiagnosticFileStore {
    private static final String PUBLIC_DIRECTORY = "Download/FindUAS/";
    private static final String PUBLIC_FILE_NAME = "FindUAS_RID_A033_latest.txt";

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

    /** Publishes the same privacy-reduced report in the RC 2 file manager's Download view. */
    static Uri writePublicDownload(Context context, String report) throws IOException {
        if (context == null || report == null) {
            throw new IllegalArgumentException("context and report are required");
        }
        ContentResolver resolver = context.getContentResolver();
        Uri collection = MediaStore.Downloads.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY);
        Uri target = findExistingPublicReport(resolver, collection);
        boolean inserted = false;
        if (target == null) {
            ContentValues values = new ContentValues();
            values.put(MediaStore.MediaColumns.DISPLAY_NAME, PUBLIC_FILE_NAME);
            values.put(MediaStore.MediaColumns.MIME_TYPE, "text/plain");
            values.put(MediaStore.MediaColumns.RELATIVE_PATH, PUBLIC_DIRECTORY);
            values.put(MediaStore.MediaColumns.IS_PENDING, 1);
            target = resolver.insert(collection, values);
            if (target == null) {
                throw new IOException("MediaStore insert returned null");
            }
            inserted = true;
        }

        try {
            try (ParcelFileDescriptor descriptor = resolver.openFileDescriptor(target, "w")) {
                if (descriptor == null) {
                    throw new IOException("MediaStore descriptor is unavailable");
                }
                try (FileOutputStream output = new FileOutputStream(descriptor.getFileDescriptor());
                        OutputStreamWriter writer = new OutputStreamWriter(
                                output, StandardCharsets.UTF_8)) {
                    writer.write(report);
                    writer.flush();
                    output.getFD().sync();
                }
            }
            if (inserted) {
                ContentValues publish = new ContentValues();
                publish.put(MediaStore.MediaColumns.IS_PENDING, 0);
                resolver.update(target, publish, null, null);
            }
            return target;
        } catch (IOException | RuntimeException exception) {
            if (inserted) {
                resolver.delete(target, null, null);
            }
            if (exception instanceof IOException) {
                throw (IOException) exception;
            }
            throw new IOException("MediaStore write failed", exception);
        }
    }

    static String publicRelativeLocation() {
        return PUBLIC_DIRECTORY + PUBLIC_FILE_NAME;
    }

    private static Uri findExistingPublicReport(
            ContentResolver resolver,
            Uri collection) throws IOException {
        String[] projection = {BaseColumns._ID};
        String selection = MediaStore.MediaColumns.DISPLAY_NAME + "=? AND "
                + MediaStore.MediaColumns.RELATIVE_PATH + "=?";
        String[] arguments = {PUBLIC_FILE_NAME, PUBLIC_DIRECTORY};
        try (Cursor cursor = resolver.query(
                collection, projection, selection, arguments, null)) {
            if (cursor == null || !cursor.moveToFirst()) {
                return null;
            }
            long id = cursor.getLong(cursor.getColumnIndexOrThrow(BaseColumns._ID));
            return ContentUris.withAppendedId(collection, id);
        } catch (RuntimeException exception) {
            throw new IOException("MediaStore query failed", exception);
        }
    }
}
