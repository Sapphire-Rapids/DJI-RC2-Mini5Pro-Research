package com.finduas.rc2ridadmin;

import android.os.Binder;
import android.os.IBinder;
import android.os.IInterface;
import android.os.Parcel;
import android.os.RemoteException;
import android.os.SystemClock;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Locale;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/** Minimal client for the stock RC331 IProtocolManager v10 Binder ABI. */
final class DjiProtocolClient {
    private static final String SERVICE_NAME = "protocol";
    private static final String MANAGER_DESCRIPTOR = "com.dji.protocol.IProtocolManager";
    private static final String LISTENER_DESCRIPTOR = "com.dji.protocol.IPackListener";

    private static final int TRANSACTION_IS_ENABLE = 1;
    private static final int TRANSACTION_ADD_PACK_LISTENER = 2;
    private static final int TRANSACTION_SEND_WITH_LISTEN = 4;
    private static final int CALLBACK_SUCCESS = 1;
    private static final int CALLBACK_FAILURE = 2;

    static final int CMD_SET_FLYC = 0x03;
    static final int CMD_SET_ADSB = 0x11;
    private static final int RID_COMMAND_TIMEOUT_MS = 500;
    private static final int PARAM_COMMAND_TIMEOUT_MS = 1000;
    static final int FLYSAFE_COMMAND_TIMEOUT_MS = 6000;
    private static final int RC331_ACT_QUEUE_RETRY_COUNT = 2;
    private static final int FLYSAFE_SET_APPLICATION_RETRY_COUNT = 0;

    static final int CMD_EID_SWITCH = 0x77;
    static final int CMD_OPERATOR_ID = 0x78;
    static final int CMD_PARAM_INFO_BY_HASH = 0xF7;
    static final int CMD_PARAM_READ_BY_HASH = 0xF8;
    static final int CMD_PARAM_WRITE_BY_HASH = 0xF9;
    static final int CMD_RID_WORKING_STATUS = 0x1C;
    static final int CMD_FLYSAFE_LICENSE_LIST = 0x11;
    static final int CMD_FLYSAFE_SET_LICENSE_ENABLED = 0x12;
    static final int CMD_FLYSAFE_AREA_INFO = 0x09;
    static final int CMD_FLYSAFE_WHITELIST_INFO = 0x42;

    interface CancellationCheck {
        boolean isCancelled();
    }

    /** Query-only proof type. It is deliberately not usable as an 11/12 write dispatch. */
    private interface FlysafeQueryAuthorization {
        void authorize(DjiProtocolClient candidate, Route route, byte[] payload);
    }

    static final Route MODERN_FC4 =
            new Route("modern-app4-fc4", 0x04, 0x02, 0x04, 0x12);
    static final Route MODERN_FLYSAFE_FC4 =
            new Route("modern-flysafe-app4-fc4", 0x04, 0x02, 0x04, 0x12);
    static final Route RC2_LEGACY_FC =
            new Route("rc2-mobile5-fc", 0x05, 0x0A, 0x00, 0x03);

    /** Process-wide lane shared by modern 11/11 queries and the drain-sensitive 11/12 SET. */
    private static final FlysafeCommandLane FLYSAFE_COMMAND_LANE =
            new FlysafeCommandLane();

    static final class Route {
        final String label;
        final int senderId;
        final int senderType;
        final int receiverId;
        final int receiverType;

        Route(
                String label,
                int senderId,
                int senderType,
                int receiverId,
                int receiverType) {
            this.label = label;
            this.senderId = senderId;
            this.senderType = senderType;
            this.receiverId = receiverId;
            this.receiverType = receiverType;
        }

        String summary() {
            return String.format(Locale.US, "%s %02X:%02X>%02X:%02X",
                    label,
                    senderType & 0xff,
                    senderId & 0xff,
                    receiverType & 0xff,
                    receiverId & 0xff);
        }
    }

    static final class Reply {
        final boolean callbackSuccess;
        final String failure;
        final int cmdId;
        final int ccode;
        final byte[] data;
        final String diagnostic;

        Reply(boolean callbackSuccess, String failure, int cmdId, int ccode, byte[] data,
                String diagnostic) {
            this.callbackSuccess = callbackSuccess;
            this.failure = failure;
            this.cmdId = cmdId;
            this.ccode = ccode;
            this.data = data == null ? null : Arrays.copyOf(data, data.length);
            this.diagnostic = diagnostic;
        }

        Reply withDiagnosticPrefix(String prefix) {
            String combined = diagnostic == null || diagnostic.isEmpty()
                    ? prefix : prefix + "; " + diagnostic;
            return new Reply(callbackSuccess, failure, cmdId, ccode, data, combined);
        }

        /** Privacy-reduced failure details for the active read-only 11/11 result. */
        String displayDirectReadonlyFailure() {
            return "failure=" + diagnosticText(failure)
                    + "; ccode_or_ecode=" + ccode
                    + "; diagnostic=" + diagnosticText(diagnostic);
        }

        private static String diagnosticText(String value) {
            if (value == null || value.isEmpty()) {
                return "<none>";
            }
            String clean = DirectDiagnosticReport.cleanSingleLine(value);
            return clean.length() <= 4096 ? clean : clean.substring(0, 4096) + "…";
        }
    }

    static final class RidStatusObservation {
        final RidStatusTimeline.Snapshot timeline;
        final String diagnostic;

        RidStatusObservation(
                RidStatusTimeline.Snapshot timeline,
                String diagnostic) {
            this.timeline = timeline;
            this.diagnostic = diagnostic;
        }

        String display() {
            StringBuilder result = new StringBuilder(timeline.display());
            if (diagnostic != null && !diagnostic.isEmpty()) {
                result.append("\n\nRID LISTEN DIAG: ").append(diagnostic);
            }
            return result.toString();
        }
    }

    static final class FlysafeGateObservation {
        private final DjiProtocolClient owner;
        final FlysafeProtocolGate.Snapshot snapshot;
        final String diagnostic;
        private final Object sessionMarker = new Object();
        private final CancellationCheck cancellationCheck;
        private FlysafeInventoryPass activeInventoryPass;
        private int completedInventoryPasses;
        private int inventoryPassAttemptsAtStage;
        private int mutationAttempts;
        private boolean recoveryMode;
        private boolean forwardTargetConfirmed;
        private boolean safelyAtBaseline;
        private boolean interruptObserved;
        private boolean cancellationObserved;
        private boolean active;

        private FlysafeGateObservation(
                DjiProtocolClient owner,
                FlysafeProtocolGate.Snapshot snapshot,
                String diagnostic,
                boolean permitAllowed,
                CancellationCheck cancellationCheck) {
            this.owner = owner;
            this.snapshot = snapshot;
            this.diagnostic = diagnostic;
            this.cancellationCheck = cancellationCheck;
            this.active = permitAllowed && snapshot.allowsModernInventory();
            this.safelyAtBaseline = true;
        }

        String display() {
            StringBuilder result = new StringBuilder(snapshot.display());
            if (snapshot.allowsModernInventory() && !allowsModernInventory()) {
                result.append("\n本次 gate 虽形成候选状态，但未在有效窗口内签发查询 permit；"
                        + "11/11 request count=0。");
            }
            return result.toString();
        }

        private synchronized boolean isActiveFor(DjiProtocolClient candidate) {
            return active && owner == candidate && snapshot.allowsModernInventory();
        }

        private synchronized Object sessionMarkerFor(DjiProtocolClient candidate) {
            requireActiveSession(candidate, true);
            return sessionMarker;
        }

        private synchronized int writeCapabilityVersionFor(
                DjiProtocolClient candidate,
                Object candidateSessionMarker) {
            requireActiveSession(candidate, mutationAttempts == 0);
            if (candidateSessionMarker == null || sessionMarker != candidateSessionMarker) {
                invalidateOnlyBeforeRecovery();
                throw new IllegalStateException("FLYSAFE_WRITE_SESSION_TOKEN_MISMATCH");
            }
            Integer version = snapshot.getVersion();
            if (!Boolean.TRUE.equals(snapshot.getSupported())
                    || version == null
                    || (version != 1 && version != 2)) {
                invalidateOnlyBeforeRecovery();
                throw new IllegalStateException("FLYSAFE_WRITE_CAPABILITY_NOT_ADMITTED");
            }
            return version;
        }

        private synchronized Route writeRouteFor(
                DjiProtocolClient candidate,
                Object candidateSessionMarker) {
            writeCapabilityVersionFor(candidate, candidateSessionMarker);
            if (!snapshot.hasProduct139ModernReverseRoute()) {
                invalidateOnlyBeforeRecovery();
                throw new IllegalStateException("FLYSAFE_WRITE_REVERSE_ROUTE_NOT_ADMITTED");
            }
            FlysafeProtocolGate.ReversedRoute observed = snapshot.getReversedRoute();
            if (observed == null) {
                invalidateOnlyBeforeRecovery();
                throw new IllegalStateException("FLYSAFE_WRITE_REVERSE_ROUTE_MISSING");
            }
            Route route = new Route(
                    "gated-flysafe-set",
                    observed.getSenderId(),
                    observed.getSenderType(),
                    observed.getReceiverId(),
                    observed.getReceiverType());
            if (!isModernFlysafeSetRoute(route)) {
                invalidateOnlyBeforeRecovery();
                throw new IllegalStateException("FLYSAFE_WRITE_REVERSE_ROUTE_CHANGED");
            }
            return route;
        }

        private void requireActiveSession(
                DjiProtocolClient candidate,
                boolean cancelBeforeMutation) {
            if (!active || owner != candidate || !snapshot.allowsModernInventory()) {
                throw new IllegalStateException("FLYSAFE_GATE_PERMIT_MISSING_OR_CONSUMED");
            }
            boolean cancelled = cancellationCheck != null && cancellationCheck.isCancelled();
            boolean interrupted = Thread.currentThread().isInterrupted();
            cancellationObserved |= cancelled;
            interruptObserved |= interrupted;
            if (!recoveryMode && cancelBeforeMutation && (cancelled || interrupted)) {
                active = false;
                throw new IllegalStateException(cancelled
                        ? "FLYSAFE_GATE_OPERATION_CANCELLED"
                        : "FLYSAFE_QUERY_THREAD_INTERRUPTED");
            }
        }

        private synchronized FlysafeInventoryPass beginInventoryPass(
                DjiProtocolClient candidate,
                Object candidateSessionMarker) {
            requireActiveSession(candidate, mutationAttempts == 0);
            if (candidateSessionMarker == null || candidateSessionMarker != sessionMarker) {
                invalidateOnlyBeforeRecovery();
                throw new IllegalStateException("FLYSAFE_INVENTORY_SESSION_TOKEN_MISMATCH");
            }
            if (activeInventoryPass != null && activeInventoryPass.isActive()) {
                invalidateOnlyBeforeRecovery();
                throw new IllegalStateException("FLYSAFE_INVENTORY_PASS_ALREADY_ACTIVE");
            }
            if (completedInventoryPasses != mutationAttempts) {
                invalidateOnlyBeforeRecovery();
                throw new IllegalStateException("FLYSAFE_INVENTORY_PASS_ORDER_INVALID");
            }
            if (completedInventoryPasses >= 3 || mutationAttempts > 2) {
                invalidateOnlyBeforeRecovery();
                throw new IllegalStateException("FLYSAFE_INVENTORY_PASS_LIMIT_EXCEEDED");
            }
            Route route = writeRouteFor(candidate, candidateSessionMarker);
            FlysafeInventoryPass pass = new FlysafeInventoryPass(
                    candidate,
                    this,
                    candidateSessionMarker,
                    route,
                    completedInventoryPasses);
            activeInventoryPass = pass;
            if (inventoryPassAttemptsAtStage < Integer.MAX_VALUE) {
                inventoryPassAttemptsAtStage++;
            }
            return pass;
        }

        private synchronized void completeInventoryPass(
                DjiProtocolClient candidate,
                FlysafeInventoryPass pass,
                FlysafeRidInventory.Result canonicalResult) {
            requireActiveSession(candidate, mutationAttempts == 0);
            if (pass == null || activeInventoryPass != pass || !pass.belongsTo(
                    candidate, this, sessionMarker, completedInventoryPasses)) {
                invalidateOnlyBeforeRecovery();
                throw new IllegalStateException("FLYSAFE_INVENTORY_PASS_IDENTITY_MISMATCH");
            }
            activeInventoryPass = null;
            pass.finishLocally();
            if (canonicalResult == null
                    || canonicalResult.isClosed()
                    || pass.getRequestCount() != canonicalResult.getPageCalls() + 1) {
                if (!recoveryMode) {
                    active = false;
                }
                throw new IllegalStateException("FLYSAFE_INVENTORY_NOT_CANONICAL");
            }
            completedInventoryPasses++;
            if (mutationAttempts == 0) {
                // The baseline pass is committed immediately. Recovery-stage passes remain
                // provisional until the exact opaque target is classified below; a transient
                // full-inventory mismatch may then be replaced by another read-only pass.
                inventoryPassAttemptsAtStage = 0;
            }
        }

