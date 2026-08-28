package com.finduas.ridswitch

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotSame
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong

class RidBoundedLeaseControllerTest {
    @Test
    fun `bounded lease feature is disabled by default and closes credential without any port call`() {
        val h = LeaseHarness()
        val defaultDisabledController = RidBoundedLeaseController(
            sessionProvider = h.sessionProvider,
            verifier = h.verifier,
            transport = h.transport,
            monotonicClock = h.clock,
            epochClock = EpochClock { NOW },
            audit = h.audit,
        )

        val result = defaultDisabledController.prepareBoundedLease(h.request)

        assertRejectedPreparation(result, RidLeaseFailure.FEATURE_DISABLED)
        assertEquals(0, h.sessionProvider.calls.get())
        assertEquals(0, h.verifier.calls.get())
        assertEquals(0, h.transport.totalCalls())
        assertTrue(h.candidate.isClosed)
    }

    @Test
    fun `bounded disable lease uses one verified credential and restores enabled baseline`() {
        val h = LeaseHarness(target = RequestedRidTransition.DISABLE)

        val active = h.commitActive(h.prepare())

        assertEquals(0, h.transport.enableCalls.get())
        assertEquals(1, h.transport.disableCalls.get())
        assertEquals(0, h.transport.restoreCalls.get())
        active.closeAndReconcile()
        assertEquals(1, h.transport.restoreCalls.get())
        assertSame(h.transport.transitionLicenses.single(), h.transport.restoreLicenses.single())
    }

    @Test
    fun `prepare proves admission but performs no mutation and abandonment zeroes credential`() {
        val h = LeaseHarness()

        val prepared = h.prepare()

        assertEquals(1, h.sessionProvider.calls.get())
        assertEquals(1, h.verifier.calls.get())
        assertEquals(1, h.transport.getCalls.get())
        assertEquals(0, h.transport.mutationCalls())
        assertFalse(h.candidate.isClosed)
        assertTrue(prepared.abandon())
        assertTrue(h.candidate.isClosed)
        assertFalse(h.controller.isOccupied)
    }

    @Test
    fun `uncommitted preparation automatically expires and zeroes credential`() {
        val h = LeaseHarness()
        val prepared = h.prepare()

        assertTrue(h.scheduler.runNextActive())

        assertTrue(h.candidate.isClosed)
        assertFalse(h.controller.isOccupied)
        val result = prepared.commitBounded(1_000_000L)
        assertRejectedCommit(result, RidLeaseFailure.PREPARED_CAPABILITY_ALREADY_CONSUMED)
    }

    @Test
    fun `prepare watchdog scheduling failure is fail-closed before mutation`() {
        val h = LeaseHarness()
        h.scheduler.failAtScheduleCall = 1

        val result = h.controller.prepareBoundedLease(h.request)

        assertRejectedPreparation(result, RidLeaseFailure.WATCHDOG_SCHEDULE_FAILED)
        assertEquals(0, h.transport.mutationCalls())
        assertTrue(h.candidate.isClosed)
        assertFalse(h.controller.isOccupied)
    }

    @Test
    fun `synchronous or already-expired watchdog cannot return a stale prepared or active capability`() {
        run {
            val h = LeaseHarness()
            h.scheduler.runSynchronouslyAtScheduleCall = 1
            val result = h.controller.prepareBoundedLease(h.request)
            assertRejectedPreparation(result, RidLeaseFailure.PREPARE_EXPIRED)
            assertTrue(h.candidate.isClosed)
            assertEquals(0, h.transport.mutationCalls())
        }

        run {
            val h = LeaseHarness()
            val prepared = h.prepare()
            h.scheduler.runSynchronouslyAtScheduleCall = 2
            val result = prepared.commitBounded(1_000_000L)
            assertRejectedCommit(result, RidLeaseFailure.LEASE_EXPIRED_BEFORE_RETURN)
            assertEquals(1, h.transport.restoreCalls.get())
            assertTrue(h.candidate.isClosed)
        }
    }

