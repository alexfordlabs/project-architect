#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# Bash integration test for `architect-brain detect` — covers the three
# classifications (greenfield / v8_project / pre_v8_project) end-to-end
# via the bin/architect-brain shim.

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCHITECT_BRAIN="$PLUGIN_ROOT/bin/architect-brain"

[ -x "$ARCHITECT_BRAIN" ] || { echo "FAIL: $ARCHITECT_BRAIN not executable"; exit 1; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Case 1: greenfield — empty docs directory
mkdir -p "$TMP/case1/docs"
out=$("$ARCHITECT_BRAIN" detect --docs-dir "$TMP/case1/docs" 2>&1)
echo "$out" | grep -q '"situation": "greenfield"' || {
  echo "FAIL case1 (greenfield): unexpected output"
  echo "$out"
  exit 1
}

# Case 2: v8_project — init creates schema 4.0 layout
mkdir -p "$TMP/case2/docs"
"$ARCHITECT_BRAIN" init --docs-dir "$TMP/case2/docs" >/dev/null 2>&1
out=$("$ARCHITECT_BRAIN" detect --docs-dir "$TMP/case2/docs" 2>&1)
echo "$out" | grep -q '"situation": "v8_project"' || {
  echo "FAIL case2 (v8_project): missing situation"
  echo "$out"
  exit 1
}
echo "$out" | grep -q '"schema_version": "4.0"' || {
  echo "FAIL case2 (v8_project): wrong schema_version"
  echo "$out"
  exit 1
}

# Case 3: pre_v8_project — hand-write v7 monolith
mkdir -p "$TMP/case3/docs"
cat > "$TMP/case3/docs/_architect_state.json" <<'EOF'
{
  "schema_version": "3.1",
  "phase": 5,
  "decisions": {}
}
EOF
out=$("$ARCHITECT_BRAIN" detect --docs-dir "$TMP/case3/docs" 2>&1)
echo "$out" | grep -q '"situation": "pre_v8_project"' || {
  echo "FAIL case3 (pre_v8_project): missing situation"
  echo "$out"
  exit 1
}
echo "$out" | grep -q '"schema_version": "3.1"' || {
  echo "FAIL case3 (pre_v8_project): wrong schema_version"
  echo "$out"
  exit 1
}

echo "PASS: architect-brain detect classifies all three situations"