        private synchronized void abortInventoryPass(FlysafeInventoryPass pass) {
            if (activeInventoryPass != pass) {
                return;
            }
            activeInventoryPass = null;
            if (!recoveryMode) {
                active = false;
            }
        }

        private synchronized Route beginMutationForWrite(
                DjiProtocolClient candidate,
                Object candidateSessionMarker,
                FlysafeRidInventory.OpaqueRidHandle target,
                boolean requestedEnabled) {
            requireActiveSession(candidate, mutationAttempts == 0);
            if (candidateSessionMarker == null || candidateSessionMarker != sessionMarker
                    || target == null) {
                invalidateOnlyBeforeRecovery();
                throw new IllegalStateException("FLYSAFE_WRITE_SESSION_OR_TARGET_MISMATCH");
            }
            if (activeInventoryPass != null && activeInventoryPass.isActive()) {
                invalidateOnlyBeforeRecovery();
                throw new IllegalStateException("FLYSAFE_WRITE_DURING_INVENTORY_PASS");
            }
            if (completedInventoryPasses != mutationAttempts + 1 || mutationAttempts >= 2) {
                invalidateOnlyBeforeRecovery();
                throw new IllegalStateException("FLYSAFE_WRITE_ORDER_INVALID");
            }
            boolean baselineEnabled = target.wasEnabled();
            if (mutationAttempts == 0) {
                if (requestedEnabled == baselineEnabled) {
                    invalidateOnlyBeforeRecovery();
                    throw new IllegalStateException("FLYSAFE_FORWARD_IS_NOT_A_TRANSITION");
                }
                // This synchronized point is the last cancellable boundary. Once a possible SET
                // is admitted, cancellation and interrupt only request prompt recovery; they can
                // no longer invalidate the route/session needed for readback and restoration.
                safelyAtBaseline = false;
                recoveryMode = true;
            } else {
                if (!forwardTargetConfirmed || requestedEnabled != baselineEnabled) {
                    invalidateOnlyBeforeRecovery();
                    throw new IllegalStateException("FLYSAFE_RESTORE_NOT_ADMITTED");
                }
            }
            mutationAttempts++;
            return writeRouteFor(candidate, candidateSessionMarker);
        }

        private synchronized ReadbackClassification classifyReadback(
                DjiProtocolClient candidate,
                Object candidateSessionMarker,
                FlysafeRidInventory.OpaqueRidHandle target,
                FlysafeRidInventory.Result fresh) {
            requireActiveSession(candidate, false);
            if (candidateSessionMarker == null || candidateSessionMarker != sessionMarker
                    || target == null || fresh == null
                    || activeInventoryPass != null
                    || completedInventoryPasses != mutationAttempts + 1) {
                invalidateOnlyBeforeRecovery();
                throw new IllegalStateException("FLYSAFE_READBACK_ORDER_OR_IDENTITY_INVALID");
            }
            boolean baselineEnabled = target.wasEnabled();
            if (mutationAttempts == 1) {
                boolean targetEnabled = !baselineEnabled;
                try {
                    target.verifyReadback(fresh, sessionMarker, targetEnabled);
                    forwardTargetConfirmed = true;
                    safelyAtBaseline = false;
                    inventoryPassAttemptsAtStage = 0;
                    return ReadbackClassification.TARGET;
                } catch (RuntimeException targetMismatch) {
                    try {
                        target.verifyReadback(fresh, sessionMarker, baselineEnabled);
                        forwardTargetConfirmed = false;
                        safelyAtBaseline = true;
                        inventoryPassAttemptsAtStage = 0;
                        return ReadbackClassification.BASELINE;
                    } catch (RuntimeException baselineMismatch) {
                        // Roll back only the provisional completion marker. The SET is never
                        // retried, but recovery may take another complete read-only inventory.
                        completedInventoryPasses--;
                        throw new IllegalStateException("FLYSAFE_FORWARD_READBACK_UNUSABLE");
                    }
                }
            }
            if (mutationAttempts == 2) {
                try {
                    target.verifyReadback(fresh, sessionMarker, baselineEnabled);
                    safelyAtBaseline = true;
                    forwardTargetConfirmed = false;
                    inventoryPassAttemptsAtStage = 0;
                    return ReadbackClassification.BASELINE;
                } catch (RuntimeException mismatch) {
                    completedInventoryPasses--;
                    throw new IllegalStateException("FLYSAFE_RESTORE_READBACK_UNUSABLE");
                }
            }
            invalidateOnlyBeforeRecovery();
            throw new IllegalStateException("FLYSAFE_READBACK_WITHOUT_MUTATION");
        }

        /**
         * Before a mutation, an invariant violation can safely consume the one-shot session.
         * After a SET may have reached RC331, preserving the legitimate coordinator's readback
         * and restore route is more important than permanently invalidating it for a local misuse.
         */
        private void invalidateOnlyBeforeRecovery() {
            if (!recoveryMode) {
                active = false;
            }
        }

        synchronized boolean allowsModernInventory() {
            return active && snapshot.allowsModernInventory();
        }

        synchronized boolean isRecoveryMode() {
            return recoveryMode;
        }

        /** Non-sensitive count of admitted SET transitions in this session (0, 1 or 2). */
        synchronized int mutationAttempts() {
            return mutationAttempts;
        }

        synchronized boolean isSafelyAtBaseline() {
            return safelyAtBaseline;
        }

        synchronized boolean wasCancellationOrInterruptObserved() {
            return cancellationObserved || interruptObserved;
        }

        private synchronized void consume() {
            if (mutationAttempts > 0 && !safelyAtBaseline) {
                throw new IllegalStateException(
                        "FLYSAFE_SESSION_CANNOT_CLOSE_BEFORE_CONFIRMED_BASELINE");
            }
            if (activeInventoryPass != null && activeInventoryPass.isActive()) {
                throw new IllegalStateException("FLYSAFE_SESSION_HAS_ACTIVE_INVENTORY_PASS");
            }
            active = false;
        }
    }

    enum ReadbackClassification {
        BASELINE,
        TARGET
    }

    /** One exact, non-reusable group/page inventory pass on the gate-derived dynamic route. */
    static final class FlysafeInventoryPass
            implements FlysafeQueryAuthorization, AutoCloseable {
        private final DjiProtocolClient owner;
        private final FlysafeGateObservation session;
        private final Object sessionMarker;
        private final Route route;
        private final int ordinal;
        private final FlysafeQuerySequence sequence = new FlysafeQuerySequence();
        private boolean active = true;

        private FlysafeInventoryPass(
                DjiProtocolClient owner,
                FlysafeGateObservation session,
                Object sessionMarker,
                Route route,
                int ordinal) {
            this.owner = owner;
            this.session = session;
            this.sessionMarker = sessionMarker;
            this.route = copyFlysafeSetRoute(route);
            this.ordinal = ordinal;
        }

        @Override
        public void authorize(
                DjiProtocolClient candidate,
                Route candidateRoute,
                byte[] payload) {
            // Keep the single lock order session -> pass. Completion uses the same order.
            synchronized (session) {
                session.requireActiveSession(candidate, session.mutationAttempts == 0);
                synchronized (this) {
                    if (!active || owner != candidate || !sameRoute(route, candidateRoute)) {
                        throw new IllegalStateException(
                                "FLYSAFE_INVENTORY_PASS_MISSING_OR_MISMATCHED");
                    }
                    try {
                        sequence.validateAndAdvance(payload);
                    } catch (RuntimeException exception) {
                        active = false;
                        session.invalidateOnlyBeforeRecovery();
                        if (session.activeInventoryPass == this) {
                            session.activeInventoryPass = null;
                        }
                        throw exception;
                    }
                }
            }
        }

        private synchronized boolean belongsTo(
                DjiProtocolClient candidate,
                FlysafeGateObservation candidateSession,
                Object candidateSessionMarker,
                int candidateOrdinal) {
            return active
                    && owner == candidate
                    && session == candidateSession
                    && sessionMarker == candidateSessionMarker
                    && ordinal == candidateOrdinal;
        }

        private synchronized int getRequestCount() {
            return sequence.getRequestCount();
        }

        private synchronized boolean isActive() {
            return active;
        }

        private synchronized void finishLocally() {
            active = false;
        }

        Route getRoute() {
            return route;
        }

        private void finishFor(
                DjiProtocolClient candidate,
                FlysafeRidInventory.Result canonicalResult) {
            session.completeInventoryPass(candidate, this, canonicalResult);
        }

        @Override
        public void close() {
            boolean needsAbort;
            synchronized (this) {
                needsAbort = active;
                active = false;
            }
            if (needsAbort) {
                session.abortInventoryPass(this);
            }
        }

        @Override
        public String toString() {
            return "FlysafeInventoryPass{ordinal=" + ordinal
                    + ", route=<bound>, active=" + isActive() + "}";
        }
    }

    /**
     * One explicit fixed-route, query-only V3/V4 compatibility probe.
     *
     * <p>This capability does not depend on the passive 03/09 + 03/42 gate. It admits only the
     * single statically supported product-139 candidate route (sender type/id 2/4 to receiver
     * type/id 18/4), one group selector and its monotonically ordered pages. It does not try other
     * sender indexes, V2 selectors, or version-default receivers. Any cancellation, interrupt,
     * selector drift, route drift, or reuse consumes the pass.</p>
     */
    static final class DirectFlysafeReadonlyPass
            implements FlysafeQueryAuthorization, AutoCloseable {
        private final DjiProtocolClient owner;
        private final CancellationCheck cancellationCheck;
        private final Route route = new Route(
                "direct-flysafe-readonly",
                MODERN_FLYSAFE_FC4.senderId,
                MODERN_FLYSAFE_FC4.senderType,
                MODERN_FLYSAFE_FC4.receiverId,
                MODERN_FLYSAFE_FC4.receiverType);
        private final FlysafeQuerySequence sequence = new FlysafeQuerySequence();
        private boolean active = true;

        private DirectFlysafeReadonlyPass(
                DjiProtocolClient owner,
                CancellationCheck cancellationCheck) {
            this.owner = owner;
            this.cancellationCheck = cancellationCheck;
        }

        @Override
        public synchronized void authorize(
                DjiProtocolClient candidate,
                Route candidateRoute,
                byte[] payload) {
            if (!active || owner != candidate || !isExactDirectFlysafeReadonlyRoute(candidateRoute)) {
                active = false;
                throw new IllegalStateException(
                        "DIRECT_FLYSAFE_READONLY_PASS_MISSING_OR_MISMATCHED");
            }
            if ((cancellationCheck != null && cancellationCheck.isCancelled())
                    || Thread.currentThread().isInterrupted()) {
                active = false;
                throw new IllegalStateException("DIRECT_FLYSAFE_READONLY_CANCELLED");
            }
            try {
                sequence.validateAndAdvance(payload);
            } catch (RuntimeException exception) {
                active = false;
                throw exception;
            }
        }

        private synchronized void finishFor(
                DjiProtocolClient candidate,
                FlysafeRidInventory.Result canonicalResult) {
            if (!active || owner != candidate) {
                active = false;
                throw new IllegalStateException(
                        "DIRECT_FLYSAFE_READONLY_PASS_MISSING_OR_CONSUMED");
            }
            active = false;
            if (canonicalResult == null
                    || canonicalResult.isClosed()
                    || canonicalResult.isControlHandleEligible()
                    || sequence.getRequestCount() != canonicalResult.getPageCalls() + 1) {
                throw new IllegalStateException(
                        "DIRECT_FLYSAFE_READONLY_RESULT_NOT_CANONICAL");
            }
        }

        synchronized Route getRoute() {
            return route;
        }

        synchronized int getRequestCount() {
            return sequence.getRequestCount();
        }

        synchronized boolean isActive() {
            return active;
        }

        @Override
        public synchronized void close() {
            active = false;
        }

        @Override
        public synchronized String toString() {
            return "DirectFlysafeReadonlyPass{route=fixed-product139-candidate, active="
                    + active + "}";
        }
    }

    /** One group selector followed by monotonically increasing V3/V4 page selectors. */
    static final class FlysafeQuerySequence {
        private int requestCount;
        private int nextPageIndex;

