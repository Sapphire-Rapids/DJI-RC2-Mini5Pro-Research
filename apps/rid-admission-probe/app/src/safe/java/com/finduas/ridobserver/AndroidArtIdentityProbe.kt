package com.finduas.ridobserver

import android.os.Build
import android.system.ErrnoException
import android.system.Os
import android.system.OsConstants
import android.system.StructStat
import java.io.File
import java.io.FileDescriptor
import java.io.FileNotFoundException
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.security.MessageDigest

internal enum class ArtIdentityState {
    NOT_RUN,
    MAPS_READ_DENIED,
    MAPS_READ_ERROR,
    MAPS_PARSE_ERROR,
    NO_LIBART_MAPPING,
    MULTIPLE_FILE_IDENTITIES,
    MAPS_FILE_COVERAGE_INVALID,
    MAPS_SECOND_READ_DENIED,
    MAPS_SECOND_READ_ERROR,
    MAPS_CHANGED_DURING_READ,
    MAPPED_FILE_DELETED,
    MAPPED_PATH_INVALID,
    MAPPED_PATH_SYMLINK,
    MAPPED_DEVICE_ZERO,
    FILE_READ_DENIED,
    FILE_READ_ERROR,
    FILE_NOT_REGULAR,
    FILE_DEVICE_ZERO,
    FILE_IDENTITY_MISMATCH,
    FILE_CHANGED_DURING_READ,
    ELF_BUILD_ID_FAILED,
    KNOWN_PROFILE_RANGE_MISMATCH,
    KNOWN_PROFILE_RANGE_READ_FAILED,
    COMPLETE
}

internal enum class KnownRc2ArtProfileState {
    NOT_EVALUATED,
    DIFFERENT,
    EXACT_MATCH
}

internal enum class ArtRangeCheckState {
    NOT_APPLICABLE,
    READ_FAILED,
    MISMATCH,
    EXACT_MATCH
}

internal data class ArtRangeCheck(
    val offset: Long,
    val size: Int,
    val state: ArtRangeCheckState = ArtRangeCheckState.NOT_APPLICABLE,
    val sha256: String? = null
)

internal data class AndroidArtIdentityResult(
    val state: ArtIdentityState = ArtIdentityState.NOT_RUN,
    val buildFingerprint: String = Build.FINGERPRINT,
    val sdk: Int = Build.VERSION.SDK_INT,
    val supportedAbis: String = Build.SUPPORTED_ABIS.joinToString(","),
    val processIs64Bit: Boolean = android.os.Process.is64Bit(),
    val pageSizeBytes: Long? = null,
    val mapEntries: List<ArtMapEntry> = emptyList(),
    val mapsEntryCount: Int = 0,
    val malformedLibartEntryCount: Int = 0,
    val fileIdentityCount: Int = 0,
    val secondMapsEntryCount: Int? = null,
    val secondMalformedLibartEntryCount: Int? = null,
    val mapsSnapshotStable: Boolean? = null,
    val mappedDevice: String? = null,
    val mappedInode: Long? = null,
    val mappedPath: String? = null,
    val mappedFileDeleted: Boolean? = null,
    val mappedDeviceNonZero: Boolean? = null,
    val finalPathSymlink: Boolean? = null,
    val fileDeviceNonZero: Boolean? = null,
    val fileIsRegular: Boolean? = null,
    val fileMetadataStable: Boolean? = null,
    val fileSize: Long? = null,
    val wholeFileSha256: String? = null,
    val gnuBuildId: String? = null,
    val knownRc2Profile: KnownRc2ArtProfileState = KnownRc2ArtProfileState.NOT_EVALUATED,
    val agentUnloadRange: ArtRangeCheck = ArtRangeCheck(
        offset = AndroidArtIdentityProbe.KNOWN_AGENT_UNLOAD_RANGE_OFFSET,
        size = AndroidArtIdentityProbe.KNOWN_AGENT_UNLOAD_RANGE_SIZE
    ),
    val runtimeAttachAgentRange: ArtRangeCheck = ArtRangeCheck(
        offset = AndroidArtIdentityProbe.KNOWN_RUNTIME_ATTACH_AGENT_RANGE_OFFSET,
        size = AndroidArtIdentityProbe.KNOWN_RUNTIME_ATTACH_AGENT_RANGE_SIZE
    )
) {
    val sectionComplete: Boolean
        get() = state == ArtIdentityState.COMPLETE
}

