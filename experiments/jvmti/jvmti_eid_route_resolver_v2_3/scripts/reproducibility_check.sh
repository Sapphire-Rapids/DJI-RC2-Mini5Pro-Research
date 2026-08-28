#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
artifact=$project_dir/dist/FindUAS-JVMTI-EID-Route-Resolver-V2.3-0.1.0-offline-unadmitted-arm64-v8a.apk
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/finduas-route-v23-repro.XXXXXX")
trap 'rm -rf -- "$temporary_dir"' EXIT HUP INT TERM

sh "$script_dir/build_and_audit.sh"
cp "$artifact" "$temporary_dir/first.apk"
first_digest=$(shasum -a 256 "$temporary_dir/first.apk" | awk '{print $1}')

sh "$script_dir/build_and_audit.sh"
second_digest=$(shasum -a 256 "$artifact" | awk '{print $1}')

if [ "$first_digest" != "$second_digest" ] || ! cmp -s "$temporary_dir/first.apk" "$artifact"; then
    echo "Reproducibility check failed: $first_digest != $second_digest" >&2
    exit 1
fi

echo "Reproducibility: PASS ($second_digest)"
