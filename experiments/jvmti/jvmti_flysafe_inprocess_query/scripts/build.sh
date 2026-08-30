#!/bin/sh
set -eu

FINDUAS_PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
FINDUAS_BUILD_ROOT="$FINDUAS_PROJECT_ROOT/build"
FINDUAS_ANDROID_SDK=${FINDUAS_ANDROID_SDK_ROOT:?set FINDUAS_ANDROID_SDK_ROOT}
FINDUAS_JAVA_HOME=${FINDUAS_JDK_ROOT:?set FINDUAS_JDK_ROOT}
FINDUAS_NDK_ROOT=${FINDUAS_ANDROID_NDK_ROOT:?set FINDUAS_ANDROID_NDK_ROOT}
FINDUAS_BUILD_TOOLS=${FINDUAS_BUILD_TOOLS_VERSION:-35.0.0}
FINDUAS_NDK_HOST_TAG=${FINDUAS_NDK_HOST_TAG:-darwin-x86_64}
FINDUAS_ANDROID_ABI=${FINDUAS_ANDROID_ABI:-arm64-v8a}
FINDUAS_D8_JAR="$FINDUAS_ANDROID_SDK/build-tools/$FINDUAS_BUILD_TOOLS/lib/d8.jar"
case "$FINDUAS_ANDROID_ABI" in
  arm64-v8a) FINDUAS_TARGET_COMPILER=aarch64-linux-android30-clang ;;
  armeabi-v7a) FINDUAS_TARGET_COMPILER=armv7a-linux-androideabi30-clang ;;
  *) printf 'Unsupported Android ABI: %s\n' "$FINDUAS_ANDROID_ABI" >&2; exit 2 ;;
esac
FINDUAS_CLANG="$FINDUAS_NDK_ROOT/toolchains/llvm/prebuilt/$FINDUAS_NDK_HOST_TAG/bin/$FINDUAS_TARGET_COMPILER"
FINDUAS_JVMTI_HEADER_DIR="$FINDUAS_PROJECT_ROOT/../jvmti_attach_canary/app/src/main/cpp/third_party/aosp_android_11_jvmti"

rm -rf "$FINDUAS_BUILD_ROOT"
mkdir -p \
  "$FINDUAS_BUILD_ROOT/stub" \
  "$FINDUAS_BUILD_ROOT/helper" \
  "$FINDUAS_BUILD_ROOT/dex" \
  "$FINDUAS_BUILD_ROOT/generated" \
  "$FINDUAS_BUILD_ROOT/out"

"$FINDUAS_JAVA_HOME/bin/javac" --release 8 \
  -d "$FINDUAS_BUILD_ROOT/stub" \
  "$FINDUAS_PROJECT_ROOT/src/stub/uav/component/flightrestrict/listener/JNIUnlockCommonCallbacks.java"

"$FINDUAS_JAVA_HOME/bin/javac" --release 8 \
  -cp "$FINDUAS_BUILD_ROOT/stub" \
  -d "$FINDUAS_BUILD_ROOT/helper" \
  "$FINDUAS_PROJECT_ROOT/src/helper/com/finduas/rid/FlySafeLicenseGroupParser.java" \
  "$FINDUAS_PROJECT_ROOT/src/helper/com/finduas/rid/FlySafeRawCallback.java"

find "$FINDUAS_BUILD_ROOT/helper" -name '*.class' -print > "$FINDUAS_BUILD_ROOT/helper-classes.txt"
"$FINDUAS_JAVA_HOME/bin/java" \
  -cp "$FINDUAS_D8_JAR" \
  com.android.tools.r8.D8 \
  --min-api 30 \
  --output "$FINDUAS_BUILD_ROOT/dex" \
  $(cat "$FINDUAS_BUILD_ROOT/helper-classes.txt")

(
  cd "$FINDUAS_PROJECT_ROOT"
  xxd -i build/dex/classes.dex > build/generated/helper_dex.inc
)

"$FINDUAS_CLANG" \
  -shared -fPIC -fvisibility=hidden -O2 -Wall -Wextra -Werror \
  -I"$FINDUAS_JVMTI_HEADER_DIR" \
  -I"$FINDUAS_BUILD_ROOT/generated" \
  "$FINDUAS_PROJECT_ROOT/src/native/agent.c" \
  -llog \
  -o "$FINDUAS_BUILD_ROOT/out/libfinduas_flysafe_query.so"

file "$FINDUAS_BUILD_ROOT/out/libfinduas_flysafe_query.so"
shasum -a 256 \
  "$FINDUAS_BUILD_ROOT/dex/classes.dex" \
  "$FINDUAS_BUILD_ROOT/out/libfinduas_flysafe_query.so"
