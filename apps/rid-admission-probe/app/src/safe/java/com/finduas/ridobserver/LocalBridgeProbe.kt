package com.finduas.ridobserver

import android.annotation.SuppressLint
import android.app.ActivityManager
import android.content.ComponentName
import android.content.Context
import android.content.pm.ActivityInfo
import android.content.pm.ApplicationInfo
import android.content.pm.PackageInfo
import android.content.pm.PackageManager
import android.os.Build
import android.system.ErrnoException
import android.system.Os
import android.system.OsConstants
import java.io.File
import java.lang.reflect.InvocationTargetException
import java.security.MessageDigest
import java.util.zip.ZipFile

internal enum class PackageProbeState { PRESENT, ABSENT, VISIBILITY_DENIED, INTERNAL_ERROR }

internal enum class ActivityProbeState {
    EXPORTED_ENABLED,
    EXPORTED_DISABLED,
    PRIVATE_ENABLED,
    PRIVATE_DISABLED,
    ABSENT,
    VISIBILITY_DENIED,
    INTERNAL_ERROR
}

internal enum class UpgradeRecoveryMarkerState {
    CLEAR,
    SET,
    OTHER,
    HIDDEN_API_BLOCKED,
    READ_DENIED,
    INTERNAL_ERROR
}

internal enum class ReadOnlyValueState {
    VALUE,
    HIDDEN_API_BLOCKED,
    READ_DENIED,
    INTERNAL_ERROR
}

internal data class ReadOnlyValue(
    val state: ReadOnlyValueState = ReadOnlyValueState.INTERNAL_ERROR,
    val value: String? = null
)

internal enum class FileProbeState {
    PRESENT,
    ABSENT,
    READ_DENIED,
    INTERNAL_ERROR
}

internal data class FileCapability(
    val state: FileProbeState = FileProbeState.INTERNAL_ERROR,
    val path: String? = null,
    val kind: String? = null,
    val ownerUid: Int? = null,
    val ownerGid: Int? = null,
    val mode: String? = null,
    val observerCanRead: Boolean? = null,
    val observerCanWrite: Boolean? = null,
    val observerCanExecute: Boolean? = null,
    val selinuxContext: ReadOnlyValue = ReadOnlyValue(),
    val sha256: ReadOnlyValue? = null
)

internal data class PackageCapability(
    val state: PackageProbeState = PackageProbeState.INTERNAL_ERROR,
    val version: String? = null,
    val versionCode: Long? = null,
    val lastUpdateTimeMs: Long? = null,
    val splitCount: Int? = null,
    val splitNames: String? = null,
    val metadataStableDuringProbe: Boolean? = null,
    val uid: Int? = null,
    val isSystemUid: Boolean? = null,
    val isSystemApp: Boolean? = null,
    val isUpdatedSystemApp: Boolean? = null,
    val isDebuggable: Boolean? = null,
    val extractsNativeLibraries: Boolean? = null,
    val processName: String? = null,
    val signerSha256: String? = null,
    val signerMatchesAdjacentDjiPlatform: Boolean? = null,
    val packagedAbis: String? = null,
    val sourceApk: FileCapability = FileCapability(),
    val sourceApkMatchesReference: Boolean? = null,
    val archiveEntries: List<ArchiveEntryCapability> = emptyList(),
    val dataDirectory: FileCapability = FileCapability(),
    val nativeLibraryDirectory: FileCapability = FileCapability(),
    val expectedNativeLibrary: FileCapability = FileCapability()
)

internal enum class AdjacentDpadReferenceState {
    EXACT_PACKAGE_MATCH,
    DIFFERENT,
    CHANGED_DURING_SCAN,
    INCOMPLETE
}

internal enum class AdjacentFrameworkReferenceState {
    EXACT_BOTH_MATCH,
    DIFFERENT,
    INCOMPLETE
}

internal enum class AdjacentBrokerReferenceState {
    EXACT_BOTH_MATCH,
    DIFFERENT,
    INCOMPLETE
}

internal enum class RunningProcessProbeState {
    FOUND,
    NOT_VISIBLE,
    READ_DENIED,
    INTERNAL_ERROR
}

internal data class RunningProcessCapability(
    val state: RunningProcessProbeState = RunningProcessProbeState.INTERNAL_ERROR,
    val processName: String? = null,
    val pid: Int? = null,
    val uid: Int? = null,
    val importance: Int? = null
)

