#!/bin/sh
set -eu

FINDUAS_PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
FINDUAS_NDK_ROOT=${FINDUAS_ANDROID_NDK_ROOT:?set FINDUAS_ANDROID_NDK_ROOT}
FINDUAS_NDK_HOST_TAG=${FINDUAS_NDK_HOST_TAG:-darwin-x86_64}
FINDUAS_ANDROID_ABI=${FINDUAS_ANDROID_ABI:-armeabi-v7a}
case "$FINDUAS_ANDROID_ABI" in
  armeabi-v7a) FINDUAS_TARGET_COMPILER=armv7a-linux-androideabi30-clang ;;
  arm64-v8a) FINDUAS_TARGET_COMPILER=aarch64-linux-android30-clang ;;
  *) printf 'Unsupported Android ABI: %s\n' "$FINDUAS_ANDROID_ABI" >&2; exit 2 ;;
esac
FINDUAS_CLANG="$FINDUAS_NDK_ROOT/toolchains/llvm/prebuilt/$FINDUAS_NDK_HOST_TAG/bin/$FINDUAS_TARGET_COMPILER"
FINDUAS_JVMTI_HEADER_DIR="$FINDUAS_PROJECT_ROOT/../jvmti_attach_canary/app/src/main/cpp/third_party/aosp_android_11_jvmti"
FINDUAS_OUTPUT_DIR="$FINDUAS_PROJECT_ROOT/build/canary/$FINDUAS_ANDROID_ABI"
FINDUAS_OUTPUT="$FINDUAS_OUTPUT_DIR/libfinduas_artti_canary.so"

mkdir -p "$FINDUAS_OUTPUT_DIR"
"$FINDUAS_CLANG" \
  -shared -fPIC -fvisibility=hidden -O2 -Wall -Wextra -Werror \
  -I"$FINDUAS_JVMTI_HEADER_DIR" \
  "$FINDUAS_PROJECT_ROOT/src/native/art_ti_canary.c" \
  -llog -o "$FINDUAS_OUTPUT"

file "$FINDUAS_OUTPUT"
shasum -a 256 "$FINDUAS_OUTPUT"
