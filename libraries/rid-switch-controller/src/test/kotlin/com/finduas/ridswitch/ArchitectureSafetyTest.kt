package com.finduas.ridswitch

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.extension

class ArchitectureSafetyTest {
    @Test
    fun `production source has no device network cloud Android or persistence implementation`() {
        val imports = productionSources()
            .flatMap { Files.readAllLines(it) }
            .map(String::trim)
            .filter { it.startsWith("import ") }
            .joinToString("\n")

        val bannedImportPrefixes = listOf(
            "import android.",
            "import java.net.",
            "import java.io.File",
            "import java.nio.file.",
            "import okhttp3.",
            "import retrofit2.",
            "import io.ktor.",
            "import kotlinx.serialization.",
            "import java.sql.",
        )
        for (prefix in bannedImportPrefixes) {
            assertFalse("unexpected production dependency: $prefix", imports.contains(prefix))
        }
    }

    @Test
    fun `production contains only the typed transport interface and no implementation`() {
        val source = productionSources().joinToString("\n") { Files.readString(it) }
        assertTrue(source.contains("interface RidUnlockTransport"))
        assertFalse(Regex("class\\s+\\w+[^\\n]*:\\s*RidUnlockTransport").containsMatchIn(source))
        assertFalse(Regex("fun\\s+(write|setRid|sendRaw|rawCommand)\\s*\\(").containsMatchIn(source))
    }

    private fun productionSources(): List<Path> {
        val root = Path.of("src", "main", "kotlin")
        return Files.walk(root).use { paths ->
            paths.filter { Files.isRegularFile(it) && it.extension == "kt" }.toList()
        }
    }
}
