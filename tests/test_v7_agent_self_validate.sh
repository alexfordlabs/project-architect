#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# A5: the two doc/tooling authoring agents must NOT ship pre-existing debt that
# the strict gate then inherits. Two prose contracts, in BOTH agents:
#   (a) self-run the no-placeholders regex \{\{[a-z_]+\}\} on every file written
#       before returning — fix (resolve from state or omit) + re-check, never
#       return an unresolved {{...}} (the B08 no_placeholders gate's exact catch).
#   (b) filter cross-references to the ACTUALLY-SELECTED Phase-4 docs only, never
#       the whole document catalog — a link to an unselected doc is a dangling
#       link that the B22 cross_link_integrity gate flags.
# This presence test pins both contracts in both agent files.
#
# Backtick + brace ({{...}}) + regex needles below are intentional content
# assertions. SC1091: test_helpers.sh is sourced dynamically (every test does).
# shellcheck disable=SC2016,SC1091
source "$(dirname "$0")/lib/test_helpers.sh"

DOCAUTH="$REPO_ROOT/agents/document-author.md"
TOOLAUTH="$REPO_ROOT/agents/claude-tooling-author.md"

# Both agent files exist.
assert_file_exists "$DOCAUTH" "agents/document-author.md exists"
assert_file_exists "$TOOLAUTH" "agents/claude-tooling-author.md exists"

D="$(cat "$DOCAUTH")"
T="$(cat "$TOOLAUTH")"

# Contract (a) — self-run the placeholder regex (both agents, case-sensitive).
assert_contains "$D" '\{\{[a-z_]+\}\}' "document-author cites the literal no-placeholders regex"
assert_contains "$D" "self-run" "document-author actively self-runs the placeholder check"
assert_contains "$D" "placeholder" "document-author names the placeholder contract"
assert_contains "$T" '\{\{[a-z_]+\}\}' "claude-tooling-author cites the literal no-placeholders regex"
assert_contains "$T" "self-run" "claude-tooling-author actively self-runs the placeholder check"
assert_contains "$T" "placeholder" "claude-tooling-author names the placeholder contract"

# Contract (b) — cross-refs limited to the Phase-4 selected docs (both agents).
assert_contains "$D" "selected" "document-author limits cross-refs to selected docs"
assert_contains "$D" "catalog" "document-author warns against the whole catalog"
assert_contains "$T" "selected" "claude-tooling-author references only selected/real targets"
assert_contains "$T" "catalog" "claude-tooling-author warns against inventing catalog docs"

test_summary
