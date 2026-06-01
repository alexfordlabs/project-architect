#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
# Test for SCAFFOLD_PLAN.md template (sketch D, task 34).
# Verifies template exists and contains required structural sections.

source "$(dirname "$0")/lib/test_helpers.sh"

T="$REPO_ROOT/skills/project-architect/references/templates/SCAFFOLD_PLAN.md"
assert_file_exists "$T" "SCAFFOLD_PLAN template must exist"
CONTENT=$(cat "$T")
assert_contains "$CONTENT" 'template_name: SCAFFOLD_PLAN'
assert_contains "$CONTENT" 'generate_when:'
assert_contains "$CONTENT" 'documentation_only'
assert_contains "$CONTENT" 'depends_on:'
assert_contains "$CONTENT" 'TECH_STACK.md'
assert_contains "$CONTENT" 'BUILD_AND_RUN.md'
assert_contains "$CONTENT" 'Build manifest'
assert_contains "$CONTENT" 'src/' 'must have src/ tree section'
assert_contains "$CONTENT" 'License' 'must have License files section'
assert_contains "$CONTENT" 'Toolchain' 'must have Toolchain pin section'
assert_contains "$CONTENT" 'bootstrap' 'must list bootstrap commands'
assert_contains "$CONTENT" 'superpowers:writing-plans' 'must reference handoff'
assert_contains "$CONTENT" '/scaffold' 'must reference /scaffold slash command'

test_summary
