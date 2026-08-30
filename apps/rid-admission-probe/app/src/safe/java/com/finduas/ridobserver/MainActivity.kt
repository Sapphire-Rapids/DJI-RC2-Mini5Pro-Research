package com.finduas.ridobserver

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import java.time.Instant
import java.util.UUID

internal enum class ProbeRunState { NOT_RUN, RUNNING, INCOMPLETE, COMPLETE }

internal enum class SettingsNavigationState {
    NOT_REQUESTED,
    PRIMARY_OPENED,
    FALLBACK_OPENED,
    ACTIVITY_NOT_FOUND,
    DENIED,
    FAILED
}

private enum class SettingsLaunchResult { OPENED, NOT_FOUND, DENIED, FAILED }

internal object ProbeCompletionPolicy {
    fun terminalState(
        protocolBinderCompleted: Boolean,
        localBridgeCompleted: Boolean,
        artIdentityState: ArtIdentityState
    ): ProbeRunState = if (
        protocolBinderCompleted &&
        localBridgeCompleted &&
        artIdentityState == ArtIdentityState.COMPLETE
    ) {
        ProbeRunState.COMPLETE
    } else {
        ProbeRunState.INCOMPLETE
    }
}

internal data class ProbeSessionSnapshot(
    val result: ProtocolBinderProbeResult = ProtocolBinderProbeResult(),
    val localBridge: LocalBridgeProbeResult = LocalBridgeProbeResult(),
    val artIdentity: AndroidArtIdentityResult = AndroidArtIdentityResult(),
    val protocolBinderCompleted: Boolean = false,
    val localBridgeCompleted: Boolean = false,
    val runState: ProbeRunState = ProbeRunState.NOT_RUN,
    val runId: String? = null,
    val runStartedAtMs: Long? = null,
    val runCompletedAtMs: Long? = null,
    val settingsNavigationState: SettingsNavigationState =
        SettingsNavigationState.NOT_REQUESTED,
    val settingsRequestedAction: String? = null,
    val settingsLaunchedAction: String? = null
)

internal object ProbeRunAdmissionPolicy {
    fun mayStart(runState: ProbeRunState): Boolean = runState != ProbeRunState.RUNNING
}

/**
 * Process-lifetime owner for one read-only probe run. Activity recreation cannot create a second
 * worker, and the replacement Activity renders the same running or completed immutable snapshot.
 */
internal object ProbeSessionCoordinator {
    private val lock = Any()
    private var state = ProbeSessionSnapshot()
    private var reportExport = ProbeReportExportSnapshot()

    fun snapshot(): ProbeSessionSnapshot = synchronized(lock) { state }
    fun displaySnapshot(): Pair<ProbeSessionSnapshot, ProbeReportExportSnapshot> =
        synchronized(lock) { state to reportExport }
    fun isBusy(): Boolean = synchronized(lock) {
        state.runState == ProbeRunState.RUNNING || ProbeReportExportPolicy.isBusy(reportExport.state)
    }

    fun start(applicationContext: Context): Boolean {
        val runId = UUID.randomUUID().toString()
        synchronized(lock) {
            if (!ProbeRunAdmissionPolicy.mayStart(state.runState)) return false
            if (ProbeReportExportPolicy.isBusy(reportExport.state)) return false
            reportExport = ProbeReportExportSnapshot(runId, ProbeReportExportState.AWAITING_PROBE)
            state = state.copy(
                result = ProtocolBinderProbeResult(),
                localBridge = LocalBridgeProbeResult(),
                artIdentity = AndroidArtIdentityResult(),
                protocolBinderCompleted = false,
                localBridgeCompleted = false,
                runState = ProbeRunState.RUNNING,
                runId = runId,
                runStartedAtMs = System.currentTimeMillis(),
                runCompletedAtMs = null
            )
        }

        Thread({
            var nextProtocolCompleted = false
            val nextProtocol = try {
                ProtocolBinderProbe.runOnce().also { nextProtocolCompleted = true }
            } catch (_: Throwable) {
                ProtocolBinderProbeResult(ProtocolBinderProbeState.INTERNAL_ERROR)
            }
            var nextLocalBridgeCompleted = false
            val nextLocalBridge = try {
                LocalBridgeProbe.run(applicationContext).also {
                    nextLocalBridgeCompleted = true
                }
            } catch (_: Throwable) {
                LocalBridgeProbeResult()
            }
            val nextArtIdentity = try {
                AndroidArtIdentityProbe.run()
            } catch (_: Throwable) {
                AndroidArtIdentityResult(state = ArtIdentityState.FILE_READ_ERROR)
            }
            synchronized(lock) {
                if (state.runId != runId || state.runState != ProbeRunState.RUNNING) {
                    return@Thread
                }
                state = state.copy(
                    result = nextProtocol,
                    localBridge = nextLocalBridge,
                    artIdentity = nextArtIdentity,
                    protocolBinderCompleted = nextProtocolCompleted,
                    localBridgeCompleted = nextLocalBridgeCompleted,
                    runCompletedAtMs = System.currentTimeMillis(),
                    runState = ProbeCompletionPolicy.terminalState(
                        nextProtocolCompleted,
                        nextLocalBridgeCompleted,
                        nextArtIdentity.state
                    )
                )
            }
            exportCompletedReport(applicationContext, runId)
        }, "protocol-binder-readonly-probe").start()
        return true
    }