internal data class ArtMapEntry(
    val startAddress: Long,
    val endAddress: Long,
    val permissions: String,
    val fileOffset: Long,
    val device: String,
    val inode: Long,
    val path: String,
    val deleted: Boolean
) {
    val addressRange: String
        get() = "${startAddress.toString(16)}-${endAddress.toString(16)}"

    val virtualSize: Long
        get() = endAddress - startAddress

    val fileCoverageEndExclusive: Long
        get() = fileOffset + virtualSize

    val identity: ArtMappedFileIdentity
        get() = ArtMappedFileIdentity(device, inode, path, deleted)
}

internal data class ArtMappedFileIdentity(
    val device: String,
    val inode: Long,
    val path: String,
    val deleted: Boolean
)

/** A normalized exact-basename libart subset of one /proc/self/maps snapshot. */
internal data class ArtMapsScan(
    val entries: List<ArtMapEntry>,
    val malformedCandidateCount: Int,
    val pageSizeBytes: Long
) {
    val hasReadableMapping: Boolean
        get() = entries.any { it.permissions[0] == 'r' }

    val hasExecutableMapping: Boolean
        get() = entries.any { it.permissions[2] == 'x' }

    val identities: List<ArtMappedFileIdentity>
        get() = entries.map(ArtMapEntry::identity).distinct()
}

internal object ArtMapsParser {
    private val whitespace = Regex("\\s+")
    private val hexadecimal = Regex("[0-9a-fA-F]+")
    private val decimal = Regex("[0-9]+")
    private val permissions = Regex("[r-][w-][x-][ps]")
    private const val DELETED_SUFFIX = " (deleted)"
    private const val DEFAULT_PAGE_SIZE = 4096L

    fun parse(
        lines: Sequence<String>,
        pageSizeBytes: Long = DEFAULT_PAGE_SIZE
    ): ArtMapsScan {
        require(isPowerOfTwo(pageSizeBytes))
        val entries = mutableListOf<ArtMapEntry>()
        var malformed = 0
        for (line in lines) {
            if (!line.contains("libart.so")) continue
            val fields = line.trim().split(whitespace, limit = 6)
            if (fields.size != 6) {
                malformed += 1
                continue
            }
            val rawPath = fields[5]
            val deleted = rawPath.endsWith(DELETED_SUFFIX)
            val path = if (deleted) rawPath.removeSuffix(DELETED_SUFFIX) else rawPath
            if (File(path).name != "libart.so") continue

            val range = parseAddressRange(fields[0], pageSizeBytes)
            val fileOffset = parseHexLong(fields[2])
            val normalizedDevice = LinuxDeviceIdentity.normalizeNonZero(fields[3])
            val inode = if (decimal.matches(fields[4])) fields[4].toLongOrNull() else null
            val geometryValid = range != null &&
                fileOffset != null &&
                fileOffset % pageSizeBytes == 0L &&
                fileOffset <= Long.MAX_VALUE - (range?.let { it.second - it.first } ?: 0L)
            val valid = geometryValid &&
                permissions.matches(fields[1]) &&
                normalizedDevice != null &&
                inode != null && inode > 0L &&
                path.startsWith('/') &&
                '\u0000' !in path && '\n' !in path && '\r' !in path
            if (!valid) {
                malformed += 1
                continue
            }
            entries += ArtMapEntry(
                startAddress = requireNotNull(range).first,
                endAddress = range.second,
                permissions = fields[1],
                fileOffset = requireNotNull(fileOffset),
                device = requireNotNull(normalizedDevice),
                inode = requireNotNull(inode),
                path = path,
                deleted = deleted
            )
        }
        return ArtMapsScan(entries, malformed, pageSizeBytes)
    }

    private fun parseAddressRange(value: String, pageSizeBytes: Long): Pair<Long, Long>? {
        val separator = value.indexOf('-')
        if (separator <= 0 || separator != value.lastIndexOf('-') || separator == value.lastIndex) {
            return null
        }
        val start = parseHexLong(value.substring(0, separator)) ?: return null
        val end = parseHexLong(value.substring(separator + 1)) ?: return null
        if (
            start <= 0L ||
            start >= end ||
            start % pageSizeBytes != 0L ||
            end % pageSizeBytes != 0L
        ) {
            return null
        }
        return start to end
    }

    private fun parseHexLong(value: String): Long? =
        if (hexadecimal.matches(value)) value.toLongOrNull(16) else null

    private fun isPowerOfTwo(value: Long): Boolean =
        value > 0L && (value and (value - 1L)) == 0L
}

/** Linux dev_t comparison for the major:minor identity printed by /proc/self/maps. */
internal object LinuxDeviceIdentity {
    private const val MAX_COMPONENT = 0xffff_ffffL
    private val hexadecimal = Regex("[0-9a-fA-F]+")

