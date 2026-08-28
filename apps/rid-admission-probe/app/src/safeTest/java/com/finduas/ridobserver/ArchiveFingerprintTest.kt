package com.finduas.ridobserver

import java.nio.file.Files
import java.nio.file.Path
import java.security.MessageDigest
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ArchiveFingerprintTest {
    @Test
    fun hashesOnlyTheFixedEntryAndMatchesExactReference() {
        val payload = "fixed-read-only-payload".toByteArray()
        val archive = zipOf("classes16.dex" to payload, "ignored.bin" to byteArrayOf(1, 2, 3))
        try {
            val expected = sha256(payload)
            val result = ArchiveFingerprint.fixedEntry(
                archivePaths = listOf(archive.toString()),
                label = "test dex",
                entryName = "classes16.dex",
                expectedSha256 = expected
            )
            assertEquals(ArchiveEntryProbeState.PRESENT, result.state)
            assertEquals(payload.size.toLong(), result.uncompressedBytes)
            assertEquals(expected, result.sha256)
            assertTrue(result.matchesReference == true)
        } finally {
            Files.deleteIfExists(archive)
        }
    }

    @Test
    fun reportsExactEntryMismatchWithoutTreatingItAsAbsent() {
        val archive = zipOf("classes23.dex" to byteArrayOf(4, 5, 6))
        try {
            val result = ArchiveFingerprint.fixedEntry(
                archivePaths = listOf(archive.toString()),
                label = "test runner",
                entryName = "classes23.dex",
                expectedSha256 = "00".repeat(32)
            )
            assertEquals(ArchiveEntryProbeState.PRESENT, result.state)
            assertFalse(result.matchesReference == true)
        } finally {
            Files.deleteIfExists(archive)
        }
    }

    @Test
    fun distinguishesMissingFixedEntry() {
        val archive = zipOf("classes.dex" to byteArrayOf(7))
        try {
            val result = ArchiveFingerprint.fixedEntry(
                archivePaths = listOf(archive.toString()),
                label = "missing",
                entryName = "classes16.dex",
                expectedSha256 = "00".repeat(32)
            )
            assertEquals(ArchiveEntryProbeState.ABSENT, result.state)
            assertNull(result.sha256)
            assertNull(result.matchesReference)
        } finally {
            Files.deleteIfExists(archive)
        }
    }

    @Test
    fun normalizesBaseAndSplitArchivePathsWithoutInventingEntries() {
        assertEquals(
            listOf("/base.apk", "/split_a.apk", "/split_b.apk"),
            ArchiveFingerprint.archivePaths(
                "/base.apk",
                arrayOf("/split_a.apk", "", "/split_b.apk")
            )
        )
    }

    private fun zipOf(vararg entries: Pair<String, ByteArray>): Path {
        val path = Files.createTempFile("finduas-archive-fingerprint-", ".zip")
        ZipOutputStream(Files.newOutputStream(path)).use { output ->
            for ((name, bytes) in entries) {
                output.putNextEntry(ZipEntry(name))
                output.write(bytes)
                output.closeEntry()
            }
        }
        return path
    }

    private fun sha256(bytes: ByteArray): String = PackageCapabilityPolicy.normalizeDigest(
        MessageDigest.getInstance("SHA-256").digest(bytes)
    )
}