    private fun exportCompletedReport(applicationContext: Context, runId: String) {
        val completed = synchronized(lock) {
            if (state.runId != runId ||
                !ProbeReportExportPolicy.maySave(runId, state.runState, reportExport)) return
            reportExport = reportExport.copy(state = ProbeReportExportState.SAVING)
            state
        }
        val saved = try {
            ProbeReportStore.saveCompletedReport(
                applicationContext,
                ProbeReportFormatter.buildReport(completed),
                requireNotNull(completed.runCompletedAtMs),
                runId
            )
        } catch (_: Throwable) {
            null
        }
        synchronized(lock) {
            if (state.runId == runId && reportExport.runId == runId) {
                reportExport = ProbeReportExportSnapshot(
                    runId,
                    if (saved?.status == ProbeReportSaveStatus.SAVED) {
                        ProbeReportExportState.SAVED
                    } else {
                        ProbeReportExportState.FAILED
                    },
                    saved,
                    preparationFailed = saved == null
                )
            }
        }
    }

    fun retryReportExport(applicationContext: Context): Boolean {
        val runId = synchronized(lock) {
            if (!ProbeReportExportPolicy.mayRetry(state.runId, state.runState, reportExport)) {
                return false
            }
            reportExport = reportExport.copy(state = ProbeReportExportState.AWAITING_PROBE)
            requireNotNull(state.runId)
        }
        Thread({ exportCompletedReport(applicationContext, runId) }, "probe-report-export").start()
        return true
    }

    fun recordSettingsNavigation(
        stateValue: SettingsNavigationState,
        requestedAction: String?,
        launchedAction: String?
    ) {
        synchronized(lock) {
            state = state.copy(
                settingsNavigationState = stateValue,
                settingsRequestedAction = requestedAction,
                settingsLaunchedAction = launchedAction
            )
        }
    }
}

class MainActivity : Activity() {
    private companion object {
        const val REFRESH_INTERVAL_MS = 200L
    }

