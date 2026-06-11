#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"

REF="$REPO_ROOT/skills/project-architect/references/anonymity-preflight.md"
assert_file_exists "$REF" 'anonymity-preflight.md must exist'
R="$(cat "$REF")"
assert_contains "$R" 'firebase' 'blocklist must include firebase (a privacy-app leak)'
assert_contains "$R" 'project.privacy_sensitive' 'must document the trigger flag'
assert_contains "$R" 'anonymity_threat_preflight' 'must name the consuming check (B25)'

SKILL="$(cat "$REPO_ROOT/skills/project-architect/SKILL.md")"
assert_contains "$SKILL" 'references/anonymity-preflight.md' 'SKILL.md must point Preflight/Phase 2.5 at the reference'

test_summary
