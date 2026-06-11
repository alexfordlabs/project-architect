#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# v8 migrator smoke via the bin/architect-brain shim: a v7 monolith
# docs/_architect_state.json (schema < 4.0) migrates forward to the
# event-sourced docs/_architect_state/ layout at schema 4.0, and detect then
# classifies the result as v8_project. (Reversibility is unit-tested in
# test_migration.py; this proves the end-to-end CLI path.)

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AB="$PLUGIN_ROOT/bin/architect-brain"
fail() { echo "FAIL: $1"; exit 1; }

[ -x "$AB" ] || fail "$AB not executable"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# work on a COPY of the committed fixture (never mutate it)
cp -r "$PLUGIN_ROOT/tests/fixtures/migration/v71-rust-cli" "$TMP/proj"
D="$TMP/proj/docs"

# precondition: a v7 monolith, detected as pre_v8_project
"$AB" detect --docs-dir "$D" 2>&1 | grep -q '"situation": "pre_v8_project"' \
  || fail "fixture not detected as pre_v8_project"

# migrate (skip the post-migration audit for a hermetic smoke)
"$AB" migrate --docs-dir "$D" --no-audit >/dev/null 2>&1 || fail "migrate exited non-zero"

# post-conditions: the v8 event-sourced layout exists at schema 4.0
[ -f "$D/_architect_state/events.jsonl" ]        || fail "events.jsonl not created by migrate"
[ -f "$D/_architect_state/99-flat-index.json" ]  || fail "99-flat-index.json not created by migrate"
grep -q '4.0' "$D/_architect_state/schema_version" || fail "schema_version probe not 4.0 after migrate"
"$AB" detect --docs-dir "$D" 2>&1 | grep -q '"situation": "v8_project"' \
  || fail "migrated project not detected as v8_project"

echo "PASS: migrate v7 monolith (schema 3.0) -> v8 event-sourced state at 4.0"
