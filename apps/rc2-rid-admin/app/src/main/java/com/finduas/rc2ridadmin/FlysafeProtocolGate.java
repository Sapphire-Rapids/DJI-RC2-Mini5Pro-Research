package com.finduas.rc2ridadmin;

import java.util.Locale;

/**
 * Privacy-reduced state machine for the passive FlySafe support/version pushes.
 *
 * <p>The observer deliberately retains no payload bytes. The sender tuple is used only as a
 * same-window epoch proxy and is never rendered or persisted.</p>
 */
final class FlysafeProtocolGate {
    static final int CMD_SET_FLYC = 0x03;
    static final int CMD_AREA_INFO = 0x09;
    static final int CMD_WHITELIST_INFO = 0x42;

    enum Decision {
        GATE_UNOBSERVED,
        GATE_UNUSABLE,
        GATE_INVALIDATED,
        OBSERVED_UNSUPPORTED,
        UNKNOWN_VERSION,
        V2_NOT_IMPLEMENTED,
        MODERN_READY_CANDIDATE
    }

    static final class Snapshot {
        private final Decision decision;
        private final boolean areaSeen;
        private final boolean areaUsable;
        private final Integer version;
        private final boolean whitelistSeen;
        private final boolean whitelistUsable;
        private final Boolean supported;
        private final boolean sameSenderProxy;
        private final int acceptedCallbacks;
        private final int ignoredCallbacks;
        private final int malformedCallbacks;
        private final int failureCallbacks;
        private final long windowElapsedMs;
        private final String invalidReason;
        private final ReversedRoute reversedRoute;

        Snapshot(
                Decision decision,
                boolean areaSeen,
                boolean areaUsable,
                Integer version,
                boolean whitelistSeen,
                boolean whitelistUsable,
                Boolean supported,
                boolean sameSenderProxy,
                int acceptedCallbacks,
                int ignoredCallbacks,
                int malformedCallbacks,
                int failureCallbacks,
                long windowElapsedMs,
                String invalidReason,
                ReversedRoute reversedRoute) {
            this.decision = decision;
            this.areaSeen = areaSeen;
            this.areaUsable = areaUsable;
            this.version = version;
            this.whitelistSeen = whitelistSeen;
            this.whitelistUsable = whitelistUsable;
            this.supported = supported;
            this.sameSenderProxy = sameSenderProxy;
            this.acceptedCallbacks = acceptedCallbacks;
            this.ignoredCallbacks = ignoredCallbacks;
            this.malformedCallbacks = malformedCallbacks;
            this.failureCallbacks = failureCallbacks;
            this.windowElapsedMs = windowElapsedMs;
            this.invalidReason = invalidReason;
            this.reversedRoute = reversedRoute;
        }

        Decision getDecision() {
            return decision;
        }

        Integer getVersion() {
            return version;
        }

        Boolean getSupported() {
            return supported;
        }

        boolean allowsModernInventory() {
            return decision == Decision.MODERN_READY_CANDIDATE;
        }

        /**
         * Returns the strict reverse of the two observed push routes for this process only.
         * Endpoint values are deliberately absent from display(), toString(), and persistence.
         */
        ReversedRoute getReversedRoute() {
            return reversedRoute;
        }

        boolean hasProduct139ModernReverseRoute() {
            return allowsModernInventory()
                    && reversedRoute != null
                    && reversedRoute.isProduct139ModernFlysafe();
        }

