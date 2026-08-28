package com.finduas.research.flysafe.wire

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class ApplicationAckCodecTest {
    @Test
    fun `V2 page parses end and bounded opaque record while consuming input`() {
        val endBody = byteArrayOf(1)
        val end = ApplicationAckCodec.consumeV2QueryPage(endBody)
        assertTrue(end is QueryApplicationAck.End)
        assertArrayEquals(ByteArray(1), endBody)

        val recordBody = byteArrayOf(0) + ByteArray(40) { it.toByte() }
        val record = ApplicationAckCodec.consumeV2QueryPage(recordBody) as QueryApplicationAck.V2Record
        assertArrayEquals(ByteArray(41), recordBody)
        assertEquals(0, record.resultCode)
        assertEquals(40, record.record.size)
        assertTrue(record.toString().contains("<redacted:40 bytes>"))
        record.close()
        assertTrue(record.record.isClosed)
    }

    @Test
    fun `query records require result zero and end markers reject trailing bytes`() {
        val v2RejectedBody = byteArrayOf(7) + ByteArray(40)
        val v2Rejected = ApplicationAckCodec.consumeV2QueryPage(v2RejectedBody)
            as QueryApplicationAck.Rejected
        assertEquals(7, v2Rejected.resultCode)
        assertEquals(403, v2Rejected.sdkErrorCode)
        assertArrayEquals(ByteArray(41), v2RejectedBody)

        val modernRejectedBody = byteArrayOf(7, 0xfd.toByte(), 0x3a)
        val modernRejected = ApplicationAckCodec.consumeModernQueryPage(
            FlySafeWireVersion.V4,
            modernRejectedBody,
        ) as QueryApplicationAck.Rejected
        assertEquals(7, modernRejected.resultCode)
        assertEquals(403, modernRejected.sdkErrorCode)
        assertArrayEquals(ByteArray(3), modernRejectedBody)

        for (body in listOf(byteArrayOf(1, 0), byteArrayOf(1, 9, 9))) {
            assertThrows(AckFormatException::class.java) {
                ApplicationAckCodec.consumeModernQueryPage(FlySafeWireVersion.V3, body)
            }
            assertArrayEquals(ByteArray(body.size), body)
        }
        val v2EndWithTail = byteArrayOf(1, 0)
        assertThrows(AckFormatException::class.java) {
            ApplicationAckCodec.consumeV2QueryPage(v2EndWithTail)
        }
        assertArrayEquals(ByteArray(2), v2EndWithTail)
    }

    @Test
    fun `V2 page rejects a short record and still consumes it`() {
        val body = byteArrayOf(0) + ByteArray(39)
        assertThrows(AckFormatException::class.java) {
            ApplicationAckCodec.consumeV2QueryPage(body)
        }
        assertArrayEquals(ByteArray(40), body)
    }

    @Test
    fun `V2 page enforces the safe forty through eighty byte record range`() {
        for (size in listOf(40, 80)) {
            val body = byteArrayOf(0) + ByteArray(size)
            val record = ApplicationAckCodec.consumeV2QueryPage(body)
                as QueryApplicationAck.V2Record
            assertEquals(size, record.record.size)
            assertArrayEquals(ByteArray(size + 1), body)
            record.close()
        }
        val tooLarge = byteArrayOf(0) + ByteArray(81)
        assertThrows(AckFormatException::class.java) {
            ApplicationAckCodec.consumeV2QueryPage(tooLarge)
        }
        assertArrayEquals(ByteArray(82), tooLarge)
    }

    @Test
    fun `modern start separates result code and keeps protobuf sensitive`() {
        for (version in listOf(FlySafeWireVersion.V3, FlySafeWireVersion.V4)) {
            val body = byteArrayOf(0, 0x08, 0x07)
            val parsed = ApplicationAckCodec.consumeModernQueryStart(version, body)
                as QueryApplicationAck.ModernGroupInfo
            assertArrayEquals(ByteArray(3), body)
            assertEquals(version, parsed.version)
            parsed.protobuf.useBytes { assertArrayEquals(byteArrayOf(0x08, 0x07), it) }
            assertTrue(parsed.toString().contains("<redacted:2 bytes>"))
            parsed.close()
        }

        val rejectedBody = byteArrayOf(5, 0x55)
        val rejected = ApplicationAckCodec.consumeModernQueryStart(
            FlySafeWireVersion.V3,
            rejectedBody,
        ) as QueryApplicationAck.Rejected
        assertEquals(5, rejected.resultCode)
        assertEquals(403, rejected.sdkErrorCode)
        assertArrayEquals(ByteArray(2), rejectedBody)
    }

    @Test
    fun `scoped sensitive copy is zeroed even when consumer throws`() {
        val body = byteArrayOf(0, 0x08, 0x07)
        val parsed = ApplicationAckCodec.consumeModernQueryStart(FlySafeWireVersion.V3, body)
            as QueryApplicationAck.ModernGroupInfo
        lateinit var escaped: ByteArray
        assertThrows(IllegalStateException::class.java) {
            parsed.protobuf.useBytes {
                escaped = it
                throw IllegalStateException("synthetic callback failure")
            }
        }
        assertArrayEquals(ByteArray(2), escaped)
        parsed.close()
    }

    @Test
    fun `modern page maps low status bits preserves high bits and accepts exact end marker`() {
        val body = byteArrayOf(0, 0xfd.toByte(), 0x3a, 0x00)
        val parsed = ApplicationAckCodec.consumeModernQueryPage(
            FlySafeWireVersion.V4,
            body,
        ) as QueryApplicationAck.ModernLicenseRecord
        assertArrayEquals(ByteArray(4), body)
        assertEquals(0, parsed.resultCode)
        assertTrue(parsed.status.invalid)
        assertFalse(parsed.status.enabled)
        assertTrue(parsed.status.inValidDate)
        assertEquals(0xf8, parsed.status.uninterpretedHighBits)
        parsed.licenseProtobuf.useBytes { assertArrayEquals(byteArrayOf(0x3a, 0x00), it) }
        parsed.close()

        val endBody = byteArrayOf(1)
        assertTrue(
            ApplicationAckCodec.consumeModernQueryPage(FlySafeWireVersion.V3, endBody)
                is QueryApplicationAck.End,
        )
        assertArrayEquals(ByteArray(1), endBody)
    }

    @Test
    fun `modern query parser rejects wrong generation empty payload and oversized body`() {
        val wrongGeneration = byteArrayOf(0, 1)
        assertThrows(PayloadBoundsException::class.java) {
            ApplicationAckCodec.consumeModernQueryStart(FlySafeWireVersion.V2, wrongGeneration)
        }
        assertArrayEquals(ByteArray(2), wrongGeneration)

        val emptyStart = byteArrayOf(0)
        assertThrows(AckFormatException::class.java) {
            ApplicationAckCodec.consumeModernQueryStart(FlySafeWireVersion.V3, emptyStart)
        }
        assertArrayEquals(ByteArray(1), emptyStart)

        val emptyRecord = byteArrayOf(0, 0x02)
        assertThrows(AckFormatException::class.java) {
            ApplicationAckCodec.consumeModernQueryPage(FlySafeWireVersion.V3, emptyRecord)
        }
        assertArrayEquals(ByteArray(2), emptyRecord)

        val oversized = ByteArray(ApplicationAckBounds.MAX_APPLICATION_BODY_BYTES + 1) { 1 }
        assertThrows(AckFormatException::class.java) {
            ApplicationAckCodec.consumeV2QueryPage(oversized)
        }
        assertArrayEquals(ByteArray(oversized.size), oversized)
    }

    @Test
    fun `SetEnable V2 interprets the sole nonzero item`() {
        for ((raw, expected) in listOf(0 to false, 1 to true, 2 to true)) {
            val body = byteArrayOf(0, 1, raw.toByte())
            val ack = ApplicationAckCodec.consumeSetEnable(FlySafeWireVersion.V2, body)
                as SetEnableApplicationAck.Accepted
            assertEquals(expected, ack.enabled)
            assertArrayEquals(ByteArray(3), body)
        }
    }

    @Test
    fun `SetEnable V3 and V4 interpret bit one`() {
        for (version in listOf(FlySafeWireVersion.V3, FlySafeWireVersion.V4)) {
            for ((raw, expected) in listOf(0 to false, 1 to false, 2 to true, 3 to true)) {
                val body = byteArrayOf(0, 1, raw.toByte())
                val ack = ApplicationAckCodec.consumeSetEnable(version, body)
                    as SetEnableApplicationAck.Accepted
                assertEquals(expected, ack.enabled)
                assertArrayEquals(ByteArray(3), body)
            }
        }
    }

    @Test
    fun `SetEnable error mapping is exact at current evidence boundary`() {
        val v2 = ApplicationAckCodec.consumeSetEnable(
            FlySafeWireVersion.V2,
            byteArrayOf(1),
        ) as SetEnableApplicationAck.Rejected
        assertEquals(404, v2.sdkErrorCode)

        val expected = mapOf(1 to 407, 2 to 406, 3 to 408, 4 to 405, 5 to 409, 6 to 404)
        for ((result, sdk) in expected) {
            val parsed = ApplicationAckCodec.consumeSetEnable(
                FlySafeWireVersion.V3,
                byteArrayOf(result.toByte()),
            ) as SetEnableApplicationAck.Rejected
            assertEquals(result, parsed.resultCode)
            assertEquals(sdk, parsed.sdkErrorCode)
        }
    }

    @Test
    fun `SetEnable success requires exact single item count and no extension tail`() {
        val noCount = byteArrayOf(0)
        assertThrows(AckFormatException::class.java) {
            ApplicationAckCodec.consumeSetEnable(FlySafeWireVersion.V4, noCount)
        }
        assertArrayEquals(ByteArray(1), noCount)

        for (invalid in listOf(
            byteArrayOf(0, 0, 1),
            byteArrayOf(0, 2, 1),
            byteArrayOf(0, 1),
            byteArrayOf(0, 1, 2, 0x55),
        )) {
            assertThrows(AckFormatException::class.java) {
                ApplicationAckCodec.consumeSetEnable(FlySafeWireVersion.V4, invalid)
            }
            assertArrayEquals(ByteArray(invalid.size), invalid)
        }
    }
}
