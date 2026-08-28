package com.finduas.ridswitch

import java.security.MessageDigest
import java.util.Arrays

class OpaqueFingerprint private constructor(private val bytes: ByteArray) {
    override fun equals(other: Any?): Boolean =
        other is OpaqueFingerprint && MessageDigest.isEqual(bytes, other.bytes)

    override fun hashCode(): Int = Arrays.hashCode(bytes)
    override fun toString(): String = "<redacted-fingerprint>"

    companion object {
        fun sha256(value: ByteArray): OpaqueFingerprint =
            OpaqueFingerprint(MessageDigest.getInstance("SHA-256").digest(value))
    }
}

enum class FlySafeProtocolFamily { V2, V3, V4 }
enum class SessionAuthentication { AUTHENTICATED, UNAUTHENTICATED }

data class KnownFlySafeSession(
    val family: FlySafeProtocolFamily,
    val authentication: SessionAuthentication,
    val serverAttested: Boolean,
    val sessionFingerprint: OpaqueFingerprint,
    val accountFingerprint: OpaqueFingerprint,
    val aircraftFingerprint: OpaqueFingerprint,
)

sealed interface SessionInspection {
    data class Known(val session: KnownFlySafeSession) : SessionInspection
    data object Missing : SessionInspection
    data object Unsupported : SessionInspection
}

enum class InventoryOrigin {
    OFFICIAL_SIGNED_ACCOUNT_INVENTORY,
    SIDELOADED,
    UNKNOWN,
}

enum class InventorySignatureScheme {
    DJI_FLYSAFE_SIGNED_ENVELOPE,
    UNSIGNED,
    UNKNOWN,
}

data class InventoryBinding(
    val accountFingerprint: OpaqueFingerprint,
    val aircraftFingerprint: OpaqueFingerprint,
    val family: FlySafeProtocolFamily,
)

/**
 * A consumable, memory-only candidate. The controller always closes it before returning.
 * Its identifier and signed envelope are never exposed through toString, audit, or result objects.
 */
class RidUnlockInventoryCandidate private constructor(
    licenseId: ByteArray,
    signedEnvelope: ByteArray,
    val typeCode: Int,
    val origin: InventoryOrigin,
    val signatureScheme: InventorySignatureScheme,
    val binding: InventoryBinding,
    val validFromEpochSeconds: Long,
    val validUntilEpochSeconds: Long,
) : AutoCloseable {
    private val id = EphemeralBytes(licenseId)
    private val envelope = EphemeralBytes(signedEnvelope)

    val isClosed: Boolean get() = id.isClosed && envelope.isClosed

    internal fun licenseFingerprint(): OpaqueFingerprint = id.useCopy(OpaqueFingerprint::sha256)

    internal fun <T> useVerificationMaterial(block: (VerificationMaterial) -> T): T {
        return id.useCopy { idCopy ->
            envelope.useCopy { envelopeCopy ->
                VerificationMaterial(idCopy, envelopeCopy).use(block)
            }
        }
    }

    fun <T> useLicenseId(block: (ByteArray) -> T): T = id.useCopy(block)

    override fun close() {
        id.close()
        envelope.close()
    }

    override fun toString(): String =
        "RidUnlockInventoryCandidate(typeCode=$typeCode, origin=$origin, signatureScheme=$signatureScheme, sensitive=<redacted>)"

    companion object {
        fun consumeCopies(
            licenseId: ByteArray,
            signedEnvelope: ByteArray,
            typeCode: Int,
            origin: InventoryOrigin,
            signatureScheme: InventorySignatureScheme,
            binding: InventoryBinding,
            validFromEpochSeconds: Long,
            validUntilEpochSeconds: Long,
        ): RidUnlockInventoryCandidate = RidUnlockInventoryCandidate(
            licenseId = licenseId.copyOf(),
            signedEnvelope = signedEnvelope.copyOf(),
            typeCode = typeCode,
            origin = origin,
            signatureScheme = signatureScheme,
            binding = binding,
            validFromEpochSeconds = validFromEpochSeconds,
            validUntilEpochSeconds = validUntilEpochSeconds,
        )
    }
}

private class EphemeralBytes(value: ByteArray) : AutoCloseable {
    private val bytes = value.copyOf()
    private var closed = false

    val isClosed: Boolean @Synchronized get() = closed

    @Synchronized
    fun <T> useCopy(block: (ByteArray) -> T): T {
        check(!closed) { "sensitive value already closed" }
        val copy = bytes.copyOf()
        return try {
            block(copy)
        } finally {
            copy.fill(0)
        }
    }

    @Synchronized
    override fun close() {
        if (!closed) {
            bytes.fill(0)
            closed = true
        }
    }
}

class VerificationMaterial internal constructor(
    private val licenseId: ByteArray,
    private val signedEnvelope: ByteArray,
) : AutoCloseable {
    fun <T> useLicenseId(block: (ByteArray) -> T): T = block(licenseId)
    fun <T> useSignedEnvelope(block: (ByteArray) -> T): T = block(signedEnvelope)
    override fun toString(): String = "VerificationMaterial(<redacted>)"

    override fun close() {
        licenseId.fill(0)
        signedEnvelope.fill(0)
    }
}

enum class AttestationRejection {
    WRONG_TYPE,
    UNTRUSTED_ORIGIN,
    UNSUPPORTED_SIGNATURE_SCHEME,
    SESSION_BINDING_MISMATCH,
    NOT_YET_VALID,
    EXPIRED,
    EMPTY_SIGNED_ENVELOPE,
    INVALID_SIGNATURE,
    NOT_IN_AUTHORITATIVE_ACCOUNT_INVENTORY,
}

