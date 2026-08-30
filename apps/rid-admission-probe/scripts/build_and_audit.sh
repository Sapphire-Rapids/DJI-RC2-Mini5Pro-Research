#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
gradle_bin="${GRADLE_BIN:-$(command -v gradle || true)}"
java_runtime="${JAVA_HOME:-}"
android_sdk="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
artifact_source="$project_dir/app/build/outputs/apk/debug/app-debug.apk"
artifact_final="$project_dir/dist/FindUAS-RID-Bridge-Probe-0.11.0-report-export.apk"

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
test -f "$artifact_source"
mkdir -p "$project_dir/dist"
cp "$artifact_source" "$artifact_final"
python3 "$project_dir/scripts/audit_artifact.py" "$artifact_final"
python3 "$project_dir/scripts/test_audit_mutations.py" "$artifact_final"
