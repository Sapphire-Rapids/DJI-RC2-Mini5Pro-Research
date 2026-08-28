package com.finduas.ridswitch

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong

class RidValidationPulseControllerTest {
    @Test
    fun `enable is proven by exact GET then exact baseline is restored`() {
        val h = Harness(RequestedRidTransition.ENABLE)

        val result = h.executeValidationPulse()

        assertEquals(RidValidationPulseStatus.VERIFIED_TRANSITION_AND_RESTORED, result.status)
        assertNull(result.primaryFailure)
        assertEquals(RestorationStatus.EXACT_BASELINE_CONFIRMED, result.restoration)
        assertTrue(result.requestedTransitionObservedByExactGet)
        assertEquals(RfEvidenceStatus.EXTERNAL_NOT_EVALUATED, result.rfEvidence)
        assertEquals(1, h.transport.enableCalls.get())
        assertEquals(0, h.transport.disableCalls.get())
        assertEquals(1, h.transport.restoreCalls.get())
        assertEquals(3, h.transport.getCalls.get())
        assertEquals(1, h.transport.transitionLicenses.size)
        assertEquals(1, h.transport.restoreLicenses.size)
        assertSame(h.transport.transitionLicenses.single(), h.transport.restoreLicenses.single())
        assertTrue(h.candidate.isClosed)
        expectIllegalState {
            h.transport.restoreLicenses.single().useLicenseId { error("closed credential leaked") }
        }
        assertFalse(h.controller.isLockedOut)
    }

    @Test
    fun `disable is proven only for the same verified active type-6 license then restored`() {
        val h = Harness(RequestedRidTransition.DISABLE)

        val result = h.executeValidationPulse()

        assertEquals(RidValidationPulseStatus.VERIFIED_TRANSITION_AND_RESTORED, result.status)
        assertEquals(0, h.transport.enableCalls.get())
        assertEquals(1, h.transport.disableCalls.get())
        assertEquals(1, h.transport.restoreCalls.get())
        assertTrue(result.requestedTransitionObservedByExactGet)
    }

    @Test
    fun `all known authenticated server-attested V2 V3 V4 sessions are admitted`() {
        for (family in FlySafeProtocolFamily.entries) {
            val h = Harness(RequestedRidTransition.ENABLE, family = family)
            val result = h.executeValidationPulse()
            assertEquals("family=$family", RidValidationPulseStatus.VERIFIED_TRANSITION_AND_RESTORED, result.status)
        }
    }

    @Test
    fun `missing unsupported unauthenticated and unattested sessions fail before inventory or transport`() {
        val cases = listOf(
            SessionInspection.Missing to RidSwitchFailure.SESSION_MISSING,
            SessionInspection.Unsupported to RidSwitchFailure.SESSION_UNSUPPORTED,
            SessionInspection.Known(defaultSession(authentication = SessionAuthentication.UNAUTHENTICATED)) to
                RidSwitchFailure.SESSION_UNAUTHENTICATED,
            SessionInspection.Known(defaultSession(serverAttested = false)) to
                RidSwitchFailure.SESSION_NOT_SERVER_ATTESTED,
        )

        for ((inspection, expectedFailure) in cases) {
            val h = Harness(RequestedRidTransition.ENABLE)
            h.sessionProvider.inspection = inspection
            val result = h.executeValidationPulse()
            assertEquals(expectedFailure, result.primaryFailure)
            assertEquals(RidValidationPulseStatus.REJECTED_WITHOUT_MUTATION, result.status)
            assertEquals(0, h.verifier.calls.get())
            assertEquals(0, h.transport.totalCalls())
            assertTrue(h.candidate.isClosed)
        }
    }

    @Test
    fun `session provider exception is redacted and mutation never starts`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        h.sessionProvider.failure = IllegalStateException(SECRET)

        val result = h.executeValidationPulse()

