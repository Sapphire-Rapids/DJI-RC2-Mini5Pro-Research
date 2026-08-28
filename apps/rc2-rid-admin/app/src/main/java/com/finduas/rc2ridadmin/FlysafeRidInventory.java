package com.finduas.rc2ridadmin;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * Bounded, read-only V3/V4 FlySafe license inventory traversal and protobuf parser.
 *
 * <p>Public inventory views retain only the RID level and status bits. After a complete inventory,
 * an exact RID_UNLOCK ID may be retained only in a clearable in-memory record and reached through
 * a session-bound opaque handle. IDs never enter display or diagnostic strings. Descriptions,
 * group IDs, aircraft serials, user IDs, dates, and geometry are validated as wire fields where
 * applicable and immediately discarded.</p>
 */
final class FlysafeRidInventory {
    static final int MAX_LICENSES = 127;
    static final int MAX_PAGE_CALLS = MAX_LICENSES + 1;
    static final long MAX_QUERY_DURATION_MS = 90_000L;
    static final int RID_UNLOCK_TYPE_CODE = 6;

    private static final int PAGE_RESULT_RECORD = 0;
    private static final int PAGE_RESULT_END = 1;
    private static final int STATUS_INVALID_MASK = 0x01;
    private static final int STATUS_ENABLED_MASK = 0x02;
    private static final int STATUS_IN_VALID_DATE_MASK = 0x04;
    private static final int STATUS_UNKNOWN_MASK = 0xf8;

    private static final int MAX_GROUP_BYTES = 2_048;
    private static final int MAX_LICENSE_BYTES = 4_096;
    private static final int MAX_LICENSE_DATA_BYTES = 2_048;
    private static final int MAX_RID_BYTES = 256;
    private static final int MAX_STRING_BYTES = 512;
    private static final int MAX_SN_BYTES = 256;
    private static final int MAX_UNKNOWN_BYTES = 2_048;
    private static final int MAX_FIELDS_PER_MESSAGE = 64;
    private static final int MAX_FIELDS_PER_PARSE = 128;
    private static final int MAX_DEPTH = 3;

    private FlysafeRidInventory() {
    }

    interface Transport {
        Response fetch(byte[] payload) throws Exception;
    }

    static final class Response {
        final boolean callbackSuccess;
        final int ccode;
        final byte[] data;

        Response(boolean callbackSuccess, int ccode, byte[] data) {
            this.callbackSuccess = callbackSuccess;
            this.ccode = ccode;
            this.data = !callbackSuccess || data == null
                    ? null : Arrays.copyOf(data, data.length);
        }

        void clear() {
            if (data != null) {
                Arrays.fill(data, (byte) 0);
            }
        }
    }

    static final class RidLicense {
        private final long level;
        private final int rawStatus;

        RidLicense(long level, int rawStatus) {
            this.level = level;
            this.rawStatus = rawStatus & 0xff;
        }

        int getTypeCode() {
            return RID_UNLOCK_TYPE_CODE;
        }

        long getLevel() {
            return level;
        }

        boolean isEnabled() {
            return (rawStatus & STATUS_ENABLED_MASK) != 0;
        }

        boolean isValid() {
            return (rawStatus & STATUS_IN_VALID_DATE_MASK) != 0;
        }

        boolean isInvalid() {
            return (rawStatus & STATUS_INVALID_MASK) != 0;
        }

        int getUninterpretedStatusBits() {
            return rawStatus & STATUS_UNKNOWN_MASK;
        }

        int getRawStatus() {
            return rawStatus;
        }

        String levelDisplay() {
            if (level == 1L) {
                return "EUROPEAN(1)";
            }
            if (level == 2L) {
                return "CHINA(2)";
            }
            return "UNKNOWN(" + Long.toUnsignedString(level) + ")";
        }

        @Override
        public String toString() {
            return "RidLicense{level=" + levelDisplay()
                    + ", enabled=" + isEnabled()
                    + ", valid=" + isValid()
                    + ", invalid=" + isInvalid()
                    + ", uninterpretedStatusBits=0x"
                    + Integer.toHexString(getUninterpretedStatusBits()) + "}";
        }
    }

    static final class Result implements AutoCloseable {
        private final int declaredLicenseCount;
        private final int parsedLicenseCount;
        private final int pageCalls;
        private final List<RidLicense> ridLicenses;
        private final List<SensitiveRidRecord> sensitiveRidRecords;
        private final boolean controlHandleEligible;
        private final Object inventoryIdentity = new Object();
        private Object boundSessionMarker;
        private boolean sessionBound;
        private boolean handleIssued;
        private boolean closed;
        private OpaqueRidHandle issuedHandle;

