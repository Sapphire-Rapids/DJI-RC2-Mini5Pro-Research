package com.finduas.ridswitch

import java.util.concurrent.CompletableFuture
import java.util.concurrent.Executors
import java.util.concurrent.ScheduledExecutorService
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference

sealed interface RidBoundedLeasePolicy {
    data object Disabled : RidBoundedLeasePolicy

    class ExplicitResearchEnable private constructor(
        val maxLeaseNanos: Long,
        val prepareTtlNanos: Long,
        val prepareTimeoutNanos: Long,
        val commitTimeoutNanos: Long,
        val cleanupTimeoutNanos: Long,
    ) : RidBoundedLeasePolicy {
        companion object {
            const val HARD_MAX_LEASE_NANOS: Long = 120_000_000_000L
            const val HARD_MAX_PREPARE_TTL_NANOS: Long = 10_000_000_000L

            fun explicitlyEnableForResearch(
                maxLeaseNanos: Long = 30_000_000_000L,
                prepareTtlNanos: Long = 3_000_000_000L,
                prepareTimeoutNanos: Long = 10_000_000_000L,
                commitTimeoutNanos: Long = 10_000_000_000L,
                cleanupTimeoutNanos: Long = 5_000_000_000L,
            ): ExplicitResearchEnable {
                require(maxLeaseNanos in 1L..HARD_MAX_LEASE_NANOS)
                require(prepareTtlNanos in 1L..HARD_MAX_PREPARE_TTL_NANOS)
                require(prepareTimeoutNanos in 1L..RidValidationPulseConfig.MAX_OVERALL_TIMEOUT_NANOS)
                require(commitTimeoutNanos in 1L..RidValidationPulseConfig.MAX_OVERALL_TIMEOUT_NANOS)
                require(cleanupTimeoutNanos in 1L..RidValidationPulseConfig.MAX_CLEANUP_TIMEOUT_NANOS)
                return ExplicitResearchEnable(
                    maxLeaseNanos,
                    prepareTtlNanos,
                    prepareTimeoutNanos,
                    commitTimeoutNanos,
                    cleanupTimeoutNanos,
                )
            }
        }
    }
}

internal fun interface LeaseScheduleHandle {
    fun cancel(): Boolean
}

internal fun interface LeaseScheduler {
    fun schedule(delayNanos: Long, action: () -> Unit): LeaseScheduleHandle
}

internal object JvmLeaseScheduler : LeaseScheduler {
    private val executor: ScheduledExecutorService = Executors.newSingleThreadScheduledExecutor { runnable ->
        Thread(runnable, "rid-bounded-lease-watchdog").apply { isDaemon = true }
    }

    override fun schedule(delayNanos: Long, action: () -> Unit): LeaseScheduleHandle {
        require(delayNanos >= 0L)
        val future = executor.schedule(action, delayNanos, TimeUnit.NANOSECONDS)
        return LeaseScheduleHandle { future.cancel(false) }
    }
}

enum class RidLeaseFailure {
    FEATURE_DISABLED,
    CONTROLLER_BUSY,
    CONTROLLER_LOCKED_OUT,
    PREPARE_EXPIRED,
    PREPARED_CAPABILITY_ALREADY_CONSUMED,
    INVALID_LEASE_DURATION,
    SESSION_MISSING,
    SESSION_UNSUPPORTED,
    SESSION_UNAUTHENTICATED,
    SESSION_NOT_SERVER_ATTESTED,
    SESSION_CHANGED_BEFORE_COMMIT,
    SESSION_READ_FAILED,
    LICENSE_ATTESTATION_REJECTED,
    LICENSE_ATTESTATION_FAILED,
    LICENSE_EXPIRED_BEFORE_COMMIT,
    BASELINE_READ_FAILED,
    BASELINE_MISMATCH,
    BASELINE_CHANGED_BEFORE_COMMIT,
    REQUEST_IS_NOT_A_TRANSITION,
    ACTIVE_LICENSE_MISMATCH,
    TRANSITION_REJECTED,
    TRANSITION_CALL_FAILED,
    TARGET_READBACK_FAILED,
    TARGET_READBACK_MISMATCH,
    WATCHDOG_SCHEDULE_FAILED,
    LEASE_EXPIRED_BEFORE_RETURN,
    CANCELLED,
    DEADLINE,
    RESTORE_UNCERTAIN,
}