    fun normalizeNonZero(mappedDevice: String): String? {
        val parts = mappedDevice.split(':', limit = 2)
        if (
            parts.size != 2 ||
            !hexadecimal.matches(parts[0]) ||
            !hexadecimal.matches(parts[1])
        ) return null
        val mappedMajor = parts[0].toLongOrNull(16) ?: return null
        val mappedMinor = parts[1].toLongOrNull(16) ?: return null
        if (
            mappedMajor !in 0L..MAX_COMPONENT || mappedMinor !in 0L..MAX_COMPONENT ||
            (mappedMajor == 0L && mappedMinor == 0L)
        ) {
            return null
        }
        return "${mappedMajor.toString(16)}:${mappedMinor.toString(16)}"
    }

    fun matches(mappedDevice: String, statDevice: Long): Boolean {
        if (statDevice == 0L) return false
        val normalized = normalizeNonZero(mappedDevice) ?: return false
        val parts = normalized.split(':', limit = 2)
        return parts[0].toLong(16) == major(statDevice) &&
            parts[1].toLong(16) == minor(statDevice)
    }

    internal fun major(device: Long): Long =
        ((device ushr 8) and 0xfffL) or ((device ushr 32) and 0xfffff000L)

    internal fun minor(device: Long): Long =
        (device and 0xffL) or ((device ushr 12) and 0xffffff00L)

    internal fun makeDevice(major: Long, minor: Long): Long =
        ((major and 0xfffL) shl 8) or
            (minor and 0xffL) or
            ((major and 0xfffff000L) shl 32) or
            ((minor and 0xffffff00L) shl 12)
}

internal object ArtMapAdmissionPolicy {
    /** Null means exactly one non-zero file identity with readable and executable mappings. */
    fun rejection(scan: ArtMapsScan): ArtIdentityState? = when {
        scan.malformedCandidateCount != 0 -> ArtIdentityState.MAPS_PARSE_ERROR
        scan.identities.isEmpty() -> ArtIdentityState.NO_LIBART_MAPPING
        scan.identities.size != 1 -> ArtIdentityState.MULTIPLE_FILE_IDENTITIES
        LinuxDeviceIdentity.normalizeNonZero(scan.identities.single().device) == null ->
            ArtIdentityState.MAPPED_DEVICE_ZERO
        !scan.hasReadableMapping || !scan.hasExecutableMapping ->
            ArtIdentityState.MAPS_PARSE_ERROR
        else -> null
    }
}

internal object ArtMapCoveragePolicy {
    /** Validates normalized VMAs against the page-rounded exact descriptor size. */
    fun isValid(entries: List<ArtMapEntry>, fileSize: Long, pageSizeBytes: Long): Boolean {
        if (
            entries.isEmpty() || fileSize <= 0L || pageSizeBytes <= 0L ||
            (pageSizeBytes and (pageSizeBytes - 1L)) != 0L
        ) {
            return false
        }
        val remainder = fileSize % pageSizeBytes
        val roundedFileSize = if (remainder == 0L) {
            fileSize
        } else {
            val padding = pageSizeBytes - remainder
            if (fileSize > Long.MAX_VALUE - padding) return false
            fileSize + padding
        }
        val byAddress = entries.sortedBy(ArtMapEntry::startAddress)
        for (index in byAddress.indices) {
            val entry = byAddress[index]
            if (
                entry.startAddress <= 0L ||
                entry.startAddress >= entry.endAddress ||
                entry.startAddress % pageSizeBytes != 0L ||
                entry.endAddress % pageSizeBytes != 0L ||
                entry.fileOffset < 0L || entry.fileOffset % pageSizeBytes != 0L ||
                entry.fileOffset >= roundedFileSize ||
                entry.virtualSize <= 0L ||
                entry.fileOffset > Long.MAX_VALUE - entry.virtualSize ||
                entry.fileCoverageEndExclusive > roundedFileSize
            ) {
                return false
            }
            if (index > 0 && byAddress[index - 1].endAddress > entry.startAddress) {
                return false
            }
        }
        return true
    }
}

internal data class ExactFileMetadata(
    val device: Long,
    val inode: Long,
    val mode: Int,
    val size: Long,
    val modifiedSeconds: Long,
    val modifiedNanoseconds: Long,
    val changedSeconds: Long,
    val changedNanoseconds: Long
)

internal object ExactFileMetadataPolicy {
    fun isWellFormed(metadata: ExactFileMetadata): Boolean =
        metadata.device != 0L &&
            metadata.inode > 0L &&
            metadata.size >= 0L &&
            metadata.modifiedNanoseconds in 0L..999_999_999L &&
            metadata.changedNanoseconds in 0L..999_999_999L

