package com.finduas.ridinventory.internal

import java.security.MessageDigest
import kotlin.test.assertContains
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertTrue
import kotlin.test.fail
import org.junit.Test

class V34InventoryParserTest {
    @Test
    fun `synthetic V4 RID protobuf is parsed with exact numbering and external status`() {
        harness(versionCode = 2, count = 1).use { h ->
            val status = ExternalLicenseStatusBits.strict(0x06)
            val protobuf = ridLicense(
                id = 0xfedcba98u,
                levelFields = concat(varintField(1, 2uL), varintField(19, 44uL)),
                description = "private-description",
                extras = concat(
                    varintField(3, 1_725_000_000uL),
                    varintField(4, 1_726_000_000uL),
                    varintField(5, 1uL),
                    bytesField(7, byteArrayOf(1, 2, 3)),
                    varintField(91, 7uL),
                ),
                dataExtras = fixed32Field(101, 0x11223344),
            )

            val record = assertIs<RidInventoryRecord>(h.accept(0, status, protobuf))
            assertEquals(6, record.summary.domainTypeCode)
            assertEquals(RidLevel.CHINA, record.summary.level)
            assertTrue(record.summary.enabled)
            assertEquals(LicenseValidity.VALID, record.summary.validity)
            assertEquals(0, record.summary.uninterpretedStatusHighBits)
            record.capability.withRawInventoryIdBytes {
                assertTrue(
                    it.contentEquals(
                        byteArrayOf(0x98.toByte(), 0xba.toByte(), 0xdc.toByte(), 0xfe.toByte()),
                    ),
                )
            }

            val completed = h.finish(1)
            assertEquals(1, completed.ridCount)
            assertTrue(completed.nonRidCounts.isEmpty())
            record.close()
        }
    }

    @Test
    fun `unknown fields at every parsed layer stay bounded and are ignored`() {
        val group = group(
            count = 1,
            extras = concat(
                varintField(90, 9uL),
                fixed64Field(91, 0x0102030405060708uL),
                bytesField(92, byteArrayOf(3, 4, 5)),
                fixed32Field(93, 0x55667788),
            ),
        )
        harness(count = 1, groupBody = group).use { h ->
            val proto = ridLicense(
                id = 77u,
                levelFields = concat(varintField(1, 1uL), bytesField(12, byteArrayOf(7))),
                extras = bytesField(88, byteArrayOf(8, 9)),
                dataExtras = varintField(89, 2uL),
            )
            val record = assertIs<RidInventoryRecord>(
                h.accept(0, ExternalLicenseStatusBits.strict(0x00), proto),
            )
            assertEquals(RidLevel.EUROPEAN, record.summary.level)
            assertFalse(record.summary.enabled)
            assertEquals(LicenseValidity.OUTSIDE_VALID_DATE, record.summary.validity)
            h.finish(1)
        }
    }

    @Test
    fun `conflicting LicenseData oneof fields are rejected`() {
        harness(count = 1).use { h ->
            val data = concat(
                bytesField(7, varintField(1, 2uL)),
                bytesField(1, byteArrayOf()),
            )
            val proto = license(4u, data)
            assertProtoFailure(ProtoFailure.ONEOF_CONFLICT) {
                h.accept(0, ExternalLicenseStatusBits.strict(0), proto)
            }
        }
    }

    @Test
    fun `duplicate license ID across records is rejected without retaining raw IDs`() {
        harness(count = 2).use { h ->
            val first = ridLicense(0x88776655u, varintField(1, 1uL))
            val second = ridLicense(0x88776655u, varintField(1, 2uL))
            h.accept(0, ExternalLicenseStatusBits.strict(0), first)
            assertProtoFailure(ProtoFailure.DUPLICATE_CRITICAL_FIELD) {
                h.accept(1, ExternalLicenseStatusBits.strict(0), second)
            }
        }
    }

    @Test
    fun `duplicate ID inside one License is rejected`() {
        harness(count = 1).use { h ->
            val proto = concat(
                varintField(1, 7uL),
                varintField(1, 8uL),
                bytesField(6, bytesField(7, varintField(1, 1uL))),
            )
            assertProtoFailure(ProtoFailure.DUPLICATE_CRITICAL_FIELD) {
                h.accept(0, ExternalLicenseStatusBits.strict(0), proto)
            }
        }
    }

    @Test
    fun `duplicate RID level is rejected`() {
        harness(count = 1).use { h ->
            val proto = ridLicense(
                7u,
                concat(varintField(1, 1uL), varintField(1, 2uL)),
            )
            assertProtoFailure(ProtoFailure.DUPLICATE_CRITICAL_FIELD) {
                h.accept(0, ExternalLicenseStatusBits.strict(0), proto)
            }
        }
    }

