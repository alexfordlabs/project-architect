#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
# Test for slash command templates (sketch D, task 40).
# Verifies SLASH_SCAFFOLD, SLASH_IMPLEMENT, SLASH_ITERATE_DESIGN templates exist
# and contain the required structural elements.

source "$(dirname "$0")/lib/test_helpers.sh"

for cmd in SLASH_SCAFFOLD SLASH_IMPLEMENT SLASH_ITERATE_DESIGN; do
  T="$REPO_ROOT/skills/project-architect/references/templates/${cmd}.md"
  assert_file_exists "$T" "${cmd} template must exist"
  CONTENT=$(cat "$T")
  assert_contains "$CONTENT" 'description:' "$cmd must have description in frontmatter"
done

# SLASH_IMPLEMENT specifically must have argument-hint
SLASH_IMPL=$(cat "$REPO_ROOT/skills/project-architect/references/templates/SLASH_IMPLEMENT.md")
assert_contains "$SLASH_IMPL" 'argument-hint:' 'SLASH_IMPLEMENT must have argument-hint: feature-name'
assert_contains "$SLASH_IMPL" 'feature-name' 'argument-hint must mention feature-name'

# Body must reference downstream skills/agents
SLASH_SCAFFOLD=$(cat "$REPO_ROOT/skills/project-architect/references/templates/SLASH_SCAFFOLD.md")
assert_contains "$SLASH_SCAFFOLD" 'superpowers:writing-plans' 'SLASH_SCAFFOLD must reference superpowers:writing-plans'

SLASH_ITERATE=$(cat "$REPO_ROOT/skills/project-architect/references/templates/SLASH_ITERATE_DESIGN.md")
assert_contains "$SLASH_ITERATE" 'project-architect' 'SLASH_ITERATE_DESIGN must reference project-architect skill'

test_summary
