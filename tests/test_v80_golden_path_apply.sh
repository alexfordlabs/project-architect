#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# v8 Golden Paths smoke via the bin/architect-brain shim: `golden-path list`
# surfaces the catalog, and `golden-path apply <id>` seeds pre-filled decisions
# into the flat index (a GoldenPathApplied event + one DecisionMade per key).

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AB="$PLUGIN_ROOT/bin/architect-brain"
fail() { echo "FAIL: $1"; exit 1; }

[ -x "$AB" ] || fail "$AB not executable"

# list surfaces the catalog (modern_saas_2026 is one of the 9 canonical paths)
"$AB" golden-path list 2>&1 | grep -q "modern_saas_2026" \
  || fail "golden-path list did not surface modern_saas_2026"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
D="$TMP/docs"
mkdir -p "$D"

"$AB" init --docs-dir "$D" >/dev/null 2>&1 || fail "init failed"
"$AB" golden-path apply modern_saas_2026 --docs-dir "$D" >/dev/null 2>&1 || fail "golden-path apply failed"

# the apply seeded decisions into the flat index (canonical stack.* keyspace)
grep -q '"stack\.' "$D/_architect_state/99-flat-index.json" \
  || fail "golden-path apply seeded no stack.* decisions into the flat index"

echo "PASS: golden-path list + apply (seeds the canonical decision keyspace)"
