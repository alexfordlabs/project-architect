#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"

REF="$REPO_ROOT/skills/project-architect/references/runtime-budgets.md"
assert_file_exists "$REF" "runtime-budgets.md reference must exist"

CONTENT=$(cat "$REF")
assert_contains "$CONTENT" 'Observer wrapper' 'must define observer wrapper'
assert_contains "$CONTENT" 'never blocks' 'must explicitly state observer never blocks'
assert_contains "$CONTENT" 'agent_work_time' 'must distinguish agent_work_time from total_elapsed'
assert_contains "$CONTENT" 'Per-agent budget table' 'must contain per-agent budget table'
assert_contains "$CONTENT" 'research-scout' 'must list research-scout in table'
assert_contains "$CONTENT" 'not persisted' 'observer telemetry must be inline + not persisted to the event log (v8: no agent_dispatches)'

SKILL_CONTENT=$(cat "$REPO_ROOT/skills/project-architect/SKILL.md")
assert_contains "$SKILL_CONTENT" 'runtime-budgets.md' 'SKILL.md must reference runtime-budgets.md'
assert_contains "$SKILL_CONTENT" 'observer wrapper' 'SKILL.md must mention observer wrapper'

test_summary
