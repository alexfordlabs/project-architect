#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
# Test for CLAUDE_MD_ROOT.md router refactor (sketch D, task 41).
# Verifies the template now describes router content (State / Quick context /
# Working in this project / Next steps + slash command pointers).

source "$(dirname "$0")/lib/test_helpers.sh"

T="$REPO_ROOT/skills/project-architect/references/templates/CLAUDE_MD_ROOT.md"
assert_file_exists "$T" "CLAUDE_MD_ROOT template must exist"

CONTENT=$(cat "$T")
assert_contains "$CONTENT" '## State' 'must have ## State section (architecture-locked indicator)'
assert_contains "$CONTENT" '## Quick context' 'must have ## Quick context section'
assert_contains "$CONTENT" '## Next steps' 'must have ## Next steps section'
assert_contains "$CONTENT" '/scaffold' 'must reference /scaffold'
assert_contains "$CONTENT" '/implement' 'must reference /implement'
assert_contains "$CONTENT" '/iterate-design' 'must reference /iterate-design'
assert_contains "$CONTENT" '## Working in this project' 'must have Working in this project section'

test_summary
