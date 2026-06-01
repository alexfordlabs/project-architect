#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)

source "$(dirname "$0")/lib/test_helpers.sh"

T="$REPO_ROOT/skills/project-architect/references/templates/LANGUAGE_GRAMMAR.md"
assert_file_exists "$T" "LANGUAGE_GRAMMAR template must exist"

CONTENT=$(cat "$T")
assert_contains "$CONTENT" 'template_name: LANGUAGE_GRAMMAR'
assert_contains "$CONTENT" 'generate_when:'
assert_contains "$CONTENT" 'transpiler_target' 'generate_when includes transpiler_target'
assert_contains "$CONTENT" 'general_purpose_language'
assert_contains "$CONTENT" 'Tokenization'
assert_contains "$CONTENT" 'Grammar specification'
assert_contains "$CONTENT" 'Ambiguity resolution'
assert_contains "$CONTENT" 'Significant whitespace'
assert_contains "$CONTENT" 'Error recovery'
assert_contains "$CONTENT" 'Reserved word policy'
assert_contains "$CONTENT" 'Lexer/parser implementation'
assert_contains "$CONTENT" 'tree-sitter' 'must reference tree-sitter for editor parsing'
assert_contains "$CONTENT" 'chumsky' 'must reference chumsky for Rust parser default'
assert_contains "$CONTENT" 'Skillfully made with' 'footer attribution required'

test_summary
