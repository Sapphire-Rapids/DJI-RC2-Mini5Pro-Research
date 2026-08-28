package com.finduas.ridobserver

import org.junit.Assert.assertEquals
import org.junit.Test

class ProbeCompletionPolicyTest {
    @Test
    fun completeRequiresBothV08ChecksAndArtIdentity() {
        assertEquals(
            ProbeRunState.COMPLETE,
            ProbeCompletionPolicy.terminalState(
                protocolBinderCompleted = true,
                localBridgeCompleted = true,
                artIdentityState = ArtIdentityState.COMPLETE
            )
        )
        for (protocol in listOf(false, true)) {
            for (bridge in listOf(false, true)) {
                for (artComplete in listOf(false, true)) {
                    if (protocol && bridge && artComplete) continue
            assertEquals(
                ProbeRunState.INCOMPLETE,
                ProbeCompletionPolicy.terminalState(
                            protocolBinderCompleted = protocol,
                            localBridgeCompleted = bridge,
                            artIdentityState = if (artComplete) {
                                ArtIdentityState.COMPLETE
                            } else {
                                ArtIdentityState.MAPS_CHANGED_DURING_READ
                            }
                        )
                    )
                }
            }
        }
    }

    @Test
    fun activityRecreationGateRejectsASecondRunningProbe() {
        assertEquals(false, ProbeRunAdmissionPolicy.mayStart(ProbeRunState.RUNNING))
        for (state in listOf(
            ProbeRunState.NOT_RUN,
            ProbeRunState.INCOMPLETE,
            ProbeRunState.COMPLETE
        )) {
            assertEquals(true, ProbeRunAdmissionPolicy.mayStart(state))
        }
    }
}
