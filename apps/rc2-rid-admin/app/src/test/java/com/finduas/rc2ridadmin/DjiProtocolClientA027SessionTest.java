package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import java.io.ByteArrayOutputStream;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicBoolean;

import org.junit.Test;

/** Focused JVM coverage for the Binder-free A-027 inventory/mutation session state machine. */
public final class DjiProtocolClientA027SessionTest {
    private static final long LICENSE_ID = 0xfedc_ba98L;
    private static final int BASELINE_DISABLED_STATUS = 0xa4;
    private static final int TARGET_ENABLED_STATUS = 0xa6;
    private static final int UNUSABLE_CHANGED_STATUS = 0xac;

    @Test
    public void threePassesUseTheSameGateDerivedDynamicRouteInMutationOrder()
            throws Exception {
        SessionFixture fixture = new SessionFixture(6);
        FlysafeRidInventory.Result baseline = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        FlysafeRidInventory.Result targetReadback = singleRidInventory(
                TARGET_ENABLED_STATUS);
        FlysafeRidInventory.Result restoredReadback = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        try {
            Object token = fixture.client.modernFlysafeSessionMarker(fixture.observation);

            DjiProtocolClient.FlysafeInventoryPass baselinePass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            assertDynamicRoute(baselinePass, fixture.client, 6);
            completePass(fixture.client, baselinePass, baseline);
            FlysafeRidInventory.OpaqueRidHandle target =
                    baseline.openSingleEligibleHandle(token);

            consumeAndClear(fixture.client.issueModernFlysafeWritePermit(
                    fixture.observation, token, target, true), fixture.client);
            assertTrue(fixture.observation.isRecoveryMode());
            assertFalse(fixture.observation.isSafelyAtBaseline());

            DjiProtocolClient.FlysafeInventoryPass targetPass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            assertDynamicRoute(targetPass, fixture.client, 6);
            completePass(fixture.client, targetPass, targetReadback);
            assertEquals(DjiProtocolClient.ReadbackClassification.TARGET,
                    fixture.client.classifyModernFlysafeReadback(
                            fixture.observation, target, targetReadback));

            consumeAndClear(fixture.client.issueModernFlysafeWritePermit(
                    fixture.observation, token, target, false), fixture.client);
            DjiProtocolClient.FlysafeInventoryPass restorePass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            assertDynamicRoute(restorePass, fixture.client, 6);
            completePass(fixture.client, restorePass, restoredReadback);
            assertEquals(DjiProtocolClient.ReadbackClassification.BASELINE,
                    fixture.client.classifyModernFlysafeReadback(
                            fixture.observation, target, restoredReadback));

            assertTrue(fixture.observation.isSafelyAtBaseline());
            fixture.client.finishModernFlysafeSession(fixture.observation);
            assertFalse(fixture.observation.allowsModernInventory());
        } finally {
            restoredReadback.close();
            targetReadback.close();
            baseline.close();
        }
    }

