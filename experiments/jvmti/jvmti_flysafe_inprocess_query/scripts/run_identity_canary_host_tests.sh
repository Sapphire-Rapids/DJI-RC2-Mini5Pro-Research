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
FINDUAS_TEST_BUILD=$(mktemp -d "$FINDUAS_PROJECT_ROOT/build/host-identity-test.XXXXXX")
trap 'rm -rf "$FINDUAS_TEST_BUILD"' 0
trap 'exit 1' HUP INT TERM

# Only the production translation unit gets fixed self-I/O substitutes. Each
# case runs in a fresh host child; production has no test-reset entry point.
"$FINDUAS_HOST_CC" -std=c11 -D_POSIX_C_SOURCE=200809L -O2 -Wall -Wextra -Werror \
  -I"$FINDUAS_PROJECT_ROOT/tests/native/include" \
  -I"$FINDUAS_JAVA_HOME/include" \
  -I"$FINDUAS_JAVA_HOME/include/$FINDUAS_JNI_PLATFORM" \
  -I"$FINDUAS_JVMTI_HEADER_DIR" \
  -include "$FINDUAS_PROJECT_ROOT/tests/native/include/identity_test_hooks.h" \
  -c "$FINDUAS_PROJECT_ROOT/src/native/art_ti_identity_canary.c" \
  -o "$FINDUAS_TEST_BUILD/identity.o"

"$FINDUAS_HOST_CC" -std=c11 -D_POSIX_C_SOURCE=200809L -O2 -Wall -Wextra -Werror \
  -I"$FINDUAS_PROJECT_ROOT/tests/native/include" \
  -I"$FINDUAS_JAVA_HOME/include" \
  -I"$FINDUAS_JAVA_HOME/include/$FINDUAS_JNI_PLATFORM" \
  -I"$FINDUAS_JVMTI_HEADER_DIR" \
  "$FINDUAS_PROJECT_ROOT/tests/native/art_ti_identity_canary_test.c" \
  "$FINDUAS_TEST_BUILD/identity.o" -o "$FINDUAS_TEST_BUILD/identity_test"

"$FINDUAS_TEST_BUILD/identity_test"
