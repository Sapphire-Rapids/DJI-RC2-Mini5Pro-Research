package com.finduas.ridobserver

import java.io.File
import java.io.FileNotFoundException
import java.security.MessageDigest
import java.util.zip.ZipException
import java.util.zip.ZipFile

internal enum class ArchiveEntryProbeState {
    PRESENT,
    ABSENT,
    READ_DENIED,
    TOO_LARGE,
    INTERNAL_ERROR
}

internal data class ArchiveEntryCapability(
    val label: String,
    val state: ArchiveEntryProbeState = ArchiveEntryProbeState.INTERNAL_ERROR,
    val archivePath: String? = null,
    val entryName: String? = null,
    val uncompressedBytes: Long? = null,
    val sha256: String? = null,
    val matchesReference: Boolean? = null
)

/**
 * Hashes one fixed ZIP entry without extracting it or loading it as code. The byte ceiling is a
 * fail-closed guard against a malformed or unexpectedly large package entry.
 */
internal object ArchiveFingerprint {
    internal const val MAX_ENTRY_BYTES = 128L * 1024L * 1024L

    fun fixedEntry(
        archivePaths: List<String>,
        label: String,
        entryName: String,
        expectedSha256: String
    ): ArchiveEntryCapability {
        var sawReadDenied = false
        var sawInternalError = false
        for (archivePath in archivePaths.distinct()) {
            try {
                ZipFile(archivePath).use { zip ->
                    val entry = zip.getEntry(entryName) ?: return@use
                    if (entry.isDirectory) {
                        return ArchiveEntryCapability(
                            label = label,
                            state = ArchiveEntryProbeState.INTERNAL_ERROR,
                            archivePath = archivePath,
                            entryName = entryName
                        )
                    }
                    if (entry.size > MAX_ENTRY_BYTES) {
                        return ArchiveEntryCapability(
                            label = label,
                            state = ArchiveEntryProbeState.TOO_LARGE,
                            archivePath = archivePath,
                            entryName = entryName,
                            uncompressedBytes = entry.size
                        )
                    }
                    val digest = MessageDigest.getInstance("SHA-256")
                    var total = 0L
                    zip.getInputStream(entry).buffered().use { input ->
                        val buffer = ByteArray(64 * 1024)
                        try {
                            while (true) {
                                val read = input.read(buffer)
                                if (read < 0) break
                                if (read == 0) continue
                                total += read
                                if (total > MAX_ENTRY_BYTES) {
                                    return ArchiveEntryCapability(
                                        label = label,
                                        state = ArchiveEntryProbeState.TOO_LARGE,
                                        archivePath = archivePath,
                                        entryName = entryName,
                                        uncompressedBytes = total
                                    )
                                }
                                digest.update(buffer, 0, read)
                            }
                        } finally {
                            buffer.fill(0)
                        }
                    }
                    val actual = PackageCapabilityPolicy.normalizeDigest(digest.digest())
                    return ArchiveEntryCapability(
                        label = label,
                        state = ArchiveEntryProbeState.PRESENT,
                        archivePath = archivePath,
                        entryName = entryName,
                        uncompressedBytes = total,
                        sha256 = actual,
                        matchesReference = actual == expectedSha256
                    )
                }
            } catch (_: SecurityException) {
                sawReadDenied = true
            } catch (_: FileNotFoundException) {
                sawReadDenied = true
            } catch (_: ZipException) {
                sawInternalError = true
            } catch (_: Throwable) {
                sawInternalError = true
            }
        }
        return ArchiveEntryCapability(
            label = label,
            state = when {
                sawReadDenied -> ArchiveEntryProbeState.READ_DENIED
                sawInternalError -> ArchiveEntryProbeState.INTERNAL_ERROR
                else -> ArchiveEntryProbeState.ABSENT
            },
            entryName = entryName
        )
    }

    fun archivePaths(sourceDir: String?, splitSourceDirs: Array<String>?): List<String> = buildList {
        if (!sourceDir.isNullOrBlank()) add(File(sourceDir).absolutePath)
        splitSourceDirs?.filterTo(this) { it.isNotBlank() }
    }
}
