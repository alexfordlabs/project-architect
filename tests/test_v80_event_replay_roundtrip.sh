#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# v8 event-sourced state round-trip via the bin/architect-brain shim:
# init -> set-decision -> set-phase -> replay -> the projections reflect the
# events (the replay invariant, end-to-end through the binary).

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AB="$PLUGIN_ROOT/bin/architect-brain"
fail() { echo "FAIL: $1"; exit 1; }

[ -x "$AB" ] || fail "$AB not executable"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
D="$TMP/docs"
mkdir -p "$D"

"$AB" init --docs-dir "$D" >/dev/null 2>&1 || fail "init failed"
"$AB" set-decision stack.backend.language python --docs-dir "$D" --phase stack >/dev/null 2>&1 || fail "set-decision failed"
"$AB" set-phase architecture --docs-dir "$D" >/dev/null 2>&1 || fail "set-phase failed"

# events.jsonl is the authoritative append-only log
[ -f "$D/_architect_state/events.jsonl" ] || fail "events.jsonl missing"

# replay regenerates the projections purely from events.jsonl
"$AB" replay --docs-dir "$D" >/dev/null 2>&1 || fail "replay failed"

# the flat index carries the decision; the workflow projection carries the phase
grep -q '"stack.backend.language": "python"' "$D/_architect_state/99-flat-index.json" \
  || fail "decision not in 99-flat-index.json after replay"
grep -q '"current_phase": "architecture"' "$D/_architect_state/workflow.json" \
  || fail "phase not reflected in workflow.json after replay"
grep -q '4.0' "$D/_architect_state/schema_version" \
  || fail "schema_version probe is not 4.0"

echo "PASS: event-replay round-trip (init -> set-decision/set-phase -> replay -> projections)"