        private Result(
                int declaredLicenseCount,
                int parsedLicenseCount,
                int pageCalls,
                List<RidLicense> ridLicenses,
                List<SensitiveRidRecord> sensitiveRidRecords,
                boolean controlHandleEligible) {
            this.declaredLicenseCount = declaredLicenseCount;
            this.parsedLicenseCount = parsedLicenseCount;
            this.pageCalls = pageCalls;
            this.ridLicenses = Collections.unmodifiableList(new ArrayList<>(ridLicenses));
            this.sensitiveRidRecords = new ArrayList<>(sensitiveRidRecords);
            this.controlHandleEligible = controlHandleEligible;
        }

        int getDeclaredLicenseCount() {
            return declaredLicenseCount;
        }

        int getParsedLicenseCount() {
            return parsedLicenseCount;
        }

        int getPageCalls() {
            return pageCalls;
        }

        List<RidLicense> getRidLicenses() {
            return ridLicenses;
        }

        boolean isControlHandleEligible() {
            return controlHandleEligible;
        }

        /**
         * Returns the sole eligible RID_UNLOCK record as an opaque, same-session capability.
         *
         * <p>Eligibility is deliberately narrow: known level 1/2, invalid bit clear, and
         * in-valid-date bit set. Zero or multiple matches are both terminal selection failures.
         * A result issues at most one handle, even if that handle is later closed.</p>
         */
        synchronized OpaqueRidHandle openSingleEligibleHandle(Object sessionMarker) {
            if (!controlHandleEligible) {
                throw new ProtocolException(
                        "public read-only inventory cannot issue a control handle");
            }
            requireUsableSession(sessionMarker);
            if (handleIssued) {
                throw new ProtocolException("RID_UNLOCK handle was already issued");
            }

            SensitiveRidRecord selected = null;
            int eligibleCount = 0;
            for (SensitiveRidRecord record : sensitiveRidRecords) {
                if (record.isEligible()) {
                    eligibleCount++;
                    selected = record;
                }
            }
            if (eligibleCount == 0) {
                throw new ProtocolException("no eligible RID_UNLOCK record");
            }
            if (eligibleCount != 1) {
                throw new ProtocolException("multiple eligible RID_UNLOCK records");
            }

            OpaqueRidHandle handle = selected.openHandle(
                    sessionMarker, inventoryIdentity);
            issuedHandle = handle;
            handleIssued = true;
            return handle;
        }

        private synchronized void verifyExactReadback(
                byte[] expectedLicenseIdLe,
                int expectedTypeCode,
                long expectedLevel,
                int baselineStatus,
                Object sessionMarker,
                Object sourceInventoryIdentity,
                boolean expectedEnabled) {
            if (sourceInventoryIdentity == inventoryIdentity) {
                throw new ProtocolException("readback must be a fresh complete inventory");
            }
            requireUsableSession(sessionMarker);

            SensitiveRidRecord match = null;
            for (SensitiveRidRecord record : sensitiveRidRecords) {
                if (record.matchesLicenseId(expectedLicenseIdLe)) {
                    if (match != null) {
                        throw new ProtocolException("readback contains duplicate target ID");
                    }
                    match = record;
                }
            }
            if (match == null) {
                throw new ProtocolException("readback target is absent");
            }
            if (match.typeCode != expectedTypeCode
                    || match.typeCode != RID_UNLOCK_TYPE_CODE) {
                throw new ProtocolException("readback target type changed");
            }
            if (match.level != expectedLevel) {
                throw new ProtocolException("readback target level changed");
            }
            if ((match.rawStatus & STATUS_INVALID_MASK)
                    != (baselineStatus & STATUS_INVALID_MASK)) {
                throw new ProtocolException("readback invalid bit changed");
            }
            if ((match.rawStatus & STATUS_IN_VALID_DATE_MASK)
                    != (baselineStatus & STATUS_IN_VALID_DATE_MASK)) {
                throw new ProtocolException("readback valid-date bit changed");
            }
            if ((match.rawStatus & STATUS_UNKNOWN_MASK)
                    != (baselineStatus & STATUS_UNKNOWN_MASK)) {
                throw new ProtocolException("readback unknown status bits changed");
            }
            boolean actualEnabled = (match.rawStatus & STATUS_ENABLED_MASK) != 0;
            if (actualEnabled != expectedEnabled) {
                throw new ProtocolException("readback enabled bit does not match target");
            }
        }

        private void requireUsableSession(Object sessionMarker) {
            if (sessionMarker == null) {
                throw new IllegalArgumentException("session token is required");
            }
            if (closed) {
                throw new IllegalStateException("inventory sensitive state was cleared");
            }
            if (!sessionBound) {
                boundSessionMarker = sessionMarker;
                sessionBound = true;
            } else if (boundSessionMarker != sessionMarker) {
                throw new ProtocolException("inventory session token changed");
            }
        }

        synchronized boolean isClosed() {
            return closed;
        }

        void clear() {
            close();
        }

