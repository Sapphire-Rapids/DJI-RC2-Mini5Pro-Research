package com.finduas.ridinventory.internal

import java.util.Arrays

internal enum class RidLevel {
    EUROPEAN,
    CHINA,
    UNKNOWN,
}

internal enum class LicenseValidity {
    VALID,
    INVALID,
    OUTSIDE_VALID_DATE,
}

internal enum class NonRidLicenseKind {
    AREA,
    CIRCLE,
    COUNTRY,
    HEIGHT,
    POLYGON,
    POWER,
    ANTI_INTERFERENCE,
    UNKNOWN,
}

internal class ExternalLicenseStatusBits private constructor(
    private val raw: Int,
) {
    val enabled: Boolean get() = (raw and 0x02) != 0

    /** Bits not mapped by the recovered client parser. They are preserved, not assigned a meaning. */
    val uninterpretedHighBits: Int get() = raw and 0xf8

    val validity: LicenseValidity
        get() = when {
            (raw and 0x01) != 0 -> LicenseValidity.INVALID
            (raw and 0x04) != 0 -> LicenseValidity.VALID
            else -> LicenseValidity.OUTSIDE_VALID_DATE
        }

    internal fun rawByte(): Byte = raw.toByte()

    override fun toString(): String =
        "ExternalLicenseStatusBits(enabled=$enabled, validity=$validity, " +
            "uninterpretedHighBits=0x${uninterpretedHighBits.toString(16)})"

    companion object {
        fun strict(raw: Int): ExternalLicenseStatusBits {
            require(raw in 0..0xff) { "status must be a byte" }
            return ExternalLicenseStatusBits(raw)
        }
    }
}

internal data class V34GroupSummary(
    val licensesCount: Int,
    val redactedSessionDigest: String,
)

internal data class RidRecordSummary(
    /** Domain type code. This is 6; it is deliberately not the protobuf field number 7. */
    val domainTypeCode: Int,
    val level: RidLevel,
    val enabled: Boolean,
    val validity: LicenseValidity,
    /** Preserved status bits 3..7. No semantics are inferred from static evidence. */
    val uninterpretedStatusHighBits: Int,
)

internal data class NonRidRecordSummary(
    val kind: NonRidLicenseKind,
)

internal sealed interface InventoryRecord

internal class RidInventoryRecord internal constructor(
    val summary: RidRecordSummary,
    val capability: UnverifiedRidInventoryCapability,
) : InventoryRecord, AutoCloseable {
    override fun close() = capability.close()

    override fun toString(): String = "RidInventoryRecord(summary=$summary, capability=$capability)"
}

internal data class NonRidInventoryRecord(
    val summary: NonRidRecordSummary,
) : InventoryRecord

internal data class CompletedInventorySummary(
    val group: V34GroupSummary,
    val ridCount: Int,
    val nonRidCounts: Map<NonRidLicenseKind, Int>,
)

/**
 * An inventory-derived, unverified ID handle. It is intentionally not a controller credential.
 * The ID is never present in toString/equals/hashCode and is wiped on close.
 */
internal class UnverifiedRidInventoryCapability internal constructor(
    id: UInt,
    private val sessionBinding: ByteArray,
) : AutoCloseable {
    private val idLittleEndian = byteArrayOf(
        (id and 0xffu).toByte(),
        ((id shr 8) and 0xffu).toByte(),
        ((id shr 16) and 0xffu).toByte(),
        ((id shr 24) and 0xffu).toByte(),
    )
    private var closed = false

    /**
     * Internal bridge only; it does not attest signature, account ownership, or applicability.
     * The callback receives a scoped little-endian copy which is wiped even if the callback throws.
     */
    fun <T> withRawInventoryIdBytes(block: (ByteArray) -> T): T {
        check(!closed) { "RID inventory capability is closed" }
        val scopedCopy = idLittleEndian.copyOf()
        return try {
            block(scopedCopy)
        } finally {
            Arrays.fill(scopedCopy, 0)
        }
    }

    override fun close() {
        if (!closed) {
            Arrays.fill(idLittleEndian, 0)
            Arrays.fill(sessionBinding, 0)
            closed = true
        }
    }

    override fun toString(): String = "UnverifiedRidInventoryCapability(closed=$closed)"
}
