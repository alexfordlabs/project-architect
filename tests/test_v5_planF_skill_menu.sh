#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"

SKILL="$(cat "$REPO_ROOT/skills/project-architect/SKILL.md")"
assert_contains "$SKILL" 'Upgrade design, then continue' 'skill gate lists option 1'
assert_contains "$SKILL" 'Upgrade design, then rebuild code' 'skill gate lists option 2'
assert_contains "$SKILL" 'Start fresh, revisiting decisions' 'skill gate lists option 3'
assert_contains "$SKILL" 'Proceed without upgrading' 'skill gate lists option 4'
assert_contains "$SKILL" 'version-awareness.md' 'skill gate cites the SSOT'
assert_contains "$SKILL" 'Precedence' 'skill gate states gate precedence'
assert_contains "$SKILL" 'version_gate_ack' 'option 4 records an ack'
assert_not_contains "$SKILL" 'do not duplicate the menu here' 'the minimal-offer deferral is replaced by the live menu'

test_summary
