package com.finduas.ridswitch

internal fun validateAdmittedBaseline(
    target: RequestedRidTransition,
    snapshot: ExactRidUnlockSnapshot,
    session: KnownFlySafeSession,
    license: VerifiedRidUnlockLicense,
): RidSwitchFailure? {
    val state = snapshot.restorableState
    if (
        state.sessionFingerprint != session.sessionFingerprint ||
        state.accountFingerprint != session.accountFingerprint ||
        state.aircraftFingerprint != session.aircraftFingerprint
    ) {
        return RidSwitchFailure.BASELINE_MISMATCH
    }

    return when (target) {
        RequestedRidTransition.ENABLE -> {
            if (state.activation != RidActivation.DISABLED) {
                RidSwitchFailure.REQUEST_IS_NOT_A_TRANSITION
            } else {
                null
            }
        }
        RequestedRidTransition.DISABLE -> when {
            state.activation != RidActivation.ENABLED -> RidSwitchFailure.REQUEST_IS_NOT_A_TRANSITION
            state.activeLicenseFingerprint != license.licenseFingerprint ->
                RidSwitchFailure.ACTIVE_LICENSE_MISMATCH
            else -> null
        }
    }
}

internal fun exactTargetMatches(
    target: RequestedRidTransition,
    license: VerifiedRidUnlockLicense,
    baseline: ExactRidUnlockSnapshot,
    observed: ExactRidUnlockSnapshot,
): Boolean {
    if (observed.revision <= baseline.revision) return false
    val expectedActivation = when (target) {
        RequestedRidTransition.ENABLE -> RidActivation.ENABLED
        RequestedRidTransition.DISABLE -> RidActivation.DISABLED
    }
    val expectedLicense = when (target) {
        RequestedRidTransition.ENABLE -> license.licenseFingerprint
        RequestedRidTransition.DISABLE -> null
    }
    return observed.restorableState == baseline.restorableState.copy(
        activation = expectedActivation,
        activeLicenseFingerprint = expectedLicense,
    )
}
