#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BUILD_DIR="$PROJECT_DIR/build"
SOURCE_DIR="$PROJECT_DIR/src/main/java"
ARTIFACT="$PROJECT_DIR/FindUAS-France-EID-GET-readonly.jar"

JAVA_HOME_VALUE=${JAVA_HOME:-}
ANDROID_SDK_VALUE=${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}
ANDROID_JAR="$ANDROID_SDK_VALUE/platforms/android-35/android.jar"
D8="$ANDROID_SDK_VALUE/build-tools/35.0.0/d8"
JAVAC="$JAVA_HOME_VALUE/bin/javac"

if [ -z "$JAVA_HOME_VALUE" ] || [ -z "$ANDROID_SDK_VALUE" ]; then
  echo "set JAVA_HOME and ANDROID_SDK_ROOT (or ANDROID_HOME)" >&2
  exit 1
fi

if [ ! -x "$JAVAC" ]; then
  echo "missing javac: $JAVAC" >&2
  exit 1
fi
if [ ! -x "$D8" ]; then
  echo "missing d8: $D8" >&2
  exit 1
fi
if [ ! -f "$ANDROID_JAR" ]; then
  echo "missing Android API jar: $ANDROID_JAR" >&2
  exit 1
fi

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/classes" "$BUILD_DIR/dex"

"$JAVAC" \
  -source 8 \
  -target 8 \
  -g:none \
  -Xlint:-options \
  -bootclasspath "$ANDROID_JAR" \
  -d "$BUILD_DIR/classes" \
  "$SOURCE_DIR/com/finduas/bridge/FranceEidGetMain.java"

find "$BUILD_DIR/classes" -type f -name '*.class' -exec touch -t 200801010000 {} +
(
  cd "$BUILD_DIR/classes"
  zip -X -q -r "$BUILD_DIR/program-classes.jar" .
)

JAVA_HOME="$JAVA_HOME_VALUE" "$D8" \
  --min-api 30 \
  --lib "$ANDROID_JAR" \
  --output "$BUILD_DIR/dex" \
  "$BUILD_DIR/program-classes.jar"

# Fixed timestamp plus zip -X makes the output reproducible across repeated builds.
touch -t 200801010000 "$BUILD_DIR/dex/classes.dex"
rm -f "$ARTIFACT"
(
  cd "$BUILD_DIR/dex"
  zip -X -q "$ARTIFACT" classes.dex
)

(cd "$PROJECT_DIR" && shasum -a 256 "$(basename "$ARTIFACT")" > SHA256SUMS)
echo "built: $ARTIFACT"
cat "$PROJECT_DIR/SHA256SUMS"
