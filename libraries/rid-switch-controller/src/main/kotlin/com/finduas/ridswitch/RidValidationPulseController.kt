package com.finduas.ridswitch

import java.util.concurrent.atomic.AtomicBoolean

data class RidValidationPulseConfig(
    val overallTimeoutNanos: Long = 10_000_000_000L,
    val cleanupTimeoutNanos: Long = 5_000_000_000L,
) {
    init {
        require(overallTimeoutNanos in 1L..MAX_OVERALL_TIMEOUT_NANOS)
        require(cleanupTimeoutNanos in 1L..MAX_CLEANUP_TIMEOUT_NANOS)
    }

    companion object {
        const val MAX_OVERALL_TIMEOUT_NANOS: Long = 30_000_000_000L
        const val MAX_CLEANUP_TIMEOUT_NANOS: Long = 10_000_000_000L
    }
}

enum class RidValidationPulseStatus {
    VERIFIED_TRANSITION_AND_RESTORED,
    REJECTED_WITHOUT_MUTATION,
    CANCELLED_WITHOUT_MUTATION,
    DEADLINE_WITHOUT_MUTATION,
    FAILURE_AND_RESTORED,
    CANCELLED_AND_RESTORED,
    DEADLINE_AND_RESTORED,
    LOCKED_OUT_UNCERTAIN_RESTORE,
}

enum class RidSwitchFailure {
    BUSY,
    LOCKED_OUT,
    SESSION_MISSING,
    SESSION_UNSUPPORTED,
    SESSION_UNAUTHENTICATED,
    SESSION_NOT_SERVER_ATTESTED,
    SESSION_READ_FAILED,
    LICENSE_ATTESTATION_REJECTED,
    LICENSE_ATTESTATION_FAILED,
    BASELINE_READ_FAILED,
    BASELINE_MISMATCH,
    REQUEST_IS_NOT_A_TRANSITION,
    ACTIVE_LICENSE_MISMATCH,
    TRANSITION_REJECTED,
    TRANSITION_CALL_FAILED,
    TARGET_READBACK_FAILED,
    TARGET_READBACK_MISMATCH,
    CANCELLED,
    DEADLINE,
    RESTORE_UNCERTAIN,
}

enum class RestorationStatus {
    NOT_REQUIRED_NO_MUTATION,
    EXACT_BASELINE_CONFIRMED,
    UNCERTAIN_LOCKED_OUT,
}

data class RidValidationPulseResult(
    val status: RidValidationPulseStatus,
    val primaryFailure: RidSwitchFailure?,
    val restoration: RestorationStatus,
    val requestedTransitionObservedByExactGet: Boolean,
    val safetyLockout: Boolean,
    val rfEvidence: RfEvidenceStatus = RfEvidenceStatus.EXTERNAL_NOT_EVALUATED,
)