        String display() {
            StringBuilder result = new StringBuilder();
            result.append("FlySafe gate：").append(decision.name());
            result.append("\n03/09 Area Info：seen=").append(areaSeen ? 1 : 0)
                    .append(" usable=").append(areaUsable ? 1 : 0)
                    .append(" version=").append(versionLabel(version));
            result.append("\n03/42 WhiteList Info：seen=").append(whitelistSeen ? 1 : 0)
                    .append(" usable=").append(whitelistUsable ? 1 : 0)
                    .append(" supported=").append(booleanLabel(supported));
            result.append("\n单链路窗口代理：")
                    .append(sameSenderProxy ? "同一完整 route" : "尚未闭合")
                    .append("；DJI device token：外部 Binder 不可见");
            result.append("\nproduct-139 动态反向 route：")
                    .append(hasProduct139ModernReverseRoute() ? "结构匹配" : "未形成/不匹配");
            result.append(String.format(Locale.US,
                    "\n窗口=%d ms；有效=%d；忽略=%d；畸形=%d；失败回调=%d",
                    windowElapsedMs,
                    acceptedCallbacks,
                    ignoredCallbacks,
                    malformedCallbacks,
                    failureCallbacks));
            if (invalidReason != null) {
                result.append("\n作废原因：").append(invalidReason);
            }
            result.append("\n本步骤只注册被动 listener，没有发送 03/09、03/42 或 11/11。");
            if (decision == Decision.MODERN_READY_CANDIDATE) {
                result.append("\n当前原子操作可立即进入现代 11/11 只读清单查询；该 gate 不跨进程复用。");
            } else if (decision == Decision.V2_NOT_IMPLEMENTED) {
                result.append("\n当前观察到 V2；A-025 的 V3/V4 查询结果不能用于判断清单为空。");
            } else if (decision == Decision.GATE_UNOBSERVED
                    || decision == Decision.GATE_UNUSABLE) {
                result.append("\n这只说明第三方 Binder listener 没有形成可用观察面，不等于飞控不支持。");
            }
            return result.toString();
        }

        private static String versionLabel(Integer value) {
            if (value == null) {
                return "UNOBSERVED";
            }
            if (value == 0) {
                return "V2(0)";
            }
            if (value == 1) {
                return "V3(1)";
            }
            if (value == 2) {
                return "V4(2)";
            }
            return "UNKNOWN(255)";
        }

        private static String booleanLabel(Boolean value) {
            return value == null ? "UNOBSERVED" : (value ? "true" : "false");
        }
    }

    /** Privacy-redacted, immutable request route derived by reversing a passive push route. */
    static final class ReversedRoute {
        private final int senderType;
        private final int senderId;
        private final int receiverType;
        private final int receiverId;

        ReversedRoute(int senderType, int senderId, int receiverType, int receiverId) {
            this.senderType = senderType;
            this.senderId = senderId;
            this.receiverType = receiverType;
            this.receiverId = receiverId;
        }

        int getSenderType() {
            return senderType;
        }

        int getSenderId() {
            return senderId;
        }

        int getReceiverType() {
            return receiverType;
        }

        int getReceiverId() {
            return receiverId;
        }

        boolean isProduct139ModernFlysafe() {
            // Product 139's final FlySafe receiver is type 18/id 4. The app sender index is
            // runtime-owned and therefore comes from the actual push receiver rather than a
            // hard-coded assumption.
            return senderType == 2
                    && senderId >= 0 && senderId <= 7
                    && receiverType == 18
                    && receiverId == 4;
        }

        @Override
        public String toString() {
            return "ReversedRoute{redacted}";
        }
    }

    private boolean closed;
    private boolean invalidated;
    private String invalidReason;
    private boolean areaSeen;
    private boolean areaUsable;
    private Integer version;
    private boolean whitelistSeen;
    private boolean whitelistUsable;
    private Boolean supported;
    private Integer senderType;
    private Integer senderId;
    private Integer receiverType;
    private Integer receiverId;
    private int acceptedCallbacks;
    private int ignoredCallbacks;
    private int malformedCallbacks;
    private int failureCallbacks;

