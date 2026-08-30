package com.finduas.ridobserver

import android.content.ContentResolver
import android.content.ContentValues
import android.content.Context
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.os.storage.StorageManager
import android.provider.MediaStore
import java.io.IOException
import java.util.UUID

internal enum class ProbeReportSaveStatus {
    SAVED,
    INVALID_RUN_METADATA,
    REPORT_INCOMPLETE,
    REPORT_TOO_LARGE,
    NO_MOUNTED_REMOVABLE_VOLUME,
    MULTIPLE_MOUNTED_REMOVABLE_VOLUMES,
    MEDIASTORE_VOLUME_UNAVAILABLE,
    VOLUME_DISCOVERY_FAILED,
    INSERT_FAILED,
    WRITE_FAILED,
    PUBLISH_FAILED
}

internal enum class ProbeReportCleanupStatus { NOT_NEEDED, REMOVED, FAILED }

internal data class ProbeReportSaveResult(
    val status: ProbeReportSaveStatus,
    val displayName: String? = null,
    val cleanupStatus: ProbeReportCleanupStatus = ProbeReportCleanupStatus.NOT_NEEDED
) {
    val relativeDirectory: String get() = ProbeReportStore.RELATIVE_DIRECTORY
}

/** A single new report in MediaStore on the unique mounted removable volume; no file-path API. */
internal object ProbeReportStore {
    const val RELATIVE_DIRECTORY = "Download/FindUAS/Probe/"
    const val FILE_PREFIX = "FindUAS_Probe_v012_"
    const val MAX_REPORT_BYTES = 256 * 1024
    private val canonicalRunId = Regex(
        "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    )
    private val volumeNamePattern = Regex("[a-z0-9][a-z0-9_-]{0,127}")

    internal data class Volume(
        val removable: Boolean,
        val mounted: Boolean,
        val primary: Boolean,
        val emulated: Boolean,
        val mediaStoreName: String?,
        val uuid: String?
    )

    internal interface PendingReport

    /** A small fakeable boundary; production handles are private and bound to their creator. */
    internal interface Store {
        val apiLevel: Int
        fun volumes(): List<Volume>
        fun externalVolumeNames(): Set<String>
        fun insertPending(volumeName: String, displayName: String): PendingReport?
        fun writeUtf8(report: PendingReport, text: String)
        fun publish(report: PendingReport): Boolean
        fun remove(report: PendingReport): Boolean
    }

    fun saveCompletedReport(
        context: Context,
        report: String,
        completedAtMs: Long,
        runId: String
    ): ProbeReportSaveResult = saveCompletedReport(
        AndroidStore(context.applicationContext), report, completedAtMs, runId
    )

    internal fun saveCompletedReport(
        store: Store,
        report: String,
        completedAtMs: Long,
        runId: String
    ): ProbeReportSaveResult {
        if (completedAtMs < 0 || !canonicalRunId.matches(runId)) {
            return ProbeReportSaveResult(ProbeReportSaveStatus.INVALID_RUN_METADATA)
        }
        // Reject before volume discovery or insert; never publish a truncated report.
        if (report.length > MAX_REPORT_BYTES ||
            report.toByteArray(Charsets.UTF_8).size > MAX_REPORT_BYTES
        ) {
            return ProbeReportSaveResult(ProbeReportSaveStatus.REPORT_TOO_LARGE)
        }
        if (!report.trimEnd().endsWith("\nreport_file_end=true")) {
            return ProbeReportSaveResult(ProbeReportSaveStatus.REPORT_INCOMPLETE)
        }
        val candidates: List<Volume>
        val externalNames: Set<String>
        try {
            candidates = store.volumes().filter {
                it.removable && it.mounted && !it.primary && !it.emulated
            }
            if (candidates.isEmpty()) {
                return ProbeReportSaveResult(ProbeReportSaveStatus.NO_MOUNTED_REMOVABLE_VOLUME)
            }
            if (candidates.size != 1) {
                return ProbeReportSaveResult(ProbeReportSaveStatus.MULTIPLE_MOUNTED_REMOVABLE_VOLUMES)
            }
            externalNames = store.externalVolumeNames()
        } catch (_: Exception) {
            return ProbeReportSaveResult(ProbeReportSaveStatus.VOLUME_DISCOVERY_FAILED)
        }
        val selected = candidates.single()
        val volumeName = if (store.apiLevel >= 30) {
            selected.mediaStoreName?.takeIf { it in externalNames }
        } else {
            selected.uuid?.let { uuid ->
                externalNames.filter { it.equals(uuid, ignoreCase = true) }.singleOrNull()
            }
        }
        if (volumeName == null || !volumeNamePattern.matches(volumeName) ||
            volumeName == MediaStore.VOLUME_EXTERNAL_PRIMARY || volumeName == MediaStore.VOLUME_EXTERNAL
        ) {
            return ProbeReportSaveResult(ProbeReportSaveStatus.MEDIASTORE_VOLUME_UNAVAILABLE)
        }

        // A retry of the same completed run must not reuse a possibly published filename.
        val attemptId = UUID.randomUUID().toString()
        val displayName = "$FILE_PREFIX${completedAtMs}_${runId}_$attemptId.txt"
        var inserted: PendingReport? = null
        var failureStage = ProbeReportSaveStatus.INSERT_FAILED
        var published = false
        var cleanup = ProbeReportCleanupStatus.NOT_NEEDED
        val status = try {
            inserted = store.insertPending(volumeName, displayName)
            val pending = inserted
            if (pending == null) {
                ProbeReportSaveStatus.INSERT_FAILED
            } else {
                failureStage = ProbeReportSaveStatus.WRITE_FAILED
                store.writeUtf8(pending, report)
                failureStage = ProbeReportSaveStatus.PUBLISH_FAILED
                if (!store.publish(pending)) throw IOException("Report publication failed")
                published = true
                ProbeReportSaveStatus.SAVED
            }
        } catch (_: Exception) {
            failureStage
        } finally {
            // Never query, replace or delete an older report, and never select another volume.
            val pending = inserted
            if (!published && pending != null) {
                cleanup = try {
                    if (store.remove(pending)) ProbeReportCleanupStatus.REMOVED
                    else ProbeReportCleanupStatus.FAILED
                } catch (_: Exception) {
                    ProbeReportCleanupStatus.FAILED
                }
            }
        }
        return ProbeReportSaveResult(
            status = status,
            displayName = if (published) displayName else null,
            cleanupStatus = cleanup
        )
    }

    private class AndroidPendingReport(val owner: AndroidStore, val uri: Uri) : PendingReport

    private class AndroidStore(private val context: Context) : Store {
        private val resolver: ContentResolver = context.contentResolver
        override val apiLevel: Int get() = Build.VERSION.SDK_INT

        override fun volumes(): List<Volume> {
            val manager = context.getSystemService(StorageManager::class.java)
                ?: throw IOException("Storage manager unavailable")
            return manager.storageVolumes.map { volume ->
                Volume(
                    removable = volume.isRemovable,
                    mounted = volume.state == Environment.MEDIA_MOUNTED,
                    primary = volume.isPrimary,
                    emulated = volume.isEmulated,
                    mediaStoreName = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                        volume.mediaStoreVolumeName
                    } else null,
                    uuid = volume.uuid
                )
            }
        }

        override fun externalVolumeNames(): Set<String> = MediaStore.getExternalVolumeNames(context)

        override fun insertPending(volumeName: String, displayName: String): PendingReport? {
            val collection = MediaStore.Downloads.getContentUri(volumeName)
            val values = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, displayName)
                put(MediaStore.MediaColumns.MIME_TYPE, "text/plain")
                put(MediaStore.MediaColumns.RELATIVE_PATH, RELATIVE_DIRECTORY)
                put(MediaStore.MediaColumns.IS_PENDING, 1)
            }
            val uri = resolver.insert(collection, values) ?: return null
            // Reject an unexpected provider return instead of opening/deleting an unrelated URI.
            if (uri.scheme != "content" || uri.authority != collection.authority ||
                uri.pathSegments.dropLast(1) != collection.pathSegments ||
                (uri.lastPathSegment?.toLongOrNull() ?: 0L) <= 0L
            ) {
                throw IOException("Unexpected inserted report URI")
            }
            return AndroidPendingReport(this, uri)
        }

        override fun writeUtf8(report: PendingReport, text: String) {
            val uri = ownedUri(report)
            val stream = resolver.openOutputStream(uri, "w")
                ?: throw IOException("Report stream unavailable")
            stream.use {
                it.write(text.toByteArray(Charsets.UTF_8))
                it.flush()
            }
        }

        override fun publish(report: PendingReport): Boolean {
            val values = ContentValues().apply { put(MediaStore.MediaColumns.IS_PENDING, 0) }
            return resolver.update(ownedUri(report), values, null, null) == 1
        }

        override fun remove(report: PendingReport): Boolean =
            resolver.delete(ownedUri(report), null, null) == 1

        private fun ownedUri(report: PendingReport): Uri {
            val pending = report as? AndroidPendingReport
                ?: throw IOException("Foreign report handle")
            if (pending.owner !== this) throw IOException("Foreign report owner")
            return pending.uri
        }
    }
}
