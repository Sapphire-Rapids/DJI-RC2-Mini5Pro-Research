package com.finduas.research.flysafe.wire

private class ZeroizableBuffer(
    ownedBytes: ByteArray,
) : AutoCloseable {
    private val bytes: ByteArray = ownedBytes
    private var closed: Boolean = false

    val size: Int get() = bytes.size

    val isClosed: Boolean
        @Synchronized get() = closed

    @Synchronized
    fun <T> useCopy(block: (ByteArray) -> T): T {
        check(!closed) { "sensitive buffer is closed" }
        val copy = bytes.copyOf()
        return try {
            block(copy)
        } finally {
            copy.fill(0)
        }
    }

    @Synchronized
    fun copyInto(destination: ByteArray, destinationOffset: Int) {
        check(!closed) { "sensitive buffer is closed" }
        require(destinationOffset >= 0 && destinationOffset + bytes.size <= destination.size) {
            "destination cannot hold the sensitive value"
        }
        bytes.copyInto(destination, destinationOffset)
    }

    @Synchronized
    override fun close() {
        if (!closed) {
            bytes.fill(0)
            closed = true
        }
    }
}

/** Four-byte little-endian u32 license identifier with deterministic memory cleanup. */
internal class SensitiveLicenseId private constructor(
    ownedLittleEndian: ByteArray,
) : AutoCloseable {
    private val buffer = ZeroizableBuffer(ownedLittleEndian)

    val isClosed: Boolean get() = buffer.isClosed

    internal fun copyInto(destination: ByteArray, destinationOffset: Int) {
        buffer.copyInto(destination, destinationOffset)
    }

    override fun close() = buffer.close()

    override fun toString(): String = "SensitiveLicenseId(<redacted>)"

    companion object {
        const val ENCODED_SIZE: Int = 4

        /**
         * Takes ownership by copying exactly four LE bytes and always zeroes the caller's array,
         * including when validation fails.
         */
        fun consumeLittleEndian(source: ByteArray): SensitiveLicenseId {
            val owned = try {
                if (source.size != ENCODED_SIZE) {
                    throw PayloadBoundsException("license ID must be exactly four little-endian bytes")
                }
                source.copyOf()
            } finally {
                source.fill(0)
            }
            return try {
                SensitiveLicenseId(owned)
            } catch (error: Throwable) {
                owned.fill(0)
                throw error
            }
        }
    }
}

/** A SetEnable application payload. It never renders its bytes and must be closed after use. */
internal class SensitiveApplicationPayload internal constructor(
    ownedBytes: ByteArray,
) : AutoCloseable {
    private val buffer = ZeroizableBuffer(ownedBytes)

    val size: Int get() = buffer.size
    val isClosed: Boolean get() = buffer.isClosed

    fun <T> useBytes(block: (ByteArray) -> T): T = buffer.useCopy(block)

    override fun close() = buffer.close()

    override fun toString(): String = "SensitiveApplicationPayload(size=$size, bytes=<redacted>)"
}

/** Opaque sensitive query response material, such as license records or protobuf bytes. */
internal class SensitiveAckPayload internal constructor(
    ownedBytes: ByteArray,
) : AutoCloseable {
    private val buffer = ZeroizableBuffer(ownedBytes)

    val size: Int get() = buffer.size
    val isClosed: Boolean get() = buffer.isClosed

    fun <T> useBytes(block: (ByteArray) -> T): T = buffer.useCopy(block)

    override fun close() = buffer.close()

    override fun toString(): String = "SensitiveAckPayload(size=$size, bytes=<redacted>)"
}
