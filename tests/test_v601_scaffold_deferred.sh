#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"
F="$(cat "$REPO_ROOT/skills/project-architect/references/re-architect-flow.md")"
assert_contains "$F" 'scaffold.deferred' 're-architect records scaffold.deferred (design-only, code not rebuilt)'
test_summary