    fun same(left: ExactFileMetadata, right: ExactFileMetadata): Boolean =
        isWellFormed(left) && isWellFormed(right) && left == right
}

internal object ArtKnownProfilePolicy {
    fun primaryMatches(sha256: String?, buildId: String?): Boolean =
        sha256 == AndroidArtIdentityProbe.KNOWN_RC2_ART_SHA256 &&
            buildId == AndroidArtIdentityProbe.KNOWN_RC2_ART_BUILD_ID

    fun rangeState(actual: String?, expected: String): ArtRangeCheckState = when {
        actual == null -> ArtRangeCheckState.READ_FAILED
        actual == expected -> ArtRangeCheckState.EXACT_MATCH
        else -> ArtRangeCheckState.MISMATCH
    }
}

internal object MachineReportValue {
    fun encode(value: String?): String {
        if (value == null) return "null"
        return buildString(value.length) {
            for (character in value) {
                when (character) {
                    '%' -> append("%25")
                    '=' -> append("%3D")
                    '\r' -> append("%0D")
                    '\n' -> append("%0A")
                    '\u007f' -> append("%7F")
                    else -> if (character.code < 0x20) {
                        append('%')
                        append("0123456789ABCDEF"[character.code ushr 4])
                        append("0123456789ABCDEF"[character.code and 0x0f])
                    } else {
                        append(character)
                    }
                }
            }
        }
    }
}

internal fun interface PositionalReadSource {
    /** Returns true only after reading exactly [byteCount] bytes at [offset]. */
    fun readFullyAt(offset: Long, destination: ByteArray, byteCount: Int): Boolean
}

internal object ElfBuildIdReader {
    private const val ELF_HEADER_SIZE = 64
    private const val ELF_CLASS_64 = 2
    private const val ELF_DATA_LITTLE_ENDIAN = 1
    private const val ELF64_PROGRAM_HEADER_MIN_SIZE = 56
    private const val PT_NOTE = 4
    private const val NT_GNU_BUILD_ID = 3
    private const val MAX_PROGRAM_HEADERS = 1024
    private const val MAX_NOTE_SEGMENT_BYTES = 1024 * 1024

    fun read(file: RandomAccessFile, fileSize: Long): String? = read(
        PositionalReadSource { offset, destination, byteCount ->
            try {
                file.seek(offset)
                file.readFully(destination, 0, byteCount)
                true
            } catch (_: Throwable) {
                false
            }
        },
        fileSize
    )

    fun read(source: PositionalReadSource, fileSize: Long): String? {
        if (fileSize < ELF_HEADER_SIZE) return null
        val header = ByteArray(ELF_HEADER_SIZE)
        if (!source.readFullyAt(0L, header, header.size)) return null
        if (
            header[0] != 0x7f.toByte() || header[1] != 'E'.code.toByte() ||
            header[2] != 'L'.code.toByte() || header[3] != 'F'.code.toByte() ||
            header[4].toInt() != ELF_CLASS_64 ||
            header[5].toInt() != ELF_DATA_LITTLE_ENDIAN
        ) {
            return null
        }
        val view = ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN)
        val programOffset = view.getLong(32)
        val programEntrySize = view.getShort(54).toInt() and 0xffff
        val programCount = view.getShort(56).toInt() and 0xffff
        if (
            programOffset < 0L || programEntrySize < ELF64_PROGRAM_HEADER_MIN_SIZE ||
            programCount <= 0 || programCount > MAX_PROGRAM_HEADERS ||
            !rangeWithinFile(programOffset, programEntrySize.toLong() * programCount, fileSize)
        ) {
            return null
        }

