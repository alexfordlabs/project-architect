#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
# Test for CLAUDE_TOOLING_PLAN.md template (sketch D, task 33).
# Verifies template exists and contains required structural sections.

source "$(dirname "$0")/lib/test_helpers.sh"

T="$REPO_ROOT/skills/project-architect/references/templates/CLAUDE_TOOLING_PLAN.md"
assert_file_exists "$T" "CLAUDE_TOOLING_PLAN template must exist"
CONTENT=$(cat "$T")
assert_contains "$CONTENT" 'template_name: CLAUDE_TOOLING_PLAN'
assert_contains "$CONTENT" 'generate_when:' 'must have generate_when'
assert_contains "$CONTENT" 'depends_on:' 'must have depends_on'
assert_contains "$CONTENT" 'SECURITY_AND_COMPLIANCE.md' 'must depend on security spec'
assert_contains "$CONTENT" 'settings.json' 'must have settings.json section'
assert_contains "$CONTENT" 'hooks/' 'must have hooks plan section'
assert_contains "$CONTENT" 'commands/' 'must have commands plan section'
assert_contains "$CONTENT" 'agents/' 'must have agents plan section'
assert_contains "$CONTENT" 'recommended-plugins.md' 'must have recommended-plugins plan'
assert_contains "$CONTENT" 'execute CLAUDE_TOOLING_PLAN' 'must reference Phase 7 execution'

test_summary
