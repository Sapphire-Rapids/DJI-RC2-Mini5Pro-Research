package com.finduas.ridinventory.internal

import java.security.MessageDigest
import java.util.Arrays

internal enum class FlySafeInventoryVersion(val observedCode: Int) {
    V3(1),
    V4(2);

    companion object {
        fun fromObservedCode(code: Int): FlySafeInventoryVersion =
            entries.firstOrNull { it.observedCode == code }
                ?: throw IllegalArgumentException("only observed V3/V4 inventory sessions are accepted")
    }
}

internal data class ReadOnlyQueryAckEvidence(
    val packState: Int,
    val protocolResult: Int,
    val commandSet: Int,
    val commandId: Int,
    val sequence: Int,
    val parserBodyLength: Int,
) {
    init {
        require(sequence in 0..0xffff) { "sequence must be a uint16" }
        require(parserBodyLength >= 0) { "parser body length cannot be negative" }
    }
}

internal class SessionCorrelationCapability private constructor(
    val version: FlySafeInventoryVersion,
    private val binding: ByteArray,
) : AutoCloseable {
    private var closed = false

    fun childBinding(): ByteArray {
        check(!closed) { "session correlation capability is closed" }
        return binding.copyOf()
    }

    override fun close() {
        if (!closed) {
            Arrays.fill(binding, 0)
            closed = true
        }
    }

    override fun toString(): String = "SessionCorrelationCapability(version=$version, closed=$closed)"

    companion object {
        fun issue(
            observedVersionCode: Int,
            supportObserved: Boolean,
            alreadyRedactedSessionDigestSha256: ByteArray,
        ): SessionCorrelationCapability {
            require(supportObserved) { "FlySafe support must be observed in this session" }
            require(alreadyRedactedSessionDigestSha256.size == 32) {
                "session evidence must already be a SHA-256 digest"
            }
            val version = FlySafeInventoryVersion.fromObservedCode(observedVersionCode)
            val digest = MessageDigest.getInstance("SHA-256")
            digest.update("finduas:v34:readonly-session:v1".encodeToByteArray())
            digest.update(version.observedCode.toByte())
            digest.update(alreadyRedactedSessionDigestSha256)
            return SessionCorrelationCapability(version, digest.digest())
        }
    }
}

internal sealed class CorrelatedResponseCapability(
    val version: FlySafeInventoryVersion,
    internal val sequence: Int,
    private val sessionBinding: ByteArray,
    private val payloadBinding: ByteArray,
    private val responseCorrelationDigest: ByteArray,
) : AutoCloseable {
    private var consumed = false

    internal fun consumeAgainst(
        expectedSessionBinding: ByteArray,
        expectedPayloadBinding: ByteArray,
    ) {
        check(!consumed) { "response correlation capability was already consumed" }
        val sessionMatches = MessageDigest.isEqual(sessionBinding, expectedSessionBinding)
        val correlatedExpected = bindTransportCorrelation(
            expectedPayloadBinding,
            responseCorrelationDigest,
        )
        val payloadMatches = MessageDigest.isEqual(payloadBinding, correlatedExpected)
        Arrays.fill(correlatedExpected, 0)
        close()
        require(sessionMatches && payloadMatches) { "response correlation does not match parser input" }
    }

    override fun close() {
        if (!consumed) {
            Arrays.fill(sessionBinding, 0)
            Arrays.fill(payloadBinding, 0)
            Arrays.fill(responseCorrelationDigest, 0)
            consumed = true
        }
    }

    override fun toString(): String =
        "${this::class.simpleName}(version=$version, sequence=$sequence, consumed=$consumed)"
}

internal class GroupResponseCorrelationCapability private constructor(
    version: FlySafeInventoryVersion,
    sequence: Int,
    sessionBinding: ByteArray,
    payloadBinding: ByteArray,
    responseCorrelationDigest: ByteArray,
) : CorrelatedResponseCapability(
    version,
    sequence,
    sessionBinding,
    payloadBinding,
    responseCorrelationDigest,
) {
    companion object {
        internal fun create(
            version: FlySafeInventoryVersion,
            sequence: Int,
            sessionBinding: ByteArray,
            payloadBinding: ByteArray,
            responseCorrelationDigest: ByteArray,
        ) = GroupResponseCorrelationCapability(
            version,
            sequence,
            sessionBinding,
            payloadBinding,
            responseCorrelationDigest,
        )
    }
}

internal class RecordResponseCorrelationCapability private constructor(
    version: FlySafeInventoryVersion,
    sequence: Int,
    val recordIndex: Int,
    sessionBinding: ByteArray,
    payloadBinding: ByteArray,
    responseCorrelationDigest: ByteArray,
) : CorrelatedResponseCapability(
    version,
    sequence,
    sessionBinding,
    payloadBinding,
    responseCorrelationDigest,
) {
    companion object {
        internal fun create(
            version: FlySafeInventoryVersion,
            sequence: Int,
            recordIndex: Int,
            sessionBinding: ByteArray,
            payloadBinding: ByteArray,
            responseCorrelationDigest: ByteArray,
        ) = RecordResponseCorrelationCapability(
            version,
            sequence,
            recordIndex,
            sessionBinding,
            payloadBinding,
            responseCorrelationDigest,
        )
    }
}

