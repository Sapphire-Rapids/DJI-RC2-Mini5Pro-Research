#!/bin/sh
set -eu

FINDUAS_PROJECT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
FINDUAS_TEST_BUILD="$FINDUAS_PROJECT_ROOT/build/host-test"
FINDUAS_JAVA_HOME=${FINDUAS_JDK_ROOT:?set FINDUAS_JDK_ROOT to a JDK}

rm -rf "$FINDUAS_TEST_BUILD"
mkdir -p "$FINDUAS_TEST_BUILD"

"$FINDUAS_JAVA_HOME/bin/javac" --release 8 \
  -d "$FINDUAS_TEST_BUILD" \
  "$FINDUAS_PROJECT_ROOT/src/helper/com/finduas/rid/FlySafeLicenseGroupParser.java" \
  "$FINDUAS_PROJECT_ROOT/tests/com/finduas/rid/FlySafeLicenseGroupParserTest.java"

"$FINDUAS_JAVA_HOME/bin/java" \
  -cp "$FINDUAS_TEST_BUILD" \
  com.finduas.rid.FlySafeLicenseGroupParserTest
