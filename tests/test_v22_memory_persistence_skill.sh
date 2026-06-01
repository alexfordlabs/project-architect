#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)

source "$(dirname "$0")/lib/test_helpers.sh"

SKILL="$REPO_ROOT/skills/project-architect/SKILL.md"
CONTENT=$(cat "$SKILL")

# memory_pointer write at end of Phase 0a (first write)
assert_contains "$CONTENT" 'memory_pointer' 'SKILL.md must reference memory_pointer'
assert_contains "$CONTENT" 'memory-persistence.md' 'SKILL.md must reference memory-persistence.md'

# Memory write mentioned across phases
assert_contains "$CONTENT" 'Memory persistence' 'must have Memory persistence section'

# Phase 6 LOCK has the major update
assert_contains "$CONTENT" 'LOCKED at' 'must reference LOCKED at <version> memory entry shape'

test_summary