    private val handler = Handler(Looper.getMainLooper())
    private lateinit var stateText: TextView
    private lateinit var probeButton: Button
    private lateinit var copyButton: Button
    private lateinit var exportStatusText: TextView
    private lateinit var retryExportButton: Button
    private lateinit var developmentSettingsButton: Button
    private lateinit var deviceInfoSettingsButton: Button
    private var currentReport = ""
    private var resumed = false
    private val refreshRunnable = object : Runnable {
        override fun run() {
            if (!resumed) return
            ProbeReportExportPolicy.refreshFromDisplayedState(::render) {
                handler.postDelayed(this, REFRESH_INTERVAL_MS)
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(buildUi())
        render()
    }

    override fun onResume() {
        super.onResume()
        resumed = true
        handler.removeCallbacks(refreshRunnable)
        refreshRunnable.run()
    }

    override fun onPause() {
        resumed = false
        handler.removeCallbacks(refreshRunnable)
        super.onPause()
    }

    private fun buildUi(): ScrollView {
        val density = resources.displayMetrics.density
        val padding = (20 * density).toInt()
        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(padding, padding, padding, padding)
        }
        content.addView(TextView(this).apply {
            text = getString(R.string.app_name)
            textSize = 24f
            setTextColor(Color.BLACK)
        })
        content.addView(TextView(this).apply {
            text = getString(R.string.probe_intro)
            textSize = 14f
            setPadding(0, padding / 2, 0, padding)
        })
        content.addView(TextView(this).apply {
            text = getString(R.string.socket_warning)
            textSize = 16f
            setTextColor(Color.rgb(180, 40, 20))
            setPadding(0, 0, 0, padding)
        })
        content.addView(TextView(this).apply {
            text = getString(R.string.scope_warning)
            textSize = 14f
            setPadding(0, 0, 0, padding)
        })
        exportStatusText = TextView(this).apply {
            textSize = 16f
            setPadding(0, 0, 0, padding / 2)
        }
        content.addView(exportStatusText)
        retryExportButton = Button(this).apply {
            text = getString(R.string.retry_report_export)
            setOnClickListener {
                ProbeSessionCoordinator.retryReportExport(applicationContext)
                render()
                if (resumed) {
                    handler.removeCallbacks(refreshRunnable)
                    handler.postDelayed(refreshRunnable, REFRESH_INTERVAL_MS)
                }
            }
        }
        content.addView(retryExportButton)
        deviceInfoSettingsButton = Button(this).apply {
            text = getString(R.string.open_device_info_settings)
            setOnClickListener { openSystemSettings(Settings.ACTION_DEVICE_INFO_SETTINGS) }
        }
        content.addView(deviceInfoSettingsButton)
        developmentSettingsButton = Button(this).apply {
            text = getString(R.string.open_development_settings)
            setOnClickListener {
                openSystemSettings(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS)
            }
        }
        content.addView(developmentSettingsButton)
        stateText = TextView(this).apply {
            typeface = android.graphics.Typeface.MONOSPACE
            textSize = 15f
            setTextIsSelectable(true)
        }
        content.addView(
            stateText,
            LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        )
        probeButton = Button(this).apply {
            text = getString(R.string.check_protocol_binder)
            setOnClickListener { checkProtocolBinder() }
        }
        content.addView(probeButton)
        copyButton = Button(this).apply {
            text = getString(R.string.copy_complete_report)
            setOnClickListener { copyCompleteReport() }
        }
        content.addView(copyButton)
        return ScrollView(this).apply { addView(content) }
    }

    private fun checkProtocolBinder() {
        ProbeSessionCoordinator.start(applicationContext)
        render()
        if (resumed) {
            handler.removeCallbacks(refreshRunnable)
            handler.postDelayed(refreshRunnable, REFRESH_INTERVAL_MS)
        }
    }

    private fun render(): Boolean {
        val (snapshot, export) = ProbeSessionCoordinator.displaySnapshot()
        currentReport = ProbeReportFormatter.buildReport(snapshot)
        stateText.text = currentReport
        exportStatusText.text = when (export.state) {
            ProbeReportExportState.NOT_REQUESTED -> "检查结束后自动保存报告到 SD 卡；请保持本应用打开至保存完成。"
            ProbeReportExportState.AWAITING_PROBE -> "等待检查完成后保存报告到 SD 卡。"
            ProbeReportExportState.SAVING -> "正在保存报告到 SD 卡，请保持本应用打开。"
            ProbeReportExportState.SAVED -> "报告已保存到 SD 卡：\n" +
                export.result?.relativeDirectory + export.result?.displayName +
                "\n电脑可通过 MTP 读取；本地保存成功不代表电脑已读回。"
            ProbeReportExportState.FAILED -> "报告未保存：" +
                (export.result?.status?.name ?: "REPORT_PREPARATION_FAILED") +
                "\n清理状态：" + (export.result?.cleanupStatus?.name ?: "NOT_REQUIRED") +
                "\n请检查 SD 卡后点击重试，无需重新执行检查。"
        }
        val probeInFlight = snapshot.runState == ProbeRunState.RUNNING ||
            ProbeReportExportPolicy.isBusy(export.state)
        probeButton.isEnabled = !probeInFlight
        retryExportButton.isEnabled =
            ProbeReportExportPolicy.mayRetry(snapshot.runId, snapshot.runState, export)
        copyButton.isEnabled = !probeInFlight &&
            (snapshot.runState == ProbeRunState.COMPLETE ||
                snapshot.runState == ProbeRunState.INCOMPLETE)
        developmentSettingsButton.isEnabled = !probeInFlight
        deviceInfoSettingsButton.isEnabled = !probeInFlight
        // Schedule from what was displayed, not a second read of worker state. A worker
        // finishing immediately after this snapshot still needs one final UI render.
        return probeInFlight
    }

    private fun copyCompleteReport() {
        val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboard.setPrimaryClip(ClipData.newPlainText("FindUAS RID probe", currentReport))
        Toast.makeText(this, getString(R.string.report_copied), Toast.LENGTH_SHORT).show()
    }

    private fun openSystemSettings(primaryAction: String) {
        if (ProbeSessionCoordinator.isBusy()) return
        var navigationState: SettingsNavigationState
        var launchedAction: String? = null
        when (launchSettingsAction(primaryAction)) {
            SettingsLaunchResult.OPENED -> {
                navigationState = SettingsNavigationState.PRIMARY_OPENED
                launchedAction = primaryAction
            }
            SettingsLaunchResult.NOT_FOUND -> when (
                launchSettingsAction(Settings.ACTION_SETTINGS)
            ) {
                SettingsLaunchResult.OPENED -> {
                    navigationState = SettingsNavigationState.FALLBACK_OPENED
                    launchedAction = Settings.ACTION_SETTINGS
                }
                SettingsLaunchResult.NOT_FOUND -> {
                    navigationState = SettingsNavigationState.ACTIVITY_NOT_FOUND
                }
                SettingsLaunchResult.DENIED -> {
                    navigationState = SettingsNavigationState.DENIED
                }
                SettingsLaunchResult.FAILED -> {
                    navigationState = SettingsNavigationState.FAILED
                }
            }
            SettingsLaunchResult.DENIED -> {
                navigationState = SettingsNavigationState.DENIED
            }
            SettingsLaunchResult.FAILED -> {
                navigationState = SettingsNavigationState.FAILED
            }
        }
        ProbeSessionCoordinator.recordSettingsNavigation(
            navigationState,
            primaryAction,
            launchedAction
        )
        render()
    }

    private fun launchSettingsAction(action: String): SettingsLaunchResult = try {
        startActivity(Intent(action))
        SettingsLaunchResult.OPENED
    } catch (_: ActivityNotFoundException) {
        SettingsLaunchResult.NOT_FOUND
    } catch (_: SecurityException) {
        SettingsLaunchResult.DENIED
    } catch (_: Throwable) {
        SettingsLaunchResult.FAILED
    }

}

/** Pure report formatting shared by the screen and the background SD export. */
internal object ProbeReportFormatter {
    const val APP_VERSION = "0.11.0-report-export"
    fun buildReport(snapshot: ProbeSessionSnapshot): String = with(snapshot) {
        buildString {
        appendMachineReport(snapshot)
        appendLine("machine_section_end=true")
        appendLine()
        appendLine("schema: finduas-rid-probe/v0.10-schema-1")
        appendLine("app version: $APP_VERSION")
        appendLine("run state: $runState")
        appendLine("run id: ${runId ?: "无"}")
        appendLine("started: ${formatTime(runStartedAtMs)}")
        appendLine("completed: ${formatTime(runCompletedAtMs)}")
        appendLine()
        appendLine("网络权限: 无")
        appendLine("DJI localhost socket: 已从发布构建移除")
        appendLine("DUML 发送: 无")
        appendLine("DJI protocol Binder 应用事务: 无")
        appendLine("AttachAgent / JVMTI attach: 无")
        appendLine("新增 ART 段中的 DJI/ART 私有类反射、类枚举或加载: 无")
        appendLine("v0.8 的 Android framework-only 只读反射检查保持不变。")
        appendLine("系统设置按钮: 只由用户点击后导航 Android 原生设置 UI。")
        appendLine(
            "设置导航: $settingsNavigationState; requested=" +
                "${settingsRequestedAction ?: "无"}; launched=${settingsLaunchedAction ?: "无"}"
        )
        appendLine()
        appendLine("Protocol Binder: ${protocolBinderText(result.state)}")
        appendLine("检查范围: service lookup / ping / descriptor")
        appendLine()
        appendLine("Android SDK: ${localBridge.sdk}")
            appendLine("Build incremental: ${localBridge.buildIncremental}")
            appendLine("设备 ABI: ${localBridge.deviceAbis}")
            appendLine("Observer UID: ${localBridge.observerUid ?: "未知"}")
            appendLine("Observer 64-bit: ${booleanText(localBridge.observerIs64Bit)}")
            appendLine("ro.debuggable: ${valueText(localBridge.roDebuggable)}")
            appendLine("SELinux enforcing: ${valueText(localBridge.selinuxEnforcing)}")
            appendLine(
                "Observer SELinux context: ${valueText(localBridge.observerSelinuxContext)}"
            )
            appendLine()
            appendPackageDetails("DJI Fly", localBridge.djiFly)
            appendRunningProcessDetails(localBridge.djiFlyProcess)
            appendPackageDetails("DJI 开发助手", localBridge.dpadFuli)
            appendLine("相邻 dpad_fuli 整包判定: ${localBridge.adjacentDpadReference}")
            appendLine("该判定只继承 Shell 静态代码结论，不证明 framework/Pack ABI。")
            appendLine(
                "DJI Fly 与 Observer 同 UID: " +
                    booleanText(localBridge.djiFlySharesUidWithObserver)
            )
            appendLine(
                "DJI Fly 与开发助手同 UID: " +
                    booleanText(localBridge.djiFlySharesUidWithDpadFuli)
            )
            appendLine("开发助手入口: ${localBridge.dpadFuliDevActivity}")
            appendLine("协议页入口: ${localBridge.dpadFuliProtocolActivity}")
            appendLine("Shell 页入口: ${localBridge.dpadFuliShellActivity}")
            appendLine()
            appendPackageDetails("JVMTI V0 carrier", localBridge.jvmtiCanaryCarrier)
            appendPackageDetails("JVMTI V1 carrier", localBridge.jvmtiEidResolverCarrier)
            appendFileDetails("framework.jar", localBridge.frameworkJar)
            appendLine(
                "  与相邻 framework.jar 一致: " +
                    booleanText(localBridge.frameworkJarMatchesAdjacent)
            )
            appendFileDetails("services.jar", localBridge.servicesJar)
            appendLine(
                "  与相邻 services.jar 一致: " +
                    booleanText(localBridge.servicesJarMatchesAdjacent)
            )
            appendLine("相邻 framework/server ABI 判定: ${localBridge.adjacentFrameworkReference}")
            appendLine("dpad/Fly APK 或 DEX 命中不能替代这个独立 ABI 判定。")
            appendFileDetails("dji.json", localBridge.djiJson)
            appendLine(
                "  与相邻 dji.json 一致: " +
                    booleanText(localBridge.djiJsonMatchesAdjacent)
            )
            appendFileDetails("libduml_frwk.so", localBridge.dumlFrameworkLibrary)
            appendLine(
                "  与相邻 libduml_frwk.so 一致: " +
                    booleanText(localBridge.dumlFrameworkLibraryMatchesAdjacent)
            )
            appendLine("相邻单活动 broker 实现判定: ${localBridge.adjacentBrokerReference}")
            appendLine("无论是否命中，v0.1-v0.4 仍禁止运行。")
            appendLine("升级恢复标记: ${localBridge.upgradeRecoveryMarker}")
            appendLine()
        appendLine("Android / ART 自进程身份: ${artIdentity.state}")
        appendLine("  section complete: ${artIdentity.sectionComplete}")
        appendLine("  build fingerprint: ${artIdentity.buildFingerprint}")
        appendLine("  SDK: ${artIdentity.sdk}")
        appendLine("  ABI: ${artIdentity.supportedAbis}")
        appendLine("  process 64-bit: ${artIdentity.processIs64Bit}")
        appendLine("  page size bytes: ${artIdentity.pageSizeBytes ?: "未知"}")
        appendLine(
            "  /proc/self/maps libart entries=${artIdentity.mapsEntryCount}, " +
                "malformed=${artIdentity.malformedLibartEntryCount}, " +
                "file identities=${artIdentity.fileIdentityCount}"
        )
        appendLine(
            "  second maps entries=${artIdentity.secondMapsEntryCount ?: "未知"}, " +
                "malformed=${artIdentity.secondMalformedLibartEntryCount ?: "未知"}, " +
                "strictly stable=${booleanText(artIdentity.mapsSnapshotStable)}"
        )
        artIdentity.mapEntries.forEachIndexed { index, entry ->
            appendLine(
                "  map[$index]: ${entry.addressRange} ${entry.permissions} " +
                    "offset=0x${entry.fileOffset.toString(16)} ${entry.device} " +
                    "inode=${entry.inode} path=${entry.path}" +
                    if (entry.deleted) " (deleted)" else ""
            )
        }
        appendLine("  mapped device: ${artIdentity.mappedDevice ?: "未知"}")
        appendLine("  mapped inode: ${artIdentity.mappedInode ?: "未知"}")
        appendLine("  mapped path: ${artIdentity.mappedPath ?: "未知"}")
        appendLine("  deleted mapping: ${booleanText(artIdentity.mappedFileDeleted)}")
        appendLine("  mapped device non-zero: ${booleanText(artIdentity.mappedDeviceNonZero)}")
        appendLine("  final path symlink: ${booleanText(artIdentity.finalPathSymlink)}")
        appendLine("  fstat device non-zero: ${booleanText(artIdentity.fileDeviceNonZero)}")
        appendLine("  exact file regular: ${booleanText(artIdentity.fileIsRegular)}")
        appendLine(
            "  metadata stable during read: " +
                booleanText(artIdentity.fileMetadataStable)
        )
        appendLine("  file bytes: ${artIdentity.fileSize ?: "未知"}")
        appendLine("  whole-file SHA-256: ${artIdentity.wholeFileSha256 ?: "未知"}")
        appendLine("  GNU build-id: ${artIdentity.gnuBuildId ?: "未知"}")
        appendLine("  known RC2 ART profile: ${artIdentity.knownRc2Profile}")
        appendArtRange("Agent::Unload range", artIdentity.agentUnloadRange)
        appendArtRange("Runtime::AttachAgent range", artIdentity.runtimeAttachAgentRange)
        appendLine("  两次严格一致的本进程 libart maps 快照，且只读其精确非符号链接 regular 文件。")
        appendLine("  没有 attach、符号调用、另一个进程读取或 native library load。")
        appendLine()
        appendLine("路径权限均为 Observer 自身 UID/SELinux 视角。")
        appendLine("它们不证明 UID1000 可写，也不证明 DJI Fly linker 可加载或执行。")
        appendLine("本版本只读取上述设备状态，不启动开发助手或协议页；仅将本报告保存到 SD 卡。")
        appendLine("report_file_end=true")
        }
    }