        synchronized void validateAndAdvance(byte[] payload) {
            if (payload == null || payload.length != 2 || payload[0] != 0) {
                throw new IllegalArgumentException("FlySafe selector shape is invalid");
            }
            if (requestCount == 0) {
                if (payload[1] != 1) {
                    throw new IllegalArgumentException("FlySafe group selector must be first");
                }
            } else {
                if (requestCount > FlysafeRidInventory.MAX_PAGE_CALLS) {
                    throw new IllegalStateException("FlySafe page request limit exceeded");
                }
                byte expected = (byte) ((nextPageIndex << 1) & 0xff);
                if (payload[1] != expected) {
                    throw new IllegalArgumentException("FlySafe page selector is out of order");
                }
                nextPageIndex++;
            }
            requestCount++;
        }

        synchronized int getRequestCount() {
            return requestCount;
        }
    }

    /**
     * Separate one-shot capability for one modern 11/12 write.
     *
     * <p>This is intentionally not the A-026 query permit. It is bound to one client owner,
     * active gate/query session identity, exact reverse route, V3/V4 capability, opaque target
     * handle and requested state. It contains no public constructor and renders no target data.</p>
     */
    static final class FlysafeWritePermit implements AutoCloseable {
        private final DjiProtocolClient owner;
        private final FlysafeGateObservation session;
        private final Object sessionMarker;
        private final Route route;
        private final int capabilityVersion;
        private final FlysafeRidInventory.OpaqueRidHandle target;
        private final int targetTypeCode;
        private final long targetLevel;
        private final boolean requestedEnabled;
        private boolean consumed;

        private FlysafeWritePermit(
                DjiProtocolClient owner,
                FlysafeGateObservation session,
                Object sessionMarker,
                Route route,
                int capabilityVersion,
                FlysafeRidInventory.OpaqueRidHandle target,
                int targetTypeCode,
                long targetLevel,
                boolean requestedEnabled) {
            this.owner = owner;
            this.session = session;
            this.sessionMarker = sessionMarker;
            this.route = copyFlysafeSetRoute(route);
            this.capabilityVersion = capabilityVersion;
            this.target = target;
            this.targetTypeCode = targetTypeCode;
            this.targetLevel = targetLevel;
            this.requestedEnabled = requestedEnabled;
        }

        private synchronized FlysafeSetDispatch consumeFor(DjiProtocolClient candidate) {
            if (consumed) {
                throw new IllegalStateException("FLYSAFE_WRITE_PERMIT_CONSUMED");
            }
            // Every attempted use is terminal, including a failed revalidation.
            consumed = true;
            if (candidate == null || owner != candidate) {
                throw new IllegalStateException("FLYSAFE_WRITE_OWNER_MISMATCH");
            }
            int currentVersion = session.writeCapabilityVersionFor(candidate, sessionMarker);
            if (currentVersion != capabilityVersion) {
                throw new IllegalStateException("FLYSAFE_WRITE_CAPABILITY_CHANGED");
            }
            Route currentRoute = session.beginMutationForWrite(
                    candidate, sessionMarker, target, requestedEnabled);
            if (!sameRoute(route, currentRoute)) {
                throw new IllegalStateException("FLYSAFE_WRITE_ROUTE_CHANGED");
            }
            if (target.getTypeCode() != targetTypeCode
                    || targetTypeCode != FlysafeRidInventory.RID_UNLOCK_TYPE_CODE
                    || target.getLevel() != targetLevel
                    || (targetLevel != 1L && targetLevel != 2L)) {
                throw new IllegalStateException("FLYSAFE_WRITE_TARGET_CAPABILITY_CHANGED");
            }

            byte[] targetIdLe = target.copyLicenseIdLeForSet(sessionMarker);
            try {
                byte[] payload = FlysafeLicenseSetCodec.buildPayload(
                        targetIdLe, requestedEnabled);
                return new FlysafeSetDispatch(
                        candidate,
                        sessionMarker,
                        route,
                        capabilityVersion,
                        target,
                        requestedEnabled,
                        payload);
            } finally {
                Arrays.fill(targetIdLe, (byte) 0);
            }
        }

        synchronized boolean isConsumed() {
            return consumed;
        }

        @Override
        public synchronized void close() {
            consumed = true;
        }

        @Override
        public synchronized String toString() {
            return "FlysafeWritePermit{owner=<bound>, session=<bound>, route=<bound>, "
                    + "capability=V" + (capabilityVersion + 2)
                    + ", target=<redacted>, state="
                    + (requestedEnabled ? "enabled" : "disabled")
                    + ", consumed=" + consumed + "}";
        }
    }

    /** Private dispatch token proving that a separate write permit was consumed for this tuple. */
    private static final class FlysafeSetDispatch {
        final DjiProtocolClient owner;
        final Object sessionMarker;
        final Route route;
        final int capabilityVersion;
        final FlysafeRidInventory.OpaqueRidHandle target;
        final boolean requestedEnabled;
        final byte[] payload;

        private FlysafeSetDispatch(
                DjiProtocolClient owner,
                Object sessionMarker,
                Route route,
                int capabilityVersion,
                FlysafeRidInventory.OpaqueRidHandle target,
                boolean requestedEnabled,
                byte[] payload) {
            this.owner = owner;
            this.sessionMarker = sessionMarker;
            this.route = copyFlysafeSetRoute(route);
            this.capabilityVersion = capabilityVersion;
            this.target = target;
            this.requestedEnabled = requestedEnabled;
            this.payload = payload;
        }

        boolean matches(DjiProtocolClient candidate, Route candidateRoute, byte[] candidatePayload) {
            return owner == candidate
                    && sessionMarker != null
                    && target != null
                    && (capabilityVersion == 1 || capabilityVersion == 2)
                    && sameRoute(route, candidateRoute)
                    && payload == candidatePayload;
        }

        void clear() {
            Arrays.fill(payload, (byte) 0);
        }

        @Override
        public String toString() {
            return "FlysafeSetDispatch{sensitive=<redacted>}";
        }
    }

    /** One process-wide outstanding modern FlySafe transaction at a time. */
    static final class FlysafeCommandLane {
        private final AtomicBoolean active = new AtomicBoolean(false);

        boolean tryAcquire() {
            return active.compareAndSet(false, true);
        }

        void release() {
            if (!active.compareAndSet(true, false)) {
                throw new IllegalStateException("FLYSAFE_COMMAND_LANE_NOT_HELD");
            }
        }

        boolean isActive() {
            return active.get();
        }
    }

    private static final class RidStatusEvent {
        final RidWorkingStatus status;
        final String failure;
        final String route;
        final String diagnostic;

        RidStatusEvent(
                RidWorkingStatus status,
                String failure,
                String route,
                String diagnostic) {
            this.status = status;
            this.failure = failure;
            this.route = route;
            this.diagnostic = diagnostic;
        }
    }

    private final IBinder service;
    private final String serviceDiagnostic;
    private volatile String enableDiagnostic = "tx1=not-run";

    DjiProtocolClient() throws Exception {
        ResolvedService resolved = resolveProtocolService();
        service = resolved.binder;
        final boolean alive;
        final String descriptor;
        try {
            alive = service.pingBinder();
            descriptor = service.getInterfaceDescriptor();
        } catch (RemoteException | RuntimeException exception) {
            throw new IllegalStateException("BINDER_IDENTITY_FAIL; " + resolved.diagnostic
                    + "; cause=" + throwableSummary(exception), exception);
        }
        if (!alive) {
            throw new IllegalStateException("BINDER_DEAD; " + resolved.diagnostic);
        }
        if (!MANAGER_DESCRIPTOR.equals(descriptor)) {
            throw new IllegalStateException("BINDER_DESCRIPTOR_MISMATCH actual=" + descriptor
                    + "; " + resolved.diagnostic);
        }
        serviceDiagnostic = resolved.diagnostic + "; binder=alive; descriptor=" + descriptor;
    }

    private static ResolvedService resolveProtocolService() throws Exception {
        Throwable vendorLookupFailure;
        try {
            Class<?> managerClass = Class.forName("com.dji.protocol.ProtocolManager");
            Object manager = managerClass.getMethod("getDefault").invoke(null);
            if (manager == null) {
                throw new IllegalStateException("ProtocolManager.getDefault() returned null");
            }
            Field serviceField = managerClass.getDeclaredField("mService");
            serviceField.setAccessible(true);
            Object managerService = serviceField.get(manager);
            if (managerService instanceof IInterface) {
                IBinder binder = ((IInterface) managerService).asBinder();
                if (binder != null) {
                    return new ResolvedService(binder,
                            "lookup=vendor.ProtocolManager.mService; vendor=ok");
                }
            }
            vendorLookupFailure = new IllegalStateException(
                    "mService is " + (managerService == null
                            ? "null" : managerService.getClass().getName()));
        } catch (Exception | LinkageError exception) {
            vendorLookupFailure = exception;
        }

        try {
            IBinder binder = checkService(SERVICE_NAME);
            if (binder != null) {
                return new ResolvedService(binder,
                        "lookup=ServiceManager.checkService; vendor="
                                + throwableSummary(vendorLookupFailure) + "; fallback=ok");
            }
            throw new IllegalStateException("LOOKUP_FAIL; vendor="
                    + throwableSummary(vendorLookupFailure) + "; fallback=returned-null");
        } catch (Exception | LinkageError serviceManagerFailure) {
            if (serviceManagerFailure instanceof IllegalStateException
                    && serviceManagerFailure.getMessage() != null
                    && serviceManagerFailure.getMessage().startsWith("LOOKUP_FAIL;")) {
                throw (IllegalStateException) serviceManagerFailure;
            }
            IllegalStateException failure = new IllegalStateException(
                    "LOOKUP_FAIL; vendor=" + throwableSummary(vendorLookupFailure)
                            + "; fallback=" + throwableSummary(serviceManagerFailure),
                    serviceManagerFailure);
            failure.addSuppressed(vendorLookupFailure);
            throw failure;
        }
    }

    boolean isEnabled() throws RemoteException {
        long started = SystemClock.elapsedRealtime();
        Parcel request = Parcel.obtain();
        Parcel reply = Parcel.obtain();
        try {
            request.writeInterfaceToken(MANAGER_DESCRIPTOR);
            if (!service.transact(TRANSACTION_IS_ENABLE, request, reply, 0)) {
                enableDiagnostic = "tx1.transact=false; elapsedMs=" + elapsedSince(started);
                throw new RemoteException("TX1_TRANSACT_FALSE; " + serviceDiagnostic);
            }
            try {
                reply.readException();
                boolean enabled = reply.readInt() != 0;
                enableDiagnostic = "tx1.transact=true; tx1.readException=ok; enabled="
                        + (enabled ? 1 : 0) + "; elapsedMs=" + elapsedSince(started);
                return enabled;
            } catch (RuntimeException exception) {
                enableDiagnostic = "tx1.transact=true; tx1.readException="
                        + throwableSummary(exception) + "; elapsedMs=" + elapsedSince(started);
                throw new IllegalStateException("TX1_REPLY_FAIL; " + serviceDiagnostic + "; "
                        + enableDiagnostic, exception);
            }
        } catch (RemoteException exception) {
            if (enableDiagnostic.equals("tx1=not-run")) {
                enableDiagnostic = "tx1.transact=threw(" + throwableSummary(exception)
                        + "); elapsedMs=" + elapsedSince(started);
            }
            throw exception;
        } finally {
            reply.recycle();
            request.recycle();
        }
    }

    Reply request(int cmdId, byte[] payload) throws Exception {
        return request(MODERN_FC4, cmdId, payload);
    }

    Reply request(Route route, int cmdId, byte[] payload) throws Exception {
        int timeoutMs = cmdId >= CMD_PARAM_INFO_BY_HASH
                ? PARAM_COMMAND_TIMEOUT_MS : RID_COMMAND_TIMEOUT_MS;
        return sendAllowedRequest(
                route, CMD_SET_FLYC, cmdId, payload, timeoutMs, null, null);
    }

    /**
     * Issues one fixed-route active-read-only compatibility pass without a passive gate.
     *
     * <p>The returned capability is intentionally weaker than a gated inventory session: it can
     * describe only whether the current Binder path produced a canonical V3/V4-compatible
     * inventory on the single product-139 candidate route. Failure remains ambiguous and this
     * pass can never be converted into a write permit.</p>
     */
    DirectFlysafeReadonlyPass beginDirectFlysafeReadonlyProbe(
            CancellationCheck cancellationCheck) {
        if ((cancellationCheck != null && cancellationCheck.isCancelled())
                || Thread.currentThread().isInterrupted()) {
            throw new IllegalStateException("DIRECT_FLYSAFE_READONLY_CANCELLED_BEFORE_START");
        }
        return new DirectFlysafeReadonlyPass(this, cancellationCheck);
    }

