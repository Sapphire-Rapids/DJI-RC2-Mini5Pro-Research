package com.finduas.rc2ridadmin;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

/**
 * Thread-safe, bounded aggregation for passive RID working-status callbacks.
 *
 * <p>Only adjacent callbacks with the same semantic status and actual route are folded together.
 * Consequently an A-B-A sequence remains three timeline entries instead of being mistaken for one
 * long A state. Callback failures and malformed packets are entries too.</p>
 */
final class RidStatusTimeline {
    static final int DEFAULT_MAX_EVENTS = 32;
    private static final int MAX_FAILURE_CHARS = 320;
    private static final int MAX_ROUTE_CHARS = 96;
    private static final int MAX_DIAGNOSTIC_CHARS = 1536;

    private final int maxEvents;
    private final ArrayList<MutableEvent> events = new ArrayList<>();
    private long totalCallbacks;
    private long validCallbacks;
    private long failureCallbacks;
    private long droppedTransitions;
    private long lastObservedAtMs;
    private boolean closed;

    RidStatusTimeline() {
        this(DEFAULT_MAX_EVENTS);
    }

    RidStatusTimeline(int maxEvents) {
        if (maxEvents < 1) {
            throw new IllegalArgumentException("maxEvents must be positive");
        }
        this.maxEvents = maxEvents;
    }

    /** Records one callback. Returns false only after the observation window has closed. */
    synchronized boolean record(
            long observedAtMs,
            RidWorkingStatus status,
            String failure,
            String route,
            String diagnostic) {
        if (closed) {
            return false;
        }

        long timestamp = Math.max(0L, observedAtMs);
        // Concurrent Binder threads can reach this lock out of timestamp order.
        timestamp = Math.max(timestamp, lastObservedAtMs);
        lastObservedAtMs = timestamp;

        String safeFailure = status == null
                ? bounded(failure == null ? "未知 RID push 失败" : failure, MAX_FAILURE_CHARS)
                : null;
        String safeRoute = bounded(route == null ? "<unknown>" : route, MAX_ROUTE_CHARS);
        String safeDiagnostic = bounded(diagnostic, MAX_DIAGNOSTIC_CHARS);
        String semanticKey = semanticKey(status, safeFailure, safeRoute);

        totalCallbacks++;
        if (status == null) {
            failureCallbacks++;
        } else {
            validCallbacks++;
        }

        MutableEvent previous = events.isEmpty() ? null : events.get(events.size() - 1);
        if (previous != null && previous.semanticKey.equals(semanticKey)) {
            previous.lastSeenMs = timestamp;
            previous.occurrences++;
            // Keep the newest low-level context without making sequence/parcel offsets part of
            // the semantic de-duplication key.
            previous.diagnostic = safeDiagnostic;
            return true;
        }

        if (events.size() == maxEvents) {
            events.remove(0);
            droppedTransitions++;
        }
        events.add(new MutableEvent(
                semanticKey,
                timestamp,
                status,
                safeFailure,
                safeRoute,
                safeDiagnostic));
        return true;
    }

    /** Atomically closes the window and returns a defensive, immutable snapshot. */
    synchronized Snapshot close(long windowElapsedMs) {
        closed = true;
        ArrayList<Event> copy = new ArrayList<>(events.size());
        for (MutableEvent event : events) {
            copy.add(event.snapshot());
        }
        return new Snapshot(
                Math.max(0L, windowElapsedMs),
                totalCallbacks,
                validCallbacks,
                failureCallbacks,
                droppedTransitions,
                copy);
    }

    private static String semanticKey(
            RidWorkingStatus status,
            String failure,
            String route) {
        if (status == null) {
            return "failure|" + route + "|" + failure;
        }
        return "status|" + route
                + "|flags=" + status.getFlags()
                + "|area=" + status.getAreaCode()
                + "|failure=" + status.getFailureCode();
    }

    private static String bounded(String value, int maxChars) {
        if (value == null || value.length() <= maxChars) {
            return value;
        }
        return value.substring(0, maxChars) + "…";
    }

    private static final class MutableEvent {
        final String semanticKey;
        final long firstSeenMs;
        final RidWorkingStatus status;
        final String failure;
        final String route;
        long lastSeenMs;
        long occurrences = 1;
        String diagnostic;

