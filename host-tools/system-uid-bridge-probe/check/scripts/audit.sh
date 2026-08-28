#!/usr/bin/env bash
set -euo pipefail

FINDUAS_CHECK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FINDUAS_SOURCE="$FINDUAS_CHECK_ROOT/src/com/finduas/systemuidbridge/check/ProtocolServiceCheck.java"
FINDUAS_JAR="$FINDUAS_CHECK_ROOT/dist/finduas-protocol-check.jar"
FINDUAS_RUNNER="$FINDUAS_CHECK_ROOT/dist/run-protocol-check.sh"
FINDUAS_ANDROID_SDK="${FINDUAS_ANDROID_SDK:-${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}}"
FINDUAS_BUILD_TOOLS="${FINDUAS_BUILD_TOOLS:-35.0.0}"
FINDUAS_DEXDUMP="$FINDUAS_ANDROID_SDK/build-tools/$FINDUAS_BUILD_TOOLS/dexdump"
FINDUAS_JDK_HOME="${FINDUAS_JDK_HOME:-${JAVA_HOME:-}}"
FINDUAS_JAVA="$FINDUAS_JDK_HOME/bin/java"
FINDUAS_JADX_JAR="${FINDUAS_JADX_JAR:-}"
FINDUAS_RG="${FINDUAS_RG:-$(command -v rg || true)}"

if [ -z "$FINDUAS_JDK_HOME" ] || [ -z "$FINDUAS_ANDROID_SDK" ] || [ -z "$FINDUAS_JADX_JAR" ]; then
    echo "set JDK, Android SDK and FINDUAS_JADX_JAR environment variables" >&2
    exit 1
fi

for FINDUAS_REQUIRED_FILE in \
    "$FINDUAS_SOURCE" \
    "$FINDUAS_JAR" \
    "$FINDUAS_RUNNER" \
    "$FINDUAS_DEXDUMP" \
    "$FINDUAS_JAVA" \
    "$FINDUAS_JADX_JAR" \
    "$FINDUAS_RG"; do
    if [ ! -f "$FINDUAS_REQUIRED_FILE" ]; then
        echo "missing required audit input: $FINDUAS_REQUIRED_FILE" >&2
        exit 1
    fi
done

FINDUAS_AUDIT_TMP="$(mktemp -d)"
trap 'rm -rf "$FINDUAS_AUDIT_TMP"' EXIT

FINDUAS_JAR_ENTRIES="$(/usr/bin/unzip -Z1 "$FINDUAS_JAR")"
if [ "$FINDUAS_JAR_ENTRIES" != "classes.dex" ]; then
    echo "unexpected JAR entries:" >&2
    echo "$FINDUAS_JAR_ENTRIES" >&2
    exit 1
fi

/usr/bin/unzip -qq "$FINDUAS_JAR" -d "$FINDUAS_AUDIT_TMP/unpacked"
"$FINDUAS_DEXDUMP" -d "$FINDUAS_AUDIT_TMP/unpacked/classes.dex" \
    > "$FINDUAS_AUDIT_TMP/dexdump.txt"
"$FINDUAS_JAVA" -cp "$FINDUAS_JADX_JAR" jadx.cli.JadxCLI \
    --quiet \
    --no-res \
    --output-dir "$FINDUAS_AUDIT_TMP/jadx" \
    "$FINDUAS_JAR"

FINDUAS_DECOMPILED="$FINDUAS_AUDIT_TMP/jadx/sources/com/finduas/systemuidbridge/check/ProtocolServiceCheck.java"
if [ ! -f "$FINDUAS_DECOMPILED" ]; then
    echo "JADX did not produce the expected source" >&2
    exit 1
fi

for FINDUAS_REQUIRED_STRING in \
    'android.os.ServiceManager' \
    'checkService' \
    'protocol' \
    'com.dji.protocol.IProtocolManager' \
    'WRONG_UID' \
    'DESCRIPTOR_MISMATCH' \
    'TRANSPORT_ENABLED' \
    'TRANSPORT_DISABLED'; do
    if ! /usr/bin/strings "$FINDUAS_AUDIT_TMP/unpacked/classes.dex" \
        | "$FINDUAS_RG" -F -q "$FINDUAS_REQUIRED_STRING"; then
        echo "missing required DEX string: $FINDUAS_REQUIRED_STRING" >&2
        exit 1
    fi
done

FINDUAS_FORBIDDEN_PATTERNS=(
    'java.net'
    'Socket'
    'InetSocketAddress'
    'getInputStream'
    'getOutputStream'
    '127.0.0.1'
    '40007'
    '40009'
    'sendWithListen'
    'addPackListener'
    'removePackListener'
    'FileOutputStream'
    'SystemProperties'
    'android.provider.Settings'
    'Runtime.getRuntime'
    'ProcessBuilder'
    'dji.midware'
    'DUML'
)