internal data class LocalBridgeProbeResult(
    val sdk: Int = Build.VERSION.SDK_INT,
    val buildIncremental: String = Build.VERSION.INCREMENTAL,
    val deviceAbis: String = Build.SUPPORTED_ABIS.joinToString(","),
    val observerUid: Int? = null,
    val observerIs64Bit: Boolean? = null,
    val observerSelinuxContext: ReadOnlyValue = ReadOnlyValue(),
    val roDebuggable: ReadOnlyValue = ReadOnlyValue(),
    val selinuxEnforcing: ReadOnlyValue = ReadOnlyValue(),
    val djiFly: PackageCapability = PackageCapability(),
    val djiFlyProcess: RunningProcessCapability = RunningProcessCapability(),
    val dpadFuli: PackageCapability = PackageCapability(),
    val djiFlySharesUidWithObserver: Boolean? = null,
    val djiFlySharesUidWithDpadFuli: Boolean? = null,
    val adjacentDpadReference: AdjacentDpadReferenceState =
        AdjacentDpadReferenceState.INCOMPLETE,
    val dpadFuliDevActivity: ActivityProbeState = ActivityProbeState.INTERNAL_ERROR,
    val dpadFuliProtocolActivity: ActivityProbeState = ActivityProbeState.INTERNAL_ERROR,
    val dpadFuliShellActivity: ActivityProbeState = ActivityProbeState.INTERNAL_ERROR,
    val jvmtiCanaryCarrier: PackageCapability = PackageCapability(),
    val jvmtiEidResolverCarrier: PackageCapability = PackageCapability(),
    val frameworkJar: FileCapability = FileCapability(),
    val frameworkJarMatchesAdjacent: Boolean? = null,
    val servicesJar: FileCapability = FileCapability(),
    val servicesJarMatchesAdjacent: Boolean? = null,
    val adjacentFrameworkReference: AdjacentFrameworkReferenceState =
        AdjacentFrameworkReferenceState.INCOMPLETE,
    val djiJson: FileCapability = FileCapability(),
    val djiJsonMatchesAdjacent: Boolean? = null,
    val dumlFrameworkLibrary: FileCapability = FileCapability(),
    val dumlFrameworkLibraryMatchesAdjacent: Boolean? = null,
    val adjacentBrokerReference: AdjacentBrokerReferenceState =
        AdjacentBrokerReferenceState.INCOMPLETE,
    val upgradeRecoveryMarker: UpgradeRecoveryMarkerState =
        UpgradeRecoveryMarkerState.INTERNAL_ERROR
)

internal object UpgradeRecoveryMarkerPolicy {
    fun classify(value: String): UpgradeRecoveryMarkerState = when (value) {
        "0", "" -> UpgradeRecoveryMarkerState.CLEAR
        "1" -> UpgradeRecoveryMarkerState.SET
        else -> UpgradeRecoveryMarkerState.OTHER
    }
}

internal object PackageCapabilityPolicy {
    private const val PER_USER_RANGE = 100_000

    fun isSystemUid(uid: Int): Boolean = uid.mod(PER_USER_RANGE) == 1000

    fun hasFlag(flags: Int, flag: Int): Boolean = flags and flag != 0

    fun normalizeDigest(bytes: ByteArray): String = bytes.joinToString("") {
        "%02x".format(it.toInt() and 0xff)
    }

    fun formatMode(mode: Int): String = (mode and 0x0fff).toString(8).padStart(4, '0')
}

internal object ReferenceClassificationPolicy {
    fun classifyDpad(capability: PackageCapability): AdjacentDpadReferenceState {
        if (capability.metadataStableDuringProbe == false) {
            return AdjacentDpadReferenceState.CHANGED_DURING_SCAN
        }
        if (
            capability.state != PackageProbeState.PRESENT ||
            capability.metadataStableDuringProbe == null ||
            capability.versionCode == null ||
            capability.version == null ||
            capability.splitCount == null ||
            capability.signerMatchesAdjacentDjiPlatform == null ||
            capability.sourceApkMatchesReference == null
        ) {
            return AdjacentDpadReferenceState.INCOMPLETE
        }
        return if (
            capability.metadataStableDuringProbe == true &&
            capability.versionCode == 155L &&
            capability.version == "1.0.08.29-5e7f0af3" &&
            capability.splitCount == 0 &&
            capability.signerMatchesAdjacentDjiPlatform == true &&
            capability.sourceApkMatchesReference == true
        ) {
            AdjacentDpadReferenceState.EXACT_PACKAGE_MATCH
        } else {
            AdjacentDpadReferenceState.DIFFERENT
        }
    }