    /** Fixed 11/11 query entry point; neither command nor route is caller-selectable. */
    Reply queryDirectFlysafeReadonly(
            DirectFlysafeReadonlyPass pass,
            byte[] payload) throws Exception {
        if (pass == null) {
            throw new IllegalStateException("DIRECT_FLYSAFE_READONLY_PASS_MISSING");
        }
        if (!FLYSAFE_COMMAND_LANE.tryAcquire()) {
            throw new IllegalStateException("FLYSAFE_COMMAND_ALREADY_OUTSTANDING");
        }
        try {
            return sendAllowedRequest(
                    pass.getRoute(),
                    CMD_SET_ADSB,
                    CMD_FLYSAFE_LICENSE_LIST,
                    payload,
                    FLYSAFE_COMMAND_TIMEOUT_MS,
                    pass,
                    null);
        } finally {
            FLYSAFE_COMMAND_LANE.release();
        }
    }

    /** Consumes a direct pass only after the strict parser produced one canonical full result. */
    void finishDirectFlysafeReadonlyProbe(
            DirectFlysafeReadonlyPass pass,
            FlysafeRidInventory.Result canonicalResult) {
        if (pass == null || canonicalResult == null) {
            throw new IllegalArgumentException(
                    "direct FlySafe pass and canonical result are required");
        }
        pass.finishFor(this, canonicalResult);
    }

    /** Starts one exact, non-reusable full V3/V4 inventory pass on the gate-derived route. */
    FlysafeInventoryPass beginModernFlysafeInventoryPass(
            FlysafeGateObservation gateObservation) {
        if (gateObservation == null || !gateObservation.isActiveFor(this)) {
            throw new IllegalStateException("FLYSAFE_GATE_PERMIT_MISSING_OR_CONSUMED");
        }
        Object sessionMarker = gateObservation.sessionMarkerFor(this);
        return gateObservation.beginInventoryPass(this, sessionMarker);
    }

    /** Exact read-only entry point for pages owned by one active inventory pass. */
    Reply queryModernFlysafeLicense(
            FlysafeInventoryPass inventoryPass,
            byte[] payload) throws Exception {
        if (inventoryPass == null) {
            throw new IllegalStateException("FLYSAFE_INVENTORY_PASS_MISSING");
        }
        if (!FLYSAFE_COMMAND_LANE.tryAcquire()) {
            throw new IllegalStateException("FLYSAFE_COMMAND_ALREADY_OUTSTANDING");
        }
        try {
            return sendAllowedRequest(
                    inventoryPass.getRoute(),
                    CMD_SET_ADSB,
                    CMD_FLYSAFE_LICENSE_LIST,
                    payload,
                    FLYSAFE_COMMAND_TIMEOUT_MS,
                    inventoryPass,
                    null);
        } finally {
            FLYSAFE_COMMAND_LANE.release();
        }
    }

    /** Completes a pass only when the parser returned a matching canonical full inventory. */
    void finishModernFlysafeInventoryPass(
            FlysafeInventoryPass inventoryPass,
            FlysafeRidInventory.Result canonicalResult) {
        if (inventoryPass == null || canonicalResult == null) {
            throw new IllegalArgumentException("FlySafe pass and canonical result are required");
        }
        inventoryPass.finishFor(this, canonicalResult);
    }

    ReadbackClassification classifyModernFlysafeReadback(
            FlysafeGateObservation gateObservation,
            FlysafeRidInventory.OpaqueRidHandle target,
            FlysafeRidInventory.Result freshResult) {
        if (gateObservation == null || target == null || freshResult == null) {
            throw new IllegalArgumentException("FlySafe session, target and readback are required");
        }
        Object sessionMarker = gateObservation.sessionMarkerFor(this);
        return gateObservation.classifyReadback(
                this, sessionMarker, target, freshResult);
    }

    /** Returns the opaque identity used to bind inventory handles to this active query session. */
    Object modernFlysafeSessionMarker(FlysafeGateObservation gateObservation) {
        if (gateObservation == null) {
            throw new IllegalArgumentException("FlySafe gate observation is required");
        }
        return gateObservation.sessionMarkerFor(this);
    }

    /**
     * Issues a separate, one-use 11/12 write capability. Merely holding the A-026 query permit is
     * insufficient: the exact active session, dynamic reverse route, modern capability and opaque
     * eligible target must all bind here.
     */
    FlysafeWritePermit issueModernFlysafeWritePermit(
            FlysafeGateObservation gateObservation,
            Object sessionMarker,
            FlysafeRidInventory.OpaqueRidHandle target,
            boolean requestedEnabled) {
        if (gateObservation == null || target == null) {
            throw new IllegalArgumentException("FlySafe session and target are required");
        }
        Object actualSessionMarker = gateObservation.sessionMarkerFor(this);
        if (sessionMarker == null || actualSessionMarker != sessionMarker) {
            throw new IllegalStateException("FLYSAFE_WRITE_SESSION_TOKEN_MISMATCH");
        }
        int capabilityVersion = gateObservation.writeCapabilityVersionFor(
                this, sessionMarker);
        Route reverseRoute = gateObservation.writeRouteFor(this, sessionMarker);
        int targetTypeCode = target.getTypeCode();
        long targetLevel = target.getLevel();
        if (targetTypeCode != FlysafeRidInventory.RID_UNLOCK_TYPE_CODE
                || (targetLevel != 1L && targetLevel != 2L)) {
            throw new IllegalArgumentException("FlySafe SET target capability is not admitted");
        }

        // Prove that the target is still open, belongs to this exact session, and has an admitted
        // nonzero uint32 shape without retaining or rendering a second ID copy.
        byte[] targetProof = target.copyLicenseIdLeForSet(sessionMarker);
        try {
            byte[] payloadProof = FlysafeLicenseSetCodec.buildPayload(
                    targetProof, requestedEnabled);
            Arrays.fill(payloadProof, (byte) 0);
        } finally {
            Arrays.fill(targetProof, (byte) 0);
        }
        return new FlysafeWritePermit(
                this,
                gateObservation,
                sessionMarker,
                reverseRoute,
                capabilityVersion,
                target,
                targetTypeCode,
                targetLevel,
                requestedEnabled);
    }

    /** Executes exactly one permitted SET and keeps the global FlySafe lane drained for 19 s. */
    FlysafeLicenseSetCodec.Ack setModernFlysafeLicenseEnabled(
            FlysafeWritePermit writePermit) throws Exception {
        if (writePermit == null) {
            throw new IllegalArgumentException("FlySafe write permit is required");
        }
        if (!FLYSAFE_COMMAND_LANE.tryAcquire()) {
            throw new IllegalStateException("FLYSAFE_COMMAND_ALREADY_OUTSTANDING");
        }

        FlysafeSetDispatch dispatch = null;
        Reply response = null;
        long dispatchStarted = 0L;
        boolean dispatchAttempted = false;
        try {
            dispatch = writePermit.consumeFor(this);
            dispatchStarted = SystemClock.elapsedRealtime();
            dispatchAttempted = true;
            response = sendAllowedRequest(
                    dispatch.route,
                    CMD_SET_ADSB,
                    CMD_FLYSAFE_SET_LICENSE_ENABLED,
                    dispatch.payload,
                    FLYSAFE_COMMAND_TIMEOUT_MS,
                    null,
                    dispatch);
            return FlysafeLicenseSetCodec.decodeAck(
                    response.callbackSuccess,
                    response.ccode,
                    response.data,
                    dispatch.requestedEnabled);
        } finally {
            if (response != null && response.data != null) {
                Arrays.fill(response.data, (byte) 0);
            }
            if (dispatch != null) {
                dispatch.clear();
            }
            try {
                if (dispatchAttempted) {
                    awaitFlysafeSetDrain(dispatchStarted);
                }
            } finally {
                FLYSAFE_COMMAND_LANE.release();
            }
        }
    }

    void finishModernFlysafeSession(FlysafeGateObservation gateObservation) {
        if (gateObservation != null) {
            gateObservation.consume();
        }
    }

    /**
     * General Pack sender used only after the route/command/payload/timeout tuple passes the
     * closed allow-list below. Modern 11/12 additionally requires a consumed dedicated dispatch
     * proof; neither the general request API nor the A-026 query permit can authorize it.
     */
    private Reply sendAllowedRequest(
            Route route,
            int cmdSet,
            int cmdId,
            byte[] payload,
            int timeoutMs,
            FlysafeQueryAuthorization flysafeQueryAuthorization,
            FlysafeSetDispatch flysafeSetDispatch) throws Exception {
        boolean modernFlysafeQuery = cmdSet == CMD_SET_ADSB
                && cmdId == CMD_FLYSAFE_LICENSE_LIST;
        boolean modernFlysafeSet = cmdSet == CMD_SET_ADSB
                && cmdId == CMD_FLYSAFE_SET_LICENSE_ENABLED;
        if (modernFlysafeQuery) {
            if (flysafeQueryAuthorization == null || flysafeSetDispatch != null) {
                throw new IllegalStateException("FLYSAFE_GATE_PERMIT_MISSING_OR_CONSUMED");
            }
            // Authorize first so malformed selectors/routes consume a one-shot query pass rather
            // than remaining reusable after the generic tuple validator rejects them.
            flysafeQueryAuthorization.authorize(this, route, payload);
            validateAllowedRequest(route, cmdSet, cmdId, payload, timeoutMs);
        } else {
            validateAllowedRequest(route, cmdSet, cmdId, payload, timeoutMs);
        }
        if (modernFlysafeSet) {
            if (flysafeQueryAuthorization != null
                    || flysafeSetDispatch == null
                    || !flysafeSetDispatch.matches(this, route, payload)) {
                throw new IllegalStateException("FLYSAFE_WRITE_PERMIT_MISSING_OR_MISMATCHED");
            }
        } else if (!modernFlysafeQuery
                && (flysafeQueryAuthorization != null || flysafeSetDispatch != null)) {
            throw new IllegalArgumentException("FlySafe permit cannot authorize this tuple");
        }

        long started = SystemClock.elapsedRealtime();
        ResultCallback callback = new ResultCallback(route, cmdSet, cmdId, started);
        try {
            Parcel request = Parcel.obtain();
            Parcel reply = Parcel.obtain();
            boolean dispatched = false;
            try {
                request.writeInterfaceToken(MANAGER_DESCRIPTOR);
                request.writeInt(1);
                writePack(request, route, cmdSet, cmdId, payload, timeoutMs);
                request.writeStrongBinder(callback.asBinder());
                if (!service.transact(TRANSACTION_SEND_WITH_LISTEN, request, reply, 0)) {
                    throw new RemoteException("TX4_TRANSACT_FALSE; " + serviceDiagnostic + "; "
                            + enableDiagnostic + "; cmd="
                            + commandSummary(route, cmdSet, cmdId, payload)
                            + "; elapsedMs=" + elapsedSince(started));
                }
                dispatched = true;
                try {
                    reply.readException();
                } catch (SecurityException exception) {
                    String message = "TX4_PERMISSION_OR_READ_EXCEPTION; "
                            + serviceDiagnostic + "; " + enableDiagnostic + "; cmd="
                            + commandSummary(route, cmdSet, cmdId, payload) + "; elapsedMs="
                            + elapsedSince(started) + "; cause="
                            + commandThrowableSummary(exception, cmdSet, cmdId);
                    if (isSensitiveCommand(cmdSet, cmdId)) {
                        throw new SecurityException(message);
                    }
                    throw new SecurityException(message, exception);
                } catch (RuntimeException exception) {
                    String message = "TX4_READ_EXCEPTION_FAIL; "
                            + serviceDiagnostic + "; " + enableDiagnostic + "; cmd="
                            + commandSummary(route, cmdSet, cmdId, payload) + "; elapsedMs="
                            + elapsedSince(started) + "; cause="
                            + commandThrowableSummary(exception, cmdSet, cmdId);
                    if (isSensitiveCommand(cmdSet, cmdId)) {
                        throw new IllegalStateException(message);
                    }
                    throw new IllegalStateException(message, exception);
                }
            } catch (RemoteException exception) {
                if (!dispatched && (exception.getMessage() == null
                        || !exception.getMessage().startsWith("TX4_TRANSACT_FALSE;"))) {
                    throw new RemoteException("TX4_TRANSACT_THROW; " + serviceDiagnostic + "; "
                            + enableDiagnostic + "; cmd="
                            + commandSummary(route, cmdSet, cmdId, payload)
                            + "; elapsedMs=" + elapsedSince(started) + "; cause="
                            + commandThrowableSummary(exception, cmdSet, cmdId));
                }
                throw exception;
            } catch (RuntimeException exception) {
                if (dispatched) {
                    throw exception;
                }
                String message = "TX4_TRANSACT_RUNTIME; "
                        + serviceDiagnostic + "; " + enableDiagnostic + "; cmd="
                        + commandSummary(route, cmdSet, cmdId, payload) + "; elapsedMs="
                        + elapsedSince(started) + "; cause="
                        + commandThrowableSummary(exception, cmdSet, cmdId);
                if (isSensitiveCommand(cmdSet, cmdId)) {
                    throw new IllegalStateException(message);
                }
                throw new IllegalStateException(message, exception);
            } finally {
                reply.recycle();
                request.recycle();
            }

            String dispatchDiagnostic = serviceDiagnostic + "; " + enableDiagnostic
                    + "; cmd=" + commandSummary(route, cmdSet, cmdId, payload)
                    + "; tx4.transact=true; tx4.readException=ok; dispatchMs="
                    + elapsedSince(started);
            long callbackWaitMs = callbackWaitMillis(timeoutMs);
            if (!callback.awaitUninterruptibly(callbackWaitMs)) {
                return new Reply(false, "规定时间内没有收到回包", cmdId, -1, null,
                        dispatchDiagnostic + "; " + callback.timeoutDiagnostic());
            }
            Reply callbackResult = callback.takeResult();
            if (callbackResult == null) {
                return new Reply(false, "回调完成但没有结果", cmdId, -1, null,
                        dispatchDiagnostic + "; callback=result-null; elapsedMs="
                                + elapsedSince(started));
            }
            try {
                return callbackResult.withDiagnosticPrefix(dispatchDiagnostic);
            } finally {
                if (callbackResult.data != null) {
                    Arrays.fill(callbackResult.data, (byte) 0);
                }
            }
        } finally {
            // Covers transact/readException failures, timeout, interruption and late callbacks.
            callback.closeAfterTimeout();
        }
    }

