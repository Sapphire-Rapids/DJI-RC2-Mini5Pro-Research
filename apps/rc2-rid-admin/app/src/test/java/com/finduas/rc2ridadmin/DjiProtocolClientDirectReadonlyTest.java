package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicBoolean;

import org.junit.Test;

/** Binder-free coverage for the fixed-route active-read-only 11/11 fallback. */
public final class DjiProtocolClientDirectReadonlyTest {
    @Test
    public void directPassHasOneExactRouteAndV34SelectorOrder() throws Exception {
        DjiProtocolClient client = newClientWithoutBinder();
        DjiProtocolClient.DirectFlysafeReadonlyPass pass =
                client.beginDirectFlysafeReadonlyProbe(() -> false);
        DjiProtocolClient.Route route = pass.getRoute();

        assertEquals(0x02, route.senderType);
        assertEquals(0x04, route.senderId);
        assertEquals(0x12, route.receiverType);
        assertEquals(0x04, route.receiverId);
        assertTrue(DjiProtocolClient.isExactDirectFlysafeReadonlyRoute(route));

        pass.authorize(client, route, new byte[] {0, 1});
        pass.authorize(client, route, new byte[] {0, 0});
        pass.authorize(client, route, new byte[] {0, 2});
        assertEquals(3, pass.getRequestCount());
        assertTrue(pass.isActive());

        pass.close();
        assertFalse(pass.isActive());
        assertMessageContains(IllegalStateException.class,
                "DIRECT_FLYSAFE_READONLY_PASS_MISSING_OR_MISMATCHED",
                () -> pass.authorize(client, route, new byte[] {0, 4}));
    }

    @Test
    public void directPassRejectsV2AndEveryRouteFallbackInsteadOfScanning()
            throws Exception {
        DjiProtocolClient client = newClientWithoutBinder();
        DjiProtocolClient.DirectFlysafeReadonlyPass v2 =
                client.beginDirectFlysafeReadonlyProbe(() -> false);
        assertThrows(IllegalArgumentException.class,
                () -> client.queryDirectFlysafeReadonly(v2, new byte[] {0}));
        assertFalse(v2.isActive());
        assertEquals(0, v2.getRequestCount());

        for (DjiProtocolClient.Route candidate : new DjiProtocolClient.Route[] {
                new DjiProtocolClient.Route("sender0", 0, 2, 4, 0x12),
                new DjiProtocolClient.Route("sender5", 5, 2, 4, 0x12),
                new DjiProtocolClient.Route("v3-default", 4, 2, 0, 3),
                new DjiProtocolClient.Route("v4-default", 4, 2, 5, 17),
                DjiProtocolClient.RC2_LEGACY_FC
        }) {
            DjiProtocolClient.DirectFlysafeReadonlyPass pass =
                    client.beginDirectFlysafeReadonlyProbe(() -> false);
            assertFalse(DjiProtocolClient.isExactDirectFlysafeReadonlyRoute(candidate));
            assertMessageContains(IllegalStateException.class,
                    "DIRECT_FLYSAFE_READONLY_PASS_MISSING_OR_MISMATCHED",
                    () -> pass.authorize(client, candidate, new byte[] {0, 1}));
            assertFalse(pass.isActive());
            assertEquals(0, pass.getRequestCount());
        }
    }

    @Test
    public void cancellationConsumesPassBeforeAnotherSelectorCanBeSent() throws Exception {
        DjiProtocolClient client = newClientWithoutBinder();
        AtomicBoolean cancelled = new AtomicBoolean(false);
        DjiProtocolClient.DirectFlysafeReadonlyPass pass =
                client.beginDirectFlysafeReadonlyProbe(cancelled::get);

        pass.authorize(client, pass.getRoute(), new byte[] {0, 1});
        cancelled.set(true);
        assertMessageContains(IllegalStateException.class,
                "DIRECT_FLYSAFE_READONLY_CANCELLED",
                () -> pass.authorize(client, pass.getRoute(), new byte[] {0, 0}));
        assertEquals(1, pass.getRequestCount());
        assertFalse(pass.isActive());

        assertMessageContains(IllegalStateException.class,
                "DIRECT_FLYSAFE_READONLY_CANCELLED_BEFORE_START",
                () -> client.beginDirectFlysafeReadonlyProbe(() -> true));
    }

