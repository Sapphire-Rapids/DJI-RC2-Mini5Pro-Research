package com.finduas.ridobserver

import android.content.ContentValues
import android.content.Context
import android.os.Build
import android.os.Environment
import android.os.storage.StorageManager
import android.provider.MediaStore
import android.net.Uri
import java.io.File
import java.io.FileInputStream
import java.io.IOException
import java.io.InputStream
import java.io.OutputStream
import java.security.MessageDigest
import java.util.UUID
import java.util.zip.Deflater
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

internal enum class InstalledFlySampleExportStatus {
    SUCCESS, PACKAGE_UNAVAILABLE, WRONG_VERSION, SOURCE_MISSING, SOURCE_CHANGED,
    SOURCE_READ_FAILED, SIZE_LIMIT_EXCEEDED, NO_SD_CARD, AMBIGUOUS_SD_CARD,
    VOLUME_UNAVAILABLE, OUTPUT_FAILED
}

internal enum class InstalledFlySampleCleanupStatus { NOT_NEEDED, REMOVED, FAILED }

internal data class InstalledFlySampleExportResult(
    val status: InstalledFlySampleExportStatus,
    val displayName: String? = null,
    val totalBytes: Long = 0,
    val failedEntry: String? = null,
    val missingOptional: List<String> = emptyList(),
    val cleanupStatus: InstalledFlySampleCleanupStatus = InstalledFlySampleCleanupStatus.NOT_NEEDED
) {
    val relativeDirectory: String get() = InstalledFlySampleExporter.RELATIVE_DIRECTORY
}

/** Copies only the fixed installed Fly package and three fixed native-library names. */
internal object InstalledFlySampleExporter {
    const val PACKAGE_NAME = "dji.go.v5"
    const val VERSION_NAME = "1.19.4"
    const val VERSION_CODE = 3113157L
    const val RELATIVE_DIRECTORY = "Download/FindUAS/Samples/"
    const val FILE_PREFIX = "FindUAS_Fly1194_"
    const val MAX_FILE_BYTES = 1024L * 1024 * 1024
    const val MAX_TOTAL_BYTES = 2L * MAX_FILE_BYTES
    const val BUFFER_BYTES = 64 * 1024

    internal enum class Entry(val archiveName: String, val required: Boolean) {
        APK("DJI_FLY.apk", true),
        JNI("libsdk_jni.so", true),
        KEY_VALUE("libsdk_key_value.so", false),
        BASE("libsdk_base.so", false)
    }

    internal data class Identity(
        val versionName: String?, val versionCode: Long,
        val sourceApkPath: String? = null, val nativeDirectoryPath: String? = null
    )
    internal data class Metadata(val size: Long, val modifiedAtMs: Long)
    internal data class Volume(
        val removable: Boolean, val mounted: Boolean, val primary: Boolean,
        val emulated: Boolean, val mediaStoreName: String?, val uuid: String?
    )

    internal interface Source {
        fun identity(): Identity
        fun metadata(entry: Entry): Metadata?
        fun open(entry: Entry): InputStream
    }

    internal interface PendingZip
    internal interface Store {
        val apiLevel: Int
        fun volumes(): List<Volume>
        fun externalVolumeNames(): Set<String>
        fun insertPending(volumeName: String, displayName: String): PendingZip?
        fun openOutput(pending: PendingZip): OutputStream?
        fun publish(pending: PendingZip): Boolean
        fun remove(pending: PendingZip): Boolean
    }

    private data class Planned(val entry: Entry, val metadata: Metadata)
    private data class Copied(val entry: Entry, val size: Long, val sha256: String)
    private class Failure(
        val status: InstalledFlySampleExportStatus, val entry: Entry? = null
    ) : IOException(status.name)

    fun export(
        context: Context,
        progress: (Long) -> Unit = {}
    ): InstalledFlySampleExportResult = export(
        AndroidSource(context.applicationContext), AndroidStore(context.applicationContext), progress
    )

