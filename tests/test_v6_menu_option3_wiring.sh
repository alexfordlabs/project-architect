#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"
VA="$(cat "$REPO_ROOT/skills/project-architect/references/version-awareness.md")"
assert_contains "$VA" 're-architect-flow.md' 'option 3 routes to the re-architect flow'
assert_contains "$VA" '/re-architect' 'option 3 names the /re-architect command'
test_summary