internal class TerminationResponseCorrelationCapability private constructor(
    version: FlySafeInventoryVersion,
    sequence: Int,
    val nextRecordIndex: Int,
    sessionBinding: ByteArray,
    payloadBinding: ByteArray,
    responseCorrelationDigest: ByteArray,
) : CorrelatedResponseCapability(
    version,
    sequence,
    sessionBinding,
    payloadBinding,
    responseCorrelationDigest,
) {
    companion object {
        internal fun create(
            version: FlySafeInventoryVersion,
            sequence: Int,
            nextRecordIndex: Int,
            sessionBinding: ByteArray,
            payloadBinding: ByteArray,
            responseCorrelationDigest: ByteArray,
        ) = TerminationResponseCorrelationCapability(
            version,
            sequence,
            nextRecordIndex,
            sessionBinding,
            payloadBinding,
            responseCorrelationDigest,
        )
    }
}

/**
 * Boundary used by a future read-only transport after it has correlated an ACK. It cannot issue a
 * setter credential, and every capability is one-shot and bound to the exact response bytes.
 */
internal object ReadOnlyInventoryCorrelation {
    fun issueGroup(
        session: SessionCorrelationCapability,
        ack: ReadOnlyQueryAckEvidence,
        responseCorrelationDigestSha256: ByteArray,
        groupProtobuf: ByteArray,
    ): GroupResponseCorrelationCapability {
        validateDataAck(ack, groupProtobuf.size)
        validateCorrelationDigest(responseCorrelationDigestSha256)
        val sessionBinding = session.childBinding()
        var ownedSession: ByteArray? = null
        var ownedPayload: ByteArray? = null
        var ownedDigest: ByteArray? = null
        return try {
            val capabilitySession = sessionBinding.copyOf().also { ownedSession = it }
            val capabilityPayload = responseBinding(
                sessionBinding,
                ack,
                responseCorrelationDigestSha256,
                groupProtobuf,
            ).also { ownedPayload = it }
            val capabilityDigest = responseCorrelationDigestSha256.copyOf().also { ownedDigest = it }
            val result = GroupResponseCorrelationCapability.create(
                session.version,
                ack.sequence,
                capabilitySession,
                capabilityPayload,
                capabilityDigest,
            )
            ownedSession = null
            ownedPayload = null
            ownedDigest = null
            result
        } finally {
            ownedSession?.let { Arrays.fill(it, 0) }
            ownedPayload?.let { Arrays.fill(it, 0) }
            ownedDigest?.let { Arrays.fill(it, 0) }
            Arrays.fill(sessionBinding, 0)
        }
    }

    fun issueRecord(
        session: SessionCorrelationCapability,
        ack: ReadOnlyQueryAckEvidence,
        recordIndex: Int,
        responseCorrelationDigestSha256: ByteArray,
        status: ExternalLicenseStatusBits,
        licenseProtobuf: ByteArray,
    ): RecordResponseCorrelationCapability {
        require(recordIndex in 0 until ProtoLimits.MAX_LICENSES) { "record index is outside safe range" }
        validateDataAck(ack, licenseProtobuf.size + 1)
        validateCorrelationDigest(responseCorrelationDigestSha256)
        val sessionBinding = session.childBinding()
        val statusAndBody = ByteArray(licenseProtobuf.size + 1)
        statusAndBody[0] = status.rawByte()
        licenseProtobuf.copyInto(statusAndBody, destinationOffset = 1)
        var ownedSession: ByteArray? = null
        var ownedPayload: ByteArray? = null
        var ownedDigest: ByteArray? = null
        return try {
            val capabilitySession = sessionBinding.copyOf().also { ownedSession = it }
            val capabilityPayload = responseBinding(
                sessionBinding,
                ack,
                responseCorrelationDigestSha256,
                statusAndBody,
            ).also { ownedPayload = it }
            val capabilityDigest = responseCorrelationDigestSha256.copyOf().also { ownedDigest = it }
            val result = RecordResponseCorrelationCapability.create(
                session.version,
                ack.sequence,
                recordIndex,
                capabilitySession,
                capabilityPayload,
                capabilityDigest,
            )
            ownedSession = null
            ownedPayload = null
            ownedDigest = null
            result
        } finally {
            ownedSession?.let { Arrays.fill(it, 0) }
            ownedPayload?.let { Arrays.fill(it, 0) }
            ownedDigest?.let { Arrays.fill(it, 0) }
            Arrays.fill(statusAndBody, 0)
            Arrays.fill(sessionBinding, 0)
        }
    }

