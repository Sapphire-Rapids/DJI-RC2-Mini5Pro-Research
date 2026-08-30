#!/bin/sh
set -eu
FINDUAS_BRIDGE_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
FINDUAS_BRIDGE_CC=${CC:-cc}
FINDUAS_BRIDGE_PKG_CONFIG=${PKG_CONFIG:-pkg-config}
mkdir -p "$FINDUAS_BRIDGE_ROOT/build"
# pkg-config supplies compiler/linker words; no local SDK or host path is embedded.
"$FINDUAS_BRIDGE_CC" -std=c11 -O2 -Wall -Wextra -Werror \
    $("$FINDUAS_BRIDGE_PKG_CONFIG" --cflags libmtp) \
    "$FINDUAS_BRIDGE_ROOT/mtp_bridge.c" \
    $("$FINDUAS_BRIDGE_PKG_CONFIG" --libs libmtp) \
    -o "$FINDUAS_BRIDGE_ROOT/build/mtp_bridge"
"$FINDUAS_BRIDGE_ROOT/build/mtp_bridge" --self-test
