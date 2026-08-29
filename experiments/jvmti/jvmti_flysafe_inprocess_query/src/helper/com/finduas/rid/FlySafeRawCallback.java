package com.finduas.rid;

import uav.component.flightrestrict.listener.JNIUnlockCommonCallbacks;

public final class FlySafeRawCallback
        implements JNIUnlockCommonCallbacks.JNIUnlockCommonCallbackWith<byte[]> {
    public static native void nativeOnFailure(int errorCode);
    public static native void nativeOnInventory(
            int parseCode,
            int declaredCount,
            int recordCount,
            int ridCount,
            int ridLicenseId,
            int ridLevel,
            boolean enabled,
            boolean inValidDate,
            boolean invalid);

    public FlySafeRawCallback() {}

    @Override
    public void onFailure(int errorCode) {
        nativeOnFailure(errorCode);
    }

    @Override
    public void onSuccess(byte[] data) {
        try {
            FlySafeLicenseGroupParser.Result result = FlySafeLicenseGroupParser.parse(data);
            nativeOnInventory(
                    0,
                    result.declaredCount,
                    result.recordCount,
                    result.ridCount,
                    result.ridLicenseId,
                    result.ridLevel,
                    result.enabled,
                    result.inValidDate,
                    result.invalid);
        } catch (FlySafeLicenseGroupParser.ParseException ignored) {
            nativeOnInventory(1, 0, 0, 0, 0, 0, false, false, false);
        }
    }
}
