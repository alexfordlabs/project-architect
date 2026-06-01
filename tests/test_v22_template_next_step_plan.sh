#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
# Test for NEXT_STEP_PLAN.md template (sketch D, task 35).
# Verifies template exists and contains required structural sections.

source "$(dirname "$0")/lib/test_helpers.sh"

T="$REPO_ROOT/skills/project-architect/references/templates/NEXT_STEP_PLAN.md"
assert_file_exists "$T" "NEXT_STEP_PLAN template must exist"
CONTENT=$(cat "$T")
assert_contains "$CONTENT" 'template_name: NEXT_STEP_PLAN'
assert_contains "$CONTENT" 'generate_when:'
assert_contains "$CONTENT" '/scaffold' 'must reference /scaffold slash command'
assert_contains "$CONTENT" '/implement' 'must reference /implement slash command'
assert_contains "$CONTENT" '/iterate-design' 'must reference /iterate-design slash command'
assert_contains "$CONTENT" 'Troubleshooting' 'must have troubleshooting section'
assert_contains "$CONTENT" 'superpowers' 'must mention superpowers (manual fallback context)'

test_summary