    fun classifyFramework(
        frameworkMatches: Boolean?,
        servicesMatches: Boolean?
    ): AdjacentFrameworkReferenceState = when {
        frameworkMatches == null || servicesMatches == null ->
            AdjacentFrameworkReferenceState.INCOMPLETE
        frameworkMatches && servicesMatches ->
            AdjacentFrameworkReferenceState.EXACT_BOTH_MATCH
        else -> AdjacentFrameworkReferenceState.DIFFERENT
    }

    fun classifyBroker(
        configMatches: Boolean?,
        libraryMatches: Boolean?
    ): AdjacentBrokerReferenceState = when {
        configMatches == null || libraryMatches == null ->
            AdjacentBrokerReferenceState.INCOMPLETE
        configMatches && libraryMatches -> AdjacentBrokerReferenceState.EXACT_BOTH_MATCH
        else -> AdjacentBrokerReferenceState.DIFFERENT
    }
}

/** Package/component/property inventory only. It never launches another activity. */
internal object LocalBridgeProbe {
    private const val DJI_FLY_PACKAGE = "dji.go.v5"
    private const val DPAD_FULI_PACKAGE = "com.dpad.fuli"
    private const val JVMTI_CANARY_PACKAGE = "com.finduas.jvmti.canary.carrier"
    private const val JVMTI_EID_RESOLVER_PACKAGE = "com.finduas.jvmti.eidresolver.v1"
    private const val DPAD_DEV_ACTIVITY = "com.dpad.fuli.DevActivity"
    private const val DPAD_PROTOCOL_ACTIVITY = "com.dpad.fuli.ProtocalActivity"
    private const val DPAD_SHELL_ACTIVITY = "com.dpad.fuli.ShellCommandActivity"
    private const val DJI_FLY_NATIVE_LIBRARY = "libsdk_jni.so"
    private const val JVMTI_CANARY_NATIVE_LIBRARY = "libfinduas_jvmti_canary.so"
    private const val JVMTI_EID_RESOLVER_NATIVE_LIBRARY = "libfinduas_eid_resolver_v1.so"
    private const val UPGRADE_RECOVERY_PROPERTY = "persist.dji.upgrade.fuli"
    private const val DEBUGGABLE_PROPERTY = "ro.debuggable"
    private const val FRAMEWORK_JAR_PATH = "/system/framework/framework.jar"
    private const val SERVICES_JAR_PATH = "/system/framework/services.jar"
    private const val DJI_JSON_PATH = "/vendor/etc/dji.json"
    private const val DUML_FRAMEWORK_LIBRARY_PATH = "/system/lib64/libduml_frwk.so"

    // Exact adjacent 10.00.0700/0205 artifacts. Equality admits only static-code parity; it does
    // not admit execution. A mismatch means the adjacent behavioral audit cannot be projected.
    private const val ADJACENT_DPAD_APK_SHA256 =
        "58b176eb1e17cacb7522914d282a69a677603ea9026993fc143c6a390211e44f"
    private const val ADJACENT_DPAD_SHELL_DEX_SHA256 =
        "71f55dbd7c2a4f6242d54b0a3f1c73eca366d7b3ca54a42fdd8c4635a15a5f56"
    private const val ADJACENT_DPAD_RUNNER_DEX_SHA256 =
        "e3ad59c1c80d8b3b495a06507ff62df64a1fd6d16dc913f57b8b63ffe85b7992"

