#!/bin/sh
set -eu
task_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
task_tmp=$(mktemp -d)
trap 'rm -rf "$task_tmp"' EXIT HUP INT TERM
${CC:-cc} -std=c11 -O2 -Wall -Wextra -Werror -pedantic \
    -I"$task_root/src/native" "$task_root/src/native/cloud_policy_parser.c" \
    "$task_root/tests/native/cloud_policy_parser_test.c" -o "$task_tmp/parser-test"
"$task_tmp/parser-test"
${CC:-cc} -std=c11 -O1 -g -Wall -Wextra -Werror -pedantic \
    -fsanitize=address,undefined -fno-omit-frame-pointer \
    -I"$task_root/src/native" "$task_root/src/native/cloud_policy_parser.c" \
    "$task_root/tests/native/cloud_policy_parser_test.c" -o "$task_tmp/parser-test-sanitized"
"$task_tmp/parser-test-sanitized"
${PYTHON:-python3} "$task_root/tests/test_cloud_policy_parser.py"