    @Test
    fun `commit holds exact target until explicit close then restores with same verified credential`() {
        val h = LeaseHarness()
        val prepared = h.prepare()

        val active = h.commitActive(prepared)

        assertEquals(RidLeaseLifecycle.ACTIVE, active.status)
        assertEquals(RfEvidenceStatus.EXTERNAL_NOT_EVALUATED, active.rfEvidence)
        assertEquals(1, h.transport.enableCalls.get())
        assertEquals(0, h.transport.restoreCalls.get())
        assertFalse(h.candidate.isClosed)
        assertTrue(h.controller.isOccupied)
        assertEquals(2, h.verifier.calls.get())
        assertRejectedCommit(
            prepared.commitBounded(1_000_000L),
            RidLeaseFailure.PREPARED_CAPABILITY_ALREADY_CONSUMED,
        )

        val transitionLicense = h.transport.transitionLicenses.single()
        assertNotSame(prepared.preparedLicense, transitionLicense)
        val closed = active.closeAndReconcile()

        assertEquals(RestorationStatus.EXACT_BASELINE_CONFIRMED, closed.restoration)
        assertEquals(RidLeaseLifecycle.RESTORED, active.status)
        assertEquals(1, h.transport.restoreCalls.get())
        assertSame(transitionLicense, h.transport.restoreLicenses.single())
        assertTrue(h.candidate.isClosed)
        assertFalse(h.controller.isOccupied)
        expectIllegalState {
            transitionLicense.useLicenseId { error("credential should already be zeroed") }
        }
    }

    @Test
    fun `lease watchdog expiry restores exact baseline and repeated close is idempotent`() {
        val h = LeaseHarness()
        val active = h.commitActive(h.prepare())

        assertTrue(h.scheduler.runNextActive())

        assertEquals(RidLeaseLifecycle.RESTORED, active.status)
        assertEquals(1, h.transport.restoreCalls.get())
        val again = active.closeAndReconcile()
        assertEquals(RestorationStatus.EXACT_BASELINE_CONFIRMED, again.restoration)
        assertEquals(1, h.transport.restoreCalls.get())
    }

    @Test
    fun `another request is rejected and its credential cleared while lease is active`() {
        val h = LeaseHarness()
        val active = h.commitActive(h.prepare())
        val secondCandidate = candidate(h.session)

        val second = h.controller.prepareBoundedLease(
            RidSwitchRequest(RequestedRidTransition.ENABLE, secondCandidate, h.baseline),
        )

        assertRejectedPreparation(second, RidLeaseFailure.CONTROLLER_BUSY)
        assertTrue(secondCandidate.isClosed)
        assertEquals(1, h.transport.mutationCalls())
        active.closeAndReconcile()
    }

    @Test
    fun `invalid lease duration does not consume preparation and a valid bounded commit can follow`() {
        val h = LeaseHarness(maxLeaseNanos = 2_000_000L)
        val prepared = h.prepare()

        assertRejectedCommit(prepared.commitBounded(0L), RidLeaseFailure.INVALID_LEASE_DURATION)
        assertRejectedCommit(prepared.commitBounded(2_000_001L), RidLeaseFailure.INVALID_LEASE_DURATION)
        assertFalse(h.candidate.isClosed)

        val active = h.commitActive(prepared, 2_000_000L)
        active.closeAndReconcile()
    }

    @Test
    fun `commit rechecks exact baseline and refuses a changed state without mutation`() {
        val h = LeaseHarness()
        val prepared = h.prepare()
        h.transport.reads.clear()
        h.transport.reads.add { h.baseline.copy(revision = h.baseline.revision + 1) }

        val result = prepared.commitBounded(1_000_000L)

        assertRejectedCommit(result, RidLeaseFailure.BASELINE_CHANGED_BEFORE_COMMIT)
        assertEquals(0, h.transport.mutationCalls())
        assertEquals(0, h.transport.restoreCalls.get())
        assertTrue(h.candidate.isClosed)
    }

    @Test
    fun `commit rechecks live session and authoritative inventory provenance`() {
        run {
            val h = LeaseHarness()
            val prepared = h.prepare()
            h.sessionProvider.inspection = SessionInspection.Known(
                h.session.copy(sessionFingerprint = fp("rotated-session")),
            )
            val result = prepared.commitBounded(1_000_000L)
            assertRejectedCommit(result, RidLeaseFailure.SESSION_CHANGED_BEFORE_COMMIT)
            assertEquals(0, h.transport.mutationCalls())
            assertTrue(h.candidate.isClosed)
        }

        run {
            val h = LeaseHarness()
            val prepared = h.prepare()
            h.verifier.inventoryMember = false
            val result = prepared.commitBounded(1_000_000L)
            assertRejectedCommit(result, RidLeaseFailure.LICENSE_ATTESTATION_REJECTED)
            assertEquals(0, h.transport.mutationCalls())
            assertTrue(h.candidate.isClosed)
        }
    }

