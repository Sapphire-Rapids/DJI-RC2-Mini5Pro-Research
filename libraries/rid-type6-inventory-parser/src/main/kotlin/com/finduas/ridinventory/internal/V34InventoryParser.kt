package com.finduas.ridinventory.internal

import java.nio.ByteBuffer
import java.nio.charset.CodingErrorAction
import java.nio.charset.StandardCharsets
import java.security.MessageDigest
import java.util.Arrays
import java.util.IdentityHashMap

internal object V34InventoryParser {
    fun open(
        session: SessionCorrelationCapability,
        correlation: GroupResponseCorrelationCapability,
        groupProtobuf: ByteArray,
    ): V34InventoryProbe {
        if (groupProtobuf.isEmpty()) {
            correlation.close()
            throw StrictProtoException(ProtoFailure.EMPTY_INPUT, "group protobuf is empty")
        }
        if (groupProtobuf.size > ProtoLimits.MAX_GROUP_BYTES) {
            correlation.close()
            throw StrictProtoException(ProtoFailure.MESSAGE_TOO_LARGE, "group protobuf exceeds cap")
        }
        if (correlation.version != session.version) {
            correlation.close()
            throw IllegalArgumentException("group protocol version does not match session")
        }
        val sessionBinding = session.childBinding()
        val expectedBinding = ReadOnlyInventoryCorrelation.expectedGroupBinding(
            sessionBinding,
            correlation.sequence,
            groupProtobuf,
        )
        try {
            correlation.consumeAgainst(sessionBinding, expectedBinding)
            val summary = parseGroup(groupProtobuf, sessionBinding)
            return V34InventoryProbe(session.version, sessionBinding.copyOf(), summary)
        } finally {
            Arrays.fill(expectedBinding, 0)
            Arrays.fill(sessionBinding, 0)
        }
    }

    private fun parseGroup(body: ByteArray, sessionBinding: ByteArray): V34GroupSummary {
        val reader = StrictProtoReader(body, 0, body.size, ParseBudget())
        val seen = BooleanArray(6)
        var licensesCount: UInt? = null

        while (true) {
            val field = reader.nextField() ?: break
            when (field.number) {
                1 -> {
                    rejectDuplicate(seen, 1)
                    reader.readUInt32(field)
                }
                2 -> {
                    rejectDuplicate(seen, 2)
                    reader.readUInt32(field)
                }
                3 -> {
                    rejectDuplicate(seen, 3)
                    reader.readLengthDelimited(field, ProtoLimits.MAX_SN_BYTES)
                }
                4 -> {
                    rejectDuplicate(seen, 4)
                    reader.readUInt64(field)
                }
                5 -> {
                    rejectDuplicate(seen, 5)
                    licensesCount = reader.readUInt32(field)
                }
                else -> reader.skip(field)
            }
        }

        val count = licensesCount
            ?: throw StrictProtoException(ProtoFailure.MISSING_CRITICAL_FIELD, "licenses_count is absent")
        if (count > ProtoLimits.MAX_LICENSES.toUInt()) {
            throw StrictProtoException(ProtoFailure.VALUE_OUT_OF_RANGE, "licenses_count exceeds page cap")
        }

        val digest = MessageDigest.getInstance("SHA-256")
        digest.update("finduas:v34:redacted-group:v1".encodeToByteArray())
        digest.update(sessionBinding)
        digest.update(body)
        val redacted = digest.digest().take(12).joinToString("") { "%02x".format(it) }
        return V34GroupSummary(count.toInt(), "sha256:$redacted")
    }
}