    // Local official DJI Fly 1.21.10 reference. A mismatch is expected for a different RC build and
    // is reported as identity evidence only, never as lack of RID support.
    private const val LOCAL_DJI_FLY_SDK_JNI_SHA256 =
        "5abd990c86bcd00c9a652a21e329ad4580a20ec9f80188075ada61f5a7b46286"
    private const val ADJACENT_FRAMEWORK_JAR_SHA256 =
        "4422ab980097dd40f0daa1b6d304ba2c0239ecad1ead0b9796952213b706043c"
    private const val ADJACENT_SERVICES_JAR_SHA256 =
        "1372cd839fc8f495d4e166bd4f29e08a446ca7fcd4154bfa642174ca4e7352ed"
    private const val ADJACENT_DJI_JSON_SHA256 =
        "dfc986823188115ef4f75599144342be427c08aca52d004d2cf141de77a08155"
    private const val ADJACENT_DUML_FRAMEWORK_LIBRARY_SHA256 =
        "a5257965135fa46118451480bdd04f109e0ec29858827e764ffeaabaf6c270a2"

    // DJI platform certificate from the adjacent official RC331 10.00.0700/0205 image.
    // A mismatch means the live build differs; it is not by itself an unsafe-package verdict.
    private const val ADJACENT_DJI_PLATFORM_CERT_SHA256 =
        "a4aa1cdd2ea580cbbe67486b5f6f3cfea83f488889995afa70793daa516687da"

    fun run(context: Context): LocalBridgeProbeResult {
        val manager = context.packageManager
        val djiEvidence = packageEvidence(manager, DJI_FLY_PACKAGE)
        val fuliEvidence = packageEvidence(manager, DPAD_FULI_PACKAGE)
        val canaryEvidence = packageEvidence(manager, JVMTI_CANARY_PACKAGE)
        val resolverEvidence = packageEvidence(manager, JVMTI_EID_RESOLVER_PACKAGE)
        val djiUid = djiEvidence.info?.applicationInfo?.uid
        val fuliUid = fuliEvidence.info?.applicationInfo?.uid
        val djiCapability = capability(
            manager,
            djiEvidence,
            expectedNativeLibraryName = DJI_FLY_NATIVE_LIBRARY,
            archiveEntryRequests = listOf(
                ArchiveEntryRequest(
                    label = "DJI Fly packaged libsdk_jni.so vs local 1.21.10",
                    entryName = "lib/arm64-v8a/libsdk_jni.so",
                    expectedSha256 = LOCAL_DJI_FLY_SDK_JNI_SHA256
                )
            )
        )
        val dpadCapability = capability(
            manager,
            fuliEvidence,
            computeSourceApkSha256 = true,
            sourceApkReferenceSha256 = ADJACENT_DPAD_APK_SHA256,
            archiveEntryRequests = listOf(
                ArchiveEntryRequest(
                    label = "adjacent ShellCommandActivity DEX",
                    entryName = "classes16.dex",
                    expectedSha256 = ADJACENT_DPAD_SHELL_DEX_SHA256
                ),
                ArchiveEntryRequest(
                    label = "adjacent RunShellCommand DEX",
                    entryName = "classes23.dex",
                    expectedSha256 = ADJACENT_DPAD_RUNNER_DEX_SHA256
                )
            )
        )
        val frameworkJar = probePath(FRAMEWORK_JAR_PATH, computeSha256 = true)
        val servicesJar = probePath(SERVICES_JAR_PATH, computeSha256 = true)
        val frameworkMatch = matchesDigest(frameworkJar, ADJACENT_FRAMEWORK_JAR_SHA256)
        val servicesMatch = matchesDigest(servicesJar, ADJACENT_SERVICES_JAR_SHA256)
        val djiJson = probePath(DJI_JSON_PATH, computeSha256 = true)
        val dumlFrameworkLibrary = probePath(
            DUML_FRAMEWORK_LIBRARY_PATH,
            computeSha256 = true
        )
        val djiJsonMatch = matchesDigest(djiJson, ADJACENT_DJI_JSON_SHA256)
        val dumlFrameworkLibraryMatch = matchesDigest(
            dumlFrameworkLibrary,
            ADJACENT_DUML_FRAMEWORK_LIBRARY_SHA256
        )
        return LocalBridgeProbeResult(
            observerUid = context.applicationInfo.uid,
            observerIs64Bit = android.os.Process.is64Bit(),
            roDebuggable = readFixedSystemProperty(DEBUGGABLE_PROPERTY, ""),
            selinuxEnforcing = readSelinuxBoolean("isSELinuxEnforced"),
            observerSelinuxContext = readSelinuxString("getContext"),
            djiFly = djiCapability,
            djiFlyProcess = runningProcess(context, djiEvidence.info?.applicationInfo),
            dpadFuli = dpadCapability,
            djiFlySharesUidWithObserver = djiUid?.let { it == context.applicationInfo.uid },
            djiFlySharesUidWithDpadFuli = if (djiUid != null && fuliUid != null) {
                djiUid == fuliUid
            } else {
                null
            },
            adjacentDpadReference = ReferenceClassificationPolicy.classifyDpad(dpadCapability),
            dpadFuliDevActivity = activityState(
                manager,
                ComponentName(DPAD_FULI_PACKAGE, DPAD_DEV_ACTIVITY)
            ),
            dpadFuliProtocolActivity = activityState(
                manager,
                ComponentName(DPAD_FULI_PACKAGE, DPAD_PROTOCOL_ACTIVITY)
            ),
            dpadFuliShellActivity = activityState(
                manager,
                ComponentName(DPAD_FULI_PACKAGE, DPAD_SHELL_ACTIVITY)
            ),
            jvmtiCanaryCarrier = capability(
                manager,
                canaryEvidence,
                JVMTI_CANARY_NATIVE_LIBRARY
            ),
            jvmtiEidResolverCarrier = capability(
                manager,
                resolverEvidence,
                JVMTI_EID_RESOLVER_NATIVE_LIBRARY
            ),
            frameworkJar = frameworkJar,
            frameworkJarMatchesAdjacent = frameworkMatch,
            servicesJar = servicesJar,
            servicesJarMatchesAdjacent = servicesMatch,
            adjacentFrameworkReference = ReferenceClassificationPolicy.classifyFramework(
                frameworkMatch,
                servicesMatch
            ),
            djiJson = djiJson,
            djiJsonMatchesAdjacent = djiJsonMatch,
            dumlFrameworkLibrary = dumlFrameworkLibrary,
            dumlFrameworkLibraryMatchesAdjacent = dumlFrameworkLibraryMatch,
            adjacentBrokerReference = ReferenceClassificationPolicy.classifyBroker(
                djiJsonMatch,
                dumlFrameworkLibraryMatch
            ),
            upgradeRecoveryMarker = readUpgradeRecoveryMarker()
        )
    }

