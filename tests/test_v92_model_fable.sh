#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# v9.2 — Fable-everywhere model contract + the set-phase-preflight fix.
#
# Operator standing rule (2026-06-13): project-architect runs on the latest
# Fable-class model — the `fable` alias (auto-tracks the newest Fable) for
# every subagent dispatch and agent frontmatter, `claude-fable-5` (the concrete
# current id) wherever a generated artifact or data file needs an exact model
# string. This test pins every surface so a future edit can't silently
# reintroduce an Opus-pinned dispatch.

source "$(dirname "$0")/lib/test_helpers.sh"

SKILL="$(cat "$REPO_ROOT/skills/project-architect/SKILL.md")"
GP="$(cat "$REPO_ROOT/skills/project-architect/references/golden-paths.json")"
CTA="$(cat "$REPO_ROOT/agents/claude-tooling-author.md")"
RAF="$(cat "$REPO_ROOT/skills/project-architect/references/re-architect-flow.md")"
CCI="$(cat "$REPO_ROOT/skills/project-architect/references/claude-code-integration.md")"

# ── every subagent runs on the fable alias (latest Fable, auto-tracking) ──
for agent in "$REPO_ROOT"/agents/*.md; do
  FM="$(head -10 "$agent")"
  assert_contains "$FM" 'model: fable' "$(basename "$agent") frontmatter dispatches on fable"
done
assert_eq "$(grep -c '^model: opus' "$REPO_ROOT"/agents/*.md | grep -v ':0' | wc -l | tr -d ' ')" "0" \
  "no agent frontmatter still pins opus"

# ── SKILL.md dispatch prose + the model gate ──
assert_not_contains "$SKILL" 'model `opus`' "SKILL.md dispatches no longer name opus"
assert_contains "$SKILL" 'model `fable`' "SKILL.md dispatches name fable"
assert_contains "$SKILL" 'claude-fable-5' "SKILL.md model gate names the current Fable id"
assert_not_contains "$SKILL" 'select the latest Opus' "SKILL.md model gate steers to Fable, not Opus"

# ── tiger-panther bug #1: preflight is banner-only; never set-phase'd ──
assert_not_contains "$SKILL" 'set-phase preflight' "SKILL.md must not instruct set-phase preflight (check_20 ladder starts at kickoff)"

# ── reference flows + generated-artifact surfaces ──
assert_contains "$RAF" 'model: "fable"' "re-architect-flow dispatches on fable"
assert_not_contains "$RAF" 'model: "opus"' "re-architect-flow no longer pins opus"
assert_contains "$CCI" 'model: fable' "claude-code-integration generated-agent examples use fable"
assert_not_contains "$CCI" 'model: opus' "claude-code-integration examples no longer pin opus"
assert_contains "$CTA" 'claude-fable-5' "claude-tooling-author settings.json quality bar names the current Fable id"
assert_not_contains "$CTA" 'claude-opus-4-8' "claude-tooling-author quality bar no longer pins an Opus id"
assert_contains "$GP" 'claude-fable-5' "golden-paths ai.model is the current Fable id"
assert_not_contains "$GP" 'claude-opus-4-8' "golden-paths no longer pins an Opus id"

test_summary
