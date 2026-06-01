#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
# Test for v2.2 task 47: claude-tooling-author has inline Validation section (sketch A).

source "$(dirname "$0")/lib/test_helpers.sh"

AGENT="$REPO_ROOT/agents/claude-tooling-author.md"
CONTENT=$(cat "$AGENT")

assert_contains "$CONTENT" '## Validation' 'agent must have ## Validation section'
assert_contains "$CONTENT" 'shellcheck' 'must run shellcheck on .sh files'
assert_contains "$CONTENT" 'jq empty' 'must run jq empty on .json files'
assert_contains "$CONTENT" 'unsafe_to_use' 'must define unsafe_to_use list'
assert_contains "$CONTENT" 'retry up to 2' 'must specify retry policy'

test_summary
