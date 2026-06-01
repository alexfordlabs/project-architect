#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)

source "$(dirname "$0")/lib/test_helpers.sh"

T="$REPO_ROOT/skills/project-architect/references/templates/STDLIB.md"
assert_file_exists "$T" "STDLIB template must exist"

CONTENT=$(cat "$T")
assert_contains "$CONTENT" 'template_name: STDLIB'
assert_contains "$CONTENT" 'generate_when:'
assert_contains "$CONTENT" 'general_purpose_language'
assert_contains "$CONTENT" 'transpiler_target'
assert_contains "$CONTENT" 'depends_on:'
assert_contains "$CONTENT" 'SEMANTICS.md'
assert_contains "$CONTENT" 'TYPE_SYSTEM.md'
assert_contains "$CONTENT" 'Inclusion philosophy'
assert_contains "$CONTENT" 'Module organization'
assert_contains "$CONTENT" 'Numeric tower'
assert_contains "$CONTENT" 'String model'
assert_contains "$CONTENT" 'Collections'
assert_contains "$CONTENT" 'I/O surface'
assert_contains "$CONTENT" 'Concurrency primitives'
assert_contains "$CONTENT" 'WasmGC' 'I/O section must reference WasmGC 2026 context'
assert_contains "$CONTENT" 'Time, errors, testing'
assert_contains "$CONTENT" 'NOT in stdlib'
assert_contains "$CONTENT" 'Skillfully made with' 'footer attribution required'
test_summary
