package com.finduas.ridobserver

import android.content.pm.ApplicationInfo
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PackageCapabilityPolicyTest {
    @Test
    fun recognizesSystemAppIdAcrossUsers() {
        assertTrue(PackageCapabilityPolicy.isSystemUid(1000))
        assertTrue(PackageCapabilityPolicy.isSystemUid(101000))
        assertFalse(PackageCapabilityPolicy.isSystemUid(10000))
    }

    @Test
    fun classifiesOnlyRequestedApplicationFlags() {
        val flags = ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_DEBUGGABLE
        assertTrue(PackageCapabilityPolicy.hasFlag(flags, ApplicationInfo.FLAG_SYSTEM))
        assertTrue(PackageCapabilityPolicy.hasFlag(flags, ApplicationInfo.FLAG_DEBUGGABLE))
        assertFalse(
            PackageCapabilityPolicy.hasFlag(flags, ApplicationInfo.FLAG_UPDATED_SYSTEM_APP)
        )
    }

    @Test
    fun rendersCertificateDigestWithoutSignedByteExpansion() {
        assertEquals(
            "00ff7f80",
            PackageCapabilityPolicy.normalizeDigest(byteArrayOf(0, -1, 127, -128))
        )
    }

    @Test
    fun rendersOnlyUnixPermissionBitsAsFourDigitOctal() {
        assertEquals("0755", PackageCapabilityPolicy.formatMode(0x8000 or 0x1ed))
        assertEquals("0640", PackageCapabilityPolicy.formatMode(0x8000 or 0x1a0))
    }

    @Test
    fun exactDpadReferenceRequiresEveryIdentityGate() {
        val exact = PackageCapability(
            state = PackageProbeState.PRESENT,
            version = "1.0.08.29-5e7f0af3",
            versionCode = 155,
            splitCount = 0,
            metadataStableDuringProbe = true,
            signerMatchesAdjacentDjiPlatform = true,
            sourceApkMatchesReference = true
        )
        assertEquals(
            AdjacentDpadReferenceState.EXACT_PACKAGE_MATCH,
            ReferenceClassificationPolicy.classifyDpad(exact)
        )
        assertEquals(
            AdjacentDpadReferenceState.DIFFERENT,
            ReferenceClassificationPolicy.classifyDpad(exact.copy(splitCount = 1))
        )
        assertEquals(
            AdjacentDpadReferenceState.DIFFERENT,
            ReferenceClassificationPolicy.classifyDpad(
                exact.copy(sourceApkMatchesReference = false)
            )
        )
    }

    @Test
    fun dpadReferenceFailsClosedOnDriftOrMissingEvidence() {
        assertEquals(
            AdjacentDpadReferenceState.CHANGED_DURING_SCAN,
            ReferenceClassificationPolicy.classifyDpad(
                PackageCapability(metadataStableDuringProbe = false)
            )
        )
        assertEquals(
            AdjacentDpadReferenceState.INCOMPLETE,
            ReferenceClassificationPolicy.classifyDpad(PackageCapability())
        )
    }

    @Test
    fun frameworkReferenceRequiresBothIndependentHashes() {
        assertEquals(
            AdjacentFrameworkReferenceState.EXACT_BOTH_MATCH,
            ReferenceClassificationPolicy.classifyFramework(true, true)
        )
        assertEquals(
            AdjacentFrameworkReferenceState.DIFFERENT,
            ReferenceClassificationPolicy.classifyFramework(true, false)
        )
        assertEquals(
            AdjacentFrameworkReferenceState.INCOMPLETE,
            ReferenceClassificationPolicy.classifyFramework(true, null)
        )
    }

    @Test
    fun brokerReferenceRequiresBothConfigAndLibraryHashes() {
        assertEquals(
            AdjacentBrokerReferenceState.EXACT_BOTH_MATCH,
            ReferenceClassificationPolicy.classifyBroker(true, true)
        )
        assertEquals(
            AdjacentBrokerReferenceState.DIFFERENT,
            ReferenceClassificationPolicy.classifyBroker(false, true)
        )
        assertEquals(
            AdjacentBrokerReferenceState.INCOMPLETE,
            ReferenceClassificationPolicy.classifyBroker(null, true)
        )
    }
}
