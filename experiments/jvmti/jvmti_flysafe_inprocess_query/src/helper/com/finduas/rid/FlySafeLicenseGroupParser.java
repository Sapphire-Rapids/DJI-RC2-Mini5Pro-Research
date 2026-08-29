package com.finduas.rid;

/** Minimal parser for the FlightRestrict v3 LicenseGroupModel returned by DJI Fly. */
public final class FlySafeLicenseGroupParser {
    private static final int MAX_RECORDS = 128;

    private FlySafeLicenseGroupParser() {}

    public static Result parse(byte[] body) {
        if (body == null || body.length == 0) {
            throw new ParseException("empty license group");
        }

        Reader reader = new Reader(body, 0, body.length);
        int declaredCount = -1;
        boolean groupInfoSeen = false;
        int recordCount = 0;
        int ridCount = 0;
        LicenseRecord uniqueRid = null;

        while (!reader.exhausted()) {
            int tag = reader.readTag();
            int field = tag >>> 3;
            int wire = tag & 7;
            if (field == 2) {
                if (groupInfoSeen) {
                    throw new ParseException("duplicate group_info");
                }
                groupInfoSeen = true;
                Reader groupInfo = reader.readMessage(wire);
                int groupCount = 0;
                while (!groupInfo.exhausted()) {
                    int infoTag = groupInfo.readTag();
                    if ((infoTag >>> 3) == 5) {
                        groupCount = groupInfo.readUInt32(infoTag & 7);
                    } else {
                        groupInfo.skip(infoTag & 7);
                    }
                }
                declaredCount = groupCount;
            } else if (field == 4) {
                if (recordCount == MAX_RECORDS) {
                    throw new ParseException("too many license records");
                }
                LicenseRecord record = parseModel(reader.readMessage(wire));
                recordCount++;
                if (record.rid) {
                    ridCount++;
                    uniqueRid = ridCount == 1 ? record : null;
                }
            } else {
                reader.skip(wire);
            }
        }

        if (!groupInfoSeen) {
            throw new ParseException("group_info is absent");
        }
        if (declaredCount != recordCount) {
            throw new ParseException("licenses_count mismatch");
        }
        return new Result(declaredCount, recordCount, ridCount, uniqueRid);
    }

    private static LicenseRecord parseModel(Reader reader) {
        LicenseRecord license = null;
        Status status = null;
        while (!reader.exhausted()) {
            int tag = reader.readTag();
            int field = tag >>> 3;
            int wire = tag & 7;
            if (field == 1) {
                license = parseLicense(reader.readMessage(wire));
            } else if (field == 2) {
                status = parseStatus(reader.readMessage(wire));
            } else {
                reader.skip(wire);
            }
        }
        if (license == null) {
            throw new ParseException("license model has no license");
        }
        if (status == null) {
            throw new ParseException("license model has no status");
        }
        license.enabled = status.enabled;
        license.inValidDate = status.inValidDate;
        license.invalid = status.invalid;
        return license;
    }

    private static LicenseRecord parseLicense(Reader reader) {
        int id = 0;
        boolean idSeen = false;
        boolean rid = false;
        int level = 0;
        while (!reader.exhausted()) {
            int tag = reader.readTag();
            int field = tag >>> 3;
            int wire = tag & 7;
            if (field == 1) {
                id = reader.readUInt32(wire);
                idSeen = true;
            } else if (field == 6) {
                Reader data = reader.readMessage(wire);
                while (!data.exhausted()) {
                    int dataTag = data.readTag();
                    int dataField = dataTag >>> 3;
                    int dataWire = dataTag & 7;
                    if (dataField == 7) {
                        if (rid) {
                            throw new ParseException("duplicate RID data");
                        }
                        rid = true;
                        level = parseRid(data.readMessage(dataWire));
                    } else {
                        data.skip(dataWire);
                    }
                }
            } else {
                reader.skip(wire);
            }
        }
        if (!idSeen || id == 0) {
            throw new ParseException("license ID is absent or zero");
        }
        return new LicenseRecord(id, rid, level);
    }

    private static int parseRid(Reader reader) {
        int level = 0;
        boolean seen = false;
        while (!reader.exhausted()) {
            int tag = reader.readTag();
            if ((tag >>> 3) == 1) {
                if (seen) {
                    throw new ParseException("duplicate RID level");
                }
                level = reader.readUInt32(tag & 7);
                seen = true;
            } else {
                reader.skip(tag & 7);
            }
        }
        if (!seen) {
            throw new ParseException("RID level is absent");
        }
        return level;
    }