    static long callbackWaitMillis(int timeoutMs) {
        if (timeoutMs <= 0) {
            throw new IllegalArgumentException("timeout must be positive");
        }
        // RC331 ActQueue owns the retry schedule: initial send plus two retries. Waiting through
        // all three timeout periods prevents cleanup while system_server still owns an in-flight
        // modern FlySafe action.
        return Math.max(
                5000L,
                (long) timeoutMs * (RC331_ACT_QUEUE_RETRY_COUNT + 1L) + 1000L);
    }

    static int flysafeSetApplicationRetryCount() {
        return FLYSAFE_SET_APPLICATION_RETRY_COUNT;
    }

    /** The direct compatibility probe never resubmits a selector at application level. */
    static int directFlysafeReadonlyApplicationRetryCount() {
        return 0;
    }

    /** RC331 may perform the initial attempt plus its fixed two internal ActQueue retries. */
    static int directFlysafeReadonlyTransportAttemptCeiling() {
        return RC331_ACT_QUEUE_RETRY_COUNT + 1;
    }

    static long flysafeSetDrainMillis() {
        return callbackWaitMillis(FLYSAFE_COMMAND_TIMEOUT_MS);
    }

    static long remainingFlysafeSetDrainMillis(long startedMs, long nowMs) {
        if (startedMs < 0L || nowMs < 0L) {
            throw new IllegalArgumentException("drain clock must be nonnegative");
        }
        long elapsedMs = nowMs - startedMs;
        if (elapsedMs < 0L) {
            // elapsedRealtime must not go backwards. If a platform anomaly occurs, retain the
            // complete conservative window rather than shortening it.
            return flysafeSetDrainMillis();
        }
        return Math.max(0L, flysafeSetDrainMillis() - elapsedMs);
    }

    /** Fixed, uninterruptible SET quarantine; restores the caller's interrupt flag afterwards. */
    private static void awaitFlysafeSetDrain(long startedMs) {
        CountDownLatch neverSignalled = new CountDownLatch(1);
        boolean interrupted = Thread.interrupted();
        while (true) {
            long remainingMs = remainingFlysafeSetDrainMillis(
                    startedMs, SystemClock.elapsedRealtime());
            if (remainingMs <= 0L) {
                break;
            }
            try {
                neverSignalled.await(remainingMs, TimeUnit.MILLISECONDS);
            } catch (InterruptedException exception) {
                interrupted = true;
            }
        }
        if (interrupted) {
            Thread.currentThread().interrupt();
        }
    }

    static void validateAllowedRequest(
            Route route,
            int cmdSet,
            int cmdId,
            byte[] payload,
            int timeoutMs) {
        if (route == null) {
            throw new IllegalArgumentException("route is required");
        }
        if (cmdSet == CMD_SET_ADSB && cmdId == CMD_FLYSAFE_LICENSE_LIST) {
            if (!isModernFlysafeSetRoute(route)) {
                throw new IllegalArgumentException("FlySafe query route is not allow-listed");
            }
            if (timeoutMs != FLYSAFE_COMMAND_TIMEOUT_MS) {
                throw new IllegalArgumentException("FlySafe query timeout is not allow-listed");
            }
            if (payload == null || payload.length != 2 || payload[0] != 0
                    || (payload[1] != 1 && (payload[1] & 1) != 0)) {
                throw new IllegalArgumentException("FlySafe selector is not allow-listed");
            }
            return;
        }
        if (cmdSet == CMD_SET_ADSB && cmdId == CMD_FLYSAFE_SET_LICENSE_ENABLED) {
            if (!isModernFlysafeSetRoute(route)) {
                throw new IllegalArgumentException("FlySafe SET reverse route is not allow-listed");
            }
            if (timeoutMs != FLYSAFE_COMMAND_TIMEOUT_MS) {
                throw new IllegalArgumentException("FlySafe SET timeout is not allow-listed");
            }
            if (!isModernFlysafeSetPayload(payload)) {
                throw new IllegalArgumentException("FlySafe SET payload is not allow-listed");
            }
            return;
        }

        if (cmdSet != CMD_SET_FLYC || !isOldFlycCommand(cmdId)) {
            throw new IllegalArgumentException("command tuple is not allow-listed");
        }
        boolean parameterCommand = cmdId == CMD_PARAM_INFO_BY_HASH
                || cmdId == CMD_PARAM_READ_BY_HASH
                || cmdId == CMD_PARAM_WRITE_BY_HASH;
        if (!sameRoute(route, MODERN_FC4)
                && !(parameterCommand && sameRoute(route, RC2_LEGACY_FC))) {
            throw new IllegalArgumentException("command route is not allow-listed");
        }
        int expectedTimeout = parameterCommand
                ? PARAM_COMMAND_TIMEOUT_MS : RID_COMMAND_TIMEOUT_MS;
        if (timeoutMs != expectedTimeout) {
            throw new IllegalArgumentException("command timeout is not allow-listed");
        }
        if (!isOldPayloadAllowed(cmdId, payload)) {
            throw new IllegalArgumentException("command payload is not allow-listed");
        }
    }

    private static boolean isOldFlycCommand(int cmdId) {
        return cmdId == CMD_EID_SWITCH
                || cmdId == CMD_OPERATOR_ID
                || cmdId == CMD_PARAM_INFO_BY_HASH
                || cmdId == CMD_PARAM_READ_BY_HASH
                || cmdId == CMD_PARAM_WRITE_BY_HASH;
    }

    private static boolean isOldPayloadAllowed(int cmdId, byte[] payload) {
        if (payload == null) {
            return false;
        }
        if (cmdId == CMD_EID_SWITCH) {
            // STATIC LOCKED: even a direct caller cannot bypass the disabled Activity controls.
            return payload.length == 1 && payload[0] == 2;
        }
        if (cmdId == CMD_OPERATOR_ID) {
            return payload.length == 1 && payload[0] == 2;
        }
        if (cmdId == CMD_PARAM_INFO_BY_HASH) {
            return isRidControlHash(payload)
                    || isHeightLimitHash(payload)
                    || isEuC0Hash(payload);
        }
        if (cmdId == CMD_PARAM_READ_BY_HASH) {
            return isRidControlHash(payload) || isEuC0Hash(payload);
        }
        return cmdId == CMD_PARAM_WRITE_BY_HASH
                && (isRidControlBooleanWrite(payload) || isEuC0BooleanWrite(payload));
    }

    private static boolean isRidControlHash(byte[] payload) {
        return payload.length == 4
                && payload[0] == 0x4f
                && payload[1] == (byte) 0x86
                && payload[2] == (byte) 0xbd
                && payload[3] == 0x3c;
    }

    private static boolean isEuC0Hash(byte[] payload) {
        return payload.length == 4
                && payload[0] == (byte) 0xfe
                && payload[1] == (byte) 0x92
                && payload[2] == (byte) 0x09
                && payload[3] == (byte) 0xf8;
    }

    private static boolean isHeightLimitHash(byte[] payload) {
        return payload.length == 4
                && payload[0] == (byte) 0x8a
                && payload[1] == 0x23
                && payload[2] == 0x71
                && payload[3] == 0x03;
    }

    private static boolean isRidControlBooleanWrite(byte[] payload) {
        if (payload.length != 5 && payload.length != 6 && payload.length != 8) {
            return false;
        }
        if (!isRidControlHash(Arrays.copyOf(payload, 4))) {
            return false;
        }
        int width = payload.length - 4;
        boolean zero = true;
        for (int index = 4; index < payload.length; index++) {
            zero &= payload[index] == 0;
        }
        if (zero) {
            return true;
        }
        if (payload[4] == 1) {
            for (int index = 5; index < payload.length; index++) {
                if (payload[index] != 0) {
                    return false;
                }
            }
            return true;
        }
        return width == 4
                && payload[4] == 0
                && payload[5] == 0
                && payload[6] == (byte) 0x80
                && payload[7] == 0x3f;
    }

    private static boolean isEuC0BooleanWrite(byte[] payload) {
        if (payload.length != 5 && payload.length != 6 && payload.length != 8) {
            return false;
        }
        if (!isEuC0Hash(Arrays.copyOf(payload, 4))) {
            return false;
        }
        int width = payload.length - 4;
        boolean zero = true;
        for (int index = 4; index < payload.length; index++) {
            zero &= payload[index] == 0;
        }
        if (zero) {
            return true;
        }
        if (payload[4] == 1) {
            for (int index = 5; index < payload.length; index++) {
                if (payload[index] != 0) {
                    return false;
                }
            }
            return true;
        }
        return width == 4
                && payload[4] == 0
                && payload[5] == 0
                && payload[6] == (byte) 0x80
                && payload[7] == 0x3f;
    }

    /**
     * A-027 uses the strict reverse of the same gate-window push route. The sender index is live
     * state and therefore cannot be replaced with the A-026 fixed sender id. Route provenance is
     * bound by the write permit; this helper only validates the admitted numeric shape.
     */
    static boolean isModernFlysafeSetRoute(Route route) {
        return route != null
                && route.senderType == 0x02
                && route.senderId >= 0
                && route.senderId <= 7
                && route.receiverType == 0x12
                && route.receiverId == 0x04;
    }

    /** The active read-only fallback has exactly one candidate and never scans sender indexes. */
    static boolean isExactDirectFlysafeReadonlyRoute(Route route) {
        return route != null && sameRoute(route, MODERN_FLYSAFE_FC4);
    }

    private static Route copyFlysafeSetRoute(Route route) {
        if (!isModernFlysafeSetRoute(route)) {
            throw new IllegalArgumentException("FlySafe SET reverse route is not admitted");
        }
        // Never retain a caller-provided label: it is diagnostic text and must not become a side
        // channel for the sensitive target ID.
        return new Route(
                "gated-flysafe-set",
                route.senderId,
                route.senderType,
                route.receiverId,
                route.receiverType);
    }

    private static boolean isModernFlysafeSetPayload(byte[] payload) {
        if (payload == null || payload.length != FlysafeLicenseSetCodec.PAYLOAD_LENGTH
                || payload[0] != 0
                || (payload[5] != 1 && payload[5] != 2)
                || payload[6] != 0) {
            return false;
        }
        return payload[1] != 0 || payload[2] != 0
                || payload[3] != 0 || payload[4] != 0;
    }

    private static boolean sameRoute(Route first, Route second) {
        return first.senderId == second.senderId
                && first.senderType == second.senderType
                && first.receiverId == second.receiverId
                && first.receiverType == second.receiverType;
    }

