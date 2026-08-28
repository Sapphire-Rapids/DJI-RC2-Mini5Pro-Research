#!/system/bin/sh
set -eu

if [ "$#" -ne 0 ]; then
  echo "FAIL_CLOSED arguments are forbidden" >&2
  exit 64
fi

if [ "$(/system/bin/id -u)" != "1000" ]; then
  echo "FAIL_CLOSED runner must inherit system UID 1000" >&2
  exit 65
fi

export CLASSPATH=/sdcard/Download/FindUAS-France-EID-GET-readonly.jar
exec /system/bin/app_process /system/bin com.finduas.bridge.FranceEidGetMain
