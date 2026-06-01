#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# Clean-break guard (v8): the v7 bash surface is REMOVED. architect-brain
# (python) is the only binary — no architect-ledger / architect-ui shims, and
# no quality-gate-auditor subagent (the audit is now `architect-brain audit`).

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fail() { echo "FAIL: $1"; exit 1; }

# architect-brain IS the binary, present + executable
[ -x "$PLUGIN_ROOT/bin/architect-brain" ] || fail "bin/architect-brain missing or not executable"

# the v7 binaries are GONE (clean break — no shims)
[ ! -e "$PLUGIN_ROOT/bin/architect-ledger" ] || fail "v7 bin/architect-ledger still present"
[ ! -e "$PLUGIN_ROOT/bin/architect-ui" ]     || fail "v7 bin/architect-ui still present"

# the v7 quality-gate-auditor subagent + its bash check tree are GONE
[ ! -e "$PLUGIN_ROOT/agents/quality-gate-auditor.md" ] || fail "v7 quality-gate-auditor.md still present (audit is now the architect-brain CLI)"
[ ! -d "$PLUGIN_ROOT/agents/quality-gate-auditor" ]    || fail "v7 agents/quality-gate-auditor/ bash tree still present"

# no surviving prose surface INVOKES a deleted v7 binary (negations are fine).
# Scans skills/ + agents/ + commands/ — the command entry files are a prose
# surface too, and historically lagged the v8 binary rename (the /upgrade-project
# and /re-architect commands shipped invoking the deleted architect-ledger).
if grep -rnE '\$\{CLAUDE_PLUGIN_ROOT\}/bin/architect-(ledger|ui)' "$PLUGIN_ROOT/skills" "$PLUGIN_ROOT/agents" "$PLUGIN_ROOT/commands" 2>/dev/null; then
  fail "a prose surface still invokes a deleted v7 binary (architect-ledger/architect-ui)"
fi

echo "PASS: clean break — architect-brain is the only binary; no v7 ledger/ui/auditor shims"
