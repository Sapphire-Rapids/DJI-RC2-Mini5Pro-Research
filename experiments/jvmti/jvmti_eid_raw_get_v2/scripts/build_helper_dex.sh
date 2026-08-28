#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)

sdk_root=${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}
: "${sdk_root:?Set ANDROID_SDK_ROOT or ANDROID_HOME}"
build_tools_root=${FINDUAS_V2_BUILD_TOOLS_ROOT:-$sdk_root/build-tools/35.0.0}
jdk_root=${FINDUAS_V2_JAVA_HOME:-${JAVA_HOME:-}}
: "${jdk_root:?Set FINDUAS_V2_JAVA_HOME or JAVA_HOME}"

javac_bin=$jdk_root/bin/javac
d8_bin=$build_tools_root/d8
android_jar=$sdk_root/platforms/android-35/android.jar

for required_path in "$javac_bin" "$d8_bin" "$android_jar"; do
    if [ ! -e "$required_path" ]; then
        echo "Missing helper build input: $required_path" >&2
        exit 1
    fi
done

generated_dir=$project_dir/build/generated
helper_output_dir=$project_dir/build/helper
stage_dir=$(mktemp -d "$project_dir/build/helper-stage.XXXXXX")
trap 'rm -rf "$stage_dir"' EXIT HUP INT TERM

stub_classes=$stage_dir/stub-classes
helper_classes=$stage_dir/helper-classes
dex_output=$stage_dir/dex-output
mkdir -p "$stub_classes" "$helper_classes" "$dex_output" "$generated_dir" "$helper_output_dir"

"$javac_bin" \
    -encoding UTF-8 \
    -source 8 \
    -target 8 \
    -g:none \
    -d "$stub_classes" \
    "$project_dir/helper/stubs/uav/jni/JNIProguardKeepTag.java" \
    "$project_dir/helper/stubs/uav/raw/jni/callback/SendInterface.java"

"$javac_bin" \
    -encoding UTF-8 \
    -source 8 \
    -target 8 \
    -g:none \
    -classpath "$stub_classes" \
    -d "$helper_classes" \
    "$project_dir/helper/src/main/java/com/finduas/ridv2/RawCallback.java"

"$d8_bin" \
    --release \
    --min-api 30 \
    --lib "$android_jar" \
    --classpath "$stub_classes" \
    --output "$dex_output" \
    "$helper_classes/com/finduas/ridv2/RawCallback.class"

cp "$dex_output/classes.dex" "$helper_output_dir/classes.dex"
python3 "$script_dir/embed_helper_dex.py" \
    "$helper_output_dir/classes.dex" \
    "$generated_dir/helper_dex.inc"

shasum -a 256 "$helper_output_dir/classes.dex"
