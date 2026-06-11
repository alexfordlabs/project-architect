#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"
T="$REPO_ROOT/skills/project-architect/references/templates/RECOVERED_DESIGN.md"
assert_file_exists "$T" 'RECOVERED_DESIGN template exists'
C="$(cat "$T" 2>/dev/null || true)"
for col in 'key' 'current_value' 'rationale' 'source' 'confidence' 'triage'; do
  assert_contains "$C" "$col" "template documents the $col field"
done
assert_contains "$C" 'keep' 'triage values include keep'
assert_contains "$C" 'revise' 'triage values include revise'
assert_contains "$C" 'drop' 'triage values include drop'
test_summary