internal class V34InventoryProbe internal constructor(
    val version: FlySafeInventoryVersion,
    private val sessionBinding: ByteArray,
    val group: V34GroupSummary,
) : AutoCloseable {
    private val seenIdFingerprints = HashSet<String>()
    private val issuedRidCapabilities = java.util.Collections.newSetFromMap(
        IdentityHashMap<UnverifiedRidInventoryCapability, Boolean>(),
    )
    private val nonRidCounts = linkedMapOf<NonRidLicenseKind, Int>()
    private var nextRecordIndex = 0
    private var ridCount = 0
    private var completed = false
    private var closed = false

    fun acceptRecord(
        correlation: RecordResponseCorrelationCapability,
        status: ExternalLicenseStatusBits,
        licenseProtobuf: ByteArray,
    ): InventoryRecord {
        check(!closed) { "inventory probe is closed" }
        check(!completed) { "inventory probe is already complete" }
        if (correlation.version != version) {
            correlation.close()
            throw IllegalArgumentException("record protocol version does not match probe")
        }
        if (correlation.recordIndex != nextRecordIndex) {
            correlation.close()
            throw IllegalArgumentException("record index is not the expected next page")
        }
        if (nextRecordIndex >= group.licensesCount) {
            correlation.close()
            throw IllegalArgumentException("record exceeds declared licenses_count")
        }
        if (licenseProtobuf.isEmpty()) {
            correlation.close()
            throw StrictProtoException(ProtoFailure.EMPTY_INPUT, "license protobuf is empty")
        }
        if (licenseProtobuf.size > ProtoLimits.MAX_LICENSE_BYTES) {
            correlation.close()
            throw StrictProtoException(ProtoFailure.MESSAGE_TOO_LARGE, "license protobuf exceeds cap")
        }

        val expectedBinding = ReadOnlyInventoryCorrelation.expectedRecordBinding(
            sessionBinding,
            correlation.sequence,
            status,
            licenseProtobuf,
        )
        try {
            correlation.consumeAgainst(sessionBinding, expectedBinding)
        } finally {
            Arrays.fill(expectedBinding, 0)
        }

        val parsed = parseLicense(licenseProtobuf)
        val idBytes = parsed.id.toLittleEndianBytes()
        val idFingerprint = digestId(idBytes)
        Arrays.fill(idBytes, 0)
        if (!seenIdFingerprints.add(idFingerprint)) {
            throw StrictProtoException(ProtoFailure.DUPLICATE_CRITICAL_FIELD, "duplicate license ID")
        }

        val result: InventoryRecord = when (val kind = parsed.kind) {
            is ParsedLicenseKind.Rid -> {
                val capability = UnverifiedRidInventoryCapability(parsed.id, sessionBinding.copyOf())
                issuedRidCapabilities += capability
                ridCount += 1
                RidInventoryRecord(
                    RidRecordSummary(
                        domainTypeCode = 6,
                        level = kind.level,
                        enabled = status.enabled,
                        validity = status.validity,
                        uninterpretedStatusHighBits = status.uninterpretedHighBits,
                    ),
                    capability,
                )
            }
            is ParsedLicenseKind.NonRid -> {
                nonRidCounts[kind.kind] = (nonRidCounts[kind.kind] ?: 0) + 1
                NonRidInventoryRecord(NonRidRecordSummary(kind.kind))
            }
        }
        nextRecordIndex += 1
        return result
    }

    fun finish(correlation: TerminationResponseCorrelationCapability): CompletedInventorySummary {
        check(!closed) { "inventory probe is closed" }
        check(!completed) { "inventory probe is already complete" }
        if (correlation.version != version) {
            correlation.close()
            throw IllegalArgumentException("terminator protocol version does not match probe")
        }
        if (correlation.nextRecordIndex != nextRecordIndex) {
            correlation.close()
            throw IllegalArgumentException("terminator index does not match record count")
        }
        val expectedBinding = ReadOnlyInventoryCorrelation.expectedTerminationBinding(
            sessionBinding,
            correlation.sequence,
        )
        try {
            correlation.consumeAgainst(sessionBinding, expectedBinding)
        } finally {
            Arrays.fill(expectedBinding, 0)
        }
        require(nextRecordIndex == group.licensesCount) {
            "normal terminator disagrees with licenses_count"
        }
        completed = true
        return CompletedInventorySummary(group, ridCount, nonRidCounts.toMap())
    }

    override fun close() {
        if (!closed) {
            issuedRidCapabilities.forEach { it.close() }
            issuedRidCapabilities.clear()
            seenIdFingerprints.clear()
            nonRidCounts.clear()
            Arrays.fill(sessionBinding, 0)
            closed = true
        }
    }

    override fun toString(): String =
        "V34InventoryProbe(version=$version, group=$group, records=$nextRecordIndex, closed=$closed)"

    private fun digestId(idLittleEndian: ByteArray): String {
        val digest = MessageDigest.getInstance("SHA-256")
        digest.update("finduas:v34:duplicate-id:v1".encodeToByteArray())
        digest.update(sessionBinding)
        digest.update(idLittleEndian)
        return digest.digest().joinToString("") { "%02x".format(it) }
    }
}

private sealed interface ParsedLicenseKind {
    data class Rid(val level: RidLevel) : ParsedLicenseKind
    data class NonRid(val kind: NonRidLicenseKind) : ParsedLicenseKind
}

private data class ParsedLicense(
    val id: UInt,
    val kind: ParsedLicenseKind,
)

private fun parseLicense(body: ByteArray): ParsedLicense {
    val budget = ParseBudget()
    val reader = StrictProtoReader(body, 0, body.size, budget)
    val seen = BooleanArray(8)
    var id: UInt? = null
    var kind: ParsedLicenseKind? = null

    while (true) {
        val field = reader.nextField() ?: break
        when (field.number) {
            1 -> {
                rejectDuplicate(seen, 1)
                id = reader.readUInt32(field)
            }
            2 -> {
                rejectDuplicate(seen, 2)
                validateUtf8(reader.readLengthDelimited(field, ProtoLimits.MAX_STRING_BYTES))
            }
            3 -> {
                rejectDuplicate(seen, 3)
                reader.readUInt32(field)
            }
            4 -> {
                rejectDuplicate(seen, 4)
                reader.readUInt32(field)
            }
            5 -> {
                rejectDuplicate(seen, 5)
                reader.readBoolean(field)
            }
            6 -> {
                rejectDuplicate(seen, 6)
                val data = reader.readLengthDelimited(field, ProtoLimits.MAX_LICENSE_DATA_BYTES)
                kind = parseLicenseData(data, budget, parentDepth = 0)
            }
            7 -> {
                rejectDuplicate(seen, 7)
                reader.readLengthDelimited(field, ProtoLimits.MAX_STRING_BYTES)
            }
            else -> reader.skip(field)
        }
    }

    val exactId = id
        ?: throw StrictProtoException(ProtoFailure.MISSING_CRITICAL_FIELD, "license ID is absent")
    if (exactId == 0u) {
        throw StrictProtoException(ProtoFailure.VALUE_OUT_OF_RANGE, "license ID zero is not accepted")
    }
    val exactKind = kind
        ?: throw StrictProtoException(ProtoFailure.MISSING_CRITICAL_FIELD, "license data is absent")
    return ParsedLicense(exactId, exactKind)
}

