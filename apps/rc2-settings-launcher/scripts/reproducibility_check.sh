#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
gradle_bin="${GRADLE_BIN:-$(command -v gradle || true)}"
java_runtime="${JAVA_HOME:-}"
android_sdk="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
temporary_root="$(mktemp -d "${TMPDIR:-/tmp}/finduas-rc2-settings-repro.XXXXXX")"
first_project="$temporary_root/first-project"
second_project="$temporary_root/second-project"
first="$temporary_root/repro-first.apk"
second="$temporary_root/repro-second.apk"

cleanup() {
    rm -rf "$temporary_root"
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
export JAVA_HOME="$java_runtime"
export ANDROID_HOME="$android_sdk"

for replica in "$first_project" "$second_project"; do
    mkdir -p "$replica"
    rsync -a \
        --exclude '.gradle/' \
        --exclude 'build/' \
        --exclude 'app/build/' \
        --exclude 'dist/' \
        "$project_dir/" "$replica/"
done

"$gradle_bin" --no-daemon --no-build-cache -p "$first_project" clean assembleDebug
cp "$first_project/app/build/outputs/apk/debug/app-debug.apk" "$first"
"$gradle_bin" --no-daemon --no-build-cache -p "$second_project" clean assembleDebug
cp "$second_project/app/build/outputs/apk/debug/app-debug.apk" "$second"

first_sha="$(shasum -a 256 "$first" | awk '{print $1}')"
second_sha="$(shasum -a 256 "$second" | awk '{print $1}')"
test "$first_sha" = "$second_sha"
cmp -s "$first" "$second"
python3 "$project_dir/scripts/audit_artifact.py" "$first"
python3 "$project_dir/scripts/audit_artifact.py" "$second"
echo "REPRODUCIBILITY PASS"
echo "sha256=$first_sha"
