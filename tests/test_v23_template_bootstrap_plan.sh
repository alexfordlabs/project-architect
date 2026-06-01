#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
# Test for BOOTSTRAP_PLAN.md template (v2.3, Task 7).

source "$(dirname "$0")/lib/test_helpers.sh"

T="$REPO_ROOT/skills/project-architect/references/templates/BOOTSTRAP_PLAN.md"
assert_file_exists "$T" "BOOTSTRAP_PLAN template must exist"

CONTENT=$(cat "$T")
assert_contains "$CONTENT" 'template_name: BOOTSTRAP_PLAN'
assert_contains "$CONTENT" 'generate_when:'
assert_contains "$CONTENT" 'Implementation language'
assert_contains "$CONTENT" 'chumsky' 'must recommend chumsky for Rust default'
assert_contains "$CONTENT" 'menhir' 'must reference OCaml + menhir as traditional alt'
assert_contains "$CONTENT" 'megaparsec'
assert_contains "$CONTENT" 'Avoid TypeScript' 'must call out TS migration to Rust'
assert_contains "$CONTENT" 'Minimum viable subset'
assert_contains "$CONTENT" 'Self-hosting trajectory'
assert_contains "$CONTENT" 'Test corpus'
assert_contains "$CONTENT" 'Reference implementation'
assert_contains "$CONTENT" 'Build + distribution'
assert_contains "$CONTENT" 'Skillfully made with' 'footer attribution required'

test_summary