    @Test
    fun `overflowing varint is rejected`() {
        harness(count = 1).use { h ->
            val overflow = byteArrayOf(
                0x08,
                0x80.toByte(), 0x80.toByte(), 0x80.toByte(), 0x80.toByte(), 0x80.toByte(),
                0x80.toByte(), 0x80.toByte(), 0x80.toByte(), 0x80.toByte(), 0x02,
            )
            assertProtoFailure(ProtoFailure.VARINT_OVERFLOW) {
                h.accept(0, ExternalLicenseStatusBits.strict(0), overflow)
            }
        }
    }

    @Test
    fun `non-canonical overlong varint is rejected`() {
        harness(count = 1).use { h ->
            val overlongId = concat(
                byteArrayOf(0x08, 0x81.toByte(), 0x00),
                bytesField(6, bytesField(7, varintField(1, 1uL))),
            )
            assertProtoFailure(ProtoFailure.NON_CANONICAL_VARINT) {
                h.accept(0, ExternalLicenseStatusBits.strict(0), overlongId)
            }
        }
    }

    @Test
    fun `declared length bomb and truncation are distinct failures`() {
        harness(count = 1).use { h ->
            val lengthBomb = concat(varintField(1, 1uL), key(6, 2), varint(4_096uL))
            assertProtoFailure(ProtoFailure.LENGTH_LIMIT) {
                h.accept(0, ExternalLicenseStatusBits.strict(0), lengthBomb)
            }
        }
        harness(count = 1).use { h ->
            val truncated = concat(
                varintField(1, 1uL),
                key(6, 2),
                varint(3uL),
                byteArrayOf(0x3a, 0x00),
            )
            assertProtoFailure(ProtoFailure.TRUNCATED) {
                h.accept(0, ExternalLicenseStatusBits.strict(0), truncated)
            }
        }
    }

    @Test
    fun `license ID zero is never a RID capability`() {
        harness(count = 1).use { h ->
            val proto = ridLicense(0u, varintField(1, 1uL))
            assertProtoFailure(ProtoFailure.VALUE_OUT_OF_RANGE) {
                h.accept(0, ExternalLicenseStatusBits.strict(0), proto)
            }
        }
    }

    @Test
    fun `non-RID record exposes only classification and aggregate count`() {
        harness(count = 1).use { h ->
            val secretDescription = "geometry-owner-secret"
            val proto = license(
                id = 4_242_424u,
                data = bytesField(5, concat(varintField(1, 99uL), bytesField(2, byteArrayOf(1, 2)))),
                description = secretDescription,
            )
            val record = assertIs<NonRidInventoryRecord>(
                h.accept(0, ExternalLicenseStatusBits.strict(0x07), proto),
            )
            assertEquals(NonRidLicenseKind.POLYGON, record.summary.kind)
            assertFalse(record.toString().contains(secretDescription))
            assertFalse(record.toString().contains("4242424"))
            val completed = h.finish(1)
            assertEquals(0, completed.ridCount)
            assertEquals(1, completed.nonRidCounts[NonRidLicenseKind.POLYGON])
        }
    }

    @Test
    fun `capability zeroization and every externally printable model are redacted`() {
        val rawSn = "sensitive-aircraft-serial"
        val rawDescription = "sensitive-license-description"
        val rawUserId = 9_876_543_210uL
        val rawGroupId = 123_456uL
        val group = group(1, rawSn, rawUserId, rawGroupId)
        harness(count = 1, groupBody = group).use { h ->
            val record = assertIs<RidInventoryRecord>(
                h.accept(
                    0,
                    ExternalLicenseStatusBits.strict(0x03),
                    ridLicense(0x1234abcdu, varintField(1, 2uL), rawDescription),
                ),
            )
            val allPrintable = listOf(h.probe.group, h.probe, record, record.summary).joinToString("|")
            assertContains(h.probe.group.redactedSessionDigest, "sha256:")
            assertEquals(31, h.probe.group.redactedSessionDigest.length)
            assertFalse(allPrintable.contains(rawSn))
            assertFalse(allPrintable.contains(rawDescription))
            assertFalse(allPrintable.contains(rawUserId.toString()))
            assertFalse(allPrintable.contains(rawGroupId.toString()))
            assertFalse(allPrintable.contains("1234abcd", ignoreCase = true))

            val field = UnverifiedRidInventoryCapability::class.java
                .getDeclaredField("idLittleEndian")
                .apply { isAccessible = true }
            val before = (field.get(record.capability) as ByteArray).copyOf()
            assertTrue(before.any { it.toInt() != 0 })
            record.close()
            val after = field.get(record.capability) as ByteArray
            assertTrue(after.all { it.toInt() == 0 })
            try {
                record.capability.withRawInventoryIdBytes { it.copyOf() }
                fail("closed capability exposed an ID")
            } catch (_: IllegalStateException) {
                // expected
            }
        }
    }

