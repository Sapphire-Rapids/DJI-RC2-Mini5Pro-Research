package com.finduas.ridobserver

import android.content.pm.PackageManager
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ActivityQueryPolicyTest {
    @Test
    fun disabledAppDoesNotMakeItsEnabledComponentLaunchable() {
        assertEquals(ActivityProbeState.EXPORTED_DISABLED,
            classify(true, true, false))
        assertEquals(ActivityProbeState.PRIVATE_DISABLED,
            classify(false, true, false))
        assertEquals(ActivityProbeState.PRIVATE_DISABLED,
            classify(false, false, true))
        assertEquals(ActivityProbeState.EXPORTED_ENABLED,
            classify(true, true, true))
    }

    @Test
    fun runtimeComponentOverrideTakesPrecedenceOverManifestDefault() {
        assertEquals(ActivityProbeState.EXPORTED_DISABLED,
            classify(true, true, true, componentSetting = PackageManager.COMPONENT_ENABLED_STATE_DISABLED))
        assertEquals(ActivityProbeState.EXPORTED_ENABLED,
            classify(true, false, true, componentSetting = PackageManager.COMPONENT_ENABLED_STATE_ENABLED))
        assertEquals(ActivityProbeState.PRIVATE_ENABLED,
            classify(false, false, true, componentSetting = PackageManager.COMPONENT_ENABLED_STATE_ENABLED))
    }

    @Test
    fun applicationOverrideStillDominatesAnExplicitlyEnabledComponent() {
        for (setting in listOf(
            PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
            PackageManager.COMPONENT_ENABLED_STATE_DISABLED_USER,
            PackageManager.COMPONENT_ENABLED_STATE_DISABLED_UNTIL_USED
        )) {
            // MATCH_DISABLED_UNTIL_USED_COMPONENTS can make ApplicationInfo.enabled true.
            assertEquals(ActivityProbeState.EXPORTED_DISABLED,
                classify(true, true, true,
                    componentSetting = PackageManager.COMPONENT_ENABLED_STATE_ENABLED,
                    applicationSetting = setting))
        }
        assertEquals(ActivityProbeState.EXPORTED_ENABLED,
            classify(true, true, false,
                applicationSetting = PackageManager.COMPONENT_ENABLED_STATE_ENABLED))
    }

    @Test
    fun unknownRuntimeSettingIsAnErrorInsteadOfEnabledOrDisabled() {
        assertEquals(ActivityProbeState.INTERNAL_ERROR,
            classify(true, true, true, componentSetting = 99))
        assertEquals(ActivityProbeState.INTERNAL_ERROR,
            classify(true, true, false, applicationSetting = 99))
    }

    @Test
    fun metadataQueryIncludesDisabledAndBothBootVariants() {
        for (flag in listOf(PackageManager.MATCH_DISABLED_COMPONENTS,
            PackageManager.MATCH_DISABLED_UNTIL_USED_COMPONENTS,
            PackageManager.MATCH_DIRECT_BOOT_AWARE, PackageManager.MATCH_DIRECT_BOOT_UNAWARE)) {
            assertTrue(ActivityQueryPolicy.FLAGS and flag == flag)
        }
    }

    private fun classify(
        exported: Boolean,
        componentEnabled: Boolean,
        applicationEnabled: Boolean,
        componentSetting: Int = PackageManager.COMPONENT_ENABLED_STATE_DEFAULT,
        applicationSetting: Int = PackageManager.COMPONENT_ENABLED_STATE_DEFAULT
    ) = ActivityQueryPolicy.classify(
        exported, componentEnabled, applicationEnabled, componentSetting, applicationSetting
    )
}