    @Test
    public void canonicalCompletionRequiresGroupPlusEveryParserPage() throws Exception {
        DjiProtocolClient client = newClientWithoutBinder();
        FlysafeRidInventory.Result empty = emptyInventory();
        FlysafeRidInventory.Result controlCapable = controlCapableEmptyInventory();
        try {
            DjiProtocolClient.DirectFlysafeReadonlyPass complete =
                    client.beginDirectFlysafeReadonlyProbe(() -> false);
            complete.authorize(client, complete.getRoute(), new byte[] {0, 1});
            complete.authorize(client, complete.getRoute(), new byte[] {0, 0});
            client.finishDirectFlysafeReadonlyProbe(complete, empty);
            assertFalse(complete.isActive());

            DjiProtocolClient.DirectFlysafeReadonlyPass missingTerminator =
                    client.beginDirectFlysafeReadonlyProbe(() -> false);
            missingTerminator.authorize(
                    client, missingTerminator.getRoute(), new byte[] {0, 1});
            assertMessageContains(IllegalStateException.class,
                    "DIRECT_FLYSAFE_READONLY_RESULT_NOT_CANONICAL",
                    () -> client.finishDirectFlysafeReadonlyProbe(
                            missingTerminator, empty));
            assertFalse(missingTerminator.isActive());

            DjiProtocolClient.DirectFlysafeReadonlyPass wrongParserMode =
                    client.beginDirectFlysafeReadonlyProbe(() -> false);
            wrongParserMode.authorize(
                    client, wrongParserMode.getRoute(), new byte[] {0, 1});
            wrongParserMode.authorize(
                    client, wrongParserMode.getRoute(), new byte[] {0, 0});
            assertMessageContains(IllegalStateException.class,
                    "DIRECT_FLYSAFE_READONLY_RESULT_NOT_CANONICAL",
                    () -> client.finishDirectFlysafeReadonlyProbe(
                            wrongParserMode, controlCapable));
            assertFalse(wrongParserMode.isActive());
        } finally {
            empty.close();
            controlCapable.close();
        }
    }

    @Test
    public void directQueryProofCannotAuthorizeElevenTwelve() throws Exception {
        DjiProtocolClient client = newClientWithoutBinder();
        DjiProtocolClient.DirectFlysafeReadonlyPass pass =
                client.beginDirectFlysafeReadonlyProbe(() -> false);
        Class<?> dispatchClass = Class.forName(
                DjiProtocolClient.class.getName() + "$FlysafeSetDispatch");
        Class<?> queryAuthorizationClass = Class.forName(
                DjiProtocolClient.class.getName() + "$FlysafeQueryAuthorization");
        assertTrue(Modifier.isPrivate(queryAuthorizationClass.getModifiers()));
        assertTrue(queryAuthorizationClass.isAssignableFrom(
                DjiProtocolClient.DirectFlysafeReadonlyPass.class));
        assertFalse(dispatchClass.isAssignableFrom(
                DjiProtocolClient.DirectFlysafeReadonlyPass.class));
        assertFalse(DjiProtocolClient.FlysafeWritePermit.class.isAssignableFrom(
                DjiProtocolClient.DirectFlysafeReadonlyPass.class));
        Method sender = DjiProtocolClient.class.getDeclaredMethod(
                "sendAllowedRequest",
                DjiProtocolClient.Route.class,
                int.class,
                int.class,
                byte[].class,
                int.class,
                queryAuthorizationClass,
                dispatchClass);
        sender.setAccessible(true);

        InvocationTargetException rejected = assertThrows(
                InvocationTargetException.class,
                () -> sender.invoke(
                        client,
                        pass.getRoute(),
                        0x11,
                        0x12,
                        new byte[] {0, 1, 0, 0, 0, 1, 0},
                        6000,
                        pass,
                        null));
        assertTrue(rejected.getCause() instanceof IllegalStateException);
        assertTrue(rejected.getCause().getMessage().contains(
                "FLYSAFE_WRITE_PERMIT_MISSING_OR_MISMATCHED"));
        assertEquals(0, pass.getRequestCount());
        assertTrue(pass.isActive());

        Method query = DjiProtocolClient.class.getDeclaredMethod(
                "queryDirectFlysafeReadonly",
                DjiProtocolClient.DirectFlysafeReadonlyPass.class,
                byte[].class);
        assertFalse(Modifier.isPublic(query.getModifiers()));
        assertEquals(DjiProtocolClient.Reply.class, query.getReturnType());
        assertThrows(NoSuchMethodException.class, () ->
                DjiProtocolClient.class.getDeclaredMethod(
                        "queryDirectFlysafeReadonly",
                        DjiProtocolClient.DirectFlysafeReadonlyPass.class,
                        int.class,
                        byte[].class));
        assertNotEquals(DjiProtocolClient.FlysafeWritePermit.class, query.getParameterTypes()[0]);
    }

