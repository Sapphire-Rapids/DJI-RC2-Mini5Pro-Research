package com.finduas.research.flysafe.wire

/**
 * Immutable evidence metadata. Constructors are internal so consumers cannot use this module as a
 * generic PackType/cmdset/cmdid builder.
 */
class FixedWireOperation internal constructor(
    val packType: Int,
    val commandSet: Int,
    val commandId: Int,
    val tupleThirdByte: Int,
    val ackHasResultCodePrefix: Boolean,
) {
    override fun toString(): String =
        "FixedWireOperation(packType=$packType, commandSet=$commandSet, commandId=$commandId, " +
            "tupleThirdByte=$tupleThirdByte, ackHasResultCodePrefix=$ackHasResultCodePrefix)"
}

object FlySafeWireMetadata {
    /** PackType 0x38 -> tuple 11 11 00 01. */
    val QUERY_LICENSES: FixedWireOperation = FixedWireOperation(
        packType = 0x38,
        commandSet = 0x11,
        commandId = 0x11,
        tupleThirdByte = 0x00,
        ackHasResultCodePrefix = true,
    )

    /** PackType 0x39 -> tuple 11 12 00 01. */
    val SET_LICENSE_ENABLE: FixedWireOperation = FixedWireOperation(
        packType = 0x39,
        commandSet = 0x11,
        commandId = 0x12,
        tupleThirdByte = 0x00,
        ackHasResultCodePrefix = true,
    )
}

enum class RouteEvidenceGate {
    RUNTIME_OBSERVATION_REQUIRED,
}

/**
 * Static research metadata only. No codec method reads this object or accepts a receiver route.
 */
internal object Product139RouteResearchMetadata {
    const val PRODUCT_ID: Int = 139
    const val STATIC_CANDIDATE_PACKED_ROUTE: Int = 0x92
    val evidenceGate: RouteEvidenceGate = RouteEvidenceGate.RUNTIME_OBSERVATION_REQUIRED
    const val USED_BY_CODEC: Boolean = false
}
