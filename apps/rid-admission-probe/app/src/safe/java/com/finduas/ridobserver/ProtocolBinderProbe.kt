package com.finduas.ridobserver

import android.annotation.SuppressLint
import android.os.IBinder
import java.lang.reflect.InvocationTargetException

internal enum class ProtocolBinderProbeState {
    NOT_RUN,
    SERVICE_AVAILABLE,
    SERVICE_ABSENT,
    HIDDEN_API_BLOCKED,
    LOOKUP_DENIED,
    BINDER_UNREACHABLE,
    DESCRIPTOR_DENIED,
    DESCRIPTOR_MISMATCH,
    INTERNAL_ERROR
}

internal data class ProtocolBinderProbeResult(
    val state: ProtocolBinderProbeState = ProtocolBinderProbeState.NOT_RUN
)

internal enum class ProtocolBinderFailure {
    HIDDEN_API,
    LOOKUP_SECURITY,
    DESCRIPTOR_SECURITY,
    INTERNAL
}

internal data class ProtocolBinderEvidence(
    val servicePresent: Boolean = false,
    val binderReachable: Boolean = false,
    val descriptorRead: Boolean = false,
    val descriptorMatches: Boolean = false,
    val failure: ProtocolBinderFailure? = null
)

internal object ProtocolBinderProbePolicy {
    fun classify(evidence: ProtocolBinderEvidence): ProtocolBinderProbeState {
        evidence.failure?.let {
            return when (it) {
                ProtocolBinderFailure.HIDDEN_API -> ProtocolBinderProbeState.HIDDEN_API_BLOCKED
                ProtocolBinderFailure.LOOKUP_SECURITY -> ProtocolBinderProbeState.LOOKUP_DENIED
                ProtocolBinderFailure.DESCRIPTOR_SECURITY ->
                    ProtocolBinderProbeState.DESCRIPTOR_DENIED
                ProtocolBinderFailure.INTERNAL -> ProtocolBinderProbeState.INTERNAL_ERROR
            }
        }
        if (!evidence.servicePresent) return ProtocolBinderProbeState.SERVICE_ABSENT
        if (!evidence.binderReachable) return ProtocolBinderProbeState.BINDER_UNREACHABLE
        if (!evidence.descriptorRead) return ProtocolBinderProbeState.INTERNAL_ERROR
        return if (evidence.descriptorMatches) {
            ProtocolBinderProbeState.SERVICE_AVAILABLE
        } else {
            ProtocolBinderProbeState.DESCRIPTOR_MISMATCH
        }
    }
}

/**
 * One non-mutating lookup of DJI's optional framework Binder.
 *
 * It deliberately stops at ServiceManager.checkService(), pingBinder(), and
 * getInterfaceDescriptor(). It never creates a Parcel, invokes an application
 * transaction, registers a listener, opens a socket, or sends a DUML frame.
 */
internal object ProtocolBinderProbe {
    private const val SERVICE_NAME = "protocol"
    private const val EXPECTED_DESCRIPTOR = "com.dji.protocol.IProtocolManager"

    private enum class Stage { HIDDEN_API, LOOKUP, DESCRIPTOR }

    @SuppressLint("DiscouragedPrivateApi", "PrivateApi")
    fun runOnce(): ProtocolBinderProbeResult {
        var stage = Stage.HIDDEN_API
        return try {
            val serviceManager = Class.forName("android.os.ServiceManager")
            val checkService = serviceManager.getDeclaredMethod(
                "checkService",
                String::class.java
            )
            stage = Stage.LOOKUP
            val binder = checkService.invoke(null, SERVICE_NAME) as? IBinder
                ?: return result(ProtocolBinderEvidence())
            if (!binder.pingBinder()) {
                return result(ProtocolBinderEvidence(servicePresent = true))
            }
            stage = Stage.DESCRIPTOR
            val descriptor = binder.interfaceDescriptor
            result(
                ProtocolBinderEvidence(
                    servicePresent = true,
                    binderReachable = true,
                    descriptorRead = true,
                    descriptorMatches = descriptor == EXPECTED_DESCRIPTOR
                )
            )
        } catch (error: Throwable) {
            val cause = if (error is InvocationTargetException) {
                error.targetException ?: error
            } else {
                error
            }
            val failure = when {
                cause is SecurityException && stage == Stage.HIDDEN_API ->
                    ProtocolBinderFailure.HIDDEN_API
                cause is SecurityException && stage == Stage.LOOKUP ->
                    ProtocolBinderFailure.LOOKUP_SECURITY
                cause is SecurityException && stage == Stage.DESCRIPTOR ->
                    ProtocolBinderFailure.DESCRIPTOR_SECURITY
                cause is ClassNotFoundException || cause is NoSuchMethodException ||
                    cause is IllegalAccessException -> ProtocolBinderFailure.HIDDEN_API
                else -> ProtocolBinderFailure.INTERNAL
            }
            result(ProtocolBinderEvidence(failure = failure))
        }
    }

    private fun result(evidence: ProtocolBinderEvidence): ProtocolBinderProbeResult =
        ProtocolBinderProbeResult(ProtocolBinderProbePolicy.classify(evidence))
}
