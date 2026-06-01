#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"

REF="$REPO_ROOT/skills/project-architect/references/dispatch-prompts.md"
assert_file_exists "$REF" 'dispatch-prompts.md must exist'
R="$(cat "$REF")"
assert_contains "$R" '## Shared dispatch header' 'must define the shared dispatch header'
assert_contains "$R" 'research-scout' 'must hold the research-scout dispatch body'
assert_contains "$R" 'document-author' 'must hold the document-author dispatch body'
assert_contains "$R" 'quality-gate-auditor' 'must hold the auditor dispatch body'
assert_contains "$R" 'decision-revisor' 'must hold the decision-revisor dispatch body'

SKILL="$(cat "$REPO_ROOT/skills/project-architect/SKILL.md")"
assert_contains "$SKILL" 'references/dispatch-prompts.md' 'SKILL.md must reference the dispatch-prompts file'
assert_not_contains "$SKILL" 'Research the project domain. Find: (1) 3–5 similar existing projects' 'verbose research-scout prompt body must move to the reference'

test_summary
