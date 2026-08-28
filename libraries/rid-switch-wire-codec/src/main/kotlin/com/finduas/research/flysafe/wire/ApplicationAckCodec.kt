package com.finduas.research.flysafe.wire

internal class AckFormatException(message: String) : IllegalArgumentException(message)

internal object ApplicationAckBounds {
    /** Local defensive cap, not a recovered DJI protocol constant. */
    const val MAX_APPLICATION_BODY_BYTES: Int = 64 * 1024
    const val V2_MIN_RECORD_DATA_BYTES: Int = 0x28
    const val V2_MAX_RECORD_DATA_BYTES: Int = 0x50
}

internal data class LicenseStatusBits(
    val invalid: Boolean,
    val enabled: Boolean,
    val inValidDate: Boolean,
    /** Bits 3..7 are preserved as an uninterpreted integer rather than guessed. */
    val uninterpretedHighBits: Int,
) {
    companion object {
        internal fun fromByte(value: Int): LicenseStatusBits = LicenseStatusBits(
            invalid = value and 0x01 != 0,
            enabled = value and 0x02 != 0,
            inValidDate = value and 0x04 != 0,
            uninterpretedHighBits = value and 0xf8,
        )
    }
}

internal sealed interface QueryApplicationAck : AutoCloseable {
    override fun close() = Unit

    data class End(val resultCode: Int = 1) : QueryApplicationAck

    data class Rejected(
        val resultCode: Int,
        val sdkErrorCode: Int,
    ) : QueryApplicationAck

    class V2Record internal constructor(
        val resultCode: Int,
        val record: SensitiveAckPayload,
    ) : QueryApplicationAck {
        override fun close() = record.close()
        override fun toString(): String =
            "V2Record(resultCode=$resultCode, record=<redacted:${record.size} bytes>)"
    }

    class ModernGroupInfo internal constructor(
        val version: FlySafeWireVersion,
        val protobuf: SensitiveAckPayload,
    ) : QueryApplicationAck {
        override fun close() = protobuf.close()
        override fun toString(): String =
            "ModernGroupInfo(version=$version, protobuf=<redacted:${protobuf.size} bytes>)"
    }

    class ModernLicenseRecord internal constructor(
        val version: FlySafeWireVersion,
        val resultCode: Int,
        val status: LicenseStatusBits,
        val licenseProtobuf: SensitiveAckPayload,
    ) : QueryApplicationAck {
        override fun close() = licenseProtobuf.close()
        override fun toString(): String =
            "ModernLicenseRecord(version=$version, resultCode=$resultCode, status=$status, " +
                "licenseProtobuf=<redacted:${licenseProtobuf.size} bytes>)"
    }
}

internal sealed interface SetEnableApplicationAck {
    data class Accepted(
        /** The exact state returned for the sole license ID in this typed operation. */
        val enabled: Boolean,
    ) : SetEnableApplicationAck

    data class Rejected(
        val resultCode: Int,
        val sdkErrorCode: Int,
    ) : SetEnableApplicationAck
}

/**
 * Parses application ACK bodies beginning with the provider-owned result-code byte. Every method
 * consumes and zeroes its input array on success or failure. Transport PackState is out of scope.
 */
/** Internal until a same-module full-frame PackState/correlation validator admits the body. */
internal object ApplicationAckCodec {
    private const val SDK_COMMON_QUERY_FAILURE: Int = 403
    private const val SDK_SET_ENABLE_FALLBACK_FAILURE: Int = 404

    fun consumeV2QueryPage(applicationBody: ByteArray): QueryApplicationAck =
        consume(applicationBody) { body ->
            val resultCode = unsigned(body[0])
            when (resultCode) {
                1 -> {
                    if (body.size != 1) {
                        throw AckFormatException("V2 query end marker must be exactly one byte")
                    }
                    QueryApplicationAck.End()
                }
                0 -> {
                    val dataLength = body.size - 1
                    if (dataLength !in ApplicationAckBounds.V2_MIN_RECORD_DATA_BYTES..
                        ApplicationAckBounds.V2_MAX_RECORD_DATA_BYTES
                    ) {
                        throw AckFormatException("V2 query record is outside the safe 40..80 byte range")
                    }
                    QueryApplicationAck.V2Record(
                        resultCode = resultCode,
                        record = sensitiveCopy(body, 1),
                    )
                }
                else -> QueryApplicationAck.Rejected(resultCode, SDK_COMMON_QUERY_FAILURE)
            }
        }