    @Test
    fun `commit cancellation before mutation consumes preparation and clears credential`() {
        val h = LeaseHarness()
        val prepared = h.prepare()
        val cancellation = CancellationSource().apply { cancel() }

        val result = prepared.commitBounded(1_000_000L, cancellation)

        assertRejectedCommit(result, RidLeaseFailure.CANCELLED)
        assertEquals(0, h.transport.mutationCalls())
        assertEquals(0, h.transport.restoreCalls.get())
        assertTrue(h.candidate.isClosed)
    }

    @Test
    fun `transition exception restores with the exact commit credential then clears it`() {
        val h = LeaseHarness()
        val prepared = h.prepare()
        h.transport.enableAction = { throw IllegalStateException("sensitive-exception") }
        h.transport.reads.clear()
        h.transport.reads.add { h.baseline }
        h.transport.reads.add { restoredFrom(h.baseline, h.baseline.revision + 1) }

        val result = prepared.commitBounded(1_000_000L)

        assertRejectedCommit(result, RidLeaseFailure.TRANSITION_CALL_FAILED)
        assertEquals(RestorationStatus.EXACT_BASELINE_CONFIRMED, (result as RidLeaseCommitResult.Rejected).restoration)
        assertEquals(1, h.transport.restoreCalls.get())
        assertSame(h.transport.transitionLicenses.single(), h.transport.restoreLicenses.single())
        assertTrue(h.candidate.isClosed)
    }

    @Test
    fun `target mismatch and post-transition cancellation both force immediate exact restore`() {
        run {
            val h = LeaseHarness()
            val prepared = h.prepare()
            h.transport.reads.clear()
            h.transport.reads.add { h.baseline }
            h.transport.reads.add { h.baseline.copy(revision = h.baseline.revision + 1) }
            h.transport.reads.add { restoredFrom(h.baseline, h.baseline.revision + 2) }
            val result = prepared.commitBounded(1_000_000L)
            assertRejectedCommit(result, RidLeaseFailure.TARGET_READBACK_MISMATCH)
            assertEquals(1, h.transport.restoreCalls.get())
        }

        run {
            val h = LeaseHarness()
            val prepared = h.prepare()
            val cancellation = CancellationSource()
            h.transport.enableAction = {
                cancellation.cancel()
                TransitionReceipt(true)
            }
            h.transport.reads.clear()
            h.transport.reads.add { h.baseline }
            h.transport.reads.add { restoredFrom(h.baseline, h.baseline.revision + 2) }
            val result = prepared.commitBounded(1_000_000L, cancellation)
            assertRejectedCommit(result, RidLeaseFailure.CANCELLED)
            assertEquals(1, h.transport.restoreCalls.get())
            assertTrue(h.transport.cleanupContexts.all { it.cleanup && !it.cancellation.isCancelled })
        }
    }

    @Test
    fun `watchdog scheduling failure after target proof immediately restores`() {
        val h = LeaseHarness()
        val prepared = h.prepare()
        h.scheduler.failAtScheduleCall = 2

        val result = prepared.commitBounded(1_000_000L)

        assertRejectedCommit(result, RidLeaseFailure.WATCHDOG_SCHEDULE_FAILED)
        val rejected = result as RidLeaseCommitResult.Rejected
        assertTrue(rejected.requestedTransitionObservedByExactGet)
        assertEquals(RestorationStatus.EXACT_BASELINE_CONFIRMED, rejected.restoration)
        assertEquals(1, h.transport.restoreCalls.get())
        assertTrue(h.candidate.isClosed)
    }