class RidValidationPulseController(
    private val sessionProvider: FlySafeSessionProvider,
    private val verifier: RidUnlockProvenanceVerifier,
    private val transport: RidUnlockTransport,
    private val monotonicClock: MonotonicClock = SystemMonotonicClock,
    private val epochClock: EpochClock = SystemEpochClock,
    private val audit: RedactedAuditSink = NullAuditSink,
    private val config: RidValidationPulseConfig = RidValidationPulseConfig(),
) {
    private val callRunner: BoundedCallRunner = JvmBoundedCallRunner(monotonicClock)
    private val inFlight = AtomicBoolean(false)
    private val uncertainRestoreLockout = AtomicBoolean(false)

    val isLockedOut: Boolean get() = uncertainRestoreLockout.get()

    fun executeValidationPulse(
        request: RidSwitchRequest,
        cancellation: CancellationToken = NeverCancelled,
    ): RidValidationPulseResult {
        if (!inFlight.compareAndSet(false, true)) {
            request.candidate.close()
            emit(AuditPhase.ADMISSION, AuditCode.BUSY_REJECTED, request.target, null)
            return noMutationResult(RidSwitchFailure.BUSY)
        }

        var reinterruptCaller = false
        return try {
            if (uncertainRestoreLockout.get()) {
                emit(AuditPhase.ADMISSION, AuditCode.LOCKOUT_REJECTED, request.target, null)
                return noMutationResult(RidSwitchFailure.LOCKED_OUT)
            }
            emit(AuditPhase.ADMISSION, AuditCode.STARTED, request.target, null)
            val overallDeadline = Deadline.after(monotonicClock, config.overallTimeoutNanos)
            val context = CallContext(overallDeadline, cancellation, cleanup = false)
            executeAdmitted(request, context) { reinterruptCaller = true }
        } finally {
            request.candidate.close()
            inFlight.set(false)
            if (reinterruptCaller) Thread.currentThread().interrupt()
        }
    }

    private fun executeAdmitted(
        request: RidSwitchRequest,
        context: CallContext,
        markInterrupted: () -> Unit,
    ): RidValidationPulseResult {
        var stage = Stage.SESSION
        var session: KnownFlySafeSession? = null
        var verifiedLicense: VerifiedRidUnlockLicense? = null
        var baseline: ExactRidUnlockSnapshot? = null
        var mutationAttempted = false
        var targetObserved = false
        var forceLockout = false
        var primary = Primary.failure(RidSwitchFailure.SESSION_READ_FAILED)

        try {
            context.checkpoint(monotonicClock)
            val inspection = callRunner.run(context) { sessionProvider.inspect(context) }
            session = when (inspection) {
                is SessionInspection.Known -> inspection.session
                SessionInspection.Missing -> throw ControlledFailure(RidSwitchFailure.SESSION_MISSING)
                SessionInspection.Unsupported -> throw ControlledFailure(RidSwitchFailure.SESSION_UNSUPPORTED)
            }
            if (session.authentication != SessionAuthentication.AUTHENTICATED) {
                throw ControlledFailure(RidSwitchFailure.SESSION_UNAUTHENTICATED)
            }
            if (!session.serverAttested) {
                throw ControlledFailure(RidSwitchFailure.SESSION_NOT_SERVER_ATTESTED)
            }
            emit(AuditPhase.SESSION, AuditCode.SESSION_ACCEPTED, request.target, session.family)

            stage = Stage.ATTESTATION
            val attestation = callRunner.run(context) {
                verifier.attest(request.candidate, session, epochClock, context, monotonicClock)
            }
            val verified = when (attestation) {
                is LicenseAttestation.Verified -> attestation.license
                is LicenseAttestation.Rejected -> throw ControlledFailure(
                    RidSwitchFailure.LICENSE_ATTESTATION_REJECTED,
                )
            }
            verifiedLicense = verified
            emit(AuditPhase.ATTESTATION, AuditCode.LICENSE_ATTESTED, request.target, session.family)

            stage = Stage.BASELINE
            baseline = callRunner.run(context) { transport.getExactRidUnlockState(session, context) }
            if (baseline != request.expectedBaseline) {
                throw ControlledFailure(RidSwitchFailure.BASELINE_MISMATCH)
            }
            validateAdmittedBaseline(request.target, baseline, session, verified)?.let {
                throw ControlledFailure(it)
            }
            emit(AuditPhase.BASELINE, AuditCode.BASELINE_EXACT, request.target, session.family)

            context.checkpoint(monotonicClock)
            stage = Stage.TRANSITION
            mutationAttempted = true
            emit(AuditPhase.TRANSITION, AuditCode.TRANSITION_ATTEMPTED, request.target, session.family)
            val receipt = when (request.target) {
                RequestedRidTransition.ENABLE -> callRunner.run(context) {
                    transport.requestEnableVerifiedRidUnlock(session, verified, baseline, context)
                }
                RequestedRidTransition.DISABLE -> callRunner.run(context) {
                    transport.requestDisableVerifiedRidUnlock(session, verified, baseline, context)
                }
            }
            if (!receipt.accepted) throw ControlledFailure(RidSwitchFailure.TRANSITION_REJECTED)
            emit(AuditPhase.TRANSITION, AuditCode.TRANSITION_ACCEPTED, request.target, session.family)

            context.checkpoint(monotonicClock)
            stage = Stage.READBACK
            val targetSnapshot = callRunner.run(context) {
                transport.getExactRidUnlockState(session, context)
            }
            context.checkpoint(monotonicClock)
            if (!exactTargetMatches(request.target, verified, baseline, targetSnapshot)) {
                throw ControlledFailure(RidSwitchFailure.TARGET_READBACK_MISMATCH)
            }
            targetObserved = true
            primary = Primary.success()
            emit(AuditPhase.READBACK, AuditCode.READBACK_EXACT, request.target, session.family)
        } catch (_: TransactionCancelledException) {
            primary = Primary.cancelled()
            emit(AuditPhase.TERMINAL, AuditCode.CANCELLED, request.target, session?.family)
        } catch (_: CallerInterruptedException) {
            markInterrupted()
            primary = Primary.cancelled()
            if (mutationAttempted) forceLockout = true
            emit(AuditPhase.TERMINAL, AuditCode.CANCELLED, request.target, session?.family)
        } catch (_: DeadlineExceededException) {
            primary = Primary.deadline()
            emit(AuditPhase.TERMINAL, AuditCode.DEADLINE, request.target, session?.family)
        } catch (_: BoundedCallTimeoutException) {
            primary = Primary.deadline()
            // A timed-out mutating call may still finish after cancellation; exact safety is unknowable.
            if (mutationAttempted) forceLockout = true
            emit(AuditPhase.TERMINAL, AuditCode.DEADLINE, request.target, session?.family)
        } catch (failure: ControlledFailure) {
            primary = Primary.failure(failure.code)
            emitFailure(stage, request.target, session?.family)
        } catch (_: Throwable) {
            primary = Primary.failure(failureForUnexpected(stage))
            emitFailure(stage, request.target, session?.family)
        }

        if (!mutationAttempted || session == null || verifiedLicense == null || baseline == null) {
            return resultWithoutMutation(primary)
        }

        val cleanup = cleanupToExactBaseline(
            request = request,
            session = session,
            license = verifiedLicense,
            baseline = baseline,
            forceLockout = forceLockout,
        )
        if (cleanup != RestorationStatus.EXACT_BASELINE_CONFIRMED) {
            uncertainRestoreLockout.set(true)
            return RidValidationPulseResult(
                status = RidValidationPulseStatus.LOCKED_OUT_UNCERTAIN_RESTORE,
                primaryFailure = primary.failure,
                restoration = RestorationStatus.UNCERTAIN_LOCKED_OUT,
                requestedTransitionObservedByExactGet = targetObserved,
                safetyLockout = true,
            )
        }

        emit(AuditPhase.TERMINAL, AuditCode.COMPLETED, request.target, session.family)
        return resultAfterRestoration(primary, targetObserved)
    }

    private fun cleanupToExactBaseline(
        request: RidSwitchRequest,
        session: KnownFlySafeSession,
        license: VerifiedRidUnlockLicense,
        baseline: ExactRidUnlockSnapshot,
        forceLockout: Boolean,
    ): RestorationStatus {
        val cleanupDeadline = Deadline.after(monotonicClock, config.cleanupTimeoutNanos)
        val cleanupContext = CallContext(cleanupDeadline, NeverCancelled, cleanup = true)
        var timedOutOrInterrupted = forceLockout

        emit(AuditPhase.RESTORE, AuditCode.RESTORE_ATTEMPTED, request.target, session.family)
        try {
            val receipt = callRunner.run(cleanupContext) {
                transport.restoreExactRidUnlockBaseline(session, license, baseline, cleanupContext)
            }
            emit(
                AuditPhase.RESTORE,
                if (receipt.accepted) AuditCode.RESTORE_ACCEPTED else AuditCode.RESTORE_CALL_FAILED,
                request.target,
                session.family,
            )
        } catch (_: BoundedCallTimeoutException) {
            timedOutOrInterrupted = true
            emit(AuditPhase.RESTORE, AuditCode.RESTORE_CALL_FAILED, request.target, session.family)
        } catch (_: CallerInterruptedException) {
            timedOutOrInterrupted = true
            emit(AuditPhase.RESTORE, AuditCode.RESTORE_CALL_FAILED, request.target, session.family)
        } catch (_: Throwable) {
            emit(AuditPhase.RESTORE, AuditCode.RESTORE_CALL_FAILED, request.target, session.family)
        }

        val exact = try {
            val finalSnapshot = callRunner.run(cleanupContext) {
                transport.getExactRidUnlockState(session, cleanupContext)
            }
            finalSnapshot.exactlyRestores(baseline)
        } catch (_: BoundedCallTimeoutException) {
            timedOutOrInterrupted = true
            false
        } catch (_: CallerInterruptedException) {
            timedOutOrInterrupted = true
            false
        } catch (_: Throwable) {
            false
        }

        return if (exact && !timedOutOrInterrupted) {
            emit(AuditPhase.FINAL_RECONCILE, AuditCode.FINAL_BASELINE_EXACT, request.target, session.family)
            RestorationStatus.EXACT_BASELINE_CONFIRMED
        } else {
            emit(AuditPhase.FINAL_RECONCILE, AuditCode.FINAL_BASELINE_UNCERTAIN, request.target, session.family)
            RestorationStatus.UNCERTAIN_LOCKED_OUT
        }
    }

    private fun resultWithoutMutation(primary: Primary): RidValidationPulseResult {
        val status = when (primary.kind) {
            PrimaryKind.CANCELLED -> RidValidationPulseStatus.CANCELLED_WITHOUT_MUTATION
            PrimaryKind.DEADLINE -> RidValidationPulseStatus.DEADLINE_WITHOUT_MUTATION
            else -> RidValidationPulseStatus.REJECTED_WITHOUT_MUTATION
        }
        return RidValidationPulseResult(
            status = status,
            primaryFailure = primary.failure,
            restoration = RestorationStatus.NOT_REQUIRED_NO_MUTATION,
            requestedTransitionObservedByExactGet = false,
            safetyLockout = false,
        )
    }

    private fun resultAfterRestoration(primary: Primary, targetObserved: Boolean): RidValidationPulseResult {
        val status = when (primary.kind) {
            PrimaryKind.SUCCESS -> RidValidationPulseStatus.VERIFIED_TRANSITION_AND_RESTORED
            PrimaryKind.CANCELLED -> RidValidationPulseStatus.CANCELLED_AND_RESTORED
            PrimaryKind.DEADLINE -> RidValidationPulseStatus.DEADLINE_AND_RESTORED
            PrimaryKind.FAILURE -> RidValidationPulseStatus.FAILURE_AND_RESTORED
        }
        return RidValidationPulseResult(
            status = status,
            primaryFailure = primary.failure,
            restoration = RestorationStatus.EXACT_BASELINE_CONFIRMED,
            requestedTransitionObservedByExactGet = targetObserved,
            safetyLockout = false,
        )
    }

    private fun noMutationResult(failure: RidSwitchFailure): RidValidationPulseResult = RidValidationPulseResult(
        status = RidValidationPulseStatus.REJECTED_WITHOUT_MUTATION,
        primaryFailure = failure,
        restoration = RestorationStatus.NOT_REQUIRED_NO_MUTATION,
        requestedTransitionObservedByExactGet = false,
        safetyLockout = uncertainRestoreLockout.get(),
    )

    private fun failureForUnexpected(stage: Stage): RidSwitchFailure = when (stage) {
        Stage.SESSION -> RidSwitchFailure.SESSION_READ_FAILED
        Stage.ATTESTATION -> RidSwitchFailure.LICENSE_ATTESTATION_FAILED
        Stage.BASELINE -> RidSwitchFailure.BASELINE_READ_FAILED
        Stage.TRANSITION -> RidSwitchFailure.TRANSITION_CALL_FAILED
        Stage.READBACK -> RidSwitchFailure.TARGET_READBACK_FAILED
    }

    private fun emitFailure(stage: Stage, target: RequestedRidTransition, family: FlySafeProtocolFamily?) {
        val phase = when (stage) {
            Stage.SESSION -> AuditPhase.SESSION
            Stage.ATTESTATION -> AuditPhase.ATTESTATION
            Stage.BASELINE -> AuditPhase.BASELINE
            Stage.TRANSITION -> AuditPhase.TRANSITION
            Stage.READBACK -> AuditPhase.READBACK
        }
        val code = when (stage) {
            Stage.SESSION -> AuditCode.SESSION_REJECTED
            Stage.ATTESTATION -> AuditCode.LICENSE_REJECTED
            Stage.BASELINE -> AuditCode.BASELINE_REJECTED
            Stage.TRANSITION -> AuditCode.TRANSITION_FAILED
            Stage.READBACK -> AuditCode.READBACK_FAILED
        }
        emit(phase, code, target, family)
    }

    private fun emit(
        phase: AuditPhase,
        code: AuditCode,
        target: RequestedRidTransition?,
        family: FlySafeProtocolFamily?,
    ) {
        try {
            audit.record(
                RedactedAuditEvent(
                    monotonicTimestampNanos = monotonicClock.nowNanos(),
                    phase = phase,
                    code = code,
                    requestedTransition = target,
                    protocolFamily = family,
                ),
            )
        } catch (_: Throwable) {
            // Audit failure must never prevent restoration.
        }
    }

    private enum class Stage { SESSION, ATTESTATION, BASELINE, TRANSITION, READBACK }
    private enum class PrimaryKind { SUCCESS, FAILURE, CANCELLED, DEADLINE }
    private data class Primary(val kind: PrimaryKind, val failure: RidSwitchFailure?) {
        companion object {
            fun success() = Primary(PrimaryKind.SUCCESS, null)
            fun failure(code: RidSwitchFailure) = Primary(PrimaryKind.FAILURE, code)
            fun cancelled() = Primary(PrimaryKind.CANCELLED, RidSwitchFailure.CANCELLED)
            fun deadline() = Primary(PrimaryKind.DEADLINE, RidSwitchFailure.DEADLINE)
        }
    }

    private class ControlledFailure(val code: RidSwitchFailure) : RuntimeException(code.name)
}
