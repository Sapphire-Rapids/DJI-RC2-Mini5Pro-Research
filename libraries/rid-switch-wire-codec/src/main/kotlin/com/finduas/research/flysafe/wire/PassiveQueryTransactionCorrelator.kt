package com.finduas.research.flysafe.wire

/** Why a checksum-valid FlySafe frame was not admitted to the correlated query ACK parser. */
internal enum class QueryCorrelationRejection {
    INVALID_DUML,
    UNSUPPORTED_COMMAND_TYPE,
    INVALID_REQUEST_SHAPE,
    RESPONSE_WITHOUT_REQUEST,
    AMBIGUOUS_SEQUENCE,
    ROUTE_MISMATCH,
    EMPTY_RESPONSE_BODY,
    TOO_MANY_PENDING_REQUESTS,
}

internal sealed interface QueryCorrelationEvent {
    data object Unrelated : QueryCorrelationEvent
    data object RequestObserved : QueryCorrelationEvent
    data object ExactRequestRetransmissionObserved : QueryCorrelationEvent
    data class Rejected(val reason: QueryCorrelationRejection) : QueryCorrelationEvent

    /**
     * A response admitted only after CRC, command type, sequence, reverse route and command match.
     * The application body starts with DJI's protocol-result byte and is deterministically zeroed.
     */
    class CorrelatedAck internal constructor(
        val version: FlySafeWireVersion,
        val requestKind: QueryRequestKind,
        internal val applicationBody: SensitiveAckPayload,
    ) : QueryCorrelationEvent, AutoCloseable {
        override fun close() = applicationBody.close()

        override fun toString(): String =
            "CorrelatedAck(version=$version, requestKind=$requestKind, body=<redacted:${applicationBody.size} bytes>)"
    }
}

internal sealed interface QueryRequestKind {
    data object ModernStart : QueryRequestKind
    data class Page(val index: Int) : QueryRequestKind
}

/**
 * Input-only full-frame transaction gate for `0x11/0x11 QueryLicense`.
 *
 * It never creates a DUML frame and has no transport. Each supplied frame is consumed and zeroed.
 * A response is released only once, and only when it reverses the exact request route and preserves
 * the request sequence and command. Pending requests expire at the recovered six-second timeout.
 */
internal class PassiveQueryTransactionCorrelator(
    private val version: FlySafeWireVersion,
    private val nowNanos: () -> Long = System::nanoTime,
) : AutoCloseable {
    private data class PendingRequest(
        val source: Int,
        val destination: Int,
        val kind: QueryRequestKind,
        val expiresAtNanos: Long,
    )

    private val pendingBySequence = mutableMapOf<Int, PendingRequest>()
    private val ambiguousUntilBySequence = mutableMapOf<Int, Long>()
    private var closed = false

    @Synchronized
    fun consume(frame: ByteArray): QueryCorrelationEvent {
        return try {
            check(!closed) { "correlator is closed" }
            val now = nowNanos()
            expire(now)

            val header = DumlFrameValidator.parse(frame)
                ?: return QueryCorrelationEvent.Rejected(QueryCorrelationRejection.INVALID_DUML)
            if (header.commandSet != FLYSAFE_COMMAND_SET || header.commandId != QUERY_LICENSE) {
                return QueryCorrelationEvent.Unrelated
            }

            when (header.commandType) {
                REQUEST_ACK_AFTER_EXEC_PLAINTEXT -> admitRequest(frame, header, now)
                RESPONSE_PLAINTEXT -> admitResponse(frame, header)
                else -> QueryCorrelationEvent.Rejected(
                    QueryCorrelationRejection.UNSUPPORTED_COMMAND_TYPE,
                )
            }
        } finally {
            frame.fill(0)
        }
    }

    private fun admitRequest(
        frame: ByteArray,
        header: DumlHeader,
        now: Long,
    ): QueryCorrelationEvent {
        val requestKind = decodeRequestKind(frame, header.payloadLength)
            ?: return QueryCorrelationEvent.Rejected(QueryCorrelationRejection.INVALID_REQUEST_SHAPE)

        if (header.sequence in ambiguousUntilBySequence) {
            return QueryCorrelationEvent.Rejected(QueryCorrelationRejection.AMBIGUOUS_SEQUENCE)
        }
        val existing = pendingBySequence[header.sequence]
        if (existing != null) {
            if (
                existing.source == header.source &&
                existing.destination == header.destination &&
                existing.kind == requestKind
            ) {
                pendingBySequence[header.sequence] = existing.copy(
                    expiresAtNanos = saturatingAdd(now, REQUEST_TTL_NANOS),
                )
                return QueryCorrelationEvent.ExactRequestRetransmissionObserved
            }
            pendingBySequence.remove(header.sequence)
            ambiguousUntilBySequence[header.sequence] = saturatingAdd(now, REQUEST_TTL_NANOS)
            return QueryCorrelationEvent.Rejected(QueryCorrelationRejection.AMBIGUOUS_SEQUENCE)
        }
        if (pendingBySequence.size >= MAX_PENDING_REQUESTS) {
            pendingBySequence.clear()
            ambiguousUntilBySequence.clear()
            return QueryCorrelationEvent.Rejected(
                QueryCorrelationRejection.TOO_MANY_PENDING_REQUESTS,
            )
        }

        pendingBySequence[header.sequence] = PendingRequest(
            source = header.source,
            destination = header.destination,
            kind = requestKind,
            expiresAtNanos = saturatingAdd(now, REQUEST_TTL_NANOS),
        )
        return QueryCorrelationEvent.RequestObserved
    }

    private fun admitResponse(frame: ByteArray, header: DumlHeader): QueryCorrelationEvent {
        if (header.sequence in ambiguousUntilBySequence) {
            return QueryCorrelationEvent.Rejected(QueryCorrelationRejection.AMBIGUOUS_SEQUENCE)
        }
        val pending = pendingBySequence.remove(header.sequence)
            ?: return QueryCorrelationEvent.Rejected(
                QueryCorrelationRejection.RESPONSE_WITHOUT_REQUEST,
            )

        if (header.source != pending.destination || header.destination != pending.source) {
            return QueryCorrelationEvent.Rejected(QueryCorrelationRejection.ROUTE_MISMATCH)
        }
        if (header.payloadLength < 1) {
            return QueryCorrelationEvent.Rejected(QueryCorrelationRejection.EMPTY_RESPONSE_BODY)
        }

        val owned = frame.copyOfRange(DUML_HEADER_BYTES, frame.size - DUML_CRC16_BYTES)
        val body = try {
            SensitiveAckPayload(owned)
        } catch (error: Throwable) {
            owned.fill(0)
            throw error
        }
        return QueryCorrelationEvent.CorrelatedAck(version, pending.kind, body)
    }

    private fun decodeRequestKind(frame: ByteArray, payloadLength: Int): QueryRequestKind? =
        when (version) {
            FlySafeWireVersion.V2 -> {
                if (payloadLength != 1) null else QueryRequestKind.Page(unsigned(frame[11]))
            }
            FlySafeWireVersion.V3, FlySafeWireVersion.V4 -> {
                if (payloadLength != 2 || unsigned(frame[11]) != 0) {
                    null
                } else {
                    val selector = unsigned(frame[12])
                    when {
                        selector == 1 -> QueryRequestKind.ModernStart
                        selector and 1 == 0 -> QueryRequestKind.Page(selector ushr 1)
                        else -> null
                    }
                }
            }
        }

    private fun expire(now: Long) {
        pendingBySequence.entries.removeAll { deadlineReached(now, it.value.expiresAtNanos) }
        ambiguousUntilBySequence.entries.removeAll { deadlineReached(now, it.value) }
    }

    @Synchronized
    override fun close() {
        pendingBySequence.clear()
        ambiguousUntilBySequence.clear()
        closed = true
    }

    private companion object {
        const val FLYSAFE_COMMAND_SET = 0x11
        const val QUERY_LICENSE = 0x11
        const val REQUEST_ACK_AFTER_EXEC_PLAINTEXT = 0x40
        const val RESPONSE_PLAINTEXT = 0x80
        const val DUML_HEADER_BYTES = 11
        const val DUML_CRC16_BYTES = 2
        const val MAX_PENDING_REQUESTS = 16
        const val REQUEST_TTL_NANOS = 6_000_000_000L

        fun unsigned(value: Byte): Int = value.toInt() and 0xff

        fun saturatingAdd(left: Long, right: Long): Long =
            if (left > Long.MAX_VALUE - right) Long.MAX_VALUE else left + right

        fun deadlineReached(now: Long, deadline: Long): Boolean = now - deadline >= 0
    }
}