for FINDUAS_FORBIDDEN in "${FINDUAS_FORBIDDEN_PATTERNS[@]}"; do
    if "$FINDUAS_RG" \
        -F -q "$FINDUAS_FORBIDDEN" \
        "$FINDUAS_SOURCE" \
        "$FINDUAS_DECOMPILED" \
        "$FINDUAS_AUDIT_TMP/dexdump.txt"; then
        echo "forbidden capability found: $FINDUAS_FORBIDDEN" >&2
        exit 1
    fi
done

FINDUAS_SOURCE_TRANSACTS="$("$FINDUAS_RG" -o '\.transact\(' "$FINDUAS_SOURCE" | wc -l | tr -d ' ')"
FINDUAS_DECOMPILED_TRANSACTS="$("$FINDUAS_RG" -o '\.transact\(' "$FINDUAS_DECOMPILED" | wc -l | tr -d ' ')"
FINDUAS_DEX_TRANSACTS="$("$FINDUAS_RG" -c 'invoke-interface.*Landroid/os/IBinder;\.transact:' "$FINDUAS_AUDIT_TMP/dexdump.txt" || true)"

if [ "$FINDUAS_SOURCE_TRANSACTS" != "1" ]; then
    echo "source must contain exactly one Binder transact call" >&2
    exit 1
fi
if [ "$FINDUAS_DECOMPILED_TRANSACTS" != "1" ]; then
    echo "decompiled DEX must contain exactly one Binder transact call" >&2
    exit 1
fi
if [ "$FINDUAS_DEX_TRANSACTS" != "1" ]; then
    echo "DEX must contain exactly one IBinder.transact instruction" >&2
    exit 1
fi

if ! "$FINDUAS_RG" \
    -q 'TRANSACTION_IS_ENABLE = 1;' "$FINDUAS_SOURCE"; then
    echo "source does not pin transaction 1" >&2
    exit 1
fi
if ! "$FINDUAS_RG" -q 'Process\.myUid\(\) != SYSTEM_UID' "$FINDUAS_SOURCE"; then
    echo "source does not fail closed outside UID 1000" >&2
    exit 1
fi
if ! "$FINDUAS_RG" -q 'getInterfaceDescriptor\(\)' "$FINDUAS_SOURCE"; then
    echo "source does not verify the Binder descriptor" >&2
    exit 1
fi
if ! "$FINDUAS_RG" \
    -q 'TRANSACTION_IS_ENABLE = 1;' "$FINDUAS_DECOMPILED"; then
    echo "decompiled DEX does not pin transaction 1" >&2
    exit 1
fi
if ! "$FINDUAS_RG" \
    -q 'SYNCHRONOUS_FLAGS = 0;' "$FINDUAS_DECOMPILED"; then
    echo "decompiled DEX does not pin synchronous Binder flags" >&2
    exit 1
fi
if ! "$FINDUAS_RG" \
    -q '\.transact\(TRANSACTION_IS_ENABLE, [^,]+, [^,]+, SYNCHRONOUS_FLAGS\)' "$FINDUAS_DECOMPILED"; then
    echo "decompiled DEX does not show synchronous transaction 1" >&2
    exit 1
fi

if "$FINDUAS_RG" \
    -q 'eval|\$@|sh -c|su |adb |Runtime|ProcessBuilder' "$FINDUAS_RUNNER"; then
    echo "runner contains a forbidden command-forwarding primitive" >&2
    exit 1
fi
if ! "$FINDUAS_RG" \
    -q '^exec /system/bin/app_process \\$' "$FINDUAS_RUNNER"; then
    echo "runner does not end in the fixed app_process launcher" >&2
    exit 1
fi
if ! "$FINDUAS_RG" -q '/system/bin/id -u' "$FINDUAS_RUNNER"; then
    echo "runner does not fail closed outside UID 1000" >&2
    exit 1
fi

echo "audit.result=PASS"
echo "audit.jar_entries=classes.dex"
echo "audit.java_source_count=1"
echo "audit.source_transact_calls=$FINDUAS_SOURCE_TRANSACTS"
echo "audit.decompiled_transact_calls=$FINDUAS_DECOMPILED_TRANSACTS"
echo "audit.dex_transact_instructions=$FINDUAS_DEX_TRANSACTS"
echo "audit.transaction=1"
echo "audit.flags=0"
echo "audit.uid_gate=1000"
echo "audit.descriptor_check=exact"
echo "audit.forbidden_capability_hits=0"
echo "audit.device_execution=NOT_PERFORMED"
