package com.finduas.research.flysafe.wire

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class PassiveQueryTransactionCorrelatorTest {
    @Test
    fun `admits one exact reverse-route same-sequence modern query ACK and consumes frames`() {
        var now = 100L
        val gate = PassiveQueryTransactionCorrelator(FlySafeWireVersion.V4) { now }
        val request = frame(0x82, 0x92, 0x1234, 0x40, 0x11, 0x11, byteArrayOf(0, 1))
        assertTrue(gate.consume(request) is QueryCorrelationEvent.RequestObserved)
        assertArrayEquals(ByteArray(request.size), request)

        now += 1
        val response = frame(0x92, 0x82, 0x1234, 0x80, 0x11, 0x11, byteArrayOf(0, 8, 7))
        val admitted = gate.consume(response) as QueryCorrelationEvent.CorrelatedAck
        assertArrayEquals(ByteArray(response.size), response)
        assertEquals(FlySafeWireVersion.V4, admitted.version)
        assertEquals(QueryRequestKind.ModernStart, admitted.requestKind)
        admitted.applicationBody.useBytes { assertArrayEquals(byteArrayOf(0, 8, 7), it) }
        assertTrue(admitted.toString().contains("body=<redacted:3 bytes>"))
        admitted.close()
        assertTrue(admitted.applicationBody.isClosed)
    }

    @Test
    fun `V2 and modern page selectors are bound to the observed request`() {
        val v2 = PassiveQueryTransactionCorrelator(FlySafeWireVersion.V2)
        val v2Request = frame(2, 3, 7, 0x40, 0x11, 0x11, byteArrayOf(0xff.toByte()))
        assertTrue(v2.consume(v2Request) is QueryCorrelationEvent.RequestObserved)
        val v2Ack = v2.consume(frame(3, 2, 7, 0x80, 0x11, 0x11, byteArrayOf(1)))
            as QueryCorrelationEvent.CorrelatedAck
        assertEquals(QueryRequestKind.Page(255), v2Ack.requestKind)
        v2Ack.close()

        val modern = PassiveQueryTransactionCorrelator(FlySafeWireVersion.V3)
        val request = frame(2, 3, 8, 0x40, 0x11, 0x11, byteArrayOf(0, 0xfe.toByte()))
        assertTrue(modern.consume(request) is QueryCorrelationEvent.RequestObserved)
        val ack = modern.consume(frame(3, 2, 8, 0x80, 0x11, 0x11, byteArrayOf(1)))
            as QueryCorrelationEvent.CorrelatedAck
        assertEquals(QueryRequestKind.Page(127), ack.requestKind)
        ack.close()
    }

    @Test
    fun `rejects corrupt frames wrong types malformed selectors and consumes all inputs`() {
        val gate = PassiveQueryTransactionCorrelator(FlySafeWireVersion.V4)
        val badCrc = frame(2, 3, 1, 0x40, 0x11, 0x11, byteArrayOf(0, 1))
            .also { it[it.lastIndex] = (it.last().toInt() xor 1).toByte() }
        assertRejected(gate, badCrc, QueryCorrelationRejection.INVALID_DUML)
        assertRejected(
            gate,
            frame(2, 3, 2, 0x60, 0x11, 0x11, byteArrayOf(0, 1)),
            QueryCorrelationRejection.UNSUPPORTED_COMMAND_TYPE,
        )
        assertRejected(
            gate,
            frame(2, 3, 3, 0x40, 0x11, 0x11, byteArrayOf(0, 3)),
            QueryCorrelationRejection.INVALID_REQUEST_SHAPE,
        )

        val unrelated = frame(2, 3, 4, 0x40, 0x03, 0x09, ByteArray(8))
        assertTrue(gate.consume(unrelated) is QueryCorrelationEvent.Unrelated)
        assertArrayEquals(ByteArray(unrelated.size), unrelated)
    }

    @Test
    fun `response requires exact sequence reverse route and nonempty application body`() {
        val gate = PassiveQueryTransactionCorrelator(FlySafeWireVersion.V3)
        assertRejected(
            gate,
            frame(3, 2, 9, 0x80, 0x11, 0x11, byteArrayOf(1)),
            QueryCorrelationRejection.RESPONSE_WITHOUT_REQUEST,
        )

        assertTrue(gate.consume(frame(2, 3, 10, 0x40, 0x11, 0x11, byteArrayOf(0, 1)))
            is QueryCorrelationEvent.RequestObserved)
        assertRejected(
            gate,
            frame(4, 2, 10, 0x80, 0x11, 0x11, byteArrayOf(1)),
            QueryCorrelationRejection.ROUTE_MISMATCH,
        )

        assertTrue(gate.consume(frame(2, 3, 11, 0x40, 0x11, 0x11, byteArrayOf(0, 1)))
            is QueryCorrelationEvent.RequestObserved)
        assertRejected(
            gate,
            frame(3, 2, 11, 0x80, 0x11, 0x11, ByteArray(0)),
            QueryCorrelationRejection.EMPTY_RESPONSE_BODY,
        )
    }

    @Test
    fun `exact retransmission stays correlatable but conflicting duplicate becomes ambiguous`() {
        val gate = PassiveQueryTransactionCorrelator(FlySafeWireVersion.V4)
        assertTrue(gate.consume(frame(2, 3, 22, 0x40, 0x11, 0x11, byteArrayOf(0, 1)))
            is QueryCorrelationEvent.RequestObserved)
        assertTrue(gate.consume(frame(2, 3, 22, 0x40, 0x11, 0x11, byteArrayOf(0, 1)))
            is QueryCorrelationEvent.ExactRequestRetransmissionObserved)
        val retriedAck = gate.consume(frame(3, 2, 22, 0x80, 0x11, 0x11, byteArrayOf(1)))
            as QueryCorrelationEvent.CorrelatedAck
        retriedAck.close()

        assertTrue(gate.consume(frame(2, 3, 24, 0x40, 0x11, 0x11, byteArrayOf(0, 1)))
            is QueryCorrelationEvent.RequestObserved)
        assertRejected(
            gate,
            frame(2, 3, 24, 0x40, 0x11, 0x11, byteArrayOf(0, 2)),
            QueryCorrelationRejection.AMBIGUOUS_SEQUENCE,
        )
        assertRejected(
            gate,
            frame(3, 2, 24, 0x80, 0x11, 0x11, byteArrayOf(1)),
            QueryCorrelationRejection.AMBIGUOUS_SEQUENCE,
        )

        assertTrue(gate.consume(frame(2, 3, 23, 0x40, 0x11, 0x11, byteArrayOf(0, 1)))
            is QueryCorrelationEvent.RequestObserved)
        val ack = gate.consume(frame(3, 2, 23, 0x80, 0x11, 0x11, byteArrayOf(1)))
            as QueryCorrelationEvent.CorrelatedAck
        ack.close()
        assertRejected(
            gate,
            frame(3, 2, 23, 0x80, 0x11, 0x11, byteArrayOf(1)),
            QueryCorrelationRejection.RESPONSE_WITHOUT_REQUEST,
        )
    }

    @Test
    fun `pending request expires at the recovered six-second timeout`() {
        var now = 1_000L
        val gate = PassiveQueryTransactionCorrelator(FlySafeWireVersion.V3) { now }
        assertTrue(gate.consume(frame(2, 3, 31, 0x40, 0x11, 0x11, byteArrayOf(0, 1)))
            is QueryCorrelationEvent.RequestObserved)
        now += 6_000_000_000L
        assertRejected(
            gate,
            frame(3, 2, 31, 0x80, 0x11, 0x11, byteArrayOf(1)),
            QueryCorrelationRejection.RESPONSE_WITHOUT_REQUEST,
        )
    }

    @Test
    fun `closed gate refuses further input but still zeroes it`() {
        val gate = PassiveQueryTransactionCorrelator(FlySafeWireVersion.V3)
        gate.close()
        val input = frame(2, 3, 1, 0x40, 0x11, 0x11, byteArrayOf(0, 1))
        assertThrows(IllegalStateException::class.java) { gate.consume(input) }
        assertArrayEquals(ByteArray(input.size), input)
    }

    private fun assertRejected(
        gate: PassiveQueryTransactionCorrelator,
        input: ByteArray,
        expected: QueryCorrelationRejection,
    ) {
        val size = input.size
        val event = gate.consume(input) as QueryCorrelationEvent.Rejected
        assertEquals(expected, event.reason)
        assertArrayEquals(ByteArray(size), input)
    }

    private fun frame(
        source: Int,
        destination: Int,
        sequence: Int,
        commandType: Int,
        commandSet: Int,
        commandId: Int,
        payload: ByteArray,
    ): ByteArray {
        val size = 13 + payload.size
        val out = ByteArray(size)
        out[0] = 0x55
        out[1] = size.toByte()
        out[2] = (((size ushr 8) and 3) or 4).toByte()
        out[3] = DumlWireCrc.crc8(out, 0, 3).toByte()
        out[4] = source.toByte()
        out[5] = destination.toByte()
        out[6] = sequence.toByte()
        out[7] = (sequence ushr 8).toByte()
        out[8] = commandType.toByte()
        out[9] = commandSet.toByte()
        out[10] = commandId.toByte()
        payload.copyInto(out, 11)
        val crc = DumlWireCrc.crc16(out, 0, size - 2)
        out[size - 2] = crc.toByte()
        out[size - 1] = (crc ushr 8).toByte()
        return out
    }
}
