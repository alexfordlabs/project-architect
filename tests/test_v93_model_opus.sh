#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# v9.3 — Opus-everywhere model contract (supersedes the v9.2 Fable contract).
#
# Operator decision (2026-06-13): pin every subagent to the latest Opus — the
# `opus` alias (the reliable, always-available top tier; latest Opus 4.8 1M) for
# every agent frontmatter and dispatch directive, `claude-opus-4-8` (the
# concrete current id) wherever a generated artifact or data file needs an exact
# model string. Chosen over a hardcoded `fable` (which hard-fails when Fable is
# unavailable to the account) and over `inherit`. This test pins every surface
# so a future edit can't silently reintroduce a Fable-pinned dispatch that could
# hard-fail. (frontmatter is the single source of truth for a dispatch's model.)

source "$(dirname "$0")/lib/test_helpers.sh"

SKILL="$(cat "$REPO_ROOT/skills/project-architect/SKILL.md")"
GP="$(cat "$REPO_ROOT/skills/project-architect/references/golden-paths.json")"
CTA="$(cat "$REPO_ROOT/agents/claude-tooling-author.md")"
RAF="$(cat "$REPO_ROOT/skills/project-architect/references/re-architect-flow.md")"
CCI="$(cat "$REPO_ROOT/skills/project-architect/references/claude-code-integration.md")"

# ── every subagent runs on the opus alias (latest Opus) ──
for agent in "$REPO_ROOT"/agents/*.md; do
  FM="$(head -10 "$agent")"
  assert_contains "$FM" 'model: opus' "$(basename "$agent") frontmatter dispatches on opus"
done
assert_eq "$(grep -c '^model: fable' "$REPO_ROOT"/agents/*.md | grep -v ':0' | wc -l | tr -d ' ')" "0" \
  "no agent frontmatter still pins fable"

# ── SKILL.md dispatch prose + the model gate ──
assert_not_contains "$SKILL" 'model `fable`' "SKILL.md dispatches no longer name fable"
assert_contains "$SKILL" 'model `opus`' "SKILL.md dispatches name opus"
assert_contains "$SKILL" 'claude-opus-4-8' "SKILL.md model gate names the current Opus id"
assert_not_contains "$SKILL" 'select the latest Fable' "SKILL.md model gate steers to Opus, not Fable"

# ── tiger-panther bug #1 (v9.2): preflight is banner-only; never set-phase'd ──
assert_not_contains "$SKILL" 'set-phase preflight' "SKILL.md must not instruct set-phase preflight (check_20 ladder starts at kickoff)"

# ── reference flows + generated-artifact surfaces ──
assert_contains "$RAF" 'model: "opus"' "re-architect-flow dispatches on opus"
assert_not_contains "$RAF" 'model: "fable"' "re-architect-flow no longer pins fable"
assert_contains "$CCI" 'model: opus' "claude-code-integration generated-agent examples use opus"
assert_not_contains "$CCI" 'model: fable' "claude-code-integration examples no longer pin fable"
assert_contains "$CTA" 'claude-opus-4-8' "claude-tooling-author settings.json quality bar names the current Opus id"
assert_not_contains "$CTA" 'claude-fable-5' "claude-tooling-author quality bar no longer pins a Fable id"
assert_contains "$GP" 'claude-opus-4-8' "golden-paths ai.model is the current Opus id"
assert_not_contains "$GP" 'claude-fable-5' "golden-paths no longer pins a Fable id"

test_summary