    internal fun export(
        source: Source, store: Store, progress: (Long) -> Unit = {}
    ): InstalledFlySampleExportResult {
        val identity = try {
            source.identity()
        } catch (_: Exception) {
            return InstalledFlySampleExportResult(InstalledFlySampleExportStatus.PACKAGE_UNAVAILABLE)
        }
        if (identity.versionName != VERSION_NAME || identity.versionCode != VERSION_CODE) {
            return InstalledFlySampleExportResult(InstalledFlySampleExportStatus.WRONG_VERSION)
        }
        val plan = mutableListOf<Planned>()
        val missing = mutableListOf<String>()
        var expectedTotal = 0L
        for (entry in Entry.values()) {
            val metadata = try {
                source.metadata(entry)
            } catch (_: Exception) {
                return InstalledFlySampleExportResult(
                    InstalledFlySampleExportStatus.SOURCE_READ_FAILED, failedEntry = entry.archiveName
                )
            }
            if (metadata == null) {
                if (entry.required) return InstalledFlySampleExportResult(
                    InstalledFlySampleExportStatus.SOURCE_MISSING, failedEntry = entry.archiveName
                )
                missing += entry.archiveName
                continue
            }
            if (metadata.size < 0 || metadata.size > MAX_FILE_BYTES ||
                expectedTotal > MAX_TOTAL_BYTES - metadata.size
            ) return InstalledFlySampleExportResult(
                InstalledFlySampleExportStatus.SIZE_LIMIT_EXCEEDED, failedEntry = entry.archiveName
            )
            expectedTotal += metadata.size
            plan += Planned(entry, metadata)
        }

        val volumeName = try {
            val candidates = store.volumes().filter {
                it.removable && it.mounted && !it.primary && !it.emulated
            }
            if (candidates.isEmpty()) return InstalledFlySampleExportResult(
                InstalledFlySampleExportStatus.NO_SD_CARD
            )
            if (candidates.size != 1) return InstalledFlySampleExportResult(
                InstalledFlySampleExportStatus.AMBIGUOUS_SD_CARD
            )
            val selected = candidates.single()
            val names = store.externalVolumeNames()
            val name = if (store.apiLevel >= 30) {
                selected.mediaStoreName?.takeIf { it in names }
            } else {
                selected.uuid?.let { uuid -> names.singleOrNull { it.equals(uuid, true) } }
            }
            if (name == null || name == MediaStore.VOLUME_EXTERNAL ||
                name == MediaStore.VOLUME_EXTERNAL_PRIMARY ||
                !Regex("[a-z0-9][a-z0-9_-]{0,127}").matches(name)
            ) return InstalledFlySampleExportResult(InstalledFlySampleExportStatus.VOLUME_UNAVAILABLE)
            name
        } catch (_: Exception) {
            return InstalledFlySampleExportResult(InstalledFlySampleExportStatus.VOLUME_UNAVAILABLE)
        }

        val displayName = "$FILE_PREFIX${UUID.randomUUID()}.zip"
        var pending: PendingZip? = null
        var published = false
        var totalBytes = 0L
        var cleanup = InstalledFlySampleCleanupStatus.NOT_NEEDED
        var failedEntry: String? = null
        val status = try {
            pending = store.insertPending(volumeName, displayName)
            val created = pending ?: throw Failure(InstalledFlySampleExportStatus.OUTPUT_FAILED)
            val output = store.openOutput(created)
                ?: throw Failure(InstalledFlySampleExportStatus.OUTPUT_FAILED)
            val copied = mutableListOf<Copied>()
            ZipOutputStream(output).use { zip ->
                zip.setLevel(Deflater.NO_COMPRESSION)
                val buffer = ByteArray(BUFFER_BYTES)
                for (item in plan) {
                    requireUnchanged(source, item)
                    val digest = MessageDigest.getInstance("SHA-256")
                    val input = try {
                        source.open(item.entry)
                    } catch (_: Exception) {
                        throw Failure(InstalledFlySampleExportStatus.SOURCE_READ_FAILED, item.entry)
                    }
                    var entryBytes = 0L
                    input.use {
                        zip.putNextEntry(ZipEntry(item.entry.archiveName))
                        while (true) {
                            val count = try {
                                it.read(buffer)
                            } catch (_: Exception) {
                                throw Failure(InstalledFlySampleExportStatus.SOURCE_READ_FAILED, item.entry)
                            }
                            if (count < 0) break
                            if (count == 0) throw Failure(
                                InstalledFlySampleExportStatus.SOURCE_READ_FAILED, item.entry
                            )
                            if (entryBytes > item.metadata.size - count ||
                                totalBytes > MAX_TOTAL_BYTES - count
                            ) throw Failure(InstalledFlySampleExportStatus.SOURCE_CHANGED, item.entry)
                            zip.write(buffer, 0, count)
                            digest.update(buffer, 0, count)
                            entryBytes += count
                            totalBytes += count
                            // UI progress cannot invalidate a successfully copied source chunk.
                            try { progress(totalBytes) } catch (_: Exception) { }
                        }
                    }
                    if (entryBytes != item.metadata.size) throw Failure(
                        InstalledFlySampleExportStatus.SOURCE_CHANGED, item.entry
                    )
                    requireUnchanged(source, item)
                    zip.closeEntry()
                    copied += Copied(item.entry, entryBytes, hex(digest.digest()))
                }
                val finalIdentity = try {
                    source.identity()
                } catch (_: Exception) {
                    throw Failure(InstalledFlySampleExportStatus.SOURCE_CHANGED)
                }
                if (finalIdentity != identity) throw Failure(InstalledFlySampleExportStatus.SOURCE_CHANGED)
                zip.putNextEntry(ZipEntry("manifest.json"))
                zip.write(manifest(copied, missing, totalBytes).toByteArray(Charsets.UTF_8))
                zip.closeEntry()
            }
            // Closing the ZIP and its underlying stream must finish before publication.
            if (!store.publish(created)) throw Failure(InstalledFlySampleExportStatus.OUTPUT_FAILED)
            published = true
            InstalledFlySampleExportStatus.SUCCESS
        } catch (failure: Failure) {
            failedEntry = failure.entry?.archiveName
            failure.status
        } catch (_: Exception) {
            InstalledFlySampleExportStatus.OUTPUT_FAILED
        } finally {
            val created = pending
            if (!published && created != null) {
                cleanup = try {
                    if (store.remove(created)) InstalledFlySampleCleanupStatus.REMOVED
                    else InstalledFlySampleCleanupStatus.FAILED
                } catch (_: Exception) {
                    InstalledFlySampleCleanupStatus.FAILED
                }
            }
        }
        return InstalledFlySampleExportResult(
            status, if (published) displayName else null, totalBytes, failedEntry,
            missing.toList(), cleanup
        )
    }

