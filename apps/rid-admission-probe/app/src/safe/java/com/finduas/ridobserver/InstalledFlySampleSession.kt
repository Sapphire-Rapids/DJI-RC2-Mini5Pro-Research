package com.finduas.ridobserver

import android.content.Context

internal data class InstalledFlySampleSnapshot(
    val running: Boolean = false,
    val bytesCopied: Long = 0,
    val result: InstalledFlySampleExportResult? = null,
    val failed: Boolean = false
)

internal object InstalledFlySampleSession {
    private val lock = Any()
    private var state = InstalledFlySampleSnapshot()

    fun snapshot(): InstalledFlySampleSnapshot = synchronized(lock) { state }

    fun start(context: Context): Boolean {
        val applicationContext = context.applicationContext
        synchronized(lock) {
            if (state.running) return false
            state = InstalledFlySampleSnapshot(running = true)
        }
        Thread({
            val result = try {
                InstalledFlySampleExporter.export(applicationContext) { copied ->
                    synchronized(lock) { state = state.copy(bytesCopied = copied) }
                }
            } catch (_: Throwable) {
                null
            }
            synchronized(lock) {
                state = state.copy(
                    running = false,
                    result = result,
                    failed = result?.status != InstalledFlySampleExportStatus.SUCCESS
                )
            }
        }, "installed-fly-sample-export").start()
        return true
    }
}