    @Test
    fun `wrong wire type is rejected for known fields`() {
        harness(count = 1).use { h ->
            val proto = concat(bytesField(1, byteArrayOf()), bytesField(6, byteArrayOf()))
            assertProtoFailure(ProtoFailure.WRONG_WIRE_TYPE) {
                h.accept(0, ExternalLicenseStatusBits.strict(0), proto)
            }
        }
    }

    @Test
    fun `V2 observed code cannot be upgraded to a V3 or V4 parser`() {
        try {
            SessionCorrelationCapability.issue(0, true, digest("session"))
            fail("V2 session was accepted")
        } catch (_: IllegalArgumentException) {
            // expected
        }
        assertEquals(FlySafeInventoryVersion.V3, FlySafeInventoryVersion.fromObservedCode(1))
        assertEquals(FlySafeInventoryVersion.V4, FlySafeInventoryVersion.fromObservedCode(2))
    }

    @Test
    fun `correlation capability is one-shot and bound to exact status and body`() {
        harness(count = 1).use { h ->
            val original = ridLicense(9u, varintField(1, 1uL))
            val altered = ridLicense(10u, varintField(1, 1uL))
            val status = ExternalLicenseStatusBits.strict(0x02)
            val correlation = h.recordCorrelation(0, status, original)
            try {
                h.probe.acceptRecord(correlation, status, altered)
                fail("altered record passed correlation")
            } catch (_: IllegalArgumentException) {
                // expected
            }
            try {
                h.probe.acceptRecord(correlation, status, original)
                fail("consumed correlation was reused")
            } catch (_: IllegalStateException) {
                // expected
            }
        }
    }

    @Test
    fun `field count and licenses count caps are enforced`() {
        val tooManyFields = Array(65) { varintField(100 + it, it.toULong()) }
        val groupWithTooManyFields = concat(group(1), *tooManyFields)
        assertProtoFailure(ProtoFailure.FIELD_LIMIT) {
            harness(count = 1, groupBody = groupWithTooManyFields).close()
        }

        assertProtoFailure(ProtoFailure.VALUE_OUT_OF_RANGE) {
            harness(count = 128, groupBody = group(128)).close()
        }
    }

    @Test
    fun `normal terminator must agree with group count`() {
        harness(count = 1).use { h ->
            try {
                h.finish(0)
                fail("terminator before declared count was accepted")
            } catch (_: IllegalArgumentException) {
                // expected
            }
        }
    }

    @Test
    fun `unmapped status bits are preserved without inventing semantics`() {
        harness(count = 1).use { h ->
            val record = assertIs<RidInventoryRecord>(
                h.accept(
                    0,
                    ExternalLicenseStatusBits.strict(0xa8),
                    ridLicense(7u, varintField(1, 1uL)),
                ),
            )
            assertFalse(record.summary.enabled)
            assertEquals(LicenseValidity.OUTSIDE_VALID_DATE, record.summary.validity)
            assertEquals(0xa8, record.summary.uninterpretedStatusHighBits)
        }
    }

    @Test
    fun `scoped raw ID copy is zeroed after callback even when retained or throwing`() {
        harness(count = 1).use { h ->
            val record = assertIs<RidInventoryRecord>(
                h.accept(
                    0,
                    ExternalLicenseStatusBits.strict(0),
                    ridLicense(0x04030201u, varintField(1, 1uL)),
                ),
            )
            lateinit var retained: ByteArray
            try {
                record.capability.withRawInventoryIdBytes {
                    retained = it
                    throw IllegalStateException("test callback failure")
                }
                fail("callback exception was swallowed")
            } catch (failure: IllegalStateException) {
                assertEquals("test callback failure", failure.message)
            }
            assertTrue(retained.all { it.toInt() == 0 })
        }
    }

    @Test
    fun `invalid correlation digest fails before issuing capability and session remains usable`() {
        val session = SessionCorrelationCapability.issue(1, true, digest("digest-prevalidation"))
        try {
            val body = group(0)
            try {
                ReadOnlyInventoryCorrelation.issueGroup(
                    session,
                    dataAck(0x201, body.size),
                    byteArrayOf(1, 2, 3),
                    body,
                )
                fail("short correlation digest was accepted")
            } catch (_: IllegalArgumentException) {
                // expected
            }
            val valid = ReadOnlyInventoryCorrelation.issueGroup(
                session,
                dataAck(0x202, body.size),
                digest("valid-after-invalid"),
                body,
            )
            valid.close()
        } finally {
            session.close()
        }
    }

