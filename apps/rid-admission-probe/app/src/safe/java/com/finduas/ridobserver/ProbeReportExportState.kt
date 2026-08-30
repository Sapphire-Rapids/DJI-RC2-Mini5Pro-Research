package com.finduas.ridobserver

internal enum class ProbeReportExportState { NOT_REQUESTED, AWAITING_PROBE, SAVING, SAVED, FAILED }

internal data class ProbeReportExportSnapshot(
    val runId: String? = null,
    val state: ProbeReportExportState = ProbeReportExportState.NOT_REQUESTED,
    val result: ProbeReportSaveResult? = null,
    val preparationFailed: Boolean = false
)

/** Export status never changes the device-inspection completion verdict. */
internal object ProbeReportExportPolicy {
    fun refreshFromDisplayedState(render: () -> Boolean, requeue: () -> Unit) {
        if (render()) requeue()
    }

    fun isBusy(state: ProbeReportExportState): Boolean =
        state == ProbeReportExportState.AWAITING_PROBE || state == ProbeReportExportState.SAVING

    fun isTerminal(state: ProbeRunState): Boolean =
        state == ProbeRunState.COMPLETE || state == ProbeRunState.INCOMPLETE

    fun maySave(runId: String?, state: ProbeRunState, export: ProbeReportExportSnapshot): Boolean =
        runId != null && runId == export.runId && isTerminal(state) &&
            export.state == ProbeReportExportState.AWAITING_PROBE

    fun mayRetry(runId: String?, state: ProbeRunState, export: ProbeReportExportSnapshot): Boolean =
        runId != null && runId == export.runId && isTerminal(state) &&
            export.state == ProbeReportExportState.FAILED
}
