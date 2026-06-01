#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"

C="$REPO_ROOT/skills/project-architect/references/document-catalog.md"
assert_file_exists "$C" "document-catalog.md must exist"

CONTENT=$(cat "$C")
assert_contains "$CONTENT" 'CLI_UX_DESIGN' 'catalog must register CLI_UX_DESIGN'
assert_contains "$CONTENT" 'cli_tool' 'catalog must reference cli_tool generate_when condition'

# Depends_on entries
assert_contains "$CONTENT" 'PROJECT_REQUIREMENTS' 'catalog must reference PROJECT_REQUIREMENTS as dep'
assert_contains "$CONTENT" 'CLI_REFERENCE' 'catalog must reference CLI_REFERENCE as dep'

test_summary
