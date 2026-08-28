package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public final class ReplySlotTest {
    @Test
    public void duplicateReplyIsRejectedAndCleared() {
        DjiProtocolClient.ReplySlot slot = new DjiProtocolClient.ReplySlot();
        DjiProtocolClient.Reply first = reply(new byte[]{1, 2});
        DjiProtocolClient.Reply duplicate = reply(new byte[]{3, 4});
        assertTrue(slot.offer(first));
        assertFalse(slot.offer(duplicate));
        assertArrayEquals(new byte[]{0, 0}, duplicate.data);
        assertSame(first, slot.take());
    }

    @Test
    public void timeoutClosesSlotAndClearsStoredOrLateReply() {
        DjiProtocolClient.ReplySlot storedSlot = new DjiProtocolClient.ReplySlot();
        DjiProtocolClient.Reply stored = reply(new byte[]{5, 6});
        assertTrue(storedSlot.offer(stored));
        storedSlot.closeAndClear();
        assertArrayEquals(new byte[]{0, 0}, stored.data);
        assertNull(storedSlot.take());

        DjiProtocolClient.ReplySlot lateSlot = new DjiProtocolClient.ReplySlot();
        lateSlot.closeAndClear();
        DjiProtocolClient.Reply late = reply(new byte[]{7, 8});
        assertFalse(lateSlot.offer(late));
        assertArrayEquals(new byte[]{0, 0}, late.data);
        assertNull(lateSlot.take());
    }

    private static DjiProtocolClient.Reply reply(byte[] data) {
        return new DjiProtocolClient.Reply(true, null, 0x11, 0, data, "redacted");
    }
}
