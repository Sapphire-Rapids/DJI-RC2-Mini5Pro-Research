#!/bin/sh
set -efu
FINDUAS_BRIDGE_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
FINDUAS_BRIDGE_CC=${CC:-cc}
FINDUAS_BRIDGE_PKG_CONFIG=${PKG_CONFIG:-pkg-config}
mkdir -p "$FINDUAS_BRIDGE_ROOT/build"
FINDUAS_BRIDGE_ARCHIVE=$("$FINDUAS_BRIDGE_PKG_CONFIG" --variable=libdir libmtp)/libmtp.a
if [ ! -f "$FINDUAS_BRIDGE_ARCHIVE" ] || [ ! -r "$FINDUAS_BRIDGE_ARCHIVE" ]; then
    printf '%s\n' 'ERROR: static libmtp.a is required; dynamic fallback is disabled.' >&2
    exit 1
fi
FINDUAS_BRIDGE_TEMP=$FINDUAS_BRIDGE_ROOT/build/.mtp_bridge.$$
trap 'rm -f "$FINDUAS_BRIDGE_TEMP" "$FINDUAS_BRIDGE_TEMP.guard" "$FINDUAS_BRIDGE_TEMP.symbols" "$FINDUAS_BRIDGE_TEMP.dependencies"' EXIT
trap 'exit 1' HUP INT TERM

# Exercise the guard without linking or initializing libusb.
"$FINDUAS_BRIDGE_CC" -std=c11 -O2 -Wall -Wextra -Werror \
    $("$FINDUAS_BRIDGE_PKG_CONFIG" --cflags libusb-1.0) \
    "$FINDUAS_BRIDGE_ROOT/usb_reset_guard.c" \
    "$FINDUAS_BRIDGE_ROOT/usb_reset_guard_test.c" \
    -o "$FINDUAS_BRIDGE_TEMP.guard"
"$FINDUAS_BRIDGE_TEMP.guard"

# Use the explicit archive so its reset references bind to our local guard.
# Keep dependency flags supplied by pkg-config, but never link -lmtp dynamically.
set --
for FINDUAS_BRIDGE_FLAG in $("$FINDUAS_BRIDGE_PKG_CONFIG" --libs --static libmtp); do
    if [ "$FINDUAS_BRIDGE_FLAG" != -lmtp ]; then
        set -- "$@" "$FINDUAS_BRIDGE_FLAG"
    fi
done
FINDUAS_BRIDGE_OS=$(uname -s)
if [ "$FINDUAS_BRIDGE_OS" = Darwin ]; then
    set -- "$@" -liconv
fi
# pkg-config supplies compiler/linker words; no local SDK or host path is embedded.
"$FINDUAS_BRIDGE_CC" -std=c11 -O2 -Wall -Wextra -Werror \
    $("$FINDUAS_BRIDGE_PKG_CONFIG" --cflags libmtp libusb-1.0) \
    "$FINDUAS_BRIDGE_ROOT/mtp_bridge.c" \
    "$FINDUAS_BRIDGE_ROOT/usb_reset_guard.c" \
    "$FINDUAS_BRIDGE_ARCHIVE" "$@" \
    -o "$FINDUAS_BRIDGE_TEMP"

nm "$FINDUAS_BRIDGE_TEMP" > "$FINDUAS_BRIDGE_TEMP.symbols"
if ! awk '
    $NF ~ /^_?libusb_reset_device$/ {
        if ($(NF - 1) != "T") exit 1
        count++
    }
    END { if (count != 1) exit 1 }
' "$FINDUAS_BRIDGE_TEMP.symbols"; then
    printf '%s\n' 'ERROR: reset guard must be locally defined, not imported.' >&2
    exit 1
fi
case "$FINDUAS_BRIDGE_OS" in
    Darwin) otool -L "$FINDUAS_BRIDGE_TEMP" > "$FINDUAS_BRIDGE_TEMP.dependencies" ;;
    Linux) readelf -d "$FINDUAS_BRIDGE_TEMP" > "$FINDUAS_BRIDGE_TEMP.dependencies" ;;
    *) printf '%s\n' 'ERROR: no dynamic dependency audit for this host platform.' >&2; exit 1 ;;
esac
if ! awk '/libmtp[^[:space:]]*\.(dylib|so)/ { exit 1 }' "$FINDUAS_BRIDGE_TEMP.dependencies"; then
    printf '%s\n' 'ERROR: dynamic libmtp dependency would bypass the reset guard.' >&2
    exit 1
fi
"$FINDUAS_BRIDGE_TEMP" --self-test
mv -f "$FINDUAS_BRIDGE_TEMP" "$FINDUAS_BRIDGE_ROOT/build/mtp_bridge"
printf '%s\n' 'BUILD_OK usb_reset=blocked libmtp_linkage=static'
