package com.finduas.ridswitch

interface FlySafeSessionProvider {
    fun inspect(context: CallContext): SessionInspection
}

/**
 * Deliberately narrow typed adapter. There is no raw-write, generic command, set(Boolean), socket,
 * device, or cloud implementation in this project.
 */
interface RidUnlockTransport {
    /** Must be a live, cache-bypassing read from the exact admitted session. */
    fun getExactRidUnlockState(session: KnownFlySafeSession, context: CallContext): ExactRidUnlockSnapshot

    fun requestEnableVerifiedRidUnlock(
        session: KnownFlySafeSession,
        license: VerifiedRidUnlockLicense,
        exactBaseline: ExactRidUnlockSnapshot,
        context: CallContext,
    ): TransitionReceipt

    fun requestDisableVerifiedRidUnlock(
        session: KnownFlySafeSession,
        license: VerifiedRidUnlockLicense,
        exactBaseline: ExactRidUnlockSnapshot,
        context: CallContext,
    ): TransitionReceipt

    fun restoreExactRidUnlockBaseline(
        session: KnownFlySafeSession,
        /** The same verified type-6 capability used by the admitted transition. */
        license: VerifiedRidUnlockLicense,
        exactBaseline: ExactRidUnlockSnapshot,
        context: CallContext,
    ): RestoreReceipt
}

enum class AuditPhase {
    ADMISSION,
    SESSION,
    ATTESTATION,
    BASELINE,
    TRANSITION,
    READBACK,
    RESTORE,
    FINAL_RECONCILE,
    LEASE,
    TERMINAL,
}

enum class AuditCode {
    STARTED,
    BUSY_REJECTED,
    LOCKOUT_REJECTED,
    SESSION_ACCEPTED,
    SESSION_REJECTED,
    LICENSE_ATTESTED,
    LICENSE_REJECTED,
    BASELINE_EXACT,
    BASELINE_REJECTED,
    TRANSITION_ATTEMPTED,
    TRANSITION_ACCEPTED,
    TRANSITION_FAILED,
    READBACK_EXACT,
    READBACK_FAILED,
    RESTORE_ATTEMPTED,
    RESTORE_ACCEPTED,
    RESTORE_CALL_FAILED,
    FINAL_BASELINE_EXACT,
    FINAL_BASELINE_UNCERTAIN,
    LEASE_PREPARED,
    LEASE_PREPARE_EXPIRED,
    LEASE_ABANDONED,
    LEASE_ACTIVE,
    LEASE_RESTORED,
    CANCELLED,
    DEADLINE,
    COMPLETED,
}

/** No free-form strings or identifiers are accepted by this audit schema. */
data class RedactedAuditEvent(
    val monotonicTimestampNanos: Long,
    val phase: AuditPhase,
    val code: AuditCode,
    val requestedTransition: RequestedRidTransition?,
    val protocolFamily: FlySafeProtocolFamily?,
)

fun interface RedactedAuditSink {
    fun record(event: RedactedAuditEvent)
}

internal object NullAuditSink : RedactedAuditSink {
    override fun record(event: RedactedAuditEvent) = Unit
}