    fun issueTermination(
        session: SessionCorrelationCapability,
        ack: ReadOnlyQueryAckEvidence,
        nextRecordIndex: Int,
        responseCorrelationDigestSha256: ByteArray,
    ): TerminationResponseCorrelationCapability {
        require(nextRecordIndex in 0..ProtoLimits.MAX_LICENSES) { "termination index is outside safe range" }
        validateEndpoint(ack)
        require(ack.packState == 0) { "termination ACK transport state is not successful" }
        require(ack.protocolResult == 1) { "inventory terminator must have protocol result 1" }
        require(ack.parserBodyLength == 0) { "inventory terminator must have an empty parser body" }
        validateCorrelationDigest(responseCorrelationDigestSha256)
        val sessionBinding = session.childBinding()
        var ownedSession: ByteArray? = null
        var ownedPayload: ByteArray? = null
        var ownedDigest: ByteArray? = null
        return try {
            val capabilitySession = sessionBinding.copyOf().also { ownedSession = it }
            val capabilityPayload = responseBinding(
                sessionBinding,
                ack,
                responseCorrelationDigestSha256,
                ByteArray(0),
            ).also { ownedPayload = it }
            val capabilityDigest = responseCorrelationDigestSha256.copyOf().also { ownedDigest = it }
            val result = TerminationResponseCorrelationCapability.create(
                session.version,
                ack.sequence,
                nextRecordIndex,
                capabilitySession,
                capabilityPayload,
                capabilityDigest,
            )
            ownedSession = null
            ownedPayload = null
            ownedDigest = null
            result
        } finally {
            ownedSession?.let { Arrays.fill(it, 0) }
            ownedPayload?.let { Arrays.fill(it, 0) }
            ownedDigest?.let { Arrays.fill(it, 0) }
            Arrays.fill(sessionBinding, 0)
        }
    }

    internal fun expectedGroupBinding(
        sessionBinding: ByteArray,
        ackSequence: Int,
        groupProtobuf: ByteArray,
    ): ByteArray = parserSideBinding(sessionBinding, ackSequence, 0, groupProtobuf)

    internal fun expectedRecordBinding(
        sessionBinding: ByteArray,
        ackSequence: Int,
        status: ExternalLicenseStatusBits,
        licenseProtobuf: ByteArray,
    ): ByteArray {
        val combined = ByteArray(licenseProtobuf.size + 1)
        combined[0] = status.rawByte()
        licenseProtobuf.copyInto(combined, destinationOffset = 1)
        return try {
            parserSideBinding(sessionBinding, ackSequence, 0, combined)
        } finally {
            Arrays.fill(combined, 0)
        }
    }

    internal fun expectedTerminationBinding(
        sessionBinding: ByteArray,
        ackSequence: Int,
    ): ByteArray = parserSideBinding(sessionBinding, ackSequence, 1, ByteArray(0))

    private fun validateDataAck(ack: ReadOnlyQueryAckEvidence, exactBodyLength: Int) {
        validateEndpoint(ack)
        require(ack.packState == 0) { "inventory ACK transport state is not successful" }
        require(ack.protocolResult == 0) { "data ACK must have protocol result 0" }
        require(ack.parserBodyLength == exactBodyLength) { "ACK body length does not match correlated bytes" }
    }

    private fun validateEndpoint(ack: ReadOnlyQueryAckEvidence) {
        require(ack.commandSet == 0x11 && ack.commandId == 0x11) {
            "only the read-only FlySafe inventory endpoint is accepted"
        }
    }

    private fun responseBinding(
        sessionBinding: ByteArray,
        ack: ReadOnlyQueryAckEvidence,
        responseCorrelationDigestSha256: ByteArray,
        parserBody: ByteArray,
    ): ByteArray {
        val parserBinding = parserSideBinding(
            sessionBinding,
            ack.sequence,
            ack.protocolResult,
            parserBody,
        )
        return try {
            bindTransportCorrelation(parserBinding, responseCorrelationDigestSha256)
        } finally {
            Arrays.fill(parserBinding, 0)
        }
    }

    private fun validateCorrelationDigest(responseCorrelationDigestSha256: ByteArray) {
        require(responseCorrelationDigestSha256.size == 32) {
            "response correlation evidence must be a SHA-256 digest"
        }
    }

    private fun parserSideBinding(
        sessionBinding: ByteArray,
        sequence: Int,
        protocolResult: Int,
        parserBody: ByteArray,
    ): ByteArray {
        val digest = MessageDigest.getInstance("SHA-256")
        digest.update("finduas:v34:parser-input:v1".encodeToByteArray())
        digest.update(sessionBinding)
        digest.update((sequence and 0xff).toByte())
        digest.update(((sequence ushr 8) and 0xff).toByte())
        digest.update(protocolResult.toByte())
        digest.update(parserBody)
        return digest.digest()
    }
}

private fun bindTransportCorrelation(
    parserBinding: ByteArray,
    responseCorrelationDigestSha256: ByteArray,
): ByteArray {
    val digest = MessageDigest.getInstance("SHA-256")
    digest.update("finduas:v34:response-correlation:v1".encodeToByteArray())
    digest.update(parserBinding)
    digest.update(responseCorrelationDigestSha256)
    return digest.digest()
}
