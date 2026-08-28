package com.finduas.research.flysafe.wire

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class QueryRequestCodecTest {
    @Test
    fun `fixed PackType and endpoint metadata cannot drift`() {
        with(FlySafeWireMetadata.QUERY_LICENSES) {
            assertEquals(0x38, packType)
            assertEquals(0x11, commandSet)
            assertEquals(0x11, commandId)
            assertEquals(0, tupleThirdByte)
            assertTrue(ackHasResultCodePrefix)
        }
        with(FlySafeWireMetadata.SET_LICENSE_ENABLE) {
            assertEquals(0x39, packType)
            assertEquals(0x11, commandSet)
            assertEquals(0x12, commandId)
            assertEquals(0, tupleThirdByte)
            assertTrue(ackHasResultCodePrefix)
        }
    }

    @Test
    fun `product 139 route remains unconfirmed metadata and is not used by codec`() {
        assertEquals(139, Product139RouteResearchMetadata.PRODUCT_ID)
        assertEquals(0x92, Product139RouteResearchMetadata.STATIC_CANDIDATE_PACKED_ROUTE)
        assertEquals(
            RouteEvidenceGate.RUNTIME_OBSERVATION_REQUIRED,
            Product139RouteResearchMetadata.evidenceGate,
        )
        assertFalse(Product139RouteResearchMetadata.USED_BY_CODEC)
    }

    @Test
    fun `V2 query page is exactly one bounded index byte`() {
        assertArrayEquals(byteArrayOf(0x00), QueryRequestCodec.encodePage(FlySafeWireVersion.V2, 0))
        assertArrayEquals(byteArrayOf(0x7f), QueryRequestCodec.encodePage(FlySafeWireVersion.V2, 127))
        assertArrayEquals(byteArrayOf(0xff.toByte()), QueryRequestCodec.encodePage(FlySafeWireVersion.V2, 255))
        assertThrows(PayloadBoundsException::class.java) {
            QueryRequestCodec.encodePage(FlySafeWireVersion.V2, -1)
        }
        assertThrows(PayloadBoundsException::class.java) {
            QueryRequestCodec.encodePage(FlySafeWireVersion.V2, 256)
        }
        assertThrows(PayloadBoundsException::class.java) {
            QueryRequestCodec.encodeStart(FlySafeWireVersion.V2)
        }
    }

    @Test
    fun `V3 and V4 query start and shifted pages never wrap`() {
        for (version in listOf(FlySafeWireVersion.V3, FlySafeWireVersion.V4)) {
            assertArrayEquals(byteArrayOf(0x00, 0x01), QueryRequestCodec.encodeStart(version))
            assertArrayEquals(byteArrayOf(0x00, 0x00), QueryRequestCodec.encodePage(version, 0))
            assertArrayEquals(byteArrayOf(0x00, 0x02), QueryRequestCodec.encodePage(version, 1))
            assertArrayEquals(
                byteArrayOf(0x00, 0xfe.toByte()),
                QueryRequestCodec.encodePage(version, 127),
            )
            assertThrows(PayloadBoundsException::class.java) {
                QueryRequestCodec.encodePage(version, -1)
            }
            assertThrows(PayloadBoundsException::class.java) {
                QueryRequestCodec.encodePage(version, 128)
            }
        }
    }
}