    @Test
    fun `uncertain lease close latches controller lockout and rejects future credentials`() {
        val h = LeaseHarness()
        val active = h.commitActive(h.prepare())
        h.transport.reads.clear()
        h.transport.reads.add { h.targetSnapshot.copy(revision = h.targetSnapshot.revision + 1) }

        val close = active.closeAndReconcile()

        assertEquals(RestorationStatus.UNCERTAIN_LOCKED_OUT, close.restoration)
        assertTrue(close.safetyLockout)
        assertTrue(h.controller.isLockedOut)
        val futureCandidate = candidate(h.session)
        val later = h.controller.prepareBoundedLease(
            RidSwitchRequest(RequestedRidTransition.ENABLE, futureCandidate, h.baseline),
        )
        assertRejectedPreparation(later, RidLeaseFailure.CONTROLLER_LOCKED_OUT)
        assertTrue(futureCandidate.isClosed)
    }

    @Test
    fun `bounded policy enforces hard caps and public API has no permanent commit or renewal`() {
        expectIllegalArgument {
            RidBoundedLeasePolicy.ExplicitResearchEnable.explicitlyEnableForResearch(maxLeaseNanos = 0L)
        }
        expectIllegalArgument {
            RidBoundedLeasePolicy.ExplicitResearchEnable.explicitlyEnableForResearch(
                maxLeaseNanos = RidBoundedLeasePolicy.ExplicitResearchEnable.HARD_MAX_LEASE_NANOS + 1,
            )
        }
        val methodNames = (PreparedRidLease::class.java.methods + ActiveRidLease::class.java.methods)
            .map { it.name.lowercase() }
        assertFalse(methodNames.any { it.contains("permanent") || it.contains("renew") || it.contains("indefinite") })
        assertTrue(methodNames.contains("commitbounded"))
    }

    @Test
    fun `lease audit and results remain redacted`() {
        val h = LeaseHarness()
        val preparedResult = h.controller.prepareBoundedLease(h.request)
        val prepared = (preparedResult as RidLeasePreparationResult.Prepared).capability
        val commit = prepared.commitBounded(1_000_000L)
        val active = (commit as RidLeaseCommitResult.Active).lease
        val rendered = buildString {
            append(preparedResult)
            append(commit)
            append(active)
            h.audit.events.forEach(::append)
        }
        assertFalse(rendered.contains(SECRET))
        assertFalse(rendered.contains("signed-envelope"))
        active.closeAndReconcile()
    }

    private class LeaseHarness(
        policy: RidBoundedLeasePolicy? = null,
        maxLeaseNanos: Long = 5_000_000L,
        target: RequestedRidTransition = RequestedRidTransition.ENABLE,
    ) {
        val clock = FakeClock()
        val session = session()
        val sessionProvider = FakeSessionProvider(SessionInspection.Known(session))
        val verifier = FakeVerifier()
        val scheduler = ManualScheduler()
        val audit = CollectingAudit()
        val candidate = candidate(session)
        val licenseFingerprint = OpaqueFingerprint.sha256(SECRET.toByteArray())
        val baseline = ExactRidUnlockSnapshot(
            RidRestorableState(
                activation = if (target == RequestedRidTransition.ENABLE) {
                    RidActivation.DISABLED
                } else {
                    RidActivation.ENABLED
                },
                activeLicenseFingerprint = if (target == RequestedRidTransition.ENABLE) {
                    null
                } else {
                    licenseFingerprint
                },
                sessionFingerprint = session.sessionFingerprint,
                accountFingerprint = session.accountFingerprint,
                aircraftFingerprint = session.aircraftFingerprint,
                policyProfileFingerprint = fp("policy"),
                inventoryGeneration = 3L,
            ),
            revision = 20L,
        )
        val targetSnapshot = baseline.copy(
            restorableState = baseline.restorableState.copy(
                activation = if (target == RequestedRidTransition.ENABLE) {
                    RidActivation.ENABLED
                } else {
                    RidActivation.DISABLED
                },
                activeLicenseFingerprint = if (target == RequestedRidTransition.ENABLE) {
                    licenseFingerprint
                } else {
                    null
                },
            ),
            revision = 21L,
        )
        val transport = FakeTransport().apply {
            reads.add { baseline }
            reads.add { baseline }
            reads.add { targetSnapshot }
            reads.add { restoredFrom(baseline, 22L) }
        }
        val request = RidSwitchRequest(target, candidate, baseline)
        val controller = RidBoundedLeaseController(
            sessionProvider = sessionProvider,
            verifier = verifier,
            transport = transport,
            monotonicClock = clock,
            epochClock = EpochClock { NOW },
            audit = audit,
            policy = policy ?: RidBoundedLeasePolicy.ExplicitResearchEnable.explicitlyEnableForResearch(
                maxLeaseNanos = maxLeaseNanos,
                prepareTtlNanos = 2_000_000L,
                prepareTimeoutNanos = 100_000_000L,
                commitTimeoutNanos = 100_000_000L,
                cleanupTimeoutNanos = 100_000_000L,
            ),
            scheduler = scheduler,
            testingMarker = Unit,
        )

        fun prepare(): PreparedRidLease {
            val result = controller.prepareBoundedLease(request)
            assertTrue("expected prepared, got $result", result is RidLeasePreparationResult.Prepared)
            return (result as RidLeasePreparationResult.Prepared).capability
        }

        fun commitActive(prepared: PreparedRidLease, duration: Long = 1_000_000L): ActiveRidLease {
            val result = prepared.commitBounded(duration)
            assertTrue("expected active, got $result", result is RidLeaseCommitResult.Active)
            return (result as RidLeaseCommitResult.Active).lease
        }
    }