        val matches = mutableListOf<String>()
        repeat(programCount) { index ->
            val programHeader = ByteArray(programEntrySize)
            val headerOffset = programOffset + index.toLong() * programEntrySize
            if (!source.readFullyAt(headerOffset, programHeader, programHeader.size)) return null
            val program = ByteBuffer.wrap(programHeader).order(ByteOrder.LITTLE_ENDIAN)
            if (program.getInt(0) != PT_NOTE) return@repeat
            val noteOffset = program.getLong(8)
            val noteSize = program.getLong(32)
            if (
                noteSize <= 0L || noteSize > MAX_NOTE_SEGMENT_BYTES ||
                !rangeWithinFile(noteOffset, noteSize, fileSize)
            ) {
                return null
            }
            val notes = ByteArray(noteSize.toInt())
            if (!source.readFullyAt(noteOffset, notes, notes.size)) return null
            parseBuildIds(notes)?.let(matches::addAll) ?: return null
        }
        return matches.singleOrNull()
    }

    internal fun parseUniqueGnuBuildId(notes: ByteArray): String? =
        parseBuildIds(notes)?.singleOrNull()

    private fun parseBuildIds(notes: ByteArray): List<String>? {
        val matches = mutableListOf<String>()
        var offset = 0
        while (offset < notes.size) {
            if (offset > notes.size - 12) return null
            val header = ByteBuffer.wrap(notes, offset, 12).order(ByteOrder.LITTLE_ENDIAN)
            val nameSize = header.int.toLong() and 0xffffffffL
            val descriptionSize = header.int.toLong() and 0xffffffffL
            val type = header.int
            val nameOffset = offset.toLong() + 12L
            val descriptionOffset = alignFour(nameOffset + nameSize) ?: return null
            val nextOffset = alignFour(descriptionOffset + descriptionSize) ?: return null
            if (
                nameSize > Int.MAX_VALUE || descriptionSize > Int.MAX_VALUE ||
                nextOffset <= offset || nextOffset > notes.size
            ) {
                return null
            }
            val nameStart = nameOffset.toInt()
            val nameEnd = nameStart + nameSize.toInt()
            val descriptionStart = descriptionOffset.toInt()
            val descriptionEnd = descriptionStart + descriptionSize.toInt()
            if (nameEnd > notes.size || descriptionEnd > notes.size) return null
            val isGnu = nameSize == 4L &&
                notes[nameStart] == 'G'.code.toByte() &&
                notes[nameStart + 1] == 'N'.code.toByte() &&
                notes[nameStart + 2] == 'U'.code.toByte() &&
                notes[nameStart + 3] == 0.toByte()
            if (isGnu && type == NT_GNU_BUILD_ID) {
                if (descriptionSize <= 0L || descriptionSize > 64L) return null
                matches += hex(notes.copyOfRange(descriptionStart, descriptionEnd))
            }
            offset = nextOffset.toInt()
        }
        return matches
    }

    private fun alignFour(value: Long): Long? = if (value > Long.MAX_VALUE - 3L) {
        null
    } else {
        (value + 3L) and -4L
    }

    private fun rangeWithinFile(offset: Long, size: Long, fileSize: Long): Boolean =
        offset >= 0L && size >= 0L && offset <= fileSize && size <= fileSize - offset

    private fun hex(bytes: ByteArray): String = bytes.joinToString("") {
        "%02x".format(it.toInt() and 0xff)
    }
}

/**
 * Reads only this probe process's mapping table and the exact non-symlink regular libart file it
 * names. It does not inspect another process, attach an agent, load a library, resolve a symbol,
 * or invoke any ART/DJI entry point.
 */
internal object AndroidArtIdentityProbe {
    private const val SELF_MAPS_PATH = "/proc/self/maps"

    internal const val KNOWN_RC2_ART_SHA256 =
        "3ec3d232ad7f4099c42f014b87658be47e83d7e21a7a053fb16c4d146103745d"
    internal const val KNOWN_RC2_ART_BUILD_ID =
        "5f839ecc60b9ae39764305b5fee6ed37"
    internal const val KNOWN_AGENT_UNLOAD_RANGE_OFFSET = 0x5ccfa0L
    internal const val KNOWN_AGENT_UNLOAD_RANGE_SIZE = 0x100
    internal const val KNOWN_AGENT_UNLOAD_RANGE_SHA256 =
        "098c16b8613f438294017b8af2e2e45685556a9cf5c6882120f08a5ea315c668"
    internal const val KNOWN_RUNTIME_ATTACH_AGENT_RANGE_OFFSET = 0x56bfc4L
    internal const val KNOWN_RUNTIME_ATTACH_AGENT_RANGE_SIZE = 0xebc
    internal const val KNOWN_RUNTIME_ATTACH_AGENT_RANGE_SHA256 =
        "9db764e816c6771623e660b308d2527da4e57d05530ae7a3c8dfdf9d07dec80a"