data class CryptographicVerdict(
    val signatureValid: Boolean,
    val authoritativeAccountInventoryMember: Boolean,
)

sealed interface LicenseAttestation {
    class Verified internal constructor(val license: VerifiedRidUnlockLicense) : LicenseAttestation
    data class Rejected(val reason: AttestationRejection) : LicenseAttestation
}

class VerifiedRidUnlockLicense internal constructor(
    private val candidate: RidUnlockInventoryCandidate,
    val licenseFingerprint: OpaqueFingerprint,
) {
    val typeCode: Int = RID_UNLOCK_TYPE_CODE
    fun <T> useLicenseId(block: (ByteArray) -> T): T = candidate.useLicenseId(block)
    override fun toString(): String = "VerifiedRidUnlockLicense(typeCode=$RID_UNLOCK_TYPE_CODE, sensitive=<redacted>)"
}

const val RID_UNLOCK_TYPE_CODE: Int = 6

abstract class RidUnlockProvenanceVerifier {
    fun attest(
        candidate: RidUnlockInventoryCandidate,
        session: KnownFlySafeSession,
        epochClock: EpochClock,
        context: CallContext,
        monotonicClock: MonotonicClock,
    ): LicenseAttestation {
        context.checkpoint(monotonicClock)
        if (candidate.typeCode != RID_UNLOCK_TYPE_CODE) {
            return LicenseAttestation.Rejected(AttestationRejection.WRONG_TYPE)
        }
        if (candidate.origin != InventoryOrigin.OFFICIAL_SIGNED_ACCOUNT_INVENTORY) {
            return LicenseAttestation.Rejected(AttestationRejection.UNTRUSTED_ORIGIN)
        }
        if (candidate.signatureScheme != InventorySignatureScheme.DJI_FLYSAFE_SIGNED_ENVELOPE) {
            return LicenseAttestation.Rejected(AttestationRejection.UNSUPPORTED_SIGNATURE_SCHEME)
        }
        if (
            candidate.binding.family != session.family ||
            candidate.binding.accountFingerprint != session.accountFingerprint ||
            candidate.binding.aircraftFingerprint != session.aircraftFingerprint
        ) {
            return LicenseAttestation.Rejected(AttestationRejection.SESSION_BINDING_MISMATCH)
        }

        val now = epochClock.nowEpochSeconds()
        if (now < candidate.validFromEpochSeconds) {
            return LicenseAttestation.Rejected(AttestationRejection.NOT_YET_VALID)
        }
        if (now >= candidate.validUntilEpochSeconds) {
            return LicenseAttestation.Rejected(AttestationRejection.EXPIRED)
        }

        var envelopeWasEmpty = false
        val verdict = candidate.useVerificationMaterial { material ->
            envelopeWasEmpty = material.useSignedEnvelope { it.isEmpty() }
            if (envelopeWasEmpty) {
                CryptographicVerdict(
                    signatureValid = false,
                    authoritativeAccountInventoryMember = false,
                )
            } else {
                verifyCryptographicSignatureAndInventoryProvenance(material, candidate, session, context)
            }
        }
        if (envelopeWasEmpty) {
            return LicenseAttestation.Rejected(AttestationRejection.EMPTY_SIGNED_ENVELOPE)
        }
        context.checkpoint(monotonicClock)
        if (!verdict.signatureValid) {
            return LicenseAttestation.Rejected(AttestationRejection.INVALID_SIGNATURE)
        }
        if (!verdict.authoritativeAccountInventoryMember) {
            return LicenseAttestation.Rejected(AttestationRejection.NOT_IN_AUTHORITATIVE_ACCOUNT_INVENTORY)
        }
        return LicenseAttestation.Verified(
            VerifiedRidUnlockLicense(candidate, candidate.licenseFingerprint()),
        )
    }

    /** Production integration must verify both the DJI signature and live authoritative inventory provenance. */
    protected abstract fun verifyCryptographicSignatureAndInventoryProvenance(
        material: VerificationMaterial,
        candidate: RidUnlockInventoryCandidate,
        session: KnownFlySafeSession,
        context: CallContext,
    ): CryptographicVerdict
}

enum class RidActivation { ENABLED, DISABLED }

data class RidRestorableState(
    val activation: RidActivation,
    val activeLicenseFingerprint: OpaqueFingerprint?,
    val sessionFingerprint: OpaqueFingerprint,
    val accountFingerprint: OpaqueFingerprint,
    val aircraftFingerprint: OpaqueFingerprint,
    val policyProfileFingerprint: OpaqueFingerprint,
    val inventoryGeneration: Long,
) {
    init {
        require((activation == RidActivation.ENABLED) == (activeLicenseFingerprint != null)) {
            "enabled state must have exactly one active license fingerprint"
        }
    }
}

/** revision is observation metadata; restorableState contains every field that must round-trip exactly. */
data class ExactRidUnlockSnapshot(
    val restorableState: RidRestorableState,
    val revision: Long,
) {
    init {
        require(revision >= 0L)
    }

    fun exactlyRestores(baseline: ExactRidUnlockSnapshot): Boolean =
        restorableState == baseline.restorableState && revision >= baseline.revision
}

enum class RequestedRidTransition { ENABLE, DISABLE }

data class RidSwitchRequest(
    val target: RequestedRidTransition,
    val candidate: RidUnlockInventoryCandidate,
    /** Must be a fresh, exact snapshot acquired by an independent read-only preflight. */
    val expectedBaseline: ExactRidUnlockSnapshot,
)

data class TransitionReceipt(val accepted: Boolean)
data class RestoreReceipt(val accepted: Boolean)

enum class RfEvidenceStatus { EXTERNAL_NOT_EVALUATED }