    private class FakeClock : MonotonicClock {
        private val now = AtomicLong(1_000L)
        override fun nowNanos(): Long = now.get()
    }

    private class FakeSessionProvider(var inspection: SessionInspection) : FlySafeSessionProvider {
        val calls = AtomicInteger()
        override fun inspect(context: CallContext): SessionInspection {
            calls.incrementAndGet()
            return inspection
        }
    }

    private class FakeVerifier : RidUnlockProvenanceVerifier() {
        val calls = AtomicInteger()
        var signatureValid = true
        var inventoryMember = true
        override fun verifyCryptographicSignatureAndInventoryProvenance(
            material: VerificationMaterial,
            candidate: RidUnlockInventoryCandidate,
            session: KnownFlySafeSession,
            context: CallContext,
        ): CryptographicVerdict {
            calls.incrementAndGet()
            return CryptographicVerdict(signatureValid, inventoryMember)
        }
    }

    private class FakeTransport : RidUnlockTransport {
        val reads = ConcurrentLinkedQueue<() -> ExactRidUnlockSnapshot>()
        val getCalls = AtomicInteger()
        val enableCalls = AtomicInteger()
        val disableCalls = AtomicInteger()
        val restoreCalls = AtomicInteger()
        val transitionLicenses = CopyOnWriteArrayList<VerifiedRidUnlockLicense>()
        val restoreLicenses = CopyOnWriteArrayList<VerifiedRidUnlockLicense>()
        val cleanupContexts = CopyOnWriteArrayList<CallContext>()
        var enableAction: () -> TransitionReceipt = { TransitionReceipt(true) }
        var disableAction: () -> TransitionReceipt = { TransitionReceipt(true) }
        var restoreAction: () -> RestoreReceipt = { RestoreReceipt(true) }

        override fun getExactRidUnlockState(
            session: KnownFlySafeSession,
            context: CallContext,
        ): ExactRidUnlockSnapshot {
            getCalls.incrementAndGet()
            if (context.cleanup) cleanupContexts.add(context)
            return checkNotNull(reads.poll()) { "unexpected GET" }.invoke()
        }

        override fun requestEnableVerifiedRidUnlock(
            session: KnownFlySafeSession,
            license: VerifiedRidUnlockLicense,
            exactBaseline: ExactRidUnlockSnapshot,
            context: CallContext,
        ): TransitionReceipt {
            enableCalls.incrementAndGet()
            transitionLicenses.add(license)
            license.useLicenseId { assertTrue(it.isNotEmpty()) }
            return enableAction()
        }

        override fun requestDisableVerifiedRidUnlock(
            session: KnownFlySafeSession,
            license: VerifiedRidUnlockLicense,
            exactBaseline: ExactRidUnlockSnapshot,
            context: CallContext,
        ): TransitionReceipt {
            disableCalls.incrementAndGet()
            transitionLicenses.add(license)
            return disableAction()
        }