sealed interface RidLeasePreparationResult {
    class Prepared internal constructor(val capability: PreparedRidLease) : RidLeasePreparationResult {
        override fun toString(): String = "Prepared(<redacted-capability>)"
    }

    data class Rejected(
        val failure: RidLeaseFailure,
        val safetyLockout: Boolean,
    ) : RidLeasePreparationResult
}

sealed interface RidLeaseCommitResult {
    class Active internal constructor(val lease: ActiveRidLease) : RidLeaseCommitResult {
        override fun toString(): String = "Active(<redacted-lease>)"
    }

    data class Rejected(
        val failure: RidLeaseFailure,
        val restoration: RestorationStatus,
        val requestedTransitionObservedByExactGet: Boolean,
        val safetyLockout: Boolean,
    ) : RidLeaseCommitResult
}

enum class RidLeaseLifecycle { ACTIVE, RESTORING, RESTORED, UNCERTAIN_LOCKED_OUT }

data class RidLeaseCloseResult(
    val restoration: RestorationStatus,
    val safetyLockout: Boolean,
)

class PreparedRidLease internal constructor(
    private val controller: RidBoundedLeaseController,
    internal val request: RidSwitchRequest,
    internal val session: KnownFlySafeSession,
    internal val preparedLicense: VerifiedRidUnlockLicense,
    internal val baseline: ExactRidUnlockSnapshot,
    internal val expiresAtNanos: Long,
) : AutoCloseable {
    private val consumed = AtomicBoolean(false)
    private val expiryHandle = AtomicReference<LeaseScheduleHandle?>()

    fun commitBounded(
        leaseDurationNanos: Long,
        cancellation: CancellationToken = CancellationSource(),
    ): RidLeaseCommitResult = controller.commitPrepared(this, leaseDurationNanos, cancellation)

    fun abandon(): Boolean = controller.abandonPrepared(this, expired = false)
    override fun close() {
        abandon()
    }

    internal fun consumeOnce(): Boolean = consumed.compareAndSet(false, true)
    internal fun isConsumed(): Boolean = consumed.get()
    internal fun installExpiry(handle: LeaseScheduleHandle) {
        if (!expiryHandle.compareAndSet(null, handle)) handle.cancel()
        if (isConsumed()) expiryHandle.getAndSet(null)?.cancel()
    }
    internal fun cancelExpiry() {
        expiryHandle.getAndSet(null)?.cancel()
    }

    override fun toString(): String = "PreparedRidLease(<redacted-capability>)"
}

class ActiveRidLease internal constructor(
    private val controller: RidBoundedLeaseController,
    internal val request: RidSwitchRequest,
    internal val session: KnownFlySafeSession,
    internal val license: VerifiedRidUnlockLicense,
    internal val baseline: ExactRidUnlockSnapshot,
    val expiresAtNanos: Long,
) : AutoCloseable {
    private val lifecycle = AtomicReference(RidLeaseLifecycle.ACTIVE)
    private val closeResult = CompletableFuture<RidLeaseCloseResult>()
    private val watchdogHandle = AtomicReference<LeaseScheduleHandle?>()

    val status: RidLeaseLifecycle get() = lifecycle.get()
    val rfEvidence: RfEvidenceStatus = RfEvidenceStatus.EXTERNAL_NOT_EVALUATED

    fun closeAndReconcile(): RidLeaseCloseResult {
        if (lifecycle.compareAndSet(RidLeaseLifecycle.ACTIVE, RidLeaseLifecycle.RESTORING)) {
            watchdogHandle.getAndSet(null)?.cancel()
            val result = controller.restoreActiveLease(this)
            lifecycle.set(
                if (result.restoration == RestorationStatus.EXACT_BASELINE_CONFIRMED) {
                    RidLeaseLifecycle.RESTORED
                } else {
                    RidLeaseLifecycle.UNCERTAIN_LOCKED_OUT
                },
            )
            closeResult.complete(result)
        }
        return closeResult.join()
    }

    override fun close() {
        closeAndReconcile()
    }

    internal fun installWatchdog(handle: LeaseScheduleHandle) {
        if (!watchdogHandle.compareAndSet(null, handle)) handle.cancel()
        if (lifecycle.get() != RidLeaseLifecycle.ACTIVE) watchdogHandle.getAndSet(null)?.cancel()
    }

    override fun toString(): String =
        "ActiveRidLease(status=$status, expiresAtNanos=$expiresAtNanos, sensitive=<redacted>)"
}

