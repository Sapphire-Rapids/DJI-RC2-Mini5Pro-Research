package com.finduas.ridobserver

import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.io.InputStream
import java.io.OutputStream
import java.util.zip.ZipInputStream
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class InstalledFlySampleExporterTest {
    private class FakeSource : InstalledFlySampleExporter.Source {
        var version = InstalledFlySampleExporter.Identity("1.19.4", 3113157L)
        var finalIdentity: InstalledFlySampleExporter.Identity? = null
        private var identityCalls = 0
        val files = InstalledFlySampleExporter.Entry.values().associateWith {
            if (it == InstalledFlySampleExporter.Entry.APK) "abc".toByteArray()
            else "fixture-${it.name}".toByteArray()
        }.toMutableMap()
        val sizes = mutableMapOf<InstalledFlySampleExporter.Entry, Long>()
        val calls = mutableMapOf<InstalledFlySampleExporter.Entry, Int>()
        var changedEntry: InstalledFlySampleExporter.Entry? = null
        var changeOnCall = 3
        var readFailure: InstalledFlySampleExporter.Entry? = null
        var opened = 0

        override fun identity(): InstalledFlySampleExporter.Identity {
            identityCalls++
            return if (identityCalls == 1) version else finalIdentity ?: version
        }
        override fun metadata(entry: InstalledFlySampleExporter.Entry): InstalledFlySampleExporter.Metadata? {
            val bytes = files[entry] ?: return null
            val count = (calls[entry] ?: 0) + 1
            calls[entry] = count
            return InstalledFlySampleExporter.Metadata(
                sizes[entry] ?: bytes.size.toLong(),
                if (entry == changedEntry && count >= changeOnCall) 2L else 1L
            )
        }

        override fun open(entry: InstalledFlySampleExporter.Entry): InputStream {
            opened++
            if (entry == readFailure) return object : InputStream() {
                override fun read(): Int = throw IOException("fixture read failure")
            }
            return ByteArrayInputStream(requireNotNull(files[entry]))
        }
    }

    private class FakeStore : InstalledFlySampleExporter.Store {
        override val apiLevel = 30
        var candidateVolumes = listOf(
            InstalledFlySampleExporter.Volume(true, true, false, false, "test-card", "TEST-CARD")
        )
        private val pending = object : InstalledFlySampleExporter.PendingZip { }
        val bytes = ByteArrayOutputStream()
        var insertedName: String? = null
        var inserts = 0
        var publications = 0
        var removals = 0
        var outputClosed = false
        var failInsert = false
        var failOpen = false
        var failWrite = false
        var failClose = false
        var failPublish = false
        var failRemove = false

        override fun volumes() = candidateVolumes
        override fun externalVolumeNames() = setOf("test-card")
        override fun insertPending(volumeName: String, displayName: String): InstalledFlySampleExporter.PendingZip? {
            assertEquals("test-card", volumeName)
            inserts++
            insertedName = displayName
            return if (failInsert) null else pending
        }

        override fun openOutput(pending: InstalledFlySampleExporter.PendingZip): OutputStream? {
            assertTrue(pending === this.pending)
            if (failOpen) return null
            return object : OutputStream() {
                override fun write(value: Int) {
                    if (failWrite) throw IOException("fixture output failure")
                    bytes.write(value)
                }
                override fun write(data: ByteArray, offset: Int, count: Int) {
                    if (failWrite) throw IOException("fixture output failure")
                    bytes.write(data, offset, count)
                }
                override fun close() {
                    outputClosed = true
                    if (failClose) throw IOException("fixture close failure")
                }
            }
        }

        override fun publish(pending: InstalledFlySampleExporter.PendingZip): Boolean {
            assertTrue(pending === this.pending)
            assertTrue("publication occurred before ZIP stream closed", outputClosed)
            publications++
            return !failPublish
        }

        override fun remove(pending: InstalledFlySampleExporter.PendingZip): Boolean {
            assertTrue(pending === this.pending)
            removals++
            return !failRemove
        }
    }

    private fun archive(store: FakeStore): Map<String, ByteArray> {
        val result = linkedMapOf<String, ByteArray>()
        ZipInputStream(ByteArrayInputStream(store.bytes.toByteArray())).use { zip ->
            while (true) {
                val entry = zip.nextEntry ?: break
                assertFalse("duplicate ZIP entry", result.containsKey(entry.name))
                result[entry.name] = zip.readBytes()
                zip.closeEntry()
            }
        }
        return result
    }

    @Test
    fun fixedArchiveContainsExactSourcesAndHashManifestWithoutSourcePaths() {
        val source = FakeSource()
        val store = FakeStore()
        val result = InstalledFlySampleExporter.export(source, store)
        assertEquals(InstalledFlySampleExportStatus.SUCCESS, result.status)
        assertEquals(1, store.publications)
        assertEquals(0, store.removals)
        assertTrue(requireNotNull(result.displayName).matches(
            Regex("FindUAS_Fly1194_[0-9a-f-]{36}\\.zip")
        ))
        val entries = archive(store)
        assertEquals(setOf("DJI_FLY.apk", "libsdk_jni.so", "libsdk_key_value.so",
            "libsdk_base.so", "manifest.json"), entries.keys)
        for ((entry, bytes) in source.files) assertArrayEquals(bytes, entries[entry.archiveName])
        val manifest = requireNotNull(entries["manifest.json"]).toString(Charsets.UTF_8)
        assertTrue(manifest.contains("\"versionName\":\"1.19.4\",\"versionCode\":3113157"))
        assertTrue(manifest.contains("\"entry\":\"DJI_FLY.apk\",\"size\":3," +
            "\"sha256\":\"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad\""))
        assertTrue(manifest.contains("\"missingOptional\":[]"))
        assertFalse(manifest.contains("/data/"))
        assertFalse(manifest.contains("sourceDir"))
        assertFalse(manifest.contains("nativeLibraryDir"))
    }

    @Test
    fun wrongVersionNeverReadsSourcesOrCreatesOutput() {
        for (identity in listOf(InstalledFlySampleExporter.Identity("1.21.10", 3113157L),
            InstalledFlySampleExporter.Identity("1.19.4", 1L))) {
            val source = FakeSource().apply { version = identity }
            val store = FakeStore()
            assertEquals(InstalledFlySampleExportStatus.WRONG_VERSION,
                InstalledFlySampleExporter.export(source, store).status)
            assertTrue(source.calls.isEmpty())
            assertEquals(0, store.inserts)
        }
    }

    @Test
    fun eitherRequiredSourceMissingStopsBeforeOutput() {
        for (entry in listOf(InstalledFlySampleExporter.Entry.APK, InstalledFlySampleExporter.Entry.JNI)) {
            val source = FakeSource().apply { files.remove(entry) }
            val store = FakeStore()
            val result = InstalledFlySampleExporter.export(source, store)
            assertEquals(InstalledFlySampleExportStatus.SOURCE_MISSING, result.status)
            assertEquals(entry.archiveName, result.failedEntry)
            assertEquals(0, source.opened)
            assertEquals(0, store.inserts)
        }
    }

    @Test
    fun optionalAbsenceIsRecordedAndDoesNotBlockRequiredSamples() {
        val source = FakeSource().apply {
            files.remove(InstalledFlySampleExporter.Entry.KEY_VALUE)
            files.remove(InstalledFlySampleExporter.Entry.BASE)
        }
        val store = FakeStore()
        val result = InstalledFlySampleExporter.export(source, store)
        assertEquals(InstalledFlySampleExportStatus.SUCCESS, result.status)
        assertEquals(listOf("libsdk_key_value.so", "libsdk_base.so"), result.missingOptional)
        val entries = archive(store)
        assertEquals(setOf("DJI_FLY.apk", "libsdk_jni.so", "manifest.json"), entries.keys)
        assertTrue(requireNotNull(entries["manifest.json"]).toString(Charsets.UTF_8)
            .contains("\"missingOptional\":[\"libsdk_key_value.so\",\"libsdk_base.so\"]"))
    }

    @Test
    fun shortOrLongSourceNeverPublishes() {
        for (declaredSize in listOf(2L, 4L)) {
            val source = FakeSource().apply { sizes[InstalledFlySampleExporter.Entry.APK] = declaredSize }
            val store = FakeStore()
            val result = InstalledFlySampleExporter.export(source, store)
            assertEquals(InstalledFlySampleExportStatus.SOURCE_CHANGED, result.status)
            assertEquals(0, store.publications)
            assertEquals(1, store.removals)
            assertNull(result.displayName)
        }
    }

    @Test
    fun changedMetadataBeforeOrAfterCopyNeverPublishes() {
        for (call in listOf(2, 3)) {
            val source = FakeSource().apply {
                changedEntry = InstalledFlySampleExporter.Entry.APK
                changeOnCall = call
            }
            val store = FakeStore()
            val result = InstalledFlySampleExporter.export(source, store)
            assertEquals(InstalledFlySampleExportStatus.SOURCE_CHANGED, result.status)
            assertEquals(0, store.publications)
            assertEquals(1, store.removals)
            if (call == 2) assertEquals(0, source.opened)
        }
    }

    @Test
    fun sourceReadFailureRemovesOnlyPendingOutput() {
        val source = FakeSource().apply { readFailure = InstalledFlySampleExporter.Entry.JNI }
        val store = FakeStore()
        val result = InstalledFlySampleExporter.export(source, store)
        assertEquals(InstalledFlySampleExportStatus.SOURCE_READ_FAILED, result.status)
        assertEquals("libsdk_jni.so", result.failedEntry)
        assertEquals(0, store.publications)
        assertEquals(1, store.removals)
    }

    @Test
    fun packageUpdateOrSourcePathChangeDuringCopyNeverPublishes() {
        for (changed in listOf(
            InstalledFlySampleExporter.Identity("1.21.10", 3115981L),
            InstalledFlySampleExporter.Identity("1.19.4", 3113157L, "TEST-CHANGED-APK", null),
            InstalledFlySampleExporter.Identity("1.19.4", 3113157L, null, "TEST-CHANGED-LIBDIR")
        )) {
            val source = FakeSource().apply { finalIdentity = changed }
            val store = FakeStore()
            val result = InstalledFlySampleExporter.export(source, store)
            assertEquals(InstalledFlySampleExportStatus.SOURCE_CHANGED, result.status)
            assertEquals(0, store.publications)
            assertEquals(1, store.removals)
        }
    }

    @Test
    fun outputOpenWriteCloseOrPublishFailureCannotReportSuccess() {
        for (stage in listOf("insert", "open", "write", "close", "publish")) {
            val store = FakeStore().apply {
                failInsert = stage == "insert"
                failOpen = stage == "open"
                failWrite = stage == "write"
                failClose = stage == "close"
                failPublish = stage == "publish"
            }
            val result = InstalledFlySampleExporter.export(FakeSource(), store)
            assertEquals(stage, InstalledFlySampleExportStatus.OUTPUT_FAILED, result.status)
            assertNull(result.displayName)
            assertEquals(if (stage == "insert") 0 else 1, store.removals)
            assertEquals(if (stage == "publish") 1 else 0, store.publications)
        }
    }

    @Test
    fun cleanupFailureIsReportedWithoutRetryingOrPublishing() {
        val store = FakeStore().apply { failWrite = true; failRemove = true }
        val result = InstalledFlySampleExporter.export(FakeSource(), store)
        assertEquals(InstalledFlySampleExportStatus.OUTPUT_FAILED, result.status)
        assertEquals(InstalledFlySampleCleanupStatus.FAILED, result.cleanupStatus)
        assertEquals(1, store.removals)
        assertEquals(0, store.publications)
    }

    @Test
    fun fileAndTotalLimitsRejectBeforeAllocatingOutput() {
        val oversized = FakeSource().apply {
            sizes[InstalledFlySampleExporter.Entry.APK] = InstalledFlySampleExporter.MAX_FILE_BYTES + 1
        }
        val totalOversized = FakeSource().apply {
            sizes[InstalledFlySampleExporter.Entry.APK] = InstalledFlySampleExporter.MAX_FILE_BYTES
            sizes[InstalledFlySampleExporter.Entry.JNI] = InstalledFlySampleExporter.MAX_FILE_BYTES
        }
        for (source in listOf(oversized, totalOversized)) {
            val store = FakeStore()
            assertEquals(InstalledFlySampleExportStatus.SIZE_LIMIT_EXCEEDED,
                InstalledFlySampleExporter.export(source, store).status)
            assertEquals(0, store.inserts)
            assertEquals(0, source.opened)
        }
    }

    @Test
    fun noCardOrTwoCardsNeverFallsBackToPrimary() {
        for (count in listOf(0, 2)) {
            val store = FakeStore().apply { candidateVolumes = List(count) { candidateVolumes.single() } }
            val result = InstalledFlySampleExporter.export(FakeSource(), store)
            assertEquals(if (count == 0) InstalledFlySampleExportStatus.NO_SD_CARD
                else InstalledFlySampleExportStatus.AMBIGUOUS_SD_CARD, result.status)
            assertEquals(0, store.inserts)
        }
    }

    @Test
    fun progressCountsOnlyCopiedSourceBytesInBoundedChunks() {
        val source = FakeSource().apply {
            files[InstalledFlySampleExporter.Entry.APK] = ByteArray(2 * InstalledFlySampleExporter.BUFFER_BYTES + 7)
        }
        val progress = mutableListOf<Long>()
        val result = InstalledFlySampleExporter.export(source, FakeStore()) { progress += it }
        assertEquals(InstalledFlySampleExportStatus.SUCCESS, result.status)
        assertEquals(source.files.values.sumOf { it.size.toLong() }, result.totalBytes)
        assertEquals(result.totalBytes, progress.last())
        val increments = (listOf(0L) + progress).zipWithNext { a, b -> b - a }
        assertTrue(increments.all { it in 1..InstalledFlySampleExporter.BUFFER_BYTES.toLong() })
    }
}