    fun run(): AndroidArtIdentityResult {
        val base = AndroidArtIdentityResult()
        val pageSize = try {
            Os.sysconf(OsConstants._SC_PAGESIZE)
        } catch (_: Throwable) {
            return base.copy(state = ArtIdentityState.MAPS_READ_ERROR)
        }
        if (pageSize <= 0L || (pageSize and (pageSize - 1L)) != 0L) {
            return base.copy(state = ArtIdentityState.MAPS_READ_ERROR)
        }

        val scan = try {
            readMapsSnapshot(pageSize)
        } catch (_: SecurityException) {
            return base.copy(state = ArtIdentityState.MAPS_READ_DENIED, pageSizeBytes = pageSize)
        } catch (_: FileNotFoundException) {
            return base.copy(state = ArtIdentityState.MAPS_READ_DENIED, pageSizeBytes = pageSize)
        } catch (_: Throwable) {
            return base.copy(state = ArtIdentityState.MAPS_READ_ERROR, pageSizeBytes = pageSize)
        }

        val identities = scan.identities
        val scanResult = base.copy(
            pageSizeBytes = pageSize,
            mapEntries = scan.entries,
            mapsEntryCount = scan.entries.size,
            malformedLibartEntryCount = scan.malformedCandidateCount,
            fileIdentityCount = identities.size
        )
        ArtMapAdmissionPolicy.rejection(scan)?.let { rejection ->
            return scanResult.copy(state = rejection)
        }

        val identity = identities.single()
        val mappedDeviceNonZero = LinuxDeviceIdentity.normalizeNonZero(identity.device) != null
        val identified = scanResult.copy(
            mappedDevice = identity.device,
            mappedInode = identity.inode,
            mappedPath = identity.path,
            mappedFileDeleted = identity.deleted,
            mappedDeviceNonZero = mappedDeviceNonZero
        )
        if (!mappedDeviceNonZero) {
            return identified.copy(state = ArtIdentityState.MAPPED_DEVICE_ZERO)
        }
        if (identity.deleted) {
            return identified.copy(state = ArtIdentityState.MAPPED_FILE_DELETED)
        }
        if (!File(identity.path).isAbsolute) {
            return identified.copy(state = ArtIdentityState.MAPPED_PATH_INVALID)
        }

        return try {
            val pathBefore = Os.lstat(identity.path)
            if (OsConstants.S_ISLNK(pathBefore.st_mode)) {
                return identified.copy(
                    state = ArtIdentityState.MAPPED_PATH_SYMLINK,
                    finalPathSymlink = true
                )
            }
            if (!OsConstants.S_ISREG(pathBefore.st_mode)) {
                return identified.copy(
                    state = ArtIdentityState.FILE_NOT_REGULAR,
                    finalPathSymlink = false,
                    fileIsRegular = false
                )
            }
            if (pathBefore.st_dev == 0L) {
                return identified.copy(
                    state = ArtIdentityState.FILE_DEVICE_ZERO,
                    finalPathSymlink = false,
                    fileDeviceNonZero = false,
                    fileIsRegular = true
                )
            }

            val descriptor = Os.open(
                identity.path,
                OsConstants.O_RDONLY or OsConstants.O_CLOEXEC or OsConstants.O_NOFOLLOW,
                0
            )
            try {
                inspectOpenDescriptor(identified, identity, scan, pathBefore, descriptor)
            } finally {
                try {
                    Os.close(descriptor)
                } catch (_: Throwable) {
                    // The complete decision is based on the already captured descriptor evidence.
                }
            }
        } catch (error: ErrnoException) {
            if (error.errno == OsConstants.ELOOP) {
                identified.copy(
                    state = ArtIdentityState.MAPPED_PATH_SYMLINK,
                    finalPathSymlink = true
                )
            } else if (
                error.errno == OsConstants.EACCES || error.errno == OsConstants.EPERM ||
                error.errno == OsConstants.ENOENT
            ) {
                identified.copy(state = ArtIdentityState.FILE_READ_DENIED)
            } else {
                identified.copy(state = ArtIdentityState.FILE_READ_ERROR)
            }
        } catch (_: SecurityException) {
            identified.copy(state = ArtIdentityState.FILE_READ_DENIED)
        } catch (_: FileNotFoundException) {
            identified.copy(state = ArtIdentityState.FILE_READ_DENIED)
        } catch (_: Throwable) {
            identified.copy(state = ArtIdentityState.FILE_READ_ERROR)
        }
    }