    private fun StringBuilder.appendMachineReport(snapshot: ProbeSessionSnapshot) =
        with(snapshot) {
            fun field(key: String, value: Any?) {
                append(key)
                append('=')
                appendLine(MachineReportValue.encode(value?.toString()))
            }
            field("schema", "finduas-rid-probe/v0.10-schema-1")
            field("app_version", APP_VERSION)
            field("run_state", runState.name)
            field("run_id", runId)
            field("started_epoch_ms", runStartedAtMs)
            field("completed_epoch_ms", runCompletedAtMs)
            field("base.protocol_binder_completed", protocolBinderCompleted)
            field("base.protocol_binder_state", result.state.name)
            field("base.local_bridge_completed", localBridgeCompleted)
            field("settings_navigation.state", settingsNavigationState.name)
            field("settings_navigation.requested_action", settingsRequestedAction)
            field("settings_navigation.launched_action", settingsLaunchedAction)
            field("art.section_complete", artIdentity.sectionComplete)
            field("android.build_fingerprint", artIdentity.buildFingerprint)
            field("android.sdk", artIdentity.sdk)
            field("android.supported_abis", artIdentity.supportedAbis)
            field("android.process_is_64_bit", artIdentity.processIs64Bit)
            field("art.state", artIdentity.state.name)
            field("art.page_size_bytes", artIdentity.pageSizeBytes)
            field("art.maps_entry_count", artIdentity.mapsEntryCount)
            field("art.malformed_entry_count", artIdentity.malformedLibartEntryCount)
            field("art.file_identity_count", artIdentity.fileIdentityCount)
            field("art.second_maps_entry_count", artIdentity.secondMapsEntryCount)
            field(
                "art.second_malformed_entry_count",
                artIdentity.secondMalformedLibartEntryCount
            )
            field("art.maps_snapshot_stable", artIdentity.mapsSnapshotStable)
            artIdentity.mapEntries.forEachIndexed { index, entry ->
                field("art.map.$index.address_range", entry.addressRange)
                field("art.map.$index.start_address", "0x${entry.startAddress.toString(16)}")
                field("art.map.$index.end_address", "0x${entry.endAddress.toString(16)}")
                field("art.map.$index.permissions", entry.permissions)
                field("art.map.$index.file_offset", "0x${entry.fileOffset.toString(16)}")
                field("art.map.$index.device", entry.device)
                field("art.map.$index.inode", entry.inode)
                field("art.map.$index.path", entry.path)
                field("art.map.$index.deleted", entry.deleted)
            }
            field("art.mapped_device", artIdentity.mappedDevice)
            field("art.mapped_inode", artIdentity.mappedInode)
            field("art.mapped_path", artIdentity.mappedPath)
            field("art.mapped_file_deleted", artIdentity.mappedFileDeleted)
            field("art.mapped_device_nonzero", artIdentity.mappedDeviceNonZero)
            field("art.final_path_symlink", artIdentity.finalPathSymlink)
            field("art.file_device_nonzero", artIdentity.fileDeviceNonZero)
            field("art.file_is_regular", artIdentity.fileIsRegular)
            field("art.file_metadata_stable", artIdentity.fileMetadataStable)
            field("art.file_size", artIdentity.fileSize)
            field("art.whole_file_sha256", artIdentity.wholeFileSha256)
            field("art.gnu_build_id", artIdentity.gnuBuildId)
            field("art.known_rc2_profile", artIdentity.knownRc2Profile.name)
            field(
                "art.agent_unload_range.offset",
                "0x${artIdentity.agentUnloadRange.offset.toString(16)}"
            )
            field(
                "art.agent_unload_range.size",
                "0x${artIdentity.agentUnloadRange.size.toString(16)}"
            )
            field("art.agent_unload_range.state", artIdentity.agentUnloadRange.state.name)
            field("art.agent_unload_range.sha256", artIdentity.agentUnloadRange.sha256)
            field(
                "art.runtime_attach_agent_range.offset",
                "0x${artIdentity.runtimeAttachAgentRange.offset.toString(16)}"
            )
            field(
                "art.runtime_attach_agent_range.size",
                "0x${artIdentity.runtimeAttachAgentRange.size.toString(16)}"
            )
            field(
                "art.runtime_attach_agent_range.state",
                artIdentity.runtimeAttachAgentRange.state.name
            )
            field(
                "art.runtime_attach_agent_range.sha256",
                artIdentity.runtimeAttachAgentRange.sha256
            )
        }

