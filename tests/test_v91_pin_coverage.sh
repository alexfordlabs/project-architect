#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# v9.1 — pin-obligation coverage contract.
#
# The tiger-panther-game forensics showed the version-pin chain silently
# breaking when the RESEARCH obligation (research-scout §1a), the ORCHESTRATOR
# instruction (SKILL.md Phase 4), the KEY REGISTRY (decision-keys.md), and the
# GENERATOR consumption (configs._pin) disagree about WHICH tokens are owed.
# This test pins all four surfaces to the same token set, so adding a consumer
# without extending the obligation (or vice versa) fails the suite.

source "$(dirname "$0")/lib/test_helpers.sh"

SKILL="$(cat "$REPO_ROOT/skills/project-architect/SKILL.md")"
RS="$(cat "$REPO_ROOT/agents/research-scout.md")"
DK="$(cat "$REPO_ROOT/skills/project-architect/references/decision-keys.md")"
RP="$(cat "$REPO_ROOT/skills/project-architect/references/research-prompts.md")"
GP="$(cat "$REPO_ROOT/skills/project-architect/references/golden-paths.json")"
PLAYBOOK="$(cat "$REPO_ROOT/skills/project-architect/references/revision-playbook.md")"
TSD="$(cat "$REPO_ROOT/skills/project-architect/references/templates/TECH_STACK.md")"
CTA="$(cat "$REPO_ROOT/agents/claude-tooling-author.md")"
DA="$(cat "$REPO_ROOT/agents/document-author.md")"
CONFIGS="$(cat "$REPO_ROOT/skills/project-architect/lib/architect_brain/configs.py")"

# ── every generator-consumed token appears in every obligation surface ──
TOKENS=(next react node python postgres redis biome typescript)
for tok in "${TOKENS[@]}"; do
  assert_contains "$CONFIGS" "\"$tok\"" "configs.py FLOORS carries '$tok'"
  assert_contains "$SKILL" "stack.versions.$tok" "SKILL.md Phase-4 pin instruction covers '$tok'"
  assert_contains "$RS" "stack.versions.$tok" "research-scout §1a obligation covers '$tok'"
  assert_contains "$DK" "stack.versions.$tok" "decision-keys.md registry covers '$tok'"
done

# ── research obligation matches the emission condition (any JS/TS → biome) ──
assert_contains "$RS" 'any JS/TS stack' "research-scout biome obligation scoped to ANY JS/TS stack (matches generate-configs emission)"

# ── research-prompts universal checklist carries the pin step (no dangling §1a) ──
assert_contains "$RP" 'stack.versions.' "research-prompts.md universal checklist resolves stack.versions pins"
assert_contains "$RP" 'newest-stable' "research-prompts.md universal checklist demands newest-stable"

# ── golden paths: no superseded keys, no stale version literals as 'default' ──
assert_not_contains "$GP" 'stack.frontend.version' "golden-paths.json must not seed the superseded stack.frontend.version key"
assert_not_contains "$GP" 'Next.js 15' "golden-paths.json must not present a hardcoded Next major as the default stack"
assert_not_contains "$GP" 'claude-opus-4-7' "golden-paths.json ai.model must track the current Opus id"

# ── revision-playbook keys live in the canonical stack.* namespace ──
assert_contains "$PLAYBOOK" 'stack.database.engine' "revision-playbook uses canonical stack.database.engine"
assert_contains "$PLAYBOOK" 'stack.frontend.framework' "revision-playbook uses canonical stack.frontend.framework"
assert_eq "$(grep -cE '^\| (frontend|backend|database|cache)\.' "$REPO_ROOT/skills/project-architect/references/revision-playbook.md")" "0" \
  "revision-playbook has no un-namespaced stack-family keys left"

# ── TECH_STACK template surfaces ALL pin rows, not a subset ──
for tok in postgres redis biome typescript; do
  assert_contains "$TSD" "stack.versions.$tok" "TECH_STACK.md template surfaces the '$tok' pin"
done

# ── stale model id swept (legacy/ and fixtures are exempt by design) ──
assert_not_contains "$CTA" 'claude-opus-4-7' "claude-tooling-author quality bar tracks the current Opus id"
assert_contains "$CTA" 'claude-opus-4-8' "claude-tooling-author names claude-opus-4-8"

# ── document-author worked example doesn't anchor a stale major ──
assert_not_contains "$DA" 'Next.js 15.x' "document-author version-family example is not a stale major"

# ── CI matrix covers the newest stable Python (floor parity) ──
CI="$(cat "$REPO_ROOT/.github/workflows/ci.yml")"
assert_contains "$CI" "'3.14'" "CI python matrix includes 3.14"

# ── templates never claim an old release is 'the latest at time of writing' ──
assert_eq "$(grep -rl 'the latest at time of writing' "$REPO_ROOT/skills/project-architect/references/templates/" | wc -l | tr -d ' ')" "0" \
  "no template asserts a frozen release as 'the latest at time of writing'"

test_summary
