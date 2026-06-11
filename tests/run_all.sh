#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)

# Run every test_*.sh file in tests/. Exits non-zero on any failure.
#
# Wave 1.13: also runs the architect_brain Python unittest suite + pre-cleans
# Python tooling caches that would otherwise trip test_v401 (pyc files embed
# absolute compile-time paths; .hypothesis caches from the Wave 1.7 property
# test have the same issue).

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
REPO_ROOT="$(pwd)"

# --- Wave 1.13: pre-clean Python tooling caches --------------------------------
# pyc files in __pycache__/ embed absolute compile-time paths that trip
# test_v401_no_absolute_home_paths.sh. .hypothesis/ caches from the Wave 1.7
# property test have the same issue. Cleanup is cheap and idempotent.
find "$REPO_ROOT/skills" -type d \( -name __pycache__ -o -name .hypothesis \) \
  -exec rm -rf {} + 2>/dev/null || true

TOTAL_PASS=0
TOTAL_FAIL=0
FAILED_FILES=()

for t in tests/test_*.sh; do
  [[ -f "$t" ]] || continue
  echo "→ Running $t"
  if bash "$t"; then
    TOTAL_PASS=$((TOTAL_PASS + 1))
  else
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
    FAILED_FILES+=("$t")
  fi
done

# --- Wave 1.13: architect_brain Python unittest suite --------------------------
# 55 Python tests (Wave 1.2–1.11) discovered + run as one logical entry in the
# bash-runner tally. Failure adds the Python suite to FAILED_FILES so the
# final report is honest about which surface broke.
echo ""
echo "→ Running architect_brain Python unit tests (python3 -m unittest discover -s architect_brain.tests)"
PY_LIB="$REPO_ROOT/skills/project-architect/lib"
if (cd "$PY_LIB" && python3 -m unittest discover -s architect_brain.tests 2>&1); then
  TOTAL_PASS=$((TOTAL_PASS + 1))
else
  TOTAL_FAIL=$((TOTAL_FAIL + 1))
  FAILED_FILES+=("architect_brain Python suite")
fi

echo ""
echo "═══════════════════════════════"
echo "Test files passed: $TOTAL_PASS"
echo "Test files failed: $TOTAL_FAIL"
if [[ "$TOTAL_FAIL" -gt 0 ]]; then
  echo "Failed:"
  for f in "${FAILED_FILES[@]}"; do
    echo "  $f"
  done
  exit 1
fi
echo "All tests passed."
