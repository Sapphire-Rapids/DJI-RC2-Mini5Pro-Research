#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)

sdk_root=${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}
: "${sdk_root:?Set ANDROID_SDK_ROOT or ANDROID_HOME}"
ndk_root=${FINDUAS_ROUTE_V21_NDK_ROOT:-$sdk_root/ndk/27.2.12479018}
build_tools_root=${FINDUAS_ROUTE_V21_BUILD_TOOLS_ROOT:-$sdk_root/build-tools/35.0.0}
jdk_root=${FINDUAS_ROUTE_V21_JAVA_HOME:-${JAVA_HOME:-}}
: "${jdk_root:?Set FINDUAS_ROUTE_V21_JAVA_HOME or JAVA_HOME}"
gradle_bin=${FINDUAS_ROUTE_V21_GRADLE_BIN:-$(command -v gradle || true)}
: "${gradle_bin:?Set FINDUAS_ROUTE_V21_GRADLE_BIN or put gradle on PATH}"
debug_keystore=${FINDUAS_ROUTE_V21_KEYSTORE:-$HOME/.android/debug.keystore}
keystore_alias=${FINDUAS_ROUTE_V21_KEY_ALIAS:-androiddebugkey}
keystore_password=${FINDUAS_ROUTE_V21_KEYSTORE_PASSWORD:-android}
key_password=${FINDUAS_ROUTE_V21_KEY_PASSWORD:-android}
inspection_mirror=$project_dir/build/inspect.so
inspection_mirror_tmp=$project_dir/build/.inspect.so.tmp

rm -f -- "$inspection_mirror" "$inspection_mirror_tmp"
trap 'rm -f -- "$inspection_mirror_tmp"' EXIT HUP INT TERM

for required_path in \
    "$gradle_bin" \
    "$ndk_root/toolchains/llvm/prebuilt/darwin-x86_64/bin/llvm-readelf" \
    "$build_tools_root/apksigner" \
    "$build_tools_root/zipalign" \
    "$debug_keystore" \
    "$jdk_root/bin/java"; do
    if [ ! -e "$required_path" ]; then
        echo "Missing required build input: $required_path" >&2
        exit 1
    fi
done

export JAVA_HOME=$jdk_root
export ANDROID_HOME=$sdk_root
export ANDROID_SDK_ROOT=$sdk_root
export PATH="$JAVA_HOME/bin:$PATH"

sh "$script_dir/run_host_tests.sh"
"$gradle_bin" --no-daemon --project-dir "$project_dir" clean :app:assembleDebug

raw_apk=$project_dir/app/build/outputs/apk/debug/app-debug.apk
package_stage=$project_dir/build/package-stage
dist_dir=$project_dir/dist
unsigned_apk=$package_stage/route-v21-no-dex-unsigned.apk
aligned_apk=$package_stage/route-v21-no-dex-aligned.apk
final_apk=$dist_dir/FindUAS-JVMTI-EID-Route-Resolver-V2.1-0.1.0-offline-unadmitted-arm64-v8a.apk
native_entry=lib/arm64-v8a/libfinduas_eid_route_resolver_v2_1.so

mkdir -p "$package_stage" "$dist_dir"
rm -f -- "$unsigned_apk" "$aligned_apk" "$final_apk"
cp "$raw_apk" "$unsigned_apk"

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

unzip -p "$final_apk" "$native_entry" > "$inspection_mirror_tmp"
mv -f -- "$inspection_mirror_tmp" "$inspection_mirror"

python3 "$script_dir/audit_artifact.py" "$final_apk"
shasum -a 256 "$final_apk" "$inspection_mirror"

trap - EXIT HUP INT TERM
echo "Built and audited: $final_apk"