    private fun StringBuilder.appendArtRange(label: String, range: ArtRangeCheck) {
        appendLine(
            "  $label: offset=0x${range.offset.toString(16)}, " +
                "size=0x${range.size.toString(16)}, state=${range.state}, " +
                "SHA-256=${range.sha256 ?: "未知"}"
        )
    }

    private fun protocolBinderText(state: ProtocolBinderProbeState): String = when (state) {
        ProtocolBinderProbeState.NOT_RUN -> "未检查"
        ProtocolBinderProbeState.SERVICE_AVAILABLE -> "可见且 descriptor 匹配"
        ProtocolBinderProbeState.SERVICE_ABSENT -> "服务不存在/未发布"
        ProtocolBinderProbeState.HIDDEN_API_BLOCKED -> "Android hidden API 阻止"
        ProtocolBinderProbeState.LOOKUP_DENIED -> "ServiceManager/SELinux 拒绝查找"
        ProtocolBinderProbeState.BINDER_UNREACHABLE -> "句柄不可达"
        ProtocolBinderProbeState.DESCRIPTOR_DENIED -> "Binder/SELinux 拒绝 descriptor"
        ProtocolBinderProbeState.DESCRIPTOR_MISMATCH -> "descriptor 不匹配"
        ProtocolBinderProbeState.INTERNAL_ERROR -> "内部错误（未执行发送事务）"
    }

