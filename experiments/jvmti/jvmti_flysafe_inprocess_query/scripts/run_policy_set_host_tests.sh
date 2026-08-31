#!/bin/sh
set -eu
FINDUAS_PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
FINDUAS_JDK_ROOT=${FINDUAS_JDK_ROOT:-${JAVA_HOME:-}}
if [ -z "$FINDUAS_JDK_ROOT" ]; then
  FINDUAS_JDK_ROOT=$(dirname "$(dirname "$(readlink -f "$(command -v javac)")")")
fi
FINDUAS_OS=$(uname -s | tr '[:upper:]' '[:lower:]')
FINDUAS_BUILD="$FINDUAS_PROJECT_ROOT/build/policy-set-host-tests"
mkdir -p "$FINDUAS_BUILD"
${CC:-cc} -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I"$FINDUAS_JDK_ROOT/include" -I"$FINDUAS_JDK_ROOT/include/$FINDUAS_OS" \
  -I"$FINDUAS_PROJECT_ROOT/src/native" \
  -I"$FINDUAS_PROJECT_ROOT/tests/native/include" \
  -I"$FINDUAS_PROJECT_ROOT/../jvmti_attach_canary/app/src/main/cpp/third_party/aosp_android_11_jvmti" \
  "$FINDUAS_PROJECT_ROOT/tests/native/art_ti_policy_set_probe_test.c" "$FINDUAS_PROJECT_ROOT/src/native/global_payload_extract.c" -o "$FINDUAS_BUILD/test"
"$FINDUAS_BUILD/test"

${CC:-cc} -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I"$FINDUAS_PROJECT_ROOT/src/native" \
  "$FINDUAS_PROJECT_ROOT/tests/native/global_payload_extract_test.c" -o "$FINDUAS_BUILD/payload-test"
"$FINDUAS_BUILD/payload-test"

${CC:-cc} -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I"$FINDUAS_JDK_ROOT/include" -I"$FINDUAS_JDK_ROOT/include/$FINDUAS_OS" \
  -I"$FINDUAS_PROJECT_ROOT/src/native" \
  "$FINDUAS_PROJECT_ROOT/tests/native/mediastore_policyset_sink_test.c" \
  "$FINDUAS_PROJECT_ROOT/src/native/mediastore_policyset_sink.c" -o "$FINDUAS_BUILD/storage-test"
"$FINDUAS_BUILD/storage-test"
