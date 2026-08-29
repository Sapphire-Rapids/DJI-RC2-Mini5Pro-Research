package com.finduas.rc2ridadmin;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertThrows;

import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

import org.junit.Test;

public final class DjiProtocolClientAllowlistTest {
    @Test
    public void modernFlysafeQueryUsesExactRouteCommandAndTimeout() {
        DjiProtocolClient.Route route = DjiProtocolClient.MODERN_FLYSAFE_FC4;
        assertEquals(0x02, route.senderType);
        assertEquals(0x04, route.senderId);
        assertEquals(0x12, route.receiverType);
        assertEquals(0x04, route.receiverId);

        DjiProtocolClient.validateAllowedRequest(
                route,
                DjiProtocolClient.CMD_SET_ADSB,
                DjiProtocolClient.CMD_FLYSAFE_LICENSE_LIST,
                new byte[] {0, 1},
                DjiProtocolClient.FLYSAFE_COMMAND_TIMEOUT_MS);
        DjiProtocolClient.validateAllowedRequest(
                route,
                0x11,
                0x11,
                new byte[] {0, (byte) 0xfe},
                6000);
    }

    @Test
    public void malformedFlysafeSetterPayloadsRemainRejected() {
        for (byte[] payload : new byte[][] {
                {0, 0},
                {0, 1},
                {1, 2, 3, 4}
        }) {
            assertThrows(IllegalArgumentException.class,
                    () -> DjiProtocolClient.validateAllowedRequest(
                            DjiProtocolClient.MODERN_FLYSAFE_FC4,
                            0x11,
                            0x12,
                            payload,
                            6000));
        }
    }

    @Test
    public void modernQueryRejectsRouteTimeoutAndSelectorDrift() {
        assertThrows(IllegalArgumentException.class,
                () -> DjiProtocolClient.validateAllowedRequest(
                        DjiProtocolClient.RC2_LEGACY_FC,
                        0x11,
                        0x11,
                        new byte[] {0, 1},
                        6000));
        assertThrows(IllegalArgumentException.class,
                () -> DjiProtocolClient.validateAllowedRequest(
                        DjiProtocolClient.MODERN_FLYSAFE_FC4,
                        0x11,
                        0x11,
                        new byte[] {0, 1},
                        5999));
        for (byte[] payload : new byte[][] {
                {0},
                {0, 3},
                {1, 0},
                {0, 0, 0}
        }) {
            assertThrows(IllegalArgumentException.class,
                    () -> DjiProtocolClient.validateAllowedRequest(
                            DjiProtocolClient.MODERN_FLYSAFE_FC4,
                            0x11,
                            0x11,
                            payload,
                            6000));
        }
    }