    private fun requireUnchanged(source: Source, planned: Planned) {
        val observed = try {
            source.metadata(planned.entry)
        } catch (_: Exception) {
            throw Failure(InstalledFlySampleExportStatus.SOURCE_READ_FAILED, planned.entry)
        }
        if (observed != planned.metadata) throw Failure(
            InstalledFlySampleExportStatus.SOURCE_CHANGED, planned.entry
        )
    }

    private fun hex(bytes: ByteArray): String = bytes.joinToString("") { "%02x".format(it) }

    private fun manifest(files: List<Copied>, missing: List<String>, totalBytes: Long): String =
        buildString {
            append("{\"schema\":\"finduas-installed-fly-sample/v1\",\"package\":\"$PACKAGE_NAME\",")
            append("\"versionName\":\"$VERSION_NAME\",\"versionCode\":$VERSION_CODE,")
            append("\"totalSourceBytes\":$totalBytes,\"files\":[")
            append(files.joinToString(",") {
                "{\"entry\":\"${it.entry.archiveName}\",\"size\":${it.size},\"sha256\":\"${it.sha256}\"}"
            })
            append("],\"missingOptional\":[")
            append(missing.joinToString(",") { "\"$it\"" })
            append("]}\n")
        }

    private class AndroidSource(context: Context) : Source {
        private val manager = context.packageManager
        private var pinnedIdentity: Identity? = null

