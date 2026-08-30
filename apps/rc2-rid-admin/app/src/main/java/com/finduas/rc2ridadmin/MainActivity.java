package com.finduas.rc2ridadmin;

import android.app.Activity;
import android.app.Application;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Process;
import android.os.SystemClock;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicBoolean;

/** RC 2 laboratory panel led by a read-only modern FlySafe RID inventory query. */
public final class MainActivity extends Activity {
    private TextView status;
    private EditText operatorInput;
    private final List<Button> operationButtons = new ArrayList<>();
    private final List<Button> identityWriteButtons = new ArrayList<>();
    private final AtomicBoolean operationRunning = new AtomicBoolean(false);
    private final AtomicBoolean flysafeStopRequested = new AtomicBoolean(false);
    private volatile boolean flysafeOneShotRunning;
    private final AtomicBoolean directFlysafeStopRequested = new AtomicBoolean(false);
    private volatile boolean directFlysafeRunning;
    private Button ridDisableButton;
    private Button ridEnableButton;
    private Button ridRestoreButton;
    private final IdentityControlTransaction eidTransaction =
            new IdentityControlTransaction(IdentityControlTransaction.Field.EID);
    private final IdentityControlTransaction operatorTransaction =
            new IdentityControlTransaction(IdentityControlTransaction.Field.OPERATOR_ID);
    private RidControlParameter.Metadata ridControlMetadata;
    private Boolean ridControlBaseline;
    private DjiProtocolClient.Route ridControlRoute;
    private Button ridEuC0DisableButton;
    private Button ridEuC0EnableButton;
    private Button ridEuC0RestoreButton;
    private RidEuC0Parameter.Metadata ridEuC0Metadata;
    private Boolean ridEuC0Baseline;
    private DjiProtocolClient.Route ridEuC0Route;
    private String ridRouteProbeDiagnostic;

