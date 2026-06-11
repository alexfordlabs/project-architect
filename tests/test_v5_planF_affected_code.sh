#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"
if ! command -v jq >/dev/null 2>&1; then echo "SKIP: jq"; test_summary; exit 0; fi

PB="$(cat "$REPO_ROOT/skills/project-architect/references/revision-playbook.md")"
assert_contains "$PB" 'Affected code areas' 'playbook documents affected-code-areas'
assert_contains "$PB" 'project_layout' 'mapping is keyed off the canonical project_layout'
assert_contains "$PB" 'coarse' 'mapping is coarse (top-level component), not file-glob'
assert_contains "$PB" '/upgrade-project' 'used by the upgrade flow (option 1)'

# Behavior: for v5 the decision-key migration table in artifact-migration.md is IDENTITY
# (no real rename/split/re-type rows) -> a stale-decision diff surfaces ZERO stale decisions.
AM="$(cat "$REPO_ROOT/skills/project-architect/references/artifact-migration.md")"
assert_contains "$AM" 'baseline is identity' 'v5 decision-key table is identity'
# Use a CONCRETE real-row needle (NOT the convention example "rename a.b → c.d", which IS present):
assert_not_contains "$AM" 'database.engine →' 'v5 ships no concrete decision-key rename rows'

test_summary
