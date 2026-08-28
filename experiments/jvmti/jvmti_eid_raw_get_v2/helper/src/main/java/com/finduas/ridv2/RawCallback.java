package com.finduas.ridv2;

import uav.raw.jni.callback.SendInterface;

/**
 * In-memory callback bridge.  It has no initializer, fields, I/O, thread,
 * loader call, or DJI send call.  Native methods are registered before the
 * object is constructed.
 */
public final class RawCallback implements SendInterface {
    public RawCallback() {}

    @Override
    public native void onReceivedData(long handle, byte[] applicationPayload);

    @Override
    public native void onTimeout(long handle);
}
