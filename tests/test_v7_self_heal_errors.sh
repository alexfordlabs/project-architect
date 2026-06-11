#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# R2: a self-healing informational error-handling protocol. At any BLOCKER/error
# the orchestrator never silently fails or dumps a raw trace — it surfaces a
# concise INFORMATIONAL error state (what failed / what's known / what's at risk),
# then AskUserQuestion offers two paths: write a diagnostic report and stop, OR
# self-heal (propose concrete remediations derived from the info already gathered
# and continue after the user approves). The full protocol lives in
# references/output-style.md §4; the flow docs + dispatch-prompts.md cite it. This
# presence test pins the protocol's load-bearing content and confirms each surface
# is wired to reach it.
#
# Backtick needles below are intentional content assertions.
# SC1091: test_helpers.sh is sourced dynamically (every test does this).
# shellcheck disable=SC2016,SC1091
source "$(dirname "$0")/lib/test_helpers.sh"

REF="$REPO_ROOT/skills/project-architect/references"

# 1. output-style.md carries the full self-healing error protocol (case-sensitive).
OUTPUT_STYLE="$(cat "$REF/output-style.md")"
assert_contains "$OUTPUT_STYLE" "AskUserQuestion"    "output-style.md offers the two paths via AskUserQuestion"
assert_contains "$OUTPUT_STYLE" "self-heal"          "output-style.md names the self-heal path"
assert_contains "$OUTPUT_STYLE" "informational error" "output-style.md surfaces a concise informational error state first"
assert_contains "$OUTPUT_STYLE" "report and stop"    "output-style.md offers write-a-report-and-stop"

# 2. the flow docs + dispatch-prompts each reach the self-heal protocol.
UPGRADE="$(cat "$REF/upgrade-flow.md")"
assert_contains "$UPGRADE" "self-heal"               "upgrade-flow.md cites the self-heal protocol on a blocker"

REARCH="$(cat "$REF/re-architect-flow.md")"
assert_contains "$REARCH" "self-heal"                "re-architect-flow.md cites the self-heal protocol on a blocker"

SA="$(cat "$REF/situation-assessment.md")"
assert_contains "$SA" "self-heal"                    "situation-assessment.md 'Report only' notes the self-heal alternative"

DISPATCH="$(cat "$REF/dispatch-prompts.md")"
assert_contains "$DISPATCH" "self-heal"              "dispatch-prompts.md: a blocked agent returns an info error state for the self-heal protocol"

test_summary
