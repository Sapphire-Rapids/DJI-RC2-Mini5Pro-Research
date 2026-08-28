package com.finduas.rc2settingslauncher;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.ResolveInfo;
import android.graphics.Color;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

/**
 * Two-button launcher for standard Android Settings activities.
 *
 * <p>This activity does not read or write settings, execute commands, access files or networks,
 * or invoke any DJI API. Every navigation is initiated by a foreground user click.</p>
 */
public final class MainActivity extends Activity {
    private TextView statusText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(buildUi());
    }

    private ScrollView buildUi() {
        final float density = getResources().getDisplayMetrics().density;
        final int padding = Math.round(20 * density);
        final int smallPadding = Math.round(10 * density);

        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(padding, padding, padding, padding);

        TextView title = new TextView(this);
        title.setText(R.string.app_name);
        title.setTextSize(24);
        title.setTextColor(Color.BLACK);
        content.addView(title);

        TextView instructions = new TextView(this);
        instructions.setText(R.string.instructions);
        instructions.setTextSize(17);
        instructions.setTextColor(Color.DKGRAY);
        instructions.setPadding(0, smallPadding, 0, smallPadding);
        content.addView(instructions);

        TextView warning = new TextView(this);
        warning.setText(R.string.warning);
        warning.setTextSize(18);
        warning.setTextColor(Color.rgb(180, 30, 20));
        warning.setPadding(0, 0, 0, smallPadding);
        content.addView(warning);

        Button deviceInfoButton = new Button(this);
        deviceInfoButton.setText(R.string.open_device_info);
        deviceInfoButton.setAllCaps(false);
        deviceInfoButton.setOnClickListener(view -> openSettings(
                LauncherContract.DEVICE_INFO_ACTION,
                R.string.device_info_opened,
                false));
        content.addView(deviceInfoButton, fullWidthWrapContent());

        Button developerOptionsButton = new Button(this);
        developerOptionsButton.setText(R.string.open_developer_options);
        developerOptionsButton.setAllCaps(false);
        developerOptionsButton.setOnClickListener(view -> openSettings(
                LauncherContract.DEVELOPMENT_SETTINGS_ACTION,
                R.string.developer_options_opened,
                true));
        content.addView(developerOptionsButton, fullWidthWrapContent());

        statusText = new TextView(this);
        statusText.setText(R.string.initial_status);
        statusText.setTextSize(15);
        statusText.setTextColor(Color.DKGRAY);
        statusText.setPadding(0, smallPadding, 0, 0);
        content.addView(statusText, fullWidthWrapContent());

        ScrollView scrollView = new ScrollView(this);
        scrollView.addView(content);
        return scrollView;
    }

    private LinearLayout.LayoutParams fullWidthWrapContent() {
        return new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private void openSettings(String action, int successMessage, boolean developmentPage) {
        Intent intent = new Intent(action);
        intent.addCategory(Intent.CATEGORY_DEFAULT);

        try {
            ResolveInfo resolved = getPackageManager().resolveActivity(intent, 0);
            if (resolved == null) {
                showFailure(R.string.no_settings_handler);
                return;
            }

            String resolvedClass = resolved.activityInfo == null
                    ? ""
                    : resolved.activityInfo.name;
            if (developmentPage
                    && resolvedClass.endsWith("DevelopmentSettingsDisabledActivity")) {
                statusText.setText(R.string.developer_mode_still_disabled);
            } else {
                statusText.setText(successMessage);
            }
            startActivity(intent);
        } catch (ActivityNotFoundException exception) {
            showFailure(R.string.no_settings_handler);
        } catch (SecurityException exception) {
            showFailure(R.string.settings_access_denied);
        } catch (RuntimeException exception) {
            showFailure(R.string.settings_open_failed);
        }
    }

    private void showFailure(int messageResource) {
        statusText.setText(messageResource);
        Toast.makeText(this, messageResource, Toast.LENGTH_LONG).show();
    }
}