        @Override
        public void close() {
            final OpaqueRidHandle handleToClose;
            final List<SensitiveRidRecord> recordsToClose;
            synchronized (this) {
                if (closed) {
                    return;
                }
                recordsToClose = new ArrayList<>(sensitiveRidRecords);
                handleToClose = issuedHandle;
                issuedHandle = null;
                sensitiveRidRecords.clear();
                boundSessionMarker = null;
                sessionBound = false;
                closed = true;
            }

            // Do not hold the Result monitor while acquiring a child-handle monitor. A readback
            // acquires those in the opposite direction, so closing outside avoids a lock cycle.
            if (handleToClose != null) {
                handleToClose.close();
            }
            for (SensitiveRidRecord record : recordsToClose) {
                record.close();
            }
        }

        String display() {
            return displayWithRoute("current-gate-session-bound");
        }

        String displayDirectReadonly() {
            return displayWithRoute("fixed-direct-readonly-02:04>12:04");
        }

        private String displayWithRoute(String routeDescription) {
            StringBuilder output = new StringBuilder();
            output.append("现代 FlySafe RID_UNLOCK 清单（只读）")
                    .append("\nroute=").append(routeDescription).append(" cmd=11/11")
                    .append("\nlicenses_count=").append(declaredLicenseCount)
                    .append(" parsed=").append(parsedLicenseCount)
                    .append(" page_calls=").append(pageCalls)
                    .append(" RID_UNLOCK=").append(ridLicenses.size());
            if (ridLicenses.isEmpty()) {
                output.append("\n未发现 LicenseData.rid(field 7) 记录。");
            } else {
                for (int index = 0; index < ridLicenses.size(); index++) {
                    RidLicense item = ridLicenses.get(index);
                    output.append("\nRID_UNLOCK #").append(index + 1)
                            .append(" level=").append(item.levelDisplay())
                            .append(" enabled(bit1)=").append(item.isEnabled() ? 1 : 0)
                            .append(" valid(bit2)=").append(item.isValid() ? 1 : 0)
                            .append(" invalid(bit0)=").append(item.isInvalid() ? 1 : 0);
                    if (item.getUninterpretedStatusBits() != 0) {
                        output.append(String.format(Locale.US,
                                " status_bits_3_7=0x%02X",
                                item.getUninterpretedStatusBits()));
                    }
                }
            }
            if (controlHandleEligible) {
                output.append("\n隐私：license ID 只在当前会话内存的不透明句柄中短暂保留；")
                        .append("不显示、不写日志、不持久化。");
            } else {
                output.append("\n隐私：本次为 public-read-only 模式；license ID 在重复校验后立即清除，")
                        .append("不保留控制句柄。");
            }
            output.append("SN、user ID、描述和原始 protobuf 不保留。")
                    .append("\n说明：清单状态本身不证明签名、区域适用性或真实空口 RID 已改变。");
            return output.toString();
        }

        @Override
        public String toString() {
            return "Result{declaredLicenseCount=" + declaredLicenseCount
                    + ", parsedLicenseCount=" + parsedLicenseCount
                    + ", pageCalls=" + pageCalls
                    + ", ridLicenses=" + ridLicenses + "}";
        }
    }

    /** Session-bound capability for the exact ID of one selected RID_UNLOCK record. */
    static final class OpaqueRidHandle implements AutoCloseable {
        private final int typeCode;
        private final long level;
        private final int baselineStatus;
        private final Object sourceInventoryIdentity;
        private byte[] licenseIdLe;
        private Object boundSessionMarker;
        private boolean closed;

        private OpaqueRidHandle(
                byte[] licenseIdLe,
                int typeCode,
                long level,
                int baselineStatus,
                Object boundSessionMarker,
                Object sourceInventoryIdentity) {
            this.licenseIdLe = Arrays.copyOf(licenseIdLe, licenseIdLe.length);
            this.typeCode = typeCode;
            this.level = level;
            this.baselineStatus = baselineStatus & 0xff;
            this.boundSessionMarker = boundSessionMarker;
            this.sourceInventoryIdentity = sourceInventoryIdentity;
        }

        synchronized int getTypeCode() {
            requireActive();
            return typeCode;
        }

        synchronized long getLevel() {
            requireActive();
            return level;
        }

        synchronized boolean wasEnabled() {
            requireActive();
            return (baselineStatus & STATUS_ENABLED_MASK) != 0;
        }

        /** Caller must clear the returned four-byte copy immediately after constructing a request. */
        synchronized byte[] copyLicenseIdLeForSet(Object sessionMarker) {
            requireSession(sessionMarker);
            return Arrays.copyOf(licenseIdLe, licenseIdLe.length);
        }

        synchronized boolean verifyReadback(
                Result fresh,
                Object sessionMarker,
                boolean expectedEnabled) {
            requireSession(sessionMarker);
            if (fresh == null) {
                throw new IllegalArgumentException("fresh inventory is required");
            }
            fresh.verifyExactReadback(
                    licenseIdLe,
                    typeCode,
                    level,
                    baselineStatus,
                    sessionMarker,
                    sourceInventoryIdentity,
                    expectedEnabled);
            return true;
        }

        synchronized boolean isClosed() {
            return closed;
        }

        synchronized void clear() {
            close();
        }

