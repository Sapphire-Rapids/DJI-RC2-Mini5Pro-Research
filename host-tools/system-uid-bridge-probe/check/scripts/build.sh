#!/usr/bin/env bash
set -euo pipefail

FINDUAS_CHECK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FINDUAS_BUILD_DIR="$FINDUAS_CHECK_ROOT/build"
FINDUAS_DIST_DIR="$FINDUAS_CHECK_ROOT/dist"
FINDUAS_CLASSES_DIR="$FINDUAS_BUILD_DIR/classes"
FINDUAS_DEX_DIR="$FINDUAS_BUILD_DIR/dex"
FINDUAS_SOURCE_DIR="$FINDUAS_CHECK_ROOT/src"

FINDUAS_JDK_HOME="${FINDUAS_JDK_HOME:-${JAVA_HOME:-}}"
FINDUAS_ANDROID_SDK="${FINDUAS_ANDROID_SDK:-${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}}"
FINDUAS_ANDROID_API="${FINDUAS_ANDROID_API:-35}"
FINDUAS_BUILD_TOOLS="${FINDUAS_BUILD_TOOLS:-35.0.0}"
FINDUAS_MIN_API="${FINDUAS_MIN_API:-30}"
FINDUAS_R8_JAR="${FINDUAS_R8_JAR:-}"

if [ -z "$FINDUAS_JDK_HOME" ] || [ -z "$FINDUAS_ANDROID_SDK" ] || [ -z "$FINDUAS_R8_JAR" ]; then
    echo "set JDK, Android SDK and FINDUAS_R8_JAR environment variables" >&2
    exit 1
fi

FINDUAS_JAVAC="$FINDUAS_JDK_HOME/bin/javac"
FINDUAS_JAVA="$FINDUAS_JDK_HOME/bin/java"
FINDUAS_ANDROID_JAR="$FINDUAS_ANDROID_SDK/platforms/android-$FINDUAS_ANDROID_API/android.jar"

for FINDUAS_REQUIRED_FILE in \
    "$FINDUAS_JAVAC" \
    "$FINDUAS_JAVA" \
    "$FINDUAS_ANDROID_JAR" \
    "$FINDUAS_R8_JAR"; do
    if [ ! -f "$FINDUAS_REQUIRED_FILE" ]; then
        echo "missing required build input: $FINDUAS_REQUIRED_FILE" >&2
        exit 1
    fi
done

rm -rf "$FINDUAS_BUILD_DIR"
mkdir -p "$FINDUAS_CLASSES_DIR" "$FINDUAS_DEX_DIR" "$FINDUAS_DIST_DIR"

FINDUAS_SOURCES=()
while IFS= read -r -d '' FINDUAS_SOURCE; do
    FINDUAS_SOURCES+=("$FINDUAS_SOURCE")
done < <(find "$FINDUAS_SOURCE_DIR" -type f -name '*.java' -print0 | sort -z)

if [ "${#FINDUAS_SOURCES[@]}" -eq 0 ]; then
    echo "no Java sources found" >&2
    exit 1
fi

"$FINDUAS_JAVAC" \
    --release 8 \
    -Xlint:-options \
    -classpath "$FINDUAS_ANDROID_JAR" \
    -d "$FINDUAS_CLASSES_DIR" \
    "${FINDUAS_SOURCES[@]}"

FINDUAS_CLASS_FILES=()
while IFS= read -r -d '' FINDUAS_CLASS_FILE; do
    FINDUAS_CLASS_FILES+=("$FINDUAS_CLASS_FILE")
done < <(find "$FINDUAS_CLASSES_DIR" -type f -name '*.class' -print0 | sort -z)

"$FINDUAS_JAVA" \
    -cp "$FINDUAS_R8_JAR" \
    com.android.tools.r8.D8 \
    --release \
    --min-api "$FINDUAS_MIN_API" \
    --lib "$FINDUAS_ANDROID_JAR" \
    --output "$FINDUAS_DEX_DIR" \
    "${FINDUAS_CLASS_FILES[@]}"

# ZIP timestamps are fixed so identical source/tool inputs produce the same JAR.
touch -t 198001010000 "$FINDUAS_DEX_DIR/classes.dex"
rm -f "$FINDUAS_DIST_DIR/finduas-protocol-check.jar"
(
    cd "$FINDUAS_DEX_DIR"
    /usr/bin/zip -X -q "$FINDUAS_DIST_DIR/finduas-protocol-check.jar" classes.dex
)

cp "$FINDUAS_CHECK_ROOT/runner/run-protocol-check.sh" \
    "$FINDUAS_DIST_DIR/run-protocol-check.sh"
chmod 0755 "$FINDUAS_DIST_DIR/run-protocol-check.sh"

"$FINDUAS_CHECK_ROOT/scripts/audit.sh" \
    | tee "$FINDUAS_DIST_DIR/STATIC_AUDIT.txt"

(
    cd "$FINDUAS_DIST_DIR"
    /usr/bin/shasum -a 256 \
        finduas-protocol-check.jar \
        run-protocol-check.sh \
        STATIC_AUDIT.txt \
        > SHA256SUMS
)

echo "build.result=PASS"
echo "build.jar=$FINDUAS_DIST_DIR/finduas-protocol-check.jar"
echo "build.runner=$FINDUAS_DIST_DIR/run-protocol-check.sh"
echo "build.hashes=$FINDUAS_DIST_DIR/SHA256SUMS"
