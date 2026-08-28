#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
research_dir=${FINDUAS_RESEARCH_FIXTURE_ROOT:-}
: "${research_dir:?Set FINDUAS_RESEARCH_FIXTURE_ROOT to the external fixture tree}"
temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/finduas-route-v22-host.XXXXXX")
trap 'rm -rf -- "$temporary_dir"' EXIT HUP INT TERM

host_cc=${FINDUAS_ROUTE_V22_HOST_CC:-cc}

"$host_cc" \
    -std=c11 \
    -Wall \
    -Wextra \
    -Werror \
    -DFINDUAS_RESEARCH_DIR=\"$research_dir\" \
    -I"$project_dir/app/src/main/cpp" \
    "$project_dir/app/src/main/cpp/identity_core.c" \
    "$project_dir/app/src/main/cpp/note_parser.c" \
    "$project_dir/app/src/main/cpp/route_policy.c" \
    "$project_dir/app/src/main/cpp/target_profile.c" \
    "$project_dir/app/src/main/cpp/sha256.c" \
    "$project_dir/tests/host/route_test.c" \
    -o "$temporary_dir/route_test"

"$temporary_dir/route_test"
echo "Host tests: PASS"
