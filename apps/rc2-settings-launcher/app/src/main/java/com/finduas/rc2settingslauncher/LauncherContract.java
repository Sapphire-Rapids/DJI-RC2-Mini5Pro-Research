package com.finduas.rc2settingslauncher;

/** Fixed, public Android settings actions used by the two user-driven buttons. */
final class LauncherContract {
    static final String DEVICE_INFO_ACTION = "android.settings.DEVICE_INFO_SETTINGS";
    static final String DEVELOPMENT_SETTINGS_ACTION =
            "android.settings.APPLICATION_DEVELOPMENT_SETTINGS";

    private LauncherContract() {
        throw new AssertionError("No instances");
    }
}
