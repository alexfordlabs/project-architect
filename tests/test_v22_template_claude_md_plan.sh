#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
# Test for CLAUDE_MD_PLAN.md template (sketch D, task 32).
# Verifies template exists and contains required structural sections.

source "$(dirname "$0")/lib/test_helpers.sh"

T="$REPO_ROOT/skills/project-architect/references/templates/CLAUDE_MD_PLAN.md"
assert_file_exists "$T" "CLAUDE_MD_PLAN template must exist"
CONTENT=$(cat "$T")
assert_contains "$CONTENT" 'generate_when:' 'must have generate_when frontmatter'
assert_contains "$CONTENT" 'depends_on:' 'must have depends_on frontmatter'
assert_contains "$CONTENT" 'Project context block' 'must include Project context section'
assert_contains "$CONTENT" 'Working-in-this-project rules' 'must include Working rules section'
assert_contains "$CONTENT" 'Next-step menu' 'must include Next-step menu section'
assert_contains "$CONTENT" 'Per-subfolder' 'must include per-subfolder section'

test_summary
