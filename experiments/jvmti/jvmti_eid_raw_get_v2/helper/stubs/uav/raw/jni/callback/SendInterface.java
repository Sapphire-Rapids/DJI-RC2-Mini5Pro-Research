package uav.raw.jni.callback;

import uav.jni.JNIProguardKeepTag;

/** Compile-only shape; DJI Fly's already-loaded interface owns this name at runtime. */
public interface SendInterface extends JNIProguardKeepTag {
    void onReceivedData(long handle, byte[] applicationPayload);

    void onTimeout(long handle);
}
