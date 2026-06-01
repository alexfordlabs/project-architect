#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"
DA="$(cat "$REPO_ROOT/agents/document-author.md")"
RS="$(cat "$REPO_ROOT/agents/research-scout.md")"

assert_contains "$DA" 'newest-stable' 'document-author must resolve newest-stable versions'
assert_contains "$DA" 'RC/beta/alpha/canary/next on P0' 'document-author must forbid pre-release on P0 deps'
assert_contains "$RS" 'newest-stable' 'research-scout must resolve newest-stable versions'
assert_contains "$RS" 'RC/beta/alpha/canary/next on P0' 'research-scout must forbid pre-release on P0 deps'
assert_contains "$RS" 'dependency_freshness' 'research-scout must reference the dependency_freshness gate (B23)'

test_summary