    fun consumeModernQueryStart(
        version: FlySafeWireVersion,
        applicationBody: ByteArray,
    ): QueryApplicationAck = consume(applicationBody) { body ->
            requireModern(version)
            val resultCode = unsigned(body[0])
            if (resultCode != 0) {
                QueryApplicationAck.Rejected(resultCode, SDK_COMMON_QUERY_FAILURE)
            } else {
                if (body.size < 2) {
                    throw AckFormatException("V3/V4 query start has no group-info protobuf")
                }
                QueryApplicationAck.ModernGroupInfo(
                    version = version,
                    protobuf = sensitiveCopy(body, 1),
                )
            }
        }

    fun consumeModernQueryPage(
        version: FlySafeWireVersion,
        applicationBody: ByteArray,
    ): QueryApplicationAck = consume(applicationBody) { body ->
            requireModern(version)
            val resultCode = unsigned(body[0])
            when (resultCode) {
                1 -> {
                    if (body.size != 1) {
                        throw AckFormatException("V3/V4 query end marker must be exactly one byte")
                    }
                    QueryApplicationAck.End()
                }
                0 -> {
                    if (body.size < 3) {
                        throw AckFormatException("V3/V4 query record needs status and non-empty protobuf")
                    }
                    val statusByte = unsigned(body[1])
                    QueryApplicationAck.ModernLicenseRecord(
                        version = version,
                        resultCode = resultCode,
                        status = LicenseStatusBits.fromByte(statusByte),
                        licenseProtobuf = sensitiveCopy(body, 2),
                    )
                }
                else -> QueryApplicationAck.Rejected(resultCode, SDK_COMMON_QUERY_FAILURE)
            }
        }

    fun consumeSetEnable(
        version: FlySafeWireVersion,
        applicationBody: ByteArray,
    ): SetEnableApplicationAck = consume(applicationBody) { body ->
        val resultCode = unsigned(body[0])
        if (resultCode != 0) {
            return@consume SetEnableApplicationAck.Rejected(
                resultCode = resultCode,
                sdkErrorCode = mapSetEnableError(version, resultCode),
            )
        }

        if (body.size != 3) {
            throw AckFormatException("successful single-license SetEnable ACK must be exactly three bytes")
        }
        val count = unsigned(body[1])
        if (count != 1) {
            throw AckFormatException("single-license SetEnable ACK count must be exactly one")
        }
        val item = unsigned(body[2])
        val enabled = when (version) {
            FlySafeWireVersion.V2 -> item != 0
            FlySafeWireVersion.V3, FlySafeWireVersion.V4 -> item and 0x02 != 0
        }
        SetEnableApplicationAck.Accepted(enabled = enabled)
    }

    private fun mapSetEnableError(version: FlySafeWireVersion, resultCode: Int): Int =
        when (version) {
            FlySafeWireVersion.V2 -> SDK_SET_ENABLE_FALLBACK_FAILURE
            FlySafeWireVersion.V3, FlySafeWireVersion.V4 -> when (resultCode) {
                1 -> 407
                2 -> 406
                3 -> 408
                4 -> 405
                5 -> 409
                else -> SDK_SET_ENABLE_FALLBACK_FAILURE
            }
        }

    private fun requireModern(version: FlySafeWireVersion) {
        if (version == FlySafeWireVersion.V2) {
            throw PayloadBoundsException("modern query ACK parser accepts only V3 or V4")
        }
    }

    private fun sensitiveCopy(source: ByteArray, fromIndex: Int): SensitiveAckPayload {
        val owned = source.copyOfRange(fromIndex, source.size)
        return try {
            SensitiveAckPayload(owned)
        } catch (error: Throwable) {
            owned.fill(0)
            throw error
        }
    }

    private fun <T> consume(applicationBody: ByteArray, parser: (ByteArray) -> T): T = try {
        if (applicationBody.isEmpty()) {
            throw AckFormatException("application ACK body is empty")
        }
        if (applicationBody.size > ApplicationAckBounds.MAX_APPLICATION_BODY_BYTES) {
            throw AckFormatException("application ACK body exceeds local safety bound")
        }
        parser(applicationBody)
    } finally {
        applicationBody.fill(0)
    }

    private fun unsigned(value: Byte): Int = value.toInt() and 0xff
}
