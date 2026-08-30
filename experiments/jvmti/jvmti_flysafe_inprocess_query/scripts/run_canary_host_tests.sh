#!/bin/sh
set -eu

FINDUAS_PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
FINDUAS_JAVA_HOME=${FINDUAS_JDK_ROOT:?set FINDUAS_JDK_ROOT to a host JDK}
FINDUAS_HOST_CC=${FINDUAS_HOST_CC:-cc}
case "$(uname -s)" in
  Darwin) FINDUAS_JNI_PLATFORM=darwin ;;
  Linux) FINDUAS_JNI_PLATFORM=linux ;;
  *) printf 'Unsupported host JNI platform\n' >&2; exit 2 ;;
esac
FINDUAS_JVMTI_HEADER_DIR="$FINDUAS_PROJECT_ROOT/../jvmti_attach_canary/app/src/main/cpp/third_party/aosp_android_11_jvmti"
test -f "$FINDUAS_JAVA_HOME/include/jni.h"
test -f "$FINDUAS_JAVA_HOME/include/$FINDUAS_JNI_PLATFORM/jni_md.h"

mkdir -p "$FINDUAS_PROJECT_ROOT/build"
FINDUAS_TEST_BUILD=$(mktemp -d "$FINDUAS_PROJECT_ROOT/build/host-canary-test.XXXXXX")
trap 'rm -rf "$FINDUAS_TEST_BUILD"' 0
trap 'exit 1' HUP INT TERM

"$FINDUAS_HOST_CC" -std=c11 -O2 -Wall -Wextra -Werror \
  -I"$FINDUAS_PROJECT_ROOT/tests/native/include" \
  -I"$FINDUAS_JAVA_HOME/include" \
  -I"$FINDUAS_JAVA_HOME/include/$FINDUAS_JNI_PLATFORM" \
  -I"$FINDUAS_JVMTI_HEADER_DIR" \
  "$FINDUAS_PROJECT_ROOT/src/native/art_ti_canary.c" \
  "$FINDUAS_PROJECT_ROOT/tests/native/art_ti_canary_test.c" \
  -o "$FINDUAS_TEST_BUILD/art_ti_canary_test"

"$FINDUAS_TEST_BUILD/art_ti_canary_test"