    private fun booleanText(value: Boolean?): String = when (value) {
        true -> "是"
        false -> "否"
        null -> "未知"
    }

    private fun StringBuilder.appendPackageDetails(
        label: String,
        capability: PackageCapability
    ) {
        appendLine(
            "$label: ${capability.state}" +
                capability.version?.let { " ($it)" }.orEmpty()
        )
        appendLine(
            "  versionCode=${capability.versionCode ?: "未知"}, " +
                "lastUpdateTimeMs=${capability.lastUpdateTimeMs ?: "未知"}, " +
                "splitCount=${capability.splitCount ?: "未知"}, " +
                "splitNames=${capability.splitNames ?: "未知"}"
        )
        appendLine(
            "  扫描前后包元数据稳定: " +
                booleanText(capability.metadataStableDuringProbe)
        )
        appendLine(
            "  UID=${capability.uid ?: "未知"}, " +
                "UID1000=${booleanText(capability.isSystemUid)}, " +
                "system=${booleanText(capability.isSystemApp)}, " +
                "updated-system=${booleanText(capability.isUpdatedSystemApp)}, " +
                "debuggable=${booleanText(capability.isDebuggable)}"
        )
        appendLine(
            "  process=${capability.processName ?: "未知"}, " +
                "extractNativeLibs=${booleanText(capability.extractsNativeLibraries)}"
        )
        appendLine("  APK ABI: ${capability.packagedAbis ?: "未知"}")
        appendLine("  签名 SHA-256: ${capability.signerSha256 ?: "未知"}")
        appendLine(
            "  匹配相邻 DJI platform 证书: " +
                booleanText(capability.signerMatchesAdjacentDjiPlatform)
        )
        appendFileDetails("source APK", capability.sourceApk)
        capability.sourceApkMatchesReference?.let {
            appendLine("    与固定相邻参考 APK 完全一致: ${booleanText(it)}")
        }
        capability.archiveEntries.forEach { appendArchiveEntryDetails(it) }
        appendFileDetails("data dir", capability.dataDirectory)
        appendFileDetails("native lib dir", capability.nativeLibraryDirectory)
        if (capability.expectedNativeLibrary.path != null) {
            appendFileDetails("expected .so", capability.expectedNativeLibrary)
        }
    }

