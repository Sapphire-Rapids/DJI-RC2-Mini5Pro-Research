package com.finduas.rc2flysafeagentcarrier;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.graphics.Color;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

/** Displays and copies fixed diagnostic commands. It never executes a command. */
public final class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(buildUi());
    }

    private ScrollView buildUi() {
        final float density = getResources().getDisplayMetrics().density;
        final int padding = Math.round(20 * density);
        final int gap = Math.round(10 * density);
        final String nativeLibraryDir = getApplicationInfo().nativeLibraryDir;
        final String libraryPath = AttachCommands.libraryPath(nativeLibraryDir);

        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(padding, padding, padding, padding);

        TextView title = text(R.string.app_name, 24, Color.BLACK);
        content.addView(title, fullWidthWrapContent());

        TextView summary = text(R.string.summary, 17, Color.DKGRAY);
        summary.setPadding(0, gap, 0, gap);
        content.addView(summary, fullWidthWrapContent());

        TextView pathLabel = text(R.string.library_path_label, 16, Color.BLACK);
        content.addView(pathLabel, fullWidthWrapContent());

        TextView pathValue = text(libraryPath, 14, Color.rgb(20, 80, 150));
        pathValue.setTextIsSelectable(true);
        pathValue.setPadding(0, 0, 0, gap);
        content.addView(pathValue, fullWidthWrapContent());

        content.addView(commandButton(R.string.copy_pid, AttachCommands.PID_COMMAND),
                fullWidthWrapContent());
        content.addView(commandButton(
                        R.string.copy_attach,
                        AttachCommands.attachCommand(nativeLibraryDir)),
                fullWidthWrapContent());
        content.addView(commandButton(R.string.copy_log, AttachCommands.LOG_COMMAND),
                fullWidthWrapContent());

        TextView boundary = text(R.string.boundary, 16, Color.rgb(150, 40, 20));
        boundary.setPadding(0, gap, 0, 0);
        content.addView(boundary, fullWidthWrapContent());

        ScrollView scrollView = new ScrollView(this);
        scrollView.addView(content);
        return scrollView;
    }

    private TextView text(int resource, float size, int color) {
        TextView view = new TextView(this);
        view.setText(resource);
        view.setTextSize(size);
        view.setTextColor(color);
        return view;
    }

    private TextView text(String value, float size, int color) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        return view;
    }

    private Button commandButton(int label, String command) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        button.setOnClickListener(view -> copyCommand(command));
        return button;
    }

    private void copyCommand(String command) {
        ClipboardManager clipboard =
                (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText("FindUAS command", command));
        Toast.makeText(this, R.string.copied, Toast.LENGTH_SHORT).show();
    }

    private LinearLayout.LayoutParams fullWidthWrapContent() {
        return new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
    }
}
