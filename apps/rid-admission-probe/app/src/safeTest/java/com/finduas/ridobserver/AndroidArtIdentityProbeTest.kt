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
    fun elf32AndElf64LittleEndianImagesReturnTheSameGnuBuildId() {
        for (elfClass in listOf(1, 2)) {
            val bytes = elfImage(elfClass)
            assertEquals("0102abcd", readElf(bytes))
            assertFalse(ArtKnownProfilePolicy.primaryMatches("TEST-UNKNOWN-ART", readElf(bytes)))
        }
    }

    @Test
    fun elf32UsesUnsignedProgramAndNoteOffsets() {
        val image = elfImage(1)
        val programOffset = 0x80000000L
        val noteOffset = 0x90000000L
        val header = image.copyOfRange(0, 52)
        val program = image.copyOfRange(52, 84)
        val note = image.copyOfRange(84, image.size)
        ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN).putInt(28, programOffset.toInt())
        ByteBuffer.wrap(program).order(ByteOrder.LITTLE_ENDIAN).putInt(4, noteOffset.toInt())
        val sections = mapOf(0L to header, programOffset to program, noteOffset to note)
        val reads = mutableListOf<Long>()
        val source = PositionalReadSource { offset, destination, count ->
            reads += offset
            val section = sections[offset]
            if (section == null || count > section.size) {
                false
            } else {
                section.copyInto(destination, endIndex = count)
                true
            }
        }

        assertEquals("0102abcd", ElfBuildIdReader.read(source, noteOffset + note.size))
        assertTrue(reads.contains(programOffset))
        assertTrue(reads.contains(noteOffset))
    }

    @Test
    fun elfBuildIdRejectsUnknownClassBigEndianAndTruncatedHeaders() {
        for (elfClass in listOf(1, 2)) {
            val image = elfImage(elfClass)
            assertNull(readElf(image.copyOf().apply { this[4] = 3 }))
            assertNull(readElf(image.copyOf().apply { this[5] = 2 }))
            assertNull(readElf(image.copyOf().apply { this[0] = 0 }))
            val headerSize = if (elfClass == 1) 52 else 64
            for (length in listOf(0, 15, headerSize - 1)) {
                assertNull(readElf(image.copyOf(length)))
            }
        }
    }

    @Test
    fun elfProgramTableRequiresFullEntriesValidCountAndFileBounds() {
        for (elfClass in listOf(1, 2)) {
            val entrySizeOffset = if (elfClass == 1) 42 else 54
            val countOffset = if (elfClass == 1) 44 else 56
            val minimumEntrySize = if (elfClass == 1) 32 else 56
            val tooShort = elfImage(elfClass)
            ByteBuffer.wrap(tooShort).order(ByteOrder.LITTLE_ENDIAN)
                .putShort(entrySizeOffset, (minimumEntrySize - 1).toShort())
            assertNull(readElf(tooShort))
            for (count in listOf(0, 1025, 65535)) {
                val image = elfImage(elfClass)
                ByteBuffer.wrap(image).order(ByteOrder.LITTLE_ENDIAN).putShort(countOffset, count.toShort())
                assertNull(readElf(image))
            }
            val outside = elfImage(elfClass)
            val view = ByteBuffer.wrap(outside).order(ByteOrder.LITTLE_ENDIAN)
            if (elfClass == 1) view.putInt(28, outside.size - 1) else view.putLong(32, outside.size - 1L)
            assertNull(readElf(outside))
        }
    }

    @Test
    fun elfNoteOffsetAndUnsignedSizeCannotEscapeFileOrAllocationBounds() {
        for (elfClass in listOf(1, 2)) {
            val headerSize = if (elfClass == 1) 52 else 64
            val outside = elfImage(elfClass)
            val outsideView = ByteBuffer.wrap(outside).order(ByteOrder.LITTLE_ENDIAN)
            if (elfClass == 1) {
                outsideView.putInt(headerSize + 4, outside.size - 1)
            } else {
                outsideView.putLong(headerSize + 8, outside.size - 1L)
            }
            assertNull(readElf(outside))
            for (size in listOf(0L, 1024 * 1024 + 1L, 0xffffffffL)) {
                val oversized = elfImage(elfClass)
                val view = ByteBuffer.wrap(oversized).order(ByteOrder.LITTLE_ENDIAN)
                if (elfClass == 1) view.putInt(headerSize + 16, size.toInt())
                else view.putLong(headerSize + 32, size)
                assertNull(readElf(oversized, 0x100000000L))
            }
        }
    }

    @Test
    fun elf64NegativeAndOverflowingOffsetsRemainRejected() {
        for (offset in listOf(-1L, Long.MAX_VALUE - 1L)) {
            val table = elfImage(2)
            ByteBuffer.wrap(table).order(ByteOrder.LITTLE_ENDIAN).putLong(32, offset)
            assertNull(readElf(table, Long.MAX_VALUE))
            val note = elfImage(2)
            ByteBuffer.wrap(note).order(ByteOrder.LITTLE_ENDIAN).putLong(64 + 8, offset)
            assertNull(readElf(note, Long.MAX_VALUE))
        }
    }

    @Test
    fun elfReadFailuresAndDuplicateBuildIdsDoNotProduceAnIdentity() {
        for (elfClass in listOf(1, 2)) {
            val image = elfImage(elfClass)
            val headerSize = if (elfClass == 1) 52 else 64
            val noteOffset = headerSize + if (elfClass == 1) 32 else 56
            for (offset in listOf(0L, headerSize.toLong(), noteOffset.toLong())) {
                val source = PositionalReadSource { at, destination, count ->
                    at != offset && readBytes(image, at, destination, count)
                }
                assertNull(ElfBuildIdReader.read(source, image.size.toLong()))
            }
            assertNull(readElf(image.copyOf(image.size - 1), image.size.toLong()))
            val note = gnuBuildIdNote(byteArrayOf(1, 2, 0xab.toByte(), 0xcd.toByte()))
            assertNull(readElf(elfImage(elfClass, note + note)))
        }
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

    private fun elfImage(
        elfClass: Int,
        note: ByteArray = gnuBuildIdNote(byteArrayOf(1, 2, 0xab.toByte(), 0xcd.toByte()))
    ): ByteArray {
        val headerSize = if (elfClass == 1) 52 else 64
        val programSize = if (elfClass == 1) 32 else 56
        val noteOffset = headerSize + programSize
        val view = ByteBuffer.allocate(noteOffset + note.size).order(ByteOrder.LITTLE_ENDIAN)
        view.put(byteArrayOf(0x7f, 'E'.code.toByte(), 'L'.code.toByte(), 'F'.code.toByte()))
        view.put(4, elfClass.toByte())
        view.put(5, 1)
        view.put(6, 1)
        view.putShort(16, 3) // ET_DYN
        view.putShort(18, (if (elfClass == 1) 40 else 183).toShort()) // ARM / AArch64
        view.putInt(20, 1)
        view.putInt(headerSize, 4) // PT_NOTE
        if (elfClass == 1) {
            view.putInt(28, headerSize)
            view.putShort(40, headerSize.toShort())
            view.putShort(42, programSize.toShort())
            view.putShort(44, 1)
            view.putInt(headerSize + 4, noteOffset)
            view.putInt(headerSize + 16, note.size)
        } else {
            view.putLong(32, headerSize.toLong())
            view.putShort(52, headerSize.toShort())
            view.putShort(54, programSize.toShort())
            view.putShort(56, 1)
            view.putLong(headerSize + 8, noteOffset.toLong())
            view.putLong(headerSize + 32, note.size.toLong())
        }
        view.position(noteOffset)
        view.put(note)
        return view.array()
    }

    private fun readElf(bytes: ByteArray, fileSize: Long = bytes.size.toLong()): String? =
        ElfBuildIdReader.read(
            PositionalReadSource { offset, destination, count -> readBytes(bytes, offset, destination, count) },
            fileSize
        )

    private fun readBytes(bytes: ByteArray, offset: Long, destination: ByteArray, count: Int): Boolean {
        if (offset < 0 || offset > bytes.size || count > bytes.size - offset) return false
        bytes.copyInto(destination, startIndex = offset.toInt(), endIndex = offset.toInt() + count)
        return true
    }
}
