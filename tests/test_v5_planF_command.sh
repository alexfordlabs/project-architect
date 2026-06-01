#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"

CMD="$REPO_ROOT/commands/upgrade-project.md"
assert_file_exists "$CMD" 'plugin command upgrade-project.md exists'
C="$(cat "$CMD" 2>/dev/null || true)"
assert_contains "$C" 'description:' 'command has frontmatter description'
assert_contains "$C" 'upgrade-flow.md' 'command points at the canonical flow'
assert_contains "$C" 'architect-brain detect' 'command runs the v8 situation detector first'
assert_not_contains "$C" 'architect-ledger' 'no invocation of the deleted v7 architect-ledger binary'
assert_contains "$C" 'snapshot' 'command mentions the snapshot-first safety'

test_summary