    private fun runningProcess(
        context: Context,
        applicationInfo: ApplicationInfo?
    ): RunningProcessCapability {
        val expectedName = applicationInfo?.processName
            ?: return RunningProcessCapability(RunningProcessProbeState.NOT_VISIBLE)
        return try {
            val manager = context.getSystemService(ActivityManager::class.java)
            val match = manager.runningAppProcesses
                ?.firstOrNull { it.processName == expectedName && it.uid == applicationInfo.uid }
                ?: return RunningProcessCapability(RunningProcessProbeState.NOT_VISIBLE)
            RunningProcessCapability(
                state = RunningProcessProbeState.FOUND,
                processName = match.processName,
                pid = match.pid,
                uid = match.uid,
                importance = match.importance
            )
        } catch (_: SecurityException) {
            RunningProcessCapability(RunningProcessProbeState.READ_DENIED)
        } catch (_: Throwable) {
            RunningProcessCapability(RunningProcessProbeState.INTERNAL_ERROR)
        }
    }

    private data class PackageEvidence(
        val state: PackageProbeState,
        val version: String? = null,
        val info: PackageInfo? = null,
        val signerSha256: String? = null
    )

    private data class ArchiveEntryRequest(
        val label: String,
        val entryName: String,
        val expectedSha256: String
    )

