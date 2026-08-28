#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MODEL_DIR=$(dirname -- "$SCRIPT_DIR")

PYTHONPATH="$MODEL_DIR" python3 -m unittest discover -s "$MODEL_DIR/tests" -v
PYTHONPATH="$MODEL_DIR" python3 -m ridq --self-check >/dev/null

FIRST_DIR=$(mktemp -d "${TMPDIR:-/tmp}/ridq-build-a.XXXXXX")
SECOND_DIR=$(mktemp -d "${TMPDIR:-/tmp}/ridq-build-b.XXXXXX")
trap 'rm -rf "$FIRST_DIR" "$SECOND_DIR"' EXIT HUP INT TERM

python3 "$SCRIPT_DIR/build.py" "$FIRST_DIR/verifier.pyz" >/dev/null
python3 "$SCRIPT_DIR/build.py" "$SECOND_DIR/verifier.pyz" >/dev/null
cmp "$FIRST_DIR/verifier.pyz" "$SECOND_DIR/verifier.pyz"
python3 "$SCRIPT_DIR/audit_artifact.py" "$FIRST_DIR/verifier.pyz"
python3 "$FIRST_DIR/verifier.pyz" --self-check >/dev/null

echo "TEST PASS: two clean artifacts are byte-identical"
