#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
# shellcheck disable=SC2016
#
# A6: re-architect Step-6 must preserve-and-update richer/bespoke docs (not blank-skeleton
# overwrite), and design-recovery must emit CANONICAL v5 flat keys with the project's slug
# as an ALIAS so catalog selection + template required_decisions slicing resolve.
source "$(dirname "$0")/lib/test_helpers.sh"

# Edit 1 — re-architect-flow.md Step 6 preserve-and-update policy.
F="$REPO_ROOT/skills/project-architect/references/re-architect-flow.md"
assert_file_exists "$F" 're-architect-flow.md exists'
C="$(cat "$F" 2>/dev/null || true)"
assert_contains "$C" 'preserve-and-update' 'Step 6 states the preserve-and-update policy'
assert_contains "$C" 'no catalog template' 'Step 6 keeps bespoke docs that have no catalog template'
assert_contains "$C" 'doc set may grow' 'Step 6 notes the live doc set may grow after re-derive'

# Edit 2 — design-recovery.md emits canonical keys with a slug alias.
A="$REPO_ROOT/agents/design-recovery.md"
assert_file_exists "$A" 'design-recovery agent exists'
D="$(cat "$A" 2>/dev/null || true)"
assert_contains "$D" 'canonical' 'recovery prefers the canonical v5 flat key'
assert_contains "$D" 'alias' 'recovery records the project slug as an alias'
assert_contains "$D" 'database.engine' 'recovery names an example canonical key'

test_summary
