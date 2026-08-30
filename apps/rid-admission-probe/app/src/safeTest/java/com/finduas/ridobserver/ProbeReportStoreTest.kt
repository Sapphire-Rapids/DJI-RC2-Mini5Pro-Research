package com.finduas.ridobserver

import java.io.IOException
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ProbeReportStoreTest {
    private val runId = "00000000-0000-0000-0000-000000000001"
    private val report = "finduas-rid-probe/v0.10-schema-1\nrun_state=INCOMPLETE\n" +
        "状态=已完成本次检查\nmachine_section_end=true\nreport_file_end=true\n"

    @Test
    fun android30PublishesOnlyTheUniqueRemovableVolumeAfterWriteCompletion() {
        val store = FakeStore()
        val result = save(store)
        assertEquals(ProbeReportSaveStatus.SAVED, result.status)
        assertEquals(ProbeReportCleanupStatus.NOT_NEEDED, result.cleanupStatus)
        assertEquals("Download/FindUAS/Probe/", result.relativeDirectory)
        assertTrue(result.displayName!!.matches(Regex(
            "FindUAS_Probe_v012_1234_${runId}_[0-9a-f]{8}-[0-9a-f]{4}-" +
                "[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\\.txt"
        )))
        assertEquals("test-sd-a", store.selectedVolume)
        assertEquals(listOf("volumes", "externalNames", "insert", "write", "publish"), store.events)
        assertEquals(report, store.files.getValue(store.created.single()).text)
        assertFalse(store.files.getValue(store.created.single()).pending)
        assertEquals("older report", store.files.getValue(store.oldFile).text)
    }

    @Test
    fun android29UsesOnlyUuidMatchedToAnExistingMediaStoreVolume() {
        val store = FakeStore().apply {
            apiLevel = 29
            volumesData = listOf(sd().copy(mediaStoreName = "wrong-name", uuid = "TEST-SD-A"))
        }
        assertEquals(ProbeReportSaveStatus.SAVED, save(store).status)
        assertEquals("test-sd-a", store.selectedVolume)
    }

    @Test
    fun android30DoesNotFallBackToUuidWhenOfficialMappingIsUnavailable() {
        val store = FakeStore().apply { volumesData = listOf(sd().copy(mediaStoreName = null)) }
        assertEquals(ProbeReportSaveStatus.MEDIASTORE_VOLUME_UNAVAILABLE, save(store).status)
        assertEquals(0, store.created.size)
    }

    @Test
    fun android29RejectsUnmatchedOrAmbiguousUuidWithoutGuessingAUri() {
        for (names in listOf(setOf("external_primary"), setOf("test-sd-a", "TEST-SD-A"))) {
            val store = FakeStore().apply {
                apiLevel = 29
                externalNamesData = names
            }
            assertEquals(ProbeReportSaveStatus.MEDIASTORE_VOLUME_UNAVAILABLE, save(store).status)
            assertEquals(0, store.created.size)
        }
    }

    @Test
    fun absentUnmountedPrimaryOrEmulatedStorageNeverReceivesAReport() {
        for (volumes in listOf(
            emptyList(),
            listOf(sd().copy(removable = false, primary = true, emulated = true)),
            listOf(sd().copy(mounted = false)),
            listOf(sd().copy(primary = true)),
            listOf(sd().copy(emulated = true))
        )) {
            val store = FakeStore().apply { volumesData = volumes }
            assertEquals(ProbeReportSaveStatus.NO_MOUNTED_REMOVABLE_VOLUME, save(store).status)
            assertEquals(listOf("volumes"), store.events)
            assertEquals(0, store.created.size)
        }
    }

    @Test
    fun twoMountedRemovableVolumesFailClosedBeforeMediaStoreInsertion() {
        val store = FakeStore().apply { volumesData = listOf(sd(), sd("test-sd-b")) }
        assertEquals(ProbeReportSaveStatus.MULTIPLE_MOUNTED_REMOVABLE_VOLUMES, save(store).status)
        assertEquals(listOf("volumes"), store.events)
        assertEquals(0, store.created.size)
    }

    @Test
    fun primaryAndUnmountedVolumesDoNotDisplaceTheOneMountedSdCard() {
        val store = FakeStore().apply {
            volumesData = listOf(
                sd("external_primary").copy(removable = false, primary = true, emulated = true),
                sd("test-sd-b").copy(mounted = false),
                sd()
            )
        }
        assertEquals(ProbeReportSaveStatus.SAVED, save(store).status)
        assertEquals("test-sd-a", store.selectedVolume)
    }

    @Test
    fun reservedOrMalformedMappedNamesCannotSelectInternalOrArbitraryUris() {
        for (name in listOf("external", "external_primary", "../external_primary", "", "test/sd")) {
            val store = FakeStore().apply {
                volumesData = listOf(sd(name))
                externalNamesData = setOf(name)
            }
            assertEquals(ProbeReportSaveStatus.MEDIASTORE_VOLUME_UNAVAILABLE, save(store).status)
            assertEquals(0, store.created.size)
        }
    }

    @Test
    fun metadataCannotSupplyAPathOrUriAndNegativeTimeIsRejected() {
        for (id in listOf("../old.txt", "content://media/external/1", "$runId/other", "", "1-1-1-1-1")) {
            val store = FakeStore()
            assertEquals(
                ProbeReportSaveStatus.INVALID_RUN_METADATA,
                ProbeReportStore.saveCompletedReport(store, report, 1234, id).status
            )
            assertTrue(store.events.isEmpty())
        }
        val store = FakeStore()
        assertEquals(
            ProbeReportSaveStatus.INVALID_RUN_METADATA,
            ProbeReportStore.saveCompletedReport(store, report, -1, runId).status
        )
        assertTrue(store.events.isEmpty())
    }

    @Test
    fun truncatedReportIsNotSavedButTerminalIncompleteProbeReportIsSaved() {
        for (text in listOf("", "partial", "partial\nreport_file_end=true\nmore data")) {
            val store = FakeStore()
            assertEquals(
                ProbeReportSaveStatus.REPORT_INCOMPLETE,
                ProbeReportStore.saveCompletedReport(store, text, 1234, runId).status
            )
            assertTrue(store.events.isEmpty())
        }
        assertEquals(ProbeReportSaveStatus.SAVED, save(FakeStore()).status)
    }

    @Test
    fun oversizedAsciiOrUtf8ReportsCauseZeroInsertWithoutTruncation() {
        val ending = "\nreport_file_end=true\n"
        for (text in listOf(
            "a".repeat(ProbeReportStore.MAX_REPORT_BYTES) + ending,
            "测".repeat(ProbeReportStore.MAX_REPORT_BYTES / 3) + ending
        )) {
            val store = FakeStore()
            assertEquals(
                ProbeReportSaveStatus.REPORT_TOO_LARGE,
                ProbeReportStore.saveCompletedReport(store, text, 1234, runId).status
            )
            assertTrue(store.events.isEmpty())
            assertEquals(setOf(store.oldFile), store.files.keys)
        }
    }

    @Test
    fun exactlyTheUtf8ByteLimitRemainsWritable() {
        val ending = "\nreport_file_end=true\n"
        val text = "a".repeat(ProbeReportStore.MAX_REPORT_BYTES - ending.length) + ending
        val store = FakeStore()
        assertEquals(
            ProbeReportSaveStatus.SAVED,
            ProbeReportStore.saveCompletedReport(store, text, 1234, runId).status
        )
        assertEquals(text, store.files.getValue(store.created.single()).text)
    }

    @Test
    fun separateRunsInsertNewFilesAndNeverChangeEarlierReports() {
        val store = FakeStore()
        val first = save(store)
        val second = ProbeReportStore.saveCompletedReport(
            store, report, 1235, "00000000-0000-0000-0000-000000000002"
        )
        assertEquals(ProbeReportSaveStatus.SAVED, second.status)
        assertNotEquals(first.displayName, second.displayName)
        assertEquals(3, store.files.size)
        assertEquals("older report", store.files.getValue(store.oldFile).text)
        assertFalse(store.events.contains("remove"))
    }

    @Test
    fun repeatedExportOfOneRunAlwaysRequestsANewAttemptFilename() {
        val store = FakeStore()
        val first = save(store)
        val second = save(store)
        assertEquals(ProbeReportSaveStatus.SAVED, first.status)
        assertEquals(ProbeReportSaveStatus.SAVED, second.status)
        assertNotEquals(first.displayName, second.displayName)
        assertEquals(3, store.files.size)
        assertFalse(store.events.contains("remove"))
    }

    @Test
    fun retryAfterUncertainPublishAndFailedCleanupCannotReuseThePriorFilename() {
        val store = FakeStore().apply {
            failAt = "publish"
            removeReturnsFalse = true
        }
        val first = save(store)
        assertEquals(ProbeReportSaveStatus.PUBLISH_FAILED, first.status)
        assertEquals(ProbeReportCleanupStatus.FAILED, first.cleanupStatus)
        store.failAt = null
        store.removeReturnsFalse = false
        val second = save(store)
        assertEquals(ProbeReportSaveStatus.SAVED, second.status)
        assertNotEquals(store.requestedNames[0], store.requestedNames[1])
        assertEquals(store.requestedNames[1], second.displayName)
        assertEquals(3, store.files.size)
        assertEquals("older report", store.files.getValue(store.oldFile).text)
    }

    @Test
    fun discoveryFailuresDoNotBecomeNoSdOrAttemptAnInternalFallback() {
        for (stage in listOf("volumes", "externalNames")) {
            val store = FakeStore().apply { failAt = stage }
            assertEquals(ProbeReportSaveStatus.VOLUME_DISCOVERY_FAILED, save(store).status)
            assertEquals(0, store.created.size)
        }
    }

    @Test
    fun insertFailureWithNoOwnedHandleDoesNotDeleteAnything() {
        for (throws in listOf(false, true)) {
            val store = FakeStore().apply {
                insertReturnsNull = !throws
                failAt = if (throws) "insert" else null
            }
            val result = save(store)
            assertEquals(ProbeReportSaveStatus.INSERT_FAILED, result.status)
            assertEquals(ProbeReportCleanupStatus.NOT_NEEDED, result.cleanupStatus)
            assertFalse(store.events.contains("write"))
            assertFalse(store.events.contains("publish"))
            assertFalse(store.events.contains("remove"))
            assertEquals(setOf(store.oldFile), store.files.keys)
        }
    }

    @Test
    fun writeOrCloseFailureDeletesOnlyThisPendingRowAndNeverPublishesIt() {
        val store = FakeStore().apply { failAt = "write" }
        val result = save(store)
        assertEquals(ProbeReportSaveStatus.WRITE_FAILED, result.status)
        assertEquals(ProbeReportCleanupStatus.REMOVED, result.cleanupStatus)
        assertEquals(listOf("volumes", "externalNames", "insert", "write", "remove"), store.events)
        assertEquals(setOf(store.oldFile), store.files.keys)
        assertEquals(store.created.single(), store.removed.single())
        assertEquals(null, result.displayName)
    }

    @Test
    fun closeFailureAfterAllTextWasWrittenStillPreventsPublication() {
        val store = FakeStore().apply { closeFails = true }
        val result = save(store)
        assertEquals(ProbeReportSaveStatus.WRITE_FAILED, result.status)
        assertEquals(ProbeReportCleanupStatus.REMOVED, result.cleanupStatus)
        assertEquals(listOf("volumes", "externalNames", "insert", "write", "remove"), store.events)
        assertEquals(setOf(store.oldFile), store.files.keys)
        assertEquals(store.created.single(), store.removed.single())
    }

    @Test
    fun failedOrNoncanonicalPublicationCleansOnlyTheInsertedRow() {
        for (throws in listOf(false, true)) {
            val store = FakeStore().apply {
                publishReturnsFalse = !throws
                failAt = if (throws) "publish" else null
            }
            val result = save(store)
            assertEquals(ProbeReportSaveStatus.PUBLISH_FAILED, result.status)
            assertEquals(ProbeReportCleanupStatus.REMOVED, result.cleanupStatus)
            assertEquals(setOf(store.oldFile), store.files.keys)
            assertEquals(store.created.single(), store.removed.single())
            assertEquals(listOf("volumes", "externalNames", "insert", "write", "publish", "remove"), store.events)
        }
    }

    @Test
    fun cleanupFailureIsVisibleAndNeverTriggersAnotherVolumeOrDeletion() {
        for (throws in listOf(false, true)) {
            val store = FakeStore().apply {
                failAt = "write"
                removeThrows = throws
                removeReturnsFalse = !throws
            }
            val result = save(store)
            assertEquals(ProbeReportSaveStatus.WRITE_FAILED, result.status)
            assertEquals(ProbeReportCleanupStatus.FAILED, result.cleanupStatus)
            assertEquals(1, store.created.size)
            assertEquals(1, store.events.count { it == "remove" })
            assertEquals("older report", store.files.getValue(store.oldFile).text)
            assertTrue(store.files.getValue(store.created.single()).pending)
        }
    }

    private fun save(store: FakeStore) =
        ProbeReportStore.saveCompletedReport(store, report, 1234, runId)

    private fun sd(name: String = "test-sd-a") = ProbeReportStore.Volume(
        removable = true, mounted = true, primary = false, emulated = false,
        mediaStoreName = name, uuid = name
    )

    private data class Token(val index: Int) : ProbeReportStore.PendingReport
    private data class FileState(var text: String, var pending: Boolean)

    private inner class FakeStore : ProbeReportStore.Store {
        override var apiLevel = 30
        var volumesData = listOf(sd())
        var externalNamesData = setOf("external_primary", "test-sd-a")
        var selectedVolume: String? = null
        var failAt: String? = null
        var insertReturnsNull = false
        var publishReturnsFalse = false
        var closeFails = false
        var removeReturnsFalse = false
        var removeThrows = false
        val events = mutableListOf<String>()
        val oldFile = Token(0)
        val files = linkedMapOf(oldFile to FileState("older report", false))
        val created = mutableListOf<Token>()
        val removed = mutableListOf<Token>()
        val requestedNames = mutableListOf<String>()

        private fun step(name: String) {
            events += name
            if (failAt == name) throw IOException("Synthetic $name failure")
        }

        override fun volumes(): List<ProbeReportStore.Volume> {
            step("volumes")
            return volumesData
        }

        override fun externalVolumeNames(): Set<String> {
            step("externalNames")
            return externalNamesData
        }

        override fun insertPending(volumeName: String, displayName: String): ProbeReportStore.PendingReport? {
            step("insert")
            selectedVolume = volumeName
            if (insertReturnsNull) return null
            requestedNames += displayName
            assertTrue(displayName.startsWith(ProbeReportStore.FILE_PREFIX))
            assertFalse(displayName.contains('/'))
            return Token(created.size + 1).also {
                created += it
                files[it] = FileState("", true)
            }
        }

        override fun writeUtf8(report: ProbeReportStore.PendingReport, text: String) {
            val token = report as Token
            assertTrue(token in created)
            assertTrue(files.getValue(token).pending)
            files.getValue(token).text = text
            step("write")
            if (closeFails) throw IOException("Synthetic close failure after complete write")
        }

        override fun publish(report: ProbeReportStore.PendingReport): Boolean {
            step("publish")
            if (publishReturnsFalse) return false
            val token = report as Token
            assertTrue(token in created)
            assertTrue(files.getValue(token).pending)
            files.getValue(token).pending = false
            return true
        }

        override fun remove(report: ProbeReportStore.PendingReport): Boolean {
            step("remove")
            if (removeThrows) throw IOException("Synthetic cleanup failure")
            if (removeReturnsFalse) return false
            val token = report as Token
            assertTrue(token in created)
            removed += token
            return files.remove(token) != null
        }
    }
}