    private inner class Harness(
        val session: SessionCorrelationCapability,
        val probe: V34InventoryProbe,
    ) : AutoCloseable {
        private var sequence = 0x100

        fun recordCorrelation(
            index: Int,
            status: ExternalLicenseStatusBits,
            body: ByteArray,
        ): RecordResponseCorrelationCapability {
            sequence += 1
            return ReadOnlyInventoryCorrelation.issueRecord(
                session,
                dataAck(sequence, body.size + 1),
                index,
                digest("record-correlation-$sequence"),
                status,
                body,
            )
        }

        fun accept(index: Int, status: ExternalLicenseStatusBits, body: ByteArray): InventoryRecord =
            probe.acceptRecord(recordCorrelation(index, status, body), status, body)

        fun finish(nextIndex: Int): CompletedInventorySummary {
            sequence += 1
            val ack = ReadOnlyQueryAckEvidence(0, 1, 0x11, 0x11, sequence, 0)
            val correlation = ReadOnlyInventoryCorrelation.issueTermination(
                session,
                ack,
                nextIndex,
                digest("terminator-correlation-$sequence"),
            )
            return probe.finish(correlation)
        }

        override fun close() {
            probe.close()
            session.close()
        }
    }

    private fun harness(
        versionCode: Int = 1,
        count: Int,
        groupBody: ByteArray = group(count),
    ): Harness {
        val session = SessionCorrelationCapability.issue(
            versionCode,
            supportObserved = true,
            alreadyRedactedSessionDigestSha256 = digest("session-$versionCode"),
        )
        try {
            val ack = dataAck(0x100, groupBody.size)
            val correlation = ReadOnlyInventoryCorrelation.issueGroup(
                session,
                ack,
                digest("group-correlation"),
                groupBody,
            )
            val probe = V34InventoryParser.open(session, correlation, groupBody)
            return Harness(session, probe)
        } catch (failure: Throwable) {
            session.close()
            throw failure
        }
    }

    private fun dataAck(sequence: Int, bodyLength: Int) =
        ReadOnlyQueryAckEvidence(0, 0, 0x11, 0x11, sequence, bodyLength)

    private fun group(
        count: Int,
        sn: String = "group-sn-not-for-output",
        userId: ULong = 123uL,
        groupId: ULong = 456uL,
        extras: ByteArray = byteArrayOf(),
    ): ByteArray = concat(
        varintField(1, groupId),
        varintField(2, 1_725_000_000uL),
        bytesField(3, sn.encodeToByteArray()),
        varintField(4, userId),
        varintField(5, count.toULong()),
        extras,
    )

    private fun ridLicense(
        id: UInt,
        levelFields: ByteArray,
        description: String = "discard-me",
        extras: ByteArray = byteArrayOf(),
        dataExtras: ByteArray = byteArrayOf(),
    ): ByteArray {
        val data = concat(dataExtras, bytesField(7, levelFields))
        return license(id, data, description, extras)
    }

    private fun license(
        id: UInt,
        data: ByteArray,
        description: String = "discard-me",
        extras: ByteArray = byteArrayOf(),
    ): ByteArray = concat(
        varintField(1, id.toULong()),
        bytesField(2, description.encodeToByteArray()),
        bytesField(6, data),
        extras,
    )

    private fun assertProtoFailure(expected: ProtoFailure, block: () -> Unit) {
        try {
            block()
            fail("expected $expected")
        } catch (failure: StrictProtoException) {
            assertEquals(expected, failure.failure)
        }
    }

    private fun digest(value: String): ByteArray =
        MessageDigest.getInstance("SHA-256").digest(value.encodeToByteArray())

    private fun varintField(number: Int, value: ULong): ByteArray =
        concat(key(number, 0), varint(value))

    private fun bytesField(number: Int, value: ByteArray): ByteArray =
        concat(key(number, 2), varint(value.size.toULong()), value)

    private fun fixed32Field(number: Int, value: Int): ByteArray = concat(
        key(number, 5),
        byteArrayOf(
            value.toByte(),
            (value ushr 8).toByte(),
            (value ushr 16).toByte(),
            (value ushr 24).toByte(),
        ),
    )

    private fun fixed64Field(number: Int, value: ULong): ByteArray = concat(
        key(number, 1),
        ByteArray(8) { index -> (value shr (index * 8)).toByte() },
    )

    private fun key(number: Int, wireType: Int): ByteArray =
        varint(((number.toULong()) shl 3) or wireType.toULong())

    private fun varint(value: ULong): ByteArray {
        var remaining = value
        val bytes = ArrayList<Byte>(10)
        while (true) {
            if (remaining < 0x80uL) {
                bytes += remaining.toByte()
                break
            }
            bytes += ((remaining and 0x7fuL).toInt() or 0x80).toByte()
            remaining = remaining shr 7
        }
        return bytes.toByteArray()
    }

    private fun concat(vararg parts: ByteArray): ByteArray {
        val result = ByteArray(parts.sumOf { it.size })
        var offset = 0
        for (part in parts) {
            part.copyInto(result, offset)
            offset += part.size
        }
        return result
    }
}
