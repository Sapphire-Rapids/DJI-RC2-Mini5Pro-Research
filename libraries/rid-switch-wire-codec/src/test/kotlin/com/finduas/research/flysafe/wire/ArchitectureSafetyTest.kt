package com.finduas.research.flysafe.wire

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.extension

class ArchitectureSafetyTest {
    @Test
    fun `production source has no device network Android USB logging or persistence dependency`() {
        val source = productionSourceText()
        val bannedFragments = listOf(
            "import android.",
            "import java.net.",
            "import java.io.",
            "import java.nio.file.",
            "javax.usb",
            "libusb",
            "Socket",
            "UsbDevice",
            "bulkTransfer",
            "okhttp",
            "retrofit",
            "ktor",
            "java.sql",
            "println(",
            "printStackTrace(",
            "Logger",
        )
        for (fragment in bannedFragments) {
            assertFalse("unexpected production capability: $fragment", source.contains(fragment))
        }
    }

    @Test
    fun `codec exposes fixed operations and no generic route frame or command sender`() {
        val source = productionSourceText()
        assertTrue(source.contains("object QueryRequestCodec"))
        assertTrue(source.contains("object SetEnableRequestCodec"))
        assertTrue(source.contains("object ApplicationAckCodec"))
        assertFalse(Regex("fun\\s+(send|write|transmit|buildRaw|rawCommand)\\s*\\(").containsMatchIn(source))
        assertFalse(Regex("fun\\s+\\w+\\s*\\([^)]*(cmdSet|commandSet|commandId|packType|route)\\s*:").containsMatchIn(source))
        assertTrue(source.contains("internal object SetEnableRequestCodec"))
        assertTrue(source.contains("internal object ApplicationAckCodec"))
        assertTrue(source.contains("internal class SensitiveLicenseId"))
        assertTrue(source.contains("internal object Product139RouteResearchMetadata"))
        assertFalse(source.contains("VerifiedRidLicenseId"))
    }

    private fun productionSourceText(): String = productionSources()
        .joinToString("\n") { Files.readString(it) }

    private fun productionSources(): List<Path> {
        val root = Path.of("src", "main", "kotlin")
        return Files.walk(root).use { paths ->
            paths.filter { Files.isRegularFile(it) && it.extension == "kt" }.toList()
        }
    }
}