class RidBoundedLeaseController private constructor(
    private val sessionProvider: FlySafeSessionProvider,
    private val verifier: RidUnlockProvenanceVerifier,
    private val transport: RidUnlockTransport,
    private val monotonicClock: MonotonicClock = SystemMonotonicClock,
    private val epochClock: EpochClock = SystemEpochClock,
    private val audit: RedactedAuditSink = NullAuditSink,
    private val policy: RidBoundedLeasePolicy = RidBoundedLeasePolicy.Disabled,
    private val scheduler: LeaseScheduler = JvmLeaseScheduler,
) {
    constructor(
        sessionProvider: FlySafeSessionProvider,
        verifier: RidUnlockProvenanceVerifier,
        transport: RidUnlockTransport,
        monotonicClock: MonotonicClock = SystemMonotonicClock,
        epochClock: EpochClock = SystemEpochClock,
        audit: RedactedAuditSink = NullAuditSink,
        policy: RidBoundedLeasePolicy = RidBoundedLeasePolicy.Disabled,
    ) : this(
        sessionProvider,
        verifier,
        transport,
        monotonicClock,
        epochClock,
        audit,
        policy,
        JvmLeaseScheduler,
    )

    /** Module-internal constructor exists only for deterministic scheduler tests. */
    internal constructor(
        sessionProvider: FlySafeSessionProvider,
        verifier: RidUnlockProvenanceVerifier,
        transport: RidUnlockTransport,
        monotonicClock: MonotonicClock,
        epochClock: EpochClock,
        audit: RedactedAuditSink,
        policy: RidBoundedLeasePolicy,
        scheduler: LeaseScheduler,
        testingMarker: Unit,
    ) : this(
        sessionProvider,
        verifier,
        transport,
        monotonicClock,
        epochClock,
        audit,
        policy,
        scheduler,
    )

    private val callRunner: BoundedCallRunner = JvmBoundedCallRunner(monotonicClock)
    private val stateLock = Any()
    private var state = ControllerState.IDLE
    private var owner: Any? = null

    val isLockedOut: Boolean get() = synchronized(stateLock) { state == ControllerState.LOCKED }
    val isOccupied: Boolean get() = synchronized(stateLock) { state != ControllerState.IDLE }

    fun prepareBoundedLease(
        request: RidSwitchRequest,
        cancellation: CancellationToken = CancellationSource(),
    ): RidLeasePreparationResult {
        val enabled = policy as? RidBoundedLeasePolicy.ExplicitResearchEnable
        if (enabled == null) {
            request.candidate.close()
            return RidLeasePreparationResult.Rejected(RidLeaseFailure.FEATURE_DISABLED, safetyLockout = false)
        }

        synchronized(stateLock) {
            when (state) {
                ControllerState.LOCKED -> {
                    request.candidate.close()
                    return RidLeasePreparationResult.Rejected(
                        RidLeaseFailure.CONTROLLER_LOCKED_OUT,
                        safetyLockout = true,
                    )
                }
                ControllerState.IDLE -> state = ControllerState.PREPARING
                else -> {
                    request.candidate.close()
                    return RidLeasePreparationResult.Rejected(
                        RidLeaseFailure.CONTROLLER_BUSY,
                        safetyLockout = false,
                    )
                }
            }
        }

        val context = CallContext(
            Deadline.after(monotonicClock, enabled.prepareTimeoutNanos),
            cancellation,
            cleanup = false,
        )
        var reinterrupt = false
        return try {
            context.checkpoint(monotonicClock)
            val session = readKnownSession(context)
            val preparedLicense = attest(request.candidate, session, context)
            val baseline = callRunner.run(context) {
                transport.getExactRidUnlockState(session, context)
            }
            if (baseline != request.expectedBaseline) {
                throw LeaseFailureException(RidLeaseFailure.BASELINE_MISMATCH)
            }
            validateAdmittedBaseline(request.target, baseline, session, preparedLicense)?.let {
                throw LeaseFailureException(it.toLeaseFailure())
            }

            val capability = PreparedRidLease(
                controller = this,
                request = request,
                session = session,
                preparedLicense = preparedLicense,
                baseline = baseline,
                expiresAtNanos = saturatedAdd(monotonicClock.nowNanos(), enabled.prepareTtlNanos),
            )
            synchronized(stateLock) {
                state = ControllerState.PREPARED
                owner = capability
            }
            val handle = try {
                val remaining = Deadline(capability.expiresAtNanos)
                    .remainingNanos(monotonicClock)
                    .coerceAtLeast(0L)
                scheduler.schedule(remaining) {
                    abandonPrepared(capability, expired = true)
                }
            } catch (_: Throwable) {
                synchronized(stateLock) {
                    if (owner === capability) {
                        owner = null
                        state = ControllerState.IDLE
                    }
                }
                capability.consumeOnce()
                request.candidate.close()
                return RidLeasePreparationResult.Rejected(
                    RidLeaseFailure.WATCHDOG_SCHEDULE_FAILED,
                    safetyLockout = false,
                )
            }
            capability.installExpiry(handle)
            if (capability.isConsumed() || monotonicClock.nowNanos() >= capability.expiresAtNanos) {
                abandonPrepared(capability, expired = true)
                return RidLeasePreparationResult.Rejected(
                    RidLeaseFailure.PREPARE_EXPIRED,
                    safetyLockout = false,
                )
            }
            emit(AuditPhase.LEASE, AuditCode.LEASE_PREPARED, request.target, session.family)
            RidLeasePreparationResult.Prepared(capability)
        } catch (_: TransactionCancelledException) {
            releasePreparationAfterFailure(request)
            RidLeasePreparationResult.Rejected(RidLeaseFailure.CANCELLED, safetyLockout = false)
        } catch (_: DeadlineExceededException) {
            releasePreparationAfterFailure(request)
            RidLeasePreparationResult.Rejected(RidLeaseFailure.DEADLINE, safetyLockout = false)
        } catch (_: BoundedCallTimeoutException) {
            releasePreparationAfterFailure(request)
            RidLeasePreparationResult.Rejected(RidLeaseFailure.DEADLINE, safetyLockout = false)
        } catch (_: CallerInterruptedException) {
            reinterrupt = true
            releasePreparationAfterFailure(request)
            RidLeasePreparationResult.Rejected(RidLeaseFailure.CANCELLED, safetyLockout = false)
        } catch (failure: LeaseFailureException) {
            releasePreparationAfterFailure(request)
            RidLeasePreparationResult.Rejected(failure.failure, safetyLockout = false)
        } catch (_: Throwable) {
            releasePreparationAfterFailure(request)
            RidLeasePreparationResult.Rejected(RidLeaseFailure.BASELINE_READ_FAILED, safetyLockout = false)
        } finally {
            if (reinterrupt) Thread.currentThread().interrupt()
        }
    }

    internal fun abandonPrepared(capability: PreparedRidLease, expired: Boolean): Boolean {
        synchronized(stateLock) {
            if (state != ControllerState.PREPARED || owner !== capability) return false
            if (!capability.consumeOnce()) return false
            state = ControllerState.IDLE
            owner = null
        }
        capability.cancelExpiry()
        capability.request.candidate.close()
        emit(
            AuditPhase.LEASE,
            if (expired) AuditCode.LEASE_PREPARE_EXPIRED else AuditCode.LEASE_ABANDONED,
            capability.request.target,
            capability.session.family,
        )
        return true
    }

    internal fun commitPrepared(
        capability: PreparedRidLease,
        leaseDurationNanos: Long,
        cancellation: CancellationToken,
    ): RidLeaseCommitResult {
        val enabled = policy as? RidBoundedLeasePolicy.ExplicitResearchEnable
            ?: return rejectedCommit(RidLeaseFailure.FEATURE_DISABLED)
        if (leaseDurationNanos !in 1L..enabled.maxLeaseNanos) {
            return rejectedCommit(RidLeaseFailure.INVALID_LEASE_DURATION)
        }

        synchronized(stateLock) {
            if (state == ControllerState.LOCKED) return rejectedCommit(
                RidLeaseFailure.CONTROLLER_LOCKED_OUT,
                lockout = true,
            )
            if (state != ControllerState.PREPARED || owner !== capability || capability.isConsumed()) {
                return rejectedCommit(RidLeaseFailure.PREPARED_CAPABILITY_ALREADY_CONSUMED)
            }
            if (monotonicClock.nowNanos() >= capability.expiresAtNanos) {
                capability.consumeOnce()
                state = ControllerState.IDLE
                owner = null
                capability.cancelExpiry()
                capability.request.candidate.close()
                return rejectedCommit(RidLeaseFailure.PREPARE_EXPIRED)
            }
            check(capability.consumeOnce())
            capability.cancelExpiry()
            state = ControllerState.COMMITTING
            owner = capability
        }

        val context = CallContext(
            Deadline.after(monotonicClock, enabled.commitTimeoutNanos),
            cancellation,
            cleanup = false,
        )
        var mutationAttempted = false
        var targetObserved = false
        var forceLockout = false
        var reinterrupt = false
        var stage = CommitStage.PREFLIGHT
        var mutationLicense = capability.preparedLicense

        try {
            context.checkpoint(monotonicClock)
            val currentSession = readKnownSession(context)
            if (currentSession != capability.session) {
                throw LeaseFailureException(RidLeaseFailure.SESSION_CHANGED_BEFORE_COMMIT)
            }
            val epochNow = epochClock.nowEpochSeconds()
            if (
                epochNow < capability.request.candidate.validFromEpochSeconds ||
                epochNow >= capability.request.candidate.validUntilEpochSeconds
            ) {
                throw LeaseFailureException(RidLeaseFailure.LICENSE_EXPIRED_BEFORE_COMMIT)
            }
            val currentLicense = attest(capability.request.candidate, currentSession, context)
            mutationLicense = currentLicense
            if (currentLicense.licenseFingerprint != capability.preparedLicense.licenseFingerprint) {
                throw LeaseFailureException(RidLeaseFailure.LICENSE_ATTESTATION_REJECTED)
            }

            stage = CommitStage.BASELINE
            val freshBaseline = callRunner.run(context) {
                transport.getExactRidUnlockState(currentSession, context)
            }
            if (freshBaseline != capability.baseline) {
                throw LeaseFailureException(RidLeaseFailure.BASELINE_CHANGED_BEFORE_COMMIT)
            }
            validateAdmittedBaseline(
                capability.request.target,
                freshBaseline,
                currentSession,
                currentLicense,
            )?.let { throw LeaseFailureException(it.toLeaseFailure()) }

            context.checkpoint(monotonicClock)
            stage = CommitStage.TRANSITION
            mutationAttempted = true
            val receipt = when (capability.request.target) {
                RequestedRidTransition.ENABLE -> callRunner.run(context) {
                    transport.requestEnableVerifiedRidUnlock(
                        currentSession,
                        currentLicense,
                        freshBaseline,
                        context,
                    )
                }
                RequestedRidTransition.DISABLE -> callRunner.run(context) {
                    transport.requestDisableVerifiedRidUnlock(
                        currentSession,
                        currentLicense,
                        freshBaseline,
                        context,
                    )
                }
            }
            if (!receipt.accepted) throw LeaseFailureException(RidLeaseFailure.TRANSITION_REJECTED)
            context.checkpoint(monotonicClock)
            stage = CommitStage.READBACK
            val target = callRunner.run(context) {
                transport.getExactRidUnlockState(currentSession, context)
            }
            context.checkpoint(monotonicClock)
            if (!exactTargetMatches(capability.request.target, currentLicense, freshBaseline, target)) {
                throw LeaseFailureException(RidLeaseFailure.TARGET_READBACK_MISMATCH)
            }
            targetObserved = true
            // Do not establish a lease after cancellation/deadline races following target readback.
            context.checkpoint(monotonicClock)

            val lease = ActiveRidLease(
                controller = this,
                request = capability.request,
                session = currentSession,
                license = currentLicense,
                baseline = freshBaseline,
                expiresAtNanos = saturatedAdd(monotonicClock.nowNanos(), leaseDurationNanos),
            )
            synchronized(stateLock) {
                state = ControllerState.ACTIVE
                owner = lease
            }
            val watchdog = try {
                val remaining = Deadline(lease.expiresAtNanos)
                    .remainingNanos(monotonicClock)
                    .coerceAtLeast(0L)
                scheduler.schedule(remaining) { lease.closeAndReconcile() }
            } catch (_: Throwable) {
                val close = lease.closeAndReconcile()
                return RidLeaseCommitResult.Rejected(
                    failure = if (close.safetyLockout) {
                        RidLeaseFailure.RESTORE_UNCERTAIN
                    } else {
                        RidLeaseFailure.WATCHDOG_SCHEDULE_FAILED
                    },
                    restoration = close.restoration,
                    requestedTransitionObservedByExactGet = true,
                    safetyLockout = close.safetyLockout,
                )
            }
            lease.installWatchdog(watchdog)
            if (lease.status != RidLeaseLifecycle.ACTIVE || monotonicClock.nowNanos() >= lease.expiresAtNanos) {
                val close = lease.closeAndReconcile()
                return RidLeaseCommitResult.Rejected(
                    failure = if (close.safetyLockout) {
                        RidLeaseFailure.RESTORE_UNCERTAIN
                    } else {
                        RidLeaseFailure.LEASE_EXPIRED_BEFORE_RETURN
                    },
                    restoration = close.restoration,
                    requestedTransitionObservedByExactGet = true,
                    safetyLockout = close.safetyLockout,
                )
            }
            emit(AuditPhase.LEASE, AuditCode.LEASE_ACTIVE, capability.request.target, currentSession.family)
            return RidLeaseCommitResult.Active(lease)
        } catch (_: TransactionCancelledException) {
            return finishFailedCommit(
                capability,
                RidLeaseFailure.CANCELLED,
                mutationAttempted,
                targetObserved,
                forceLockout,
                mutationLicense,
            )
        } catch (_: DeadlineExceededException) {
            return finishFailedCommit(
                capability,
                RidLeaseFailure.DEADLINE,
                mutationAttempted,
                targetObserved,
                forceLockout,
                mutationLicense,
            )
        } catch (_: BoundedCallTimeoutException) {
            forceLockout = mutationAttempted
            return finishFailedCommit(
                capability,
                RidLeaseFailure.DEADLINE,
                mutationAttempted,
                targetObserved,
                forceLockout,
                mutationLicense,
            )
        } catch (_: CallerInterruptedException) {
            reinterrupt = true
            forceLockout = mutationAttempted
            return finishFailedCommit(
                capability,
                RidLeaseFailure.CANCELLED,
                mutationAttempted,
                targetObserved,
                forceLockout,
                mutationLicense,
            )
        } catch (failure: LeaseFailureException) {
            return finishFailedCommit(
                capability,
                failure.failure,
                mutationAttempted,
                targetObserved,
                forceLockout,
                mutationLicense,
            )
        } catch (_: Throwable) {
            val failure = when (stage) {
                CommitStage.PREFLIGHT -> RidLeaseFailure.SESSION_READ_FAILED
                CommitStage.BASELINE -> RidLeaseFailure.BASELINE_READ_FAILED
                CommitStage.TRANSITION -> RidLeaseFailure.TRANSITION_CALL_FAILED
                CommitStage.READBACK -> RidLeaseFailure.TARGET_READBACK_FAILED
            }
            return finishFailedCommit(
                capability,
                failure,
                mutationAttempted,
                targetObserved,
                forceLockout,
                mutationLicense,
            )
        } finally {
            if (reinterrupt) Thread.currentThread().interrupt()
        }
    }

    internal fun restoreActiveLease(lease: ActiveRidLease): RidLeaseCloseResult {
        synchronized(stateLock) {
            if (state != ControllerState.ACTIVE || owner !== lease) {
                return RidLeaseCloseResult(
                    restoration = if (state == ControllerState.LOCKED) {
                        RestorationStatus.UNCERTAIN_LOCKED_OUT
                    } else {
                        RestorationStatus.EXACT_BASELINE_CONFIRMED
                    },
                    safetyLockout = state == ControllerState.LOCKED,
                )
            }
            state = ControllerState.RESTORING
        }
        val result = restoreAndReconcile(
            lease.request,
            lease.session,
            lease.license,
            lease.baseline,
            forceLockout = false,
            cleanupTimeoutNanos = enabledPolicy().cleanupTimeoutNanos,
        )
        lease.request.candidate.close()
        synchronized(stateLock) {
            owner = null
            state = if (result.safetyLockout) ControllerState.LOCKED else ControllerState.IDLE
        }
        emit(
            AuditPhase.LEASE,
            if (result.safetyLockout) AuditCode.FINAL_BASELINE_UNCERTAIN else AuditCode.LEASE_RESTORED,
            lease.request.target,
            lease.session.family,
        )
        return result
    }

    private fun finishFailedCommit(
        capability: PreparedRidLease,
        failure: RidLeaseFailure,
        mutationAttempted: Boolean,
        targetObserved: Boolean,
        forceLockout: Boolean,
        mutationLicense: VerifiedRidUnlockLicense,
    ): RidLeaseCommitResult {
        if (!mutationAttempted) {
            capability.request.candidate.close()
            synchronized(stateLock) {
                owner = null
                state = ControllerState.IDLE
            }
            return RidLeaseCommitResult.Rejected(
                failure,
                RestorationStatus.NOT_REQUIRED_NO_MUTATION,
                targetObserved,
                safetyLockout = false,
            )
        }

        synchronized(stateLock) { state = ControllerState.RESTORING }
        val close = restoreAndReconcile(
            capability.request,
            capability.session,
            mutationLicense,
            capability.baseline,
            forceLockout,
            enabledPolicy().cleanupTimeoutNanos,
        )
        capability.request.candidate.close()
        synchronized(stateLock) {
            owner = null
            state = if (close.safetyLockout) ControllerState.LOCKED else ControllerState.IDLE
        }
        return RidLeaseCommitResult.Rejected(
            failure = if (close.safetyLockout) RidLeaseFailure.RESTORE_UNCERTAIN else failure,
            restoration = close.restoration,
            requestedTransitionObservedByExactGet = targetObserved,
            safetyLockout = close.safetyLockout,
        )
    }

    private fun restoreAndReconcile(
        request: RidSwitchRequest,
        session: KnownFlySafeSession,
        license: VerifiedRidUnlockLicense,
        baseline: ExactRidUnlockSnapshot,
        forceLockout: Boolean,
        cleanupTimeoutNanos: Long,
    ): RidLeaseCloseResult {
        val context = CallContext(
            Deadline.after(monotonicClock, cleanupTimeoutNanos),
            NeverCancelled,
            cleanup = true,
        )
        var uncertain = forceLockout
        var reinterrupt = false
        try {
            callRunner.run(context) {
                transport.restoreExactRidUnlockBaseline(session, license, baseline, context)
            }
        } catch (_: BoundedCallTimeoutException) {
            uncertain = true
        } catch (_: CallerInterruptedException) {
            uncertain = true
            reinterrupt = true
        } catch (_: Throwable) {
            // Final live GET is authoritative unless the call timed out and could complete late.
        }

        val exact = try {
            callRunner.run(context) {
                transport.getExactRidUnlockState(session, context)
            }.exactlyRestores(baseline)
        } catch (_: CallerInterruptedException) {
            reinterrupt = true
            false
        } catch (_: Throwable) {
            false
        }
        if (!exact) uncertain = true
        val result = RidLeaseCloseResult(
            restoration = if (uncertain) {
                RestorationStatus.UNCERTAIN_LOCKED_OUT
            } else {
                RestorationStatus.EXACT_BASELINE_CONFIRMED
            },
            safetyLockout = uncertain,
        )
        if (reinterrupt) Thread.currentThread().interrupt()
        return result
    }

    private fun readKnownSession(context: CallContext): KnownFlySafeSession {
        val inspection = try {
            callRunner.run(context) { sessionProvider.inspect(context) }
        } catch (error: TransactionCancelledException) {
            throw error
        } catch (error: DeadlineExceededException) {
            throw error
        } catch (error: BoundedCallTimeoutException) {
            throw error
        } catch (error: CallerInterruptedException) {
            throw error
        } catch (_: Throwable) {
            throw LeaseFailureException(RidLeaseFailure.SESSION_READ_FAILED)
        }
        val session = when (inspection) {
            is SessionInspection.Known -> inspection.session
            SessionInspection.Missing -> throw LeaseFailureException(RidLeaseFailure.SESSION_MISSING)
            SessionInspection.Unsupported -> throw LeaseFailureException(RidLeaseFailure.SESSION_UNSUPPORTED)
        }
        if (session.authentication != SessionAuthentication.AUTHENTICATED) {
            throw LeaseFailureException(RidLeaseFailure.SESSION_UNAUTHENTICATED)
        }
        if (!session.serverAttested) {
            throw LeaseFailureException(RidLeaseFailure.SESSION_NOT_SERVER_ATTESTED)
        }
        return session
    }

    private fun attest(
        candidate: RidUnlockInventoryCandidate,
        session: KnownFlySafeSession,
        context: CallContext,
    ): VerifiedRidUnlockLicense {
        val attestation = try {
            callRunner.run(context) {
                verifier.attest(candidate, session, epochClock, context, monotonicClock)
            }
        } catch (error: TransactionCancelledException) {
            throw error
        } catch (error: DeadlineExceededException) {
            throw error
        } catch (error: BoundedCallTimeoutException) {
            throw error
        } catch (error: CallerInterruptedException) {
            throw error
        } catch (_: Throwable) {
            throw LeaseFailureException(RidLeaseFailure.LICENSE_ATTESTATION_FAILED)
        }
        return when (attestation) {
            is LicenseAttestation.Verified -> attestation.license
            is LicenseAttestation.Rejected -> throw LeaseFailureException(
                RidLeaseFailure.LICENSE_ATTESTATION_REJECTED,
            )
        }
    }

    private fun releasePreparationAfterFailure(request: RidSwitchRequest) {
        request.candidate.close()
        synchronized(stateLock) {
            owner = null
            state = ControllerState.IDLE
        }
    }

    private fun rejectedCommit(
        failure: RidLeaseFailure,
        lockout: Boolean = false,
    ) = RidLeaseCommitResult.Rejected(
        failure,
        RestorationStatus.NOT_REQUIRED_NO_MUTATION,
        requestedTransitionObservedByExactGet = false,
        safetyLockout = lockout,
    )

    private fun enabledPolicy(): RidBoundedLeasePolicy.ExplicitResearchEnable =
        checkNotNull(policy as? RidBoundedLeasePolicy.ExplicitResearchEnable)

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
            // Audit never controls safety behavior.
        }
    }

    private fun RidSwitchFailure.toLeaseFailure(): RidLeaseFailure = when (this) {
        RidSwitchFailure.BASELINE_MISMATCH -> RidLeaseFailure.BASELINE_MISMATCH
        RidSwitchFailure.REQUEST_IS_NOT_A_TRANSITION -> RidLeaseFailure.REQUEST_IS_NOT_A_TRANSITION
        RidSwitchFailure.ACTIVE_LICENSE_MISMATCH -> RidLeaseFailure.ACTIVE_LICENSE_MISMATCH
        else -> error("unexpected shared validation failure")
    }

    private fun saturatedAdd(left: Long, right: Long): Long = try {
        Math.addExact(left, right)
    } catch (_: ArithmeticException) {
        Long.MAX_VALUE
    }

    private enum class ControllerState { IDLE, PREPARING, PREPARED, COMMITTING, ACTIVE, RESTORING, LOCKED }
    private enum class CommitStage { PREFLIGHT, BASELINE, TRANSITION, READBACK }
    private class LeaseFailureException(val failure: RidLeaseFailure) : RuntimeException(failure.name)
}
