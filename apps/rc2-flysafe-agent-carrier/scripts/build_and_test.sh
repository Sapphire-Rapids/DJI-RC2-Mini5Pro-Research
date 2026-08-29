#!/bin/sh
set -eu

FINDUAS_PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
FINDUAS_REPOSITORY_ROOT=$(CDPATH= cd -- "$FINDUAS_PROJECT_ROOT/../.." && pwd)
FINDUAS_AGENT_ROOT="$FINDUAS_REPOSITORY_ROOT/experiments/jvmti/jvmti_flysafe_inprocess_query"
FINDUAS_ANDROID_SDK=${FINDUAS_ANDROID_SDK_ROOT:?set FINDUAS_ANDROID_SDK_ROOT}
FINDUAS_JAVA_HOME=${FINDUAS_JDK_ROOT:?set FINDUAS_JDK_ROOT}
FINDUAS_NDK_ROOT=${FINDUAS_ANDROID_NDK_ROOT:?set FINDUAS_ANDROID_NDK_ROOT}
FINDUAS_GRADLE=${FINDUAS_GRADLE_BIN:?set FINDUAS_GRADLE_BIN}
FINDUAS_JNI_ROOT="$FINDUAS_PROJECT_ROOT/app/build/generated/jniLibs/arm64-v8a"

export ANDROID_HOME="$FINDUAS_ANDROID_SDK"
export JAVA_HOME="$FINDUAS_JAVA_HOME"

(
  cd "$FINDUAS_PROJECT_ROOT"
  "$FINDUAS_GRADLE" --no-daemon clean
)

(
  cd "$FINDUAS_AGENT_ROOT"
  sh scripts/run_host_tests.sh
  sh scripts/build.sh
)

mkdir -p "$FINDUAS_JNI_ROOT"
cp \
  "$FINDUAS_AGENT_ROOT/build/out/libfinduas_flysafe_query.so" \
  "$FINDUAS_JNI_ROOT/libfinduas_flysafe_query.so"

(
  cd "$FINDUAS_PROJECT_ROOT"
  "$FINDUAS_GRADLE" --no-daemon testDebugUnitTest lintDebug assembleDebug
)
