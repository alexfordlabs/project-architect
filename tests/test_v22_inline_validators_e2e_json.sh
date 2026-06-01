#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
# Test for v2.2 task 49: E2E validator chain for bad JSON (sketch A).
#
# This test validates that the jq command from the Validation section
# actually catches a malformed settings.json (trailing comma). We can't
# dispatch the actual claude-tooling-author agent in a test, so we verify
# the validator command itself rejects invalid JSON.

source "$(dirname "$0")/lib/test_helpers.sh"

# jq empty must reject trailing-comma JSON
if ! command -v jq >/dev/null 2>&1; then
  echo "SKIP: jq not installed"
  test_summary
  exit 0
fi

RESULT=$(jq empty "$REPO_ROOT/tests/fixtures/bad-settings.json" 2>&1; true)

# jq empty should return non-zero on invalid JSON
RESULT2=$(jq empty "$REPO_ROOT/tests/fixtures/bad-settings.json" 2>/dev/null; echo "exit=$?")
[[ "$RESULT2" == *"exit=0"* ]] && \
  { FAIL_COUNT=$((FAIL_COUNT + 1)); FAIL_MESSAGES+=("FAIL: jq empty must reject invalid JSON"); } || \
  PASS_COUNT=$((PASS_COUNT + 1))

# Error message should reference the parse failure
[[ "$RESULT" == *"parse error"* || "$RESULT" == *"Invalid"* || "$RESULT" == *"error"* ]] && \
  PASS_COUNT=$((PASS_COUNT + 1)) || \
  { FAIL_COUNT=$((FAIL_COUNT + 1)); FAIL_MESSAGES+=("FAIL: jq error message expected; got: $RESULT"); }

test_summary