        MutableEvent(
                String semanticKey,
                long timestamp,
                RidWorkingStatus status,
                String failure,
                String route,
                String diagnostic) {
            this.semanticKey = semanticKey;
            this.firstSeenMs = timestamp;
            this.lastSeenMs = timestamp;
            this.status = status;
            this.failure = failure;
            this.route = route;
            this.diagnostic = diagnostic;
        }

        Event snapshot() {
            return new Event(
                    firstSeenMs,
                    lastSeenMs,
                    occurrences,
                    status,
                    failure,
                    route,
                    diagnostic);
        }
    }

    static final class Event {
        private final long firstSeenMs;
        private final long lastSeenMs;
        private final long occurrences;
        private final RidWorkingStatus status;
        private final String failure;
        private final String route;
        private final String diagnostic;

        Event(
                long firstSeenMs,
                long lastSeenMs,
                long occurrences,
                RidWorkingStatus status,
                String failure,
                String route,
                String diagnostic) {
            this.firstSeenMs = firstSeenMs;
            this.lastSeenMs = lastSeenMs;
            this.occurrences = occurrences;
            this.status = status;
            this.failure = failure;
            this.route = route;
            this.diagnostic = diagnostic;
        }

        long getFirstSeenMs() {
            return firstSeenMs;
        }

        long getLastSeenMs() {
            return lastSeenMs;
        }

        long getOccurrences() {
            return occurrences;
        }

        RidWorkingStatus getStatus() {
            return status;
        }

        String getFailure() {
            return failure;
        }

        String getRoute() {
            return route;
        }

        String getDiagnostic() {
            return diagnostic;
        }
    }

    static final class Snapshot {
        private final long windowElapsedMs;
        private final long totalCallbacks;
        private final long validCallbacks;
        private final long failureCallbacks;
        private final long droppedTransitions;
        private final List<Event> events;

        Snapshot(
                long windowElapsedMs,
                long totalCallbacks,
                long validCallbacks,
                long failureCallbacks,
                long droppedTransitions,
                List<Event> events) {
            this.windowElapsedMs = windowElapsedMs;
            this.totalCallbacks = totalCallbacks;
            this.validCallbacks = validCallbacks;
            this.failureCallbacks = failureCallbacks;
            this.droppedTransitions = droppedTransitions;
            this.events = Collections.unmodifiableList(new ArrayList<>(events));
        }

        long getWindowElapsedMs() {
            return windowElapsedMs;
        }

        long getTotalCallbacks() {
            return totalCallbacks;
        }

        long getValidCallbacks() {
            return validCallbacks;
        }

        long getFailureCallbacks() {
            return failureCallbacks;
        }

        long getDroppedTransitions() {
            return droppedTransitions;
        }

        List<Event> getEvents() {
            return events;
        }

        String display() {
            StringBuilder result = new StringBuilder();
            result.append(String.format(Locale.US,
                    "RID 监听时间线：窗口=%d ms；回调=%d（有效=%d，异常=%d）；状态段=%d",
                    windowElapsedMs,
                    totalCallbacks,
                    validCallbacks,
                    failureCallbacks,
                    events.size()));
            if (droppedTransitions > 0) {
                result.append("；因上限丢弃最早状态段=").append(droppedTransitions);
            }
            if (events.isEmpty()) {
                result.append("\n监听窗口内没有收到 0x11/0x1C；这不等于飞机不支持 RID。");
                return result.toString();
            }

            for (int index = 0; index < events.size(); index++) {
                Event event = events.get(index);
                result.append(String.format(Locale.US,
                        "\n\n#%d [+%d..+%d ms, x%d] 实际 route=%s",
                        index + 1,
                        event.firstSeenMs,
                        event.lastSeenMs,
                        event.occurrences,
                        event.route));
                if (event.status != null) {
                    result.append("\n").append(event.status.display());
                } else {
                    result.append("\n异常：").append(event.failure);
                }
                if (event.diagnostic != null && !event.diagnostic.isEmpty()) {
                    result.append("\nDIAG: ").append(event.diagnostic);
                }
            }
            return result.toString();
        }
    }
}
