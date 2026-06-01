#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"

T="$REPO_ROOT/skills/project-architect/references/templates/CLI_UX_DESIGN.md"
assert_file_exists "$T" "CLI_UX_DESIGN.md must exist"

CONTENT=$(cat "$T")
assert_contains "$CONTENT" 'generate_when:' 'must have generate_when frontmatter'
assert_contains "$CONTENT" 'cli_tool' 'generate_when must include cli_tool'
assert_contains "$CONTENT" 'tui_app' 'generate_when must include tui_app'

# 8 sections
assert_contains "$CONTENT" 'Interaction model' 'must have Interaction model section'
assert_contains "$CONTENT" 'Key bindings' 'must have Key bindings section'
assert_contains "$CONTENT" 'Visual design' 'must have Visual design section'
assert_contains "$CONTENT" 'Output formats' 'must have Output formats section'
assert_contains "$CONTENT" 'Error conventions' 'must have Error conventions section'
assert_contains "$CONTENT" 'Accessibility' 'must have Accessibility section'
assert_contains "$CONTENT" 'Help text' 'must have Help text section'
assert_contains "$CONTENT" 'Library inventory' 'must have Library inventory section'

test_summary