    private fun inspectOpenDescriptor(
        identified: AndroidArtIdentityResult,
        identity: ArtMappedFileIdentity,
        firstScan: ArtMapsScan,
        pathBefore: StructStat,
        descriptor: FileDescriptor
    ): AndroidArtIdentityResult {
        val descriptorBefore = Os.fstat(descriptor)
        if (!OsConstants.S_ISREG(descriptorBefore.st_mode)) {
            return identified.copy(
                state = ArtIdentityState.FILE_NOT_REGULAR,
                finalPathSymlink = false,
                fileDeviceNonZero = descriptorBefore.st_dev != 0L,
                fileIsRegular = false
            )
        }
        if (descriptorBefore.st_dev == 0L) {
            return identified.copy(
                state = ArtIdentityState.FILE_DEVICE_ZERO,
                finalPathSymlink = false,
                fileDeviceNonZero = false,
                fileIsRegular = true
            )
        }
        val pathMetadataBefore = exactMetadata(pathBefore)
        val descriptorMetadataBefore = exactMetadata(descriptorBefore)
        if (
            identity.inode != descriptorBefore.st_ino ||
            !LinuxDeviceIdentity.matches(identity.device, descriptorBefore.st_dev) ||
            !ExactFileMetadataPolicy.same(pathMetadataBefore, descriptorMetadataBefore)
        ) {
            return identified.copy(
                state = ArtIdentityState.FILE_IDENTITY_MISMATCH,
                finalPathSymlink = false,
                fileDeviceNonZero = true,
                fileIsRegular = true,
                fileMetadataStable = false
            )
        }
        if (!ArtMapCoveragePolicy.isValid(
                firstScan.entries,
                descriptorBefore.st_size,
                firstScan.pageSizeBytes
            )
        ) {
            return identified.copy(
                state = ArtIdentityState.MAPS_FILE_COVERAGE_INVALID,
                finalPathSymlink = false,
                fileDeviceNonZero = true,
                fileIsRegular = true,
                fileMetadataStable = false,
                fileSize = descriptorBefore.st_size
            )
        }

        val source = descriptorSource(descriptor)
        val wholeSha256 = hashWholeFile(source, descriptorBefore.st_size)
        val buildId = ElfBuildIdReader.read(source, descriptorBefore.st_size)
        var agentUnloadRange = identified.agentUnloadRange
        var runtimeAttachAgentRange = identified.runtimeAttachAgentRange
        var profile = KnownRc2ArtProfileState.DIFFERENT
        var terminalState = ArtIdentityState.COMPLETE
        if (buildId == null) {
            terminalState = ArtIdentityState.ELF_BUILD_ID_FAILED
            profile = KnownRc2ArtProfileState.NOT_EVALUATED
        } else if (ArtKnownProfilePolicy.primaryMatches(wholeSha256, buildId)) {
            profile = KnownRc2ArtProfileState.EXACT_MATCH
            val agentUnloadDigest = hashRange(
                source,
                descriptorBefore.st_size,
                KNOWN_AGENT_UNLOAD_RANGE_OFFSET,
                KNOWN_AGENT_UNLOAD_RANGE_SIZE
            )
            val runtimeAttachAgentDigest = hashRange(
                source,
                descriptorBefore.st_size,
                KNOWN_RUNTIME_ATTACH_AGENT_RANGE_OFFSET,
                KNOWN_RUNTIME_ATTACH_AGENT_RANGE_SIZE
            )
            agentUnloadRange = agentUnloadRange.copy(
                state = ArtKnownProfilePolicy.rangeState(
                    agentUnloadDigest,
                    KNOWN_AGENT_UNLOAD_RANGE_SHA256
                ),
                sha256 = agentUnloadDigest
            )
            runtimeAttachAgentRange = runtimeAttachAgentRange.copy(
                state = ArtKnownProfilePolicy.rangeState(
                    runtimeAttachAgentDigest,
                    KNOWN_RUNTIME_ATTACH_AGENT_RANGE_SHA256
                ),
                sha256 = runtimeAttachAgentDigest
            )
            terminalState = when {
                agentUnloadRange.state == ArtRangeCheckState.READ_FAILED ||
                    runtimeAttachAgentRange.state == ArtRangeCheckState.READ_FAILED ->
                    ArtIdentityState.KNOWN_PROFILE_RANGE_READ_FAILED
                agentUnloadRange.state != ArtRangeCheckState.EXACT_MATCH ||
                    runtimeAttachAgentRange.state != ArtRangeCheckState.EXACT_MATCH ->
                    ArtIdentityState.KNOWN_PROFILE_RANGE_MISMATCH
                else -> ArtIdentityState.COMPLETE
            }
        }

        val evidence = identified.copy(
            finalPathSymlink = false,
            fileDeviceNonZero = true,
            fileIsRegular = true,
            fileSize = descriptorBefore.st_size,
            wholeFileSha256 = wholeSha256,
            gnuBuildId = buildId,
            knownRc2Profile = profile,
            agentUnloadRange = agentUnloadRange,
            runtimeAttachAgentRange = runtimeAttachAgentRange
        )
        val descriptorAfter = Os.fstat(descriptor)
        val pathAfter = Os.lstat(identity.path)
        if (OsConstants.S_ISLNK(pathAfter.st_mode)) {
            return evidence.copy(
                state = ArtIdentityState.MAPPED_PATH_SYMLINK,
                finalPathSymlink = true,
                fileMetadataStable = false
            )
        }
        if (
            !OsConstants.S_ISREG(pathAfter.st_mode) || pathAfter.st_dev == 0L ||
            !ExactFileMetadataPolicy.same(
                descriptorMetadataBefore,
                exactMetadata(descriptorAfter)
            ) ||
            !ExactFileMetadataPolicy.same(
                descriptorMetadataBefore,
                exactMetadata(pathAfter)
            )
        ) {
            return evidence.copy(
                state = ArtIdentityState.FILE_CHANGED_DURING_READ,
                fileMetadataStable = false
            )
        }

        val secondScan = try {
            readMapsSnapshot(firstScan.pageSizeBytes)
        } catch (_: SecurityException) {
            return evidence.copy(
                state = ArtIdentityState.MAPS_SECOND_READ_DENIED,
                fileMetadataStable = true,
                mapsSnapshotStable = false
            )
        } catch (_: FileNotFoundException) {
            return evidence.copy(
                state = ArtIdentityState.MAPS_SECOND_READ_DENIED,
                fileMetadataStable = true,
                mapsSnapshotStable = false
            )
        } catch (_: Throwable) {
            return evidence.copy(
                state = ArtIdentityState.MAPS_SECOND_READ_ERROR,
                fileMetadataStable = true,
                mapsSnapshotStable = false
            )
        }
        val secondEvidence = evidence.copy(
            secondMapsEntryCount = secondScan.entries.size,
            secondMalformedLibartEntryCount = secondScan.malformedCandidateCount,
            fileMetadataStable = true,
            mapsSnapshotStable = firstScan == secondScan
        )
        if (
            ArtMapAdmissionPolicy.rejection(secondScan) != null ||
            firstScan != secondScan
        ) {
            return secondEvidence.copy(state = ArtIdentityState.MAPS_CHANGED_DURING_READ)
        }
        return secondEvidence.copy(state = terminalState)
    }