    private fun capability(
        manager: PackageManager,
        evidence: PackageEvidence,
        expectedNativeLibraryName: String? = null,
        computeSourceApkSha256: Boolean = false,
        sourceApkReferenceSha256: String? = null,
        archiveEntryRequests: List<ArchiveEntryRequest> = emptyList()
    ): PackageCapability {
        val app = evidence.info?.applicationInfo
        val flags = app?.flags
        val sourceApk = probePath(app?.publicSourceDir, computeSha256 = computeSourceApkSha256)
        val sourceApkDigest = sourceApk.sha256
            ?.takeIf { it.state == ReadOnlyValueState.VALUE }
            ?.value
        val archivePaths = ArchiveFingerprint.archivePaths(
            app?.publicSourceDir,
            app?.splitPublicSourceDirs
        )
        val packagedAbis = app?.let(::readPackagedAbis)
        val archiveEntries = archiveEntryRequests.map { request ->
            ArchiveFingerprint.fixedEntry(
                archivePaths = archivePaths,
                label = request.label,
                entryName = request.entryName,
                expectedSha256 = request.expectedSha256
            )
        }
        val dataDirectory = probePath(app?.dataDir)
        val nativeLibraryDirectory = probePath(app?.nativeLibraryDir)
        val nativeLibraryPath = if (app != null && expectedNativeLibraryName != null) {
            File(app.nativeLibraryDir, expectedNativeLibraryName).absolutePath
        } else {
            null
        }
        val expectedNativeLibrary = probePath(nativeLibraryPath, computeSha256 = true)
        val metadataStableDuringProbe = packageMetadataStable(manager, evidence)
        return PackageCapability(
            state = evidence.state,
            version = evidence.version,
            versionCode = evidence.info?.longVersionCode,
            lastUpdateTimeMs = evidence.info?.lastUpdateTime,
            splitCount = app?.let {
                evidence.info?.splitNames?.size ?: it.splitPublicSourceDirs?.size ?: 0
            },
            splitNames = app?.let {
                evidence.info?.splitNames
                    ?.sorted()
                    ?.joinToString(",")
                    ?: "none"
            },
            metadataStableDuringProbe = metadataStableDuringProbe,
            uid = app?.uid,
            isSystemUid = app?.uid?.let(PackageCapabilityPolicy::isSystemUid),
            isSystemApp = flags?.let {
                PackageCapabilityPolicy.hasFlag(it, ApplicationInfo.FLAG_SYSTEM)
            },
            isUpdatedSystemApp = flags?.let {
                PackageCapabilityPolicy.hasFlag(it, ApplicationInfo.FLAG_UPDATED_SYSTEM_APP)
            },
            isDebuggable = flags?.let {
                PackageCapabilityPolicy.hasFlag(it, ApplicationInfo.FLAG_DEBUGGABLE)
            },
            extractsNativeLibraries = flags?.let {
                PackageCapabilityPolicy.hasFlag(it, ApplicationInfo.FLAG_EXTRACT_NATIVE_LIBS)
            },
            processName = app?.processName,
            signerSha256 = evidence.signerSha256,
            signerMatchesAdjacentDjiPlatform = evidence.signerSha256?.let {
                it == ADJACENT_DJI_PLATFORM_CERT_SHA256
            },
            packagedAbis = packagedAbis,
            sourceApk = sourceApk,
            sourceApkMatchesReference = if (sourceApkReferenceSha256 != null) {
                sourceApkDigest?.let { it == sourceApkReferenceSha256 }
            } else {
                null
            },
            archiveEntries = archiveEntries,
            dataDirectory = dataDirectory,
            nativeLibraryDirectory = nativeLibraryDirectory,
            expectedNativeLibrary = expectedNativeLibrary
        )
    }

    @Suppress("DEPRECATION")
    private fun packageMetadataStable(
        manager: PackageManager,
        evidence: PackageEvidence
    ): Boolean? {
        val before = evidence.info ?: return null
        return try {
            val after = manager.getPackageInfo(
                before.packageName,
                PackageManager.GET_SIGNING_CERTIFICATES
            )
            before.longVersionCode == after.longVersionCode &&
                before.lastUpdateTime == after.lastUpdateTime &&
                before.applicationInfo?.publicSourceDir == after.applicationInfo?.publicSourceDir &&
                before.applicationInfo?.splitPublicSourceDirs?.toList().orEmpty() ==
                    after.applicationInfo?.splitPublicSourceDirs?.toList().orEmpty() &&
                before.splitNames?.toList().orEmpty() == after.splitNames?.toList().orEmpty()
        } catch (_: Throwable) {
            null
        }
    }

    private fun matchesDigest(file: FileCapability, expected: String): Boolean? = file.sha256
        ?.takeIf { it.state == ReadOnlyValueState.VALUE }
        ?.value
        ?.let { it == expected }