        override fun identity(): Identity {
            val info = manager.getPackageInfo(PACKAGE_NAME, 0)
            val application = info.applicationInfo ?: throw IOException("Package unavailable")
            val observed = Identity(info.versionName, info.longVersionCode,
                application.sourceDir, application.nativeLibraryDir)
            if (pinnedIdentity == null) pinnedIdentity = observed
            return observed
        }

        private fun file(entry: Entry): File? = if (entry == Entry.APK) {
            pinnedIdentity?.sourceApkPath?.let { File(it) }
        } else {
            pinnedIdentity?.nativeDirectoryPath?.let { File(it, entry.archiveName) }
        }

        override fun metadata(entry: Entry): Metadata? {
            val file = file(entry) ?: return null
            return if (file.isFile) Metadata(file.length(), file.lastModified()) else null
        }

        override fun open(entry: Entry): InputStream =
            FileInputStream(file(entry) ?: throw IOException("Fixed source unavailable"))
    }

    private class AndroidPendingZip(val owner: AndroidStore, val uri: Uri) : PendingZip

    private class AndroidStore(private val context: Context) : Store {
        private val resolver = context.contentResolver
        override val apiLevel: Int get() = Build.VERSION.SDK_INT

        override fun volumes(): List<Volume> {
            val manager = context.getSystemService(StorageManager::class.java)
                ?: throw IOException("Storage manager unavailable")
            return manager.storageVolumes.map {
                Volume(it.isRemovable, it.state == Environment.MEDIA_MOUNTED,
                    it.isPrimary, it.isEmulated,
                    if (Build.VERSION.SDK_INT >= 30) it.mediaStoreVolumeName else null, it.uuid)
            }
        }

        override fun externalVolumeNames(): Set<String> = MediaStore.getExternalVolumeNames(context)

        override fun insertPending(volumeName: String, displayName: String): PendingZip? {
            val collection = MediaStore.Downloads.getContentUri(volumeName)
            val values = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, displayName)
                put(MediaStore.MediaColumns.MIME_TYPE, "application/zip")
                put(MediaStore.MediaColumns.RELATIVE_PATH, RELATIVE_DIRECTORY)
                put(MediaStore.MediaColumns.IS_PENDING, 1)
            }
            val uri = resolver.insert(collection, values) ?: return null
            if (uri.scheme != "content" || uri.authority != collection.authority ||
                uri.pathSegments.dropLast(1) != collection.pathSegments ||
                (uri.lastPathSegment?.toLongOrNull() ?: 0L) <= 0L
            ) throw IOException("Unexpected sample URI")
            return AndroidPendingZip(this, uri)
        }

        override fun openOutput(pending: PendingZip): OutputStream? =
            resolver.openOutputStream(ownedUri(pending), "w")

        override fun publish(pending: PendingZip): Boolean {
            val values = ContentValues().apply { put(MediaStore.MediaColumns.IS_PENDING, 0) }
            return resolver.update(ownedUri(pending), values, null, null) == 1
        }

        override fun remove(pending: PendingZip): Boolean =
            resolver.delete(ownedUri(pending), null, null) == 1

        private fun ownedUri(pending: PendingZip): Uri {
            val owned = pending as? AndroidPendingZip ?: throw IOException("Foreign sample handle")
            if (owned.owner !== this) throw IOException("Foreign sample owner")
            return owned.uri
        }
    }
}