internal data class DumlHeader(
    val source: Int,
    val destination: Int,
    val sequence: Int,
    val commandType: Int,
    val commandSet: Int,
    val commandId: Int,
    val payloadLength: Int,
)

/** Strict DUML-v1 validation used before any application ACK body becomes visible. */
internal object DumlFrameValidator {
    fun parse(frame: ByteArray): DumlHeader? {
        if (frame.size !in MIN_FRAME_BYTES..MAX_FRAME_BYTES || frame[0] != 0x55.toByte()) {
            return null
        }
        val declared = littleU16(frame, 1)
        if (declared and 0x03ff != frame.size || declared ushr 10 != 1) return null
        if (DumlWireCrc.crc8(frame, 0, 3) != unsigned(frame[3])) return null
        if (DumlWireCrc.crc16(frame, 0, frame.size - 2) != littleU16(frame, frame.size - 2)) {
            return null
        }
        return DumlHeader(
            source = unsigned(frame[4]),
            destination = unsigned(frame[5]),
            sequence = littleU16(frame, 6),
            commandType = unsigned(frame[8]),
            commandSet = unsigned(frame[9]),
            commandId = unsigned(frame[10]),
            payloadLength = frame.size - MIN_FRAME_BYTES,
        )
    }

    private fun littleU16(bytes: ByteArray, offset: Int): Int =
        unsigned(bytes[offset]) or (unsigned(bytes[offset + 1]) shl 8)

    private fun unsigned(value: Byte): Int = value.toInt() and 0xff

    private const val MIN_FRAME_BYTES = 13
    private const val MAX_FRAME_BYTES = 1023
}

internal object DumlWireCrc {
    fun crc8(data: ByteArray, offset: Int, length: Int): Int {
        var value = 0x77
        for (index in offset until offset + length) {
            value = value xor (data[index].toInt() and 0xff)
            repeat(8) {
                value = if (value and 1 != 0) (value ushr 1) xor 0x8c else value ushr 1
            }
        }
        return value and 0xff
    }

    fun crc16(data: ByteArray, offset: Int, length: Int): Int {
        var value = 0x3692
        for (index in offset until offset + length) {
            value = value xor (data[index].toInt() and 0xff)
            repeat(8) {
                value = if (value and 1 != 0) (value ushr 1) xor 0x8408 else value ushr 1
            }
        }
        return value and 0xffff
    }
}