        @Override
        public synchronized void close() {
            if (closed) {
                return;
            }
            Arrays.fill(licenseIdLe, (byte) 0);
            licenseIdLe = new byte[0];
            boundSessionMarker = null;
            closed = true;
        }

        private void requireSession(Object sessionMarker) {
            requireActive();
            if (sessionMarker == null || boundSessionMarker != sessionMarker) {
                throw new ProtocolException("RID_UNLOCK handle session token changed");
            }
        }

        private void requireActive() {
            if (closed) {
                throw new IllegalStateException("RID_UNLOCK handle was cleared");
            }
        }

        @Override
        public synchronized String toString() {
            return "OpaqueRidHandle{type=RID_UNLOCK, sensitive=<redacted>}";
        }
    }

    static Result query(Transport transport) throws Exception {
        return query(transport, true);
    }

    /**
     * Runs the same strict inventory parser without retaining any exact license ID.
     *
     * <p>The returned result deliberately cannot issue an {@link OpaqueRidHandle}; this is the
     * only parser entry point used by the fixed-route direct-read-only UI.</p>
     */
    static Result queryReadOnly(Transport transport) throws Exception {
        return query(transport, false);
    }

    private static Result query(Transport transport, boolean retainControlState) throws Exception {
        if (transport == null) {
            throw new IllegalArgumentException("transport is required");
        }

        long queryStartedNanos = System.nanoTime();
        Response groupResponse = transport.fetch(startPayload());
        final GroupInfo group;
        try {
            requireWithinDeadline(queryStartedNanos);
            requireCallback(groupResponse, "group");
            if (groupResponse.ccode != PAGE_RESULT_RECORD) {
                throw new ProtocolException(
                        "group ccode=" + (groupResponse.ccode & 0xff) + " (expected 0)");
            }
            group = parseGroup(groupResponse.data);
        } finally {
            if (groupResponse != null) {
                groupResponse.clear();
            }
        }

        int parsedCount = 0;
        int pageCalls = 0;
        List<RidLicense> ridLicenses = new ArrayList<>();
        List<SensitiveRidRecord> sensitiveRidRecords = new ArrayList<>();
        byte[] duplicateSalt = new byte[16];
        new SecureRandom().nextBytes(duplicateSalt);
        Set<IdFingerprint> seenIds = new HashSet<>();
        boolean completed = false;
        try {
            for (int index = 0; index <= group.licensesCount; index++) {
                if (pageCalls >= MAX_PAGE_CALLS) {
                    throw new ProtocolException("page call limit exceeded");
                }
                requireWithinDeadline(queryStartedNanos);
                Response page = transport.fetch(pagePayload(index));
                try {
                    requireWithinDeadline(queryStartedNanos);
                    pageCalls++;
                    requireCallback(page, "page");

                    if (page.ccode == PAGE_RESULT_END) {
                        if (page.data != null && page.data.length != 0) {
                            throw new ProtocolException(
                                    "page " + index + " terminator has data length="
                                            + page.data.length);
                        }
                        if (index != group.licensesCount || parsedCount != group.licensesCount) {
                            throw new ProtocolException("terminator disagrees with licenses_count");
                        }
                        Result result = new Result(
                                group.licensesCount,
                                parsedCount,
                                pageCalls,
                                ridLicenses,
                                sensitiveRidRecords,
                                retainControlState);
                        completed = true;
                        return result;
                    }
                    if (page.ccode != PAGE_RESULT_RECORD) {
                        throw new ProtocolException(
                                "page " + index + " ccode=" + (page.ccode & 0xff)
                                        + " (expected record 0 or terminator 1)");
                    }
                    if (index >= group.licensesCount) {
                        throw new ProtocolException(
                                "record returned where terminator was required");
                    }

                    ParsedRecord record = parsePageRecord(page.data, duplicateSalt);
                    if (!seenIds.add(record.idFingerprint)) {
                        record.clear();
                        throw new ProtocolException("duplicate license ID");
                    }
                    parsedCount++;
                    if (record.ridLicense != null) {
                        SensitiveRidRecord sensitive = record.takeSensitiveRidRecord();
                        boolean retained = false;
                        try {
                            ridLicenses.add(record.ridLicense);
                            if (retainControlState) {
                                sensitiveRidRecords.add(sensitive);
                            } else {
                                sensitive.close();
                            }
                            retained = true;
                        } finally {
                            if (!retained) {
                                sensitive.close();
                            }
                        }
                    }
                } finally {
                    if (page != null) {
                        page.clear();
                    }
                }
            }
        } finally {
            for (IdFingerprint fingerprint : seenIds) {
                fingerprint.clear();
            }
            seenIds.clear();
            Arrays.fill(duplicateSalt, (byte) 0);
            if (!completed) {
                for (SensitiveRidRecord record : sensitiveRidRecords) {
                    record.close();
                }
                sensitiveRidRecords.clear();
            }
        }
        throw new ProtocolException("inventory ended without a terminator");
    }