    /**
     * Registers one process-lifetime listener for the passive FlySafe support/version pushes.
     *
     * <p>No Pack is sent by this method. The listener is closed locally before return and must be
     * removed from system_server through this APK process dying after the caller has optionally
     * completed the same-process gated 11/11 inventory query.</p>
     */
    FlysafeGateObservation listenForFlysafeProtocolGate(
            long timeoutMs,
            Runnable onRegistered,
            CancellationCheck cancellationCheck) throws Exception {
        if (timeoutMs < 5_000 || timeoutMs > 120_000) {
            throw new IllegalArgumentException("FlySafe gate timeout must be 5-120 seconds");
        }
        if (cancellationCheck != null && cancellationCheck.isCancelled()) {
            throw new IllegalStateException("FLYSAFE_GATE_CANCELLED_BEFORE_REGISTRATION");
        }
        long started = SystemClock.elapsedRealtime();
        FlysafeGatePushCallback callback = new FlysafeGatePushCallback();
        callback.beginWindow(started);
        Parcel request = Parcel.obtain();
        Parcel reply = Parcel.obtain();
        try {
            request.writeInterfaceToken(MANAGER_DESCRIPTOR);
            request.writeInt(1); // PackFilter present.
            request.writeInt(2); // Area Info + WhiteList Info.
            writeWildcardPushRule(request, CMD_SET_FLYC, CMD_FLYSAFE_AREA_INFO);
            writeWildcardPushRule(request, CMD_SET_FLYC, CMD_FLYSAFE_WHITELIST_INFO);
            request.writeStrongBinder(callback.asBinder());
            if (!service.transact(TRANSACTION_ADD_PACK_LISTENER, request, reply, 0)) {
                throw new RemoteException("TX2_FLYSAFE_TRANSACT_FALSE; "
                        + serviceDiagnostic + "; " + enableDiagnostic
                        + "; elapsedMs=" + elapsedSince(started));
            }
            try {
                reply.readException();
            } catch (SecurityException exception) {
                throw new SecurityException("TX2_FLYSAFE_PERMISSION_OR_READ_EXCEPTION; "
                        + serviceDiagnostic + "; " + enableDiagnostic + "; elapsedMs="
                        + elapsedSince(started) + "; cause=" + throwableSummary(exception),
                        exception);
            }
        } finally {
            reply.recycle();
            request.recycle();
        }

        long acceptedMs = elapsedSince(started);
        if (onRegistered != null) {
            try {
                onRegistered.run();
            } catch (RuntimeException ignored) {
                // A display callback must never break listener lifecycle/cleanup.
            }
        }
        FlysafeGatePushCallback.WaitResult waitResult = callback.awaitGate(
                timeoutMs,
                cancellationCheck);
        FlysafeGatePushCallback.FinishResult finishResult = callback.finishWindow();
        FlysafeProtocolGate.Snapshot snapshot = finishResult.snapshot;
        boolean cancelledAfterWindow = cancellationCheck != null
                && cancellationCheck.isCancelled();
        return new FlysafeGateObservation(
                this,
                snapshot,
                serviceDiagnostic + "; " + enableDiagnostic
                        + "; tx2.transact=true; tx2.readException=ok; acceptedMs="
                        + acceptedMs
                        + "; wait=" + (waitResult.completed ? "gate-terminal" : "deadline")
                        + "; waitInterrupted=" + (waitResult.interrupted ? 1 : 0)
                        + "; waitCancelled=" + (waitResult.cancelled ? 1 : 0)
                        + "; freezeInterrupted=" + (finishResult.interrupted ? 1 : 0)
                        + "; cancelledAfterWindow=" + (cancelledAfterWindow ? 1 : 0)
                        + "; cleanup=process-death-required",
                waitResult.completed
                        && !waitResult.interrupted
                        && !waitResult.cancelled
                        && !finishResult.interrupted
                        && !cancelledAfterWindow,
                cancellationCheck);
    }

    private static void writeWildcardPushRule(Parcel request, int cmdSet, int cmdId) {
        // RC331 PushQueue treats app4 (type 2, id 4) as a wildcard sender rule.
        request.writeInt(0x04); // senderId
        request.writeInt(0x02); // senderType
        request.writeInt(0x04); // receiverId, ignored by PushQueue dispatch
        request.writeInt(0x02); // receiverType, ignored by PushQueue dispatch
        request.writeInt(cmdSet);
        request.writeInt(cmdId);
    }

    /**
     * Registers one process-lifetime local listener for the passive RID status push.
     *
     * <p>RC331 v10 cannot reliably remove a cross-process listener with transaction 5 because
     * its implementation compares AIDL proxy object identity. The caller must terminate this
     * APK process after this method returns so Binder death performs deterministic cleanup.</p>
     */
    RidStatusObservation listenForRidWorkingStatus(long timeoutMs) throws Exception {
        if (timeoutMs < 1000 || timeoutMs > 120_000) {
            throw new IllegalArgumentException("RID listen timeout must be 1-120 seconds");
        }
        long started = SystemClock.elapsedRealtime();
        RidPushCallback callback = new RidPushCallback();
        Parcel request = Parcel.obtain();
        Parcel reply = Parcel.obtain();
        try {
            request.writeInterfaceToken(MANAGER_DESCRIPTOR);
            request.writeInt(1); // PackFilter present.
            request.writeInt(1); // One PackRule.
            // Exact PackRule parcel order. Sender app4 is a PushQueue wildcard on RC331 v10.
            request.writeInt(0x04); // senderId
            request.writeInt(0x02); // senderType
            request.writeInt(0x04); // receiverId (not used by PushQueue dispatch)
            request.writeInt(0x02); // receiverType (not used by PushQueue dispatch)
            request.writeInt(CMD_SET_ADSB);
            request.writeInt(CMD_RID_WORKING_STATUS);
            request.writeStrongBinder(callback.asBinder());
            if (!service.transact(TRANSACTION_ADD_PACK_LISTENER, request, reply, 0)) {
                throw new RemoteException("TX2_TRANSACT_FALSE; " + serviceDiagnostic + "; "
                        + enableDiagnostic + "; elapsedMs=" + elapsedSince(started));
            }
            try {
                reply.readException();
            } catch (SecurityException exception) {
                throw new SecurityException("TX2_PERMISSION_OR_READ_EXCEPTION; "
                        + serviceDiagnostic + "; " + enableDiagnostic + "; elapsedMs="
                        + elapsedSince(started) + "; cause=" + throwableSummary(exception),
                        exception);
            }
        } finally {
            reply.recycle();
            request.recycle();
        }

        long acceptedMs = elapsedSince(started);
        long windowStarted = SystemClock.elapsedRealtime();
        callback.beginWindow(windowStarted);
        String registered = serviceDiagnostic + "; " + enableDiagnostic
                + "; tx2.transact=true; tx2.readException=ok; acceptedMs="
                + acceptedMs
                + "; cleanup=process-death-required";
        boolean interrupted = awaitFullWindow(timeoutMs);
        RidStatusTimeline.Snapshot timeline = callback.finishWindow();
        long windowElapsedMs = timeline.getWindowElapsedMs();
        return new RidStatusObservation(
                timeline,
                registered
                        + "; requestedWindowMs=" + timeoutMs
                        + "; actualWindowMs=" + windowElapsedMs
                        + "; waitInterrupted=" + (interrupted ? 1 : 0));
    }

    /** Waits the whole observation interval even if an incidental interrupt is delivered. */
    private static boolean awaitFullWindow(long timeoutMs) {
        CountDownLatch neverSignalled = new CountDownLatch(1);
        long deadline = SystemClock.elapsedRealtime() + timeoutMs;
        boolean interrupted = false;
        while (true) {
            long remainingMs = deadline - SystemClock.elapsedRealtime();
            if (remainingMs <= 0) {
                break;
            }
            try {
                neverSignalled.await(remainingMs, TimeUnit.MILLISECONDS);
            } catch (InterruptedException exception) {
                interrupted = true;
            }
        }
        if (interrupted) {
            Thread.currentThread().interrupt();
        }
        return interrupted;
    }

    private static long elapsedSince(long started) {
        return SystemClock.elapsedRealtime() - started;
    }

    private static String commandSummary(
            Route route,
            int cmdSet,
            int cmdId,
            byte[] payload) {
        String payloadSummary = cmdSet == CMD_SET_FLYC && cmdId == CMD_OPERATOR_ID
                ? "<redacted-operator-id>"
                : isSensitiveCommand(cmdSet, cmdId) ? "<redacted-license-action>" : hex(payload);
        return String.format(Locale.US, "%s cmd=%02X/%02X payload=%s",
                route.summary(), cmdSet & 0xff, cmdId & 0xff, payloadSummary);
    }

    private static boolean isSensitiveCommand(int cmdSet, int cmdId) {
        return (cmdSet == CMD_SET_FLYC && cmdId == CMD_OPERATOR_ID)
                || (cmdSet == CMD_SET_ADSB
                && (cmdId == CMD_FLYSAFE_LICENSE_LIST
                || cmdId == CMD_FLYSAFE_SET_LICENSE_ENABLED));
    }

    private static String hex(byte[] value) {
        if (value == null) {
            return "<null>";
        }
        if (value.length == 0) {
            return "<empty>";
        }
        StringBuilder result = new StringBuilder(value.length * 2);
        for (byte item : value) {
            result.append(String.format(Locale.US, "%02X", item & 0xff));
        }
        return result.toString();
    }

    private static String printableText(byte[] value) {
        if (value == null) {
            return "<null>";
        }
        if (value.length == 0) {
            return "<empty>";
        }
        String decoded = new String(value, StandardCharsets.UTF_8);
        StringBuilder printable = new StringBuilder(decoded.length());
        for (int index = 0; index < decoded.length(); index++) {
            char item = decoded.charAt(index);
            if (item == '\n') {
                printable.append("\\n");
            } else if (item == '\r') {
                printable.append("\\r");
            } else if (item == '\t') {
                printable.append("\\t");
            } else if (Character.isISOControl(item)) {
                printable.append('?');
            } else {
                printable.append(item);
            }
        }
        return printable.toString();
    }

    private static String throwableSummary(Throwable throwable) {
        Throwable current = unwrapInvocationTarget(throwable);
        String name = current.getClass().getSimpleName();
        if (name.isEmpty()) {
            name = current.getClass().getName();
        }
        String message = current.getMessage();
        if (message == null || message.isEmpty()) {
            return name;
        }
        String sanitized = message.replace('\n', ' ').replace('\r', ' ');
        if (sanitized.length() > 320) {
            sanitized = sanitized.substring(0, 320) + "…";
        }
        return name + ":" + sanitized;
    }

    private static String commandThrowableSummary(
            Throwable throwable,
            int cmdSet,
            int cmdId) {
        if (!isSensitiveCommand(cmdSet, cmdId)) {
            return throwableSummary(throwable);
        }
        Throwable current = unwrapInvocationTarget(throwable);
        String name = current.getClass().getSimpleName();
        return name.isEmpty() ? current.getClass().getName() : name;
    }

    private static Throwable unwrapInvocationTarget(Throwable throwable) {
        Throwable current = throwable;
        while (current instanceof InvocationTargetException
                && current.getCause() != null) {
            current = current.getCause();
        }
        return current;
    }

    private static final class ResolvedService {
        final IBinder binder;
        final String diagnostic;

        ResolvedService(IBinder binder, String diagnostic) {
            this.binder = binder;
            this.diagnostic = diagnostic;
        }
    }

    private static IBinder checkService(String name) throws Exception {
        Class<?> serviceManager = Class.forName("android.os.ServiceManager");
        Method method = serviceManager.getDeclaredMethod("checkService", String.class);
        try {
            return (IBinder) method.invoke(null, name);
        } catch (InvocationTargetException exception) {
            Throwable cause = exception.getCause();
            if (cause instanceof Exception) {
                throw (Exception) cause;
            }
            throw exception;
        }
    }

    private static void writePack(
            Parcel parcel,
            Route route,
            int cmdSet,
            int cmdId,
            byte[] payload,
            int timeoutMs) {
        parcel.writeByte((byte) 0x55);
        parcel.writeInt(1);
        parcel.writeInt(0);
        parcel.writeInt(0);
        parcel.writeInt(route.senderId);
        parcel.writeInt(route.senderType);
        parcel.writeInt(route.receiverId);
        parcel.writeInt(route.receiverType);
        parcel.writeInt(-1);
        parcel.writeInt(0); // request
        parcel.writeInt(2); // ACK after execution
        parcel.writeInt(0); // duplicate cmdType in vendor ABI
        parcel.writeInt(0); // plaintext
        parcel.writeInt(cmdSet);
        parcel.writeInt(cmdId);
        parcel.writeInt(payload.length);
        parcel.writeByteArray(payload);
        parcel.writeInt(0);
        parcel.writeInt(0);
        parcel.writeInt(timeoutMs);
        parcel.writeInt(0);
    }

    private static final class ResultCallback extends Binder implements IInterface {
        private final Route expectedRoute;
        private final int expectedCmdSet;
        private final int expectedCmdId;
        private final long requestStarted;
        private final CountDownLatch done = new CountDownLatch(1);
        private final ReplySlot replySlot = new ReplySlot();
        private final AtomicInteger duplicateCallbacks = new AtomicInteger(0);
        volatile int lastCode = -1;
        volatile int lastFlags = -1;
        volatile int lastInitialAvail = -1;

        ResultCallback(
                Route expectedRoute,
                int expectedCmdSet,
                int expectedCmdId,
                long requestStarted) {
            this.expectedRoute = expectedRoute;
            this.expectedCmdSet = expectedCmdSet;
            this.expectedCmdId = expectedCmdId;
            this.requestStarted = requestStarted;
            attachInterface(this, LISTENER_DESCRIPTOR);
        }