    private fun StringBuilder.appendFileDetails(label: String, capability: FileCapability) {
        appendLine("  $label: ${capability.state} ${capability.path ?: ""}".trimEnd())
        if (capability.state != FileProbeState.PRESENT) return
        appendLine(
            "    kind=${capability.kind ?: "未知"}, " +
                "owner=${capability.ownerUid ?: "?"}:${capability.ownerGid ?: "?"}, " +
                "mode=${capability.mode ?: "未知"}"
        )
        appendLine(
            "    observer r/w/x=" +
                "${booleanText(capability.observerCanRead)}/" +
                "${booleanText(capability.observerCanWrite)}/" +
                booleanText(capability.observerCanExecute)
        )
        appendLine("    SELinux=${valueText(capability.selinuxContext)}")
        capability.sha256?.let { appendLine("    SHA-256=${valueText(it)}") }
    }

    private fun StringBuilder.appendRunningProcessDetails(
        capability: RunningProcessCapability
    ) {
        appendLine("  runtime process visibility: ${capability.state}")
        if (capability.state != RunningProcessProbeState.FOUND) return
        appendLine(
            "    process=${capability.processName ?: "未知"}, " +
                "pid=${capability.pid ?: "未知"}, uid=${capability.uid ?: "未知"}, " +
                "importance=${capability.importance ?: "未知"}"
        )
    }

    private fun StringBuilder.appendArchiveEntryDetails(
        capability: ArchiveEntryCapability
    ) {
        appendLine("  固定归档项 ${capability.label}: ${capability.state}")
        if (capability.state != ArchiveEntryProbeState.PRESENT) {
            capability.entryName?.let { appendLine("    entry=$it") }
            return
        }
        appendLine(
            "    archive=${capability.archivePath ?: "未知"}, " +
                "entry=${capability.entryName ?: "未知"}, " +
                "bytes=${capability.uncompressedBytes ?: "未知"}"
        )
        appendLine("    SHA-256=${capability.sha256 ?: "未知"}")
        appendLine("    与固定只读参考一致: ${booleanText(capability.matchesReference)}")
    }

    private fun valueText(value: ReadOnlyValue): String = when (value.state) {
        ReadOnlyValueState.VALUE -> value.value ?: "空"
        else -> value.state.name
    }

    private fun formatTime(value: Long?): String = value?.let {
        Instant.ofEpochMilli(it).toString()
    } ?: "无"
}
