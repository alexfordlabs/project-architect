#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"
CMD="$REPO_ROOT/commands/re-architect.md"
assert_file_exists "$CMD" '/re-architect command exists'
C="$(cat "$CMD" 2>/dev/null || true)"
assert_contains "$C" 'description:' 'has frontmatter description'
assert_contains "$C" 're-architect-flow.md' 'drives the canonical flow'
assert_contains "$C" 'architect-brain detect' 'runs the v8 situation detector first'
assert_not_contains "$C" 'architect-ledger' 'no invocation of the deleted v7 architect-ledger binary'
assert_contains "$C" 'RECOVERED_DESIGN' 'mentions the recovered-design review'
test_summary
