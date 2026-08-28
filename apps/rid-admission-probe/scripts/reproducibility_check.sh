#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
gradle_bin="${GRADLE_BIN:-$(command -v gradle || true)}"
java_runtime="${JAVA_HOME:-}"
android_sdk="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
built_apk="$project_dir/app/build/outputs/apk/debug/app-debug.apk"
published_apk="$project_dir/dist/FindUAS-RID-Bridge-Probe-0.10.0-research.apk"
task_tmp="$(mktemp -d "${TMPDIR:-/tmp}/finduas-rid-v010-repro.XXXXXX")"

cleanup() {
    case "$task_tmp" in
        "${TMPDIR:-/tmp}"/finduas-rid-v010-repro.*) rm -rf -- "$task_tmp" ;;
        *) printf '%s\n' "refusing to remove unexpected temporary path: $task_tmp" >&2 ;;
    esac
}
trap cleanup EXIT

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
test -f "$published_apk"
export JAVA_HOME="$java_runtime"
export ANDROID_HOME="$android_sdk"

cd "$project_dir"
"$gradle_bin" --no-daemon clean assembleDebug
cp "$built_apk" "$task_tmp/build-1.apk"
"$gradle_bin" --no-daemon clean assembleDebug
cp "$built_apk" "$task_tmp/build-2.apk"
cmp "$task_tmp/build-1.apk" "$task_tmp/build-2.apk"
cmp "$task_tmp/build-1.apk" "$published_apk"
python3 "$project_dir/scripts/audit_artifact.py" "$task_tmp/build-1.apk"
python3 "$project_dir/scripts/audit_artifact.py" "$task_tmp/build-2.apk"
python3 "$project_dir/scripts/test_audit_mutations.py" "$task_tmp/build-1.apk"
python3 "$project_dir/scripts/test_audit_mutations.py" "$task_tmp/build-2.apk"
first_sha="$(shasum -a 256 "$task_tmp/build-1.apk" | awk '{print $1}')"
second_sha="$(shasum -a 256 "$task_tmp/build-2.apk" | awk '{print $1}')"
test "$first_sha" = "$second_sha"
printf '%s\n' "REPRODUCIBLE_PASS" "build_1_sha256=$first_sha" "build_2_sha256=$second_sha"
