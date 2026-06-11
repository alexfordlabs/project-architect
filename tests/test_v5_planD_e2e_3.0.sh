#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
source "$(dirname "$0")/lib/test_helpers.sh"
if ! command -v jq >/dev/null 2>&1; then echo "SKIP: jq"; test_summary; exit 0; fi
RUN_ALL="$REPO_ROOT/agents/quality-gate-auditor/run_all.sh"

for d in "$REPO_ROOT"/tests/fixtures/e2e-go-cli "$REPO_ROOT"/tests/fixtures/e2e-programming-language-interpreter "$REPO_ROOT"/tests/fixtures/e2e-programming-language-transpiler "$REPO_ROOT"/tests/fixtures/e2e-python-tui "$REPO_ROOT"/tests/fixtures/e2e-rust-cli; do
  S="$d/docs/_architect_state.json"
  assert_eq "$(jq -r '.schema_version' "$S")" "3.0" "$(basename "$d") migrated to 3.0"
  assert_eq "$(jq 'has("decisions_dir")' "$S")" "true" "$(basename "$d") has decisions_dir"
  assert_eq "$(jq 'has("project_layout")' "$S")" "true" "$(basename "$d") has project_layout"
  R=$(bash "$RUN_ALL" "$d" "$S")
  BC=$(echo "$R" | jq -r '.summary.blocker')
  [[ "$BC" -le 3 ]] && PASS_COUNT=$((PASS_COUNT+1)) || { FAIL_COUNT=$((FAIL_COUNT+1)); FAIL_MESSAGES+=("$(basename "$d") BLOCKER $BC > 3"); }
done

test_summary
