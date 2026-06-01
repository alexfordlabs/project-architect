#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
# Test for STABILITY_AND_RFC.md template (v2.3, Task 8 — closes the 7-template PL design arc).

source "$(dirname "$0")/lib/test_helpers.sh"

T="$REPO_ROOT/skills/project-architect/references/templates/STABILITY_AND_RFC.md"
assert_file_exists "$T" "STABILITY_AND_RFC template must exist"

CONTENT=$(cat "$T")
assert_contains "$CONTENT" 'template_name: STABILITY_AND_RFC'
assert_contains "$CONTENT" 'generate_when:'
assert_contains "$CONTENT" 'general_purpose_language'
assert_contains "$CONTENT" 'transpiler_target'
assert_contains "$CONTENT" 'depends_on:'
assert_contains "$CONTENT" 'BOOTSTRAP_PLAN.md'
assert_contains "$CONTENT" 'TOOLCHAIN.md'
assert_contains "$CONTENT" 'Versioning policy'
assert_contains "$CONTENT" 'edition-based' 'must reference edition-based versioning'
assert_contains "$CONTENT" 'Rust 2024' 'edition exemplar'
assert_contains "$CONTENT" 'Stability tiers'
assert_contains "$CONTENT" '#![feature' 'Rust feature gating'
assert_contains "$CONTENT" 'Breaking change policy'
assert_contains "$CONTENT" 'edition migration tool'
assert_contains "$CONTENT" 'cargo fix --edition'
assert_contains "$CONTENT" 'RFC process'
assert_contains "$CONTENT" 'Rust RFCs' 'RFC repo exemplar'
assert_contains "$CONTENT" 'Decision-making model'
assert_contains "$CONTENT" 'Backwards-compatibility'
assert_contains "$CONTENT" 'Skillfully made with' 'footer attribution required'

test_summary
