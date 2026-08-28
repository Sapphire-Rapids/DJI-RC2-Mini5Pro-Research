#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)

sdk_root=${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}
: "${sdk_root:?Set ANDROID_SDK_ROOT or ANDROID_HOME}"
ndk_root=${FINDUAS_CANARY_NDK_ROOT:-$sdk_root/ndk/27.2.12479018}
build_tools_root=${FINDUAS_CANARY_BUILD_TOOLS_ROOT:-$sdk_root/build-tools/35.0.0}
jdk_root=${FINDUAS_CANARY_JAVA_HOME:-${JAVA_HOME:-}}
: "${jdk_root:?Set FINDUAS_CANARY_JAVA_HOME or JAVA_HOME}"
gradle_bin=${FINDUAS_CANARY_GRADLE_BIN:-$(command -v gradle || true)}
: "${gradle_bin:?Set FINDUAS_CANARY_GRADLE_BIN or put gradle on PATH}"
debug_keystore=${FINDUAS_CANARY_KEYSTORE:-$HOME/.android/debug.keystore}
keystore_alias=${FINDUAS_CANARY_KEY_ALIAS:-androiddebugkey}
keystore_password=${FINDUAS_CANARY_KEYSTORE_PASSWORD:-android}
key_password=${FINDUAS_CANARY_KEY_PASSWORD:-android}

for required_path in \
    "$gradle_bin" \
    "$ndk_root/toolchains/llvm/prebuilt/darwin-x86_64/bin/llvm-readelf" \
    "$build_tools_root/apksigner" \
    "$build_tools_root/zipalign" \
    "$debug_keystore"; do
    if [ ! -e "$required_path" ]; then
        echo "Missing required build input: $required_path" >&2
        exit 1
    fi
done

export JAVA_HOME=$jdk_root
export ANDROID_HOME=$sdk_root
export ANDROID_SDK_ROOT=$sdk_root
export PATH="$JAVA_HOME/bin:$PATH"

"$gradle_bin" --no-daemon --project-dir "$project_dir" clean :app:assembleDebug

raw_apk="$project_dir/app/build/outputs/apk/debug/app-debug.apk"
package_stage="$project_dir/build/package-stage"
dist_dir="$project_dir/dist"
unsigned_apk="$package_stage/canary-no-dex-unsigned.apk"
aligned_apk="$package_stage/canary-no-dex-aligned.apk"
final_apk="$dist_dir/FindUAS-JVMTI-Attach-Canary-0.1.0-arm64-v8a.apk"

mkdir -p "$package_stage" "$dist_dir"
rm -f "$unsigned_apk" "$aligned_apk" "$final_apk"
cp "$raw_apk" "$unsigned_apk"

# AGP emits a generated, otherwise empty R class even though the manifest hasCode flag is false.
# Remove that build-only DEX before alignment and signing; the distributable carrier has no DEX.
if unzip -Z1 "$unsigned_apk" | grep -q '^classes[0-9]*\.dex$'; then
    zip -q -d "$unsigned_apk" 'classes*.dex'
fi

"$build_tools_root/zipalign" -f 4 "$unsigned_apk" "$aligned_apk"
"$build_tools_root/apksigner" sign \
    --ks "$debug_keystore" \
    --ks-key-alias "$keystore_alias" \
    --ks-pass "pass:$keystore_password" \
    --key-pass "pass:$key_password" \
    --v1-signing-enabled false \
    --v2-signing-enabled true \
    --v3-signing-enabled false \
    --v4-signing-enabled false \
    --out "$final_apk" \
    "$aligned_apk"

python3 "$script_dir/audit_artifact.py" "$final_apk"
shasum -a 256 "$final_apk"

echo "Built and audited: $final_apk"
