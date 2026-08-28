package com.finduas.research.flysafe.wire

enum class FlySafeWireVersion {
    V2,
    V3,
    V4,
}

class PayloadBoundsException(message: String) : IllegalArgumentException(message)

/** Fixed QueryLicenseFromFC application payloads. This object cannot build another command. */
object QueryRequestCodec {
    const val V2_MIN_INDEX: Int = 0
    const val V2_MAX_INDEX: Int = 0xff
    const val MODERN_MIN_INDEX: Int = 0
    const val MODERN_MAX_INDEX: Int = 0x7f

    fun encodeStart(version: FlySafeWireVersion): ByteArray = when (version) {
        FlySafeWireVersion.V2 -> throw PayloadBoundsException("V2 has no separate start selector")
        FlySafeWireVersion.V3, FlySafeWireVersion.V4 -> byteArrayOf(0x00, 0x01)
    }

    fun encodePage(version: FlySafeWireVersion, index: Int): ByteArray = when (version) {
        FlySafeWireVersion.V2 -> {
            if (index !in V2_MIN_INDEX..V2_MAX_INDEX) {
                throw PayloadBoundsException("V2 query index is outside 0..255")
            }
            byteArrayOf(index.toByte())
        }

        FlySafeWireVersion.V3, FlySafeWireVersion.V4 -> {
            if (index !in MODERN_MIN_INDEX..MODERN_MAX_INDEX) {
                throw PayloadBoundsException("V3/V4 query index is outside non-wrapping 0..127")
            }
            byteArrayOf(0x00, (index shl 1).toByte())
        }
    }
}
