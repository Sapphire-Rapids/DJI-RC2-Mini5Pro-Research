#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BUILD_DIR="$PROJECT_DIR/build"
ARTIFACT="$PROJECT_DIR/FindUAS-France-EID-GET-readonly.jar"
SOURCE="$PROJECT_DIR/src/main/java/com/finduas/bridge/FranceEidGetMain.java"

JAVA_HOME_VALUE=${JAVA_HOME:-}
ANDROID_SDK_VALUE=${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}
DEXDUMP="$ANDROID_SDK_VALUE/build-tools/35.0.0/dexdump"
JADX=${JADX:-$(command -v jadx || true)}
PYTHON=${PYTHON:-/usr/bin/python3}

if [ -z "$JAVA_HOME_VALUE" ] || [ -z "$ANDROID_SDK_VALUE" ] || [ -z "$JADX" ]; then
  echo "set JAVA_HOME, ANDROID_SDK_ROOT (or ANDROID_HOME), and JADX (or put jadx on PATH)" >&2
  exit 1
fi

"$PROJECT_DIR/build.sh"

mkdir -p "$BUILD_DIR/audit"
unzip -p "$ARTIFACT" classes.dex > "$BUILD_DIR/audit/classes.dex"
"$DEXDUMP" -c "$BUILD_DIR/audit/classes.dex"
"$DEXDUMP" -d "$BUILD_DIR/audit/classes.dex" > "$BUILD_DIR/audit/dexdump.txt"

rm -rf "$BUILD_DIR/audit/jadx"
JAVA_HOME="$JAVA_HOME_VALUE" "$JADX" \
  --show-bad-code \
  --no-res \
  -d "$BUILD_DIR/audit/jadx" \
  "$ARTIFACT" >/dev/null

"$PYTHON" "$PROJECT_DIR/tests/test_source_contract.py"

# Artifact-level capability denylist. These strings must not occur in DEX or JADX output.
if rg -n -i \
  'java/net|socket|inetaddress|outputstream|fileoutputstream|randomaccessfile|processbuilder|runtime;->exec|startactivity|setprop|127\.0\.0\.1|40007|40009' \
  "$BUILD_DIR/audit/dexdump.txt" "$BUILD_DIR/audit/jadx"; then
  echo "forbidden capability found in built artifact" >&2
  exit 1
fi

# The program owns only its namespace and does not bundle DJI framework replicas.
if rg -n "Class descriptor.*Lcom/dji/" "$BUILD_DIR/audit/dexdump.txt"; then
  echo "unexpected bundled DJI class" >&2
  exit 1
fi

CLASS_COUNT=$(rg -c "Class descriptor" "$BUILD_DIR/audit/dexdump.txt")
TRANSACT_CALL_COUNT=$(rg -c "Landroid/os/IBinder;\.transact:" "$BUILD_DIR/audit/dexdump.txt")
if [ "$CLASS_COUNT" -ne 3 ]; then
  echo "unexpected DEX class count: $CLASS_COUNT" >&2
  exit 1
fi
if [ "$TRANSACT_CALL_COUNT" -ne 1 ]; then
  echo "unexpected outbound IBinder.transact callsite count: $TRANSACT_CALL_COUNT" >&2
  exit 1
fi

shasum -a 256 "$ARTIFACT" "$PROJECT_DIR/runner/run-france-eid-get-readonly.sh"
echo "audit passed"