private fun parseLicenseData(
    data: ByteSlice,
    budget: ParseBudget,
    parentDepth: Int,
): ParsedLicenseKind {
    val reader = data.reader(budget, parentDepth)
    var knownOneofField: Int? = null
    var kind: ParsedLicenseKind = ParsedLicenseKind.NonRid(NonRidLicenseKind.UNKNOWN)

    while (true) {
        val field = reader.nextField() ?: break
        if (field.number in 1..8) {
            if (knownOneofField != null) {
                throw StrictProtoException(
                    ProtoFailure.ONEOF_CONFLICT,
                    "multiple current LicenseData oneof fields are present",
                )
            }
            knownOneofField = field.number
            val payload = reader.readLengthDelimited(field, ProtoLimits.MAX_LICENSE_DATA_BYTES)
            kind = when (field.number) {
                1 -> ParsedLicenseKind.NonRid(NonRidLicenseKind.AREA)
                2 -> ParsedLicenseKind.NonRid(NonRidLicenseKind.CIRCLE)
                3 -> ParsedLicenseKind.NonRid(NonRidLicenseKind.COUNTRY)
                4 -> ParsedLicenseKind.NonRid(NonRidLicenseKind.HEIGHT)
                5 -> ParsedLicenseKind.NonRid(NonRidLicenseKind.POLYGON)
                6 -> ParsedLicenseKind.NonRid(NonRidLicenseKind.POWER)
                // Field 7 is the protobuf oneof tag. The summary's domain type is separately 6.
                7 -> ParsedLicenseKind.Rid(parseRidLevel(payload, budget, parentDepth + 1))
                8 -> ParsedLicenseKind.NonRid(NonRidLicenseKind.ANTI_INTERFERENCE)
                else -> error("unreachable")
            }
        } else {
            reader.skip(field)
        }
    }
    return kind
}

private fun parseRidLevel(
    data: ByteSlice,
    budget: ParseBudget,
    parentDepth: Int,
): RidLevel {
    if (data.length > ProtoLimits.MAX_RID_BYTES) {
        throw StrictProtoException(ProtoFailure.LENGTH_LIMIT, "RID payload exceeds cap")
    }
    val reader = data.reader(budget, parentDepth)
    var level: UInt? = null
    while (true) {
        val field = reader.nextField() ?: break
        when (field.number) {
            1 -> {
                if (level != null) {
                    throw StrictProtoException(
                        ProtoFailure.DUPLICATE_CRITICAL_FIELD,
                        "RID level occurs more than once",
                    )
                }
                level = reader.readUInt32(field)
            }
            else -> reader.skip(field)
        }
    }
    return when (level ?: throw StrictProtoException(
        ProtoFailure.MISSING_CRITICAL_FIELD,
        "RID level is absent",
    )) {
        1u -> RidLevel.EUROPEAN
        2u -> RidLevel.CHINA
        else -> RidLevel.UNKNOWN
    }
}

private fun rejectDuplicate(seen: BooleanArray, fieldNumber: Int) {
    if (seen[fieldNumber]) {
        throw StrictProtoException(
            ProtoFailure.DUPLICATE_CRITICAL_FIELD,
            "known field $fieldNumber occurs more than once",
        )
    }
    seen[fieldNumber] = true
}

private fun validateUtf8(data: ByteSlice) {
    val decoder = StandardCharsets.UTF_8.newDecoder()
        .onMalformedInput(CodingErrorAction.REPORT)
        .onUnmappableCharacter(CodingErrorAction.REPORT)
    try {
        decoder.decode(ByteBuffer.wrap(data.bytes, data.offset, data.length))
    } catch (_: java.nio.charset.CharacterCodingException) {
        throw StrictProtoException(ProtoFailure.INVALID_UTF8, "description is not valid UTF-8")
    }
}

private fun UInt.toLittleEndianBytes(): ByteArray = byteArrayOf(
    (this and 0xffu).toByte(),
    ((this shr 8) and 0xffu).toByte(),
    ((this shr 16) and 0xffu).toByte(),
    ((this shr 24) and 0xffu).toByte(),
)
