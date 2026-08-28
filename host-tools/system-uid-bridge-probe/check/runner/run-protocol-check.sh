#!/system/bin/sh

# Fixed launcher for the read-only FindUAS protocol Binder capability probe.
# It deliberately accepts no arguments and forwards no user-controlled command.

if [ "$#" -ne 0 ]; then
    echo "finduas.protocol_check.result=USAGE_ERROR"
    echo "finduas.protocol_check.detail=This fixed launcher accepts no arguments."
    exit 64
fi

if [ "$(/system/bin/id -u)" != "1000" ]; then
    echo "finduas.protocol_check.result=WRONG_UID"
    echo "finduas.protocol_check.detail=The launcher did not inherit Android system UID 1000."
    exit 65
fi

FINDUAS_CHECK_JAR=/sdcard/Download/finduas-protocol-check.jar

if [ ! -r "$FINDUAS_CHECK_JAR" ]; then
    echo "finduas.protocol_check.result=JAR_NOT_READABLE"
    echo "finduas.protocol_check.detail=Expected /sdcard/Download/finduas-protocol-check.jar."
    exit 66
fi

export CLASSPATH="$FINDUAS_CHECK_JAR"
exec /system/bin/app_process \
    /system/bin \
    com.finduas.systemuidbridge.check.ProtocolServiceCheck
