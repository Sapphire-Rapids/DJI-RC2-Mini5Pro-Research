package com.finduas.research.flysafe.wire

/** Fixed SetLicenseEnable application payloads. This object cannot build another command. */
internal object SetEnableRequestCodec {
    const val V2_PAYLOAD_SIZE: Int = 6
    const val V3_V4_PAYLOAD_SIZE: Int = 7

    fun encode(
        version: FlySafeWireVersion,
        licenseId: SensitiveLicenseId,
        enable: Boolean,
    ): SensitiveApplicationPayload {
        val bytes = ByteArray(
            if (version == FlySafeWireVersion.V2) V2_PAYLOAD_SIZE else V3_V4_PAYLOAD_SIZE,
        )
        return try {
            when (version) {
                FlySafeWireVersion.V2 -> {
                    licenseId.copyInto(bytes, 0)
                    bytes[4] = if (enable) 1 else 0
                    // bytes[5] remains the recovered reserved zero byte.
                }
                FlySafeWireVersion.V3, FlySafeWireVersion.V4 -> {
                    // bytes[0] remains zero.
                    licenseId.copyInto(bytes, 1)
                    bytes[5] = if (enable) 1 else 2
                    // bytes[6] remains the recovered reserved zero byte.
                }
            }
            SensitiveApplicationPayload(bytes)
        } catch (error: Throwable) {
            bytes.fill(0)
            throw error
        }
    }
}
