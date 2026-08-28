package com.finduas.ridinventory.internal

internal enum class ProtoFailure {
    EMPTY_INPUT,
    MESSAGE_TOO_LARGE,
    FIELD_LIMIT,
    DEPTH_LIMIT,
    INVALID_TAG,
    WRONG_WIRE_TYPE,
    UNSUPPORTED_WIRE_TYPE,
    TRUNCATED,
    VARINT_OVERFLOW,
    NON_CANONICAL_VARINT,
    LENGTH_LIMIT,
    DUPLICATE_CRITICAL_FIELD,
    ONEOF_CONFLICT,
    INVALID_UTF8,
    INVALID_BOOLEAN,
    MISSING_CRITICAL_FIELD,
    VALUE_OUT_OF_RANGE,
}

internal class StrictProtoException(
    internal val failure: ProtoFailure,
    detail: String,
) : IllegalArgumentException("$failure: $detail")

internal object ProtoLimits {
    const val MAX_GROUP_BYTES = 2_048
    const val MAX_LICENSE_BYTES = 4_096
    const val MAX_LICENSE_DATA_BYTES = 2_048
    const val MAX_RID_BYTES = 256
    const val MAX_STRING_BYTES = 512
    const val MAX_SN_BYTES = 256
    const val MAX_UNKNOWN_BYTES = 2_048
    const val MAX_FIELDS_PER_MESSAGE = 64
    const val MAX_FIELDS_PER_PARSE = 128
    const val MAX_DEPTH = 3
    const val MAX_LICENSES = 127
}

internal class ParseBudget(
    private var remainingFields: Int = ProtoLimits.MAX_FIELDS_PER_PARSE,
) {
    fun consumeField() {
        if (remainingFields == 0) {
            throw StrictProtoException(ProtoFailure.FIELD_LIMIT, "global field budget exhausted")
        }
        remainingFields -= 1
    }
}

internal data class ProtoField(
    val number: Int,
    val wireType: Int,
)

/** A non-copying, short-lived view used only while a parent parser is on the stack. */
internal class ByteSlice(
    internal val bytes: ByteArray,
    internal val offset: Int,
    internal val length: Int,
) {
    fun reader(budget: ParseBudget, parentDepth: Int): StrictProtoReader =
        StrictProtoReader(bytes, offset, length, budget, parentDepth + 1)

    fun updateDigest(digest: java.security.MessageDigest) {
        digest.update(bytes, offset, length)
    }
}

internal class StrictProtoReader(
    private val bytes: ByteArray,
    offset: Int,
    length: Int,
    private val budget: ParseBudget,
    private val depth: Int = 0,
) {
    private var position = offset
    private val end: Int
    private var localFields = 0

    init {
        if (depth > ProtoLimits.MAX_DEPTH) {
            throw StrictProtoException(ProtoFailure.DEPTH_LIMIT, "nested message depth exceeded")
        }
        if (offset < 0 || length < 0 || offset > bytes.size - length) {
            throw StrictProtoException(ProtoFailure.TRUNCATED, "invalid bounded input slice")
        }
        end = offset + length
    }

    fun nextField(): ProtoField? {
        if (position == end) return null
        localFields += 1
        if (localFields > ProtoLimits.MAX_FIELDS_PER_MESSAGE) {
            throw StrictProtoException(ProtoFailure.FIELD_LIMIT, "message field limit exceeded")
        }
        budget.consumeField()

        val tag = readVarint64()
        val wireType = (tag and 0x07uL).toInt()
        val fieldNumber = tag shr 3
        if (fieldNumber == 0uL || fieldNumber > 536_870_911uL) {
            throw StrictProtoException(ProtoFailure.INVALID_TAG, "field number outside protobuf range")
        }
        if (wireType !in 0..5) {
            throw StrictProtoException(ProtoFailure.INVALID_TAG, "invalid protobuf wire type")
        }
        if (wireType == 3 || wireType == 4) {
            throw StrictProtoException(ProtoFailure.UNSUPPORTED_WIRE_TYPE, "groups are not accepted")
        }
        return ProtoField(fieldNumber.toInt(), wireType)
    }

    fun readUInt32(field: ProtoField): UInt {
        requireWire(field, 0)
        val value = readVarint64()
        if (value > UInt.MAX_VALUE.toULong()) {
            throw StrictProtoException(ProtoFailure.VALUE_OUT_OF_RANGE, "uint32 exceeds 32 bits")
        }
        return value.toUInt()
    }

    fun readUInt64(field: ProtoField): ULong {
        requireWire(field, 0)
        return readVarint64()
    }

    fun readBoolean(field: ProtoField): Boolean {
        val value = readUInt64(field)
        if (value > 1uL) {
            throw StrictProtoException(ProtoFailure.INVALID_BOOLEAN, "boolean must be zero or one")
        }
        return value == 1uL
    }

    fun readLengthDelimited(field: ProtoField, maxLength: Int): ByteSlice {
        requireWire(field, 2)
        val encodedLength = readVarint64()
        if (encodedLength > maxLength.toULong()) {
            throw StrictProtoException(ProtoFailure.LENGTH_LIMIT, "length-delimited field exceeds cap")
        }
        val length = encodedLength.toInt()
        if (length > end - position) {
            throw StrictProtoException(ProtoFailure.TRUNCATED, "length-delimited field is truncated")
        }
        val result = ByteSlice(bytes, position, length)
        position += length
        return result
    }

    fun skip(field: ProtoField) {
        when (field.wireType) {
            0 -> readVarint64()
            1 -> skipFixed(8)
            2 -> readLengthDelimited(field, ProtoLimits.MAX_UNKNOWN_BYTES)
            5 -> skipFixed(4)
            else -> throw StrictProtoException(
                ProtoFailure.UNSUPPORTED_WIRE_TYPE,
                "wire type is not accepted",
            )
        }
    }

    private fun skipFixed(byteCount: Int) {
        if (byteCount > end - position) {
            throw StrictProtoException(ProtoFailure.TRUNCATED, "fixed-width field is truncated")
        }
        position += byteCount
    }

    private fun readVarint64(): ULong {
        var result = 0uL
        for (index in 0 until 10) {
            if (position == end) {
                throw StrictProtoException(ProtoFailure.TRUNCATED, "varint is truncated")
            }
            val current = bytes[position++].toInt() and 0xff
            if (index == 9 && (current and 0xfe) != 0) {
                throw StrictProtoException(ProtoFailure.VARINT_OVERFLOW, "varint exceeds 64 bits")
            }
            result = result or ((current and 0x7f).toULong() shl (index * 7))
            if ((current and 0x80) == 0) {
                if (index > 0 && (current and 0x7f) == 0) {
                    throw StrictProtoException(
                        ProtoFailure.NON_CANONICAL_VARINT,
                        "varint uses a longer encoding than required",
                    )
                }
                return result
            }
        }
        throw StrictProtoException(ProtoFailure.VARINT_OVERFLOW, "varint exceeds ten bytes")
    }

    private fun requireWire(field: ProtoField, expected: Int) {
        if (field.wireType != expected) {
            throw StrictProtoException(
                ProtoFailure.WRONG_WIRE_TYPE,
                "known field ${field.number} has wire ${field.wireType}, expected $expected",
            )
        }
    }
}
