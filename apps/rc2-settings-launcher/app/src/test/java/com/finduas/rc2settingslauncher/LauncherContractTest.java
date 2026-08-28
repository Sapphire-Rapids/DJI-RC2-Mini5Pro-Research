package com.finduas.rc2settingslauncher;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;

import org.junit.Test;

public final class LauncherContractTest {
    @Test
    public void deviceInfoActionIsExactPublicAndroidAction() {
        assertEquals(
                "android.settings.DEVICE_INFO_SETTINGS",
                LauncherContract.DEVICE_INFO_ACTION);
    }

    @Test
    public void developerOptionsActionIsExactPublicAndroidAction() {
        assertEquals(
                "android.settings.APPLICATION_DEVELOPMENT_SETTINGS",
                LauncherContract.DEVELOPMENT_SETTINGS_ACTION);
    }

    @Test
    public void twoButtonsCannotAccidentallyShareOneAction() {
        assertNotEquals(
                LauncherContract.DEVICE_INFO_ACTION,
                LauncherContract.DEVELOPMENT_SETTINGS_ACTION);
    }
}
