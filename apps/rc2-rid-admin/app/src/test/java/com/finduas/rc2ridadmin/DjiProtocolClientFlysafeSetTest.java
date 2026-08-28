package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

import org.junit.Test;

public final class DjiProtocolClientFlysafeSetTest {
    private static final byte[] KNOWN_SET_PAYLOAD = new byte[] {
            0, (byte) 0xcd, (byte) 0xab, 0x34, 0x12, 1, 0
    };

    @Test
    public void exactDynamicReverseRouteAndPayloadAreAllowListed() {
        for (int senderId : new int[] {0, 3, 7}) {
            DjiProtocolClient.Route route = setRoute("live", senderId);
            assertTrue(DjiProtocolClient.isModernFlysafeSetRoute(route));
            DjiProtocolClient.validateAllowedRequest(
                    route,
                    DjiProtocolClient.CMD_SET_ADSB,
                    DjiProtocolClient.CMD_FLYSAFE_SET_LICENSE_ENABLED,
                    KNOWN_SET_PAYLOAD,
                    DjiProtocolClient.FLYSAFE_COMMAND_TIMEOUT_MS);
        }
    }

    @Test
    public void routeTimeoutAndEveryPayloadShapeDriftFailClosed() {
        DjiProtocolClient.Route good = setRoute("live", 3);
        for (DjiProtocolClient.Route route : new DjiProtocolClient.Route[] {
                new DjiProtocolClient.Route("bad", -1, 2, 4, 0x12),
                new DjiProtocolClient.Route("bad", 8, 2, 4, 0x12),
                new DjiProtocolClient.Route("bad", 3, 3, 4, 0x12),
                new DjiProtocolClient.Route("bad", 3, 2, 5, 0x12),
                new DjiProtocolClient.Route("bad", 3, 2, 4, 0x11),
                DjiProtocolClient.RC2_LEGACY_FC
        }) {
            assertFalse(DjiProtocolClient.isModernFlysafeSetRoute(route));
            assertThrows(IllegalArgumentException.class,
                    () -> DjiProtocolClient.validateAllowedRequest(
                            route, 0x11, 0x12, KNOWN_SET_PAYLOAD, 6000));
        }
        assertThrows(IllegalArgumentException.class,
                () -> DjiProtocolClient.validateAllowedRequest(
                        good, 0x11, 0x12, KNOWN_SET_PAYLOAD, 5999));

        for (byte[] payload : new byte[][] {
                null,
                {},
                {0, 1, 2, 3, 4, 1},
                {0, 1, 2, 3, 4, 1, 0, 0},
                {1, 1, 2, 3, 4, 1, 0},
                {0, 0, 0, 0, 0, 1, 0},
                {0, 1, 2, 3, 4, 0, 0},
                {0, 1, 2, 3, 4, 3, 0},
                {0, 1, 2, 3, 4, 2, 1}
        }) {
            assertThrows(IllegalArgumentException.class,
                    () -> DjiProtocolClient.validateAllowedRequest(
                            good, 0x11, 0x12, payload, 6000));
        }
    }

    @Test
    public void setHasSeparateUnforgeablePermitEntryPoint() throws Exception {
        Method setter = DjiProtocolClient.class.getDeclaredMethod(
                "setModernFlysafeLicenseEnabled",
                DjiProtocolClient.FlysafeWritePermit.class);
        assertFalse(Modifier.isPublic(setter.getModifiers()));
        assertEquals(FlysafeLicenseSetCodec.Ack.class, setter.getReturnType());

        Method issuer = DjiProtocolClient.class.getDeclaredMethod(
                "issueModernFlysafeWritePermit",
                DjiProtocolClient.FlysafeGateObservation.class,
                Object.class,
                FlysafeRidInventory.OpaqueRidHandle.class,
                boolean.class);
        assertFalse(Modifier.isPublic(issuer.getModifiers()));
        assertEquals(DjiProtocolClient.FlysafeWritePermit.class, issuer.getReturnType());
        assertNotEquals(DjiProtocolClient.FlysafeGateObservation.class, issuer.getReturnType());

        Constructor<?>[] constructors =
                DjiProtocolClient.FlysafeWritePermit.class.getDeclaredConstructors();
        boolean privateConstructorFound = false;
        for (Constructor<?> constructor : constructors) {
            assertFalse(Modifier.isPublic(constructor.getModifiers()));
            assertFalse(Modifier.isProtected(constructor.getModifiers()));
            privateConstructorFound |= Modifier.isPrivate(constructor.getModifiers());
        }
        assertTrue(privateConstructorFound);
        assertThrows(NoSuchMethodException.class, () ->
                DjiProtocolClient.class.getDeclaredMethod(
                        "issueModernFlysafeWritePermit",
                        DjiProtocolClient.FlysafeGateObservation.class,
                        Object.class,
                        DjiProtocolClient.Route.class,
                        FlysafeRidInventory.OpaqueRidHandle.class,
                        boolean.class));
        assertThrows(NoSuchMethodException.class, () ->
                DjiProtocolClient.class.getDeclaredMethod(
                        "setModernFlysafeLicenseEnabled", long.class, boolean.class));
    }

