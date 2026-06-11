#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# v8 agent-roster invariant (robust presence check; supersedes the v7
# hardcoded-value runtime-budget tests): the v8 roster is EXACTLY 7 agents,
# each declaring model: opus + a runtime_budget (typical_minutes + max_minutes).
# quality-gate-auditor is NOT an agent in v8 — the audit is the architect-brain CLI.

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fail() { echo "FAIL: $1"; exit 1; }

AGENTS="research-scout architecture-specialist document-author claude-md-author claude-tooling-author decision-revisor design-recovery"

for a in $AGENTS; do
  f="$PLUGIN_ROOT/agents/$a.md"
  [ -f "$f" ] || fail "v8 agent $a.md missing"
  grep -qE '^model: *opus' "$f"        || fail "$a missing 'model: opus'"
  grep -q 'runtime_budget:' "$f"        || fail "$a missing runtime_budget frontmatter"
  grep -q 'typical_minutes:' "$f"       || fail "$a missing typical_minutes"
  grep -q 'max_minutes:' "$f"           || fail "$a missing max_minutes"
done

# quality-gate-auditor is removed in v8 (audit is `architect-brain audit`)
[ ! -e "$PLUGIN_ROOT/agents/quality-gate-auditor.md" ] \
  || fail "agents/quality-gate-auditor.md should be removed in v8"

# the roster is EXACTLY 7
n=$(ls "$PLUGIN_ROOT"/agents/*.md | wc -l | tr -d ' ')
[ "$n" -eq 7 ] || fail "expected exactly 7 v8 agents, found $n"

echo "PASS: 7 v8 agents declare model:opus + runtime_budget; quality-gate-auditor removed"