    private static final int PARAM_READBACK_ATTEMPTS = 4;
    private static final int HEIGHT_LIMIT_HASH = 0x0371238A;
    private static final String HEIGHT_LIMIT_NAME = "g_config.flying_limit.max_height_0";
    private static final String RESULT_PREFS = "flysafe_gate_result";
    private static final String RESULT_KEY = "last_privacy_reduced_result";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(buildUi());
        String previousResult = getSharedPreferences(RESULT_PREFS, MODE_PRIVATE)
                .getString(RESULT_KEY, null);
        status.setText(runtimeLine() + (previousResult == null
                ? "\n尚未执行操作。FlySafe gate + 清单查询是一次性原子流程。"
                : "\n上次一次性 FlySafe 结果：\n" + previousResult));
        updateButtonState();
    }

    @Override
    protected void onStop() {
        super.onStop();
        if (flysafeOneShotRunning) {
            // Never kill while system_server may still be inside tx2/linkToDeath registration.
            // The worker observes this flag and exits only after the Binder transaction returns.
            flysafeStopRequested.set(true);
        }
        if (directFlysafeRunning) {
            // An already dispatched Binder request is allowed to finish its bounded vendor retry
            // window; cancellation prevents any following page selector from being sent.
            directFlysafeStopRequested.set(true);
        }
    }

    private ScrollView buildUi() {
        int p = Math.round(16 * getResources().getDisplayMetrics().density);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(p, p, p, p);

        TextView title = text("FindUAS — RC 2 RID 查询与管理面板", 26, Color.BLACK);
        content.addView(title);
        content.addView(text(
                "主目标：查询并验证现有 RID_UNLOCK 清单。被动 gate 路线继续保留；如果第三方 "
                        + "listener 看不到 03/09 与 03/42，也可单独运行固定候选路线的主动只读 "
                        + "11/11 兼容性探针。两条路线都不会从该按钮发送 11/12。",
                17,
                Color.DKGRAY));

        status = text("准备中…", 17, Color.rgb(20, 80, 160));
        status.setPadding(0, p, 0, p);
        status.setTextIsSelectable(true);
        status.setTypeface(Typeface.MONOSPACE);
        content.addView(status);

        content.addView(button("复制当前结果", this::copyStatus));
        content.addView(button("主动只读查询 11/11（固定单候选，无需 gate）",
                this::runDirectFlysafeReadonlyProbe));
        content.addView(text(
                "只尝试一次固定候选 02:04→12:04；使用 V3/V4 共用的 00 01 起始选择器，"
                        + "不扫描 sender、receiver 或 V2。每个选择器不做应用层重试；RC331 "
                        + "内部最多初发加两次重试。只有 count、逐页和空终止包全部一致才算清单结果；"
                        + "超时/失败只表示该候选查询不可用，不能解释为没有 RID 许可。",
                14,
                Color.GRAY));
        content.addView(button("被动识别 FlySafe gate，并在通过后查询 RID 清单（一次性）",
                this::runFlysafeGateAndInventory));
        content.addView(text(
                "使用方法：飞机先保持关闭或断开，点击后再正常开机并连接。观察最长 60 秒；"
                        + "完成后应用会保存去敏结果并自动退出，以让 Binder death 清理 listener。"
                        + "重新打开只用于查看结果，不能复用旧 gate 发查询。",
                14,
                Color.GRAY));
        content.addView(text(
                "已知不可用诊断：旧 11/1C 被动监听在当前 RC331 主界面路径没有形成可靠"
                        + "观测面，现已降级为历史诊断，不再作为 RID 状态主流程或操作按钮。",
                14,
                Color.GRAY));
        content.addView(text(
                "以下为既有实验功能。RIDCtrlEnable：先用 F7/F8 确认 Mini 5 Pro 是否暴露"
                        + " rid_ctrl_enable_0；"
                        + "只有确认存在并取得原值后，开关按钮才会执行 F9。",
                16,
                Color.DKGRAY));
        content.addView(button("探测并读取 RIDCtrlEnable（只读）", () ->
                runOperation("正在探测 RIDCtrlEnable…", this::readRidControl)));
        ridDisableButton = button("关闭候选参数并读回", () ->
                runOperation("正在关闭候选参数…", () -> setAndReadRidControl(false)));
        content.addView(ridDisableButton);
        ridEnableButton = button("开启候选参数并读回", () ->
                runOperation("正在开启候选参数…", () -> setAndReadRidControl(true)));
        content.addView(ridEnableButton);
        ridRestoreButton = button("恢复本次读取到的候选参数基线", () ->
                runOperation("正在恢复候选参数…", this::restoreRidControl));
        content.addView(ridRestoreButton);
        content.addView(text(
                "EU C0 独立通路：只对 EU_CE_enable_c0_rid_0（0xF80992FE）执行"
                        + " F7/F8 只读探测；只有 F7/F8 基线通过后，开关按钮才会发送 F9。"
                        + " 该参数是 EU C0 策略候选，不是全局 RID 主开关；写入不代表空口广播改变。",
                14,
                Color.DKGRAY));
        content.addView(button("探测并读取 EU C0 参数（只读）", () ->
                runOperation("正在探测 EU C0 参数…", this::readRidEuC0)));
        ridEuC0DisableButton = button("关闭 EU C0 候选参数并读回", () ->
                runOperation("正在关闭 EU C0 候选参数…", () -> setAndReadRidEuC0(false)));
        content.addView(ridEuC0DisableButton);
        ridEuC0EnableButton = button("开启 EU C0 候选参数并读回", () ->
                runOperation("正在开启 EU C0 候选参数…", () -> setAndReadRidEuC0(true)));
        content.addView(ridEuC0EnableButton);
        ridEuC0RestoreButton = button("恢复 EU C0 候选参数基线", () ->
                runOperation("正在恢复 EU C0 候选参数…", this::restoreRidEuC0));
        content.addView(ridEuC0RestoreButton);
        content.addView(text(
                "STATIC LOCKED：法国 EID / EASA OPID 写入、删除和恢复均未准入。"
                        + "当前缺少已验证的设备 owner/route、恢复和 RF 证据；读取成功也不会解锁。"
                        + "OPID 仅显示已设置/未设置/未知，不显示或复制编号。",
                14,
                Color.DKGRAY));
        content.addView(button("刷新 EID 状态（候选只读）", () -> runOperation("正在读取 EID…", this::readEid)));
        content.addView(identityWriteButton("关闭法国 EID（未准入）", () ->
                runOperation("正在关闭并读回…", () -> setAndReadEid(false))));
        content.addView(identityWriteButton("开启法国 EID（未准入）", () ->
                runOperation("正在开启并读回…", () -> setAndReadEid(true))));
        content.addView(identityWriteButton("恢复 EID 基线（未准入）", () ->
                runOperation("正在恢复并读回…", this::restoreBaseline)));
        content.addView(button("读取 EU 运营人编号", () ->
                runOperation("正在读取运营人编号…", this::readOperatorId)));
        operatorInput = new EditText(this);
        operatorInput.setSingleLine(true);
        operatorInput.setTextSize(16);
        operatorInput.setHint("OPID 编辑未准入，不接受编号输入");
        operatorInput.setEnabled(false);
        operatorInput.setSaveEnabled(false);
        content.addView(operatorInput);
        content.addView(identityWriteButton("设置 EU 运营人编号（未准入）", () ->
                runOperation("正在设置运营人编号并读回…", this::setOperatorId)));
        content.addView(identityWriteButton("删除 EU 运营人编号（未准入）", () ->
                runOperation("正在删除运营人编号并读回…", this::deleteOperatorId)));
        content.addView(identityWriteButton("恢复 EU 运营人编号（未准入）", () ->
                runOperation("正在恢复运营人编号并读回…", this::restoreOperatorId)));
        content.addView(button("打开 DJI 开发助手（人工协议页）", this::openDeveloperAssistant));

        TextView process = text(
                "进程标签：" + Application.getProcessName()
                        + "\nLinux UID 不会改变；该标签用于兼容 RC331 ProtocolManagerService v10 的调用方识别实现。",
                13,
                Color.GRAY);
        process.setPadding(0, p, 0, 0);
        content.addView(process);

        ScrollView scroll = new ScrollView(this);
        scroll.addView(content);
        return scroll;
    }

    private Button button(String label, Runnable action) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        button.setTextSize(17);
        button.setOnClickListener(view -> action.run());
        button.setLayoutParams(new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));
        operationButtons.add(button);
        return button;
    }

    private Button identityWriteButton(String label, Runnable action) {
        Button button = button(label, action);
        identityWriteButtons.add(button);
        button.setEnabled(false);
        return button;
    }

    private TextView text(String value, int size, int color) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        return view;
    }

    private interface Operation {
        String run() throws Exception;
    }

    private void runOperation(String workingText, Operation operation) {
        if (!operationRunning.compareAndSet(false, true)) {
            status.setText(runtimeLine() + "\n已有操作正在进行，请等待其完成。");
            return;
        }
        updateButtonState();
        status.setText(runtimeLine() + "\n" + workingText);
        new Thread(() -> {
            String operationResult;
            try {
                operationResult = operation.run();
            } catch (Throwable throwable) {
                operationResult = "失败：" + throwable.getClass().getSimpleName()
                        + (throwable.getMessage() == null ? "" : " — " + throwable.getMessage());
            }
            final String displayResult = runtimeLine() + "\n" + operationResult;
            runOnUiThread(() -> {
                status.setText(displayResult);
                operationRunning.set(false);
                updateButtonState();
            });
        }, "finduas-rid-operation").start();
    }

    private void updateButtonState() {
        boolean idle = !operationRunning.get();
        for (Button button : operationButtons) {
            button.setEnabled(idle);
        }
        for (Button button : identityWriteButtons) {
            button.setEnabled(idle && IdentityControlTransaction.writesAdmitted());
        }
        boolean candidateReady = idle
                && ridControlMetadata != null
                && ridControlBaseline != null
                && ridControlRoute != null;
        if (ridDisableButton != null) {
            ridDisableButton.setEnabled(candidateReady);
        }
        if (ridEnableButton != null) {
            ridEnableButton.setEnabled(candidateReady);
        }
        if (ridRestoreButton != null) {
            ridRestoreButton.setEnabled(candidateReady);
        }
        boolean euC0CandidateReady = idle
                && ridEuC0Metadata != null
                && ridEuC0Baseline != null
                && ridEuC0Route != null;
        if (ridEuC0DisableButton != null) {
            ridEuC0DisableButton.setEnabled(euC0CandidateReady);
        }
        if (ridEuC0EnableButton != null) {
            ridEuC0EnableButton.setEnabled(euC0CandidateReady);
        }
        if (ridEuC0RestoreButton != null) {
            ridEuC0RestoreButton.setEnabled(euC0CandidateReady);
        }
    }

    private static String runtimeLine() {
        return "L0 process=" + Application.getProcessName()
                + " pid=" + Process.myPid()
                + " uid=" + Process.myUid();
    }

    private void copyStatus() {
        ClipboardManager clipboard =
                (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText("FindUAS RID result", status.getText()));
    }

    private DjiProtocolClient client() throws Exception {
        DjiProtocolClient client = new DjiProtocolClient();
        if (!client.isEnabled()) {
            throw new IllegalStateException("DJI protocol 服务返回 disabled");
        }
        return client;
    }

    private void runDirectFlysafeReadonlyProbe() {
        if (!operationRunning.compareAndSet(false, true)) {
            status.setText(runtimeLine() + "\n已有操作正在进行，请等待其完成。");
            return;
        }
        directFlysafeStopRequested.set(false);
        directFlysafeRunning = true;
        updateButtonState();
        status.setText(runtimeLine()
                + "\n正在执行固定单候选主动只读 11/11 查询。"
                + "\n请保持飞机与遥控器正常连接、桨叶停止，并保持本页面在前台。"
                + "\n不会发送 11/12，也不会扫描其他 route。");
        new Thread(() -> {
            String operationResult;
            try {
                operationResult = readDirectFlysafeReadonlyInventory();
            } catch (Throwable throwable) {
                operationResult = "DIRECT_V3_V4_QUERY_UNAVAILABLE_OR_AMBIGUOUS"
                        + "\n阶段=" + throwable.getClass().getSimpleName()
                        + directFlysafeFailureDetail(throwable)
                        + "\n该结果不能解释为 unsupported、清单为空或没有 RID_UNLOCK。"
                        + "\n11/12 request count=0。";
            } finally {
                directFlysafeRunning = false;
            }
            final String diagnosticFileStatus = writeDirectDiagnostic(operationResult);
            final String displayResult = runtimeLine() + "\n" + operationResult
                    + "\n\n" + diagnosticFileStatus;
            runOnUiThread(() -> {
                status.setText(displayResult);
                operationRunning.set(false);
                updateButtonState();
            });
        }, "finduas-flysafe-direct-readonly").start();
    }

    private static String directFlysafeFailureDetail(Throwable throwable) {
        if (!(throwable instanceof FlysafeRidInventory.ProtocolException)) {
            return "";
        }
        String message = throwable.getMessage();
        return message == null || message.isEmpty() ? "" : "\n细分=" + message;
    }

    private String writeDirectDiagnostic(String operationResult) {
        String report;
        try {
            report = DirectDiagnosticReport.format(
                    getPackageManager().getPackageInfo(getPackageName(), 0).versionName,
                    Instant.now().toString(),
                    operationResult);
        } catch (Exception exception) {
            return "diagnosticFormat=FAILED:" + exception.getClass().getSimpleName();
        }

        StringBuilder status = new StringBuilder();
        try {
            File written = DiagnosticFileStore.writeLatest(
                    getExternalFilesDir("diagnostics"), report);
            status.append("diagnosticPrivate=").append(written.getAbsolutePath());
        } catch (Exception exception) {
            status.append("diagnosticPrivate=FAILED:")
                    .append(exception.getClass().getSimpleName());
        }
        try {
            DiagnosticFileStore.writePublicDownload(this, report);
            status.append("\ndiagnosticDownload=")
                    .append(DiagnosticFileStore.publicRelativeLocation());
        } catch (Exception exception) {
            status.append("\ndiagnosticDownload=FAILED:")
                    .append(exception.getClass().getSimpleName());
        }
        return status.toString();
    }

    private String readDirectFlysafeReadonlyInventory() throws Exception {
        DjiProtocolClient protocolClient = client();
        DjiProtocolClient.DirectFlysafeReadonlyPass pass =
                protocolClient.beginDirectFlysafeReadonlyProbe(
                        directFlysafeStopRequested::get);
        FlysafeRidInventory.Result result = null;
        boolean passCompleted = false;
        try {
            result = FlysafeRidInventory.queryReadOnly(payload -> {
                DjiProtocolClient.Reply reply = protocolClient.queryDirectFlysafeReadonly(
                        pass, payload);
                try {
                    if (!reply.callbackSuccess) {
                        throw new FlysafeRidInventory.ProtocolException(
                                "transport callback failed; "
                                        + reply.displayDirectReadonlyFailure());
                    }
                    return new FlysafeRidInventory.Response(
                            reply.callbackSuccess,
                            reply.ccode,
                            reply.data);
                } finally {
                    if (reply.data != null) {
                        Arrays.fill(reply.data, (byte) 0);
                    }
                }
            });
            protocolClient.finishDirectFlysafeReadonlyProbe(pass, result);
            passCompleted = true;
            return "DIRECT_V3_V4_CANONICAL_INVENTORY"
                    + "\n候选 route=02:04>12:04；应用层重试=0；"
                    + "RC331 transport attempts<=3。"
                    + "\n这证明本次固定候选返回了 count 一致的 V3/V4-compatible 清单；"
                    + "不能据此区分 V3/V4，也不证明 RF RID 行为。"
                    + "\n\n" + result.displayDirectReadonly()
                    + "\n11/12 request count=0。";
        } finally {
            if (!passCompleted) {
                pass.close();
            }
            if (result != null) {
                result.close();
            }
        }
    }

    private String readFlysafeRidInventory(
            DjiProtocolClient protocolClient,
            DjiProtocolClient.FlysafeGateObservation gateObservation) throws Exception {
        DjiProtocolClient.FlysafeInventoryPass inventoryPass =
                protocolClient.beginModernFlysafeInventoryPass(gateObservation);
        FlysafeRidInventory.Result result = null;
        boolean passCompleted = false;
        try {
            result = FlysafeRidInventory.query(payload -> {
                if (flysafeStopRequested.get() && !gateObservation.isRecoveryMode()) {
                    throw new IllegalStateException("FLYSAFE_QUERY_CANCELLED_BY_ACTIVITY_STOP");
                }
                DjiProtocolClient.Reply reply = protocolClient.queryModernFlysafeLicense(
                        inventoryPass, payload);
                try {
                    // Do not pass reply diagnostics into the semantic layer: a license ACK is
                    // sensitive.
                    return new FlysafeRidInventory.Response(
                            reply.callbackSuccess,
                            reply.ccode,
                            reply.data);
                } finally {
                    if (reply.data != null) {
                        Arrays.fill(reply.data, (byte) 0);
                    }
                }
            });
            protocolClient.finishModernFlysafeInventoryPass(inventoryPass, result);
            passCompleted = true;
            return result.display();
        } finally {
            if (!passCompleted) {
                inventoryPass.close();
            }
            if (result != null) {
                result.close();
            }
        }
    }

    private void runFlysafeGateAndInventory() {
        if (!operationRunning.compareAndSet(false, true)) {
            status.setText(runtimeLine() + "\n已有操作正在进行，请等待其完成。");
            return;
        }
        flysafeStopRequested.set(false);
        flysafeOneShotRunning = true;
        updateButtonState();
        status.setText(runtimeLine()
                + "\nLISTENER 准备中。确认飞机当前关闭/断开；显示 LISTENER_READY 后再开机连接。"
                + "\n本应用不会控制电机。请保持本页面在前台。");
        new Thread(() -> {
            String durableResult;
            String transientDiagnostic = "";
            DjiProtocolClient protocolClient = null;
            DjiProtocolClient.FlysafeGateObservation gateObservation = null;
            try {
                protocolClient = client();
                gateObservation = protocolClient.listenForFlysafeProtocolGate(
                        60_000,
                        () -> {
                            if (!flysafeStopRequested.get()) {
                                runOnUiThread(() -> status.setText(runtimeLine()
                                        + "\nLISTENER_READY：现在正常开机并连接飞机；"
                                        + "正在等待 03/09 与 03/42…"));
                            }
                        },
                        flysafeStopRequested::get);
                durableResult = gateObservation.display();
                transientDiagnostic = gateObservation.diagnostic;
                if (flysafeStopRequested.get()) {
                    durableResult += "\n\n11/11 request count=0（页面已离开，操作已取消）";
                } else if (gateObservation.allowsModernInventory()) {
                    try {
                        durableResult += "\n\n" + readFlysafeRidInventory(
                                protocolClient, gateObservation);
                    } catch (Throwable throwable) {
                        durableResult += "\n\nQUERY_TRANSPORT_OR_SCHEMA_FAILED："
                                + throwable.getClass().getSimpleName();
                    }
                } else {
                    durableResult += "\n\n11/11 request count=0（gate 未准入）";
                }
            } catch (Throwable throwable) {
                durableResult = "FLYSAFE_GATE_OPERATION_FAILED："
                        + throwable.getClass().getSimpleName()
                        + "\n11/11 request count=0 或未能确认；不能解释为无 RID 许可。";
            } finally {
                if (protocolClient != null) {
                    protocolClient.finishModernFlysafeSession(gateObservation);
                }
            }

            boolean persisted;
            try {
                persisted = getSharedPreferences(RESULT_PREFS, MODE_PRIVATE).edit()
                        .putString(RESULT_KEY, durableResult)
                        .commit();
            } catch (RuntimeException exception) {
                persisted = false;
            }
            new Thread(() -> {
                if (!flysafeStopRequested.get()) {
                    SystemClock.sleep(4000);
                }
                Process.killProcess(Process.myPid());
            }, "finduas-flysafe-process-cleanup").start();
            final String displayResult = runtimeLine() + "\n" + durableResult
                    + (transientDiagnostic.isEmpty()
                    ? "" : "\n\n本次临时诊断（不持久化）：" + transientDiagnostic)
                    + "\n\nresultPersist=" + (persisted ? "ok" : "failed")
                    + "；应用即将退出并清理 listener。";
            try {
                runOnUiThread(() -> status.setText(displayResult));
            } catch (RuntimeException ignored) {
                // The independent cleanup thread remains authoritative.
            }
        }, "finduas-flysafe-gated-query").start();
    }

    private String readEid() throws Exception {
        DjiProtocolClient.Reply reply = client().request(
                DjiProtocolClient.CMD_EID_SWITCH, new byte[]{0x02});
        Boolean value = parseEid(reply);
        eidTransaction.captureBaseline(new byte[] {(byte) (value ? 1 : 0)});
        return "法国 EID：" + (value ? "开启" : "关闭")
                + "；本次基线：" + (eidTransaction.baseline()[0] == 1 ? "开启" : "关闭")
                + "；写入仍未准入；不证明 RF 状态"
                + diagnosticBlock("EID GET", reply);
    }

    private DjiProtocolClient.Route findWorkingParameterRoute(DjiProtocolClient client)
            throws Exception {
        DjiProtocolClient.Route[] candidates = {
                DjiProtocolClient.RC2_LEGACY_FC,
                DjiProtocolClient.MODERN_FC4
        };
        StringBuilder diagnostics = new StringBuilder();
        for (DjiProtocolClient.Route route : candidates) {
            DjiProtocolClient.Reply reply = client.request(
                    route,
                    DjiProtocolClient.CMD_PARAM_INFO_BY_HASH,
                    hashPayload(HEIGHT_LIMIT_HASH));
            if (diagnostics.length() > 0) {
                diagnostics.append("\n");
            }
            diagnostics.append(route.summary())
                    .append(" positiveControl=")
                    .append(f7MatchesName(reply, HEIGHT_LIMIT_NAME) ? "PASS" : "FAIL")
                    .append(" callback=").append(reply.callbackSuccess)
                    .append(" ccode=").append(reply.ccode)
                    .append(" data=").append(hex(reply.data))
                    .append("; ").append(reply.diagnostic);
            if (f7MatchesName(reply, HEIGHT_LIMIT_NAME)) {
                ridRouteProbeDiagnostic = diagnostics.toString();
                return route;
            }
        }
        ridRouteProbeDiagnostic = diagnostics.toString();
        throw new IllegalStateException(
                "两条 Binder 参数路由的最大高度 F7 正控都未通过；不能解释目标参数结果"
                        + "\nROUTE PROBE: " + ridRouteProbeDiagnostic);
    }

    private static boolean f7MatchesName(DjiProtocolClient.Reply reply, String expectedName) {
        if (reply == null || !reply.callbackSuccess || reply.ccode != 0
                || reply.data == null || reply.data.length < 20 || reply.data[0] != 0) {
            return false;
        }
        int terminator = -1;
        for (int index = 19; index < reply.data.length; index++) {
            if (reply.data[index] == 0) {
                terminator = index;
                break;
            }
        }
        if (terminator < 0) {
            return false;
        }
        String actual = new String(
                reply.data, 19, terminator - 19, StandardCharsets.US_ASCII);
        if (!expectedName.equals(actual)) {
            return false;
        }
        for (int index = terminator + 1; index < reply.data.length; index++) {
            if (reply.data[index] != 0) {
                return false;
            }
        }
        return true;
    }

    private static byte[] hashPayload(int hash) {
        return new byte[] {
                (byte) hash,
                (byte) (hash >>> 8),
                (byte) (hash >>> 16),
                (byte) (hash >>> 24)
        };
    }

    private String readRidControl() throws Exception {
        RidControlRead read = probeRidControl(client());
        return ridControlDisplay("RIDCtrlEnable 候选参数", read)
                + "\nROUTE PROBE: " + ridRouteProbeDiagnostic
                + diagnosticBlock("RID F7", read.metadataReply)
                + diagnosticBlock("RID F8", read.valueReply);
    }

    private RidControlRead probeRidControl(DjiProtocolClient client) throws Exception {
        DjiProtocolClient.Route route = findWorkingParameterRoute(client);
        DjiProtocolClient.Reply metadataReply = client.request(
                route,
                DjiProtocolClient.CMD_PARAM_INFO_BY_HASH,
                RidControlParameter.buildHashRequestPayload());
        requireSuccess(metadataReply, "RID F7");

        final RidControlParameter.Metadata metadata;
        try {
            metadata = RidControlParameter.parseF7Metadata(metadataReply.data);
        } catch (RidControlParameter.ProtocolException exception) {
            throw new IllegalStateException(exception.getMessage()
                    + "\nROUTE PROBE: " + ridRouteProbeDiagnostic
                    + diagnosticBlock("RID F7", metadataReply), exception);
        }

        RidControlRead read = readRidControlValue(client, route, metadata, metadataReply);
        ridControlRoute = route;
        ridControlMetadata = metadata;
        if (ridControlBaseline == null) {
            ridControlBaseline = read.value.isEnabled();
        }
        return read;
    }

    private RidControlRead readRidControlValue(
            DjiProtocolClient client,
            DjiProtocolClient.Route route,
            RidControlParameter.Metadata metadata,
            DjiProtocolClient.Reply metadataReply) throws Exception {
        DjiProtocolClient.Reply valueReply = client.request(
                route,
                DjiProtocolClient.CMD_PARAM_READ_BY_HASH,
                RidControlParameter.buildHashRequestPayload());
        requireSuccess(valueReply, "RID F8");
        final RidControlParameter.Value value;
        try {
            value = RidControlParameter.parseF8Value(valueReply.data, metadata);
        } catch (RidControlParameter.ProtocolException exception) {
            throw new IllegalStateException(exception.getMessage()
                    + diagnosticBlock("RID F8", valueReply), exception);
        }
        return new RidControlRead(metadata, value, metadataReply, valueReply);
    }

    private String setAndReadRidControl(boolean enabled) throws Exception {
        DjiProtocolClient client = client();
        // Refresh F7/F8 and the live route immediately before every write.
        RidControlRead before = probeRidControl(client);
        if (before.value.isEnabled() == enabled) {
            return ridControlDisplay("候选参数已经是目标值，未发送 F9", before)
                    + "\n这只代表参数值，不代表真实 RID 空口广播。";
        }

        byte[] setPayload = RidControlParameter.buildSetPayload(enabled, ridControlMetadata);
        DjiProtocolClient.Reply setReply = null;
        Throwable setIssue = null;
        try {
            setReply = client.request(
                    ridControlRoute,
                    DjiProtocolClient.CMD_PARAM_WRITE_BY_HASH,
                    setPayload);
            requireSuccess(setReply, "RID F9");
            requireParamWriteStatus(setReply);
        } catch (Throwable throwable) {
            setIssue = throwable;
        }

        RidControlRead readback = null;
        Throwable readbackIssue = null;
        try {
            readback = pollRidControlValue(client, enabled);
        } catch (Throwable throwable) {
            readbackIssue = throwable;
        }
        if (readback != null && readback.value.isEnabled() == enabled) {
            return ridControlDisplay("候选参数写入并连续读回一致", readback)
                    + (setIssue == null ? "" : "\nF9 ACK 异常，但 F8 已确认目标值：" + setIssue)
                + "\n尚未证明 RID 广播改变；必须结合 RID 工作状态和起桨后的空口 A/B/A。"
                + diagnosticBlock("RID F9", setReply)
                + diagnosticBlock("RID F8", readback.valueReply);
        }

        boolean restoreValue = before.value.isEnabled();
        DjiProtocolClient.Reply restoreReply = null;
        Throwable restoreIssue = null;
        try {
            restoreReply = client.request(
                    ridControlRoute,
                    DjiProtocolClient.CMD_PARAM_WRITE_BY_HASH,
                    RidControlParameter.buildSetPayload(restoreValue, ridControlMetadata));
            requireSuccess(restoreReply, "RID F9 ROLLBACK");
            requireParamWriteStatus(restoreReply);
        } catch (Throwable throwable) {
            restoreIssue = throwable;
        }

        RidControlRead restored = null;
        Throwable rollbackReadIssue = null;
        try {
            restored = pollRidControlValue(client, restoreValue);
        } catch (Throwable throwable) {
            rollbackReadIssue = throwable;
        }
        if (restored != null) {
            throw new IllegalStateException(
                    "候选参数写入未能可靠确认，已恢复操作前状态："
                            + (restoreValue ? "开启" : "关闭")
                            + "\n原 F9：" + issueSummary(setIssue)
                            + "\n原 F8：" + issueSummary(readbackIssue)
                            + "\n恢复 F9：" + issueSummary(restoreIssue)
                            + diagnosticBlock("RID ROLLBACK F9", restoreReply)
                            + diagnosticBlock("RID ROLLBACK F8", restored.valueReply));
        }
        throw new IllegalStateException(
                "候选参数状态 UNKNOWN：写入后无法确认，恢复也未能读回。"
                        + "请勿继续点击写入；重新连接后先做只读探测。"
                        + "\n原 F9：" + issueSummary(setIssue)
                        + "\n原 F8：" + issueSummary(readbackIssue)
                        + "\n恢复 F9：" + issueSummary(restoreIssue)
                        + "\n恢复 F8：" + issueSummary(rollbackReadIssue)
                        + diagnosticBlock("RID ROLLBACK F9", restoreReply),
                rollbackReadIssue);
    }

    private RidControlRead pollRidControlValue(DjiProtocolClient client, boolean expected)
            throws Exception {
        RidControlRead lastRead = null;
        Throwable lastIssue = null;
        for (int attempt = 1; attempt <= PARAM_READBACK_ATTEMPTS; attempt++) {
            Thread.sleep(200L * attempt);
            try {
                lastRead = readRidControlValue(
                        client, ridControlRoute, ridControlMetadata, null);
                if (lastRead.value.isEnabled() == expected) {
                    // Require a second consistent sample so a transient cache value is not enough.
                    Thread.sleep(200);
                    RidControlRead confirmation = readRidControlValue(
                            client, ridControlRoute, ridControlMetadata, null);
                    if (confirmation.value.isEnabled() == expected) {
                        return confirmation;
                    }
                    lastRead = confirmation;
                }
            } catch (Throwable throwable) {
                lastIssue = throwable;
            }
        }
        if (lastRead != null) {
            throw new IllegalStateException(
                    "F8 未连续读回预期值 " + (expected ? 1 : 0)
                            + diagnosticBlock("RID F8 LAST", lastRead.valueReply));
        }
        if (lastIssue instanceof Exception) {
            throw (Exception) lastIssue;
        }
        throw new IllegalStateException("F8 读回失败：" + issueSummary(lastIssue));
    }

    private static String issueSummary(Throwable throwable) {
        if (throwable == null) {
            return "none";
        }
        return throwable.getClass().getSimpleName()
                + (throwable.getMessage() == null ? "" : ":" + throwable.getMessage());
    }

    private String restoreRidControl() throws Exception {
        if (ridControlBaseline == null || ridControlMetadata == null) {
            return "尚未取得 RIDCtrlEnable 基线，请先执行只读探测";
        }
        return setAndReadRidControl(ridControlBaseline);
    }

    private String readRidEuC0() throws Exception {
        RidEuC0Read read = probeRidEuC0(client());
        return ridEuC0Display("EU C0 候选参数", read)
                + "\nROUTE PROBE: " + ridRouteProbeDiagnostic
                + "\n据 FreeFCC 公开记载，DJI Fly 的 C0 class 运行时标志会在每次连接时覆盖飞控参数；"
                + "单次 F8 读回不等于重连后仍保持。"
                + diagnosticBlock("EU C0 F7", read.metadataReply)
                + diagnosticBlock("EU C0 F8", read.valueReply);
    }

    private RidEuC0Read probeRidEuC0(DjiProtocolClient client) throws Exception {
        DjiProtocolClient.Route route = findWorkingParameterRoute(client);
        DjiProtocolClient.Reply metadataReply = client.request(
                route,
                DjiProtocolClient.CMD_PARAM_INFO_BY_HASH,
                RidEuC0Parameter.buildHashRequestPayload());
        requireSuccess(metadataReply, "EU C0 F7");

        final RidEuC0Parameter.Metadata metadata;
        try {
            metadata = RidEuC0Parameter.parseF7Metadata(metadataReply.data);
        } catch (RidEuC0Parameter.ProtocolException exception) {
            throw new IllegalStateException(exception.getMessage()
                    + "\nROUTE PROBE: " + ridRouteProbeDiagnostic
                    + diagnosticBlock("EU C0 F7", metadataReply), exception);
        }

        RidEuC0Read read = readRidEuC0Value(client, route, metadata, metadataReply);
        ridEuC0Route = route;
        ridEuC0Metadata = metadata;
        if (ridEuC0Baseline == null) {
            ridEuC0Baseline = read.value.isEnabled();
        }
        return read;
    }

    private RidEuC0Read readRidEuC0Value(
            DjiProtocolClient client,
            DjiProtocolClient.Route route,
            RidEuC0Parameter.Metadata metadata,
            DjiProtocolClient.Reply metadataReply) throws Exception {
        DjiProtocolClient.Reply valueReply = client.request(
                route,
                DjiProtocolClient.CMD_PARAM_READ_BY_HASH,
                RidEuC0Parameter.buildHashRequestPayload());
        requireSuccess(valueReply, "EU C0 F8");
        final RidEuC0Parameter.Value value;
        try {
            value = RidEuC0Parameter.parseF8Value(valueReply.data, metadata);
        } catch (RidEuC0Parameter.ProtocolException exception) {
            throw new IllegalStateException(exception.getMessage()
                    + diagnosticBlock("EU C0 F8", valueReply), exception);
        }
        return new RidEuC0Read(metadata, value, metadataReply, valueReply);
    }

    private String setAndReadRidEuC0(boolean enabled) throws Exception {
        DjiProtocolClient client = client();
        // Refresh F7/F8 and the live route immediately before every write.
        RidEuC0Read before = probeRidEuC0(client);
        if (before.value.isEnabled() == enabled) {
            return ridEuC0Display("EU C0 候选参数已经是目标值，未发送 F9", before)
                    + "\n这只代表参数值，不代表真实 RID 空口广播；重连后可能被 DJI Fly 覆盖。";
        }

        byte[] setPayload = RidEuC0Parameter.buildSetPayload(enabled, ridEuC0Metadata);
        DjiProtocolClient.Reply setReply = null;
        Throwable setIssue = null;
        try {
            setReply = client.request(
                    ridEuC0Route,
                    DjiProtocolClient.CMD_PARAM_WRITE_BY_HASH,
                    setPayload);
            requireSuccess(setReply, "EU C0 F9");
            requireEuC0ParamWriteStatus(setReply);
        } catch (Throwable throwable) {
            setIssue = throwable;
        }

        RidEuC0Read readback = null;
        Throwable readbackIssue = null;
        try {
            readback = pollRidEuC0Value(client, enabled);
        } catch (Throwable throwable) {
            readbackIssue = throwable;
        }
        if (readback != null && readback.value.isEnabled() == enabled) {
            return ridEuC0Display("EU C0 候选参数写入并连续读回一致", readback)
                    + (setIssue == null ? "" : "\nF9 ACK 异常，但 F8 已确认目标值：" + setIssue)
                    + "\n尚未证明 RID 广播改变，且重连后可能被 DJI Fly C0 运行时标志覆盖；"
                    + "必须结合独立接收机做断开/重连后的空口 A-B/A。"
                    + diagnosticBlock("EU C0 F9", setReply)
                    + diagnosticBlock("EU C0 F8", readback.valueReply);
        }

        boolean restoreValue = before.value.isEnabled();
        DjiProtocolClient.Reply restoreReply = null;
        Throwable restoreIssue = null;
        try {
            restoreReply = client.request(
                    ridEuC0Route,
                    DjiProtocolClient.CMD_PARAM_WRITE_BY_HASH,
                    RidEuC0Parameter.buildSetPayload(restoreValue, ridEuC0Metadata));
            requireSuccess(restoreReply, "EU C0 F9 ROLLBACK");
            requireEuC0ParamWriteStatus(restoreReply);
        } catch (Throwable throwable) {
            restoreIssue = throwable;
        }

        RidEuC0Read restored = null;
        Throwable rollbackReadIssue = null;
        try {
            restored = pollRidEuC0Value(client, restoreValue);
        } catch (Throwable throwable) {
            rollbackReadIssue = throwable;
        }
        if (restored != null) {
            throw new IllegalStateException(
                    "EU C0 候选参数写入未能可靠确认，已恢复操作前状态："
                            + (restoreValue ? "开启" : "关闭")
                            + "\n原 F9：" + issueSummary(setIssue)
                            + "\n原 F8：" + issueSummary(readbackIssue)
                            + "\n恢复 F9：" + issueSummary(restoreIssue)
                            + diagnosticBlock("EU C0 ROLLBACK F9", restoreReply)
                            + diagnosticBlock("EU C0 ROLLBACK F8", restored.valueReply));
        }
        throw new IllegalStateException(
                "EU C0 候选参数状态 UNKNOWN：写入后无法确认，恢复也未能读回。"
                        + "请勿继续点击写入；重新连接后先做只读探测。"
                        + "\n原 F9：" + issueSummary(setIssue)
                        + "\n原 F8：" + issueSummary(readbackIssue)
                        + "\n恢复 F9：" + issueSummary(restoreIssue)
                        + "\n恢复 F8：" + issueSummary(rollbackReadIssue)
                        + diagnosticBlock("EU C0 ROLLBACK F9", restoreReply),
                rollbackReadIssue);
    }

    private RidEuC0Read pollRidEuC0Value(DjiProtocolClient client, boolean expected)
            throws Exception {
        RidEuC0Read lastRead = null;
        Throwable lastIssue = null;
        for (int attempt = 1; attempt <= PARAM_READBACK_ATTEMPTS; attempt++) {
            Thread.sleep(200L * attempt);
            try {
                lastRead = readRidEuC0Value(client, ridEuC0Route, ridEuC0Metadata, null);
                if (lastRead.value.isEnabled() == expected) {
                    // Require a second consistent sample so a transient cache value is not enough.
                    Thread.sleep(200);
                    RidEuC0Read confirmation = readRidEuC0Value(
                            client, ridEuC0Route, ridEuC0Metadata, null);
                    if (confirmation.value.isEnabled() == expected) {
                        return confirmation;
                    }
                    lastRead = confirmation;
                }
            } catch (Throwable throwable) {
                lastIssue = throwable;
            }
        }
        if (lastRead != null) {
            throw new IllegalStateException(
                    "EU C0 F8 未连续读回预期值 " + (expected ? 1 : 0)
                            + diagnosticBlock("EU C0 F8 LAST", lastRead.valueReply));
        }
        if (lastIssue instanceof Exception) {
            throw (Exception) lastIssue;
        }
        throw new IllegalStateException("EU C0 F8 读回失败：" + issueSummary(lastIssue));
    }

    private String restoreRidEuC0() throws Exception {
        if (ridEuC0Baseline == null || ridEuC0Metadata == null) {
            return "尚未取得 EU C0 基线，请先执行只读探测";
        }
        return setAndReadRidEuC0(ridEuC0Baseline);
    }

    private static void requireEuC0ParamWriteStatus(DjiProtocolClient.Reply reply) {
        if (reply.data == null || reply.data.length < 1) {
            // requireSuccess() has already required ccode == 0; F8 readback remains authoritative.
            return;
        }
        int statusValue = reply.data[0] & 0xff;
        if (statusValue != 0) {
            throw new IllegalStateException(String.format(Locale.US,
                    "EU C0 F9 status=0x%02X", statusValue)
                    + diagnosticBlock("EU C0 F9", reply));
        }
    }

    private String ridEuC0Display(String prefix, RidEuC0Read read) {
        RidEuC0Parameter.Metadata metadata = read.metadata;
        return prefix + "：" + (read.value.isEnabled() ? "开启" : "关闭")
                + "；基线：" + (ridEuC0Baseline != null && ridEuC0Baseline ? "开启" : "关闭")
                + "\nparam=" + metadata.getName()
                + " hash=0x" + String.format(Locale.US, "%08X", metadata.getHash())
                + " route=" + (ridEuC0Route == null ? "<unknown>" : ridEuC0Route.summary())
                + " type=" + metadata.getType()
                + " size=" + metadata.getSize()
                + " attr=0x" + String.format(Locale.US, "%04X", metadata.getAttribute())
                + " layout=" + read.value.getLayout()
                + " raw=" + hex(read.value.getRaw())
                + " min/max/default=" + hex(metadata.getMinimumRaw())
                + "/" + hex(metadata.getMaximumRaw())
                + "/" + hex(metadata.getDefaultRaw());
    }

    private static void requireParamWriteStatus(DjiProtocolClient.Reply reply) {
        if (reply.data == null || reply.data.length < 1) {
            // The RC331 Pack layer may expose the one-byte result as ccode and leave data empty.
            // requireSuccess() has already required ccode == 0; F8 readback remains authoritative.
            return;
        }
        int statusValue = reply.data[0] & 0xff;
        if (statusValue != 0) {
            throw new IllegalStateException(String.format(Locale.US,
                    "RID F9 status=0x%02X", statusValue)
                    + diagnosticBlock("RID F9", reply));
        }
    }

    private String ridControlDisplay(String prefix, RidControlRead read) {
        RidControlParameter.Metadata metadata = read.metadata;
        return prefix + "：" + (read.value.isEnabled() ? "开启" : "关闭")
                + "；基线：" + (ridControlBaseline != null && ridControlBaseline ? "开启" : "关闭")
                + "\nparam=" + metadata.getName()
                + " hash=0x" + String.format(Locale.US, "%08X", metadata.getHash())
                + " route=" + (ridControlRoute == null ? "<unknown>" : ridControlRoute.summary())
                + " type=" + metadata.getType()
                + " size=" + metadata.getSize()
                + " attr=0x" + String.format(Locale.US, "%04X", metadata.getAttribute())
                + " layout=" + read.value.getLayout()
                + " raw=" + hex(read.value.getRaw())
                + " min/max/default=" + hex(metadata.getMinimumRaw())
                + "/" + hex(metadata.getMaximumRaw())
                + "/" + hex(metadata.getDefaultRaw());
    }

    private static String hex(byte[] value) {
        if (value == null) {
            return "<null>";
        }
        StringBuilder result = new StringBuilder(value.length * 2);
        for (byte item : value) {
            result.append(String.format(Locale.US, "%02X", item & 0xff));
        }
        return result.toString();
    }

    private static final class RidControlRead {
        final RidControlParameter.Metadata metadata;
        final RidControlParameter.Value value;
        final DjiProtocolClient.Reply metadataReply;
        final DjiProtocolClient.Reply valueReply;

        RidControlRead(
                RidControlParameter.Metadata metadata,
                RidControlParameter.Value value,
                DjiProtocolClient.Reply metadataReply,
                DjiProtocolClient.Reply valueReply) {
            this.metadata = metadata;
            this.value = value;
            this.metadataReply = metadataReply;
            this.valueReply = valueReply;
        }
    }

    private static final class RidEuC0Read {
        final RidEuC0Parameter.Metadata metadata;
        final RidEuC0Parameter.Value value;
        final DjiProtocolClient.Reply metadataReply;
        final DjiProtocolClient.Reply valueReply;

        RidEuC0Read(
                RidEuC0Parameter.Metadata metadata,
                RidEuC0Parameter.Value value,
                DjiProtocolClient.Reply metadataReply,
                DjiProtocolClient.Reply valueReply) {
            this.metadata = metadata;
            this.value = value;
            this.metadataReply = metadataReply;
            this.valueReply = valueReply;
        }
    }

    private String setAndReadEid(boolean enabled) throws Exception {
        IdentityControlTransaction.requireWriteAdmission();
        return eidTransaction.transition(
                new byte[] {(byte) (enabled ? 1 : 0)}, eidDeviceState(client()));
    }

    private String restoreBaseline() throws Exception {
        IdentityControlTransaction.requireWriteAdmission();
        return eidTransaction.restore(eidDeviceState(client()));
    }

    private IdentityControlTransaction.DeviceState eidDeviceState(DjiProtocolClient client) {
        return new IdentityControlTransaction.DeviceState() {
            @Override
            public byte[] read() throws Exception {
                boolean value = parseEid(client.request(
                        DjiProtocolClient.CMD_EID_SWITCH, new byte[] {0x02}));
                return new byte[] {(byte) (value ? 1 : 0)};
            }

            @Override
            public void write(byte[] state) throws Exception {
                requireIdentityWriteAck(client.request(DjiProtocolClient.CMD_EID_SWITCH, state));
            }
        };
    }

    private String readOperatorId() throws Exception {
        DjiProtocolClient.Reply reply = client().request(
                DjiProtocolClient.CMD_OPERATOR_ID, new byte[] {0x02});
        byte[] value = parseOperatorId(reply);
        try {
            operatorTransaction.captureBaseline(value);
            return "EU 运营人编号：" + OperatorIdCodec.maskedSummary(value)
                    + "；写入仍未准入；不证明 RF 字段。";
        } finally {
            Arrays.fill(value, (byte) 0);
        }
    }

    private String setOperatorId() throws Exception {
        IdentityControlTransaction.requireWriteAdmission();
        byte[] payload = OperatorIdCodec.encodeSetPayload(
                operatorInput.getText().toString().trim());
        byte[] desired = Arrays.copyOfRange(payload, 2, 18);
        try {
            return operatorTransaction.transition(desired, operatorDeviceState(client()));
        } finally {
            Arrays.fill(payload, (byte) 0);
            Arrays.fill(desired, (byte) 0);
        }
    }

    private String deleteOperatorId() throws Exception {
        IdentityControlTransaction.requireWriteAdmission();
        return operatorTransaction.transition(new byte[0], operatorDeviceState(client()));
    }

    private String restoreOperatorId() throws Exception {
        IdentityControlTransaction.requireWriteAdmission();
        return operatorTransaction.restore(operatorDeviceState(client()));
    }

    private IdentityControlTransaction.DeviceState operatorDeviceState(DjiProtocolClient client) {
        return new IdentityControlTransaction.DeviceState() {
            @Override
            public byte[] read() throws Exception {
                return parseOperatorId(client.request(
                        DjiProtocolClient.CMD_OPERATOR_ID, new byte[] {0x02}));
            }

            @Override
            public void write(byte[] state) throws Exception {
                OperatorIdCodec.requireRestorableBaseline(state);
                byte[] payload = state.length == 0
                        ? new byte[] {0x01} : OperatorIdCodec.encodeRawPublic16(state);
                try {
                    requireIdentityWriteAck(client.request(DjiProtocolClient.CMD_OPERATOR_ID, payload));
                } finally {
                    Arrays.fill(payload, (byte) 0);
                }
            }
        };
    }

    private static byte[] parseOperatorId(DjiProtocolClient.Reply reply) {
        try {
            requireIdentityReplySuccess(reply);
            return OperatorIdCodec.decodeGetData(reply.data);
        } finally {
            if (reply != null && reply.data != null) {
                Arrays.fill(reply.data, (byte) 0);
            }
        }
    }

    private static void requireIdentityReplySuccess(DjiProtocolClient.Reply reply) {
        if (reply == null || !reply.callbackSuccess || reply.ccode != 0) {
            throw new IllegalStateException("IDENTITY_REPLY_UNAVAILABLE：未取得规范成功回包；值未知。");
        }
    }

    private static void requireIdentityWriteAck(DjiProtocolClient.Reply reply) {
        requireIdentityReplySuccess(reply);
        // Parsed Reply separates the result byte into ccode; SET/DELETE have no data bytes.
        if (reply.data != null && reply.data.length != 0) {
            throw new IllegalStateException("IDENTITY_WRITE_ACK_NONCANONICAL");
        }
    }

    private static Boolean parseEid(DjiProtocolClient.Reply reply) {
        requireSuccess(reply, "EID GET");
        if (reply.data == null || reply.data.length != 1) {
            throw new IllegalStateException("EID GET 回包长度不是 1"
                    + diagnosticBlock("EID GET", reply));
        }
        int value = reply.data[0] & 0xff;
        if (value != 0 && value != 1) {
            throw new IllegalStateException(String.format(Locale.US,
                    "EID 状态不是 Boolean: 0x%02X", value)
                    + diagnosticBlock("EID GET", reply));
        }
        return value == 1;
    }

    private static void requireSuccess(DjiProtocolClient.Reply reply, String operation) {
        if (!reply.callbackSuccess) {
            throw new IllegalStateException(operation + "：" + reply.failure
                    + diagnosticBlock(operation, reply));
        }
        if (reply.ccode != 0) {
            throw new IllegalStateException(operation + " ccode=" + reply.ccode
                    + diagnosticBlock(operation, reply));
        }
    }

    private static String diagnosticBlock(String label, DjiProtocolClient.Reply reply) {
        if (reply == null || reply.diagnostic == null || reply.diagnostic.isEmpty()) {
            return "";
        }
        return "\n" + label + " DIAG: " + reply.diagnostic;
    }

    private void openDeveloperAssistant() {
        Intent intent = new Intent("dji.intent.action.fuli");
        intent.addCategory(Intent.CATEGORY_DEFAULT);
        try {
            startActivity(intent);
        } catch (ActivityNotFoundException | SecurityException exception) {
            status.setText("无法打开 DJI 开发助手：" + exception.getClass().getSimpleName());
        }
    }
}
