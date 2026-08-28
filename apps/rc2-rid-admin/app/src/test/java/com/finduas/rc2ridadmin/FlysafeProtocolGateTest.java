package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public final class FlysafeProtocolGateTest {
    private static final int SENDER_TYPE = 3;
    private static final int SENDER_ID = 0;
    private static final int RECEIVER_TYPE = 2;
    private static final int RECEIVER_ID = 4;

    @Test
    public void noCallbacksRemainUnobserved() {
        FlysafeProtocolGate.Snapshot snapshot = new FlysafeProtocolGate().close(60_000);
        assertEquals(FlysafeProtocolGate.Decision.GATE_UNOBSERVED, snapshot.getDecision());
        assertFalse(snapshot.allowsModernInventory());
    }

    @Test
    public void shortAreaIsSeenButUnusable() {
        FlysafeProtocolGate gate = new FlysafeProtocolGate();
        gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 9, new byte[7]);
        gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42, new byte[]{10});
        assertEquals(FlysafeProtocolGate.Decision.GATE_INVALIDATED,
                gate.close(100).getDecision());
    }

    @Test
    public void areaTopBitsDecodeV2V3V4AndUnknown() {
        assertEquals(Integer.valueOf(0), areaOnly(new byte[]{0x34, 0x12}));
        assertEquals(Integer.valueOf(1), areaOnly(new byte[]{0x00, 0x40}));
        assertEquals(Integer.valueOf(2), areaOnly(new byte[]{0x00, (byte) 0x80}));
        assertEquals(Integer.valueOf(255), areaOnly(new byte[]{0x00, (byte) 0xc0}));
    }

    @Test
    public void modernWhitelistEncodingTakesPriority() {
        assertEquals(Boolean.TRUE, whitelistOnly(new byte[]{10}));
        assertEquals(Boolean.TRUE, whitelistOnly(new byte[]{(byte) 254}));
        assertEquals(Boolean.FALSE, whitelistOnly(new byte[]{(byte) 255}));

        byte[] tenWithFalseLegacyByte = new byte[28];
        tenWithFalseLegacyByte[0] = 10;
        tenWithFalseLegacyByte[3] = 0;
        assertEquals(Boolean.TRUE, whitelistOnly(tenWithFalseLegacyByte));

        byte[] ffWithTrueLegacyByte = new byte[28];
        ffWithTrueLegacyByte[0] = (byte) 255;
        ffWithTrueLegacyByte[3] = 1;
        assertEquals(Boolean.FALSE, whitelistOnly(ffWithTrueLegacyByte));
    }

    @Test
    public void legacyWhitelistEncodingRequiresTwentyEightBytes() {
        byte[] shortValue = new byte[27];
        shortValue[0] = 9;
        FlysafeProtocolGate shortGate = gateWithArea(1);
        shortGate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42, shortValue);
        assertEquals(FlysafeProtocolGate.Decision.GATE_INVALIDATED,
                shortGate.close(100).getDecision());

        byte[] disabled = new byte[28];
        disabled[0] = 9;
        disabled[3] = 0;
        assertEquals(Boolean.FALSE, whitelistOnly(disabled));

        byte[] enabled = new byte[28];
        enabled[0] = 9;
        enabled[3] = 1;
        assertEquals(Boolean.TRUE, whitelistOnly(enabled));
    }

    @Test
    public void shortWhitelistPermanentlyInvalidatesPriorUsableValue() {
        FlysafeProtocolGate gate = gateWithArea(1);
        gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42, new byte[]{10});
        byte[] shortValue = new byte[27];
        shortValue[0] = 9;
        gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42, shortValue);
        FlysafeProtocolGate.Snapshot snapshot = gate.close(100);
        assertEquals(FlysafeProtocolGate.Decision.GATE_INVALIDATED,
                snapshot.getDecision());
        assertEquals(Boolean.TRUE, snapshot.getSupported());
        assertFalse(snapshot.allowsModernInventory());
    }

    @Test
    public void malformedRecognizedCommandOnDifferentRouteCannotBeWashedOut() {
        FlysafeProtocolGate gate = gateWithArea(2);
        gate.observe(18, 4, 2, 5, 3, 0x42, new byte[0]);
        gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42, new byte[]{10});
        FlysafeProtocolGate.Snapshot snapshot = gate.close(100);
        assertEquals(FlysafeProtocolGate.Decision.GATE_INVALIDATED,
                snapshot.getDecision());
        assertFalse(snapshot.allowsModernInventory());
    }

    @Test
    public void v2IsObservedButNotSentThroughModernQuery() {
        FlysafeProtocolGate gate = gateWithArea(0);
        gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42, new byte[]{10});
        assertEquals(FlysafeProtocolGate.Decision.V2_NOT_IMPLEMENTED,
                gate.close(100).getDecision());
    }

    @Test
    public void v3AndV4WithSupportAreModernCandidates() {
        for (int version : new int[]{1, 2}) {
            FlysafeProtocolGate gate = gateWithArea(version);
            gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                    3, 0x42, new byte[]{10});
            assertTrue(gate.close(100).allowsModernInventory());
        }
    }

    @Test
    public void product139RequestRouteIsTheStrictReverseOfObservedPush() {
        FlysafeProtocolGate gate = new FlysafeProtocolGate();
        gate.observe(18, 4, 2, 5, 3, 9, areaPayload(2));
        gate.observe(18, 4, 2, 5, 3, 0x42, new byte[]{10});
        FlysafeProtocolGate.Snapshot snapshot = gate.close(100);
        assertTrue(snapshot.hasProduct139ModernReverseRoute());
        FlysafeProtocolGate.ReversedRoute route = snapshot.getReversedRoute();
        assertEquals(2, route.getSenderType());
        assertEquals(5, route.getSenderId());
        assertEquals(18, route.getReceiverType());
        assertEquals(4, route.getReceiverId());
        assertEquals("ReversedRoute{redacted}", route.toString());
    }

    @Test
    public void fixedSenderIndexIsNotAssumedAndWrongEndpointShapeCannotWrite() {
        FlysafeProtocolGate gate = gateWithArea(2);
        gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42, new byte[]{10});
        FlysafeProtocolGate.Snapshot snapshot = gate.close(100);
        assertTrue(snapshot.allowsModernInventory());
        assertFalse(snapshot.hasProduct139ModernReverseRoute());
        assertEquals("ReversedRoute{redacted}", snapshot.getReversedRoute().toString());
    }

    @Test
    public void unknownVersionAndObservedUnsupportedDoNotAdmit() {
        FlysafeProtocolGate unknown = gateWithArea(255);
        unknown.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42, new byte[]{10});
        assertEquals(FlysafeProtocolGate.Decision.UNKNOWN_VERSION,
                unknown.close(100).getDecision());

        FlysafeProtocolGate unsupported = gateWithArea(2);
        unsupported.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42,
                new byte[]{(byte) 255});
        assertEquals(FlysafeProtocolGate.Decision.OBSERVED_UNSUPPORTED,
                unsupported.close(100).getDecision());
    }

    @Test
    public void senderChangeInvalidatesWindow() {
        FlysafeProtocolGate gate = gateWithArea(2);
        gate.observe(SENDER_TYPE, SENDER_ID + 1, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42, new byte[]{10});
        assertEquals(FlysafeProtocolGate.Decision.GATE_INVALIDATED,
                gate.close(100).getDecision());
    }

    @Test
    public void receiverChangeAlsoInvalidatesWindow() {
        FlysafeProtocolGate gate = gateWithArea(2);
        gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID + 1,
                3, 0x42, new byte[]{10});
        assertEquals(FlysafeProtocolGate.Decision.GATE_INVALIDATED,
                gate.close(100).getDecision());
    }

    @Test
    public void conflictingValuesInvalidateWindow() {
        FlysafeProtocolGate versionConflict = gateWithArea(1);
        versionConflict.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 9, areaPayload(2));
        assertEquals(FlysafeProtocolGate.Decision.GATE_INVALIDATED,
                versionConflict.close(100).getDecision());

        FlysafeProtocolGate supportConflict = gateWithArea(2);
        supportConflict.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42, new byte[]{10});
        supportConflict.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42,
                new byte[]{(byte) 255});
        assertEquals(FlysafeProtocolGate.Decision.GATE_INVALIDATED,
                supportConflict.close(100).getDecision());
    }

    @Test
    public void malformedOrFailureCallbackPermanentlyClosesGate() {
        FlysafeProtocolGate malformed = gateWithArea(2);
        malformed.recordMalformedCallback();
        malformed.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42, new byte[]{10});
        FlysafeProtocolGate.Snapshot malformedSnapshot = malformed.close(100);
        assertEquals(FlysafeProtocolGate.Decision.GATE_INVALIDATED,
                malformedSnapshot.getDecision());
        assertFalse(malformedSnapshot.allowsModernInventory());

        FlysafeProtocolGate failure = gateWithArea(2);
        failure.recordFailureCallback();
        failure.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42, new byte[]{10});
        FlysafeProtocolGate.Snapshot failureSnapshot = failure.close(100);
        assertEquals(FlysafeProtocolGate.Decision.GATE_INVALIDATED,
                failureSnapshot.getDecision());
        assertFalse(failureSnapshot.allowsModernInventory());
    }

    @Test
    public void unrelatedAndLateCallbacksNeverMutateDecision() {
        FlysafeProtocolGate gate = new FlysafeProtocolGate();
        gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x55, new byte[]{10});
        FlysafeProtocolGate.Snapshot snapshot = gate.close(100);
        gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 9, areaPayload(2));
        assertEquals(FlysafeProtocolGate.Decision.GATE_UNOBSERVED,
                snapshot.getDecision());
    }

    @Test
    public void displayDoesNotContainPayloadOrSenderValues() {
        FlysafeProtocolGate gate = gateWithArea(2);
        gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42, new byte[]{10});
        String display = gate.close(1234).display();
        assertFalse(display.contains("03:00"));
        assertFalse(display.contains("02:04"));
        assertFalse(display.contains("00800000"));
        assertTrue(display.contains("外部 Binder 不可见"));
        assertFalse(display.contains("senderId"));
        assertFalse(display.contains("receiverId"));
    }

    private static FlysafeProtocolGate gateWithArea(int version) {
        FlysafeProtocolGate gate = new FlysafeProtocolGate();
        gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 9, areaPayload(version));
        return gate;
    }

    private static Integer areaOnly(byte[] bytesAtThreeAndFour) {
        FlysafeProtocolGate gate = new FlysafeProtocolGate();
        byte[] payload = new byte[8];
        payload[3] = bytesAtThreeAndFour[0];
        payload[4] = bytesAtThreeAndFour[1];
        gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 9, payload);
        return gate.close(100).getVersion();
    }

    private static Boolean whitelistOnly(byte[] payload) {
        FlysafeProtocolGate gate = gateWithArea(1);
        gate.observe(SENDER_TYPE, SENDER_ID, RECEIVER_TYPE, RECEIVER_ID,
                3, 0x42, payload);
        return gate.close(100).getSupported();
    }

    private static byte[] areaPayload(int version) {
        byte[] payload = new byte[8];
        int top2 = version == 255 ? 3 : version;
        int raw16 = top2 << 14;
        payload[3] = (byte) raw16;
        payload[4] = (byte) (raw16 >>> 8);
        return payload;
    }
}