    @Suppress("DEPRECATION")
    private fun packageEvidence(
        manager: PackageManager,
        packageName: String
    ): PackageEvidence = try {
        val info = manager.getPackageInfo(packageName, PackageManager.GET_SIGNING_CERTIFICATES)
        val signer = info.signingInfo?.apkContentsSigners
            ?.map { signature ->
                PackageCapabilityPolicy.normalizeDigest(
                    MessageDigest.getInstance("SHA-256").digest(signature.toByteArray())
                )
            }
            ?.sorted()
            ?.joinToString(",")
        PackageEvidence(PackageProbeState.PRESENT, info.versionName, info, signer)
    } catch (_: PackageManager.NameNotFoundException) {
        PackageEvidence(PackageProbeState.ABSENT)
    } catch (_: SecurityException) {
        PackageEvidence(PackageProbeState.VISIBILITY_DENIED)
    } catch (_: Throwable) {
        PackageEvidence(PackageProbeState.INTERNAL_ERROR)
    }

    private fun readPackagedAbis(info: ApplicationInfo): String? = try {
        val paths = buildList {
            add(info.publicSourceDir)
            info.splitPublicSourceDirs?.let(::addAll)
        }
        val abis = sortedSetOf<String>()
        for (path in paths) {
            ZipFile(path).use { zip ->
                val entries = zip.entries()
                while (entries.hasMoreElements()) {
                    val name = entries.nextElement().name
                    if (!name.startsWith("lib/") || !name.endsWith(".so")) continue
                    val pieces = name.split('/')
                    if (pieces.size >= 3 && pieces[1].isNotBlank()) abis += pieces[1]
                }
            }
        }
        abis.takeIf { it.isNotEmpty() }?.joinToString(",") ?: "none-in-apk"
    } catch (_: Throwable) {
        "unreadable"
    }

    private fun probePath(path: String?, computeSha256: Boolean = false): FileCapability {
        if (path.isNullOrBlank()) return FileCapability()
        return try {
            val stat = Os.stat(path)
            val file = File(path)
            FileCapability(
                state = FileProbeState.PRESENT,
                path = path,
                kind = when {
                    OsConstants.S_ISDIR(stat.st_mode) -> "directory"
                    OsConstants.S_ISREG(stat.st_mode) -> "regular"
                    OsConstants.S_ISLNK(stat.st_mode) -> "symlink"
                    else -> "other"
                },
                ownerUid = stat.st_uid,
                ownerGid = stat.st_gid,
                mode = PackageCapabilityPolicy.formatMode(stat.st_mode),
                observerCanRead = file.canRead(),
                observerCanWrite = file.canWrite(),
                observerCanExecute = file.canExecute(),
                selinuxContext = readSelinuxFileContext(path),
                sha256 = if (computeSha256) readFileSha256(file) else null
            )
        } catch (error: ErrnoException) {
            when (error.errno) {
                OsConstants.ENOENT -> FileCapability(FileProbeState.ABSENT, path)
                OsConstants.EACCES,
                OsConstants.EPERM -> FileCapability(FileProbeState.READ_DENIED, path)
                else -> FileCapability(FileProbeState.INTERNAL_ERROR, path)
            }
        } catch (_: SecurityException) {
            FileCapability(FileProbeState.READ_DENIED, path)
        } catch (_: Throwable) {
            FileCapability(FileProbeState.INTERNAL_ERROR, path)
        }
    }

    private fun readFileSha256(file: File): ReadOnlyValue = try {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().buffered().use { input ->
            val buffer = ByteArray(64 * 1024)
            while (true) {
                val read = input.read(buffer)
                if (read < 0) break
                if (read > 0) digest.update(buffer, 0, read)
            }
            buffer.fill(0)
        }
        ReadOnlyValue(
            ReadOnlyValueState.VALUE,
            PackageCapabilityPolicy.normalizeDigest(digest.digest())
        )
    } catch (_: SecurityException) {
        ReadOnlyValue(ReadOnlyValueState.READ_DENIED)
    } catch (_: Throwable) {
        ReadOnlyValue(ReadOnlyValueState.INTERNAL_ERROR)
    }

    @Suppress("DEPRECATION")
    private fun activityState(
        manager: PackageManager,
        component: ComponentName
    ): ActivityProbeState = try {
        classifyActivity(manager.getActivityInfo(component, 0))
    } catch (_: PackageManager.NameNotFoundException) {
        ActivityProbeState.ABSENT
    } catch (_: SecurityException) {
        ActivityProbeState.VISIBILITY_DENIED
    } catch (_: Throwable) {
        ActivityProbeState.INTERNAL_ERROR
    }