        @Override
        public IBinder asBinder() {
            return this;
        }

        @Override
        protected boolean onTransact(int code, Parcel data, Parcel reply, int flags)
                throws RemoteException {
            if (code == IBinder.INTERFACE_TRANSACTION) {
                if (reply != null) {
                    reply.writeString(LISTENER_DESCRIPTOR);
                }
                return true;
            }
            lastCode = code;
            lastFlags = flags;
            lastInitialAvail = data.dataAvail();
            if (code == CALLBACK_SUCCESS) {
                int afterTokenAvail = -1;
                try {
                    data.enforceInterface(LISTENER_DESCRIPTOR);
                    afterTokenAvail = data.dataAvail();
                    if (data.readInt() == 0) {
                        finish(new Reply(false, "回包 Pack 为空", expectedCmdId, -1, null,
                                callbackSummary("SUCCESS_NULL_PACK", afterTokenAvail, data)));
                    } else {
                        ParsedPack pack = ParsedPack.readFrom(data);
                        pack.trailingBytes = data.dataAvail();
                        Reply validated;
                        try {
                            validated = validate(
                                    pack,
                                    expectedRoute,
                                    expectedCmdSet,
                                    expectedCmdId,
                                    callbackSummary("SUCCESS", afterTokenAvail, data));
                        } finally {
                            if (isSensitiveCommand(expectedCmdSet, expectedCmdId)
                                    && pack.data != null) {
                                Arrays.fill(pack.data, (byte) 0);
                            }
                        }
                        finish(validated);
                    }
                } catch (RuntimeException exception) {
                    String cause = commandThrowableSummary(
                            exception, expectedCmdSet, expectedCmdId);
                    finish(new Reply(false, "回包解析失败: " + cause,
                            expectedCmdId, -1, null,
                            callbackSummary("SUCCESS_TOKEN_OR_ABI_FAIL", afterTokenAvail, data)
                                    + "; cause=" + cause));
                }
                return true;
            }
            if (code == CALLBACK_FAILURE) {
                int afterTokenAvail = -1;
                byte[] description = null;
                try {
                    data.enforceInterface(LISTENER_DESCRIPTOR);
                    afterTokenAvail = data.dataAvail();
                    int present = data.readInt();
                    if (present == 0) {
                        finish(new Reply(false, "DJI callback failure：ECode 为空",
                                expectedCmdId, -1, null,
                                callbackSummary("FAILURE_NULL_ECODE", afterTokenAvail, data)));
                    } else {
                        int error = data.readInt();
                        int explicitLength = data.readInt();
                        if (explicitLength < 0 || explicitLength > 4096) {
                            throw new IllegalArgumentException(
                                    "ECode description length=" + explicitLength);
                        }
                        if (explicitLength > 0) {
                            description = new byte[explicitLength];
                            data.readByteArray(description);
                        }
                        final String ecodeDiagnostic;
                        if (isSensitiveCommand(expectedCmdSet, expectedCmdId)) {
                            ecodeDiagnostic = String.format(Locale.US,
                                    "ecode{id=%d descLen=%d desc=<redacted> trailing=%d}",
                                    error,
                                    explicitLength,
                                    data.dataAvail());
                        } else {
                            ecodeDiagnostic = String.format(Locale.US,
                                    "ecode{id=%d descLen=%d descHex=%s descText=%s trailing=%d}",
                                    error,
                                    explicitLength,
                                    hex(description),
                                    printableText(description),
                                    data.dataAvail());
                        }
                        finish(new Reply(false, "DJI callback failure=" + error,
                                expectedCmdId, error, null,
                                callbackSummary("FAILURE", afterTokenAvail, data)
                                        + "; " + ecodeDiagnostic));
                    }
                } catch (RuntimeException exception) {
                    String cause = commandThrowableSummary(
                            exception, expectedCmdSet, expectedCmdId);
                    finish(new Reply(false, "ECode 回包解析失败: " + cause,
                            expectedCmdId, -1, null,
                            callbackSummary("FAILURE_TOKEN_OR_ABI_FAIL",
                                    afterTokenAvail, data)
                                    + "; cause=" + cause));
                } finally {
                    if (description != null) {
                        Arrays.fill(description, (byte) 0);
                    }
                }
                return true;
            }
            int afterTokenAvail = -1;
            String tokenResult = "ok";
            try {
                data.enforceInterface(LISTENER_DESCRIPTOR);
                afterTokenAvail = data.dataAvail();
            } catch (RuntimeException exception) {
                tokenResult = commandThrowableSummary(
                        exception, expectedCmdSet, expectedCmdId);
            }
            finish(new Reply(false, "未知 DJI callback transaction=" + code,
                    expectedCmdId, -1, null,
                    callbackSummary("UNKNOWN", afterTokenAvail, data)
                            + "; token=" + tokenResult));
            return true;
        }

        private void finish(Reply candidate) {
            if (replySlot.offer(candidate)) {
                done.countDown();
            } else {
                duplicateCallbacks.incrementAndGet();
            }
        }

        boolean awaitUninterruptibly(long timeoutMs) {
            long deadline = SystemClock.elapsedRealtime() + timeoutMs;
            boolean interrupted = false;
            boolean completed = false;
            while (!completed) {
                long remainingMs = deadline - SystemClock.elapsedRealtime();
                if (remainingMs <= 0) {
                    break;
                }
                try {
                    completed = done.await(remainingMs, TimeUnit.MILLISECONDS);
                } catch (InterruptedException exception) {
                    interrupted = true;
                }
            }
            if (interrupted) {
                Thread.currentThread().interrupt();
            }
            return completed;
        }

        void closeAfterTimeout() {
            replySlot.closeAndClear();
        }

        Reply takeResult() {
            return replySlot.take();
        }

        String timeoutDiagnostic() {
            return "callback=NONE; elapsedMs=" + elapsedSince(requestStarted)
                    + "; lastCode=" + lastCode
                    + "; lastFlags=" + lastFlags
                    + "; lastInitialAvail=" + lastInitialAvail
                    + "; duplicateCallbacks=" + duplicateCallbacks.get();
        }

        private String callbackSummary(String event, int afterTokenAvail, Parcel data) {
            return "callback=" + event
                    + "; elapsedMs=" + elapsedSince(requestStarted)
                    + "; code=" + lastCode
                    + "; flags=" + lastFlags
                    + "; initialAvail=" + lastInitialAvail
                    + "; afterTokenAvail=" + afterTokenAvail
                    + "; parcelPos=" + data.dataPosition()
                    + "; parcelSize=" + data.dataSize()
                    + "; remaining=" + data.dataAvail();
        }
    }

    /** Race-safe owner of the single accepted callback Reply. */
    static final class ReplySlot {
        private boolean closed;
        private Reply value;

        synchronized boolean offer(Reply candidate) {
            if (!closed) {
                closed = true;
                value = candidate;
                return true;
            }
            clear(candidate);
            return false;
        }

        synchronized void closeAndClear() {
            closed = true;
            clear(value);
            value = null;
        }

        synchronized Reply take() {
            Reply accepted = value;
            value = null;
            return accepted;
        }

        private static void clear(Reply reply) {
            if (reply != null && reply.data != null) {
                Arrays.fill(reply.data, (byte) 0);
            }
        }
    }

    private static final class FlysafeGatePushCallback extends Binder implements IInterface {
        private final FlysafeProtocolGate gate = new FlysafeProtocolGate();
        private final CountDownLatch terminalGate = new CountDownLatch(1);
        private final Object callbackGate = new Object();
        private boolean acceptingCallbacks = true;
        private int callbacksInFlight;
        private volatile long windowStarted;

        FlysafeGatePushCallback() {
            attachInterface(this, LISTENER_DESCRIPTOR);
        }

        static final class WaitResult {
            final boolean completed;
            final boolean interrupted;
            final boolean cancelled;

            WaitResult(boolean completed, boolean interrupted, boolean cancelled) {
                this.completed = completed;
                this.interrupted = interrupted;
                this.cancelled = cancelled;
            }
        }

        static final class FinishResult {
            final FlysafeProtocolGate.Snapshot snapshot;
            final boolean interrupted;

            FinishResult(FlysafeProtocolGate.Snapshot snapshot, boolean interrupted) {
                this.snapshot = snapshot;
                this.interrupted = interrupted;
            }
        }

        void beginWindow(long started) {
            windowStarted = started;
        }

        @Override
        public IBinder asBinder() {
            return this;
        }

        @Override
        protected boolean onTransact(int code, Parcel data, Parcel reply, int flags)
                throws RemoteException {
            if (code == IBinder.INTERFACE_TRANSACTION) {
                if (reply != null) {
                    reply.writeString(LISTENER_DESCRIPTOR);
                }
                return true;
            }
            if (!beginCallback()) {
                return true;
            }
            try {
                handleCallback(code, data);
                if (gate.hasTerminalGateResult()) {
                    terminalGate.countDown();
                }
                return true;
            } finally {
                endCallback();
            }
        }

        private void handleCallback(int code, Parcel data) {
            if (code == CALLBACK_SUCCESS) {
                try {
                    data.enforceInterface(LISTENER_DESCRIPTOR);
                    if (data.readInt() == 0) {
                        gate.recordMalformedCallback();
                        return;
                    }
                    ParsedPack pack = ParsedPack.readFrom(data);
                    pack.trailingBytes = data.dataAvail();
                    try {
                        if (!isValidGatePush(pack)) {
                            gate.recordMalformedCallback();
                            return;
                        }
                        gate.observe(
                                pack.senderType,
                                pack.senderId,
                                pack.receiverType,
                                pack.receiverId,
                                pack.cmdSet,
                                pack.cmdId,
                                pack.data);
                    } finally {
                        if (pack.data != null) {
                            Arrays.fill(pack.data, (byte) 0);
                        }
                    }
                } catch (RuntimeException exception) {
                    gate.recordMalformedCallback();
                }
                return;
            }
            if (code == CALLBACK_FAILURE) {
                byte[] description = null;
                try {
                    data.enforceInterface(LISTENER_DESCRIPTOR);
                    int present = data.readInt();
                    if (present != 0) {
                        data.readInt(); // ECode id, intentionally not persisted.
                        int length = data.readInt();
                        if (length < 0 || length > 4096) {
                            throw new IllegalArgumentException(
                                    "FlySafe gate ECode description length=" + length);
                        }
                        if (length > 0) {
                            description = new byte[length];
                            data.readByteArray(description);
                        }
                    }
                } catch (RuntimeException exception) {
                    gate.recordMalformedCallback();
                } finally {
                    if (description != null) {
                        Arrays.fill(description, (byte) 0);
                    }
                    gate.recordFailureCallback();
                }
                return;
            }
            gate.recordMalformedCallback();
        }

        private static boolean isValidGatePush(ParsedPack pack) {
            if ((pack.sof & 0xff) != 0x55 || pack.version != 1) {
                return false;
            }
            if (pack.senderType < 0 || pack.senderType > 31
                    || pack.receiverType < 0 || pack.receiverType > 31
                    || pack.senderId < 0 || pack.senderId > 7
                    || pack.receiverId < 0 || pack.receiverId > 7) {
                return false;
            }
            if (pack.cmdSet != CMD_SET_FLYC
                    || (pack.cmdId != CMD_FLYSAFE_AREA_INFO
                    && pack.cmdId != CMD_FLYSAFE_WHITELIST_INFO)) {
                return false;
            }
            return pack.cmdType == 0
                    && pack.duplicateCmdType == 0
                    && pack.isNeedAck == 0
                    && pack.encryptType == 0
                    && pack.ccode == 0
                    && pack.trailingBytes == 0;
        }

        WaitResult awaitGate(long timeoutMs, CancellationCheck cancellationCheck) {
            long deadline = SystemClock.elapsedRealtime() + timeoutMs;
            boolean interrupted = false;
            boolean completed = false;
            boolean cancelled = false;
            while (!completed) {
                if (cancellationCheck != null && cancellationCheck.isCancelled()) {
                    cancelled = true;
                    break;
                }
                long remainingMs = deadline - SystemClock.elapsedRealtime();
                if (remainingMs <= 0) {
                    break;
                }
                try {
                    completed = terminalGate.await(
                            Math.min(remainingMs, 200L),
                            TimeUnit.MILLISECONDS);
                } catch (InterruptedException exception) {
                    interrupted = true;
                }
            }
            if (interrupted) {
                Thread.currentThread().interrupt();
            }
            return new WaitResult(completed, interrupted, cancelled);
        }

        FinishResult finishWindow() {
            boolean interrupted = Thread.interrupted();
            synchronized (callbackGate) {
                acceptingCallbacks = false;
                while (callbacksInFlight > 0) {
                    try {
                        callbackGate.wait();
                    } catch (InterruptedException exception) {
                        interrupted = true;
                    }
                }
            }
            interrupted |= Thread.interrupted();
            if (interrupted) {
                Thread.currentThread().interrupt();
            }
            long started = windowStarted;
            long elapsed = started == 0L ? 0L : elapsedSince(started);
            return new FinishResult(gate.close(elapsed), interrupted);
        }