    private static Status parseStatus(Reader reader) {
        Status status = new Status();
        while (!reader.exhausted()) {
            int tag = reader.readTag();
            int field = tag >>> 3;
            int wire = tag & 7;
            if (field == 1) {
                status.enabled = reader.readBoolean(wire);
            } else if (field == 2) {
                status.inValidDate = reader.readBoolean(wire);
            } else if (field == 3) {
                status.invalid = reader.readBoolean(wire);
            } else {
                reader.skip(wire);
            }
        }
        return status;
    }

    public static final class Result {
        public final int declaredCount;
        public final int recordCount;
        public final int ridCount;
        public final int ridLicenseId;
        public final int ridLevel;
        public final boolean enabled;
        public final boolean inValidDate;
        public final boolean invalid;

        private Result(int declaredCount, int recordCount, int ridCount, LicenseRecord uniqueRid) {
            this.declaredCount = declaredCount;
            this.recordCount = recordCount;
            this.ridCount = ridCount;
            this.ridLicenseId = uniqueRid == null ? 0 : uniqueRid.id;
            this.ridLevel = uniqueRid == null ? 0 : uniqueRid.level;
            this.enabled = uniqueRid != null && uniqueRid.enabled;
            this.inValidDate = uniqueRid != null && uniqueRid.inValidDate;
            this.invalid = uniqueRid != null && uniqueRid.invalid;
        }
    }

    public static final class ParseException extends IllegalArgumentException {
        ParseException(String message) {
            super(message);
        }
    }

    private static final class LicenseRecord {
        final int id;
        final boolean rid;
        final int level;
        boolean enabled;
        boolean inValidDate;
        boolean invalid;

        LicenseRecord(int id, boolean rid, int level) {
            this.id = id;
            this.rid = rid;
            this.level = level;
        }
    }

    private static final class Status {
        boolean enabled;
        boolean inValidDate;
        boolean invalid;
    }

    private static final class Reader {
        private final byte[] bytes;
        private int position;
        private final int end;

        Reader(byte[] bytes, int offset, int length) {
            if (offset < 0 || length < 0 || offset > bytes.length - length) {
                throw new ParseException("invalid message bounds");
            }
            this.bytes = bytes;
            this.position = offset;
            this.end = offset + length;
        }

        boolean exhausted() {
            return position == end;
        }

        int readTag() {
            long value = readVarint();
            int field = (int) (value >>> 3);
            int wire = (int) value & 7;
            if (field == 0 || wire == 3 || wire == 4 || wire > 5) {
                throw new ParseException("invalid protobuf tag");
            }
            return (field << 3) | wire;
        }

        int readUInt32(int wire) {
            requireWire(wire, 0);
            long value = readVarint();
            if ((value & 0xffffffff00000000L) != 0) {
                throw new ParseException("uint32 overflow");
            }
            return (int) value;
        }

        boolean readBoolean(int wire) {
            int value = readUInt32(wire);
            if (value != 0 && value != 1) {
                throw new ParseException("invalid Boolean");
            }
            return value == 1;
        }

        Reader readMessage(int wire) {
            requireWire(wire, 2);
            int length = readLength();
            Reader child = new Reader(bytes, position, length);
            position += length;
            return child;
        }

        void skip(int wire) {
            if (wire == 0) {
                readVarint();
            } else if (wire == 1) {
                advance(8);
            } else if (wire == 2) {
                advance(readLength());
            } else if (wire == 5) {
                advance(4);
            } else {
                throw new ParseException("unsupported wire type");
            }
        }

        private int readLength() {
            long length = readVarint();
            if (length > Integer.MAX_VALUE || length > end - position) {
                throw new ParseException("truncated length-delimited field");
            }
            return (int) length;
        }

        private long readVarint() {
            long value = 0;
            for (int shift = 0; shift < 64; shift += 7) {
                if (position == end) {
                    throw new ParseException("truncated varint");
                }
                int current = bytes[position++] & 0xff;
                if (shift == 63 && (current & 0xfe) != 0) {
                    throw new ParseException("varint overflow");
                }
                value |= (long) (current & 0x7f) << shift;
                if ((current & 0x80) == 0) {
                    return value;
                }
            }
            throw new ParseException("varint overflow");
        }

        private void advance(int count) {
            if (count < 0 || count > end - position) {
                throw new ParseException("truncated field");
            }
            position += count;
        }

        private void requireWire(int actual, int expected) {
            if (actual != expected) {
                throw new ParseException("wrong wire type");
            }
        }
    }
}