        override fun restoreExactRidUnlockBaseline(
            session: KnownFlySafeSession,
            license: VerifiedRidUnlockLicense,
            exactBaseline: ExactRidUnlockSnapshot,
            context: CallContext,
        ): RestoreReceipt {
            restoreCalls.incrementAndGet()
            restoreLicenses.add(license)
            cleanupContexts.add(context)
            license.useLicenseId { assertTrue(it.isNotEmpty()) }
            return restoreAction()
        }

        fun mutationCalls(): Int = enableCalls.get() + disableCalls.get()
        fun totalCalls(): Int = getCalls.get() + mutationCalls() + restoreCalls.get()
    }

    private class ManualScheduler : LeaseScheduler {
        private data class Task(val action: () -> Unit, var cancelled: Boolean = false)
        private val tasks = mutableListOf<Task>()
        var scheduleCalls = 0
        var failAtScheduleCall: Int? = null
        var runSynchronouslyAtScheduleCall: Int? = null

        override fun schedule(delayNanos: Long, action: () -> Unit): LeaseScheduleHandle {
            scheduleCalls += 1
            if (failAtScheduleCall == scheduleCalls) throw IllegalStateException("scheduler failure")
            val task = Task(action)
            tasks.add(task)
            if (runSynchronouslyAtScheduleCall == scheduleCalls) {
                task.cancelled = true
                task.action()
            }
            return LeaseScheduleHandle {
                val wasActive = !task.cancelled
                task.cancelled = true
                wasActive
            }
        }

        fun runNextActive(): Boolean {
            val task = tasks.firstOrNull { !it.cancelled } ?: return false
            task.cancelled = true
            task.action()
            return true
        }
    }

    private class CollectingAudit : RedactedAuditSink {
        val events = CopyOnWriteArrayList<RedactedAuditEvent>()
        override fun record(event: RedactedAuditEvent) {
            events.add(event)
        }
    }

    companion object {
        private const val NOW = 2_000_000_000L
        private const val SECRET = "bounded-lease-secret-id"

        private fun fp(label: String) = OpaqueFingerprint.sha256(label.toByteArray())

        private fun session() = KnownFlySafeSession(
            family = FlySafeProtocolFamily.V4,
            authentication = SessionAuthentication.AUTHENTICATED,
            serverAttested = true,
            sessionFingerprint = fp("session"),
            accountFingerprint = fp("account"),
            aircraftFingerprint = fp("aircraft"),
        )

        private fun candidate(session: KnownFlySafeSession) = RidUnlockInventoryCandidate.consumeCopies(
            licenseId = SECRET.toByteArray(),
            signedEnvelope = "signed-envelope".toByteArray(),
            typeCode = RID_UNLOCK_TYPE_CODE,
            origin = InventoryOrigin.OFFICIAL_SIGNED_ACCOUNT_INVENTORY,
            signatureScheme = InventorySignatureScheme.DJI_FLYSAFE_SIGNED_ENVELOPE,
            binding = InventoryBinding(
                session.accountFingerprint,
                session.aircraftFingerprint,
                session.family,
            ),
            validFromEpochSeconds = NOW - 60L,
            validUntilEpochSeconds = NOW + 60L,
        )

        private fun restoredFrom(baseline: ExactRidUnlockSnapshot, revision: Long) =
            baseline.copy(revision = revision)

        private fun assertRejectedPreparation(result: RidLeasePreparationResult, failure: RidLeaseFailure) {
            assertTrue("expected rejected, got $result", result is RidLeasePreparationResult.Rejected)
            assertEquals(failure, (result as RidLeasePreparationResult.Rejected).failure)
        }

        private fun assertRejectedCommit(result: RidLeaseCommitResult, failure: RidLeaseFailure) {
            assertTrue("expected rejected, got $result", result is RidLeaseCommitResult.Rejected)
            assertEquals(failure, (result as RidLeaseCommitResult.Rejected).failure)
        }

        private fun expectIllegalArgument(block: () -> Unit) {
            try {
                block()
                throw AssertionError("expected IllegalArgumentException")
            } catch (_: IllegalArgumentException) {
                // expected
            }
        }

        private fun expectIllegalState(block: () -> Unit) {
            try {
                block()
                throw AssertionError("expected IllegalStateException")
            } catch (_: IllegalStateException) {
                // expected
            }
        }
    }
}
