package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertThrows;

import org.junit.Test;

public final class FlysafeQuerySequenceTest {
    @Test
    public void admitsOneGroupThenStrictlyOrderedPages() {
        DjiProtocolClient.FlysafeQuerySequence sequence =
                new DjiProtocolClient.FlysafeQuerySequence();
        sequence.validateAndAdvance(new byte[]{0, 1});
        sequence.validateAndAdvance(new byte[]{0, 0});
        sequence.validateAndAdvance(new byte[]{0, 2});
        sequence.validateAndAdvance(new byte[]{0, 4});
        assertEquals(4, sequence.getRequestCount());
    }

    @Test
    public void rejectsMissingRepeatedOrOutOfOrderGroupAndPages() {
        DjiProtocolClient.FlysafeQuerySequence missingGroup =
                new DjiProtocolClient.FlysafeQuerySequence();
        assertThrows(IllegalArgumentException.class,
                () -> missingGroup.validateAndAdvance(new byte[]{0, 0}));

        DjiProtocolClient.FlysafeQuerySequence repeatedGroup =
                new DjiProtocolClient.FlysafeQuerySequence();
        repeatedGroup.validateAndAdvance(new byte[]{0, 1});
        assertThrows(IllegalArgumentException.class,
                () -> repeatedGroup.validateAndAdvance(new byte[]{0, 1}));

        DjiProtocolClient.FlysafeQuerySequence skippedPage =
                new DjiProtocolClient.FlysafeQuerySequence();
        skippedPage.validateAndAdvance(new byte[]{0, 1});
        assertThrows(IllegalArgumentException.class,
                () -> skippedPage.validateAndAdvance(new byte[]{0, 2}));
    }

    @Test
    public void rejectsMoreThanBoundedPageCount() {
        DjiProtocolClient.FlysafeQuerySequence sequence =
                new DjiProtocolClient.FlysafeQuerySequence();
        sequence.validateAndAdvance(new byte[]{0, 1});
        for (int index = 0; index < FlysafeRidInventory.MAX_PAGE_CALLS; index++) {
            sequence.validateAndAdvance(FlysafeRidInventory.pagePayload(index));
        }
        assertThrows(IllegalStateException.class,
                () -> sequence.validateAndAdvance(new byte[]{0, 0}));
        assertEquals(FlysafeRidInventory.MAX_PAGE_CALLS + 1,
                sequence.getRequestCount());
    }
}