    @Test
    public void mutationCannotSkipACompletedPassOrItsExactReadback() throws Exception {
        SessionFixture missingBaselinePass = new SessionFixture(3);
        FlysafeRidInventory.Result unprovenBaseline = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        try {
            Object token = missingBaselinePass.client.modernFlysafeSessionMarker(
                    missingBaselinePass.observation);
            FlysafeRidInventory.OpaqueRidHandle target =
                    unprovenBaseline.openSingleEligibleHandle(token);
            DjiProtocolClient.FlysafeWritePermit permit =
                    missingBaselinePass.client.issueModernFlysafeWritePermit(
                            missingBaselinePass.observation, token, target, true);
            assertMessageContains(IllegalStateException.class,
                    "FLYSAFE_WRITE_ORDER_INVALID",
                    () -> consumeAndClear(permit, missingBaselinePass.client));
        } finally {
            unprovenBaseline.close();
        }

        SessionFixture missingForwardReadback = new SessionFixture(5);
        FlysafeRidInventory.Result baseline = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        FlysafeRidInventory.Result targetReadback = singleRidInventory(
                TARGET_ENABLED_STATUS);
        try {
            Object token = missingForwardReadback.client.modernFlysafeSessionMarker(
                    missingForwardReadback.observation);
            DjiProtocolClient.FlysafeInventoryPass baselinePass =
                    missingForwardReadback.client.beginModernFlysafeInventoryPass(
                            missingForwardReadback.observation);
            completePass(missingForwardReadback.client, baselinePass, baseline);
            FlysafeRidInventory.OpaqueRidHandle target =
                    baseline.openSingleEligibleHandle(token);
            consumeAndClear(missingForwardReadback.client.issueModernFlysafeWritePermit(
                    missingForwardReadback.observation, token, target, true),
                    missingForwardReadback.client);

            DjiProtocolClient.FlysafeInventoryPass readbackPass =
                    missingForwardReadback.client.beginModernFlysafeInventoryPass(
                            missingForwardReadback.observation);
            completePass(missingForwardReadback.client, readbackPass, targetReadback);
            DjiProtocolClient.FlysafeWritePermit prematureRestore =
                    missingForwardReadback.client.issueModernFlysafeWritePermit(
                            missingForwardReadback.observation, token, target, false);
            assertMessageContains(IllegalStateException.class,
                    "FLYSAFE_RESTORE_NOT_ADMITTED",
                    () -> consumeAndClear(prematureRestore, missingForwardReadback.client));
        } finally {
            targetReadback.close();
            baseline.close();
        }
    }

    @Test
    public void transientUnusableReadbackRollsBackCompletionAndNextPassCanClassify()
            throws Exception {
        SessionFixture fixture = new SessionFixture(5);
        FlysafeRidInventory.Result baseline = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        FlysafeRidInventory.Result transientMismatch = singleRidInventory(
                UNUSABLE_CHANGED_STATUS);
        FlysafeRidInventory.Result targetReadback = singleRidInventory(
                TARGET_ENABLED_STATUS);
        try {
            Object token = fixture.client.modernFlysafeSessionMarker(fixture.observation);
            DjiProtocolClient.FlysafeInventoryPass baselinePass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, baselinePass, baseline);
            FlysafeRidInventory.OpaqueRidHandle target =
                    baseline.openSingleEligibleHandle(token);
            consumeAndClear(fixture.client.issueModernFlysafeWritePermit(
                    fixture.observation, token, target, true), fixture.client);
            assertEquals(1, privateInt(fixture.observation, "mutationAttempts"));

            DjiProtocolClient.FlysafeInventoryPass firstReadbackPass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, firstReadbackPass, transientMismatch);
            assertMessageContains(IllegalStateException.class,
                    "FLYSAFE_FORWARD_READBACK_UNUSABLE",
                    () -> fixture.client.classifyModernFlysafeReadback(
                            fixture.observation, target, transientMismatch));
            assertTrue(fixture.observation.allowsModernInventory());
            assertEquals(1, privateInt(fixture.observation, "completedInventoryPasses"));
            assertEquals(1, privateInt(fixture.observation, "mutationAttempts"));