        private boolean beginCallback() {
            synchronized (callbackGate) {
                if (!acceptingCallbacks) {
                    return false;
                }
                callbacksInFlight++;
                return true;
            }
        }

        private void endCallback() {
            synchronized (callbackGate) {
                callbacksInFlight--;
                if (callbacksInFlight == 0) {
                    callbackGate.notifyAll();
                }
            }
        }
    }

    private static final class RidPushCallback extends Binder implements IInterface {
        private final RidStatusTimeline timeline = new RidStatusTimeline();
        private final Object callbackGate = new Object();
        private boolean acceptingCallbacks = true;
        private int callbacksInFlight;
        private volatile long windowStarted;

        RidPushCallback() {
            attachInterface(this, LISTENER_DESCRIPTOR);
        }

        void beginWindow(long started) {
            windowStarted = started;
        }

        @Override
        public IBinder asBinder() {
            return this;
        }

        @Override
        protected boolean onTransact(int code, Parcel data, Parcel reply, int flags)
                throws RemoteException {
            if (code == IBinder.INTERFACE_TRANSACTION) {
                if (reply != null) {
                    reply.writeString(LISTENER_DESCRIPTOR);
                }
                return true;
            }
            if (!beginCallback()) {
                return true;
            }
            try {
                return handleCallback(code, data, flags);
            } finally {
                endCallback();
            }
        }

        private boolean handleCallback(int code, Parcel data, int flags) {
            long observedAtMs = eventElapsedMs();
            int initialAvail = data.dataAvail();
            if (code == CALLBACK_SUCCESS) {
                int afterTokenAvail = -1;
                try {
                    data.enforceInterface(LISTENER_DESCRIPTOR);
                    afterTokenAvail = data.dataAvail();
                    if (data.readInt() == 0) {
                        record(observedAtMs,
                                new RidStatusEvent(null, "RID push Pack 为空", null,
                                        pushDiagnostic("SUCCESS_NULL_PACK", code, flags,
                                                initialAvail, afterTokenAvail, data,
                                                observedAtMs)));
                    } else {
                        ParsedPack pack = ParsedPack.readFrom(data);
                        pack.trailingBytes = data.dataAvail();
                        try {
                            record(observedAtMs, validateRidPush(pack,
                                    pushDiagnostic("SUCCESS", code, flags,
                                            initialAvail, afterTokenAvail, data, observedAtMs)));
                        } finally {
                            if (pack.data != null) {
                                Arrays.fill(pack.data, (byte) 0);
                            }
                        }
                    }
                } catch (RuntimeException exception) {
                    record(observedAtMs, new RidStatusEvent(null,
                            "RID push 解析失败: " + throwableSummary(exception),
                            null,
                            pushDiagnostic("SUCCESS_TOKEN_OR_ABI_FAIL", code, flags,
                                    initialAvail, afterTokenAvail, data, observedAtMs)
                                    + "; cause=" + throwableSummary(exception)));
                }
                return true;
            }
            if (code == CALLBACK_FAILURE) {
                int afterTokenAvail = -1;
                byte[] description = null;
                try {
                    data.enforceInterface(LISTENER_DESCRIPTOR);
                    afterTokenAvail = data.dataAvail();
                    int present = data.readInt();
                    int error = present == 0 ? -1 : data.readInt();
                    int descriptionLength = present == 0 ? 0 : data.readInt();
                    if (descriptionLength < 0 || descriptionLength > 4096) {
                        throw new IllegalArgumentException(
                                "RID push ECode description length=" + descriptionLength);
                    }
                    if (descriptionLength > 0) {
                        description = new byte[descriptionLength];
                        data.readByteArray(description);
                    }
                    record(observedAtMs, new RidStatusEvent(null,
                            "RID push callback failure=" + error,
                            null,
                            pushDiagnostic("FAILURE", code, flags, initialAvail,
                                    afterTokenAvail, data, observedAtMs)
                                    + "; descLen=" + descriptionLength
                                    + "; desc=<redacted>"));
                } catch (RuntimeException exception) {
                    record(observedAtMs, new RidStatusEvent(null,
                            "RID push ECode 解析失败: " + throwableSummary(exception),
                            null,
                            pushDiagnostic("FAILURE_TOKEN_OR_ABI_FAIL", code, flags,
                                    initialAvail, afterTokenAvail, data, observedAtMs)
                                    + "; cause=" + throwableSummary(exception)));
                } finally {
                    if (description != null) {
                        Arrays.fill(description, (byte) 0);
                    }
                }
                return true;
            }

            record(observedAtMs, new RidStatusEvent(null,
                    "未知 RID push callback transaction=" + code,
                    null,
                    pushDiagnostic("UNKNOWN", code, flags, initialAvail, -1, data,
                            observedAtMs)));
            return true;
        }

        RidStatusTimeline.Snapshot finishWindow() {
            boolean interrupted = false;
            synchronized (callbackGate) {
                acceptingCallbacks = false;
                while (callbacksInFlight > 0) {
                    try {
                        callbackGate.wait();
                    } catch (InterruptedException exception) {
                        interrupted = true;
                    }
                }
            }
            if (interrupted) {
                Thread.currentThread().interrupt();
            }
            return timeline.close(eventElapsedMs());
        }

        private boolean beginCallback() {
            synchronized (callbackGate) {
                if (!acceptingCallbacks) {
                    return false;
                }
                callbacksInFlight++;
                return true;
            }
        }

        private void endCallback() {
            synchronized (callbackGate) {
                callbacksInFlight--;
                if (callbacksInFlight == 0) {
                    callbackGate.notifyAll();
                }
            }
        }

        private void record(long observedAtMs, RidStatusEvent candidate) {
            timeline.record(
                    observedAtMs,
                    candidate.status,
                    candidate.failure,
                    candidate.route,
                    candidate.diagnostic);
        }

        private long eventElapsedMs() {
            long started = windowStarted;
            // A service is allowed to invoke the callback immediately as transaction 2 returns.
            // Such a callback belongs to the window and is represented at t=0.
            return started == 0L ? 0L : elapsedSince(started);
        }

        private String pushDiagnostic(
                String event,
                int code,
                int flags,
                int initialAvail,
                int afterTokenAvail,
                Parcel data,
                long observedAtMs) {
            return "callback=" + event
                    + "; elapsedMs=" + observedAtMs
                    + "; code=" + code
                    + "; flags=" + flags
                    + "; initialAvail=" + initialAvail
                    + "; afterTokenAvail=" + afterTokenAvail
                    + "; parcelPos=" + data.dataPosition()
                    + "; parcelSize=" + data.dataSize()
                    + "; remaining=" + data.dataAvail();
        }
    }

    private static RidStatusEvent validateRidPush(
            ParsedPack pack,
            String callbackDiagnostic) {
        String route = String.format(Locale.US, "%02X:%02X>%02X:%02X",
                pack.senderType & 0xff,
                pack.senderId & 0xff,
                pack.receiverType & 0xff,
                pack.receiverId & 0xff);
        String diagnostic = callbackDiagnostic + "; " + pack.summary();
        if ((pack.sof & 0xff) != 0x55 || pack.version != 1) {
            return new RidStatusEvent(null, "RID push DUML envelope 不匹配",
                    route, diagnostic);
        }
        if (pack.cmdSet != CMD_SET_ADSB || pack.cmdId != CMD_RID_WORKING_STATUS) {
            return new RidStatusEvent(null, "RID push 命令不匹配", route, diagnostic);
        }
        if (pack.cmdType != 0 || pack.duplicateCmdType != 0
                || pack.isNeedAck != 0 || pack.encryptType != 0) {
            return new RidStatusEvent(null, "RID push 类型、ACK 或加密方式不匹配",
                    route, diagnostic);
        }
        if (pack.trailingBytes != 0) {
            return new RidStatusEvent(null, "RID push Parcel 有尾随字段",
                    route, diagnostic);
        }
        try {
            return new RidStatusEvent(
                    RidWorkingStatus.parse(pack.data), null, route, diagnostic);
        } catch (RidWorkingStatus.ProtocolException exception) {
            return new RidStatusEvent(null, exception.getMessage(), route, diagnostic);
        }
    }

    private static Reply validate(
            ParsedPack pack,
            Route expectedRoute,
            int expectedCmdSet,
            int expectedCmdId,
            String callbackDiagnostic) {
        String diagnostic = callbackDiagnostic + "; " + pack.summary();
        if ((pack.sof & 0xff) != 0x55 || pack.version != 1) {
            return new Reply(false, "DUML envelope 不匹配", expectedCmdId, pack.ccode,
                    pack.data, diagnostic);
        }
        if (pack.senderType != expectedRoute.receiverType
                || pack.senderId != expectedRoute.receiverId
                || pack.receiverType != expectedRoute.senderType
                || pack.receiverId != expectedRoute.senderId) {
            return new Reply(false, "回包路由不匹配", expectedCmdId, pack.ccode,
                    pack.data, diagnostic);
        }
        if (pack.cmdSet != expectedCmdSet || pack.cmdId != expectedCmdId) {
            return new Reply(false, "回包命令不匹配", expectedCmdId, pack.ccode,
                    pack.data, diagnostic);
        }
        if (pack.cmdType != 1 || pack.duplicateCmdType != 1
                || pack.isNeedAck != 0 || pack.encryptType != 0) {
            return new Reply(false, "回包类型、ACK 或加密方式不匹配", expectedCmdId,
                    pack.ccode, pack.data, diagnostic);
        }
        if (pack.trailingBytes != 0) {
            return new Reply(false, "回包 Parcel 有尾随字段", expectedCmdId,
                    pack.ccode, pack.data, diagnostic);
        }
        return new Reply(true, null, expectedCmdId, pack.ccode, pack.data, diagnostic);
    }

    private static final class ParsedPack {
        byte sof;
        int version;
        int length;
        int crc8;
        int senderId;
        int senderType;
        int receiverId;
        int receiverType;
        int seq;
        int cmdType;
        int isNeedAck;
        int duplicateCmdType;
        int encryptType;
        int cmdSet;
        int cmdId;
        int dataLength;
        byte[] data;
        int ccode;
        int crc16;
        int timeOut;
        int retryCnt;
        int trailingBytes;

        static ParsedPack readFrom(Parcel parcel) {
            ParsedPack pack = new ParsedPack();
            try {
                pack.sof = parcel.readByte();
                pack.version = parcel.readInt();
                pack.length = parcel.readInt();
                pack.crc8 = parcel.readInt();
                pack.senderId = parcel.readInt();
                pack.senderType = parcel.readInt();
                pack.receiverId = parcel.readInt();
                pack.receiverType = parcel.readInt();
                pack.seq = parcel.readInt();
                pack.cmdType = parcel.readInt();
                pack.isNeedAck = parcel.readInt();
                pack.duplicateCmdType = parcel.readInt();
                pack.encryptType = parcel.readInt();
                pack.cmdSet = parcel.readInt();
                pack.cmdId = parcel.readInt();
                int length = parcel.readInt();
                if (length < 0 || length > 4097) {
                    throw new IllegalArgumentException("Pack data length=" + length);
                }
                pack.dataLength = length;
                if (length > 0) {
                    pack.data = new byte[length];
                    parcel.readByteArray(pack.data);
                }
                pack.ccode = parcel.readInt();
                pack.crc16 = parcel.readInt();
                pack.timeOut = parcel.readInt();
                pack.retryCnt = parcel.readInt();
                return pack;
            } catch (RuntimeException exception) {
                if (pack.data != null) {
                    Arrays.fill(pack.data, (byte) 0);
                }
                throw exception;
            }
        }

        String summary() {
            return String.format(Locale.US,
                    "ack{sof=%02X ver=%d len=%d crc8=%02X route=%02X:%02X>%02X:%02X "
                            + "seq=%d type=%d/%d needAck=%d enc=%d cmd=%02X/%02X "
                            + "ccode=%d dataLen=%d data=<redacted> crc16=%04X timeout=%d retry=%d "
                            + "trailing=%d}",
                    sof & 0xff,
                    version,
                    length,
                    crc8 & 0xff,
                    senderType & 0xff,
                    senderId & 0xff,
                    receiverType & 0xff,
                    receiverId & 0xff,
                    seq,
                    cmdType,
                    duplicateCmdType,
                    isNeedAck,
                    encryptType,
                    cmdSet & 0xff,
                    cmdId & 0xff,
                    ccode,
                    dataLength,
                    crc16 & 0xffff,
                    timeOut,
                    retryCnt,
                    trailingBytes);
        }
    }
}