    private fun readMapsSnapshot(pageSizeBytes: Long): ArtMapsScan =
        File(SELF_MAPS_PATH).bufferedReader().useLines { lines ->
            ArtMapsParser.parse(lines, pageSizeBytes)
        }

    private fun exactMetadata(stat: StructStat): ExactFileMetadata = ExactFileMetadata(
        device = stat.st_dev,
        inode = stat.st_ino,
        mode = stat.st_mode,
        size = stat.st_size,
        modifiedSeconds = stat.st_mtim.tv_sec,
        modifiedNanoseconds = stat.st_mtim.tv_nsec,
        changedSeconds = stat.st_ctim.tv_sec,
        changedNanoseconds = stat.st_ctim.tv_nsec
    )

    private fun descriptorSource(descriptor: FileDescriptor): PositionalReadSource =
        PositionalReadSource { offset, destination, byteCount ->
            if (
                offset < 0L || byteCount < 0 || byteCount > destination.size ||
                offset > Long.MAX_VALUE - byteCount.toLong()
            ) {
                false
            } else {
                var total = 0
                while (total < byteCount) {
                    val count = try {
                        Os.pread(
                            descriptor,
                            destination,
                            total,
                            byteCount - total,
                            offset + total
                        )
                    } catch (_: Throwable) {
                        return@PositionalReadSource false
                    }
                    if (count <= 0) return@PositionalReadSource false
                    total += count
                }
                true
            }
        }

    private fun hashWholeFile(source: PositionalReadSource, expectedSize: Long): String {
        require(expectedSize >= 0L)
        val digest = MessageDigest.getInstance("SHA-256")
        val buffer = ByteArray(64 * 1024)
        var offset = 0L
        while (offset < expectedSize) {
            val count = minOf(buffer.size.toLong(), expectedSize - offset).toInt()
            require(source.readFullyAt(offset, buffer, count))
            digest.update(buffer, 0, count)
            offset += count
        }
        buffer.fill(0)
        require(offset == expectedSize)
        return PackageCapabilityPolicy.normalizeDigest(digest.digest())
    }

    private fun hashRange(
        source: PositionalReadSource,
        fileSize: Long,
        offset: Long,
        size: Int
    ): String? {
        return try {
            if (
                offset < 0L || size <= 0 || offset > fileSize ||
                size.toLong() > fileSize - offset
            ) {
                null
            } else {
                val digest = MessageDigest.getInstance("SHA-256")
                val buffer = ByteArray(minOf(size, 64 * 1024))
                var position = offset
                var remaining = size
                while (remaining > 0) {
                    val count = minOf(buffer.size, remaining)
                    if (!source.readFullyAt(position, buffer, count)) return null
                    digest.update(buffer, 0, count)
                    position += count
                    remaining -= count
                }
                buffer.fill(0)
                PackageCapabilityPolicy.normalizeDigest(digest.digest())
            }
        } catch (_: Throwable) {
            null
        }
    }
}
