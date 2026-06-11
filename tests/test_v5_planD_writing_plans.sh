#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"
SKILL="$(cat "$REPO_ROOT/skills/project-architect/SKILL.md")"

assert_contains "$SKILL" 'invoke `Skill: superpowers:writing-plans`' 'plan-doc gen must invoke writing-plans when present'
assert_contains "$SKILL" 'template fallback' 'plan-doc gen must fall back to the template when superpowers is absent'
assert_contains "$SKILL" 'soft-dependency probe' 'plan-doc gen must probe for superpowers (graceful-optional)'

test_summary