            DjiProtocolClient.FlysafeInventoryPass secondReadbackPass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, secondReadbackPass, targetReadback);
            assertEquals(DjiProtocolClient.ReadbackClassification.TARGET,
                    fixture.client.classifyModernFlysafeReadback(
                            fixture.observation, target, targetReadback));
            assertEquals(2, privateInt(fixture.observation, "completedInventoryPasses"));
            assertEquals(1, privateInt(fixture.observation, "mutationAttempts"));
            assertFalse(fixture.observation.isSafelyAtBaseline());
        } finally {
            targetReadback.close();
            transientMismatch.close();
            baseline.close();
        }
    }

    @Test
    public void recoveryReadbacksHaveNoPermanentSessionAttemptCeiling()
            throws Exception {
        SessionFixture fixture = new SessionFixture(5);
        FlysafeRidInventory.Result baseline = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        FlysafeRidInventory.Result[] mismatches = {
                singleRidInventory(UNUSABLE_CHANGED_STATUS),
                singleRidInventory(UNUSABLE_CHANGED_STATUS),
                singleRidInventory(UNUSABLE_CHANGED_STATUS)
        };
        FlysafeRidInventory.Result fourthTarget = singleRidInventory(
                TARGET_ENABLED_STATUS);
        try {
            Object token = fixture.client.modernFlysafeSessionMarker(fixture.observation);
            DjiProtocolClient.FlysafeInventoryPass baselinePass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, baselinePass, baseline);
            FlysafeRidInventory.OpaqueRidHandle target =
                    baseline.openSingleEligibleHandle(token);
            consumeAndClear(fixture.client.issueModernFlysafeWritePermit(
                    fixture.observation, token, target, true), fixture.client);

            for (int index = 0; index < mismatches.length; index++) {
                DjiProtocolClient.FlysafeInventoryPass readbackPass =
                        fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
                completePass(fixture.client, readbackPass, mismatches[index]);
                final int mismatchIndex = index;
                assertMessageContains(IllegalStateException.class,
                        "FLYSAFE_FORWARD_READBACK_UNUSABLE",
                        () -> fixture.client.classifyModernFlysafeReadback(
                                fixture.observation, target, mismatches[mismatchIndex]));
                assertEquals(index + 1,
                        privateInt(fixture.observation, "inventoryPassAttemptsAtStage"));
                assertEquals(1,
                        privateInt(fixture.observation, "completedInventoryPasses"));
                assertEquals(1, privateInt(fixture.observation, "mutationAttempts"));
                assertTrue(fixture.observation.allowsModernInventory());
            }

            DjiProtocolClient.FlysafeInventoryPass fourthPass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, fourthPass, fourthTarget);
            assertEquals(4,
                    privateInt(fixture.observation, "inventoryPassAttemptsAtStage"));
            assertEquals(1, privateInt(fixture.observation, "mutationAttempts"));
            assertEquals(DjiProtocolClient.ReadbackClassification.TARGET,
                    fixture.client.classifyModernFlysafeReadback(
                            fixture.observation, target, fourthTarget));
            assertEquals(1, privateInt(fixture.observation, "mutationAttempts"));
            assertEquals(0,
                    privateInt(fixture.observation, "inventoryPassAttemptsAtStage"));
            assertFalse(fixture.observation.isSafelyAtBaseline());
            assertTrue(fixture.observation.allowsModernInventory());
        } finally {
            fourthTarget.close();
            for (FlysafeRidInventory.Result mismatch : mismatches) {
                mismatch.close();
            }
            baseline.close();
        }
    }

    @Test
    public void duplicateBeginAfterForwardIsRejectedWithoutDestroyingActivePass()
            throws Exception {
        SessionFixture fixture = new SessionFixture(6);
        FlysafeRidInventory.Result baseline = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        FlysafeRidInventory.Result targetReadback = singleRidInventory(
                TARGET_ENABLED_STATUS);
        try {
            Object token = fixture.client.modernFlysafeSessionMarker(fixture.observation);
            DjiProtocolClient.FlysafeInventoryPass baselinePass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, baselinePass, baseline);
            FlysafeRidInventory.OpaqueRidHandle target =
                    baseline.openSingleEligibleHandle(token);
            consumeAndClear(fixture.client.issueModernFlysafeWritePermit(
                    fixture.observation, token, target, true), fixture.client);

            DjiProtocolClient.FlysafeInventoryPass originalReadbackPass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            assertMessageContains(IllegalStateException.class,
                    "FLYSAFE_INVENTORY_PASS_ALREADY_ACTIVE",
                    () -> fixture.client.beginModernFlysafeInventoryPass(
                            fixture.observation));
            assertTrue(fixture.observation.allowsModernInventory());
            assertEquals(1, privateInt(fixture.observation, "mutationAttempts"));

            completePass(fixture.client, originalReadbackPass, targetReadback);
            assertEquals(DjiProtocolClient.ReadbackClassification.TARGET,
                    fixture.client.classifyModernFlysafeReadback(
                            fixture.observation, target, targetReadback));
            assertEquals(1, privateInt(fixture.observation, "mutationAttempts"));
            assertTrue(fixture.observation.allowsModernInventory());
        } finally {
            targetReadback.close();
            baseline.close();
        }
    }

    @Test
    public void recoverySelectorFailureAllowsFreshPassThenRestoreToBaseline()
            throws Exception {
        SessionFixture fixture = new SessionFixture(6);
        FlysafeRidInventory.Result baseline = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        FlysafeRidInventory.Result targetReadback = singleRidInventory(
                TARGET_ENABLED_STATUS);
        FlysafeRidInventory.Result restoredReadback = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        try {
            Object token = fixture.client.modernFlysafeSessionMarker(fixture.observation);
            DjiProtocolClient.FlysafeInventoryPass baselinePass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, baselinePass, baseline);
            FlysafeRidInventory.OpaqueRidHandle target =
                    baseline.openSingleEligibleHandle(token);
            consumeAndClear(fixture.client.issueModernFlysafeWritePermit(
                    fixture.observation, token, target, true), fixture.client);

            DjiProtocolClient.FlysafeInventoryPass malformedPass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            authorize(malformedPass, fixture.client, malformedPass.getRoute(),
                    FlysafeRidInventory.startPayload());
            assertMessageContains(IllegalArgumentException.class,
                    "FlySafe page selector is out of order",
                    () -> authorize(malformedPass, fixture.client, malformedPass.getRoute(),
                            FlysafeRidInventory.pagePayload(1)));
            assertTrue(fixture.observation.allowsModernInventory());
            assertEquals(1, privateInt(fixture.observation, "completedInventoryPasses"));
            assertEquals(1, privateInt(fixture.observation, "mutationAttempts"));

            DjiProtocolClient.FlysafeInventoryPass freshTargetPass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, freshTargetPass, targetReadback);
            assertEquals(DjiProtocolClient.ReadbackClassification.TARGET,
                    fixture.client.classifyModernFlysafeReadback(
                            fixture.observation, target, targetReadback));

            consumeAndClear(fixture.client.issueModernFlysafeWritePermit(
                    fixture.observation, token, target, false), fixture.client);
            assertEquals(2, privateInt(fixture.observation, "mutationAttempts"));
            DjiProtocolClient.FlysafeInventoryPass restorePass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, restorePass, restoredReadback);
            assertEquals(DjiProtocolClient.ReadbackClassification.BASELINE,
                    fixture.client.classifyModernFlysafeReadback(
                            fixture.observation, target, restoredReadback));
            assertTrue(fixture.observation.isSafelyAtBaseline());
            fixture.client.finishModernFlysafeSession(fixture.observation);
        } finally {
            restoredReadback.close();
            targetReadback.close();
            baseline.close();
        }
    }

    @Test
    public void wrongRestoreStateRequestDoesNotDestroyRecoverySession()
            throws Exception {
        SessionFixture fixture = new SessionFixture(6);
        FlysafeRidInventory.Result baseline = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        FlysafeRidInventory.Result targetReadback = singleRidInventory(
                TARGET_ENABLED_STATUS);
        FlysafeRidInventory.Result restoredReadback = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        try {
            Object token = fixture.client.modernFlysafeSessionMarker(fixture.observation);
            DjiProtocolClient.FlysafeInventoryPass baselinePass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, baselinePass, baseline);
            FlysafeRidInventory.OpaqueRidHandle target =
                    baseline.openSingleEligibleHandle(token);
            consumeAndClear(fixture.client.issueModernFlysafeWritePermit(
                    fixture.observation, token, target, true), fixture.client);

            DjiProtocolClient.FlysafeInventoryPass targetPass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, targetPass, targetReadback);
            assertEquals(DjiProtocolClient.ReadbackClassification.TARGET,
                    fixture.client.classifyModernFlysafeReadback(
                            fixture.observation, target, targetReadback));

            DjiProtocolClient.FlysafeWritePermit wrongRestore =
                    fixture.client.issueModernFlysafeWritePermit(
                            fixture.observation, token, target, true);
            assertMessageContains(IllegalStateException.class,
                    "FLYSAFE_RESTORE_NOT_ADMITTED",
                    () -> consumeAndClear(wrongRestore, fixture.client));
            assertTrue(wrongRestore.isConsumed());
            assertTrue(fixture.observation.allowsModernInventory());
            assertEquals(1, privateInt(fixture.observation, "mutationAttempts"));
            assertFalse(fixture.observation.isSafelyAtBaseline());

            consumeAndClear(fixture.client.issueModernFlysafeWritePermit(
                    fixture.observation, token, target, false), fixture.client);
            assertEquals(2, privateInt(fixture.observation, "mutationAttempts"));
            DjiProtocolClient.FlysafeInventoryPass restorePass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, restorePass, restoredReadback);
            assertEquals(DjiProtocolClient.ReadbackClassification.BASELINE,
                    fixture.client.classifyModernFlysafeReadback(
                            fixture.observation, target, restoredReadback));
            assertTrue(fixture.observation.isSafelyAtBaseline());
            fixture.client.finishModernFlysafeSession(fixture.observation);
        } finally {
            restoredReadback.close();
            targetReadback.close();
            baseline.close();
        }
    }

    @Test
    public void cancellationAndInterruptAfterMutationStillPermitMandatoryRecovery()
            throws Exception {
        SessionFixture fixture = new SessionFixture(7);
        FlysafeRidInventory.Result baseline = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        FlysafeRidInventory.Result targetReadback = singleRidInventory(
                TARGET_ENABLED_STATUS);
        FlysafeRidInventory.Result restoredReadback = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        try {
            Object token = fixture.client.modernFlysafeSessionMarker(fixture.observation);
            DjiProtocolClient.FlysafeInventoryPass baselinePass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, baselinePass, baseline);
            FlysafeRidInventory.OpaqueRidHandle target =
                    baseline.openSingleEligibleHandle(token);
            consumeAndClear(fixture.client.issueModernFlysafeWritePermit(
                    fixture.observation, token, target, true), fixture.client);

            fixture.cancelled.set(true);
            Thread.currentThread().interrupt();

            DjiProtocolClient.FlysafeInventoryPass targetPass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, targetPass, targetReadback);
            assertEquals(DjiProtocolClient.ReadbackClassification.TARGET,
                    fixture.client.classifyModernFlysafeReadback(
                            fixture.observation, target, targetReadback));
            consumeAndClear(fixture.client.issueModernFlysafeWritePermit(
                    fixture.observation, token, target, false), fixture.client);

            DjiProtocolClient.FlysafeInventoryPass restorePass =
                    fixture.client.beginModernFlysafeInventoryPass(fixture.observation);
            completePass(fixture.client, restorePass, restoredReadback);
            assertEquals(DjiProtocolClient.ReadbackClassification.BASELINE,
                    fixture.client.classifyModernFlysafeReadback(
                            fixture.observation, target, restoredReadback));
            assertTrue(fixture.observation.wasCancellationOrInterruptObserved());
            assertTrue(Thread.currentThread().isInterrupted());
            fixture.client.finishModernFlysafeSession(fixture.observation);
        } finally {
            // Do not leak the intentional interrupt into Gradle's JUnit worker.
            Thread.interrupted();
            restoredReadback.close();
            targetReadback.close();
            baseline.close();
        }
    }

    @Test
    public void closeRejectsActivePassAndUnrestoredMutation() throws Exception {
        SessionFixture activePassFixture = new SessionFixture(1);
        DjiProtocolClient.FlysafeInventoryPass abandoned =
                activePassFixture.client.beginModernFlysafeInventoryPass(
                        activePassFixture.observation);
        assertMessageContains(IllegalStateException.class,
                "FLYSAFE_SESSION_HAS_ACTIVE_INVENTORY_PASS",
                () -> activePassFixture.client.finishModernFlysafeSession(
                        activePassFixture.observation));
        abandoned.close();
        abandoned.close();
        assertFalse(activePassFixture.observation.allowsModernInventory());
        activePassFixture.client.finishModernFlysafeSession(
                activePassFixture.observation);

        SessionFixture mutatedFixture = new SessionFixture(2);
        FlysafeRidInventory.Result baseline = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        try {
            Object token = mutatedFixture.client.modernFlysafeSessionMarker(
                    mutatedFixture.observation);
            DjiProtocolClient.FlysafeInventoryPass pass =
                    mutatedFixture.client.beginModernFlysafeInventoryPass(
                            mutatedFixture.observation);
            completePass(mutatedFixture.client, pass, baseline);
            FlysafeRidInventory.OpaqueRidHandle target =
                    baseline.openSingleEligibleHandle(token);
            consumeAndClear(mutatedFixture.client.issueModernFlysafeWritePermit(
                    mutatedFixture.observation, token, target, true),
                    mutatedFixture.client);
            assertMessageContains(IllegalStateException.class,
                    "FLYSAFE_SESSION_CANNOT_CLOSE_BEFORE_CONFIRMED_BASELINE",
                    () -> mutatedFixture.client.finishModernFlysafeSession(
                            mutatedFixture.observation));
            assertTrue(mutatedFixture.observation.allowsModernInventory());
        } finally {
            baseline.close();
        }
    }

    @Test
    public void passCompletionRequiresCanonicalRequestCountAndOpenResult()
            throws Exception {
        SessionFixture countMismatch = new SessionFixture(4);
        FlysafeRidInventory.Result result = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        try {
            DjiProtocolClient.FlysafeInventoryPass pass =
                    countMismatch.client.beginModernFlysafeInventoryPass(
                            countMismatch.observation);
            authorize(pass, countMismatch.client, pass.getRoute(),
                    FlysafeRidInventory.startPayload());
            assertMessageContains(IllegalStateException.class,
                    "FLYSAFE_INVENTORY_NOT_CANONICAL",
                    () -> countMismatch.client.finishModernFlysafeInventoryPass(
                            pass, result));
            assertFalse(countMismatch.observation.allowsModernInventory());
        } finally {
            result.close();
        }

        SessionFixture closedResultFixture = new SessionFixture(4);
        FlysafeRidInventory.Result closed = singleRidInventory(
                BASELINE_DISABLED_STATUS);
        DjiProtocolClient.FlysafeInventoryPass pass =
                closedResultFixture.client.beginModernFlysafeInventoryPass(
                        closedResultFixture.observation);
        authorizeAll(pass, closedResultFixture.client, closed.getPageCalls());
        closed.close();
        assertMessageContains(IllegalStateException.class,
                "FLYSAFE_INVENTORY_NOT_CANONICAL",
                () -> closedResultFixture.client.finishModernFlysafeInventoryPass(
                        pass, closed));
    }

    private static void completePass(
            DjiProtocolClient client,
            DjiProtocolClient.FlysafeInventoryPass pass,
            FlysafeRidInventory.Result result) throws Exception {
        authorizeAll(pass, client, result.getPageCalls());
        client.finishModernFlysafeInventoryPass(pass, result);
    }

    private static void authorizeAll(
            DjiProtocolClient.FlysafeInventoryPass pass,
            DjiProtocolClient client,
            int pageCalls) throws Exception {
        authorize(pass, client, pass.getRoute(), FlysafeRidInventory.startPayload());
        for (int index = 0; index < pageCalls; index++) {
            authorize(pass, client, pass.getRoute(), FlysafeRidInventory.pagePayload(index));
        }
    }

    private static void assertDynamicRoute(
            DjiProtocolClient.FlysafeInventoryPass pass,
            DjiProtocolClient client,
            int expectedSenderId) throws Exception {
        DjiProtocolClient.Route route = pass.getRoute();
        assertEquals(0x02, route.senderType);
        assertEquals(expectedSenderId, route.senderId);
        assertEquals(0x12, route.receiverType);
        assertEquals(0x04, route.receiverId);
        DjiProtocolClient.validateAllowedRequest(
                route,
                DjiProtocolClient.CMD_SET_ADSB,
                DjiProtocolClient.CMD_FLYSAFE_LICENSE_LIST,
                FlysafeRidInventory.startPayload(),
                DjiProtocolClient.FLYSAFE_COMMAND_TIMEOUT_MS);

        DjiProtocolClient.Route oldFixedRoute = DjiProtocolClient.MODERN_FLYSAFE_FC4;
        if (expectedSenderId != oldFixedRoute.senderId) {
            assertMessageContains(IllegalStateException.class,
                    "FLYSAFE_INVENTORY_PASS_MISSING_OR_MISMATCHED",
                    () -> authorize(pass, client, oldFixedRoute,
                            FlysafeRidInventory.startPayload()));
        }
    }

    private static void authorize(
            DjiProtocolClient.FlysafeInventoryPass pass,
            DjiProtocolClient client,
            DjiProtocolClient.Route route,
            byte[] payload) throws Exception {
        Method authorize = DjiProtocolClient.FlysafeInventoryPass.class.getDeclaredMethod(
                "authorize",
                DjiProtocolClient.class,
                DjiProtocolClient.Route.class,
                byte[].class);
        authorize.setAccessible(true);
        invoke(authorize, pass, client, route, payload);
    }

    private static void consumeAndClear(
            DjiProtocolClient.FlysafeWritePermit permit,
            DjiProtocolClient client) throws Exception {
        Method consume = DjiProtocolClient.FlysafeWritePermit.class.getDeclaredMethod(
                "consumeFor", DjiProtocolClient.class);
        consume.setAccessible(true);
        Object dispatch = invoke(consume, permit, client);
        Method clear = dispatch.getClass().getDeclaredMethod("clear");
        clear.setAccessible(true);
        invoke(clear, dispatch);
    }

    private static Object invoke(Method method, Object target, Object... arguments)
            throws Exception {
        try {
            return method.invoke(target, arguments);
        } catch (InvocationTargetException exception) {
            Throwable cause = exception.getCause();
            if (cause instanceof Exception) {
                throw (Exception) cause;
            }
            if (cause instanceof Error) {
                throw (Error) cause;
            }
            throw exception;
        }
    }

    private static int privateInt(Object target, String fieldName) throws Exception {
        Field field = target.getClass().getDeclaredField(fieldName);
        field.setAccessible(true);
        return field.getInt(target);
    }

    private static <T extends Throwable> void assertMessageContains(
            Class<T> expectedType,
            String expectedText,
            ThrowingRunnable runnable) {
        T error = assertThrows(expectedType, runnable::run);
        assertTrue(error.getMessage(), error.getMessage().contains(expectedText));
    }

    private static FlysafeRidInventory.Result singleRidInventory(int status)
            throws Exception {
        FlysafeRidInventory.Response group = response(0, group(1));
        FlysafeRidInventory.Response record = response(
                0, page(status, ridLicense(LICENSE_ID, 2)));
        FlysafeRidInventory.Response terminator = response(1, null);
        FlysafeRidInventory.Response[] responses = {group, record, terminator};
        return FlysafeRidInventory.query(new FlysafeRidInventory.Transport() {
            private int next;

            @Override
            public FlysafeRidInventory.Response fetch(byte[] payload) {
                if (next >= responses.length) {
                    throw new AssertionError("unexpected inventory fetch");
                }
                return responses[next++];
            }
        });
    }

    private static FlysafeRidInventory.Response response(int ccode, byte[] data) {
        return new FlysafeRidInventory.Response(true, ccode, data);
    }

    private static byte[] group(int count) {
        return concat(
                varintField(1, 8),
                bytesField(3, "sn".getBytes(StandardCharsets.UTF_8)),
                varintField(5, count));
    }

    private static byte[] ridLicense(long id, long level) {
        return concat(
                varintField(1, id),
                bytesField(2, "rid".getBytes(StandardCharsets.UTF_8)),
                bytesField(6, bytesField(7, varintField(1, level))));
    }

    private static byte[] page(int status, byte[] license) {
        return concat(new byte[] {(byte) status}, license);
    }

    private static byte[] varintField(int number, long value) {
        return concat(varint(((long) number) << 3), varint(value));
    }

    private static byte[] bytesField(int number, byte[] value) {
        return concat(
                varint((((long) number) << 3) | 2L),
                varint(value.length),
                value);
    }

    private static byte[] varint(long value) {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        long remaining = value;
        while ((remaining & ~0x7fL) != 0L) {
            output.write(((int) remaining & 0x7f) | 0x80);
            remaining >>>= 7;
        }
        output.write((int) remaining);
        return output.toByteArray();
    }

    private static byte[] concat(byte[]... values) {
        int length = 0;
        for (byte[] value : values) {
            length += value.length;
        }
        byte[] result = new byte[length];
        int offset = 0;
        for (byte[] value : values) {
            System.arraycopy(value, 0, result, offset, value.length);
            offset += value.length;
        }
        return result;
    }

    private static DjiProtocolClient.FlysafeGateObservation newObservation(
            DjiProtocolClient owner,
            int dynamicSenderId,
            DjiProtocolClient.CancellationCheck cancellationCheck) throws Exception {
        FlysafeProtocolGate gate = new FlysafeProtocolGate();
        byte[] area = new byte[8];
        area[4] = (byte) 0x80; // V4 (wire version 2).
        gate.observe(0x12, 0x04, 0x02, dynamicSenderId,
                0x03, 0x09, area);
        gate.observe(0x12, 0x04, 0x02, dynamicSenderId,
                0x03, 0x42, new byte[] {10});
        FlysafeProtocolGate.Snapshot snapshot = gate.close(100);
        assertTrue(snapshot.hasProduct139ModernReverseRoute());

        Constructor<DjiProtocolClient.FlysafeGateObservation> constructor =
                DjiProtocolClient.FlysafeGateObservation.class.getDeclaredConstructor(
                        DjiProtocolClient.class,
                        FlysafeProtocolGate.Snapshot.class,
                        String.class,
                        boolean.class,
                        DjiProtocolClient.CancellationCheck.class);
        constructor.setAccessible(true);
        return constructor.newInstance(owner, snapshot, "test", true, cancellationCheck);
    }

    private static DjiProtocolClient newClientWithoutBinder() throws Exception {
        Class<?> unsafeClass = Class.forName("sun.misc.Unsafe");
        Field singleton = unsafeClass.getDeclaredField("theUnsafe");
        singleton.setAccessible(true);
        Object unsafe = singleton.get(null);
        Method allocateInstance = unsafeClass.getMethod("allocateInstance", Class.class);
        return (DjiProtocolClient) allocateInstance.invoke(unsafe, DjiProtocolClient.class);
    }

    private interface ThrowingRunnable {
        void run() throws Exception;
    }

    private static final class SessionFixture {
        final DjiProtocolClient client;
        final AtomicBoolean cancelled = new AtomicBoolean(false);
        final DjiProtocolClient.FlysafeGateObservation observation;

        SessionFixture(int dynamicSenderId) throws Exception {
            client = newClientWithoutBinder();
            observation = newObservation(client, dynamicSenderId, cancelled::get);
        }
    }
}
