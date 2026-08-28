package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public final class RidStatusTimelineTest {
    @Test
    public void foldsOnlyAdjacentEqualSemanticStatusOnSameRoute() {
        RidStatusTimeline timeline = new RidStatusTimeline(8);

        timeline.record(10, status(0x0101, 44, 0), null, "02:04>02:04", "seq=1");
        timeline.record(30, status(0x0101, 44, 0), null, "02:04>02:04", "seq=2");

        RidStatusTimeline.Snapshot snapshot = timeline.close(30_000);
        assertEquals(2, snapshot.getTotalCallbacks());
        assertEquals(2, snapshot.getValidCallbacks());
        assertEquals(0, snapshot.getFailureCallbacks());
        assertEquals(1, snapshot.getEvents().size());
        RidStatusTimeline.Event event = snapshot.getEvents().get(0);
        assertEquals(10, event.getFirstSeenMs());
        assertEquals(30, event.getLastSeenMs());
        assertEquals(2, event.getOccurrences());
        assertEquals("seq=2", event.getDiagnostic());
    }

    @Test
    public void preservesStatusChangesIncludingReturnToEarlierState() {
        RidStatusTimeline timeline = new RidStatusTimeline(8);

        timeline.record(1, status(0x0001, 7, 0), null, "route-a", null);
        timeline.record(2, status(0x0101, 7, 0), null, "route-a", null);
        timeline.record(3, status(0x0001, 7, 0), null, "route-a", null);

        RidStatusTimeline.Snapshot snapshot = timeline.close(30_000);
        assertEquals(3, snapshot.getEvents().size());
        assertEquals(0x0001, snapshot.getEvents().get(0).getStatus().getFlags());
        assertEquals(0x0101, snapshot.getEvents().get(1).getStatus().getFlags());
        assertEquals(0x0001, snapshot.getEvents().get(2).getStatus().getFlags());
    }

    @Test
    public void actualRouteIsPartOfStatusIdentity() {
        RidStatusTimeline timeline = new RidStatusTimeline(8);
        RidWorkingStatus value = status(0x0101, 7, 0);

        timeline.record(1, value, null, "route-a", null);
        timeline.record(2, value, null, "route-b", null);

        RidStatusTimeline.Snapshot snapshot = timeline.close(30_000);
        assertEquals(2, snapshot.getEvents().size());
        assertEquals("route-a", snapshot.getEvents().get(0).getRoute());
        assertEquals("route-b", snapshot.getEvents().get(1).getRoute());
    }

    @Test
    public void callbackFailuresAndMalformedFramesRemainInTimeline() {
        RidStatusTimeline timeline = new RidStatusTimeline(8);

        timeline.record(5, null, "DJI callback failure=3", null, "first");
        timeline.record(7, null, "DJI callback failure=3", null, "second");
        timeline.record(9, null, "RID push payload length is 6, expected 7",
                "02:04>02:04", "malformed");

        RidStatusTimeline.Snapshot snapshot = timeline.close(30_000);
        assertEquals(3, snapshot.getTotalCallbacks());
        assertEquals(0, snapshot.getValidCallbacks());
        assertEquals(3, snapshot.getFailureCallbacks());
        assertEquals(2, snapshot.getEvents().size());
        assertEquals(2, snapshot.getEvents().get(0).getOccurrences());
        assertEquals("<unknown>", snapshot.getEvents().get(0).getRoute());
        assertEquals("second", snapshot.getEvents().get(0).getDiagnostic());
        assertEquals("02:04>02:04", snapshot.getEvents().get(1).getRoute());
    }

    @Test
    public void eventCapacityDropsOldestTransitionsButKeepsTotals() {
        RidStatusTimeline timeline = new RidStatusTimeline(2);

        timeline.record(1, status(0x0001, 0, 0), null, "route", null);
        timeline.record(2, status(0x0101, 0, 0), null, "route", null);
        timeline.record(3, status(0x0001, 0, 1), null, "route", null);
        timeline.record(4, status(0x0001, 0, 1), null, "route", null);

        RidStatusTimeline.Snapshot snapshot = timeline.close(30_000);
        assertEquals(4, snapshot.getTotalCallbacks());
        assertEquals(1, snapshot.getDroppedTransitions());
        assertEquals(2, snapshot.getEvents().size());
        assertEquals(0x0101, snapshot.getEvents().get(0).getStatus().getFlags());
        assertEquals(2, snapshot.getEvents().get(1).getOccurrences());
    }

    @Test
    public void timestampsAreMonotonicAcrossConcurrentArrivalOrder() {
        RidStatusTimeline timeline = new RidStatusTimeline(4);

        timeline.record(20, status(0x0001, 0, 0), null, "route", null);
        timeline.record(10, status(0x0001, 0, 0), null, "route", null);

        RidStatusTimeline.Event event = timeline.close(30_000).getEvents().get(0);
        assertEquals(20, event.getFirstSeenMs());
        assertEquals(20, event.getLastSeenMs());
        assertEquals(2, event.getOccurrences());
    }

    @Test
    public void closeFreezesAnImmutableDisplayableSnapshot() {
        RidStatusTimeline timeline = new RidStatusTimeline(4);
        timeline.record(12, status(0x0101, 1, 0), null, "route", "diag");

        RidStatusTimeline.Snapshot snapshot = timeline.close(30_001);
        assertFalse(timeline.record(13, null, "late", null, null));
        assertEquals(1, snapshot.getTotalCallbacks());
        assertEquals(30_001, snapshot.getWindowElapsedMs());
        assertThrows(UnsupportedOperationException.class,
                () -> snapshot.getEvents().clear());
        assertTrue(snapshot.display().contains("RID 监听时间线"));
        assertTrue(snapshot.display().contains("x1"));
        assertTrue(snapshot.display().contains("实际 route=route"));
    }

    @Test
    public void emptyWindowHasExplicitNonSupportDisclaimer() {
        RidStatusTimeline.Snapshot snapshot = new RidStatusTimeline(4).close(30_000);

        assertEquals(0, snapshot.getTotalCallbacks());
        assertTrue(snapshot.getEvents().isEmpty());
        assertTrue(snapshot.display().contains("这不等于飞机不支持 RID"));
    }

    private static RidWorkingStatus status(int flags, int area, int failure) {
        return RidWorkingStatus.parse(new byte[] {
                (byte) flags,
                (byte) (flags >>> 8),
                (byte) area,
                (byte) (area >>> 8),
                (byte) (area >>> 16),
                (byte) (area >>> 24),
                (byte) failure
        });
    }
}
