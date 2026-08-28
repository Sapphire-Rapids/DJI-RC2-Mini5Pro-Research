package com.finduas.ridobserver

import org.junit.Assert.assertEquals
import org.junit.Test

class ProtocolBinderProbePolicyTest {
    @Test
    fun reportsMatchingReachableService() {
        assertEquals(
            ProtocolBinderProbeState.SERVICE_AVAILABLE,
            ProtocolBinderProbePolicy.classify(
                ProtocolBinderEvidence(
                    servicePresent = true,
                    binderReachable = true,
                    descriptorRead = true,
                    descriptorMatches = true
                )
            )
        )
    }

    @Test
    fun distinguishesAbsentAndDenied() {
        assertEquals(
            ProtocolBinderProbeState.SERVICE_ABSENT,
            ProtocolBinderProbePolicy.classify(ProtocolBinderEvidence())
        )
        assertEquals(
            ProtocolBinderProbeState.LOOKUP_DENIED,
            ProtocolBinderProbePolicy.classify(
                ProtocolBinderEvidence(failure = ProtocolBinderFailure.LOOKUP_SECURITY)
            )
        )
    }

    @Test
    fun doesNotPromoteDescriptorMismatch() {
        assertEquals(
            ProtocolBinderProbeState.DESCRIPTOR_MISMATCH,
            ProtocolBinderProbePolicy.classify(
                ProtocolBinderEvidence(
                    servicePresent = true,
                    binderReachable = true,
                    descriptorRead = true,
                    descriptorMatches = false
                )
            )
        )
    }
}