    @Test
    public void generalizedSenderRequiresDistinctQueryAndSetProofs() throws Exception {
        Class<?> dispatchClass = Class.forName(
                DjiProtocolClient.class.getName() + "$FlysafeSetDispatch");
        Class<?> queryAuthorizationClass = Class.forName(
                DjiProtocolClient.class.getName() + "$FlysafeQueryAuthorization");
        Method method = DjiProtocolClient.class.getDeclaredMethod(
                "sendAllowedRequest",
                DjiProtocolClient.Route.class,
                int.class,
                int.class,
                byte[].class,
                int.class,
                queryAuthorizationClass,
                dispatchClass);
        assertTrue(Modifier.isPrivate(method.getModifiers()));
        assertNotEquals(
                method.getParameterTypes()[5],
                method.getParameterTypes()[6]);
    }

    @Test
    public void processWideLaneAdmitsOnlyOneOutstandingOperation() {
        DjiProtocolClient.FlysafeCommandLane lane =
                new DjiProtocolClient.FlysafeCommandLane();
        assertTrue(lane.tryAcquire());
        assertTrue(lane.isActive());
        assertFalse(lane.tryAcquire());
        lane.release();
        assertFalse(lane.isActive());
        assertTrue(lane.tryAcquire());
        lane.release();
        assertThrows(IllegalStateException.class, lane::release);
    }

    @Test
    public void setUsesNoApplicationRetryAndAFullNineteenSecondDrain() {
        assertEquals(0, DjiProtocolClient.flysafeSetApplicationRetryCount());
        assertEquals(19_000L, DjiProtocolClient.flysafeSetDrainMillis());
        assertEquals(19_000L,
                DjiProtocolClient.remainingFlysafeSetDrainMillis(1000L, 1000L));
        assertEquals(1L,
                DjiProtocolClient.remainingFlysafeSetDrainMillis(1000L, 19_999L));
        assertEquals(0L,
                DjiProtocolClient.remainingFlysafeSetDrainMillis(1000L, 20_000L));
        assertEquals(19_000L,
                DjiProtocolClient.remainingFlysafeSetDrainMillis(1000L, 999L));
        assertThrows(IllegalArgumentException.class,
                () -> DjiProtocolClient.remainingFlysafeSetDrainMillis(-1L, 0L));
    }

    @Test
    public void commandDiagnosticRedactsIdAndSanitizesCallerRouteLabel() throws Exception {
        Method copyRoute = DjiProtocolClient.class.getDeclaredMethod(
                "copyFlysafeSetRoute", DjiProtocolClient.Route.class);
        copyRoute.setAccessible(true);
        DjiProtocolClient.Route route = (DjiProtocolClient.Route) copyRoute.invoke(
                null, setRoute("injected-CDAB3412", 3));

        Method summary = DjiProtocolClient.class.getDeclaredMethod(
                "commandSummary",
                DjiProtocolClient.Route.class,
                int.class,
                int.class,
                byte[].class);
        summary.setAccessible(true);
        String diagnostic = (String) summary.invoke(
                null, route, 0x11, 0x12, KNOWN_SET_PAYLOAD);
        assertTrue(diagnostic.contains("payload=<redacted-license-action>"));
        assertFalse(diagnostic.contains("CDAB3412"));
        assertFalse(diagnostic.contains("00CDAB34120100"));
        assertFalse(diagnostic.contains("injected"));

        Method throwableSummary = DjiProtocolClient.class.getDeclaredMethod(
                "commandThrowableSummary",
                Throwable.class,
                int.class,
                int.class);
        throwableSummary.setAccessible(true);
        String cause = (String) throwableSummary.invoke(
                null,
                new IllegalStateException("vendor echoed 00CDAB34120100"),
                0x11,
                0x12);
        assertEquals("IllegalStateException", cause);
        assertFalse(cause.contains("CDAB3412"));
    }

