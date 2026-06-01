#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"
QF="$(cat "$REPO_ROOT/skills/project-architect/references/questioning-flow.md")"

assert_contains "$QF" '## Divergent questioning' 'questioning-flow must add a divergent-questioning section'
assert_contains "$QF" 'one question at a time' 'must adopt one-question-at-a-time discipline'
assert_contains "$QF" 'assumptions' 'must surface unstated assumptions'
assert_contains "$QF" 'no nested' 'must clarify principles are baked in, not a nested skill'

test_summary
