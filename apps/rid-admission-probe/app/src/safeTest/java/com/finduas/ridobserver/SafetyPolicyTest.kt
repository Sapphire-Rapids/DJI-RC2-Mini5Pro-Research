package com.finduas.ridobserver

import java.nio.file.Files
import java.nio.file.Path
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SafetyPolicyTest {
    @Test
    fun releaseManifestHasNoPermissionsOrBackgroundComponents() {
        val manifest = source("src/safe/AndroidManifest.xml")
        assertFalse(manifest.contains("uses-permission"))
        assertFalse(manifest.contains("<service"))
        assertFalse(manifest.contains("<receiver"))
        assertFalse(manifest.contains("<provider"))
    }

    @Test
    fun packagedSourceSetExcludesLegacySocketObserver() {
        val build = source("build.gradle.kts")
        assertTrue(build.contains("manifest.srcFile(\"src/safe/AndroidManifest.xml\")"))
        assertTrue(build.contains("java.setSrcDirs(listOf(\"src/safe/java\"))"))
        val sources = safeSources()
        for (forbidden in listOf(
            "java.net", "Socket(", "connect(",
            "127.0.0.1", "40007", "40009", "ObserverService", "startService",
            "Runtime.getRuntime", "ProcessBuilder", "dalvik.system",
            "DexFile", "loadClass(", "createPackageContext", "FileOutputStream",
            "System.load", ".loadLibrary(", ".writeText(", ".writeBytes(",
            ".appendText(", ".appendBytes(", "Files.newOutputStream(",
            "Files.newBufferedWriter(", "Os.write(", "Os.pwrite(", "Os.socket(",
            "Os.connect(", "Os.sendto("
        )) {
            assertFalse("packaged source contains $forbidden", sources.contains(forbidden))
        }
    }

    @Test
    fun binderProbeStopsBeforeApplicationTransactions() {
        val probe = source("src/safe/java/com/finduas/ridobserver/ProtocolBinderProbe.kt")
        assertTrue(probe.contains("checkService"))
        assertTrue(probe.contains("pingBinder"))
        assertTrue(probe.contains("interfaceDescriptor"))
        for (forbidden in listOf(
            "android.os.Parcel", ".transact(", "sendWithListen", "addPackListener",
            "removePackListener", "Pack.Builder"
        )) {
            assertFalse("active Binder surface contains $forbidden", probe.contains(forbidden))
        }
    }

    @Test
    fun archiveFingerprintIsReadOnlyBoundedAndNeverLoadsTargetCode() {
        val source = source("src/safe/java/com/finduas/ridobserver/ArchiveFingerprint.kt")
        assertTrue(source.contains("MAX_ENTRY_BYTES"))
        assertTrue(source.contains("ZipFile"))
        assertTrue(source.contains("MessageDigest"))
        for (forbidden in listOf(
            "DexFile", "ClassLoader", "loadClass", "FileOutputStream", "ZipOutputStream",
            "Runtime.getRuntime", "ProcessBuilder"
        )) {
            assertFalse("archive scanner contains $forbidden", source.contains(forbidden))
        }
    }

    @Test
    fun uiExplainsFailClosedBoundary() {
        val strings = source("src/safe/res/values/strings.xml")
        assertTrue(strings.contains("没有网络权限"))
        assertTrue(strings.contains("40007/40009 已硬禁用"))
        assertTrue(strings.contains("不是 FAA Remote ID 或全局 RID 总开关"))
        assertTrue(strings.contains("不执行 DJI 协议 Binder 应用事务"))
        assertTrue(strings.contains("哈希只读取、不加载或执行目标代码"))
        assertTrue(strings.contains("/proc/self/maps"))
        assertTrue(strings.contains("不反射或枚举 DJI/ART 私有类"))
        assertTrue(strings.contains("打开 Android 开发者选项"))
        assertTrue(strings.contains("打开 Android 设备信息"))
        val activity = source("src/safe/java/com/finduas/ridobserver/MainActivity.kt")
        assertTrue(activity.contains("路径权限均为 Observer 自身 UID/SELinux 视角"))
        assertTrue(activity.contains("不证明 UID1000 可写"))
        assertTrue(activity.contains("copyCompleteReport"))
        assertTrue(activity.contains("finduas-rid-probe/v0.10-schema-1"))
        assertTrue(activity.contains("ProbeRunState.RUNNING"))
        assertTrue(activity.contains("ProbeRunState.COMPLETE"))
        assertTrue(activity.contains("ProbeRunState.INCOMPLETE"))
        assertTrue(activity.contains("ProbeSessionCoordinator"))
        assertTrue(activity.contains("ProbeRunAdmissionPolicy.mayStart"))
        assertTrue(activity.contains("machine_section_end=true"))
    }

    @Test
    fun versionAndApplicationIdRemainUpgradeCompatible() {
        val build = source("build.gradle.kts")
        assertTrue(build.contains("applicationId = \"com.finduas.ridobserver\""))
        assertTrue(build.contains("versionCode = 11"))
        assertTrue(build.contains("versionName = \"0.11.0-report-export\""))
    }

    @Test
    fun artIdentitySectionIsSelfProcessOnlyAndAddsNoPrivateRuntimeSurface() {
        val probe = source(
            "src/safe/java/com/finduas/ridobserver/AndroidArtIdentityProbe.kt"
        )
        assertTrue(probe.contains("SELF_MAPS_PATH = \"/proc/self/maps\""))
        assertTrue(probe.contains("readMapsSnapshot(pageSize)"))
        assertTrue(probe.contains("readMapsSnapshot(firstScan.pageSizeBytes)"))
        assertTrue(probe.contains("firstScan != secondScan"))
        assertTrue(probe.contains("Os.lstat(identity.path)"))
        assertTrue(probe.contains("OsConstants.O_NOFOLLOW"))
        assertTrue(probe.contains("Os.fstat(descriptor)"))
        assertTrue(probe.contains("st_mtim.tv_nsec"))
        assertTrue(probe.contains("st_ctim.tv_nsec"))
        assertTrue(probe.contains("descriptorBefore.st_dev == 0L"))
        assertTrue(probe.contains("start <= 0L"))
        assertTrue(probe.contains("decimal.matches(fields[4])"))
        assertTrue(probe.contains("!hexadecimal.matches(parts[0])"))
        assertTrue(probe.contains("MessageDigest.getInstance(\"SHA-256\")"))
        assertTrue(probe.contains("ElfBuildIdReader.read"))
        for (required in listOf(
            "3ec3d232ad7f4099c42f014b87658be47e83d7e21a7a053fb16c4d146103745d",
            "5f839ecc60b9ae39764305b5fee6ed37",
            "0x5ccfa0L", "0x100",
            "098c16b8613f438294017b8af2e2e45685556a9cf5c6882120f08a5ea315c668",
            "0x56bfc4L", "0xebc",
            "9db764e816c6771623e660b308d2527da4e57d05530ae7a3c8dfdf9d07dec80a"
        )) {
            assertTrue("ART probe misses $required", probe.contains(required))
        }
        assertTrue(probe.contains("KNOWN_AGENT_UNLOAD_RANGE_OFFSET = 0x5ccfa0L"))
        assertTrue(probe.contains("KNOWN_RUNTIME_ATTACH_AGENT_RANGE_OFFSET = 0x56bfc4L"))
        assertFalse(probe.contains("KNOWN_ATTACH_RANGE"))
        assertFalse(probe.contains("KNOWN_LOADER_RANGE"))
        for (forbidden in listOf(
            "Class.forName", "getDeclaredMethod", "java.lang.reflect", ".invoke(",
            "attachJvmtiAgent", "AttachAgent(", "System.load", "loadLibrary(",
            "Runtime.getRuntime", "ProcessBuilder", "DexFile", "ClassLoader",
            "java.net", "Socket(", "dji.go.v5", "com.dji."
        )) {
            assertFalse("ART identity probe contains $forbidden", probe.contains(forbidden))
        }
        assertEqualsOneSelfProcPath(probe)
    }

    @Test
    fun settingsButtonsOnlyNavigateFixedAndroidSettingsActions() {
        val activity = source("src/safe/java/com/finduas/ridobserver/MainActivity.kt")
        for (required in listOf(
            "Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS",
            "Settings.ACTION_DEVICE_INFO_SETTINGS",
            "Settings.ACTION_SETTINGS",
            "ActivityNotFoundException",
            "SettingsNavigationState.ACTIVITY_NOT_FOUND",
            "SettingsNavigationState.DENIED",
            "startActivity(Intent(action))"
        )) {
            assertTrue("settings navigation misses $required", activity.contains(required))
        }
        assertTrue(
            "only the fixed settings helper may call startActivity",
            Regex("startActivity\\(").findAll(safeSources()).count() == 1
        )
        for (forbidden in listOf(
            ".setPackage(", ".setComponent(", ".putExtra(", ".setData(",
            "dji.go.v5", "com.dji."
        )) {
            assertFalse("settings navigation contains $forbidden", activity.contains(forbidden))
        }
    }

    @Test
    fun manifestQueriesOnlyFixedResearchPackages() {
        val manifest = source("src/safe/AndroidManifest.xml")
        for (packageName in listOf(
            "dji.go.v5",
            "com.dpad.fuli",
            "com.finduas.jvmti.canary.carrier",
            "com.finduas.jvmti.eidresolver.v1"
        )) {
            assertTrue(manifest.contains("android:name=\"$packageName\""))
        }
    }

    private fun safeSources(): String = Files.walk(Path.of("src/safe/java")).use { paths ->
        paths.filter { Files.isRegularFile(it) && it.fileName.toString().endsWith(".kt") }
            .sorted()
            .map { String(Files.readAllBytes(it), Charsets.UTF_8) }
            .toList()
            .joinToString("\n")
    }

    private fun source(relative: String): String =
        String(Files.readAllBytes(Path.of(relative)), Charsets.UTF_8)

    private fun assertEqualsOneSelfProcPath(source: String) {
        val procPaths = Regex("/proc/[A-Za-z0-9_{}$./-]+").findAll(source)
            .map { it.value.trimEnd('.', ',') }
            .toSet()
        assertTrue("unexpected proc paths: $procPaths", procPaths == setOf("/proc/self/maps"))
    }
}
