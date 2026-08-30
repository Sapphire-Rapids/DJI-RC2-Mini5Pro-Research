package com.finduas.ridobserver

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Assert.assertEquals
import org.junit.Test

class ProbeReportExportPolicyTest {
    private val run = "00000000-0000-4000-8000-000000000001"

    @Test
    fun incompleteDiagnosticsAreExportedButRunningSnapshotsAreNot() {
        val pending = ProbeReportExportSnapshot(run, ProbeReportExportState.AWAITING_PROBE)
        assertTrue(ProbeReportExportPolicy.maySave(run, ProbeRunState.INCOMPLETE, pending))
        assertTrue(ProbeReportExportPolicy.maySave(run, ProbeRunState.COMPLETE, pending))
        assertFalse(ProbeReportExportPolicy.maySave(run, ProbeRunState.RUNNING, pending))
        assertFalse(ProbeReportExportPolicy.maySave(run, ProbeRunState.NOT_RUN, pending))
        assertFalse(ProbeReportExportPolicy.maySave("other-run", ProbeRunState.COMPLETE, pending))
    }

    @Test
    fun rotationAndResumeCannotScheduleAnotherAutomaticWrite() {
        for (exportState in listOf(
            ProbeReportExportState.SAVING, ProbeReportExportState.SAVED, ProbeReportExportState.FAILED
        )) {
            val export = ProbeReportExportSnapshot(run, exportState)
            repeat(3) {
                assertFalse(ProbeReportExportPolicy.maySave(run, ProbeRunState.COMPLETE, export))
            }
        }
    }

    @Test
    fun retryRequiresFailedExportOfTheSameCompletedRun() {
        val failed = ProbeReportExportSnapshot(run, ProbeReportExportState.FAILED)
        assertTrue(ProbeReportExportPolicy.mayRetry(run, ProbeRunState.INCOMPLETE, failed))
        assertTrue(ProbeReportExportPolicy.mayRetry(run, ProbeRunState.COMPLETE, failed))
        assertFalse(ProbeReportExportPolicy.mayRetry("new-run", ProbeRunState.COMPLETE, failed))
        assertFalse(ProbeReportExportPolicy.mayRetry(run, ProbeRunState.RUNNING, failed))
        assertFalse(ProbeReportExportPolicy.mayRetry(run, ProbeRunState.COMPLETE,
            failed.copy(state = ProbeReportExportState.SAVED)))
        assertFalse(ProbeReportExportPolicy.mayRetry(run, ProbeRunState.COMPLETE,
            failed.copy(state = ProbeReportExportState.SAVING)))
    }

    @Test
    fun pendingExportKeepsButtonsBlockedAcrossTheInspectionCompletionRace() {
        assertTrue(ProbeReportExportPolicy.isBusy(ProbeReportExportState.AWAITING_PROBE))
        assertTrue(ProbeReportExportPolicy.isBusy(ProbeReportExportState.SAVING))
        assertFalse(ProbeReportExportPolicy.isBusy(ProbeReportExportState.SAVED))
        assertFalse(ProbeReportExportPolicy.isBusy(ProbeReportExportState.FAILED))
    }

    @Test
    fun workerFinishingAfterRenderStillGetsOneFinalScreenRefresh() {
        var workerBusy = true
        var queued = 0
        val displayed = mutableListOf<Boolean>()
        val render = {
            val captured = workerBusy
            displayed.add(captured)
            // Deterministic interleaving: export completes after the display snapshot.
            workerBusy = false
            captured
        }
        ProbeReportExportPolicy.refreshFromDisplayedState(render) { queued++ }
        assertEquals(1, queued)
        ProbeReportExportPolicy.refreshFromDisplayedState(render) { queued++ }
        assertEquals(listOf(true, false), displayed)
        assertEquals(1, queued)
    }
}
