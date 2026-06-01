#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
# Test for TOOLCHAIN.md template (v2.3, Task 6).

source "$(dirname "$0")/lib/test_helpers.sh"

T="$REPO_ROOT/skills/project-architect/references/templates/TOOLCHAIN.md"
assert_file_exists "$T" "TOOLCHAIN template must exist"

CONTENT=$(cat "$T")
assert_contains "$CONTENT" 'template_name: TOOLCHAIN'
assert_contains "$CONTENT" 'generate_when:'
assert_contains "$CONTENT" 'general_purpose_language'
assert_contains "$CONTENT" 'transpiler_target'
assert_contains "$CONTENT" 'depends_on:'
assert_contains "$CONTENT" 'SEMANTICS.md'
assert_contains "$CONTENT" 'LANGUAGE_GRAMMAR.md'
assert_contains "$CONTENT" 'REPL'
assert_contains "$CONTENT" 'Formatter'
assert_contains "$CONTENT" 'Linter'
assert_contains "$CONTENT" 'LSP'
assert_contains "$CONTENT" '3.17' 'LSP target version'
assert_contains "$CONTENT" 'tree-sitter' 'tree-sitter for incremental parsing'
assert_contains "$CONTENT" 'Debugger'
assert_contains "$CONTENT" 'Debug Adapter Protocol' 'DAP referenced'
assert_contains "$CONTENT" 'Package manager'
assert_contains "$CONTENT" 'Build tool'
assert_contains "$CONTENT" 'rust-analyzer' 'reference architecture'
assert_contains "$CONTENT" 'Documentation generator'
assert_contains "$CONTENT" 'Test runner'
assert_contains "$CONTENT" 'Skillfully made with' 'footer attribution required'

test_summary