    @Test
    public void preexistingFlycCommandsRemainExplicitlyAllowListed() {
        DjiProtocolClient.validateAllowedRequest(
                DjiProtocolClient.MODERN_FC4, 0x03,
                DjiProtocolClient.CMD_EID_SWITCH, new byte[] {2}, 500);
        DjiProtocolClient.validateAllowedRequest(
                DjiProtocolClient.MODERN_FC4, 0x03,
                DjiProtocolClient.CMD_OPERATOR_ID,
                new byte[] {0, 0x10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
                500);
        DjiProtocolClient.validateAllowedRequest(
                DjiProtocolClient.MODERN_FC4, 0x03,
                DjiProtocolClient.CMD_PARAM_INFO_BY_HASH,
                new byte[] {(byte) 0x8a, 0x23, 0x71, 0x03}, 1000);
        DjiProtocolClient.validateAllowedRequest(
                DjiProtocolClient.RC2_LEGACY_FC, 0x03,
                DjiProtocolClient.CMD_PARAM_READ_BY_HASH,
                new byte[] {0x4f, (byte) 0x86, (byte) 0xbd, 0x3c}, 1000);
        DjiProtocolClient.validateAllowedRequest(
                DjiProtocolClient.RC2_LEGACY_FC, 0x03,
                DjiProtocolClient.CMD_PARAM_WRITE_BY_HASH,
                new byte[] {0x4f, (byte) 0x86, (byte) 0xbd, 0x3c, 1}, 1000);

        assertThrows(IllegalArgumentException.class,
                () -> DjiProtocolClient.validateAllowedRequest(
                        DjiProtocolClient.MODERN_FC4, 0x04,
                        DjiProtocolClient.CMD_EID_SWITCH, new byte[] {2}, 500));
        assertThrows(IllegalArgumentException.class,
                () -> DjiProtocolClient.validateAllowedRequest(
                        DjiProtocolClient.RC2_LEGACY_FC, 0x03,
                        DjiProtocolClient.CMD_OPERATOR_ID, new byte[] {2}, 500));
    }

    @Test
    public void generalizedSenderIsPrivateAndRequiresQueryAuthorization() throws Exception {
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
        assertNotNull(method);
        assertEquals(true, Modifier.isPrivate(method.getModifiers()));
        assertThrows(NoSuchMethodException.class, () ->
                DjiProtocolClient.class.getDeclaredMethod(
                        "request",
                        DjiProtocolClient.Route.class,
                        int.class,
                        int.class,
                        byte[].class,
                        int.class));
        assertFalse(Modifier.isPublic(method.getModifiers()));
    }

    @Test
    public void callbackWaitCoversRc331InitialSendAndTwoRetries() {
        assertEquals(19_000L,
                DjiProtocolClient.callbackWaitMillis(
                        DjiProtocolClient.FLYSAFE_COMMAND_TIMEOUT_MS));
        assertEquals(5_000L, DjiProtocolClient.callbackWaitMillis(500));
        assertThrows(IllegalArgumentException.class,
                () -> DjiProtocolClient.callbackWaitMillis(0));
    }

    @Test
    public void euC0ByHashCommandsAreAllowListedSeparatelyFromRidCtrl() {
        // F7 metadata (hash 0xF80992FE) and F8 read are read-only and allowed on both routes.
        DjiProtocolClient.validateAllowedRequest(
                DjiProtocolClient.RC2_LEGACY_FC, 0x03,
                DjiProtocolClient.CMD_PARAM_INFO_BY_HASH,
                new byte[] {(byte) 0xfe, (byte) 0x92, 0x09, (byte) 0xf8}, 1000);
        DjiProtocolClient.validateAllowedRequest(
                DjiProtocolClient.MODERN_FC4, 0x03,
                DjiProtocolClient.CMD_PARAM_READ_BY_HASH,
                new byte[] {(byte) 0xfe, (byte) 0x92, 0x09, (byte) 0xf8}, 1000);

        // F9 Boolean write in both width-1 and float32 forms.
        DjiProtocolClient.validateAllowedRequest(
                DjiProtocolClient.RC2_LEGACY_FC, 0x03,
                DjiProtocolClient.CMD_PARAM_WRITE_BY_HASH,
                new byte[] {(byte) 0xfe, (byte) 0x92, 0x09, (byte) 0xf8, 1}, 1000);
        DjiProtocolClient.validateAllowedRequest(
                DjiProtocolClient.RC2_LEGACY_FC, 0x03,
                DjiProtocolClient.CMD_PARAM_WRITE_BY_HASH,
                new byte[] {(byte) 0xfe, (byte) 0x92, 0x09, (byte) 0xf8,
                        0, 0, (byte) 0x80, 0x3f}, 1000);

        // A different hash is not admitted for the EU C0 F8 read path.
        assertThrows(IllegalArgumentException.class,
                () -> DjiProtocolClient.validateAllowedRequest(
                        DjiProtocolClient.RC2_LEGACY_FC, 0x03,
                        DjiProtocolClient.CMD_PARAM_READ_BY_HASH,
                        new byte[] {0x4f, (byte) 0x86, (byte) 0xbd, 0x3c, 1}, 1000));
    }
}