    @Test
    public void exactReversedAckEnvelopeIsRequiredBeforeSemanticDecode() throws Exception {
        DjiProtocolClient.Route requestRoute = setRoute("bound", 3);
        Object validPack = validAckPack(requestRoute);
        DjiProtocolClient.Reply valid = validateAck(validPack, requestRoute);
        assertTrue(valid.callbackSuccess);
        FlysafeLicenseSetCodec.decodeAck(
                valid.callbackSuccess, valid.ccode, valid.data, true);

        Object nonzeroCode = validAckPack(requestRoute);
        setField(nonzeroCode, "ccode", 1);
        DjiProtocolClient.Reply nonzero = validateAck(nonzeroCode, requestRoute);
        assertTrue(nonzero.callbackSuccess);
        assertThrows(FlysafeLicenseSetCodec.ProtocolException.class,
                () -> FlysafeLicenseSetCodec.decodeAck(
                        nonzero.callbackSuccess, nonzero.ccode, nonzero.data, true));

        for (Mutation mutation : new Mutation[] {
                new Mutation("senderType", 2),
                new Mutation("senderId", 3),
                new Mutation("receiverType", 0x12),
                new Mutation("receiverId", 4),
                new Mutation("cmdSet", 3),
                new Mutation("cmdId", 0x11),
                new Mutation("cmdType", 0),
                new Mutation("duplicateCmdType", 0),
                new Mutation("isNeedAck", 1),
                new Mutation("encryptType", 1),
                new Mutation("trailingBytes", 1)
        }) {
            Object pack = validAckPack(requestRoute);
            setField(pack, mutation.field, mutation.value);
            DjiProtocolClient.Reply rejected = validateAck(pack, requestRoute);
            assertFalse(mutation.field, rejected.callbackSuccess);
            assertNotNull(mutation.field, rejected.failure);
        }
    }

    private static DjiProtocolClient.Route setRoute(String label, int senderId) {
        return new DjiProtocolClient.Route(label, senderId, 2, 4, 0x12);
    }

    private static Object validAckPack(DjiProtocolClient.Route requestRoute) throws Exception {
        Class<?> packClass = Class.forName(
                DjiProtocolClient.class.getName() + "$ParsedPack");
        Constructor<?> constructor = packClass.getDeclaredConstructor();
        constructor.setAccessible(true);
        Object pack = constructor.newInstance();
        setField(pack, "sof", (byte) 0x55);
        setField(pack, "version", 1);
        setField(pack, "senderType", requestRoute.receiverType);
        setField(pack, "senderId", requestRoute.receiverId);
        setField(pack, "receiverType", requestRoute.senderType);
        setField(pack, "receiverId", requestRoute.senderId);
        setField(pack, "cmdSet", 0x11);
        setField(pack, "cmdId", 0x12);
        setField(pack, "cmdType", 1);
        setField(pack, "duplicateCmdType", 1);
        setField(pack, "isNeedAck", 0);
        setField(pack, "encryptType", 0);
        setField(pack, "ccode", 0);
        setField(pack, "dataLength", 2);
        setField(pack, "data", new byte[] {1, 2});
        setField(pack, "trailingBytes", 0);
        return pack;
    }

    private static DjiProtocolClient.Reply validateAck(
            Object pack,
            DjiProtocolClient.Route requestRoute) throws Exception {
        Method validate = DjiProtocolClient.class.getDeclaredMethod(
                "validate",
                pack.getClass(),
                DjiProtocolClient.Route.class,
                int.class,
                int.class,
                String.class);
        validate.setAccessible(true);
        return (DjiProtocolClient.Reply) validate.invoke(
                null, pack, requestRoute, 0x11, 0x12, "callback=<redacted>");
    }

    private static void setField(Object target, String name, Object value) throws Exception {
        Field field = target.getClass().getDeclaredField(name);
        field.setAccessible(true);
        field.set(target, value);
    }

    private static final class Mutation {
        final String field;
        final Object value;

        Mutation(String field, Object value) {
            this.field = field;
            this.value = value;
        }
    }
}
