#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"
DISPATCH="$(cat "$REPO_ROOT/skills/project-architect/references/dispatch-prompts.md")"
SKILL="$(cat "$REPO_ROOT/skills/project-architect/SKILL.md")"

assert_contains "$DISPATCH" '[IDENTITY HYGIENE — HARD RULE]' 'shared dispatch header must carry the identity-hygiene clause'
assert_contains "$DISPATCH" 'deanonymizing identifier' 'identity clause must forbid deanonymizing identifiers'
assert_contains "$DISPATCH" '[POST-RETURN SCRUB]' 'shared dispatch header must carry the post-return scrub'
assert_contains "$DISPATCH" 'complements gitleaks' 'identity clause must position itself vs gitleaks'
# SKILL.md ties the clause to the enforcing check.
assert_contains "$SKILL" 'identity_hygiene' 'SKILL.md must reference the identity_hygiene gate (B24)'
# D8 step 3b — the Phase 4 doc-gen region OPERATIONALLY runs the B24 gate after a batch (not just the §5 map row).
assert_contains "$SKILL" 'identity-deny.txt' 'Phase 4 must run the identity_hygiene gate against the deny-list after doc/research batches'

test_summary
