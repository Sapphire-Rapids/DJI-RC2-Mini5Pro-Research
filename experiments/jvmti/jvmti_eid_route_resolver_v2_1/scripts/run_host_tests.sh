#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/finduas-route-v21-host.XXXXXX")
trap 'rm -rf -- "$temporary_dir"' EXIT HUP INT TERM

host_cc=${FINDUAS_ROUTE_V21_HOST_CC:-cc}

"$host_cc" \
    -std=c11 \
    -Wall \
    -Wextra \
    -Werror \
    -I"$project_dir/app/src/main/cpp" \
    "$project_dir/app/src/main/cpp/note_parser.c" \
    "$project_dir/app/src/main/cpp/route_policy.c" \
    "$project_dir/app/src/main/cpp/target_profile.c" \
    "$project_dir/tests/host/route_test.c" \
    -o "$temporary_dir/route_test"

"$temporary_dir/route_test"
echo "Host tests: PASS"
