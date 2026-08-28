package com.finduas.research.flysafe.wire

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class SetEnableRequestCodecTest {
    private val idBytes = byteArrayOf(0x78, 0x56, 0x34, 0x12)

    @Test
    fun `V2 enable and disable layouts are exact and reserved byte stays zero`() {
        assertEncoded(
            version = FlySafeWireVersion.V2,
            enable = true,
            expected = byteArrayOf(0x78, 0x56, 0x34, 0x12, 0x01, 0x00),
        )
        assertEncoded(
            version = FlySafeWireVersion.V2,
            enable = false,
            expected = byteArrayOf(0x78, 0x56, 0x34, 0x12, 0x00, 0x00),
        )
    }

    @Test
    fun `V3 and V4 layouts use prefix state one or two and reserved suffix`() {
        for (version in listOf(FlySafeWireVersion.V3, FlySafeWireVersion.V4)) {
            assertEncoded(
                version = version,
                enable = true,
                expected = byteArrayOf(0x00, 0x78, 0x56, 0x34, 0x12, 0x01, 0x00),
            )
            assertEncoded(
                version = version,
                enable = false,
                expected = byteArrayOf(0x00, 0x78, 0x56, 0x34, 0x12, 0x02, 0x00),
            )
        }
    }

    @Test
    fun `license ID factory consumes source and closed values are inaccessible`() {
        val source = idBytes.copyOf()
        val id = SensitiveLicenseId.consumeLittleEndian(source)
        assertArrayEquals(ByteArray(4), source)
        assertTrue(id.toString().contains("<redacted>"))
        id.close()
        assertTrue(id.isClosed)
        assertThrows(IllegalStateException::class.java) {
            SetEnableRequestCodec.encode(FlySafeWireVersion.V2, id, true)
        }
    }

    @Test
    fun `invalid license ID source is still zeroed`() {
        val invalid = byteArrayOf(1, 2, 3)
        assertThrows(PayloadBoundsException::class.java) {
            SensitiveLicenseId.consumeLittleEndian(invalid)
        }
        assertArrayEquals(ByteArray(3), invalid)
    }

    @Test
    fun `sensitive payload redacts and zeroes scoped copies`() {
        val id = SensitiveLicenseId.consumeLittleEndian(idBytes.copyOf())
        val payload = SetEnableRequestCodec.encode(FlySafeWireVersion.V2, id, true)
        id.close()

        assertEquals(6, payload.size)
        assertTrue(payload.toString().contains("bytes=<redacted>"))
        lateinit var escapedCopy: ByteArray
        payload.useBytes { scoped ->
            escapedCopy = scoped
            assertArrayEquals(byteArrayOf(0x78, 0x56, 0x34, 0x12, 1, 0), scoped)
        }
        assertArrayEquals(ByteArray(6), escapedCopy)
        payload.close()
        assertTrue(payload.isClosed)
        assertThrows(IllegalStateException::class.java) {
            payload.useBytes { Unit }
        }
    }

    @Test
    fun `close overwrites owned license and payload backing arrays`() {
        val id = SensitiveLicenseId.consumeLittleEndian(idBytes.copyOf())
        val idBacking = backingBytes(id)
        assertArrayEquals(idBytes, idBacking)

        val payload = SetEnableRequestCodec.encode(FlySafeWireVersion.V3, id, false)
        val payloadBacking = backingBytes(payload)
        assertArrayEquals(byteArrayOf(0, 0x78, 0x56, 0x34, 0x12, 2, 0), payloadBacking)

        id.close()
        payload.close()
        assertArrayEquals(ByteArray(4), idBacking)
        assertArrayEquals(ByteArray(7), payloadBacking)
    }

    private fun assertEncoded(
        version: FlySafeWireVersion,
        enable: Boolean,
        expected: ByteArray,
    ) {
        val source = idBytes.copyOf()
        SensitiveLicenseId.consumeLittleEndian(source).use { id ->
            SetEnableRequestCodec.encode(version, id, enable).use { payload ->
                payload.useBytes { actual -> assertArrayEquals(expected, actual) }
            }
        }
        assertArrayEquals(ByteArray(4), source)
    }

    private fun backingBytes(owner: Any): ByteArray {
        val bufferField = owner.javaClass.getDeclaredField("buffer").apply { isAccessible = true }
        val buffer = bufferField.get(owner)
        val bytesField = buffer.javaClass.getDeclaredField("bytes").apply { isAccessible = true }
        return bytesField.get(buffer) as ByteArray
    }
}
