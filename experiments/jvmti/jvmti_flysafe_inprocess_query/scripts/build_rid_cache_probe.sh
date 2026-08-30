#!/bin/sh
set -eu
FINDUAS_PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
FINDUAS_NDK_ROOT=${FINDUAS_ANDROID_NDK_ROOT:?set FINDUAS_ANDROID_NDK_ROOT}
FINDUAS_NDK_HOST_TAG=${FINDUAS_NDK_HOST_TAG:-darwin-x86_64}
FINDUAS_CLANG="$FINDUAS_NDK_ROOT/toolchains/llvm/prebuilt/$FINDUAS_NDK_HOST_TAG/bin/armv7a-linux-androideabi30-clang"
FINDUAS_JVMTI_HEADER_DIR="$FINDUAS_PROJECT_ROOT/../jvmti_attach_canary/app/src/main/cpp/third_party/aosp_android_11_jvmti"
FINDUAS_OUTPUT_DIR="$FINDUAS_PROJECT_ROOT/build/rid-cache/armeabi-v7a"
FINDUAS_OUTPUT="$FINDUAS_OUTPUT_DIR/libfinduas_rid_cache.so"
test -x "$FINDUAS_CLANG"
test -f "$FINDUAS_JVMTI_HEADER_DIR/jvmti.h"
mkdir -p "$FINDUAS_OUTPUT_DIR"
"$FINDUAS_CLANG" -std=c11 -shared -fPIC -fvisibility=hidden -O2 -Wall -Wextra -Werror \
  -I"$FINDUAS_JVMTI_HEADER_DIR" "$FINDUAS_PROJECT_ROOT/src/native/art_ti_rid_cache_probe.c" \
  -llog -ldl -o "$FINDUAS_OUTPUT"
file "$FINDUAS_OUTPUT"
shasum -a 256 "$FINDUAS_OUTPUT"