    @Test
    public void directProbeHasNoApplicationRetryAndOneBoundedVendorSchedule() {
        assertEquals(0, DjiProtocolClient.directFlysafeReadonlyApplicationRetryCount());
        assertEquals(3, DjiProtocolClient.directFlysafeReadonlyTransportAttemptCeiling());
        assertEquals(19_000L,
                DjiProtocolClient.callbackWaitMillis(
                        DjiProtocolClient.FLYSAFE_COMMAND_TIMEOUT_MS));
    }

    @Test
    public void directFailureDisplayIncludesRedactedTransportFactsButNotRawData() {
        byte[] raw = "RAW-LICENSE-DATA-1234".getBytes(StandardCharsets.US_ASCII);
        DjiProtocolClient.Reply reply = new DjiProtocolClient.Reply(
                false,
                "DJI callback failure=7",
                0x11,
                7,
                raw,
                "callback=FAILURE; ecode{id=7 desc=<redacted>}; data=<redacted>");

        String display = reply.displayDirectReadonlyFailure();

        assertTrue(display.contains("failure=DJI callback failure=7"));
        assertTrue(display.contains("ccode_or_ecode=7"));
        assertTrue(display.contains("ecode{id=7 desc=<redacted>}"));
        assertFalse(display.contains("RAW-LICENSE-DATA-1234"));
        assertFalse(display.contains("5241572D4C4943454E53452D444154412D31323334"));
    }

    private static FlysafeRidInventory.Result emptyInventory() throws Exception {
        AtomicBoolean group = new AtomicBoolean(true);
        return FlysafeRidInventory.queryReadOnly(payload -> {
            if (group.getAndSet(false)) {
                // Nonempty valid protobuf with no field 5 means proto3 licenses_count == 0.
                return new FlysafeRidInventory.Response(true, 0, new byte[] {0x08, 0x01});
            }
            return new FlysafeRidInventory.Response(true, 1, null);
        });
    }

    private static FlysafeRidInventory.Result controlCapableEmptyInventory() throws Exception {
        AtomicBoolean group = new AtomicBoolean(true);
        return FlysafeRidInventory.query(payload -> {
            if (group.getAndSet(false)) {
                return new FlysafeRidInventory.Response(true, 0, new byte[] {0x08, 0x01});
            }
            return new FlysafeRidInventory.Response(true, 1, null);
        });
    }

    private static DjiProtocolClient newClientWithoutBinder() throws Exception {
        Class<?> unsafeClass = Class.forName("sun.misc.Unsafe");
        Field singleton = unsafeClass.getDeclaredField("theUnsafe");
        singleton.setAccessible(true);
        Object unsafe = singleton.get(null);
        Method allocateInstance = unsafeClass.getMethod("allocateInstance", Class.class);
        return (DjiProtocolClient) allocateInstance.invoke(unsafe, DjiProtocolClient.class);
    }

    private static <T extends Throwable> void assertMessageContains(
            Class<T> expectedType,
            String expectedText,
            ThrowingRunnable runnable) {
        T error = assertThrows(expectedType, runnable::run);
        assertTrue(error.getMessage(), error.getMessage().contains(expectedText));
    }

    private interface ThrowingRunnable {
        void run() throws Exception;
    }
}
