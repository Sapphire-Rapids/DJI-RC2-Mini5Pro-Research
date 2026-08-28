package com.finduas.ridobserver

import org.junit.Assert.assertEquals
import org.junit.Test

class UpgradeRecoveryMarkerPolicyTest {
    @Test
    fun recognizesClearAndSet() {
        assertEquals(
            UpgradeRecoveryMarkerState.CLEAR,
            UpgradeRecoveryMarkerPolicy.classify("0")
        )
        assertEquals(
            UpgradeRecoveryMarkerState.CLEAR,
            UpgradeRecoveryMarkerPolicy.classify("")
        )
        assertEquals(
            UpgradeRecoveryMarkerState.SET,
            UpgradeRecoveryMarkerPolicy.classify("1")
        )
    }

    @Test
    fun failsClosedForUnexpectedValue() {
        assertEquals(
            UpgradeRecoveryMarkerState.OTHER,
            UpgradeRecoveryMarkerPolicy.classify("unexpected")
        )
    }
}
