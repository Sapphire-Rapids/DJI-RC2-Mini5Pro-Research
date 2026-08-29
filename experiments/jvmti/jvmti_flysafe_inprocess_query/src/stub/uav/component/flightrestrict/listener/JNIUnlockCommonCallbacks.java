package uav.component.flightrestrict.listener;

public final class JNIUnlockCommonCallbacks {
    private JNIUnlockCommonCallbacks() {}

    public interface JNIUnlockCommonCallbackWith<T> {
        void onFailure(int errorCode);
        void onSuccess(T value);
    }
}
