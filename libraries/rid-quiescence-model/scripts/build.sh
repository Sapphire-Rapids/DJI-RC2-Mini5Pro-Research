#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MODEL_DIR=$(dirname -- "$SCRIPT_DIR")
TARGET="$MODEL_DIR/dist/rid-quiescence-verifier.pyz"

python3 "$SCRIPT_DIR/build.py" "$TARGET"
python3 "$SCRIPT_DIR/audit_artifact.py" "$TARGET"