    synchronized void observe(
            int actualSenderType,
            int actualSenderId,
            int actualReceiverType,
            int actualReceiverId,
            int cmdSet,
            int cmdId,
            byte[] payload) {
        if (closed) {
            ignoredCallbacks++;
            return;
        }
        if (cmdSet != CMD_SET_FLYC || (cmdId != CMD_AREA_INFO
                && cmdId != CMD_WHITELIST_INFO)) {
            ignoredCallbacks++;
            return;
        }

        // A recognized gate command is part of the admission window even when its payload is
        // unusable. Bind/compare the complete route before parsing so a malformed callback on a
        // different route cannot be ignored and later washed out by a valid callback.
        if (!acceptRoute(actualSenderType, actualSenderId,
                actualReceiverType, actualReceiverId)) {
            return;
        }

        if (cmdId == CMD_AREA_INFO) {
            areaSeen = true;
            if (payload == null || payload.length < 8) {
                invalidate("03/09 payload 长度不足");
                return;
            }
            int raw16 = (payload[3] & 0xff) | ((payload[4] & 0xff) << 8);
            int top2 = raw16 >>> 14;
            int candidate = top2 == 3 ? 255 : top2;
            if (version != null && version != candidate) {
                invalidate("03/09 version 在同一窗口内发生冲突");
                return;
            }
            version = candidate;
            areaUsable = true;
            acceptedCallbacks++;
            return;
        }

        whitelistSeen = true;
        if (payload == null || payload.length == 0) {
            invalidate("03/42 payload 为空");
            return;
        }
        int b0 = payload[0] & 0xff;
        final Boolean candidate;
        if (b0 >= 10) {
            candidate = b0 != 255;
        } else if (payload.length >= 28) {
            candidate = payload[3] != 0;
        } else {
            invalidate("03/42 legacy payload 长度不足");
            return;
        }
        if (supported != null && !supported.equals(candidate)) {
            invalidate("03/42 support 在同一窗口内发生冲突");
            return;
        }
        supported = candidate;
        whitelistUsable = true;
        acceptedCallbacks++;
    }

    synchronized void recordMalformedCallback() {
        if (!closed) {
            malformedCallbacks++;
            invalidate("监听窗口收到无法验证的 callback/Pack");
        }
    }

    synchronized void recordFailureCallback() {
        if (!closed) {
            failureCallbacks++;
            invalidate("监听窗口收到 DJI failure callback");
        }
    }

    synchronized boolean hasTerminalGateResult() {
        return invalidated || (areaUsable && whitelistUsable
                && version != null && supported != null);
    }

    synchronized Snapshot close(long windowElapsedMs) {
        closed = true;
        Decision decision = decide();
        ReversedRoute reversedRoute = decision == Decision.MODERN_READY_CANDIDATE
                && senderType != null && senderId != null
                && receiverType != null && receiverId != null
                ? new ReversedRoute(receiverType, receiverId, senderType, senderId)
                : null;
        return new Snapshot(
                decision,
                areaSeen,
                areaUsable,
                version,
                whitelistSeen,
                whitelistUsable,
                supported,
                senderType != null && areaUsable && whitelistUsable && !invalidated,
                acceptedCallbacks,
                ignoredCallbacks,
                malformedCallbacks,
                failureCallbacks,
                windowElapsedMs,
                invalidReason,
                reversedRoute);
    }

    private boolean acceptRoute(
            int actualSenderType,
            int actualSenderId,
            int actualReceiverType,
            int actualReceiverId) {
        if (invalidated) {
            return false;
        }
        if (senderType == null) {
            senderType = actualSenderType;
            senderId = actualSenderId;
            receiverType = actualReceiverType;
            receiverId = actualReceiverId;
            return true;
        }
        if (senderType != actualSenderType || senderId != actualSenderId
                || receiverType != actualReceiverType || receiverId != actualReceiverId) {
            invalidate("03/09 与 03/42 的实际完整 route 不一致");
            return false;
        }
        return true;
    }

    private void invalidate(String reason) {
        invalidated = true;
        invalidReason = reason;
    }

    private Decision decide() {
        if (invalidated) {
            return Decision.GATE_INVALIDATED;
        }
        if (!areaSeen && !whitelistSeen) {
            return Decision.GATE_UNOBSERVED;
        }
        if (!areaUsable || !whitelistUsable || version == null || supported == null) {
            return Decision.GATE_UNUSABLE;
        }
        if (!supported) {
            return Decision.OBSERVED_UNSUPPORTED;
        }
        if (version == 255) {
            return Decision.UNKNOWN_VERSION;
        }
        if (version == 0) {
            return Decision.V2_NOT_IMPLEMENTED;
        }
        if (version == 1 || version == 2) {
            return Decision.MODERN_READY_CANDIDATE;
        }
        return Decision.UNKNOWN_VERSION;
    }
}
