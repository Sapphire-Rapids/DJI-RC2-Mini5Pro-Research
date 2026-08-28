#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
test_output=$project_dir/build/host-tests/state_test

mkdir -p "$(dirname -- "$test_output")"
cc \
    -std=c11 \
    -D_POSIX_C_SOURCE=200809L \
    -Wall \
    -Wextra \
    -Werror \
    -pthread \
    -I "$project_dir/app/src/main/cpp" \
    "$project_dir/app/src/main/cpp/state.c" \
    "$project_dir/tests/host/state_test.c" \
    -o "$test_output"

"$test_output"