        assertEquals(RidSwitchFailure.SESSION_READ_FAILED, result.primaryFailure)
        assertEquals(0, h.transport.totalCalls())
        assertFalse(result.toString().contains(SECRET))
        assertTrue(h.candidate.isClosed)
    }

    @Test
    fun `every structural provenance rejection fails before cryptographic verifier and transport`() {
        val session = defaultSession()
        val cases = listOf(
            candidate(session, typeCode = 5) to AttestationRejection.WRONG_TYPE,
            candidate(session, origin = InventoryOrigin.SIDELOADED) to AttestationRejection.UNTRUSTED_ORIGIN,
            candidate(session, scheme = InventorySignatureScheme.UNSIGNED) to
                AttestationRejection.UNSUPPORTED_SIGNATURE_SCHEME,
            candidate(session, binding = defaultBinding(session).copy(accountFingerprint = fp("other-account"))) to
                AttestationRejection.SESSION_BINDING_MISMATCH,
            candidate(session, validFrom = NOW + 1) to AttestationRejection.NOT_YET_VALID,
            candidate(session, validUntil = NOW) to AttestationRejection.EXPIRED,
            candidate(session, envelope = byteArrayOf()) to AttestationRejection.EMPTY_SIGNED_ENVELOPE,
        )

        for ((candidate, _) in cases) {
            val h = Harness(RequestedRidTransition.ENABLE, candidateOverride = candidate)
            val result = h.executeValidationPulse()
            assertEquals(RidSwitchFailure.LICENSE_ATTESTATION_REJECTED, result.primaryFailure)
            assertEquals(0, h.transport.totalCalls())
            assertTrue(candidate.isClosed)
        }
    }

    @Test
    fun `invalid signature and missing authoritative inventory provenance are independently rejected`() {
        for ((signature, membership) in listOf(false to true, true to false)) {
            val h = Harness(RequestedRidTransition.ENABLE)
            h.verifier.signatureValid = signature
            h.verifier.inventoryMember = membership
            val result = h.executeValidationPulse()
            assertEquals(RidSwitchFailure.LICENSE_ATTESTATION_REJECTED, result.primaryFailure)
            assertEquals(0, h.transport.totalCalls())
        }
    }

    @Test
    fun `attestation exception cannot reach transport`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        h.verifier.failure = IllegalArgumentException(SECRET)

        val result = h.executeValidationPulse()

        assertEquals(RidSwitchFailure.LICENSE_ATTESTATION_FAILED, result.primaryFailure)
        assertEquals(0, h.transport.totalCalls())
        assertFalse(result.toString().contains(SECRET))
    }

    @Test
    fun `baseline GET failure cannot invoke a transition or restoration`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        h.transport.reads.clear()
        h.transport.reads.add { throw IllegalStateException(SECRET) }

        val result = h.executeValidationPulse()

        assertEquals(RidSwitchFailure.BASELINE_READ_FAILED, result.primaryFailure)
        assertEquals(0, h.transport.mutationCalls())
        assertEquals(0, h.transport.restoreCalls.get())
        assertFalse(h.controller.isLockedOut)
    }

    @Test
    fun `stale or non-exact expected baseline is rejected without mutation`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        h.request = h.request.copy(expectedBaseline = h.baseline.copy(revision = h.baseline.revision - 1))

        val result = h.executeValidationPulse()

        assertEquals(RidSwitchFailure.BASELINE_MISMATCH, result.primaryFailure)
        assertEquals(0, h.transport.mutationCalls())
        assertEquals(0, h.transport.restoreCalls.get())
    }

    @Test
    fun `baseline bound to a different session is rejected`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        val wrong = h.baseline.copy(
            restorableState = h.baseline.restorableState.copy(sessionFingerprint = fp("wrong-session")),
        )
        h.transport.reads.clear()
        h.transport.reads.add { wrong }
        h.request = h.request.copy(expectedBaseline = wrong)

        val result = h.executeValidationPulse()

        assertEquals(RidSwitchFailure.BASELINE_MISMATCH, result.primaryFailure)
        assertEquals(0, h.transport.mutationCalls())
    }

    @Test
    fun `request already equal to baseline is not treated as a transition`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        val alreadyEnabled = enabledFrom(h.baseline, h.licenseFingerprint, h.baseline.revision)
        h.transport.reads.clear()
        h.transport.reads.add { alreadyEnabled }
        h.request = h.request.copy(expectedBaseline = alreadyEnabled)

        val result = h.executeValidationPulse()

        assertEquals(RidSwitchFailure.REQUEST_IS_NOT_A_TRANSITION, result.primaryFailure)
        assertEquals(0, h.transport.mutationCalls())
    }

    @Test
    fun `disable rejects a different active license even when state is enabled`() {
        val h = Harness(RequestedRidTransition.DISABLE)
        val other = h.baseline.copy(
            restorableState = h.baseline.restorableState.copy(activeLicenseFingerprint = fp("different-license")),
        )
        h.transport.reads.clear()
        h.transport.reads.add { other }
        h.request = h.request.copy(expectedBaseline = other)

        val result = h.executeValidationPulse()

        assertEquals(RidSwitchFailure.ACTIVE_LICENSE_MISMATCH, result.primaryFailure)
        assertEquals(0, h.transport.mutationCalls())
    }

    @Test
    fun `transition rejection still invokes one restore and final exact GET`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        h.transport.enableAction = { TransitionReceipt(false) }
        h.transport.reads.clear()
        h.transport.reads.add { h.baseline }
        h.transport.reads.add { restoredFrom(h.baseline, h.baseline.revision + 1) }

        val result = h.executeValidationPulse()

        assertEquals(RidValidationPulseStatus.FAILURE_AND_RESTORED, result.status)
        assertEquals(RidSwitchFailure.TRANSITION_REJECTED, result.primaryFailure)
        assertEquals(1, h.transport.enableCalls.get())
        assertEquals(1, h.transport.restoreCalls.get())
        assertEquals(2, h.transport.getCalls.get())
    }

    @Test
    fun `transition exception still invokes one restore and final exact GET`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        h.transport.enableAction = { throw IllegalStateException(SECRET) }
        h.transport.reads.clear()
        h.transport.reads.add { h.baseline }
        h.transport.reads.add { restoredFrom(h.baseline, h.baseline.revision + 1) }

        val result = h.executeValidationPulse()

        assertEquals(RidSwitchFailure.TRANSITION_CALL_FAILED, result.primaryFailure)
        assertEquals(RestorationStatus.EXACT_BASELINE_CONFIRMED, result.restoration)
        assertEquals(1, h.transport.restoreCalls.get())
        assertFalse(result.toString().contains(SECRET))
    }

    @Test
    fun `target GET exception restores exact baseline`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        h.transport.reads.clear()
        h.transport.reads.add { h.baseline }
        h.transport.reads.add { throw IllegalStateException(SECRET) }
        h.transport.reads.add { restoredFrom(h.baseline, h.baseline.revision + 2) }

        val result = h.executeValidationPulse()

        assertEquals(RidSwitchFailure.TARGET_READBACK_FAILED, result.primaryFailure)
        assertEquals(RidValidationPulseStatus.FAILURE_AND_RESTORED, result.status)
        assertEquals(1, h.transport.restoreCalls.get())
    }

    @Test
    fun `target GET must be exact across all fields and newer revision`() {
        val variants: (ExactRidUnlockSnapshot) -> List<ExactRidUnlockSnapshot> = { target ->
            listOf(
                target.copy(revision = target.revision - 1),
                target.copy(restorableState = target.restorableState.copy(policyProfileFingerprint = fp("wrong-policy"))),
                target.copy(restorableState = target.restorableState.copy(inventoryGeneration = 99L)),
                target.copy(restorableState = target.restorableState.copy(accountFingerprint = fp("wrong-account"))),
            )
        }

        val seed = Harness(RequestedRidTransition.ENABLE)
        for (wrong in variants(seed.targetSnapshot)) {
            val h = Harness(RequestedRidTransition.ENABLE)
            h.transport.reads.clear()
            h.transport.reads.add { h.baseline }
            h.transport.reads.add { wrong }
            h.transport.reads.add { restoredFrom(h.baseline, h.baseline.revision + 2) }
            val result = h.executeValidationPulse()
            assertEquals(RidSwitchFailure.TARGET_READBACK_MISMATCH, result.primaryFailure)
            assertEquals(1, h.transport.restoreCalls.get())
        }
    }

    @Test
    fun `pre-mutation cancellation is safe and does not restore`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        val cancellation = CancellationSource().apply { cancel() }

        val result = h.executeValidationPulse(cancellation)

        assertEquals(RidValidationPulseStatus.CANCELLED_WITHOUT_MUTATION, result.status)
        assertEquals(RidSwitchFailure.CANCELLED, result.primaryFailure)
        assertEquals(0, h.sessionProvider.calls.get())
        assertEquals(0, h.transport.totalCalls())
    }

    @Test
    fun `cancellation after transition is non-cancellable during restore and final reconcile`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        val cancellation = CancellationSource()
        h.transport.enableAction = {
            cancellation.cancel()
            TransitionReceipt(true)
        }
        h.transport.reads.clear()
        h.transport.reads.add { h.baseline }
        h.transport.reads.add { restoredFrom(h.baseline, h.baseline.revision + 2) }

        val result = h.executeValidationPulse(cancellation)

        assertEquals(RidValidationPulseStatus.CANCELLED_AND_RESTORED, result.status)
        assertEquals(1, h.transport.restoreCalls.get())
        assertTrue(h.transport.cleanupContexts.all { it.cleanup && !it.cancellation.isCancelled })
    }

    @Test
    fun `cancellation during target GET also restores`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        val cancellation = CancellationSource()
        h.transport.reads.clear()
        h.transport.reads.add { h.baseline }
        h.transport.reads.add {
            cancellation.cancel()
            h.targetSnapshot
        }
        h.transport.reads.add { restoredFrom(h.baseline, h.baseline.revision + 2) }

        val result = h.executeValidationPulse(cancellation)

        assertEquals(RidValidationPulseStatus.CANCELLED_AND_RESTORED, result.status)
        assertFalse(result.requestedTransitionObservedByExactGet)
        assertEquals(1, h.transport.restoreCalls.get())
    }

    @Test
    fun `overall deadline after mutation gets a separate bounded cleanup budget`() {
        val clock = FakeClock()
        val h = Harness(RequestedRidTransition.ENABLE, clock = clock)
        h.transport.enableAction = {
            clock.advance(2_000_000_000L)
            TransitionReceipt(true)
        }
        h.controller = h.newController(
            RidValidationPulseConfig(overallTimeoutNanos = 1_000_000_000L, cleanupTimeoutNanos = 500_000_000L),
        )
        h.transport.reads.clear()
        h.transport.reads.add { h.baseline }
        h.transport.reads.add { restoredFrom(h.baseline, h.baseline.revision + 2) }

        val result = h.executeValidationPulse()

        assertEquals(RidValidationPulseStatus.DEADLINE_AND_RESTORED, result.status)
        assertEquals(1, h.transport.restoreCalls.get())
        assertFalse(h.controller.isLockedOut)
    }

    @Test
    fun `bounded transition timeout forces lockout even if immediate final GET looks restored`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        h.controller = h.newController(
            RidValidationPulseConfig(overallTimeoutNanos = 20_000_000L, cleanupTimeoutNanos = 200_000_000L),
        )
        h.transport.enableAction = {
            Thread.sleep(5_000L)
            TransitionReceipt(true)
        }
        h.transport.reads.clear()
        h.transport.reads.add { h.baseline }
        h.transport.reads.add { restoredFrom(h.baseline, h.baseline.revision + 1) }

        val result = h.executeValidationPulse()

        assertEquals(RidValidationPulseStatus.LOCKED_OUT_UNCERTAIN_RESTORE, result.status)
        assertTrue(result.safetyLockout)
        assertTrue(h.controller.isLockedOut)
        assertEquals(1, h.transport.restoreCalls.get())
    }

    @Test
    fun `restore exception or rejected receipt is safe only when final GET proves exact baseline`() {
        val actions = listOf<() -> RestoreReceipt>(
            { throw IllegalStateException(SECRET) },
            { RestoreReceipt(false) },
        )
        for (restoreAction in actions) {
            val h = Harness(RequestedRidTransition.ENABLE)
            h.transport.restoreAction = restoreAction
            val result = h.executeValidationPulse()
            assertEquals(RidValidationPulseStatus.VERIFIED_TRANSITION_AND_RESTORED, result.status)
            assertEquals(RestorationStatus.EXACT_BASELINE_CONFIRMED, result.restoration)
            assertFalse(h.controller.isLockedOut)
        }
    }

    @Test
    fun `final GET mismatch locks controller and rejects every later request`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        h.transport.reads.clear()
        h.transport.reads.add { h.baseline }
        h.transport.reads.add { h.targetSnapshot }
        h.transport.reads.add { h.targetSnapshot.copy(revision = h.targetSnapshot.revision + 1) }

        val first = h.executeValidationPulse()

        assertEquals(RidValidationPulseStatus.LOCKED_OUT_UNCERTAIN_RESTORE, first.status)
        assertTrue(h.controller.isLockedOut)
        val callsBefore = h.transport.totalCalls()

        val secondCandidate = candidate(h.session)
        val second = h.controller.executeValidationPulse(
            RidSwitchRequest(RequestedRidTransition.ENABLE, secondCandidate, h.baseline),
        )
        assertEquals(RidSwitchFailure.LOCKED_OUT, second.primaryFailure)
        assertEquals(callsBefore, h.transport.totalCalls())
        assertTrue(secondCandidate.isClosed)
    }

    @Test
    fun `final GET exception locks controller`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        h.transport.reads.clear()
        h.transport.reads.add { h.baseline }
        h.transport.reads.add { h.targetSnapshot }
        h.transport.reads.add { throw IllegalStateException(SECRET) }

        val result = h.executeValidationPulse()

        assertEquals(RidValidationPulseStatus.LOCKED_OUT_UNCERTAIN_RESTORE, result.status)
        assertTrue(h.controller.isLockedOut)
    }

    @Test
    fun `cleanup deadline exhaustion locks controller`() {
        val clock = FakeClock()
        val h = Harness(RequestedRidTransition.ENABLE, clock = clock)
        h.controller = h.newController(
            RidValidationPulseConfig(overallTimeoutNanos = 1_000_000_000L, cleanupTimeoutNanos = 10L),
        )
        h.transport.restoreAction = {
            clock.advance(11L)
            RestoreReceipt(true)
        }

        val result = h.executeValidationPulse()

        assertEquals(RidValidationPulseStatus.LOCKED_OUT_UNCERTAIN_RESTORE, result.status)
        assertTrue(h.controller.isLockedOut)
    }

    @Test
    fun `single-flight rejects a concurrent request without touching transport`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        val entered = CountDownLatch(1)
        val release = CountDownLatch(1)
        h.transport.enableAction = {
            entered.countDown()
            assertTrue(release.await(2, TimeUnit.SECONDS))
            TransitionReceipt(true)
        }
        var firstResult: RidValidationPulseResult? = null
        val firstThread = Thread {
            firstResult = h.executeValidationPulse()
        }
        firstThread.start()
        assertTrue(entered.await(2, TimeUnit.SECONDS))
        val callsBefore = h.transport.totalCalls()

        val secondCandidate = candidate(h.session)
        val second = h.controller.executeValidationPulse(
            RidSwitchRequest(RequestedRidTransition.ENABLE, secondCandidate, h.baseline),
        )

        assertEquals(RidSwitchFailure.BUSY, second.primaryFailure)
        assertEquals(callsBefore, h.transport.totalCalls())
        assertTrue(secondCandidate.isClosed)
        release.countDown()
        firstThread.join(2_000L)
        assertNotNull(firstResult)
        assertEquals(RidValidationPulseStatus.VERIFIED_TRANSITION_AND_RESTORED, firstResult!!.status)
    }

    @Test
    fun `caller interruption is restored only after fail-safe cleanup`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        var result: RidValidationPulseResult? = null
        var interruptedAfterReturn = false
        val thread = Thread {
            Thread.currentThread().interrupt()
            result = h.executeValidationPulse()
            interruptedAfterReturn = Thread.currentThread().isInterrupted
        }
        thread.start()
        thread.join(2_000L)

        assertNotNull(result)
        assertEquals(RidValidationPulseStatus.CANCELLED_WITHOUT_MUTATION, result!!.status)
        assertTrue(interruptedAfterReturn)
        assertEquals(0, h.transport.mutationCalls())
    }

    @Test
    fun `redacted audit schema and public results never contain license ID or exception text`() {
        val h = Harness(RequestedRidTransition.ENABLE)
        h.audit.throwOnCode = AuditCode.RESTORE_ATTEMPTED

        val result = h.executeValidationPulse()
        val rendered = buildString {
            append(result)
            append(h.candidate)
            h.audit.events.forEach { append(it) }
        }

        assertFalse(rendered.contains(SECRET))
        assertFalse(rendered.contains("signed-envelope-payload"))
        assertEquals(RidValidationPulseStatus.VERIFIED_TRANSITION_AND_RESTORED, result.status)
        assertEquals(1, h.transport.restoreCalls.get())
    }

    @Test
    fun `transport API contains no generic raw write or boolean setter`() {
        val names = RidUnlockTransport::class.java.declaredMethods.map { it.name.lowercase() }
        assertFalse(names.any { it.contains("raw") || it.contains("socket") || it.contains("cloud") })
        assertFalse(names.any { it.startsWith("set") || it == "write" || it.contains("command") })
        assertEquals(
            setOf(
                "getexactridunlockstate",
                "requestenableverifiedridunlock",
                "requestdisableverifiedridunlock",
                "restoreexactridunlockbaseline",
            ),
            names.toSet(),
        )
    }

    @Test
    fun `timeouts are hard capped by configuration`() {
        expectIllegalArgument { RidValidationPulseConfig(overallTimeoutNanos = 0L) }
        expectIllegalArgument {
            RidValidationPulseConfig(
                overallTimeoutNanos = RidValidationPulseConfig.MAX_OVERALL_TIMEOUT_NANOS + 1,
            )
        }
        expectIllegalArgument { RidValidationPulseConfig(cleanupTimeoutNanos = 0L) }
        expectIllegalArgument {
            RidValidationPulseConfig(
                cleanupTimeoutNanos = RidValidationPulseConfig.MAX_CLEANUP_TIMEOUT_NANOS + 1,
            )
        }
    }

    @Test
    fun `deadline arithmetic remains bounded across negative nanoTime origin and overflow`() {
        val negative = MonotonicClock { Long.MIN_VALUE + 100L }
        val regular = Deadline.after(negative, 50L)
        assertEquals(50L, regular.remainingNanos(negative))

        val nearMaximum = MonotonicClock { Long.MAX_VALUE - 5L }
        val saturated = Deadline.after(nearMaximum, 10L)
        assertEquals(5L, saturated.remainingNanos(nearMaximum))
    }

    private class Harness(
        target: RequestedRidTransition,
        family: FlySafeProtocolFamily = FlySafeProtocolFamily.V4,
        val clock: FakeClock = FakeClock(),
        candidateOverride: RidUnlockInventoryCandidate? = null,
    ) {
        val session = defaultSession(family = family)
        val sessionProvider = FakeSessionProvider(SessionInspection.Known(session))
        val verifier = FakeVerifier()
        val audit = CollectingAudit()
        val candidate = candidateOverride ?: candidate(session)
        val licenseFingerprint = candidateFingerprint()
        val baseline = when (target) {
            RequestedRidTransition.ENABLE -> disabledBaseline(session)
            RequestedRidTransition.DISABLE -> enabledBaseline(session, licenseFingerprint)
        }
        val targetSnapshot = when (target) {
            RequestedRidTransition.ENABLE -> enabledFrom(baseline, licenseFingerprint, baseline.revision + 1)
            RequestedRidTransition.DISABLE -> disabledFrom(baseline, baseline.revision + 1)
        }
        val transport = ScriptedTransport().apply {
            reads.add { baseline }
            reads.add { targetSnapshot }
            reads.add { restoredFrom(baseline, baseline.revision + 2) }
        }
        var request = RidSwitchRequest(target, candidate, baseline)
        var controller = newController()

        fun newController(config: RidValidationPulseConfig = RidValidationPulseConfig()): RidValidationPulseController =
            RidValidationPulseController(
                sessionProvider = sessionProvider,
                verifier = verifier,
                transport = transport,
                monotonicClock = clock,
                epochClock = EpochClock { NOW },
                audit = audit,
                config = config,
            )

        fun executeValidationPulse(cancellation: CancellationToken = CancellationSource()): RidValidationPulseResult =
            controller.executeValidationPulse(request, cancellation)

        private fun candidateFingerprint(): OpaqueFingerprint = OpaqueFingerprint.sha256(SECRET.toByteArray())
    }

    private class FakeClock : MonotonicClock {
        private val value = AtomicLong(1_000L)
        override fun nowNanos(): Long = value.get()
        fun advance(nanos: Long) = value.addAndGet(nanos)
    }

    private class FakeSessionProvider(var inspection: SessionInspection) : FlySafeSessionProvider {
        val calls = AtomicInteger()
        var failure: Throwable? = null
        override fun inspect(context: CallContext): SessionInspection {
            calls.incrementAndGet()
            failure?.let { throw it }
            return inspection
        }
    }

    private class FakeVerifier : RidUnlockProvenanceVerifier() {
        val calls = AtomicInteger()
        var signatureValid = true
        var inventoryMember = true
        var failure: Throwable? = null

        override fun verifyCryptographicSignatureAndInventoryProvenance(
            material: VerificationMaterial,
            candidate: RidUnlockInventoryCandidate,
            session: KnownFlySafeSession,
            context: CallContext,
        ): CryptographicVerdict {
            calls.incrementAndGet()
            failure?.let { throw it }
            // Exercise scoped sensitive access without retaining it.
            assertTrue(material.useLicenseId { it.isNotEmpty() })
            assertTrue(material.useSignedEnvelope { it.isNotEmpty() })
            return CryptographicVerdict(signatureValid, inventoryMember)
        }
    }

    private class ScriptedTransport : RidUnlockTransport {
        val reads = ConcurrentLinkedQueue<() -> ExactRidUnlockSnapshot>()
        val getCalls = AtomicInteger()
        val enableCalls = AtomicInteger()
        val disableCalls = AtomicInteger()
        val restoreCalls = AtomicInteger()
        val cleanupContexts = CopyOnWriteArrayList<CallContext>()
        val transitionLicenses = CopyOnWriteArrayList<VerifiedRidUnlockLicense>()
        val restoreLicenses = CopyOnWriteArrayList<VerifiedRidUnlockLicense>()
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
            assertEquals(RID_UNLOCK_TYPE_CODE, license.typeCode)
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
            assertEquals(RID_UNLOCK_TYPE_CODE, license.typeCode)
            license.useLicenseId { assertTrue(it.isNotEmpty()) }
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
            license.useLicenseId { assertTrue(it.isNotEmpty()) }
            cleanupContexts.add(context)
            return restoreAction()
        }

        fun mutationCalls(): Int = enableCalls.get() + disableCalls.get()
        fun totalCalls(): Int = getCalls.get() + mutationCalls() + restoreCalls.get()
    }

    private class CollectingAudit : RedactedAuditSink {
        val events = CopyOnWriteArrayList<RedactedAuditEvent>()
        var throwOnCode: AuditCode? = null
        override fun record(event: RedactedAuditEvent) {
            if (event.code == throwOnCode) throw IllegalStateException(SECRET)
            events.add(event)
        }
    }

    companion object {
        private const val NOW = 2_000_000_000L
        private const val SECRET = "license-secret-123"

        private fun fp(label: String): OpaqueFingerprint = OpaqueFingerprint.sha256(label.toByteArray())

        private fun defaultSession(
            family: FlySafeProtocolFamily = FlySafeProtocolFamily.V4,
            authentication: SessionAuthentication = SessionAuthentication.AUTHENTICATED,
            serverAttested: Boolean = true,
        ) = KnownFlySafeSession(
            family = family,
            authentication = authentication,
            serverAttested = serverAttested,
            sessionFingerprint = fp("session-$family"),
            accountFingerprint = fp("account"),
            aircraftFingerprint = fp("aircraft"),
        )

        private fun defaultBinding(session: KnownFlySafeSession) = InventoryBinding(
            accountFingerprint = session.accountFingerprint,
            aircraftFingerprint = session.aircraftFingerprint,
            family = session.family,
        )

        private fun candidate(
            session: KnownFlySafeSession,
            typeCode: Int = RID_UNLOCK_TYPE_CODE,
            origin: InventoryOrigin = InventoryOrigin.OFFICIAL_SIGNED_ACCOUNT_INVENTORY,
            scheme: InventorySignatureScheme = InventorySignatureScheme.DJI_FLYSAFE_SIGNED_ENVELOPE,
            binding: InventoryBinding = defaultBinding(session),
            validFrom: Long = NOW - 100,
            validUntil: Long = NOW + 100,
            envelope: ByteArray = "signed-envelope-payload".toByteArray(),
        ) = RidUnlockInventoryCandidate.consumeCopies(
            licenseId = SECRET.toByteArray(),
            signedEnvelope = envelope,
            typeCode = typeCode,
            origin = origin,
            signatureScheme = scheme,
            binding = binding,
            validFromEpochSeconds = validFrom,
            validUntilEpochSeconds = validUntil,
        )

        private fun restorable(
            session: KnownFlySafeSession,
            activation: RidActivation,
            license: OpaqueFingerprint?,
        ) = RidRestorableState(
            activation = activation,
            activeLicenseFingerprint = license,
            sessionFingerprint = session.sessionFingerprint,
            accountFingerprint = session.accountFingerprint,
            aircraftFingerprint = session.aircraftFingerprint,
            policyProfileFingerprint = fp("policy-profile"),
            inventoryGeneration = 7L,
        )

        private fun disabledBaseline(session: KnownFlySafeSession) = ExactRidUnlockSnapshot(
            restorableState = restorable(session, RidActivation.DISABLED, null),
            revision = 10L,
        )

        private fun enabledBaseline(
            session: KnownFlySafeSession,
            license: OpaqueFingerprint,
        ) = ExactRidUnlockSnapshot(
            restorableState = restorable(session, RidActivation.ENABLED, license),
            revision = 10L,
        )

        private fun enabledFrom(
            baseline: ExactRidUnlockSnapshot,
            license: OpaqueFingerprint,
            revision: Long,
        ) = baseline.copy(
            restorableState = baseline.restorableState.copy(
                activation = RidActivation.ENABLED,
                activeLicenseFingerprint = license,
            ),
            revision = revision,
        )

        private fun disabledFrom(baseline: ExactRidUnlockSnapshot, revision: Long) = baseline.copy(
            restorableState = baseline.restorableState.copy(
                activation = RidActivation.DISABLED,
                activeLicenseFingerprint = null,
            ),
            revision = revision,
        )

        private fun restoredFrom(baseline: ExactRidUnlockSnapshot, revision: Long) =
            baseline.copy(revision = revision)

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
