package com.finduas.ridobserver

import java.nio.ByteBuffer
import java.nio.ByteOrder
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class AndroidArtIdentityProbeTest {
    @Test
    fun parserEnumeratesMappingsAndCollapsesOneExactFileIdentity() {
        val scan = ArtMapsParser.parse(
            sequenceOf(
                "70000000-70001000 r--p 00000000 00:1d 123 /apex/com.android.art/lib64/libart.so",
                "70001000-70002000 r-xp 00001000 00:1d 123 /apex/com.android.art/lib64/libart.so",
                "70002000-70003000 rw-p 00002000 00:1d 123 /apex/com.android.art/lib64/libart.so"
            )
        )

        assertEquals(3, scan.entries.size)
        assertEquals(1, scan.identities.size)
        assertEquals("70001000-70002000", scan.entries[1].addressRange)
        assertEquals("r-xp", scan.entries[1].permissions)
        assertEquals(0x1000L, scan.entries[1].fileOffset)
        assertEquals("0:1d", scan.identities.single().device)
        assertEquals(123L, scan.identities.single().inode)
        assertTrue(scan.hasReadableMapping)
        assertTrue(scan.hasExecutableMapping)
        assertEquals(0, scan.malformedCandidateCount)
    }

    @Test
    fun parserKeepsDifferentMappedFilesAsDifferentIdentities() {
        val scan = ArtMapsParser.parse(
            sequenceOf(
                "70000000-70001000 r-xp 00000000 00:1d 123 /apex/a/lib64/libart.so",
                "71000000-71001000 r-xp 00000000 00:1e 124 /apex/b/lib64/libart.so"
            )
        )

        assertEquals(2, scan.identities.size)
    }

    @Test
    fun parserMarksDeletedAndMalformedExactCandidates() {
        val scan = ArtMapsParser.parse(
            sequenceOf(
                "not-a-range r-xp 00000000 00:1d 123 /apex/a/lib64/libart.so",
                "70000000-70001000 r-xp 00000000 00:1d 123 /apex/a/lib64/libart.so (deleted)",
                "70000000-70001000 r-xp 00000000 00:1d 123 /apex/a/lib64/libart.so.debug"
            )
        )

        assertEquals(1, scan.malformedCandidateCount)
        assertEquals(1, scan.entries.size)
        assertTrue(scan.entries.single().deleted)
        assertEquals("/apex/a/lib64/libart.so", scan.entries.single().path)
    }

    @Test
    fun parserRejectsNonCanonicalPermissionShape() {
        val scan = ArtMapsParser.parse(
            sequenceOf(
                "70000000-70001000 rrrr 00000000 00:1d 123 /apex/a/lib64/libart.so"
            )
        )

        assertEquals(1, scan.malformedCandidateCount)
        assertTrue(scan.entries.isEmpty())
    }

    @Test
    fun parserRejectsReversedZeroLengthOverflowAndUnalignedGeometry() {
        val invalidRows = listOf(
            "0-1000 r-xp 00000000 00:1d 123 /apex/a/lib64/libart.so",
            "70001000-70000000 r-xp 00000000 00:1d 123 /apex/a/lib64/libart.so",
            "70000000-70000000 r-xp 00000000 00:1d 123 /apex/a/lib64/libart.so",
            "70000001-70001000 r-xp 00000000 00:1d 123 /apex/a/lib64/libart.so",
            "70000000-70001001 r-xp 00000000 00:1d 123 /apex/a/lib64/libart.so",
            "70000000-70001000 r-xp 00000001 00:1d 123 /apex/a/lib64/libart.so",
            "10000000000000000-10000000000001000 r-xp 00000000 00:1d 123 /apex/a/lib64/libart.so",
            "70000000-70001000 r-xp fffffffffffff000 00:1d 123 /apex/a/lib64/libart.so"
        )

        invalidRows.forEach { row ->
            val scan = ArtMapsParser.parse(sequenceOf(row))
            assertEquals("row=$row", 1, scan.malformedCandidateCount)
            assertTrue("row=$row", scan.entries.isEmpty())
        }
    }

    @Test
    fun parserRejectsZeroAndOversizedDeviceIdentities() {
        for (device in listOf(
            "00:00", "100000000:1", "1:100000000", "x:1", "+0:+1", "+1:1"
        )) {
            val scan = ArtMapsParser.parse(
                sequenceOf(
                    "70000000-70001000 r-xp 00000000 $device 123 " +
                        "/apex/a/lib64/libart.so"
                )
            )
            assertEquals("device=$device", 1, scan.malformedCandidateCount)
            assertTrue("device=$device", scan.entries.isEmpty())
        }
        assertNull(LinuxDeviceIdentity.normalizeNonZero("00:00"))
        assertFalse(LinuxDeviceIdentity.matches("00:00", 1L))
        assertFalse(LinuxDeviceIdentity.matches("00:1d", 0L))
    }

    @Test
    fun parserRejectsNonCanonicalSignedDecimalInode() {
        for (inode in listOf("+123", "-123", "12x")) {
            val scan = ArtMapsParser.parse(
                sequenceOf(
                    "70000000-70001000 r-xp 00000000 00:1d $inode " +
                        "/apex/a/lib64/libart.so"
                )
            )
            assertEquals("inode=$inode", 1, scan.malformedCandidateCount)
            assertTrue("inode=$inode", scan.entries.isEmpty())
        }
    }

    @Test
    fun coverageRejectsOverlapBeyondFileAndRoundedSizeOverflow() {
        fun entry(start: Long, end: Long, offset: Long) = ArtMapEntry(
            startAddress = start,
            endAddress = end,
            permissions = "r-xp",
            fileOffset = offset,
            device = "00:1d",
            inode = 123L,
            path = "/apex/a/lib64/libart.so",
            deleted = false
        )

        assertTrue(
            ArtMapCoveragePolicy.isValid(
                listOf(entry(0x70000000, 0x70001000, 0L)),
                fileSize = 1L,
                pageSizeBytes = 4096L
            )
        )
        assertFalse(
            ArtMapCoveragePolicy.isValid(
                listOf(entry(0x70000000, 0x70002000, 0L)),
                fileSize = 4096L,
                pageSizeBytes = 4096L
            )
        )
        assertFalse(
            ArtMapCoveragePolicy.isValid(
                listOf(
                    entry(0x70000000, 0x70002000, 0L),
                    entry(0x70001000, 0x70003000, 0L)
                ),
                fileSize = 0x4000L,
                pageSizeBytes = 4096L
            )
        )
        assertFalse(
            ArtMapCoveragePolicy.isValid(
                listOf(entry(0x70000000, 0x70001000, 0L)),
                fileSize = Long.MAX_VALUE,
                pageSizeBytes = 4096L
            )
        )
    }

    @Test
    fun normalizedMapsSnapshotsRequireExactEquality() {
        val first = ArtMapsParser.parse(
            sequenceOf(
                "70000000-70001000 r--p 00000000 00:1d 123 /apex/a/lib64/libart.so",
                "70001000-70002000 r-xp 00001000 00:1d 123 /apex/a/lib64/libart.so"
            )
        )
        val equal = ArtMapsParser.parse(
            sequenceOf(
                "70000000-70001000 r--p 00000000 00:1d 123 /apex/a/lib64/libart.so",
                "70001000-70002000 r-xp 00001000 00:1d 123 /apex/a/lib64/libart.so"
            )
        )
        val changedPermission = ArtMapsParser.parse(
            sequenceOf(
                "70000000-70001000 r--p 00000000 00:1d 123 /apex/a/lib64/libart.so",
                "70001000-70002000 rw-p 00001000 00:1d 123 /apex/a/lib64/libart.so"
            )
        )
        val changedOffset = ArtMapsParser.parse(
            sequenceOf(
                "70000000-70001000 r--p 00000000 00:1d 123 /apex/a/lib64/libart.so",
                "70001000-70002000 r-xp 00002000 00:1d 123 /apex/a/lib64/libart.so"
            )
        )

        assertEquals(first, equal)
        assertFalse(first == changedPermission)
        assertFalse(first == changedOffset)
    }

    @Test
    fun exactMetadataDetectsSameSecondNanosecondDriftAndZeroDevice() {
        val base = ExactFileMetadata(
            device = 1L,
            inode = 2L,
            mode = 0x81a4,
            size = 100L,
            modifiedSeconds = 10L,
            modifiedNanoseconds = 20L,
            changedSeconds = 30L,
            changedNanoseconds = 40L
        )
        assertTrue(ExactFileMetadataPolicy.same(base, base.copy()))
        assertFalse(
            ExactFileMetadataPolicy.same(
                base,
                base.copy(modifiedNanoseconds = 21L)
            )
        )
        assertFalse(
            ExactFileMetadataPolicy.same(
                base,
                base.copy(changedNanoseconds = 41L)
            )
        )
        assertFalse(ExactFileMetadataPolicy.same(base, base.copy(device = 0L)))
        assertFalse(
            ExactFileMetadataPolicy.same(
                base,
                base.copy(modifiedNanoseconds = 1_000_000_000L)
            )
        )
    }

    @Test
    fun admissionDistinguishesZeroAndMultipleFileIdentities() {
        val empty = ArtMapsParser.parse(emptySequence())
        val multiple = ArtMapsParser.parse(
            sequenceOf(
                "70000000-70001000 r-xp 00000000 00:1d 123 /apex/a/lib64/libart.so",
                "71000000-71001000 r-xp 00000000 00:1e 124 /apex/b/lib64/libart.so"
            )
        )
        val one = ArtMapsParser.parse(
            sequenceOf(
                "70000000-70001000 r--p 00000000 00:1d 123 /apex/a/lib64/libart.so",
                "70001000-70002000 r-xp 00001000 00:1d 123 /apex/a/lib64/libart.so"
            )
        )

        assertEquals(ArtIdentityState.NO_LIBART_MAPPING, ArtMapAdmissionPolicy.rejection(empty))
        assertEquals(
            ArtIdentityState.MULTIPLE_FILE_IDENTITIES,
            ArtMapAdmissionPolicy.rejection(multiple)
        )
        assertNull(ArtMapAdmissionPolicy.rejection(one))
    }

    @Test
    fun linuxDeviceEncodingMatchesProcMajorMinor() {
        val encoded = LinuxDeviceIdentity.makeDevice(0x1234L, 0x567L)

        assertEquals(0x1234L, LinuxDeviceIdentity.major(encoded))
        assertEquals(0x567L, LinuxDeviceIdentity.minor(encoded))
        assertTrue(LinuxDeviceIdentity.matches("1234:567", encoded))
        assertFalse(LinuxDeviceIdentity.matches("1234:568", encoded))
        assertFalse(LinuxDeviceIdentity.matches("invalid", encoded))
    }

    @Test
    fun gnuBuildIdParserAcceptsOneExactNote() {
        val note = gnuBuildIdNote(byteArrayOf(0x01, 0x02, 0xab.toByte(), 0xcd.toByte()))

        assertEquals("0102abcd", ElfBuildIdReader.parseUniqueGnuBuildId(note))
        assertNull(ElfBuildIdReader.parseUniqueGnuBuildId(note + note))
        assertNull(ElfBuildIdReader.parseUniqueGnuBuildId(note + byteArrayOf(0)))
    }

    @Test
    fun knownProfileRequiresBothPrimaryIdentifiersAndExactRanges() {
        assertTrue(
            ArtKnownProfilePolicy.primaryMatches(
                AndroidArtIdentityProbe.KNOWN_RC2_ART_SHA256,
                AndroidArtIdentityProbe.KNOWN_RC2_ART_BUILD_ID
            )
        )
        assertFalse(
            ArtKnownProfilePolicy.primaryMatches(
                AndroidArtIdentityProbe.KNOWN_RC2_ART_SHA256,
                "different"
            )
        )
        assertEquals(
            ArtRangeCheckState.EXACT_MATCH,
            ArtKnownProfilePolicy.rangeState("abc", "abc")
        )
        assertEquals(
            ArtRangeCheckState.MISMATCH,
            ArtKnownProfilePolicy.rangeState("def", "abc")
        )
        assertEquals(
            ArtRangeCheckState.READ_FAILED,
            ArtKnownProfilePolicy.rangeState(null, "abc")
        )
    }

    @Test
    fun machineValuesCannotCreateOrSplitKeyValueLines() {
        assertEquals("null", MachineReportValue.encode(null))
        assertEquals(
            "a%3Db%25c%0Aline%0D%09end%7F",
            MachineReportValue.encode("a=b%c\nline\r\tend\u007f")
        )
    }

    private fun gnuBuildIdNote(description: ByteArray): ByteArray {
        val paddedDescription = (description.size + 3) and -4
        return ByteBuffer.allocate(16 + paddedDescription)
            .order(ByteOrder.LITTLE_ENDIAN)
            .putInt(4)
            .putInt(description.size)
            .putInt(3)
            .put(byteArrayOf('G'.code.toByte(), 'N'.code.toByte(), 'U'.code.toByte(), 0))
            .put(description)
            .array()
    }
}
