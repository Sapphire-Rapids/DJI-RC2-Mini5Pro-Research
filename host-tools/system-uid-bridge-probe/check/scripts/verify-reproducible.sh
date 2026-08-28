#!/usr/bin/env bash
set -euo pipefail

FINDUAS_CHECK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FINDUAS_REPRO_TMP="$(mktemp -d)"
trap 'rm -rf "$FINDUAS_REPRO_TMP"' EXIT

"$FINDUAS_CHECK_ROOT/scripts/build.sh" >/dev/null
cp "$FINDUAS_CHECK_ROOT/dist/finduas-protocol-check.jar" \
    "$FINDUAS_REPRO_TMP/first.jar"
FINDUAS_FIRST_HASH="$(/usr/bin/shasum -a 256 "$FINDUAS_REPRO_TMP/first.jar" | awk '{print $1}')"

"$FINDUAS_CHECK_ROOT/scripts/build.sh" >/dev/null
FINDUAS_SECOND_HASH="$(/usr/bin/shasum -a 256 "$FINDUAS_CHECK_ROOT/dist/finduas-protocol-check.jar" | awk '{print $1}')"

if ! cmp -s \
    "$FINDUAS_REPRO_TMP/first.jar" \
    "$FINDUAS_CHECK_ROOT/dist/finduas-protocol-check.jar"; then
    echo "reproducibility.result=FAIL" >&2
    echo "reproducibility.first_sha256=$FINDUAS_FIRST_HASH" >&2
    echo "reproducibility.second_sha256=$FINDUAS_SECOND_HASH" >&2
    exit 1
fi

echo "reproducibility.result=PASS"
echo "reproducibility.sha256=$FINDUAS_SECOND_HASH"