    private static IdFingerprint fingerprint(long id, byte[] salt) {
        byte[] idBytes = new byte[] {
                (byte) id,
                (byte) (id >>> 8),
                (byte) (id >>> 16),
                (byte) (id >>> 24)
        };
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            digest.update("finduas:rid-inventory-duplicate:v1"
                    .getBytes(StandardCharsets.US_ASCII));
            digest.update(salt);
            digest.update(idBytes);
            return new IdFingerprint(digest.digest());
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 unavailable", exception);
        } finally {
            Arrays.fill(idBytes, (byte) 0);
        }
    }

    private static final class IdFingerprint {
        private final byte[] value;
        private final int hashCode;

        IdFingerprint(byte[] value) {
            this.value = value;
            this.hashCode = Arrays.hashCode(value);
        }

        void clear() {
            Arrays.fill(value, (byte) 0);
        }

        @Override
        public boolean equals(Object other) {
            return other instanceof IdFingerprint
                    && Arrays.equals(value, ((IdFingerprint) other).value);
        }

        @Override
        public int hashCode() {
            return hashCode;
        }

        @Override
        public String toString() {
            return "IdFingerprint{redacted}";
        }
    }

    /** Exact ID material retained only for a completed in-memory inventory. */
    private static final class SensitiveRidRecord implements AutoCloseable {
        private final int typeCode;
        private final long level;
        private final int rawStatus;
        private byte[] licenseIdLe;
        private boolean closed;

        private SensitiveRidRecord(
                byte[] licenseIdLe,
                long level,
                int rawStatus) {
            this.licenseIdLe = Arrays.copyOf(licenseIdLe, licenseIdLe.length);
            this.typeCode = RID_UNLOCK_TYPE_CODE;
            this.level = level;
            this.rawStatus = rawStatus & 0xff;
        }

        static SensitiveRidRecord create(long licenseId, long level, int rawStatus) {
            byte[] idLe = uint32LittleEndian(licenseId);
            try {
                return new SensitiveRidRecord(idLe, level, rawStatus);
            } finally {
                Arrays.fill(idLe, (byte) 0);
            }
        }

        synchronized boolean isEligible() {
            requireActive();
            return typeCode == RID_UNLOCK_TYPE_CODE
                    && (level == 1L || level == 2L)
                    && (rawStatus & STATUS_INVALID_MASK) == 0
                    && (rawStatus & STATUS_IN_VALID_DATE_MASK) != 0;
        }

        synchronized boolean matchesLicenseId(byte[] expectedLicenseIdLe) {
            requireActive();
            return expectedLicenseIdLe != null
                    && expectedLicenseIdLe.length == 4
                    && MessageDigest.isEqual(licenseIdLe, expectedLicenseIdLe);
        }

        synchronized OpaqueRidHandle openHandle(
                Object sessionMarker,
                Object inventoryIdentity) {
            requireActive();
            return new OpaqueRidHandle(
                    licenseIdLe,
                    typeCode,
                    level,
                    rawStatus,
                    sessionMarker,
                    inventoryIdentity);
        }

        @Override
        public synchronized void close() {
            if (closed) {
                return;
            }
            Arrays.fill(licenseIdLe, (byte) 0);
            licenseIdLe = new byte[0];
            closed = true;
        }

        private void requireActive() {
            if (closed) {
                throw new IllegalStateException("RID_UNLOCK inventory record was cleared");
            }
        }

        @Override
        public synchronized String toString() {
            return "SensitiveRidRecord{type=RID_UNLOCK, sensitive=<redacted>}";
        }
    }

    private static byte[] uint32LittleEndian(long value) {
        if (value <= 0L || value > 0xffff_ffffL) {
            throw new ProtocolException("license ID is outside nonzero uint32 range");
        }
        return new byte[] {
                (byte) value,
                (byte) (value >>> 8),
                (byte) (value >>> 16),
                (byte) (value >>> 24)
        };
    }

    private static void requireWithinDeadline(long startedNanos) {
        long elapsedNanos = System.nanoTime() - startedNanos;
        if (elapsedNanos < 0L
                || elapsedNanos > MAX_QUERY_DURATION_MS * 1_000_000L) {
            throw new ProtocolException("overall inventory query deadline exceeded");
        }
    }

    static byte[] startPayload() {
        return new byte[] {0x00, 0x01};
    }

    static byte[] pagePayload(int index) {
        if (index < 0 || index >= MAX_PAGE_CALLS) {
            throw new IllegalArgumentException("page index is outside bounded range");
        }
        return new byte[] {0x00, (byte) ((index << 1) & 0xff)};
    }

    private static void requireCallback(Response response, String phase) {
        if (response == null) {
            throw new ProtocolException(phase + " response is null");
        }
        if (!response.callbackSuccess) {
            // Deliberately do not propagate vendor descriptions or raw callback diagnostics.
            throw new ProtocolException(phase + " transport callback failed");
        }
    }

    static GroupInfo parseGroup(byte[] body) {
        requireTopLevel(body, MAX_GROUP_BYTES, "group protobuf");
        ParseBudget budget = new ParseBudget();
        ProtoReader reader = new ProtoReader(body, 0, body.length, budget, 0);
        boolean[] seen = new boolean[6];
        // Proto3 omits a scalar whose value is zero; absence is therefore the canonical empty
        // inventory count and is still confirmed by a ccode=1 page-0 terminator.
        int licensesCount = 0;

        ProtoField field;
        while ((field = reader.nextField()) != null) {
            switch (field.number) {
                case 1:
                    rejectDuplicate(seen, 1);
                    reader.readUInt32(field);
                    break;
                case 2:
                    rejectDuplicate(seen, 2);
                    reader.readUInt32(field);
                    break;
                case 3:
                    rejectDuplicate(seen, 3);
                    reader.readLengthDelimited(field, MAX_SN_BYTES);
                    break;
                case 4:
                    rejectDuplicate(seen, 4);
                    reader.readUInt64(field);
                    break;
                case 5:
                    rejectDuplicate(seen, 5);
                    long count = reader.readUInt32(field);
                    if (count > MAX_LICENSES) {
                        throw new ProtocolException("licenses_count exceeds bounded page limit");
                    }
                    licensesCount = (int) count;
                    break;
                default:
                    reader.skip(field);
                    break;
            }
        }
        return new GroupInfo(licensesCount);
    }

    static ParsedRecord parsePageRecord(byte[] framedBody) {
        return parsePageRecord(framedBody, null);
    }

    private static ParsedRecord parsePageRecord(byte[] framedBody, byte[] duplicateSalt) {
        if (framedBody == null || framedBody.length < 2) {
            throw new ProtocolException("page data must contain status and License protobuf");
        }
        if (framedBody.length > MAX_LICENSE_BYTES + 1) {
            throw new ProtocolException("page data exceeds size limit");
        }
        int status = framedBody[0] & 0xff;
        ParseBudget budget = new ParseBudget();
        ProtoReader reader = new ProtoReader(
                framedBody, 1, framedBody.length - 1, budget, 0);
        boolean[] seen = new boolean[8];
        boolean hasId = false;
        long licenseId = 0L;
        boolean hasData = false;
        RidLevel ridLevel = null;

        ProtoField field;
        while ((field = reader.nextField()) != null) {
            switch (field.number) {
                case 1:
                    rejectDuplicate(seen, 1);
                    licenseId = reader.readUInt32(field);
                    if (licenseId == 0L) {
                        throw new ProtocolException("license ID zero is not accepted");
                    }
                    hasId = true;
                    break;
                case 2:
                    rejectDuplicate(seen, 2);
                    validateUtf8(reader.readLengthDelimited(field, MAX_STRING_BYTES));
                    break;
                case 3:
                case 4:
                    rejectDuplicate(seen, field.number);
                    reader.readUInt32(field);
                    break;
                case 5:
                    rejectDuplicate(seen, 5);
                    reader.readBoolean(field);
                    break;
                case 6:
                    rejectDuplicate(seen, 6);
                    ByteSlice licenseData = reader.readLengthDelimited(
                            field, MAX_LICENSE_DATA_BYTES);
                    ridLevel = parseLicenseData(licenseData, budget, 0);
                    hasData = true;
                    break;
                case 7:
                    rejectDuplicate(seen, 7);
                    reader.readLengthDelimited(field, MAX_STRING_BYTES);
                    break;
                default:
                    reader.skip(field);
                    break;
            }
        }
        if (!hasId) {
            throw new ProtocolException("license ID is absent");
        }
        if (!hasData) {
            throw new ProtocolException("license data is absent");
        }

        RidLicense rid = ridLevel == null ? null : new RidLicense(ridLevel.level, status);
        IdFingerprint idFingerprint = duplicateSalt == null
                ? null : fingerprint(licenseId, duplicateSalt);
        SensitiveRidRecord sensitive = rid == null || duplicateSalt == null
                ? null
                : SensitiveRidRecord.create(licenseId, ridLevel.level, status);
        return new ParsedRecord(rid, idFingerprint, sensitive);
    }

    /** Returns a RID level only when the exact current oneof field 7 is present. */
    private static RidLevel parseLicenseData(
            ByteSlice data,
            ParseBudget budget,
            int parentDepth) {
        ProtoReader reader = data.reader(budget, parentDepth);
        Integer knownOneof = null;
        RidLevel ridLevel = null;
        ProtoField field;
        while ((field = reader.nextField()) != null) {
            if (field.number >= 1 && field.number <= 8) {
                if (knownOneof != null) {
                    throw new ProtocolException(
                            "multiple current LicenseData oneof fields are present");
                }
                knownOneof = field.number;
                ByteSlice payload = reader.readLengthDelimited(field, MAX_LICENSE_DATA_BYTES);
                if (field.number == 7) {
                    ridLevel = parseRidLevel(payload, budget, parentDepth + 1);
                }
            } else {
                reader.skip(field);
            }
        }
        return ridLevel;
    }

    private static RidLevel parseRidLevel(
            ByteSlice data,
            ParseBudget budget,
            int parentDepth) {
        if (data.length > MAX_RID_BYTES) {
            throw new ProtocolException("RID payload exceeds size limit");
        }
        ProtoReader reader = data.reader(budget, parentDepth);
        Long level = null;
        ProtoField field;
        while ((field = reader.nextField()) != null) {
            if (field.number == 1) {
                if (level != null) {
                    throw new ProtocolException("RID level occurs more than once");
                }
                level = reader.readUInt32(field);
            } else {
                reader.skip(field);
            }
        }
        if (level == null) {
            throw new ProtocolException("RID level is absent");
        }
        return new RidLevel(level);
    }

    private static void requireTopLevel(byte[] body, int maxLength, String name) {
        if (body == null || body.length == 0) {
            throw new ProtocolException(name + " is empty");
        }
        if (body.length > maxLength) {
            throw new ProtocolException(name + " exceeds size limit");
        }
    }

    private static void rejectDuplicate(boolean[] seen, int fieldNumber) {
        if (seen[fieldNumber]) {
            throw new ProtocolException("known singular field occurs more than once");
        }
        seen[fieldNumber] = true;
    }

    private static void validateUtf8(ByteSlice data) {
        int end = data.offset + data.length;
        int index = data.offset;
        while (index < end) {
            int first = data.bytes[index++] & 0xff;
            if (first <= 0x7f) {
                continue;
            }
            if (first >= 0xc2 && first <= 0xdf) {
                index = requireContinuation(data.bytes, index, end, 1);
                continue;
            }
            if (first >= 0xe0 && first <= 0xef) {
                if (index >= end) {
                    throw new ProtocolException("description is not valid UTF-8");
                }
                int second = data.bytes[index++] & 0xff;
                boolean validSecond = first == 0xe0
                        ? second >= 0xa0 && second <= 0xbf
                        : first == 0xed
                        ? second >= 0x80 && second <= 0x9f
                        : second >= 0x80 && second <= 0xbf;
                if (!validSecond) {
                    throw new ProtocolException("description is not valid UTF-8");
                }
                index = requireContinuation(data.bytes, index, end, 1);
                continue;
            }
            if (first >= 0xf0 && first <= 0xf4) {
                if (index >= end) {
                    throw new ProtocolException("description is not valid UTF-8");
                }
                int second = data.bytes[index++] & 0xff;
                boolean validSecond = first == 0xf0
                        ? second >= 0x90 && second <= 0xbf
                        : first == 0xf4
                        ? second >= 0x80 && second <= 0x8f
                        : second >= 0x80 && second <= 0xbf;
                if (!validSecond) {
                    throw new ProtocolException("description is not valid UTF-8");
                }
                index = requireContinuation(data.bytes, index, end, 2);
                continue;
            }
            throw new ProtocolException("description is not valid UTF-8");
        }
    }

    private static int requireContinuation(byte[] bytes, int index, int end, int count) {
        for (int offset = 0; offset < count; offset++) {
            if (index >= end) {
                throw new ProtocolException("description is not valid UTF-8");
            }
            int value = bytes[index++] & 0xff;
            if (value < 0x80 || value > 0xbf) {
                throw new ProtocolException("description is not valid UTF-8");
            }
        }
        return index;
    }

    static final class GroupInfo {
        final int licensesCount;

        GroupInfo(int licensesCount) {
            this.licensesCount = licensesCount;
        }

        @Override
        public String toString() {
            return "GroupInfo{licensesCount=" + licensesCount + "}";
        }
    }

    static final class ParsedRecord {
        final RidLicense ridLicense;
        final IdFingerprint idFingerprint;
        private SensitiveRidRecord sensitiveRidRecord;

        ParsedRecord(
                RidLicense ridLicense,
                IdFingerprint idFingerprint,
                SensitiveRidRecord sensitiveRidRecord) {
            this.ridLicense = ridLicense;
            this.idFingerprint = idFingerprint;
            this.sensitiveRidRecord = sensitiveRidRecord;
        }

        SensitiveRidRecord takeSensitiveRidRecord() {
            SensitiveRidRecord record = sensitiveRidRecord;
            sensitiveRidRecord = null;
            if (record == null) {
                throw new IllegalStateException("RID record has no retained opaque ID");
            }
            return record;
        }

        void clear() {
            if (idFingerprint != null) {
                idFingerprint.clear();
            }
            if (sensitiveRidRecord != null) {
                sensitiveRidRecord.close();
                sensitiveRidRecord = null;
            }
        }

        @Override
        public String toString() {
            return "ParsedRecord{ridLicense=" + ridLicense + "}";
        }
    }

    static final class ProtocolException extends IllegalArgumentException {
        ProtocolException(String message) {
            super(message);
        }
    }

    private static final class RidLevel {
        final long level;

        RidLevel(long level) {
            this.level = level;
        }
    }

    private static final class ParseBudget {
        private int remainingFields = MAX_FIELDS_PER_PARSE;

        void consumeField() {
            if (remainingFields == 0) {
                throw new ProtocolException("global protobuf field budget exhausted");
            }
            remainingFields--;
        }
    }

    private static final class ProtoField {
        final int number;
        final int wireType;

        ProtoField(int number, int wireType) {
            this.number = number;
            this.wireType = wireType;
        }
    }

    private static final class ByteSlice {
        final byte[] bytes;
        final int offset;
        final int length;

        ByteSlice(byte[] bytes, int offset, int length) {
            this.bytes = bytes;
            this.offset = offset;
            this.length = length;
        }

        ProtoReader reader(ParseBudget budget, int parentDepth) {
            return new ProtoReader(bytes, offset, length, budget, parentDepth + 1);
        }
    }

    /** Strict protobuf reader with local/global field, length, depth, and varint bounds. */
    private static final class ProtoReader {
        private final byte[] bytes;
        private final int end;
        private final ParseBudget budget;
        private int position;
        private int localFields;

        ProtoReader(
                byte[] bytes,
                int offset,
                int length,
                ParseBudget budget,
                int depth) {
            if (depth > MAX_DEPTH) {
                throw new ProtocolException("nested protobuf depth exceeded");
            }
            if (bytes == null || offset < 0 || length < 0
                    || offset > bytes.length - length) {
                throw new ProtocolException("invalid bounded protobuf slice");
            }
            this.bytes = bytes;
            this.position = offset;
            this.end = offset + length;
            this.budget = budget;
        }

        ProtoField nextField() {
            if (position == end) {
                return null;
            }
            localFields++;
            if (localFields > MAX_FIELDS_PER_MESSAGE) {
                throw new ProtocolException("protobuf message field limit exceeded");
            }
            budget.consumeField();

            long tag = readVarint64();
            int wireType = (int) (tag & 0x07L);
            long fieldNumber = tag >>> 3;
            if (fieldNumber == 0L || fieldNumber > 536_870_911L) {
                throw new ProtocolException("protobuf field number is outside range");
            }
            if (wireType > 5 || wireType == 3 || wireType == 4) {
                throw new ProtocolException("protobuf wire type is unsupported");
            }
            return new ProtoField((int) fieldNumber, wireType);
        }

        long readUInt32(ProtoField field) {
            requireWire(field, 0);
            long value = readVarint64();
            if ((value & 0xffffffff00000000L) != 0L) {
                throw new ProtocolException("uint32 exceeds 32 bits");
            }
            return value;
        }

        long readUInt64(ProtoField field) {
            requireWire(field, 0);
            return readVarint64();
        }

        boolean readBoolean(ProtoField field) {
            long value = readUInt64(field);
            if (value != 0L && value != 1L) {
                throw new ProtocolException("boolean is not canonical");
            }
            return value == 1L;
        }

        ByteSlice readLengthDelimited(ProtoField field, int maxLength) {
            requireWire(field, 2);
            long encodedLength = readVarint64();
            if (encodedLength < 0L || encodedLength > maxLength) {
                throw new ProtocolException("length-delimited field exceeds limit");
            }
            int length = (int) encodedLength;
            if (length > end - position) {
                throw new ProtocolException("length-delimited field is truncated");
            }
            ByteSlice result = new ByteSlice(bytes, position, length);
            position += length;
            return result;
        }

        void skip(ProtoField field) {
            switch (field.wireType) {
                case 0:
                    readVarint64();
                    return;
                case 1:
                    skipFixed(8);
                    return;
                case 2:
                    readLengthDelimited(field, MAX_UNKNOWN_BYTES);
                    return;
                case 5:
                    skipFixed(4);
                    return;
                default:
                    throw new ProtocolException("protobuf wire type cannot be skipped");
            }
        }

        private void skipFixed(int byteCount) {
            if (byteCount > end - position) {
                throw new ProtocolException("fixed-width field is truncated");
            }
            position += byteCount;
        }

        private long readVarint64() {
            long result = 0L;
            for (int index = 0; index < 10; index++) {
                if (position == end) {
                    throw new ProtocolException("varint is truncated");
                }
                int current = bytes[position++] & 0xff;
                if (index == 9 && (current & 0xfe) != 0) {
                    throw new ProtocolException("varint exceeds 64 bits");
                }
                result |= ((long) (current & 0x7f)) << (index * 7);
                if ((current & 0x80) == 0) {
                    if (index > 0 && (current & 0x7f) == 0) {
                        throw new ProtocolException("varint is not canonical");
                    }
                    return result;
                }
            }
            throw new ProtocolException("varint exceeds ten bytes");
        }

        private static void requireWire(ProtoField field, int expected) {
            if (field.wireType != expected) {
                throw new ProtocolException("known protobuf field has wrong wire type");
            }
        }
    }
}
