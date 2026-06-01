#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)

source "$(dirname "$0")/lib/test_helpers.sh"

T="$REPO_ROOT/skills/project-architect/references/templates/TYPE_SYSTEM.md"
assert_file_exists "$T" "TYPE_SYSTEM template must exist"

CONTENT=$(cat "$T")
assert_contains "$CONTENT" 'template_name: TYPE_SYSTEM'
assert_contains "$CONTENT" 'generate_when:'
assert_contains "$CONTENT" 'general_purpose_language'
assert_contains "$CONTENT" 'transpiler_target'
assert_contains "$CONTENT" 'Static / dynamic / gradual'
assert_contains "$CONTENT" 'Type inference algorithm'
assert_contains "$CONTENT" 'Polymorphism'
assert_contains "$CONTENT" 'Sum types'
assert_contains "$CONTENT" 'pattern matching'
assert_contains "$CONTENT" 'Algebraic data types'
assert_contains "$CONTENT" 'Advanced features'
assert_contains "$CONTENT" 'Type coercion'
# 2026 exemplars
assert_contains "$CONTENT" 'Lean 4' 'advanced features must reference Lean 4'
assert_contains "$CONTENT" 'Mathlib4' 'advanced features must reference Mathlib4 (>210K theorems)'
assert_contains "$CONTENT" 'GATs' 'must reference Generic Associated Types (Rust)'
assert_contains "$CONTENT" 'Idris 2' 'advanced features must reference Idris 2 (QTT)'
assert_contains "$CONTENT" 'Skillfully made with' 'footer attribution required'
test_summary