    private fun classifyActivity(info: ActivityInfo): ActivityProbeState = when {
        info.exported && info.enabled -> ActivityProbeState.EXPORTED_ENABLED
        info.exported -> ActivityProbeState.EXPORTED_DISABLED
        info.enabled -> ActivityProbeState.PRIVATE_ENABLED
        else -> ActivityProbeState.PRIVATE_DISABLED
    }

    private fun readUpgradeRecoveryMarker(): UpgradeRecoveryMarkerState {
        val read = readFixedSystemProperty(UPGRADE_RECOVERY_PROPERTY, "0")
        return when (read.state) {
            ReadOnlyValueState.VALUE -> UpgradeRecoveryMarkerPolicy.classify(read.value.orEmpty())
            ReadOnlyValueState.HIDDEN_API_BLOCKED ->
                UpgradeRecoveryMarkerState.HIDDEN_API_BLOCKED
            ReadOnlyValueState.READ_DENIED -> UpgradeRecoveryMarkerState.READ_DENIED
            ReadOnlyValueState.INTERNAL_ERROR -> UpgradeRecoveryMarkerState.INTERNAL_ERROR
        }
    }

    @SuppressLint("PrivateApi")
    private fun readFixedSystemProperty(key: String, defaultValue: String): ReadOnlyValue = try {
        val systemProperties = Class.forName("android.os.SystemProperties")
        val getter = systemProperties.getDeclaredMethod(
            "get",
            String::class.java,
            String::class.java
        )
        val value = getter.invoke(null, key, defaultValue) as? String
            ?: return ReadOnlyValue(ReadOnlyValueState.INTERNAL_ERROR)
        ReadOnlyValue(ReadOnlyValueState.VALUE, value)
    } catch (error: Throwable) {
        classifyReflectionFailure(error)
    }

    @SuppressLint("PrivateApi")
    private fun readSelinuxBoolean(methodName: String): ReadOnlyValue = try {
        val selinux = Class.forName("android.os.SELinux")
        val method = selinux.getDeclaredMethod(methodName)
        val value = method.invoke(null) as? Boolean
            ?: return ReadOnlyValue(ReadOnlyValueState.INTERNAL_ERROR)
        ReadOnlyValue(ReadOnlyValueState.VALUE, value.toString())
    } catch (error: Throwable) {
        classifyReflectionFailure(error)
    }

    @SuppressLint("PrivateApi")
    private fun readSelinuxString(methodName: String): ReadOnlyValue = try {
        val selinux = Class.forName("android.os.SELinux")
        val method = selinux.getDeclaredMethod(methodName)
        val value = method.invoke(null) as? String
            ?: return ReadOnlyValue(ReadOnlyValueState.INTERNAL_ERROR)
        ReadOnlyValue(ReadOnlyValueState.VALUE, value)
    } catch (error: Throwable) {
        classifyReflectionFailure(error)
    }

    @SuppressLint("PrivateApi", "DiscouragedPrivateApi")
    private fun readSelinuxFileContext(path: String): ReadOnlyValue = try {
        val selinux = Class.forName("android.os.SELinux")
        val method = selinux.getDeclaredMethod("getFileContext", String::class.java)
        val value = method.invoke(null, path) as? String
            ?: return ReadOnlyValue(ReadOnlyValueState.INTERNAL_ERROR)
        ReadOnlyValue(ReadOnlyValueState.VALUE, value)
    } catch (error: Throwable) {
        classifyReflectionFailure(error)
    }

    private fun classifyReflectionFailure(error: Throwable): ReadOnlyValue {
        val cause = if (error is InvocationTargetException) {
            error.targetException ?: error
        } else {
            error
        }
        return when (cause) {
            is SecurityException -> ReadOnlyValue(ReadOnlyValueState.READ_DENIED)
            is ClassNotFoundException,
            is NoSuchMethodException,
            is IllegalAccessException -> ReadOnlyValue(ReadOnlyValueState.HIDDEN_API_BLOCKED)
            else -> ReadOnlyValue(ReadOnlyValueState.INTERNAL_ERROR)
        }
    }
}
