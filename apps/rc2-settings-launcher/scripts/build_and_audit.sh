#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
gradle_bin="${GRADLE_BIN:-$(command -v gradle || true)}"
java_runtime="${JAVA_HOME:-}"
android_sdk="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
source_apk="$project_dir/app/build/outputs/apk/debug/app-debug.apk"
final_apk="$project_dir/dist/FindUAS-RC2-Settings-Launcher-1.0.0.apk"

test -n "$gradle_bin" && test -x "$gradle_bin" || {
    printf '%s\n' "Set GRADLE_BIN or put Gradle 8.10.2 on PATH." >&2
    exit 2
}
test -n "$java_runtime" && test -x "$java_runtime/bin/java" || {
    printf '%s\n' "Set JAVA_HOME to a JDK 21 installation." >&2
    exit 2
}
test -n "$android_sdk" && test -d "$android_sdk" || {
    printf '%s\n' "Set ANDROID_HOME or ANDROID_SDK_ROOT to Android SDK 35." >&2
    exit 2
}
export JAVA_HOME="$java_runtime"
export ANDROID_HOME="$android_sdk"

cd "$project_dir"
"$gradle_bin" --no-daemon clean testDebugUnitTest lintDebug assembleDebug
test -f "$source_apk"
mkdir -p "$project_dir/dist"
cp "$source_apk" "$final_apk"
python3 "$project_dir/scripts/audit_artifact.py" "$final_apk"
