package com.finduas.rc2ridadmin;

import java.util.Arrays;

/** Retained EID/OPID transaction logic; this build admits neither device write lane. */
final class IdentityControlTransaction {
    enum Field { EID, OPERATOR_ID }

    interface DeviceState {
        byte[] read() throws Exception;
        /** Returns only after a canonical successful application ACK. */
        void write(byte[] state) throws Exception;
    }

    private final Field field;
    private byte[] baseline;
    private byte[] attemptedState;
    private boolean restoreRequired;
    private boolean baselineInvalid;

    IdentityControlTransaction(Field field) {
        this.field = field;
    }

    static boolean writesAdmitted() {
        return false;
    }

    static void requireWriteAdmission() {
        if (!writesAdmitted()) {
            throw new IllegalStateException(
                    "NOT_ADMITTED：EID/OPID 写入未准入；只读结果不能解锁写入。");
        }
    }

    void captureBaseline(byte[] value) {
        if (baseline == null && value != null) {
            baseline = value.clone();
        }
    }

    byte[] baseline() {
        return baseline == null ? null : baseline.clone();
    }

    boolean isRestoreRequired() {
        return restoreRequired;
    }

    /** Called only behind admission; DeviceState is a fake in host tests, never a new sender. */
    String transition(byte[] desired, DeviceState device) throws Exception {
        requireValidSession();
        if (restoreRequired) {
            throw new IllegalStateException("RESTORE_REQUIRED：先确认恢复本次基线，禁止继续变更。");
        }
        requireRestorable(desired);
        if (baseline != null) {
            requireRestorable(baseline);
        }
        byte[] current = device.read();
        requireRestorable(current);
        captureBaseline(current);
        if (!Arrays.equals(current, baseline)) {
            invalidateSession();
        }
        if (Arrays.equals(current, desired)) {
            return "UNCHANGED_READBACK：当前值已匹配；未发送写入；不证明 RF 状态。";
        }
        return writeAndReadback(desired, device, false);
    }

    String restore(DeviceState device) throws Exception {
        requireValidSession();
        requireRestorable(baseline);
        byte[] current;
        try {
            current = device.read();
            requireRestorable(current);
        } catch (Exception exception) {
            restoreRequired = true;
            if (exception instanceof InterruptedException) {
                Thread.currentThread().interrupt();
            }
            return restoreRequiredResult("RESTORE_BASELINE_READ");
        }
        if (Arrays.equals(current, baseline)) {
            restoreRequired = false;
            attemptedState = null;
            return "BASELINE_READBACK_NO_WRITE：已读回原基线；未发送恢复写入；不证明 RF 或持久性。";
        }
        if (attemptedState == null || !Arrays.equals(current, attemptedState)) {
            invalidateSession();
        }
        return writeAndReadback(baseline, device, true);
    }

    private String writeAndReadback(byte[] desired, DeviceState device, boolean restoring) {
        // Set before dispatch: an exception/timeout may occur after the device applied the value.
        restoreRequired = true;
        if (!restoring) {
            attemptedState = desired.clone();
        }
        String phase = "ACK";
        try {
            device.write(desired.clone());
            phase = "READBACK";
            byte[] actual = device.read();
            requireRestorable(actual);
            if (!Arrays.equals(actual, desired)) {
                return restoreRequiredResult(phase);
            }
            restoreRequired = !Arrays.equals(actual, baseline);
            if (!restoreRequired) {
                attemptedState = null;
            }
            return restoring
                    ? "RESTORED_READBACK：本次基线已恢复并读回；不证明 RF 或重连持久性。"
                    : "APPLIED_READBACK_RESTORE_REQUIRED：写入已读回；须恢复原基线后才能再次变更；不证明 RF。";
        } catch (Exception exception) {
            if (exception instanceof InterruptedException) {
                Thread.currentThread().interrupt();
            }
            // Never include transport exception text, returned bytes, or identifiers in reports.
            return restoreRequiredResult(phase);
        }
    }

    private void requireValidSession() {
        if (baselineInvalid) {
            throw new IllegalStateException(
                    "SESSION_BASELINE_CHANGED：外部状态变化；禁止写入及覆盖旧基线，须重新建立只读会话。");
        }
    }

    private void invalidateSession() {
        baselineInvalid = true;
        requireValidSession();
    }

    private static String restoreRequiredResult(String phase) {
        return "RESTORE_REQUIRED：" + phase + " 未确认；本次基线仅保留在进程内。"
                + "禁止继续变更或声称已恢复；本构建不自动重试/恢复，请停止并按获准恢复流程处理。";
    }

    private void requireRestorable(byte[] value) {
        if (field == Field.OPERATOR_ID) {
            OperatorIdCodec.requireRestorableBaseline(value);
        } else if (value == null || value.length != 1 || (value[0] != 0 && value[0] != 1)) {
            throw new IllegalStateException("EID 基线不是可恢复 Boolean；未发送写入。");
        }
    }
}
