#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)

source "$(dirname "$0")/lib/test_helpers.sh"

T="$REPO_ROOT/skills/project-architect/references/templates/SEMANTICS.md"
assert_file_exists "$T" "SEMANTICS template must exist"

CONTENT=$(cat "$T")
assert_contains "$CONTENT" 'template_name: SEMANTICS'
assert_contains "$CONTENT" 'generate_when:'
assert_contains "$CONTENT" 'general_purpose_language'
assert_contains "$CONTENT" 'transpiler_target'
assert_contains "$CONTENT" 'Evaluation model'
assert_contains "$CONTENT" 'Scoping'
assert_contains "$CONTENT" 'Memory model'
assert_contains "$CONTENT" 'Mutability defaults'
assert_contains "$CONTENT" 'Effects model'
assert_contains "$CONTENT" 'Concurrency model'
assert_contains "$CONTENT" 'Error model'
assert_contains "$CONTENT" 'Equality semantics'
# 2026 exemplars
assert_contains "$CONTENT" 'Koka' 'effects must reference Koka'
assert_contains "$CONTENT" 'OCaml 5' 'effects must reference OCaml 5 algebraic effects'
assert_contains "$CONTENT" 'virtual threads' 'concurrency must reference Java virtual threads'
assert_contains "$CONTENT" 'Skillfully made with' 'footer attribution required'
test_summary
